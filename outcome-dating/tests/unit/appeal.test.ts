import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import * as appeal from '../../src/services/appeal.service.js';
import * as moderation from '../../src/services/moderation.service.js';
import {
  setupTestDatabase,
  teardownTestDatabase,
  buildCtx,
  userActor,
  insertUser,
  insertPaymentMethod,
} from './testCtxAgentE.js';
import { ManualClock } from '../../src/lib/time.js';

before(async () => {
  await setupTestDatabase('appeal');
});

after(async () => {
  await teardownTestDatabase();
});

async function shadowbanUser(ctx: Awaited<ReturnType<typeof buildCtx>>, userId: string): Promise<void> {
  await moderation.recordAutomatedFlag(ctx, { userId, signalType: 'device_reputation', weight: 80 });
  const action = await moderation.applyThresholds(ctx, userId);
  assert.equal(action?.action, 'shadowban');
}

// =====================================================================
// Passing appeal.
// =====================================================================
test('submitAppeal: payment_verification passes and restores a shadowbanned account', async () => {
  const clock = new ManualClock(new Date());
  const setupCtx = buildCtx({ clock });
  const userId = await insertUser(setupCtx);
  await shadowbanUser(setupCtx, userId);
  assert.equal(await moderation.isVisibleInDiscovery(setupCtx, userId), false);

  clock.advanceHours(25); // clear the default 24h appeal cooldown
  const paymentMethodId = await insertPaymentMethod(setupCtx, userId, { verified: true });

  const userCtx = buildCtx({ actor: userActor(userId), clock });
  const result = await appeal.submitAppeal(userCtx, { method: 'payment_verification', evidence: { paymentMethodId } });

  assert.equal(result.status, 'approved');
  assert.equal(result.resolvedAt !== null, true);
  assert.equal(await moderation.isVisibleInDiscovery(setupCtx, userId), true, 'a passed appeal must restore discovery visibility');
});

test('submitAppeal: liveness_check passes with a positive liveness result', async () => {
  const clock = new ManualClock(new Date());
  const setupCtx = buildCtx({ clock });
  const userId = await insertUser(setupCtx);
  await shadowbanUser(setupCtx, userId);
  clock.advanceHours(25);

  const userCtx = buildCtx({ actor: userActor(userId), clock });
  const result = await appeal.submitAppeal(userCtx, { method: 'liveness_check', evidence: { livenessSessionId: 'sess_1', passed: true } });
  assert.equal(result.status, 'approved');
});

// =====================================================================
// Failing appeal.
// =====================================================================
test('submitAppeal: fails and maintains the restriction when the automated signal does not verify', async () => {
  const clock = new ManualClock(new Date());
  const setupCtx = buildCtx({ clock });
  const userId = await insertUser(setupCtx);
  await shadowbanUser(setupCtx, userId);
  clock.advanceHours(25);

  const userCtx = buildCtx({ actor: userActor(userId), clock });
  const result = await appeal.submitAppeal(userCtx, { method: 'liveness_check', evidence: { livenessSessionId: 'sess_1', passed: false } });

  assert.equal(result.status, 'rejected');
  assert.equal(await moderation.isVisibleInDiscovery(setupCtx, userId), false, 'a failed appeal must NOT restore the account');
});

test('submitAppeal: payment_verification fails for an unverified payment method', async () => {
  const clock = new ManualClock(new Date());
  const setupCtx = buildCtx({ clock });
  const userId = await insertUser(setupCtx);
  await shadowbanUser(setupCtx, userId);
  clock.advanceHours(25);
  const unverifiedPaymentMethodId = await insertPaymentMethod(setupCtx, userId, { verified: false });

  const userCtx = buildCtx({ actor: userActor(userId), clock });
  const result = await appeal.submitAppeal(userCtx, { method: 'payment_verification', evidence: { paymentMethodId: unverifiedPaymentMethodId } });
  assert.equal(result.status, 'rejected');
});

test('a rejected appeal does not itself add a new negative trust event', async () => {
  const clock = new ManualClock(new Date());
  const setupCtx = buildCtx({ clock });
  const userId = await insertUser(setupCtx);
  await shadowbanUser(setupCtx, userId);
  clock.advanceHours(25);

  const { rows: before } = await setupCtx.db.query('SELECT count(*)::int AS count FROM trust_events WHERE user_id = $1', [userId]);

  const userCtx = buildCtx({ actor: userActor(userId), clock });
  await appeal.submitAppeal(userCtx, { method: 'liveness_check', evidence: { passed: false } });

  const { rows: after } = await setupCtx.db.query('SELECT count(*)::int AS count FROM trust_events WHERE user_id = $1', [userId]);
  assert.equal(after[0]!.count, before[0]!.count, 'a rejected appeal must not write any new trust_events row');
});

// =====================================================================
// Cooldown / rate limiting.
// =====================================================================
test('checkCooldownElapsed: false immediately after a moderation action, true once the configured cooldown passes', async () => {
  const clock = new ManualClock(new Date());
  const ctx = buildCtx({ clock });
  const userId = await insertUser(ctx);
  await shadowbanUser(ctx, userId);

  assert.equal(await appeal.checkCooldownElapsed(ctx, userId), false);
  clock.advanceHours(23);
  assert.equal(await appeal.checkCooldownElapsed(ctx, userId), false);
  clock.advanceHours(2); // total 25h > default 24h cooldown
  assert.equal(await appeal.checkCooldownElapsed(ctx, userId), true);
});

test('submitAppeal is rejected with a rate-limit error before the cooldown elapses', async () => {
  const clock = new ManualClock(new Date());
  const setupCtx = buildCtx({ clock });
  const userId = await insertUser(setupCtx);
  await shadowbanUser(setupCtx, userId);

  const userCtx = buildCtx({ actor: userActor(userId), clock });
  await assert.rejects(() => appeal.submitAppeal(userCtx, { method: 'liveness_check', evidence: { passed: true } }));
});

test('repeated failed appeals are rate-limited: a second attempt right after a rejection is blocked until the cooldown elapses again', async () => {
  const clock = new ManualClock(new Date());
  const setupCtx = buildCtx({ clock });
  const userId = await insertUser(setupCtx);
  await shadowbanUser(setupCtx, userId);
  clock.advanceHours(25);

  const userCtx = buildCtx({ actor: userActor(userId), clock });
  const first = await appeal.submitAppeal(userCtx, { method: 'liveness_check', evidence: { passed: false } });
  assert.equal(first.status, 'rejected');

  // Immediately try again — must be blocked by the cooldown anchored on
  // the just-rejected appeal, not just the original moderation action.
  await assert.rejects(() => appeal.submitAppeal(userCtx, { method: 'liveness_check', evidence: { livenessSessionId: 'sess_2', passed: true } }));

  clock.advanceHours(25);
  const second = await appeal.submitAppeal(userCtx, { method: 'liveness_check', evidence: { livenessSessionId: 'sess_2', passed: true } });
  assert.equal(second.status, 'approved');
});

// =====================================================================
// No human step anywhere.
// =====================================================================
test('submitAppeal never returns a pending appeal — every result is already a terminal approved/rejected decision', async () => {
  const clock = new ManualClock(new Date());
  const setupCtx = buildCtx({ clock });
  const userId = await insertUser(setupCtx);
  await shadowbanUser(setupCtx, userId);
  clock.advanceHours(25);

  const userCtx = buildCtx({ actor: userActor(userId), clock });
  const result = await appeal.submitAppeal(userCtx, { method: 'cooldown' });
  assert.notEqual(result.status, 'pending');
  assert.ok(result.status === 'approved' || result.status === 'rejected');
});

test('getMyLatestAppeal returns null when the user has never appealed, then the most recent appeal after one', async () => {
  const clock = new ManualClock(new Date());
  const setupCtx = buildCtx({ clock });
  const userId = await insertUser(setupCtx);
  const userCtx = buildCtx({ actor: userActor(userId), clock });

  assert.equal(await appeal.getMyLatestAppeal(userCtx), null);

  await shadowbanUser(setupCtx, userId);
  clock.advanceHours(25);
  await appeal.submitAppeal(userCtx, { method: 'cooldown' });

  const latest = await appeal.getMyLatestAppeal(userCtx);
  assert.ok(latest);
  assert.equal(latest?.userId, userId);
});
