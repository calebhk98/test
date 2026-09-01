/**
 * Decision 2 unit tests (see docs/conformance.md Open Question OQ-3):
 * `sweepTicketedCompletionWindows` (dateProposal.service.ts) and
 * `resolveDueDisputes` (disputeResolution.service.ts) — what actually
 * produces `no_show`, and how `disputed` gets resolved, both with zero
 * human input (spec §18.1).
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { FakeProcessor } from '../../src/services/payments/fake.processor.js';
import * as dateProposalService from '../../src/services/dateProposal.service.js';
import * as disputeResolutionService from '../../src/services/disputeResolution.service.js';
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
} from './testCtxDecisions.js';

let db: TestDb;
// ONE shared FakeProcessor for the whole file — deliberately, not one per
// pair: `sweepTicketedCompletionWindows`/`resolveDueDisputes` are called
// with a single `system`-actor Ctx that scans every ticketed/disputed
// proposal in the database regardless of which test created it, so its
// `ctx.payments` must be able to resolve EVERY pair's holds, not just one
// pair's. Sharing one `FakeProcessor` instance (keyed internally by
// idempotency key / processor intent id, never by pair) is safe — see
// `sweepCtx` below.
let sharedProcessor: FakeProcessor;

before(async () => {
  db = await setupTestDb('outcomesweep');
  sharedProcessor = new FakeProcessor();
});

after(async () => {
  await teardownTestDb(db);
});

function sweepCtx(): ReturnType<typeof makeCtx> {
  return makeCtx(db, systemActor(), { payments: sharedProcessor });
}

interface Pair {
  proposerId: string;
  recipientId: string;
  conversationId: string;
  venueId: string;
  proposerCtx: ReturnType<typeof makeCtx>;
  recipientCtx: ReturnType<typeof makeCtx>;
}

async function setupPair(): Promise<Pair> {
  const proposerId = await createUser(db);
  const recipientId = await createUser(db);
  await createPaymentMethod(db, proposerId, 'tok_good');
  await createPaymentMethod(db, recipientId, 'tok_good');
  const conversationId = await createConversation(db, proposerId, recipientId, 'active');
  const venueId = await createVenue(db);
  return {
    proposerId,
    recipientId,
    conversationId,
    venueId,
    proposerCtx: makeCtx(db, userActor(proposerId), { payments: sharedProcessor }),
    recipientCtx: makeCtx(db, userActor(recipientId), { payments: sharedProcessor }),
  };
}

function futureRange(hoursFromNow: number): { scheduledStart: Date; scheduledEnd: Date } {
  const start = new Date(db.clock.now().getTime() + hoursFromNow * 60 * 60 * 1000);
  return { scheduledStart: start, scheduledEnd: new Date(start.getTime() + 2 * 60 * 60 * 1000) };
}

async function ticketedFlow(pair: Pair, hoursUntilDateAtCreation: number): Promise<string> {
  const { scheduledStart, scheduledEnd } = futureRange(hoursUntilDateAtCreation);
  const proposed = await dateProposalService.proposeDate(pair.proposerCtx, {
    conversationId: pair.conversationId,
    venueId: pair.venueId,
    scheduledStart,
    scheduledEnd,
  });
  const accepted = await dateProposalService.acceptDateProposal(pair.recipientCtx, proposed.id);
  assert.equal(accepted.status, 'ticketed');
  return proposed.id;
}

async function holdStatus(dateProposalId: string, userId: string): Promise<string | undefined> {
  const { rows } = await db.pool.query<{ status: string }>(
    'SELECT status FROM payment_holds WHERE date_proposal_id = $1 AND user_id = $2',
    [dateProposalId, userId],
  );
  return rows[0]?.status;
}

async function trustEventCount(userId: string, eventType: string): Promise<number> {
  const { rows } = await db.pool.query<{ count: string }>(
    'SELECT count(*)::text AS count FROM trust_events WHERE user_id = $1 AND event_type = $2',
    [userId, eventType],
  );
  return Number(rows[0]!.count);
}

async function notificationCount(userId: string, eventType: string): Promise<number> {
  const { rows } = await db.pool.query<{ count: string }>(
    'SELECT count(*)::text AS count FROM notifications WHERE user_id = $1 AND event_type = $2',
    [userId, eventType],
  );
  return Number(rows[0]!.count);
}

// =====================================================================
// sweepTicketedCompletionWindows — zero confirmations -> no_show
// =====================================================================

test('sweepTicketedCompletionWindows: zero confirmations after the window closes -> no_show for both parties automatically, no human input', async () => {
  const pair = await setupPair();
  const dateProposalId = await ticketedFlow(pair, 2);
  // Deadline = scheduledEnd (created 2h + 2h duration = 4h from now) + the
  // default 72h no_scan_confirmation_hours = 76h from now; advance well past it.
  db.clock.advanceHours(80);

  const result = await dateProposalService.sweepTicketedCompletionWindows(sweepCtx());
  assert.equal(result.autoNoShow, 1);
  assert.equal(result.autoDisputed, 0);

  const proposal = await dateProposalService.getDateProposal(sweepCtx(), dateProposalId);
  assert.equal(proposal.status, 'no_show');

  // Default no_show_refund_percent = 0 -> both remain captured (nobody refunded).
  assert.equal(await holdStatus(dateProposalId, pair.proposerId), 'captured');
  assert.equal(await holdStatus(dateProposalId, pair.recipientId), 'captured');

  assert.equal(await trustEventCount(pair.proposerId, 'no_show'), 1);
  assert.equal(await trustEventCount(pair.recipientId, 'no_show'), 1);
  assert.equal(await notificationCount(pair.proposerId, 'date_no_show'), 1);
  assert.equal(await notificationCount(pair.recipientId, 'date_no_show'), 1);

  // Idempotent: re-running the sweep does not touch an already-resolved proposal.
  const second = await dateProposalService.sweepTicketedCompletionWindows(sweepCtx());
  assert.equal(second.autoNoShow, 0);
  assert.equal(await trustEventCount(pair.proposerId, 'no_show'), 1, 'no double trust event on re-sweep');
});

test('sweepTicketedCompletionWindows: with a non-zero no_show_refund_percent, both forfeiting parties keep that percent captured, the rest refunded', async () => {
  await db.config.set('date.no_show_refund_percent', 40, 'test-admin');
  const pair = await setupPair();
  const dateProposalId = await ticketedFlow(pair, 2);
  db.clock.advanceHours(80); // well past the 76h deadline (see the previous test's comment)

  await dateProposalService.sweepTicketedCompletionWindows(sweepCtx());

  const { rows } = await db.pool.query<{ status: string; amount_cents: string }>(
    'SELECT status, amount_cents FROM payment_holds WHERE date_proposal_id = $1',
    [dateProposalId],
  );
  // no_show_refund_percent is the percent REFUNDED back to the no-show
  // party (40% here -> 800 of 2000 refunded, 1200 forfeited) — not fully
  // refunded, so status stays 'captured' per payment.service#refundHold's
  // "only 'refunded' once the FULL amount has been refunded" rule.
  assert.equal(rows.length, 2);
  for (const row of rows) assert.equal(row.status, 'captured');

  const { rows: ledgerRows } = await db.pool.query<{ amount_cents: string }>(
    `SELECT amount_cents FROM payment_ledger WHERE date_proposal_id = $1 AND type = 'refund'`,
    [dateProposalId],
  );
  assert.equal(ledgerRows.length, 2);
  for (const row of ledgerRows) assert.equal(Number(row.amount_cents), 800); // floor(2000 * 40 / 100) = 800 refunded to each

  await db.config.set('date.no_show_refund_percent', 0, 'test-admin'); // restore default for subsequent tests
});

test('sweepTicketedCompletionWindows: the window still being open leaves a ticketed proposal untouched', async () => {
  const pair = await setupPair();
  const dateProposalId = await ticketedFlow(pair, 2);
  db.clock.advanceHours(3); // past scheduledEnd, but well inside the 72h window

  await dateProposalService.sweepTicketedCompletionWindows(sweepCtx());

  const proposal = await dateProposalService.getDateProposal(sweepCtx(), dateProposalId);
  assert.equal(proposal.status, 'ticketed');

  // Clean up: this file's clock is shared and monotonic across every test
  // below, so a proposal deliberately left 'ticketed' here would otherwise
  // become "due" and get swept up by a LATER test once enough cumulative
  // time has passed — cancel it now so later tests' own sweep results stay
  // scoped to what they themselves created.
  await dateProposalService.cancelDateProposal(pair.proposerCtx, dateProposalId);
});

// =====================================================================
// sweepTicketedCompletionWindows — exactly one confirmation -> disputed,
// with nobody ever calling confirmAttendance again after the deadline.
// =====================================================================

test('sweepTicketedCompletionWindows: exactly one confirmation, window elapsed, nobody calls back -> disputed automatically', async () => {
  const pair = await setupPair();
  const dateProposalId = await ticketedFlow(pair, 2);
  db.clock.advanceHours(3); // past scheduledStart, registers a confirmation early
  await dateProposalService.confirmAttendance(pair.proposerCtx, dateProposalId);

  db.clock.advanceHours(76); // total ~79h from creation — well past the 76h deadline; the recipient never confirms and nobody calls confirmAttendance again
  const result = await dateProposalService.sweepTicketedCompletionWindows(sweepCtx());
  assert.equal(result.autoDisputed, 1);
  assert.equal(result.autoNoShow, 0);

  const proposal = await dateProposalService.getDateProposal(sweepCtx(), dateProposalId);
  assert.equal(proposal.status, 'disputed');
  assert.equal(await notificationCount(pair.proposerId, 'date_disputed'), 1);
  assert.equal(await notificationCount(pair.recipientId, 'date_disputed'), 1);

  // Clean up: resolve this dispute now rather than leaving it lingering
  // 'disputed'+unresolved — this file's clock is shared and monotonic, so
  // an unresolved dispute here would otherwise become "due" for
  // `resolveDueDisputes` partway through a LATER test and contaminate that
  // test's own aggregate `resolved` count.
  db.clock.advanceHours(150); // past the default 72h dispute_auto_resolve_hours cooldown
  await disputeResolutionService.resolveDueDisputes(sweepCtx());
});

// =====================================================================
// resolveDueDisputes — automated dispute resolution, no human step.
// =====================================================================

async function reachDisputedState(pair: Pair, confirmingCtx: ReturnType<typeof makeCtx>): Promise<string> {
  const dateProposalId = await ticketedFlow(pair, 2);
  db.clock.advanceHours(3); // past scheduledStart, registers one confirmation early
  await dateProposalService.confirmAttendance(confirmingCtx, dateProposalId);
  // Total elapsed since creation must exceed the 76h deadline
  // (scheduledEnd at +4h, plus the default 72h no_scan_confirmation_hours).
  db.clock.advanceHours(76);
  const result = await dateProposalService.confirmAttendance(confirmingCtx, dateProposalId);
  assert.equal(result.dateProposal.status, 'disputed');
  return dateProposalId;
}

test('resolveDueDisputes: after dispute_auto_resolve_hours, files an implicit no_show report against the non-confirming party and records a negative trust event — with zero human input', async () => {
  const pair = await setupPair();
  const dateProposalId = await reachDisputedState(pair, pair.proposerCtx); // proposer confirmed; recipient did not

  // Still within the cooldown -> nothing resolves yet.
  const tooEarly = await disputeResolutionService.resolveDueDisputes(sweepCtx());
  assert.equal(tooEarly.resolved, 0);

  db.clock.advanceHours(73); // past the default 72h dispute_auto_resolve_hours cooldown
  const result = await disputeResolutionService.resolveDueDisputes(sweepCtx());
  assert.equal(result.resolved, 1);

  // Status stays 'disputed' — terminal per §13.3; only the side effects fired.
  const proposal = await dateProposalService.getDateProposal(sweepCtx(), dateProposalId);
  assert.equal(proposal.status, 'disputed');

  const { rows: reportRows } = await db.pool.query<{ reporter_id: string; reported_id: string; category: string }>(
    'SELECT reporter_id, reported_id, category FROM reports WHERE reported_id = $1',
    [pair.recipientId],
  );
  assert.equal(reportRows.length, 1, 'an implicit report was filed against the non-confirming party');
  assert.equal(reportRows[0]!.reporter_id, pair.proposerId, 'the confirming party is the reporter');
  assert.equal(reportRows[0]!.category, 'no_show');

  assert.equal(await trustEventCount(pair.recipientId, 'no_show'), 1);
  assert.equal(await trustEventCount(pair.proposerId, 'no_show'), 0, 'the confirming party is not penalized');

  const { rows: dpRows } = await db.pool.query<{ dispute_resolved_at: Date | null }>(
    'SELECT dispute_resolved_at FROM date_proposals WHERE id = $1',
    [dateProposalId],
  );
  assert.ok(dpRows[0]!.dispute_resolved_at, 'dispute_resolved_at marks the automated resolution as done');

  // Idempotent: re-running does not file a second report or double the trust hit.
  const again = await disputeResolutionService.resolveDueDisputes(sweepCtx());
  assert.equal(again.resolved, 0);
  const { rows: reportRowsAgain } = await db.pool.query<{ count: string }>(
    'SELECT count(*)::text AS count FROM reports WHERE reported_id = $1',
    [pair.recipientId],
  );
  assert.equal(reportRowsAgain[0]!.count, '1');
  assert.equal(await trustEventCount(pair.recipientId, 'no_show'), 1, 'no double trust event on re-run');
});

test('resolveDueDisputes: the report targets whichever party did NOT confirm, regardless of who proposed', async () => {
  const pair = await setupPair();
  // This time the RECIPIENT confirms; the PROPOSER does not.
  const dateProposalId = await reachDisputedState(pair, pair.recipientCtx);

  db.clock.advanceHours(73);
  await disputeResolutionService.resolveDueDisputes(sweepCtx());

  const { rows } = await db.pool.query<{ reporter_id: string; reported_id: string }>(
    'SELECT reporter_id, reported_id FROM reports WHERE reported_id = $1',
    [pair.proposerId],
  );
  assert.equal(rows.length, 1);
  assert.equal(rows[0]!.reporter_id, pair.recipientId);
  assert.equal(await trustEventCount(pair.proposerId, 'no_show'), 1);
  assert.equal(await trustEventCount(pair.recipientId, 'no_show'), 0);
  void dateProposalId;
});

test('end-to-end no-human-input proof: ticketed -> (nobody scans, nobody confirms twice) -> disputed -> auto-resolved, driven only by system-actor sweeps', async () => {
  const pair = await setupPair();
  const dateProposalId = await ticketedFlow(pair, 2);
  db.clock.advanceHours(3);
  await dateProposalService.confirmAttendance(pair.proposerCtx, dateProposalId); // one participant confirms; this is a normal user action, not an admin one

  db.clock.advanceHours(76); // total ~79h — past the 76h no-scan-window deadline
  const systemCtx = sweepCtx();
  const sweep = await dateProposalService.sweepTicketedCompletionWindows(systemCtx);
  assert.equal(sweep.autoDisputed, 1);

  db.clock.advanceHours(73); // total ~152h — past the 148h dispute-auto-resolve deadline
  const resolution = await disputeResolutionService.resolveDueDisputes(systemCtx);
  assert.equal(resolution.resolved, 1);

  // Every state-changing call above used only a `user` actor's own
  // attendance confirmation and `system`-actor sweeps — never `admin`.
  const proposal = await dateProposalService.getDateProposal(systemCtx, dateProposalId);
  assert.equal(proposal.status, 'disputed');
});
