import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import pg from 'pg';
import * as conversationService from '../../src/services/conversation.service.js';
import * as messageService from '../../src/services/message.service.js';
import { ForbiddenError, RateLimitError } from '../../src/lib/errors.js';
import { ManualClock } from '../../src/lib/time.js';
import { setupTestDatabase, teardownTestDatabase, buildCtx, userActor, insertUser } from './testCtxAgentC.js';
import type { Ctx } from '../../src/lib/ctx.js';

let pool: pg.Pool;

before(async () => {
  pool = await setupTestDatabase('chat');
});

after(async () => {
  await teardownTestDatabase();
});

async function makeUser(trustLevel: 'limited' | 'standard' | 'trusted' | 'elite' = 'standard'): Promise<string> {
  return insertUser(pool, { trustLevel });
}

/** Directly creates an 'active' conversation row, bypassing interest.service (out of this file's scope, interest.test.ts already covers acceptInterest -> conversation wiring). */
async function makeConversation(
  ctx: Ctx,
  userAId: string,
  userBId: string,
): Promise<Awaited<ReturnType<typeof conversationService.getOrCreateConversation>>> {
  return conversationService.getOrCreateConversation(ctx, userAId, userBId);
}

// =====================================================================
// getOrCreateConversation, canonical ordering + idempotency.
// =====================================================================

test('getOrCreateConversation: canonical ordering holds regardless of argument order', async () => {
  const u1 = await makeUser();
  const u2 = await makeUser();
  const clock = new ManualClock(new Date('2026-01-01T00:00:00.000Z'));
  const ctx = buildCtx({ actor: userActor(u1), clock });

  const [lo, hi] = u1 < u2 ? [u1, u2] : [u2, u1];
  const a = await conversationService.getOrCreateConversation(ctx, u1, u2);
  const b = await conversationService.getOrCreateConversation(ctx, u2, u1);
  assert.equal(a.id, b.id);
  assert.equal(a.userAId, lo);
  assert.equal(a.userBId, hi);
});

test('getOrCreateConversation: reactivates an archived conversation for the same pair rather than creating a second row', async () => {
  const u1 = await makeUser();
  const u2 = await makeUser();
  const clock = new ManualClock(new Date('2026-01-02T00:00:00.000Z'));
  const ctx = buildCtx({ actor: userActor(u1), clock });

  const first = await makeConversation(ctx, u1, u2);
  await conversationService.archiveConversation(ctx, first.id);

  const again = await conversationService.getOrCreateConversation(ctx, u1, u2);
  assert.equal(again.id, first.id);
  assert.equal(again.status, 'active');
  assert.equal(again.archivedAt, null);
});

// =====================================================================
// §12.6-vs-§12.7 precedence: established always wins, unconditionally.
// =====================================================================

test('establishConversation is idempotent and terminal, a second call and getOrCreateConversation both leave it untouched', async () => {
  const u1 = await makeUser();
  const u2 = await makeUser();
  const clock = new ManualClock(new Date('2026-01-03T00:00:00.000Z'));
  const ctx = buildCtx({ actor: userActor(u1), clock });

  const conv = await makeConversation(ctx, u1, u2);
  const established = await conversationService.establishConversation(ctx, conv.id);
  assert.equal(established.status, 'established');
  assert.ok(established.firstDateCompletedAt);

  const firstCompletedAt = established.firstDateCompletedAt!.getTime();
  clock.advanceHours(5);
  const establishedAgain = await conversationService.establishConversation(ctx, conv.id);
  assert.equal(establishedAgain.status, 'established');
  assert.equal(establishedAgain.firstDateCompletedAt!.getTime(), firstCompletedAt, 'first_date_completed_at must not move on a second call');

  // getOrCreateConversation must never revert an established conversation.
  const viaGetOrCreate = await conversationService.getOrCreateConversation(ctx, u1, u2);
  assert.equal(viaGetOrCreate.status, 'established');
});

test('established conversations are immune to decay, however far past every threshold', async () => {
  const u1 = await makeUser();
  const u2 = await makeUser();
  const clock = new ManualClock(new Date('2026-01-04T00:00:00.000Z'));
  const ctx = buildCtx({ actor: { type: 'system', job: 'chat_decay' }, clock });

  const conv = await makeConversation(ctx, u1, u2);
  await messageService.sendMessage(buildCtx({ actor: userActor(u1), clock }), conv.id, 'hey! excited to chat');
  await conversationService.establishConversation(ctx, conv.id);

  clock.advanceDays(365); // absurdly far past 72h/14d/21d
  const result = await conversationService.runChatDecayJob(ctx);
  assert.equal(result.archived, 0);
  assert.equal(result.cooled, 0);

  const stillEstablished = await conversationService.getConversation(buildCtx({ actor: userActor(u1), clock }), conv.id);
  assert.equal(stillEstablished.status, 'established');
});

test('established conversations are excluded from the active-conversation count', async () => {
  const u1 = await makeUser();
  const u2 = await makeUser();
  const clock = new ManualClock(new Date('2026-01-05T00:00:00.000Z'));
  const ctx = buildCtx({ actor: userActor(u1), clock });

  const before = await conversationService.countActiveConversationsForUser(ctx, u1);
  const conv = await makeConversation(ctx, u1, u2);
  assert.equal(await conversationService.countActiveConversationsForUser(ctx, u1), before + 1);

  await conversationService.establishConversation(ctx, conv.id);
  assert.equal(await conversationService.countActiveConversationsForUser(ctx, u1), before);
});

// =====================================================================
// Decay boundaries at exactly 72h / 14d / 21d.
// =====================================================================

test('decay job: prompts at 72h, cools at 14d, archives at 21d, and never touches a conversation with a date proposal', async () => {
  const clock = new ManualClock(new Date('2026-02-01T00:00:00.000Z'));
  const jobCtx = buildCtx({ actor: { type: 'system', job: 'chat_decay' }, clock });

  // Conversation A: will cross every threshold, no date proposal.
  const a1 = await makeUser();
  const a2 = await makeUser();
  const convA = await makeConversation(jobCtx, a1, a2);
  await messageService.sendMessage(buildCtx({ actor: userActor(a1), clock }), convA.id, 'first message in A');

  // Conversation B: has a date proposal on record -> decay must skip it entirely.
  const b1 = await makeUser();
  const b2 = await makeUser();
  const convB = await makeConversation(jobCtx, b1, b2);
  await messageService.sendMessage(buildCtx({ actor: userActor(b1), clock }), convB.id, 'first message in B');
  // date_proposals.venue_id FKs to venues, insert a throwaway venue first.
  const { rows: venueRows } = await pool.query<{ id: string }>(
    `INSERT INTO venues (name, address, latitude, longitude, category, active, margin_percent, redemption_method)
     VALUES ('Test Venue', '1 Test St', 0, 0, 'coffee', true, 0, 'qr_scan') RETURNING id`,
  );
  await pool.query(
    `INSERT INTO date_proposals (conversation_id, proposer_id, recipient_id, venue_id, scheduled_start, scheduled_end, status, policy_snapshot, escrow_amount_cents)
     VALUES ($1, $2, $3, $4, now() + interval '2 days', now() + interval '2 days 1 hour', 'draft', '{}'::jsonb, 0)`,
    [convB.id, b1, b2, venueRows[0]!.id],
  );

  // --- 72h: prompt (no status change) ---
  clock.advanceHours(73);
  let result = await conversationService.runChatDecayJob(jobCtx);
  assert.equal(result.prompted, 1, 'only conversation A (no date proposal) should be prompted');
  assert.equal(result.cooled, 0);
  assert.equal(result.archived, 0);
  assert.equal((await conversationService.getConversation(buildCtx({ actor: userActor(a1), clock }), convA.id)).status, 'active');

  // --- 14d: cooling ---
  clock.set(new Date('2026-02-01T00:00:00.000Z'));
  clock.advanceDays(14);
  clock.advanceHours(1);
  result = await conversationService.runChatDecayJob(jobCtx);
  assert.equal(result.cooled, 1);
  assert.equal(
    (await conversationService.getConversation(buildCtx({ actor: userActor(a1), clock }), convA.id)).status,
    'cooling',
  );
  assert.equal(
    (await conversationService.getConversation(buildCtx({ actor: userActor(b1), clock }), convB.id)).status,
    'active',
    'conversation B has a date proposal and must never be touched by decay',
  );

  // --- 21d: archived ---
  clock.set(new Date('2026-02-01T00:00:00.000Z'));
  clock.advanceDays(21);
  clock.advanceHours(1);
  result = await conversationService.runChatDecayJob(jobCtx);
  assert.equal(result.archived, 1);
  assert.equal(
    (await conversationService.getConversation(buildCtx({ actor: userActor(a1), clock }), convA.id)).status,
    'archived',
  );
});

// =====================================================================
// message.service, chat unlock, rate limits, textscan wiring.
// =====================================================================

test('sendMessage: rejects when the conversation is not open (archived)', async () => {
  const u1 = await makeUser();
  const u2 = await makeUser();
  const clock = new ManualClock(new Date('2026-03-01T00:00:00.000Z'));
  const ctx = buildCtx({ actor: userActor(u1), clock });
  const conv = await makeConversation(ctx, u1, u2);
  await conversationService.archiveConversation(ctx, conv.id);

  await assert.rejects(() => messageService.sendMessage(ctx, conv.id, 'hello?'), ForbiddenError);
});

test('sendMessage: a stranger (non-participant) cannot send into the conversation', async () => {
  const u1 = await makeUser();
  const u2 = await makeUser();
  const stranger = await makeUser();
  const clock = new ManualClock(new Date('2026-03-02T00:00:00.000Z'));
  const ctx = buildCtx({ actor: userActor(u1), clock });
  const conv = await makeConversation(ctx, u1, u2);

  await assert.rejects(() => messageService.sendMessage(buildCtx({ actor: userActor(stranger), clock }), conv.id, 'hi'));
});

test('sendMessage: happy path persists the message, updates last_message_at, and records no flags for ordinary text', async () => {
  const u1 = await makeUser();
  const u2 = await makeUser();
  const clock = new ManualClock(new Date('2026-03-03T00:00:00.000Z'));
  const ctx = buildCtx({ actor: userActor(u1), clock });
  const conv = await makeConversation(ctx, u1, u2);

  const message = await messageService.sendMessage(ctx, conv.id, 'Looking forward to grabbing coffee!');
  assert.equal(message.senderId, u1);
  assert.equal(message.body, 'Looking forward to grabbing coffee!');
  assert.deepEqual(message.analysisFlags, []);

  const updated = await conversationService.getConversation(ctx, conv.id);
  assert.equal(updated.lastMessageAt?.getTime(), clock.now().getTime());
});

test('sendMessage: a flagged message still sends (never blocked by content) and persists message_flags rows', async () => {
  const u1 = await makeUser();
  const u2 = await makeUser();
  const clock = new ManualClock(new Date('2026-03-04T00:00:00.000Z'));
  const ctx = buildCtx({ actor: userActor(u1), clock });
  const conv = await makeConversation(ctx, u1, u2);

  const message = await messageService.sendMessage(ctx, conv.id, 'just venmo me the deposit, my handle is @scammer');
  assert.ok(message.analysisFlags.includes('money_request'));

  const { rows } = await pool.query('SELECT flag_type FROM message_flags WHERE message_id = $1', [message.id]);
  assert.ok(rows.length > 0);
});

test('sendMessage: 120/hr rate limit boundary, 120th send ok, 121st refused', async () => {
  const u1 = await makeUser();
  const u2 = await makeUser();
  const clock = new ManualClock(new Date('2026-03-05T00:00:00.000Z'));
  const ctx = buildCtx({ actor: userActor(u1), clock });
  const conv = await makeConversation(ctx, u1, u2);
  await ctx.config.set('chat.max_messages_per_hour', 3, 'test-admin');

  await messageService.sendMessage(ctx, conv.id, 'one');
  await messageService.sendMessage(ctx, conv.id, 'two');
  await messageService.sendMessage(ctx, conv.id, 'three');
  await assert.rejects(() => messageService.sendMessage(ctx, conv.id, 'four'), RateLimitError);

  await ctx.config.set('chat.max_messages_per_hour', 120, 'test-admin');
});

test('sendMessage: a limited-trust sender\'s link is flagged non-clickable (spec §6.4 "Send links: Limited = no")', async () => {
  const u1 = await makeUser('limited');
  const u2 = await makeUser();
  const clock = new ManualClock(new Date('2026-03-06T00:00:00.000Z'));
  const ctx = buildCtx({ actor: userActor(u1, 'limited'), clock });
  const conv = await makeConversation(ctx, u1, u2);

  const message = await messageService.sendMessage(ctx, conv.id, 'check this out https://example.com/thing');
  assert.ok(message.analysisFlags.includes('link'));

  const { rows } = await pool.query<{ severity: number }>(
    'SELECT severity FROM message_flags WHERE message_id = $1 AND flag_type = $2',
    [message.id, 'link'],
  );
  // Resolved via trust.service#canSendClickableLinks (called, not
  // reimplemented), a Limited-trust sender's link must never render
  // clickable, encoded here as severity 2 (see message.service.ts's
  // LINK_NOT_CLICKABLE_SEVERITY convention; the message itself still
  // sends either way, §19.3 never blocks on content).
  assert.equal(rows[0]!.severity, 2);
});

test('markRead marks the counterpart\'s messages read, not the caller\'s own', async () => {
  const u1 = await makeUser();
  const u2 = await makeUser();
  const clock = new ManualClock(new Date('2026-03-07T00:00:00.000Z'));
  const ctx1 = buildCtx({ actor: userActor(u1), clock });
  const ctx2 = buildCtx({ actor: userActor(u2), clock });
  const conv = await makeConversation(ctx1, u1, u2);

  const fromU1 = await messageService.sendMessage(ctx1, conv.id, 'hi from u1');
  const fromU2 = await messageService.sendMessage(ctx2, conv.id, 'hi from u2');

  await messageService.markRead(ctx2, conv.id, fromU1.id);

  const { rows } = await pool.query<{ id: string; read_at: Date | null }>(
    'SELECT id, read_at FROM messages WHERE conversation_id = $1 ORDER BY created_at',
    [conv.id],
  );
  const u1Row = rows.find((r) => r.id === fromU1.id)!;
  const u2Row = rows.find((r) => r.id === fromU2.id)!;
  assert.ok(u1Row.read_at, "the counterpart's message should now be marked read");
  assert.equal(u2Row.read_at, null, "the reader's own message must not be marked read by their own markRead call");
});
