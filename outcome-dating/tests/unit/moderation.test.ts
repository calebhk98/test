import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import * as moderation from '../../src/services/moderation.service.js';
import * as report from '../../src/services/report.service.js';
import {
  setupTestDatabase,
  teardownTestDatabase,
  buildCtx,
  userActor,
  insertUser,
  insertConversation,
} from './testCtxAgentE.js';

before(async () => {
  await setupTestDatabase('moderation');
});

after(async () => {
  await teardownTestDatabase();
});

test('computeModerationScore sums every recorded automated flag for the user', async () => {
  const ctx = buildCtx();
  const userId = await insertUser(ctx);

  await moderation.recordAutomatedFlag(ctx, { userId, signalType: 'device_reputation', weight: 30 });
  await moderation.recordAutomatedFlag(ctx, { userId, signalType: 'message_velocity', weight: 25 });

  assert.equal(await moderation.computeModerationScore(ctx, userId), 55);
});

// =====================================================================
// Threshold crossings at exactly the configured 50 / 80 (spec §21.4
// defaults: moderation.auto_restriction_score=50, ..._shadowban_score=80).
// =====================================================================
test('applyThresholds: score of exactly 50 crosses into restriction; 49 does not', async () => {
  const ctx = buildCtx();

  const atThreshold = await insertUser(ctx);
  await moderation.recordAutomatedFlag(ctx, { userId: atThreshold, signalType: 'device_reputation', weight: 50 });
  const atResult = await moderation.applyThresholds(ctx, atThreshold);
  assert.equal(atResult?.action, 'restriction');

  const belowThreshold = await insertUser(ctx);
  await moderation.recordAutomatedFlag(ctx, { userId: belowThreshold, signalType: 'device_reputation', weight: 49 });
  const belowResult = await moderation.applyThresholds(ctx, belowThreshold);
  assert.notEqual(belowResult?.action, 'restriction');
  assert.notEqual(belowResult?.action, 'shadowban');
  assert.notEqual(belowResult?.action, 'suspension');
});

test('applyThresholds: score of exactly 80 crosses into shadowban; 79 stays at restriction', async () => {
  const ctx = buildCtx();

  const atThreshold = await insertUser(ctx);
  await moderation.recordAutomatedFlag(ctx, { userId: atThreshold, signalType: 'device_reputation', weight: 80 });
  const atResult = await moderation.applyThresholds(ctx, atThreshold);
  assert.equal(atResult?.action, 'shadowban');
  assert.equal(await moderation.isVisibleInDiscovery(ctx, atThreshold), false);

  const belowThreshold = await insertUser(ctx);
  await moderation.recordAutomatedFlag(ctx, { userId: belowThreshold, signalType: 'device_reputation', weight: 79 });
  const belowResult = await moderation.applyThresholds(ctx, belowThreshold);
  assert.equal(belowResult?.action, 'restriction');
  assert.equal(await moderation.isVisibleInDiscovery(ctx, belowThreshold), true);
});

test('applyThresholds: crossing auto_suspension_score suspends the account', async () => {
  const ctx = buildCtx();
  const userId = await insertUser(ctx);
  await moderation.recordAutomatedFlag(ctx, { userId, signalType: 'device_reputation', weight: 95 });
  const result = await moderation.applyThresholds(ctx, userId);
  assert.equal(result?.action, 'suspension');
  assert.equal(await moderation.isVisibleInDiscovery(ctx, userId), false);
});

test('applyThresholds: thresholds are config-driven, not hardcoded', async () => {
  const ctx = buildCtx({ actor: { type: 'admin', adminId: 'admin-1' } });
  await ctx.config.set('moderation.auto_restriction_score', 10, 'test-admin');

  const userId = await insertUser(ctx);
  await moderation.recordAutomatedFlag(ctx, { userId, signalType: 'device_reputation', weight: 12 });
  const result = await moderation.applyThresholds(ctx, userId);
  assert.equal(result?.action, 'restriction');
});

test('applyThresholds only escalates: a second call at the same score is a no-op', async () => {
  const ctx = buildCtx();
  const userId = await insertUser(ctx);
  await moderation.recordAutomatedFlag(ctx, { userId, signalType: 'device_reputation', weight: 55 });

  const first = await moderation.applyThresholds(ctx, userId);
  assert.equal(first?.action, 'restriction');

  const second = await moderation.applyThresholds(ctx, userId);
  assert.equal(second, null, 'already at/above the warranted action must return null, not a duplicate action');
});

// =====================================================================
// §18.3/§18.5 "minor suspected" = maximum severity, immediate protective
// action, SAF-1 FIX: a single report no longer instantly suspends
// anyone; see report.service.ts's "SAF-1 FIX" module doc for the full
// corroboration model, and tests/unit/safetyFixes.test.ts for the
// exhaustive both-directions proof this brief requires. These two tests
// just keep this file's own suite honest about the new contract.
// =====================================================================
test('minor_suspected: a single report, even from a well-established, trusted, matched reporter, applies the fast interim restriction, never an immediate suspension', async () => {
  const ctx = buildCtx();
  const longAgo = new Date(Date.now() - 90 * 24 * 60 * 60 * 1000);
  const reporterId = await insertUser(ctx, { trustLevel: 'elite', createdAt: longAgo });
  const reportedId = await insertUser(ctx);
  await insertConversation(ctx, reporterId, reportedId); // established relationship, as credible a lone report as this system can produce
  const reporterCtx = buildCtx({ actor: userActor(reporterId, 'elite') });

  await report.submitReport(reporterCtx, { reportedId, category: 'minor_suspected' });

  const page = await moderation.listModerationActions(ctx, reportedId);
  assert.equal(page.items[0]?.action, 'restriction', 'one report must never terminate an account, however credible its reporter');
  assert.equal(page.items[0]?.reason, 'minor_suspected_report_interim_protective_action');
  // Restriction is real and immediate (reduced visibility), not a no-op:
  assert.equal(await moderation.isVisibleInDiscovery(ctx, reportedId), true, 'restriction alone does not hide from discovery, only shadowban/suspension do; the protective effect here is the interest/link restriction trust.service enforces');
});

test('minor_suspected: two independent, non-clustered, credible reporters escalate straight to suspension on the second report', async () => {
  const ctx = buildCtx();
  const reportedId = await insertUser(ctx);

  // Deliberately spaced createdAt (well outside the anti-brigading
  // account-creation-proximity window) and no shared device/IP/
  // conversation between the two reporters, two GENUINELY independent
  // people, not a brigade wearing two accounts.
  const reporter1 = await insertUser(ctx, { trustLevel: 'trusted', createdAt: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000) });
  const reporter1Ctx = buildCtx({ actor: userActor(reporter1, 'trusted') });
  await report.submitReport(reporter1Ctx, { reportedId, category: 'minor_suspected' });
  assert.equal((await moderation.listModerationActions(ctx, reportedId)).items[0]?.action, 'restriction');

  const reporter2 = await insertUser(ctx, { trustLevel: 'trusted', createdAt: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000) });
  const reporter2Ctx = buildCtx({ actor: userActor(reporter2, 'trusted') });
  await report.submitReport(reporter2Ctx, { reportedId, category: 'minor_suspected' });

  const page = await moderation.listModerationActions(ctx, reportedId);
  assert.equal(page.items[0]?.action, 'suspension', 'a second, independent, credible corroborating report must escalate fast, same call, no waiting');
  assert.equal(page.items[0]?.reason, 'minor_suspected_report_immediate_protective_action');
  assert.equal(await moderation.isVisibleInDiscovery(ctx, reportedId), false);
});

// =====================================================================
// §30.4, a shadowban must not touch existing conversations.
// =====================================================================
test('shadowban cuts discovery visibility but leaves an existing conversation completely intact', async () => {
  const ctx = buildCtx();
  const userA = await insertUser(ctx);
  const userB = await insertUser(ctx);
  const conversationId = await insertConversation(ctx, userA, userB);

  const before = await ctx.db.query('SELECT status, created_at FROM conversations WHERE id = $1', [conversationId]);

  await moderation.recordAutomatedFlag(ctx, { userId: userA, signalType: 'device_reputation', weight: 80 });
  const result = await moderation.applyThresholds(ctx, userA);
  assert.equal(result?.action, 'shadowban');

  assert.equal(await moderation.isVisibleInDiscovery(ctx, userA), false);

  const after = await ctx.db.query('SELECT status, created_at FROM conversations WHERE id = $1', [conversationId]);
  assert.deepEqual(after.rows[0], before.rows[0], 'shadowban must not mutate the conversation row at all');
});

// =====================================================================
// Zero human moderation (spec §18.1, Definition of Done #17).
// =====================================================================
test('the action pipeline reaches a terminal automated decision with no human input, in one synchronous call', async () => {
  const ctx = buildCtx();
  const userId = await insertUser(ctx);
  await moderation.recordAutomatedFlag(ctx, { userId, signalType: 'device_reputation', weight: 60 });

  const result = await moderation.applyThresholds(ctx, userId);
  assert.ok(result);
  // A terminal decision from the fixed, closed action set, never
  // something queue-shaped like "pending_review".
  assert.ok(['warning', 'restriction', 'shadowban', 'suspension'].includes(result.action));
});

test('the moderation_actions schema itself has no human-review-queue state, inserting one is rejected', async () => {
  const ctx = buildCtx();
  const userId = await insertUser(ctx);
  await assert.rejects(
    ctx.db.query(`INSERT INTO moderation_actions (user_id, action, reason, score) VALUES ($1, 'pending_review', 'x', 0)`, [userId]),
  );
});

test('runModerationRecalculation evaluates every flagged/reported user and applies warranted actions with no human step', async () => {
  const ctx = buildCtx();
  const userId = await insertUser(ctx);
  await moderation.recordAutomatedFlag(ctx, { userId, signalType: 'device_reputation', weight: 55 });

  const result = await moderation.runModerationRecalculation(ctx);
  assert.ok(result.usersEvaluated >= 1);
  assert.ok(result.actionsApplied >= 1);
  assert.equal(await moderation.isVisibleInDiscovery(ctx, userId), true); // restriction only, not shadowban/suspension
});

test('listModerationActions supports the admin view-only path (spec §4.3, viewing is never required for the system to function)', async () => {
  const ctx = buildCtx();
  const userId = await insertUser(ctx);
  await moderation.recordAutomatedFlag(ctx, { userId, signalType: 'device_reputation', weight: 55 });
  await moderation.applyThresholds(ctx, userId);

  const adminCtx = buildCtx({ actor: { type: 'admin', adminId: 'admin-1' } });
  const page = await moderation.listModerationActions(adminCtx, userId);
  assert.equal(page.items.length, 1);
  assert.equal(page.items[0]?.userId, userId);
});
