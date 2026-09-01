/**
 * True concurrency tests for `dateProposal.service.ts`'s money-moving
 * state transitions (accept -> capture, cancel -> refund).
 *
 * test-audit.md Finding 3 named this gap directly: "a genuinely
 * concurrent double-accept (e.g. a client retry racing the original
 * request) is never tested for double-capture — only sequential
 * idempotent-retry ... is covered." Unlike `interest.service.ts` (see
 * `tests/concurrency/interestRace.test.ts`), `acceptDateProposal` and
 * `cancelDateProposal` are NOT single atomic CAS updates — they read the
 * proposal row, then perform several separately-committing checkpoints
 * (payment authorize/capture/refund calls), by design, for crash
 * resumability (see `dateProposal.service.ts`'s module header). Writing
 * this test for real (`Promise.allSettled`, not sequential `await`s)
 * surfaced a genuine double-capture/double-refund bug from that gap,
 * fixed in `dateProposal.service.ts` with a per-date-proposal
 * `pg_try_advisory_lock` (mirroring the one already-correct concurrency
 * pattern in this codebase, `src/jobs/scheduler.ts`). These tests are the
 * proof that fix holds, not merely that no exception escapes.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { ConflictError } from '../../src/lib/errors.js';
import { FakeProcessor } from '../../src/services/payments/fake.processor.js';
import * as dateProposalService from '../../src/services/dateProposal.service.js';
import * as ledgerService from '../../src/services/ledger.service.js';
import {
  setupTestDb,
  teardownTestDb,
  makeCtx,
  userActor,
  systemActor,
  createUser,
  createPaymentMethod,
  createConversation,
  createVenue,
  type TestDb,
} from '../unit/testHarness.js';

let db: TestDb;

before(async () => {
  db = await setupTestDb('concurrency_dateproposal');
});

after(async () => {
  await teardownTestDb(db);
});

interface Pair {
  proposerId: string;
  recipientId: string;
  conversationId: string;
  venueId: string;
  processor: FakeProcessor;
}

async function setupPair(): Promise<Pair> {
  const proposerId = await createUser(db);
  const recipientId = await createUser(db);
  await createPaymentMethod(db, proposerId, 'tok_good');
  await createPaymentMethod(db, recipientId, 'tok_good');
  const conversationId = await createConversation(db, proposerId, recipientId, 'active');
  const venueId = await createVenue(db);
  return { proposerId, recipientId, conversationId, venueId, processor: new FakeProcessor() };
}

function futureRange(hoursFromNow: number): { scheduledStart: Date; scheduledEnd: Date } {
  const start = new Date(db.clock.now().getTime() + hoursFromNow * 60 * 60 * 1000);
  return { scheduledStart: start, scheduledEnd: new Date(start.getTime() + 2 * 60 * 60 * 1000) };
}

async function captureLedgerTotal(dateProposalId: string, userId: string): Promise<number> {
  const ctx = makeCtx(db, systemActor());
  const entries = await ledgerService.listEntriesForDateProposal(ctx, dateProposalId);
  return entries
    .filter((e) => e.userId === userId)
    .reduce((sum, e) => {
      if (e.type === 'capture') return sum + e.amountCents;
      if (e.type === 'refund') return sum - e.amountCents;
      return sum;
    }, 0);
}

async function captureEntryCount(dateProposalId: string, userId: string): Promise<number> {
  const ctx = makeCtx(db, systemActor());
  const entries = await ledgerService.listEntriesForDateProposal(ctx, dateProposalId);
  return entries.filter((e) => e.userId === userId && e.type === 'capture').length;
}

test('concurrent accept of the SAME date proposal: exactly one winner reaches ticketed, no double-capture', async () => {
  const pair = await setupPair();
  const proposerCtx = makeCtx(db, userActor(pair.proposerId), { payments: pair.processor });
  const recipientCtx = makeCtx(db, userActor(pair.recipientId), { payments: pair.processor });

  const proposed = await dateProposalService.proposeDate(proposerCtx, {
    conversationId: pair.conversationId,
    venueId: pair.venueId,
    ...futureRange(72),
  });
  assert.equal(proposed.status, 'pending_acceptance');

  // Two concurrent "accept" calls for the same recipient — e.g. a
  // double-tap or a client retry racing the original request.
  const [a, b] = await Promise.allSettled([
    dateProposalService.acceptDateProposal(recipientCtx, proposed.id),
    dateProposalService.acceptDateProposal(recipientCtx, proposed.id),
  ]);

  const fulfilled = [a, b].filter((r) => r.status === 'fulfilled');
  const rejected = [a, b].filter((r) => r.status === 'rejected');
  assert.equal(fulfilled.length, 1, 'exactly one of the two concurrent accepts should actually run the accept flow');
  assert.equal(rejected.length, 1, 'the loser must fail fast with a typed conflict, not race the winner');
  assert.ok(
    (rejected[0] as PromiseRejectedResult).reason instanceof ConflictError,
    'the loser must get ConflictError (the per-date-proposal lock), not a silent no-op or a 500',
  );

  const finalStatus = (fulfilled[0] as PromiseFulfilledResult<Awaited<ReturnType<typeof dateProposalService.acceptDateProposal>>>).value.status;
  assert.equal(finalStatus, 'ticketed', 'the winner must have carried the flow all the way through to ticketed');

  const reloaded = await dateProposalService.getDateProposal(proposerCtx, proposed.id);
  assert.equal(reloaded.status, 'ticketed', 'the persisted state must agree with the winner — never stuck mid-flow, never double-applied');

  // The money assertion: each side captured EXACTLY ONCE, not twice.
  assert.equal(await captureEntryCount(proposed.id, pair.proposerId), 1, 'the proposer must be captured exactly once, never double-captured by the race');
  assert.equal(await captureEntryCount(proposed.id, pair.recipientId), 1, 'the recipient must be captured exactly once, never double-captured by the race');
  assert.equal(await captureLedgerTotal(proposed.id, pair.proposerId), 2000);
  assert.equal(await captureLedgerTotal(proposed.id, pair.recipientId), 2000);

  const { rows: vouchers } = await db.pool.query<{ count: string }>(
    `SELECT count(*)::text AS count FROM vouchers WHERE date_proposal_id = $1`,
    [proposed.id],
  );
  assert.equal(vouchers[0]!.count, '1', 'exactly one voucher must be issued, never two from a duplicated capture->ticket transition');
});

test('concurrent cancel of the SAME ticketed date proposal (full-refund window): exactly one refund is issued, never two', async () => {
  const pair = await setupPair();
  const proposerCtx = makeCtx(db, userActor(pair.proposerId), { payments: pair.processor });
  const recipientCtx = makeCtx(db, userActor(pair.recipientId), { payments: pair.processor });

  const { scheduledStart, scheduledEnd } = futureRange(100);
  const proposed = await dateProposalService.proposeDate(proposerCtx, { conversationId: pair.conversationId, venueId: pair.venueId, scheduledStart, scheduledEnd });
  const accepted = await dateProposalService.acceptDateProposal(recipientCtx, proposed.id);
  assert.equal(accepted.status, 'ticketed');

  // Move to exactly the full-refund boundary (>= cutoff hours out).
  db.clock.set(new Date(scheduledStart.getTime() - 24 * 60 * 60 * 1000));

  // Both participants race to cancel at once — a real scenario (either
  // side may cancel per §14.7) and the "refund plus cancel" race: the
  // winner's cancel must trigger the refund exactly once.
  const [a, b] = await Promise.allSettled([
    dateProposalService.cancelDateProposal(proposerCtx, proposed.id),
    dateProposalService.cancelDateProposal(recipientCtx, proposed.id),
  ]);

  const fulfilled = [a, b].filter((r) => r.status === 'fulfilled');
  const rejected = [a, b].filter((r) => r.status === 'rejected');
  assert.equal(fulfilled.length, 1, 'exactly one of the two concurrent cancels should actually run the cancel/refund flow');
  assert.equal(rejected.length, 1, 'the loser must fail fast with a typed conflict');
  assert.ok((rejected[0] as PromiseRejectedResult).reason instanceof ConflictError);

  const finalStatus = (fulfilled[0] as PromiseFulfilledResult<Awaited<ReturnType<typeof dateProposalService.cancelDateProposal>>>).value.status;
  assert.equal(finalStatus, 'refunded');

  // The money assertion: nets to zero, from EXACTLY one capture and
  // EXACTLY one refund per side — not a double-refund driving the ledger
  // negative, and not a no-op leaving money captured.
  const ctx = makeCtx(db, systemActor());
  const proposerEntries = await ledgerService.listEntriesForDateProposal(ctx, proposed.id);
  const proposerRefunds = proposerEntries.filter((e) => e.userId === pair.proposerId && e.type === 'refund');
  const recipientRefunds = proposerEntries.filter((e) => e.userId === pair.recipientId && e.type === 'refund');
  assert.equal(proposerRefunds.length, 1, 'the proposer must be refunded exactly once, never twice by the race');
  assert.equal(recipientRefunds.length, 1, 'the recipient must be refunded exactly once, never twice by the race');
  assert.equal(await captureLedgerTotal(proposed.id, pair.proposerId), 0, 'fully refunded nets to zero — not negative from a double-refund');
  assert.equal(await captureLedgerTotal(proposed.id, pair.recipientId), 0);
});
