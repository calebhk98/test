/**
 * §25.3 Chat Cooling/Archival job — the 72h/14d/21d thresholds and the
 * "never archive established" invariant (mirrors C-25.3.1, C-12.6.*,
 * C-12.6.4), run through the actual job function.
 */
import { test, before, after, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestDb, teardownTestDb, makeCtx, createUser, createConversation } from './testHarness.js';
import type { TestDb } from './testHarness.js';
import { runChatCoolingArchivalJob } from '../../src/jobs/chatDecay.job.js';

let db: TestDb;

before(async () => {
  db = await setupTestDb('chat_decay');
});

after(async () => {
  await teardownTestDb(db);
});

// This job scans EVERY active/cooling conversation in the database, so a
// prior test's fixture conversation (left in whatever state that test put
// it in) would otherwise keep contributing to later tests' aggregate
// prompted/cooled/archived counts (a "prompted" conversation in particular
// never changes persisted state, so it would silently re-count forever).
// Each test in this file gets a clean slate.
afterEach(async () => {
  await db.pool.query('DELETE FROM date_proposals');
  await db.pool.query('DELETE FROM messages');
  await db.pool.query('DELETE FROM conversations');
});

async function insertMessage(conversationId: string, senderId: string, createdAt: Date): Promise<void> {
  await db.pool.query(
    `INSERT INTO messages (conversation_id, sender_id, body, created_at, analysis_flags) VALUES ($1, $2, 'hi', $3, '[]'::jsonb)`,
    [conversationId, senderId, createdAt],
  );
}

test('72h since first message with no date proposal -> counted as "prompted", conversation stays active', async () => {
  const ctx = makeCtx(db);
  const a = await createUser(db);
  const b = await createUser(db);
  const conversationId = await createConversation(db, a, b, 'active');
  await insertMessage(conversationId, a, new Date(ctx.clock.now().getTime() - 73 * 60 * 60 * 1000));

  const result = await runChatCoolingArchivalJob(ctx);
  assert.equal(result.prompted, 1);
  assert.equal(result.cooled, 0);
  assert.equal(result.archived, 0);

  const { rows } = await db.pool.query<{ status: string }>(`SELECT status FROM conversations WHERE id = $1`, [conversationId]);
  assert.equal(rows[0]!.status, 'active');
});

test('14 days since first message with no date proposal -> cooling', async () => {
  const ctx = makeCtx(db);
  const a = await createUser(db);
  const b = await createUser(db);
  const conversationId = await createConversation(db, a, b, 'active');
  await insertMessage(conversationId, a, new Date(ctx.clock.now().getTime() - 14 * 24 * 60 * 60 * 1000));

  const result = await runChatCoolingArchivalJob(ctx);
  assert.equal(result.cooled, 1);

  const { rows } = await db.pool.query<{ status: string }>(`SELECT status FROM conversations WHERE id = $1`, [conversationId]);
  assert.equal(rows[0]!.status, 'cooling');
});

test('21 days since first message with no date proposal -> archived', async () => {
  const ctx = makeCtx(db);
  const a = await createUser(db);
  const b = await createUser(db);
  const conversationId = await createConversation(db, a, b, 'active');
  await insertMessage(conversationId, a, new Date(ctx.clock.now().getTime() - 21 * 24 * 60 * 60 * 1000));

  const result = await runChatCoolingArchivalJob(ctx);
  assert.equal(result.archived, 1);

  const { rows } = await db.pool.query<{ status: string; archived_at: Date }>(`SELECT status, archived_at FROM conversations WHERE id = $1`, [conversationId]);
  assert.equal(rows[0]!.status, 'archived');
  assert.ok(rows[0]!.archived_at);
});

test('C-12.6.4: an established conversation, even 100 days old with no proposal, is NEVER touched', async () => {
  const ctx = makeCtx(db);
  const a = await createUser(db);
  const b = await createUser(db);
  const conversationId = await createConversation(db, a, b, 'established');
  await insertMessage(conversationId, a, new Date(ctx.clock.now().getTime() - 100 * 24 * 60 * 60 * 1000));

  const result = await runChatCoolingArchivalJob(ctx);
  assert.equal(result.prompted, 0);
  assert.equal(result.cooled, 0);
  assert.equal(result.archived, 0);

  const { rows } = await db.pool.query<{ status: string }>(`SELECT status FROM conversations WHERE id = $1`, [conversationId]);
  assert.equal(rows[0]!.status, 'established');
});

test('a conversation with any date proposal on record is exempt from every threshold, regardless of age', async () => {
  const ctx = makeCtx(db);
  const a = await createUser(db);
  const b = await createUser(db);
  const conversationId = await createConversation(db, a, b, 'active');
  await insertMessage(conversationId, a, new Date(ctx.clock.now().getTime() - 30 * 24 * 60 * 60 * 1000));

  const venue = await db.pool.query<{ id: string }>(
    `INSERT INTO venues (name, address, latitude, longitude, category, active, margin_percent, time_slot_config, redemption_method)
     VALUES ('V', 'A', 0, 0, 'coffee', true, 10, '{"slots":[]}'::jsonb, 'qr_scan') RETURNING id`,
  );
  await db.pool.query(
    `INSERT INTO date_proposals (conversation_id, proposer_id, recipient_id, venue_id, scheduled_start, scheduled_end, status, policy_snapshot, escrow_amount_cents)
     VALUES ($1, $2, $3, $4, now() + interval '1 day', now() + interval '1 day 1 hour', 'pending_acceptance', '{}'::jsonb, 2000)`,
    [conversationId, a, b, venue.rows[0]!.id],
  );

  const result = await runChatCoolingArchivalJob(ctx);
  assert.equal(result.prompted, 0);
  assert.equal(result.cooled, 0);
  assert.equal(result.archived, 0);
});

test('idempotent re-run: an already-cooling conversation is not re-processed into a duplicate notification/effect', async () => {
  const ctx = makeCtx(db);
  const a = await createUser(db);
  const b = await createUser(db);
  const conversationId = await createConversation(db, a, b, 'active');
  await insertMessage(conversationId, a, new Date(ctx.clock.now().getTime() - 15 * 24 * 60 * 60 * 1000));

  const first = await runChatCoolingArchivalJob(ctx);
  assert.equal(first.cooled, 1);
  const second = await runChatCoolingArchivalJob(ctx);
  assert.equal(second.cooled, 0, 'already-cooling conversation must not be re-cooled');

  const { rows } = await db.pool.query<{ status: string }>(`SELECT status FROM conversations WHERE id = $1`, [conversationId]);
  assert.equal(rows[0]!.status, 'cooling');
});
