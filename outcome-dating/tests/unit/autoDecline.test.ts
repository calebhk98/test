/**
 * Unit tests for the opt-in pending-interest cleanup
 * (`interest.service.ts#previewFilterCleanup` / `runFilterCleanup`),
 * built on the same `eligibility.service.ts#evaluateMutualEligibility`
 * Layer 2 uses. Own database (`odate_elig_autodecline`) — see
 * `testCtxEligibility.ts`.
 *
 * ---------------------------------------------------------------------
 * PRODUCT-OWNER CORRECTION — read this before changing anything here:
 * ---------------------------------------------------------------------
 * This file used to test a THIRD enforcement layer: `sweepAutoDecline-
 * ForRecipient`/`sweepAutoDeclineAll`, which auto-declined a recipient's
 * PENDING incoming interests the instant their filters changed —
 * intended to run automatically, inline, right after every filter save.
 * That was wrong: people narrow and widen their filters for ordinary
 * reasons, and doing so must never destroy a pending like or put a
 * conversation at risk. That automatic behavior has been removed.
 *
 * The FIRST test below used to be named
 * "sweepAutoDeclineForRecipient: declines exactly the interests the
 * recipient's NEW filter now excludes, leaves the rest pending" and
 * asserted the opposite of what it asserts now — it drove a filter
 * change straight into an auto-decline and checked that the excluded
 * interest ended up 'declined'. It has been INVERTED: it now drives the
 * exact same filter change through the real `filter.service#updateMyFilters`
 * call and asserts every pending interest — the one the new filter would
 * exclude included — is still 'pending' afterward, because a filter
 * change alone must never decline anything. See
 * 'a filter change alone never declines anything — every pending
 * interest survives, `updateMyFilters` has no such side effect' below.
 *
 * What the old sweep was ever actually FOR (keeping a recipient's NEW
 * incoming likes close to a "yes") is Layer 2's job — see
 * `eligibility.test.ts` — and is untouched by this correction: Layer 2
 * only ever refuses a send that has not happened yet.
 *
 * The remaining capability — a user who genuinely wants to tidy their
 * inbox after narrowing their filters — survives as `previewFilterCleanup`
 * (read-only count, so the UI can say "this would decline N" before
 * anyone confirms) and `runFilterCleanup` (the actual decline), both
 * scoped to the calling user's own inbox, both callable ONLY by explicit
 * user action (see `src/http/routes/filters.routes.ts`'s
 * `/me/filters/cleanup*` routes) — never from a filter update, never
 * from a job. `sweepAutoDeclineAll` (the periodic/all-recipients variant)
 * has been deleted outright: there is no longer any background sweep for
 * it to serve, and a per-user opt-in action has no "all recipients" form.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import * as interestService from '../../src/services/interest.service.js';
import * as filterService from '../../src/services/filter.service.js';
import * as conversationService from '../../src/services/conversation.service.js';
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
// INVERTED (see file-level "PRODUCT-OWNER CORRECTION" note): a filter
// change, on its own, must never decline anything.
// =====================================================================

test('a filter change alone never declines anything — every pending interest survives, `updateMyFilters` has no such side effect', async () => {
  const pool = getTestPool();
  const recipient = await makeUser(pool, { age: 30 });
  const senderWouldNowFail = await makeUser(pool, { age: 30 });
  const senderStillEligible = await makeUser(pool, { age: 30 });
  await setSelfAnswer(pool, senderWouldNowFail, 'has_children', 5); // "has kids"
  await setSelfAnswer(pool, senderStillEligible, 'has_children', 1); // "no kids"

  // Both interests sent BEFORE the recipient had any filter at all — both legitimately eligible at send time.
  const iWouldNowFail = await interestService.sendInterest(ctxFor(senderWouldNowFail), recipient);
  const iEligible = await interestService.sendInterest(ctxFor(senderStillEligible), recipient);
  assert.equal(iWouldNowFail.status, 'pending');
  assert.equal(iEligible.status, 'pending');

  // Recipient saves a deal-breaker filter, via the REAL service call,
  // that would exclude senderWouldNowFail were a new interest sent today.
  await filterService.updateMyFilters(ctxFor(recipient), [
    { filterKey: 'has_children', operator: 'lte', value: 2, enabled: true },
  ]);

  // Nothing about either interest changed. No decline, no notification,
  // no trust impact — `updateMyFilters` touched only `hard_filters`.
  const stillFailsRow = await interestStatus(iWouldNowFail.id);
  assert.equal(stillFailsRow.status, 'pending', 'the now-excluded interest must remain pending — a filter change must never auto-decline it');
  assert.equal(stillFailsRow.declineOrigin, null);
  assert.equal(stillFailsRow.declinedAt, null);

  const eligibleRow = await interestStatus(iEligible.id);
  assert.equal(eligibleRow.status, 'pending');
  assert.equal(eligibleRow.declineOrigin, null);

  // A fresh Layer-2 preview of the same recipient's inbox nonetheless
  // shows the mismatch is real (proves this isn't passing merely because
  // the filter never took effect) — it just isn't acted on automatically.
  const preview = await interestService.previewFilterCleanup(ctxFor(recipient));
  assert.equal(preview.wouldDecline, 1, 'the filter really did take effect — the cleanup preview can see the now-ineligible interest, it just was not auto-run');
});

test('changing filters never touches a conversation: an already-accepted interest and its conversation survive a filter change that would exclude the other party', async () => {
  const pool = getTestPool();
  const recipient = await makeUser(pool, { age: 30 });
  const sender = await makeUser(pool, { age: 30 });
  await setSelfAnswer(pool, sender, 'has_children', 5);

  const interest = await interestService.sendInterest(ctxFor(sender), recipient);
  const { conversation } = await interestService.acceptInterest(ctxFor(recipient), interest.id);

  await filterService.updateMyFilters(ctxFor(recipient), [
    { filterKey: 'has_children', operator: 'lte', value: 2, enabled: true },
  ]);

  const row = await interestStatus(interest.id);
  assert.equal(row.status, 'accepted', 'an accepted interest must never be touched by a filter change');

  const fetchedConversation = await conversationService.getConversation(ctxFor(recipient), conversation.id);
  assert.equal(fetchedConversation.id, conversation.id, 'the conversation must still exist after the filter change');
});

// =====================================================================
// previewFilterCleanup — read-only, tells the user the count BEFORE
// anything is declined.
// =====================================================================

test('previewFilterCleanup reports how many pending interests would be declined, and mutates nothing', async () => {
  const pool = getTestPool();
  const recipient = await makeUser(pool, { age: 30 });
  const senderNowExcluded = await makeUser(pool, { age: 30 });
  const senderStillEligible = await makeUser(pool, { age: 30 });
  await setSelfAnswer(pool, senderNowExcluded, 'has_children', 5);
  await setSelfAnswer(pool, senderStillEligible, 'has_children', 1);

  const iExcluded = await interestService.sendInterest(ctxFor(senderNowExcluded), recipient);
  const iEligible = await interestService.sendInterest(ctxFor(senderStillEligible), recipient);
  await setHardFilter(pool, recipient, 'has_children', 'lte', 2);

  const preview = await interestService.previewFilterCleanup(ctxFor(recipient));
  assert.equal(preview.wouldDecline, 1);

  // Calling preview again changes nothing — it never writes.
  const previewAgain = await interestService.previewFilterCleanup(ctxFor(recipient));
  assert.equal(previewAgain.wouldDecline, 1);

  const excludedRow = await interestStatus(iExcluded.id);
  assert.equal(excludedRow.status, 'pending', 'preview must never decline anything itself');
  assert.equal(excludedRow.declineOrigin, null);

  const eligibleRow = await interestStatus(iEligible.id);
  assert.equal(eligibleRow.status, 'pending');
});

// =====================================================================
// runFilterCleanup — the explicit, user-invoked decline.
// =====================================================================

test('runFilterCleanup: declines exactly the pending interests the CALLING user\'s current filters exclude, leaves the rest pending', async () => {
  const pool = getTestPool();
  const recipient = await makeUser(pool, { age: 30 });
  const senderNowExcluded = await makeUser(pool, { age: 30 });
  const senderStillEligible = await makeUser(pool, { age: 30 });
  await setSelfAnswer(pool, senderNowExcluded, 'has_children', 5); // "has kids"
  await setSelfAnswer(pool, senderStillEligible, 'has_children', 1); // "no kids"

  const iExcluded = await interestService.sendInterest(ctxFor(senderNowExcluded), recipient);
  const iEligible = await interestService.sendInterest(ctxFor(senderStillEligible), recipient);
  assert.equal(iExcluded.status, 'pending');
  assert.equal(iEligible.status, 'pending');

  await setHardFilter(pool, recipient, 'has_children', 'lte', 2);

  // The user previews first (what the UI would show before confirming)...
  const preview = await interestService.previewFilterCleanup(ctxFor(recipient));
  assert.equal(preview.wouldDecline, 1);

  // ...then deliberately confirms.
  const result = await interestService.runFilterCleanup(ctxFor(recipient));
  assert.equal(result.declined, 1);

  const excludedRow = await interestStatus(iExcluded.id);
  assert.equal(excludedRow.status, 'declined');
  assert.equal(excludedRow.declineOrigin, 'auto');
  assert.ok(excludedRow.declinedAt);

  const eligibleRow = await interestStatus(iEligible.id);
  assert.equal(eligibleRow.status, 'pending', 'still-eligible interest must survive untouched');
  assert.equal(eligibleRow.declineOrigin, null);
});

test('an interest that was eligible when sent and REMAINS eligible survives runFilterCleanup completely untouched', async () => {
  const pool = getTestPool();
  const recipient = await makeUser(pool, { age: 30 });
  const sender = await makeUser(pool, { age: 30 });
  await setSelfAnswer(pool, sender, 'has_children', 1);
  await setHardFilter(pool, recipient, 'has_children', 'lte', 2);

  const interest = await interestService.sendInterest(ctxFor(sender), recipient);
  const before = await interestStatus(interest.id);

  const result = await interestService.runFilterCleanup(ctxFor(recipient));
  assert.equal(result.declined, 0);

  const after = await interestStatus(interest.id);
  assert.deepEqual(after, before);
});

// =====================================================================
// Distinguishable from a human decline; sender never learns which.
// =====================================================================

test('a human decline is stamped decline_origin = "human", distinct from a cleanup decline', async () => {
  const pool = getTestPool();
  const recipient = await makeUser(pool, { age: 30 });
  const sender = await makeUser(pool, { age: 30 });
  const interest = await interestService.sendInterest(ctxFor(sender), recipient);
  await interestService.declineInterest(ctxFor(recipient), interest.id);

  const row = await interestStatus(interest.id);
  assert.equal(row.status, 'declined');
  assert.equal(row.declineOrigin, 'human');
});

test('the sender-visible Interest shape never carries decline_origin — cleanup vs human is not observable via listOutgoing', async () => {
  const pool = getTestPool();
  const recipient = await makeUser(pool, { age: 30 });
  const sender = await makeUser(pool, { age: 30 });
  await setSelfAnswer(pool, sender, 'has_children', 5);
  const interest = await interestService.sendInterest(ctxFor(sender), recipient);
  await setHardFilter(pool, recipient, 'has_children', 'lte', 2);
  await interestService.runFilterCleanup(ctxFor(recipient));

  const { items } = await interestService.listOutgoing(ctxFor(sender));
  const mine = items.find((i) => i.id === interest.id);
  assert.ok(mine);
  assert.equal(mine.status, 'declined');
  assert.equal('declineOrigin' in mine, false, 'declineOrigin must never appear on the sender-facing Interest object');
});

// =====================================================================
// Sender's slot is freed; sender's trust is not harmed.
// =====================================================================

test('runFilterCleanup frees the sender\'s outgoing slot, exactly like any other decline', async () => {
  const pool = getTestPool();
  const recipient = await makeUser(pool, { age: 30 });
  const sender = await makeUser(pool, { age: 30 });
  await setSelfAnswer(pool, sender, 'has_children', 5);

  const interest = await interestService.sendInterest(ctxFor(sender), recipient);
  assert.equal(await outgoingPendingCount(sender), 1);

  await setHardFilter(pool, recipient, 'has_children', 'lte', 2);
  await interestService.runFilterCleanup(ctxFor(recipient));

  assert.equal(await outgoingPendingCount(sender), 0);
  const row = await interestStatus(interest.id);
  assert.equal(row.status, 'declined');
});

test('runFilterCleanup does NOT harm the sender\'s trust score', async () => {
  const pool = getTestPool();
  const recipient = await makeUser(pool, { age: 30 });
  const sender = await makeUser(pool, { age: 30 });
  await setSelfAnswer(pool, sender, 'has_children', 5);

  const before = await trustScore(sender);
  await interestService.sendInterest(ctxFor(sender), recipient);
  await setHardFilter(pool, recipient, 'has_children', 'lte', 2);
  await interestService.runFilterCleanup(ctxFor(recipient));
  const after = await trustScore(sender);

  assert.equal(after, before, 'a cleanup decline must never move the sender\'s trust score');
});

// =====================================================================
// Idempotency.
// =====================================================================

test('runFilterCleanup is idempotent: re-running changes nothing further', async () => {
  const pool = getTestPool();
  const recipient = await makeUser(pool, { age: 30 });
  const senderA = await makeUser(pool, { age: 30 });
  const senderB = await makeUser(pool, { age: 30 });
  await setSelfAnswer(pool, senderA, 'has_children', 5);
  await setSelfAnswer(pool, senderB, 'has_children', 4);

  const iA = await interestService.sendInterest(ctxFor(senderA), recipient);
  const iB = await interestService.sendInterest(ctxFor(senderB), recipient);
  await setHardFilter(pool, recipient, 'has_children', 'lte', 2);

  const first = await interestService.runFilterCleanup(ctxFor(recipient));
  assert.equal(first.declined, 2);

  const rowAAfterFirst = await interestStatus(iA.id);
  const rowBAfterFirst = await interestStatus(iB.id);

  const second = await interestService.runFilterCleanup(ctxFor(recipient));
  assert.equal(second.declined, 0, 're-running must not re-decline (or double-count) already-declined rows');

  assert.deepEqual(await interestStatus(iA.id), rowAAfterFirst);
  assert.deepEqual(await interestStatus(iB.id), rowBAfterFirst);
});

test('runFilterCleanup never touches a non-pending interest (accepted survives a would-be-excluding filter change)', async () => {
  const pool = getTestPool();
  const recipient = await makeUser(pool, { age: 30 });
  const sender = await makeUser(pool, { age: 30 });
  await setSelfAnswer(pool, sender, 'has_children', 5);

  const interest = await interestService.sendInterest(ctxFor(sender), recipient);
  const { interest: accepted } = await interestService.acceptInterest(ctxFor(recipient), interest.id);
  assert.equal(accepted.status, 'accepted');

  // Recipient tightens filters AFTER already accepting — an existing
  // match must not be retroactively affected, cleanup included.
  await setHardFilter(pool, recipient, 'has_children', 'lte', 2);
  const result = await interestService.runFilterCleanup(ctxFor(recipient));
  assert.equal(result.declined, 0);

  const row = await interestStatus(interest.id);
  assert.equal(row.status, 'accepted');
});

test('runFilterCleanup only ever acts on the CALLING user\'s own inbox — it takes no recipientId to point at someone else\'s', async () => {
  const pool = getTestPool();
  const recipient = await makeUser(pool, { age: 30 });
  const otherUser = await makeUser(pool, { age: 30 });
  const sender = await makeUser(pool, { age: 30 });
  await setSelfAnswer(pool, sender, 'has_children', 5);

  const interest = await interestService.sendInterest(ctxFor(sender), recipient);
  await setHardFilter(pool, recipient, 'has_children', 'lte', 2);

  // otherUser has a pending interest of their own, unaffected by
  // recipient's filter — running cleanup as otherUser must not touch
  // recipient's inbox at all.
  const result = await interestService.runFilterCleanup(ctxFor(otherUser));
  assert.equal(result.declined, 0);

  const row = await interestStatus(interest.id);
  assert.equal(row.status, 'pending', 'cleanup run by a different user must never affect recipient\'s inbox');
});

// =====================================================================
// Driven by a controllable clock (no wall-clock reads).
// =====================================================================

test('runFilterCleanup uses ctx.clock for declined_at, not the wall clock', async () => {
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

  await interestService.runFilterCleanup(recipientCtx);
  const row = await interestStatus(interest.id);
  assert.equal(row.declinedAt?.toISOString(), localClock.now().toISOString());
});

// =====================================================================
// The scenario the product owner specifically asked to be proven: narrow
// drastically, then widen back — pending interests and conversations
// intact the entire time.
// =====================================================================

test('narrowing filters drastically and then widening them back again leaves every pending interest AND every conversation intact throughout', async () => {
  const pool = getTestPool();
  const recipient = await makeUser(pool, { age: 30 });

  // Three senders: one the recipient will go on to accept (a real
  // conversation at stake), two who stay pending throughout.
  const senderToAccept = await makeUser(pool, { age: 30 });
  const senderPendingA = await makeUser(pool, { age: 30 });
  const senderPendingB = await makeUser(pool, { age: 30 });
  await setSelfAnswer(pool, senderToAccept, 'has_children', 5);
  await setSelfAnswer(pool, senderPendingA, 'has_children', 5);
  await setSelfAnswer(pool, senderPendingB, 'has_children', 1);

  const interestToAccept = await interestService.sendInterest(ctxFor(senderToAccept), recipient);
  const interestPendingA = await interestService.sendInterest(ctxFor(senderPendingA), recipient);
  const interestPendingB = await interestService.sendInterest(ctxFor(senderPendingB), recipient);

  const { conversation } = await interestService.acceptInterest(ctxFor(recipient), interestToAccept.id);

  async function assertEverythingIntact(): Promise<void> {
    const acceptedRow = await interestStatus(interestToAccept.id);
    assert.equal(acceptedRow.status, 'accepted');

    const pendingARow = await interestStatus(interestPendingA.id);
    assert.equal(pendingARow.status, 'pending');
    assert.equal(pendingARow.declineOrigin, null);

    const pendingBRow = await interestStatus(interestPendingB.id);
    assert.equal(pendingBRow.status, 'pending');
    assert.equal(pendingBRow.declineOrigin, null);

    const fetchedConversation = await conversationService.getConversation(ctxFor(recipient), conversation.id);
    assert.equal(fetchedConversation.id, conversation.id, 'conversation must exist');
  }

  await assertEverythingIntact();

  // 1) Narrow drastically: a deal-breaker filter that would exclude BOTH
  // remaining pending senders (and would have excluded the now-accepted
  // one too, were it evaluated) if it were ever applied to them.
  await filterService.updateMyFilters(ctxFor(recipient), [
    { filterKey: 'has_children', operator: 'lte', value: -1, enabled: true }, // excludes every possible self_value (1-5)
  ]);
  await assertEverythingIntact();

  // A preview at this point proves the narrowing genuinely took effect —
  // both pending interests WOULD be declined by an explicit cleanup —
  // it just wasn't run.
  const previewAfterNarrow = await interestService.previewFilterCleanup(ctxFor(recipient));
  assert.equal(previewAfterNarrow.wouldDecline, 2);
  await assertEverythingIntact();

  // 2) Narrow again, differently (overwriting the same filter key, plus
  // adding a second deal-breaker) — still nothing touched.
  await filterService.updateMyFilters(ctxFor(recipient), [
    { filterKey: 'has_children', operator: 'eq', value: 999, enabled: true },
    { filterKey: 'age_min', operator: 'gte', value: 90, enabled: true },
  ]);
  await assertEverythingIntact();

  // 3) Widen back out: disable/relax every filter again.
  await filterService.updateMyFilters(ctxFor(recipient), [
    { filterKey: 'has_children', operator: 'gte', value: 0, enabled: false },
    { filterKey: 'age_min', operator: 'gte', value: 0, enabled: false },
  ]);
  await assertEverythingIntact();

  // Widened back out: the cleanup preview now agrees nothing would even
  // be declined if the user chose to run it.
  const previewAfterWiden = await interestService.previewFilterCleanup(ctxFor(recipient));
  assert.equal(previewAfterWiden.wouldDecline, 0);
  await assertEverythingIntact();

  // And the pending interests are still fully actionable — the recipient
  // can still accept one, proving they were never silently harmed.
  const { interest: acceptedB, conversation: conversationB } = await interestService.acceptInterest(
    ctxFor(recipient),
    interestPendingB.id,
  );
  assert.equal(acceptedB.status, 'accepted');
  assert.ok(conversationB.id);
});
