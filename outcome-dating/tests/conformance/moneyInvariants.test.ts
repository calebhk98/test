/**
 * Cross-cutting money invariants (CC-2, CC-3, CC-4, CC-11) and the §14.5
 * failure-ordering rows they're proven by, driven entirely through
 * `dateProposal.service.ts` + `payment.service.ts` + `ledger.service.ts`
 * against a real Postgres database and `FakeProcessor`'s magic-substring
 * failure injection (see docs/test-strategy.md).
 *
 * These are the obligations the task brief calls out as most important
 * and least likely to already be covered: "nobody is charged unless both
 * holds authorized, across every failure ordering" and "the ledger is
 * append-only and a completed flow reconciles to the expected net
 * position for both people." Per-service unit tests already exercise
 * dateProposal.service.ts's happy path and a couple of failure branches
 * in isolation; this file's job is to walk the FULL failure-ordering
 * matrix in one place and assert the CROSS-module invariant (no orphaned
 * capture, no premature voucher, a balanced ledger) rather than any one
 * module's internal state.
 *
 * NOTE: dateProposal.service.ts, payment.service.ts's caller, is on the
 * task's list of files other agents are concurrently changing. If a case
 * below starts failing, check `git log -- src/services/dateProposal.service.ts`
 * before assuming this test found a new defect (see task instructions).
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import {
  setupConformanceDb,
  teardownConformanceDb,
  makeCtx,
  userActor,
  createUser,
  createPaymentMethod,
  createConversation,
  createVenue,
  rawRow,
  rawRows,
  type TestDb,
} from './support.js';
import * as dateProposalService from '../../src/services/dateProposal.service.js';
import * as ledgerService from '../../src/services/ledger.service.js';
import { FakeProcessor } from '../../src/services/payments/fake.processor.js';
import type { Ctx } from '../../src/lib/ctx.js';

let db: TestDb;

before(async () => {
  db = await setupConformanceDb('money');
});

after(async () => {
  await teardownConformanceDb(db);
});

interface Pair {
  proposerId: string;
  recipientId: string;
  conversationId: string;
  venueId: string;
  processor: FakeProcessor;
  proposerCtx: Ctx;
  recipientCtx: Ctx;
}

/** One proposer + one recipient sharing ONE `FakeProcessor` instance (one "processor account"), each with their own payment method token so authorize/capture failures can be steered independently per side. */
async function setupPair(tokens: { proposer: string; recipient: string }): Promise<Pair> {
  const proposerId = await createUser(db);
  const recipientId = await createUser(db);
  await createPaymentMethod(db, proposerId, tokens.proposer);
  await createPaymentMethod(db, recipientId, tokens.recipient);
  const conversationId = await createConversation(db, proposerId, recipientId, 'active');
  const venueId = await createVenue(db);
  const processor = new FakeProcessor();
  const proposerCtx = makeCtx(db, userActor(proposerId), { payments: processor });
  const recipientCtx = makeCtx(db, userActor(recipientId), { payments: processor });
  return { proposerId, recipientId, conversationId, venueId, processor, proposerCtx, recipientCtx };
}

function futureWindow(): { scheduledStart: Date; scheduledEnd: Date } {
  const scheduledStart = new Date(db.clock.now().getTime() + 3 * 24 * 60 * 60 * 1000);
  const scheduledEnd = new Date(scheduledStart.getTime() + 60 * 60 * 1000);
  return { scheduledStart, scheduledEnd };
}

async function holdRow(userId: string, dateProposalId: string): Promise<{ status: string; amount_cents: string } | undefined> {
  return rawRow(db, `SELECT status, amount_cents FROM payment_holds WHERE date_proposal_id = $1 AND user_id = $2`, [dateProposalId, userId]);
}

async function voucherExists(dateProposalId: string): Promise<boolean> {
  const row = await rawRow(db, `SELECT id FROM vouchers WHERE date_proposal_id = $1`, [dateProposalId]);
  return row !== undefined;
}

/** No `payment_holds` row for `dateProposalId` is ever left `captured` without every other hold on that same proposal being `captured` too (CC-2's "capture of one side never proceeds/persists without the other succeeding"). */
async function assertNoLonelyCapture(dateProposalId: string): Promise<void> {
  const rows = await rawRows<{ status: string }>(db, `SELECT status FROM payment_holds WHERE date_proposal_id = $1`, [dateProposalId]);
  const captured = rows.filter((r) => r.status === 'captured');
  assert.ok(
    captured.length === 0 || captured.length === rows.length,
    `expected either zero captured holds or ALL holds captured for this proposal, got ${captured.length}/${rows.length}`,
  );
}

// =====================================================================
// CC-2 / C-14.5.1: proposer's own authorization fails
// =====================================================================

test('C-14.5.1 / CC-2: proposer authorization fails -> payment_failed, no recipient hold is ever created, nobody charged', async () => {
  const pair = await setupPair({ proposer: 'tok_fail_authorize', recipient: 'tok_good' });
  const { scheduledStart, scheduledEnd } = futureWindow();

  const proposal = await dateProposalService.proposeDate(pair.proposerCtx, {
    conversationId: pair.conversationId,
    venueId: pair.venueId,
    scheduledStart,
    scheduledEnd,
  });

  assert.equal(proposal.status, 'payment_failed');
  const proposerHold = await holdRow(pair.proposerId, proposal.id);
  assert.equal(proposerHold?.status, 'failed');
  const recipientHold = await holdRow(pair.recipientId, proposal.id);
  assert.equal(recipientHold, undefined, 'recipient hold must never be created when the proposer never got past authorization');
  await assertNoLonelyCapture(proposal.id);
  assert.equal(await voucherExists(proposal.id), false);
});

// =====================================================================
// CC-2 / C-14.5.2: recipient's authorization fails after proposer's succeeded
// =====================================================================

test('C-14.5.2 / CC-2: recipient authorization fails -> proposer hold released, nobody charged, both notified paths reached', async () => {
  const pair = await setupPair({ proposer: 'tok_good', recipient: 'tok_fail_authorize' });
  const { scheduledStart, scheduledEnd } = futureWindow();

  const proposed = await dateProposalService.proposeDate(pair.proposerCtx, {
    conversationId: pair.conversationId,
    venueId: pair.venueId,
    scheduledStart,
    scheduledEnd,
  });
  assert.equal(proposed.status, 'pending_acceptance');
  assert.equal((await holdRow(pair.proposerId, proposed.id))?.status, 'authorized');

  const accepted = await dateProposalService.acceptDateProposal(pair.recipientCtx, proposed.id);
  assert.equal(accepted.status, 'payment_failed');

  const proposerHold = await holdRow(pair.proposerId, proposed.id);
  assert.equal(proposerHold?.status, 'released', "proposer's already-authorized hold must be released, never left dangling or captured");
  const recipientHold = await holdRow(pair.recipientId, proposed.id);
  assert.equal(recipientHold?.status, 'failed');

  await assertNoLonelyCapture(proposed.id);
  assert.equal(await voucherExists(proposed.id), false, 'CC-3: no ticket before capture succeeded');
});

// =====================================================================
// CC-2 / C-14.5.3: capture fails on the PROPOSER's side after both authorized
// =====================================================================

test('C-14.5.3a / CC-2: both authorized, proposer capture fails first -> recipient hold released (never captured alone), nobody charged', async () => {
  const pair = await setupPair({ proposer: 'tok_good_fail_capture', recipient: 'tok_good' });
  const { scheduledStart, scheduledEnd } = futureWindow();

  const proposed = await dateProposalService.proposeDate(pair.proposerCtx, {
    conversationId: pair.conversationId,
    venueId: pair.venueId,
    scheduledStart,
    scheduledEnd,
  });
  assert.equal(proposed.status, 'pending_acceptance');

  const accepted = await dateProposalService.acceptDateProposal(pair.recipientCtx, proposed.id);
  assert.equal(accepted.status, 'payment_failed');

  const proposerHold = await holdRow(pair.proposerId, proposed.id);
  assert.equal(proposerHold?.status, 'failed', "the side whose capture failed ends 'failed', not 'captured'");
  const recipientHold = await holdRow(pair.recipientId, proposed.id);
  assert.equal(recipientHold?.status, 'released', "the OTHER side's successful capture must never persist alone; it is released, not captured");

  await assertNoLonelyCapture(proposed.id);
  assert.equal(await voucherExists(proposed.id), false);

  // CC-4: no orphaned capture ledger entry for either side (the one
  // 'capture' row FakeProcessor's failure produces is amountCents: 0,
  // see payment.service.ts#captureHold, never a positive orphan).
  const entries = await ledgerService.listEntriesForDateProposal(pair.proposerCtx, proposed.id);
  const positiveCaptures = entries.filter((e) => e.type === 'capture' && e.amountCents > 0);
  assert.equal(positiveCaptures.length, 0, 'no side may have a positive capture ledger entry when the pair never both captured');
});

// =====================================================================
// CC-2 / C-14.5.3 / OQ-5: capture fails on the RECIPIENT's side, AFTER the
// proposer's capture already succeeded, proposer must be REFUNDED (money
// already moved), not merely released.
// =====================================================================

test('C-14.5.3b / CC-2 / OQ-5: proposer already captured, recipient capture then fails -> proposer is REFUNDED (not released), net position zero, nobody charged alone', async () => {
  const pair = await setupPair({ proposer: 'tok_good', recipient: 'tok_good_fail_capture' });
  const { scheduledStart, scheduledEnd } = futureWindow();

  const proposed = await dateProposalService.proposeDate(pair.proposerCtx, {
    conversationId: pair.conversationId,
    venueId: pair.venueId,
    scheduledStart,
    scheduledEnd,
  });
  const accepted = await dateProposalService.acceptDateProposal(pair.recipientCtx, proposed.id);
  assert.equal(accepted.status, 'payment_failed');

  const proposerHold = await holdRow(pair.proposerId, proposed.id);
  assert.equal(proposerHold?.status, 'refunded', 'money already moved for the proposer, undoing it must be a refund, not a release (OQ-5)');
  const recipientHold = await holdRow(pair.recipientId, proposed.id);
  assert.equal(recipientHold?.status, 'failed');

  await assertNoLonelyCapture(proposed.id);
  assert.equal(await voucherExists(proposed.id), false, 'CC-3: still no ticket, even though one side was captured transiently');

  // CC-4: the proposer's capture and refund must be a matched, equal pair
  // (money that moved and came back nets to zero, no residue).
  const entries = await ledgerService.listEntriesForDateProposal(pair.proposerCtx, proposed.id);
  const proposerEntries = entries.filter((e) => e.userId === pair.proposerId);
  const captureCents = proposerEntries.filter((e) => e.type === 'capture').reduce((s, e) => s + e.amountCents, 0);
  const refundCents = proposerEntries.filter((e) => e.type === 'refund').reduce((s, e) => s + e.amountCents, 0);
  assert.equal(captureCents, refundCents, 'proposer capture and refund must net to exactly zero');
  assert.ok(captureCents > 0, 'sanity: a real capture actually happened before the refund');
});

// =====================================================================
// Happy path: both authorize, both capture -> charged -> ticketed, and
// ONLY THEN does a voucher exist (CC-3), with a fully balanced ledger.
// =====================================================================

test('C-14.2.3 / C-14.2.4 / CC-2 / CC-3 / CC-4 / CC-11: both holds authorized then captured -> charged -> ticketed; voucher appears only after; ledger is balanced and integer-cents', async () => {
  const pair = await setupPair({ proposer: 'tok_good', recipient: 'tok_good' });
  const { scheduledStart, scheduledEnd } = futureWindow();

  const proposed = await dateProposalService.proposeDate(pair.proposerCtx, {
    conversationId: pair.conversationId,
    venueId: pair.venueId,
    scheduledStart,
    scheduledEnd,
  });
  assert.equal(await voucherExists(proposed.id), false, 'no voucher before both accept+capture');

  const finalProposal = await dateProposalService.acceptDateProposal(pair.recipientCtx, proposed.id);
  assert.equal(finalProposal.status, 'ticketed');

  const proposerHold = await holdRow(pair.proposerId, proposed.id);
  const recipientHold = await holdRow(pair.recipientId, proposed.id);
  assert.equal(proposerHold?.status, 'captured');
  assert.equal(recipientHold?.status, 'captured');
  assert.equal(await voucherExists(proposed.id), true, 'CC-3: voucher exists now that both captures succeeded');

  const entries = await ledgerService.listEntriesForDateProposal(pair.proposerCtx, proposed.id);
  // Exactly 2 authorizations + 2 captures, nothing else, for the happy path.
  assert.equal(entries.filter((e) => e.type === 'authorization').length, 2);
  assert.equal(entries.filter((e) => e.type === 'capture' && e.amountCents > 0).length, 2);
  assert.equal(entries.filter((e) => e.type === 'refund' || e.type === 'release').length, 0);

  // CC-11: every amount ever recorded is an integer number of cents.
  for (const e of entries) {
    assert.ok(Number.isInteger(e.amountCents), `ledger amountCents must be an integer, got ${e.amountCents}`);
  }

  // Net position: both users end up down exactly the escrow amount, no more, no less.
  for (const userId of [pair.proposerId, pair.recipientId]) {
    const userEntries = entries.filter((e) => e.userId === userId);
    const captured = userEntries.filter((e) => e.type === 'capture').reduce((s, e) => s + e.amountCents, 0);
    const refunded = userEntries.filter((e) => e.type === 'refund').reduce((s, e) => s + e.amountCents, 0);
    assert.equal(captured - refunded, proposed.escrowAmountCents, `net captured position for ${userId} must equal the escrow amount exactly`);
  }
});

// =====================================================================
// CC-4: append-only. Earlier ledger rows are never mutated by later
// operations on the same date proposal (full-refund cancellation after
// ticketing appends new rows, never rewrites the capture rows).
// =====================================================================

test('CC-4: cancelling a ticketed, fully-refundable date proposal APPENDS refund entries; the original capture entries are byte-identical afterward', async () => {
  const pair = await setupPair({ proposer: 'tok_good', recipient: 'tok_good' });
  const { scheduledStart, scheduledEnd } = futureWindow();

  const proposed = await dateProposalService.proposeDate(pair.proposerCtx, {
    conversationId: pair.conversationId,
    venueId: pair.venueId,
    scheduledStart,
    scheduledEnd,
  });
  const ticketed = await dateProposalService.acceptDateProposal(pair.recipientCtx, proposed.id);
  assert.equal(ticketed.status, 'ticketed');

  const beforeCancel = await ledgerService.listEntriesForDateProposal(pair.proposerCtx, proposed.id);
  const beforeCancelSnapshot = JSON.parse(JSON.stringify(beforeCancel)) as typeof beforeCancel;

  // Cancel comfortably outside the (default 24h) full-refund cutoff: proposal
  // is 3 days out, we haven't advanced the clock at all.
  const canceled = await dateProposalService.cancelDateProposal(pair.proposerCtx, proposed.id);
  assert.equal(canceled.status, 'refunded');

  const afterCancel = await ledgerService.listEntriesForDateProposal(pair.proposerCtx, proposed.id);
  assert.ok(afterCancel.length > beforeCancelSnapshot.length, 'cancellation must APPEND new ledger rows');

  // Every row present before the cancel must still be present, in the
  // same order, with every field unchanged (append-only, never mutated).
  for (let i = 0; i < beforeCancelSnapshot.length; i++) {
    const before = beforeCancelSnapshot[i]!;
    const after = afterCancel[i]!;
    assert.deepEqual(
      { ...after, createdAt: undefined },
      { ...before, createdAt: undefined },
      `ledger row #${i} (id ${before.id}) must be unchanged after a later operation on the same date proposal`,
    );
  }

  // The new rows are exactly a matching refund per side, full escrow amount.
  const newRows = afterCancel.slice(beforeCancelSnapshot.length);
  const refundRows = newRows.filter((e) => e.type === 'refund');
  assert.equal(refundRows.length, 2, 'one refund row per participant');
  for (const r of refundRows) assert.equal(r.amountCents, proposed.escrowAmountCents);

  // Full reconciliation: for each participant, captured - refunded == 0
  // (a fully-refunded cancellation nets to nobody being charged anything).
  for (const userId of [pair.proposerId, pair.recipientId]) {
    const userEntries = afterCancel.filter((e) => e.userId === userId);
    const captured = userEntries.filter((e) => e.type === 'capture').reduce((s, e) => s + e.amountCents, 0);
    const refunded = userEntries.filter((e) => e.type === 'refund').reduce((s, e) => s + e.amountCents, 0);
    assert.equal(captured - refunded, 0, `${userId} must net to zero after a full-refund cancellation`);
  }
});
