/**
 * Unit tests for Layer 3 — the retroactive auto-decline sweep
 * (`interest.service.ts#sweepAutoDeclineForRecipient` /
 * `sweepAutoDeclineAll`), built on the same
 * `eligibility.service.ts#evaluateMutualEligibility` Layers 1/2 use.
 * Own database (`odate_elig_autodecline`) — see `testCtxEligibility.ts`.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import * as interestService from '../../src/services/interest.service.js';
import { ManualClock } from '../../src/lib/time.js';
import type { Ctx } from '../../src/lib/ctx.js';
import {
  setupTestDatabase,
  teardownTestDatabase,
  buildCtx,
  userActor,
  makeUser,
  setHardFilter,
  setSelfAnswer,
  getTestPool,
} from './testCtxEligibility.js';

let clock: ManualClock;

before(async () => {
  await setupTestDatabase('autodecline');
  clock = new ManualClock(new Date('2026-01-01T00:00:00.000Z'));
});

after(async () => {
  await teardownTestDatabase();
});

function ctxFor(userId: string): Ctx {
  return buildCtx({ actor: userActor(userId), clock });
}

async function interestStatus(id: string): Promise<{ status: string; declineOrigin: string | null; declinedAt: Date | null }> {
  const { rows } = await getTestPool().query<{ status: string; decline_origin: string | null; declined_at: Date | null }>(
    `SELECT status, decline_origin, declined_at FROM interests WHERE id = $1`,
    [id],
  );
  const row = rows[0]!;
  return { status: row.status, declineOrigin: row.decline_origin, declinedAt: row.declined_at };
}

async function outgoingPendingCount(userId: string): Promise<number> {
  const { rows } = await getTestPool().query<{ count: string }>(
    `SELECT count(*)::text AS count FROM interests WHERE sender_id = $1 AND status = 'pending'`,
    [userId],
  );
  return Number(rows[0]!.count);
}

async function trustScore(userId: string): Promise<number> {
  const { rows } = await getTestPool().query<{ trust_score: number }>(`SELECT trust_score FROM users WHERE id = $1`, [
    userId,
  ]);
  return rows[0]!.trust_score;
}

// =====================================================================
// Core behavior: filter change auto-declines exactly the now-ineligible
// pending interests, leaves the eligible ones alone.
// =====================================================================

test('sweepAutoDeclineForRecipient: declines exactly the interests the recipient\'s NEW filter now excludes, leaves the rest pending', async () => {
  const pool = getTestPool();
  const recipient = await makeUser(pool, { age: 30 });
  const senderNowExcluded = await makeUser(pool, { age: 30 });
  const senderStillEligible = await makeUser(pool, { age: 30 });
  await setSelfAnswer(pool, senderNowExcluded, 'has_children', 5); // "has kids"
  await setSelfAnswer(pool, senderStillEligible, 'has_children', 1); // "no kids"

  // Both interests sent BEFORE the recipient had any filter at all — both legitimately eligible at send time.
  const iExcluded = await interestService.sendInterest(ctxFor(senderNowExcluded), recipient);
  const iEligible = await interestService.sendInterest(ctxFor(senderStillEligible), recipient);
  assert.equal(iExcluded.status, 'pending');
  assert.equal(iEligible.status, 'pending');

  // Recipient now sets a deal-breaker filter that retroactively excludes senderNowExcluded.
  await setHardFilter(pool, recipient, 'has_children', 'lte', 2);

  const result = await interestService.sweepAutoDeclineForRecipient(ctxFor(recipient), recipient);
  assert.equal(result.declined, 1);

  const excludedRow = await interestStatus(iExcluded.id);
  assert.equal(excludedRow.status, 'declined');
  assert.equal(excludedRow.declineOrigin, 'auto');
  assert.ok(excludedRow.declinedAt);

  const eligibleRow = await interestStatus(iEligible.id);
  assert.equal(eligibleRow.status, 'pending', 'still-eligible interest must survive untouched');
  assert.equal(eligibleRow.declineOrigin, null);
});

test('an interest that was eligible when sent and REMAINS eligible survives a sweep completely untouched', async () => {
  const pool = getTestPool();
  const recipient = await makeUser(pool, { age: 30 });
  const sender = await makeUser(pool, { age: 30 });
  await setSelfAnswer(pool, sender, 'has_children', 1);
  await setHardFilter(pool, recipient, 'has_children', 'lte', 2);

  const interest = await interestService.sendInterest(ctxFor(sender), recipient);
  const before = await interestStatus(interest.id);

  const result = await interestService.sweepAutoDeclineForRecipient(ctxFor(recipient), recipient);
  assert.equal(result.declined, 0);

  const after = await interestStatus(interest.id);
  assert.deepEqual(after, before);
});

// =====================================================================
// Distinguishable from a human decline; sender never learns which.
// =====================================================================

test('a human decline is stamped decline_origin = "human", distinct from an auto-decline', async () => {
  const pool = getTestPool();
  const recipient = await makeUser(pool, { age: 30 });
  const sender = await makeUser(pool, { age: 30 });
  const interest = await interestService.sendInterest(ctxFor(sender), recipient);
  await interestService.declineInterest(ctxFor(recipient), interest.id);

  const row = await interestStatus(interest.id);
  assert.equal(row.status, 'declined');
  assert.equal(row.declineOrigin, 'human');
});

test('the sender-visible Interest shape never carries decline_origin — auto vs human is not observable via listOutgoing', async () => {
  const pool = getTestPool();
  const recipient = await makeUser(pool, { age: 30 });
  const sender = await makeUser(pool, { age: 30 });
  await setSelfAnswer(pool, sender, 'has_children', 5);
  const interest = await interestService.sendInterest(ctxFor(sender), recipient);
  await setHardFilter(pool, recipient, 'has_children', 'lte', 2);
  await interestService.sweepAutoDeclineForRecipient(ctxFor(recipient), recipient);

  const { items } = await interestService.listOutgoing(ctxFor(sender));
  const mine = items.find((i) => i.id === interest.id);
  assert.ok(mine);
  assert.equal(mine.status, 'declined');
  assert.equal('declineOrigin' in mine, false, 'declineOrigin must never appear on the sender-facing Interest object');
});

// =====================================================================
// Sender's slot is freed; sender's trust is not harmed.
// =====================================================================

test('auto-decline frees the sender\'s outgoing slot, exactly like any other decline', async () => {
  const pool = getTestPool();
  const recipient = await makeUser(pool, { age: 30 });
  const sender = await makeUser(pool, { age: 30 });
  await setSelfAnswer(pool, sender, 'has_children', 5);

  const interest = await interestService.sendInterest(ctxFor(sender), recipient);
  assert.equal(await outgoingPendingCount(sender), 1);

  await setHardFilter(pool, recipient, 'has_children', 'lte', 2);
  await interestService.sweepAutoDeclineForRecipient(ctxFor(recipient), recipient);

  assert.equal(await outgoingPendingCount(sender), 0);
  const row = await interestStatus(interest.id);
  assert.equal(row.status, 'declined');
});

test('auto-decline does NOT harm the sender\'s trust score', async () => {
  const pool = getTestPool();
  const recipient = await makeUser(pool, { age: 30 });
  const sender = await makeUser(pool, { age: 30 });
  await setSelfAnswer(pool, sender, 'has_children', 5);

  const before = await trustScore(sender);
  await interestService.sendInterest(ctxFor(sender), recipient);
  await setHardFilter(pool, recipient, 'has_children', 'lte', 2);
  await interestService.sweepAutoDeclineForRecipient(ctxFor(recipient), recipient);
  const after = await trustScore(sender);

  assert.equal(after, before, 'an auto-decline must never move the sender\'s trust score');
});

// =====================================================================
// Idempotency.
// =====================================================================

test('sweepAutoDeclineForRecipient is idempotent: re-running changes nothing further', async () => {
  const pool = getTestPool();
  const recipient = await makeUser(pool, { age: 30 });
  const senderA = await makeUser(pool, { age: 30 });
  const senderB = await makeUser(pool, { age: 30 });
  await setSelfAnswer(pool, senderA, 'has_children', 5);
  await setSelfAnswer(pool, senderB, 'has_children', 4);

  const iA = await interestService.sendInterest(ctxFor(senderA), recipient);
  const iB = await interestService.sendInterest(ctxFor(senderB), recipient);
  await setHardFilter(pool, recipient, 'has_children', 'lte', 2);

  const first = await interestService.sweepAutoDeclineForRecipient(ctxFor(recipient), recipient);
  assert.equal(first.declined, 2);

  const rowAAfterFirst = await interestStatus(iA.id);
  const rowBAfterFirst = await interestStatus(iB.id);

  const second = await interestService.sweepAutoDeclineForRecipient(ctxFor(recipient), recipient);
  assert.equal(second.declined, 0, 're-running must not re-decline (or double-count) already-declined rows');

  assert.deepEqual(await interestStatus(iA.id), rowAAfterFirst);
  assert.deepEqual(await interestStatus(iB.id), rowBAfterFirst);
});

test('sweepAutoDeclineForRecipient never touches a non-pending interest (accepted survives a would-be-excluding filter change)', async () => {
  const pool = getTestPool();
  const recipient = await makeUser(pool, { age: 30 });
  const sender = await makeUser(pool, { age: 30 });
  await setSelfAnswer(pool, sender, 'has_children', 5);

  const interest = await interestService.sendInterest(ctxFor(sender), recipient);
  const { interest: accepted } = await interestService.acceptInterest(ctxFor(recipient), interest.id);
  assert.equal(accepted.status, 'accepted');

  // Recipient tightens filters AFTER already accepting — spec §30.7.1:
  // existing matches must not be retroactively affected.
  await setHardFilter(pool, recipient, 'has_children', 'lte', 2);
  const result = await interestService.sweepAutoDeclineForRecipient(ctxFor(recipient), recipient);
  assert.equal(result.declined, 0);

  const row = await interestStatus(interest.id);
  assert.equal(row.status, 'accepted');
});

// =====================================================================
// sweepAutoDeclineAll — the periodic/all-recipients variant.
// =====================================================================

test('sweepAutoDeclineAll sweeps every recipient with a pending interest, and is itself idempotent', async () => {
  const pool = getTestPool();
  const recipient1 = await makeUser(pool, { age: 30 });
  const recipient2 = await makeUser(pool, { age: 30 });
  const sender1 = await makeUser(pool, { age: 30 });
  const sender2 = await makeUser(pool, { age: 30 });
  await setSelfAnswer(pool, sender1, 'has_children', 5);
  await setSelfAnswer(pool, sender2, 'has_children', 5);

  await interestService.sendInterest(ctxFor(sender1), recipient1);
  await interestService.sendInterest(ctxFor(sender2), recipient2);
  await setHardFilter(pool, recipient1, 'has_children', 'lte', 2);
  await setHardFilter(pool, recipient2, 'has_children', 'lte', 2);

  const sysCtx = buildCtx({ actor: { type: 'system', job: 'eligibility_sweep' }, clock });
  const first = await interestService.sweepAutoDeclineAll(sysCtx);
  assert.equal(first.declined, 2);
  assert.ok(first.recipientsSwept >= 2);

  const second = await interestService.sweepAutoDeclineAll(sysCtx);
  assert.equal(second.declined, 0);
});

// =====================================================================
// Driven by a controllable clock (no wall-clock reads).
// =====================================================================

test('sweep uses ctx.clock for declined_at, not the wall clock', async () => {
  const pool = getTestPool();
  const recipient = await makeUser(pool, { age: 30 });
  const sender = await makeUser(pool, { age: 30 });
  await setSelfAnswer(pool, sender, 'has_children', 5);

  const localClock = new ManualClock(new Date('2030-06-15T00:00:00.000Z'));
  const senderCtx = buildCtx({ actor: userActor(sender), clock: localClock });
  const recipientCtx = buildCtx({ actor: userActor(recipient), clock: localClock });

  const interest = await interestService.sendInterest(senderCtx, recipient);
  await setHardFilter(pool, recipient, 'has_children', 'lte', 2);
  localClock.advanceHours(5);

  await interestService.sweepAutoDeclineForRecipient(recipientCtx, recipient);
  const row = await interestStatus(interest.id);
  assert.equal(row.declinedAt?.toISOString(), localClock.now().toISOString());
});
