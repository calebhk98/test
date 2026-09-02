/**
 * CC-6: "An established conversation is NEVER archived, put into cooling,
 * or otherwise decayed by any background job, ever, no matter how much
 * time passes," plus the full §12.6 decay ladder (72h prompt / 14d
 * cooling / 21d archived) at each named boundary, §12.7's "established
 * conversations don't count against chat.active_limit," and §30.4's
 * "a shadowbanned person keeps their existing conversations."
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { setupConformanceDb, teardownConformanceDb, makeCtx, userActor, systemActor, createUser, createConversation, rawRow, type TestDb } from './support.js';
import * as conversationService from '../../src/services/conversation.service.js';
import * as moderationService from '../../src/services/moderation.service.js';
import * as discoveryService from '../../src/services/discovery.service.js';

let db: TestDb;

before(async () => {
  db = await setupConformanceDb('convolifecycle');
});

after(async () => {
  await teardownConformanceDb(db);
});

async function firstMessageAt(conversationId: string, senderId: string, at: Date): Promise<void> {
  await db.pool.query(`INSERT INTO messages (conversation_id, sender_id, body, created_at) VALUES ($1, $2, 'hi', $3)`, [conversationId, senderId, at]);
}

test('C-12.6.1: 72h after the first message with no date proposal -> date-prompt notification, conversation remains active', async () => {
  const a = await createUser(db);
  const b = await createUser(db);
  const conversationId = await createConversation(db, a, b, 'active');
  await firstMessageAt(conversationId, a, db.clock.now());

  db.clock.advanceHours(72);
  const systemCtx = makeCtx(db, systemActor('chat_decay'));
  const result = await conversationService.runChatDecayJob(systemCtx);
  assert.ok(result.prompted >= 1, 'the date-prompt notification path must fire at the 72h mark');

  const row = await rawRow<{ status: string }>(db, `SELECT status FROM conversations WHERE id = $1`, [conversationId]);
  assert.equal(row?.status, 'active', 'the 72h prompt is a notification only, not a status change');
});

test('C-12.6.2: 14 days with no date proposal -> conversation moves to cooling', async () => {
  const a = await createUser(db);
  const b = await createUser(db);
  const conversationId = await createConversation(db, a, b, 'active');
  await firstMessageAt(conversationId, a, db.clock.now());

  db.clock.advanceDays(13);
  const systemCtx = makeCtx(db, systemActor('chat_decay'));
  let result = await conversationService.runChatDecayJob(systemCtx);
  assert.equal(result.cooled, 0, 'must not cool a day early');
  let row = await rawRow<{ status: string }>(db, `SELECT status FROM conversations WHERE id = $1`, [conversationId]);
  assert.equal(row?.status, 'active');

  db.clock.advanceDays(1); // exactly 14 days
  result = await conversationService.runChatDecayJob(systemCtx);
  assert.equal(result.cooled, 1);
  row = await rawRow<{ status: string }>(db, `SELECT status FROM conversations WHERE id = $1`, [conversationId]);
  assert.equal(row?.status, 'cooling');
});

test('C-12.6.3: 21 days with no date proposal -> conversation is archived', async () => {
  const a = await createUser(db);
  const b = await createUser(db);
  const conversationId = await createConversation(db, a, b, 'active');
  await firstMessageAt(conversationId, a, db.clock.now());

  db.clock.advanceDays(20);
  const systemCtx = makeCtx(db, systemActor('chat_decay'));
  let result = await conversationService.runChatDecayJob(systemCtx);
  assert.equal(result.archived, 0, 'must not archive a day early');

  db.clock.advanceDays(1); // exactly 21 days
  result = await conversationService.runChatDecayJob(systemCtx);
  assert.equal(result.archived, 1);
  const row = await rawRow<{ status: string }>(db, `SELECT status FROM conversations WHERE id = $1`, [conversationId]);
  assert.equal(row?.status, 'archived');
});

test('CC-6 / C-12.6.4 / C-12.7.1: an established conversation never decays, no matter how far the clock advances or how many times the job runs', async () => {
  const a = await createUser(db);
  const b = await createUser(db);
  const conversationId = await createConversation(db, a, b, 'active');
  await firstMessageAt(conversationId, a, db.clock.now());
  const systemCtx = makeCtx(db, systemActor('chat_decay'));

  const established = await conversationService.establishConversation(systemCtx, conversationId);
  assert.equal(established.status, 'established');

  // Run the job repeatedly, advancing the clock far past every decay
  // threshold each time.
  for (let i = 0; i < 5; i++) {
    db.clock.advanceDays(100);
    await conversationService.runChatDecayJob(systemCtx);
    const row = await rawRow<{ status: string }>(db, `SELECT status FROM conversations WHERE id = $1`, [conversationId]);
    assert.equal(row?.status, 'established', `must still be established after ${(i + 1) * 100} more days and ${i + 1} job runs`);
  }
});

test('C-12.7.2: established conversations do not count against chat.active_limit', async () => {
  const userId = await createUser(db);
  const systemCtx = makeCtx(db, systemActor('conformance-test'));

  for (let i = 0; i < 15; i++) {
    const other = await createUser(db);
    const conversationId = await createConversation(db, userId, other, 'active');
    await conversationService.establishConversation(systemCtx, conversationId);
  }
  const activeCount = await conversationService.countActiveConversationsForUser(systemCtx, userId);
  assert.equal(activeCount, 0, '15 ESTABLISHED conversations must not count toward the active-conversation capacity at all');

  // A brand-new (non-established) conversation on top of those 15 must
  // still be possible, proving the count genuinely excludes them rather
  // than merely reporting 0 by coincidence.
  const freshOther = await createUser(db);
  const freshConversationId = await createConversation(db, userId, freshOther, 'active');
  const activeCountAfter = await conversationService.countActiveConversationsForUser(systemCtx, userId);
  assert.equal(activeCountAfter, 1);
  assert.ok(freshConversationId);
});

test('C-12.7.3: an established conversation only changes via an explicit user action (archive), never a background job', async () => {
  const a = await createUser(db);
  const b = await createUser(db);
  const conversationId = await createConversation(db, a, b, 'active');
  const systemCtx = makeCtx(db, systemActor('conformance-test'));
  await conversationService.establishConversation(systemCtx, conversationId);

  const userCtx = makeCtx(db, userActor(a));
  const archived = await conversationService.archiveConversation(userCtx, conversationId);
  assert.equal(archived.status, 'archived', 'an explicit user action CAN move an established conversation, unlike any background job');
});

test('C-30.4.1 / C-18.4.6: a shadowbanned person keeps their existing conversations, and can still use them, but is not shown to others as a new candidate', async () => {
  const a = await createUser(db); // will be shadowbanned
  const b = await createUser(db);
  const conversationId = await createConversation(db, a, b, 'active');
  await firstMessageAt(conversationId, b, db.clock.now());

  const systemCtx = makeCtx(db, systemActor('conformance-test'));
  await moderationService.recordAutomatedFlag(systemCtx, { userId: a, signalType: 'user_report', weight: 85, metadata: {} }); // clears the shadowban threshold (default 80)
  const action = await moderationService.applyThresholds(systemCtx, a);
  assert.equal(action?.action, 'shadowban');

  const row = await rawRow<{ status: string; shadowbanned: boolean }>(db, `SELECT status, shadowbanned FROM users WHERE id = $1`, [a]);
  assert.equal(row?.shadowbanned, true);

  // The conversation itself is untouched.
  const convoRow = await rawRow<{ status: string }>(db, `SELECT status FROM conversations WHERE id = $1`, [conversationId]);
  assert.equal(convoRow?.status, 'active', 'an existing conversation must survive a shadowban applied to one participant');

  // A can still list/use it.
  const listed = await conversationService.listMyConversations(makeCtx(db, userActor(a)));
  assert.ok(listed.some((c) => c.id === conversationId));

  // But A is not shown to others as a NEW candidate (same underlying gate as C-10.2.2).
  const bCtx = makeCtx(db, userActor(b));
  assert.equal(await discoveryService.isProfileVisibleTo(bCtx, b, a), false);
});
