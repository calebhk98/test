/**
 * The §13/§14/§15 date-proposal and voucher state machines, driven
 * exhaustively against `dateProposal.service.ts`, `redemption.service.ts`,
 * and `voucher.service.ts`. `moneyInvariants.test.ts` already exhaustively
 * covers the payment-failure branches (draft->payment_failed,
 * pending_acceptance->accepted->payment_failed at every capture-ordering
 * point); this file covers the REMAINING legal/illegal edges the
 * checklist's state-machine tables name: decline/cancel/expire before
 * money moves, the post-ticketing outcomes (redemption, no-scan
 * confirmation, no-show), and the voucher lifecycle's own table
 * (C-15.SM.L1-L3 / I1-I4).
 *
 * dateProposal.service.ts is on the task's list of concurrently-changing
 * files.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import {
  setupConformanceDb,
  teardownConformanceDb,
  makeCtx,
  userActor,
  systemActor,
  adminActor,
  venueStaffActor,
  createUser,
  createPaymentMethod,
  createConversation,
  createVenue,
  rawRow,
  type TestDb,
} from './support.js';
import * as dateProposalService from '../../src/services/dateProposal.service.js';
import * as redemptionService from '../../src/services/redemption.service.js';
import * as voucherService from '../../src/services/voucher.service.js';
import { FakeProcessor } from '../../src/services/payments/fake.processor.js';
import { ConflictError, ForbiddenError } from '../../src/lib/errors.js';
import type { Ctx } from '../../src/lib/ctx.js';

let db: TestDb;

before(async () => {
  db = await setupConformanceDb('dpvouchersm');
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

/** `venue_redemptions.venue_staff_id` FKs to `venue_staff.id` (not `users.id`), so the venue-staff actor id must be a real row here. */
async function createVenueStaff(venueId: string): Promise<string> {
  const staffUserId = await createUser(db);
  const row = await rawRow<{ id: string }>(db, `INSERT INTO venue_staff (user_id, venue_id, active) VALUES ($1, $2, true) RETURNING id`, [staffUserId, venueId]);
  return row!.id;
}

async function setupPair(): Promise<Pair> {
  const proposerId = await createUser(db);
  const recipientId = await createUser(db);
  await createPaymentMethod(db, proposerId, 'tok_good');
  await createPaymentMethod(db, recipientId, 'tok_good');
  const conversationId = await createConversation(db, proposerId, recipientId, 'active');
  const venueId = await createVenue(db);
  const processor = new FakeProcessor();
  return {
    proposerId,
    recipientId,
    conversationId,
    venueId,
    processor,
    proposerCtx: makeCtx(db, userActor(proposerId), { payments: processor }),
    recipientCtx: makeCtx(db, userActor(recipientId), { payments: processor }),
  };
}

function futureWindow(hoursOut = 72) {
  const scheduledStart = new Date(db.clock.now().getTime() + hoursOut * 60 * 60 * 1000);
  const scheduledEnd = new Date(scheduledStart.getTime() + 60 * 60 * 1000);
  return { scheduledStart, scheduledEnd };
}

async function propose(pair: Pair, hoursOut = 72) {
  const { scheduledStart, scheduledEnd } = futureWindow(hoursOut);
  return dateProposalService.proposeDate(pair.proposerCtx, { conversationId: pair.conversationId, venueId: pair.venueId, scheduledStart, scheduledEnd });
}

async function proposeAndTicket(pair: Pair, hoursOut = 72) {
  const proposed = await propose(pair, hoursOut);
  const ticketed = await dateProposalService.acceptDateProposal(pair.recipientCtx, proposed.id);
  assert.equal(ticketed.status, 'ticketed');
  return ticketed;
}

// =====================================================================
// Legal transitions before any capture happens.
// =====================================================================

test('date-proposal SM legal: pending_acceptance -> declined', async () => {
  const pair = await setupPair();
  const proposed = await propose(pair);
  const declined = await dateProposalService.declineDateProposal(pair.recipientCtx, proposed.id);
  assert.equal(declined.status, 'declined');
});

test('date-proposal SM legal: pending_acceptance -> canceled (proposer cancels before acceptance, hold released not captured)', async () => {
  const pair = await setupPair();
  const proposed = await propose(pair);
  const canceled = await dateProposalService.cancelDateProposal(pair.proposerCtx, proposed.id);
  assert.equal(canceled.status, 'canceled');
  const hold = await rawRow<{ status: string }>(db, `SELECT status FROM payment_holds WHERE date_proposal_id = $1 AND user_id = $2`, [proposed.id, pair.proposerId]);
  assert.equal(hold?.status, 'released');
});

test('C-14.6.1: pending_acceptance -> expired at the 48h accept-expiry boundary, proposer hold released', async () => {
  const pair = await setupPair();
  const proposed = await propose(pair);
  const systemCtx = makeCtx(db, systemActor('date_proposal_expiry'), { payments: pair.processor });

  db.clock.advanceHours(47);
  db.clock.advanceMs(59 * 60 * 1000 + 59 * 1000);
  let swept = await dateProposalService.expireDuePendingProposals(systemCtx);
  assert.equal(swept.expired, 0, 'must not expire a second before the 48h boundary');

  db.clock.advanceMs(1000);
  swept = await dateProposalService.expireDuePendingProposals(systemCtx);
  assert.equal(swept.expired, 1);

  const row = await rawRow<{ status: string }>(db, `SELECT status FROM date_proposals WHERE id = $1`, [proposed.id]);
  assert.equal(row?.status, 'expired');
  const hold = await rawRow<{ status: string }>(db, `SELECT status FROM payment_holds WHERE date_proposal_id = $1 AND user_id = $2`, [proposed.id, pair.proposerId]);
  assert.equal(hold?.status, 'released');
});

// =====================================================================
// Post-ticketing outcomes.
// =====================================================================

test('C-15.3.2 / C-15.3.3 / C-15.3.4 / C-15.SM.L1: venue redemption -> voucher redeemed, date proposal completed, conversation established, atomically', async () => {
  const pair = await setupPair();
  const ticketed = await proposeAndTicket(pair, 3 /* hours out, close enough to redeem "at the venue" */);
  const voucherRow = await rawRow<{ id: string; code: string }>(db, `SELECT id, code FROM vouchers WHERE date_proposal_id = $1`, [ticketed.id]);
  assert.ok(voucherRow);

  const venueStaffId = await createVenueStaff(pair.venueId);
  const venueStaffCtx = makeCtx(db, venueStaffActor(venueStaffId, pair.venueId));
  const result = await redemptionService.redeemByStaff(venueStaffCtx, { code: voucherRow!.code });
  assert.equal(result.voucher.status, 'redeemed');
  assert.equal(result.dateProposal.status, 'completed');

  const convo = await rawRow<{ status: string }>(db, `SELECT status FROM conversations WHERE id = $1`, [pair.conversationId]);
  assert.equal(convo?.status, 'established');
});

test('C-15.4.1: both users confirm attendance within the no-scan window -> completed_unverified, conversation established', async () => {
  const pair = await setupPair();
  const ticketed = await proposeAndTicket(pair, 1);
  db.clock.advanceHours(2); // past scheduledEnd, still well inside the 72h confirmation window

  await dateProposalService.confirmAttendance(pair.proposerCtx, ticketed.id);
  const after = await dateProposalService.confirmAttendance(pair.recipientCtx, ticketed.id);
  assert.equal(after.dateProposal.status, 'completed_unverified');

  const convo = await rawRow<{ status: string }>(db, `SELECT status FROM conversations WHERE id = $1`, [pair.conversationId]);
  assert.equal(convo?.status, 'established');
});

test('C-15.4.3 / C-15.4.4: only ONE user confirms and the window closes with no venue scan -> disputed, resolved automatically (no human/admin step)', async () => {
  const pair = await setupPair();
  const ticketed = await proposeAndTicket(pair, 1);
  db.clock.advanceHours(2);
  await dateProposalService.confirmAttendance(pair.proposerCtx, ticketed.id);

  // Close the 72h (default date.no_scan_confirmation_hours) window from
  // scheduledEnd WITHOUT a second confirmAttendance call ever arriving,
  // and let the real §25 sweep job (not a manual re-poke) resolve it, per
  // the checklist's own oracle ("driven by §25 background job").
  db.clock.advanceHours(73);
  const systemCtx = makeCtx(db, systemActor('ticketed_completion_sweep'), { payments: pair.processor });
  const swept = await dateProposalService.sweepTicketedCompletionWindows(systemCtx);
  assert.equal(swept.autoDisputed, 1);
  assert.equal(swept.autoNoShow, 0);

  const row = await rawRow<{ status: string }>(db, `SELECT status FROM date_proposals WHERE id = $1`, [ticketed.id]);
  assert.equal(row?.status, 'disputed', 'exactly one confirmation, window closed, no scan -> disputed, with no admin call anywhere in this test');
});

test('C-14.7.W4 / C-15.4: NEITHER user confirms and the window closes with no venue scan -> auto no_show for both, refunded per the no_show policy (default 0%)', async () => {
  const pair = await setupPair();
  const ticketed = await proposeAndTicket(pair, 1);
  db.clock.advanceHours(2 + 73); // past scheduledEnd + the 72h confirmation window, no confirmations at all

  const systemCtx = makeCtx(db, systemActor('ticketed_completion_sweep'), { payments: pair.processor });
  const swept = await dateProposalService.sweepTicketedCompletionWindows(systemCtx);
  assert.equal(swept.autoNoShow, 1);

  const row = await rawRow<{ status: string }>(db, `SELECT status FROM date_proposals WHERE id = $1`, [ticketed.id]);
  assert.equal(row?.status, 'no_show');
  for (const userId of [pair.proposerId, pair.recipientId]) {
    const hold = await rawRow<{ status: string }>(db, `SELECT status FROM payment_holds WHERE date_proposal_id = $1 AND user_id = $2`, [ticketed.id, userId]);
    // Default `date.no_show_refund_percent` is 0, so the "refund" is for
    // zero cents; the hold's OWN status stays 'captured' (the escrow was
    // genuinely earned by nobody, but with a 0% policy there is nothing
    // to move), this pins the default-policy behavior as the oracle.
    assert.equal(hold?.status, 'captured');
  }
});

test('date-proposal SM legal: ticketed -> no_show (admin/system marks it), the OTHER party is refunded in full', async () => {
  const pair = await setupPair();
  const ticketed = await proposeAndTicket(pair, 1);
  const adminCtx = makeCtx(db, adminActor(), { payments: pair.processor });
  const result = await dateProposalService.markNoShow(adminCtx, ticketed.id, pair.recipientId);
  assert.equal(result.status, 'no_show');

  const otherHold = await rawRow<{ status: string }>(db, `SELECT status FROM payment_holds WHERE date_proposal_id = $1 AND user_id = $2`, [ticketed.id, pair.proposerId]);
  assert.equal(otherHold?.status, 'refunded', 'the party who showed up must be made whole');
});

// =====================================================================
// Illegal transitions.
// =====================================================================

test('date-proposal SM illegal: declined is terminal, recipient cannot later accept it', async () => {
  const pair = await setupPair();
  const proposed = await propose(pair);
  await dateProposalService.declineDateProposal(pair.recipientCtx, proposed.id);
  await assert.rejects(() => dateProposalService.acceptDateProposal(pair.recipientCtx, proposed.id), ConflictError);
});

test('date-proposal SM illegal: expired is terminal, recipient cannot accept after the expiry sweep', async () => {
  const pair = await setupPair();
  const proposed = await propose(pair);
  const systemCtx = makeCtx(db, systemActor('date_proposal_expiry'), { payments: pair.processor });
  db.clock.advanceHours(48);
  await dateProposalService.expireDuePendingProposals(systemCtx);
  await assert.rejects(() => dateProposalService.acceptDateProposal(pair.recipientCtx, proposed.id), ConflictError);
});

test('date-proposal SM illegal: canceled is terminal, cannot cancel it again from a fully-settled state', async () => {
  const pair = await setupPair();
  const proposed = await propose(pair);
  await dateProposalService.cancelDateProposal(pair.proposerCtx, proposed.id);
  await assert.rejects(() => dateProposalService.cancelDateProposal(pair.proposerCtx, proposed.id), ConflictError);
});

test('date-proposal SM illegal: completed is terminal, cannot be canceled after the fact', async () => {
  const pair = await setupPair();
  const ticketed = await proposeAndTicket(pair, 3);
  const voucherRow = await rawRow<{ code: string }>(db, `SELECT code FROM vouchers WHERE date_proposal_id = $1`, [ticketed.id]);
  const venueStaffId = await createVenueStaff(pair.venueId);
  const venueStaffCtx = makeCtx(db, venueStaffActor(venueStaffId, pair.venueId));
  await redemptionService.redeemByStaff(venueStaffCtx, { code: voucherRow!.code });
  await assert.rejects(() => dateProposalService.cancelDateProposal(pair.proposerCtx, ticketed.id), ConflictError);
});

test('date-proposal SM illegal: confirmAttendance is rejected before ticketed (still pending_acceptance)', async () => {
  const pair = await setupPair();
  const proposed = await propose(pair);
  await assert.rejects(() => dateProposalService.confirmAttendance(pair.proposerCtx, proposed.id), ConflictError);
});

test('date-proposal SM illegal: a non-participant cannot cancel someone else\'s date proposal', async () => {
  const pair = await setupPair();
  const proposed = await propose(pair);
  const strangerId = await createUser(db);
  const strangerCtx = makeCtx(db, userActor(strangerId));
  await assert.rejects(() => dateProposalService.cancelDateProposal(strangerCtx, proposed.id), ForbiddenError);
});

// =====================================================================
// Voucher state machine (§15 / §23.20): C-15.SM.L1-L3 / I1-I4.
// =====================================================================

test('C-15.SM.L2: issued -> expired (voucher-expiry job, past voucher.expiry_hours_after_date_end)', async () => {
  const pair = await setupPair();
  const ticketed = await proposeAndTicket(pair, 1);
  db.clock.advanceHours(1 + 72 + 2); // past scheduledEnd + default 72h expiry window
  const systemCtx = makeCtx(db, systemActor('voucher_expiry'), { payments: pair.processor });
  const swept = await voucherService.expireDueVouchers(systemCtx);
  assert.ok(swept.expired >= 1);
  const row = await rawRow<{ status: string }>(db, `SELECT status FROM vouchers WHERE date_proposal_id = $1`, [ticketed.id]);
  assert.equal(row?.status, 'expired');
});

test('C-15.SM.L3: issued -> canceled (the underlying date proposal is canceled after ticketing)', async () => {
  const pair = await setupPair();
  const ticketed = await proposeAndTicket(pair, 3);
  // Inside the (default 24h) full-refund cutoff, still a legal cancel.
  db.clock.advanceHours(2);
  await dateProposalService.cancelDateProposal(pair.proposerCtx, ticketed.id);
  const row = await rawRow<{ status: string }>(db, `SELECT status FROM vouchers WHERE date_proposal_id = $1`, [ticketed.id]);
  assert.equal(row?.status, 'canceled');
});

test('C-15.SM.I1: a redeemed voucher is terminal, cannot un-redeem via expiry or cancellation', async () => {
  const pair = await setupPair();
  const ticketed = await proposeAndTicket(pair, 3);
  const voucherRow = await rawRow<{ id: string; code: string }>(db, `SELECT id, code FROM vouchers WHERE date_proposal_id = $1`, [ticketed.id]);
  const venueStaffId = await createVenueStaff(pair.venueId);
  const venueStaffCtx = makeCtx(db, venueStaffActor(venueStaffId, pair.venueId));
  await redemptionService.redeemByStaff(venueStaffCtx, { code: voucherRow!.code });

  // The expiry job must not touch an already-redeemed voucher.
  db.clock.advanceHours(1000);
  const systemCtx = makeCtx(db, systemActor('voucher_expiry'), { payments: pair.processor });
  await voucherService.expireDueVouchers(systemCtx);
  const row = await rawRow<{ status: string }>(db, `SELECT status FROM vouchers WHERE id = $1`, [voucherRow!.id]);
  assert.equal(row?.status, 'redeemed', 'a redeemed voucher must remain redeemed forever, never silently expired');
});

test('C-15.SM.I2: expired -> redeemed is rejected, venue cannot scan a code past its expiry', async () => {
  const pair = await setupPair();
  const ticketed = await proposeAndTicket(pair, 1);
  const voucherRow = await rawRow<{ code: string }>(db, `SELECT code FROM vouchers WHERE date_proposal_id = $1`, [ticketed.id]);
  db.clock.advanceHours(1 + 72 + 2);
  const systemCtx = makeCtx(db, systemActor('voucher_expiry'), { payments: pair.processor });
  await voucherService.expireDueVouchers(systemCtx);

  const venueStaffId = await createVenueStaff(pair.venueId);
  const venueStaffCtx = makeCtx(db, venueStaffActor(venueStaffId, pair.venueId));
  await assert.rejects(() => redemptionService.redeemByStaff(venueStaffCtx, { code: voucherRow!.code }), ConflictError);
});

test('C-15.SM.I3: canceled -> redeemed is rejected, a canceled proposal\'s voucher cannot later be scanned', async () => {
  const pair = await setupPair();
  const ticketed = await proposeAndTicket(pair, 3);
  const voucherRow = await rawRow<{ code: string }>(db, `SELECT code FROM vouchers WHERE date_proposal_id = $1`, [ticketed.id]);
  db.clock.advanceHours(2);
  await dateProposalService.cancelDateProposal(pair.proposerCtx, ticketed.id);

  const venueStaffId = await createVenueStaff(pair.venueId);
  const venueStaffCtx = makeCtx(db, venueStaffActor(venueStaffId, pair.venueId));
  await assert.rejects(() => redemptionService.redeemByStaff(venueStaffCtx, { code: voucherRow!.code }), ConflictError);
});

test('C-15.SM.I4: scanning the same voucher twice is rejected as a conflict, not silently accepted', async () => {
  const pair = await setupPair();
  const ticketed = await proposeAndTicket(pair, 3);
  const voucherRow = await rawRow<{ code: string }>(db, `SELECT code FROM vouchers WHERE date_proposal_id = $1`, [ticketed.id]);
  const venueStaffId = await createVenueStaff(pair.venueId);
  const venueStaffCtx = makeCtx(db, venueStaffActor(venueStaffId, pair.venueId));
  await redemptionService.redeemByStaff(venueStaffCtx, { code: voucherRow!.code });
  await assert.rejects(() => redemptionService.redeemByStaff(venueStaffCtx, { code: voucherRow!.code }), ConflictError);
});
