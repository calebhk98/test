/**
 * venueSettlement.service.ts unit tests (Decision 1 — see docs/conformance.md
 * Open Question OQ-8). Drives real `dateProposal.service`/`redemption.service`
 * flows against a real Postgres DB — `conversation`/`notification`/`trust`
 * are the real, complete implementations (no mocking needed; the parallel
 * build's stub period is over).
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { FakeProcessor } from '../../src/services/payments/fake.processor.js';
import * as dateProposalService from '../../src/services/dateProposal.service.js';
import * as redemptionService from '../../src/services/redemption.service.js';
import * as venueSettlementService from '../../src/services/venueSettlement.service.js';
import { ForbiddenError } from '../../src/lib/errors.js';
import {
  setupTestDb,
  teardownTestDb,
  makeCtx,
  userActor,
  adminActor,
  systemActor,
  venueStaffActor,
  createUser,
  createPaymentMethod,
  createConversation,
  createVenue,
  createVenueStaff,
  type TestDb,
} from './testCtxDecisions.js';

let db: TestDb;

before(async () => {
  db = await setupTestDb('venuesettlement');
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
  proposerCtx: ReturnType<typeof makeCtx>;
  recipientCtx: ReturnType<typeof makeCtx>;
}

async function setupPair(marginPercent = 15): Promise<Pair> {
  const proposerId = await createUser(db);
  const recipientId = await createUser(db);
  await createPaymentMethod(db, proposerId, 'tok_good');
  await createPaymentMethod(db, recipientId, 'tok_good');
  const conversationId = await createConversation(db, proposerId, recipientId, 'active');
  const venueId = await createVenue(db, { marginPercent });
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

function futureRange(hoursFromNow: number): { scheduledStart: Date; scheduledEnd: Date } {
  const start = new Date(db.clock.now().getTime() + hoursFromNow * 60 * 60 * 1000);
  return { scheduledStart: start, scheduledEnd: new Date(start.getTime() + 2 * 60 * 60 * 1000) };
}

async function ticketedFlow(pair: Pair, hoursUntilDateAtCreation = 100): Promise<string> {
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

async function redeemViaStaff(pair: Pair, dateProposalId: string): Promise<void> {
  const vouchers = await db.pool.query<{ qr_payload: string }>('SELECT qr_payload FROM vouchers WHERE date_proposal_id = $1', [dateProposalId]);
  const { staffId } = await createVenueStaff(db, pair.venueId);
  const staffCtx = makeCtx(db, venueStaffActor(staffId, pair.venueId), { payments: pair.processor });
  const result = await redemptionService.redeemByStaff(staffCtx, { qrPayload: vouchers.rows[0]!.qr_payload });
  assert.equal(result.dateProposal.status, 'completed');
}

// =====================================================================
// Payout math (pure, no DB) — the rounding hazard.
// =====================================================================

test('computeVenuePayout: payout + platform === gross, exactly, even when margin does not divide evenly into cents', () => {
  // floor(1999 * 33 / 100) = floor(659.67) = 659; platform = 1999 - 659 = 1340.
  const result = venueSettlementService.computeVenuePayout(1999, 33);
  assert.equal(result.venuePayoutCents, 659);
  assert.equal(result.platformCents, 1340);
  assert.equal(result.venuePayoutCents + result.platformCents, 1999);
});

test('computeVenuePayout: whole-percent case divides exactly', () => {
  const result = venueSettlementService.computeVenuePayout(4000, 15);
  assert.equal(result.venuePayoutCents, 600);
  assert.equal(result.platformCents, 3400);
  assert.equal(result.venuePayoutCents + result.platformCents, 4000);
});

test('computeVenuePayout: 0% margin pays the venue nothing; 100% pays the venue everything — sum still exact', () => {
  assert.deepEqual(venueSettlementService.computeVenuePayout(4000, 0), { venuePayoutCents: 0, platformCents: 4000 });
  assert.deepEqual(venueSettlementService.computeVenuePayout(4000, 100), { venuePayoutCents: 4000, platformCents: 0 });
});

test('computeVenuePayout: property check across many gross/margin combinations, payout + platform === gross always', () => {
  for (let gross = 1; gross <= 5000; gross += 137) {
    for (let margin = 0; margin <= 100; margin += 7) {
      const { venuePayoutCents, platformCents } = venueSettlementService.computeVenuePayout(gross, margin);
      assert.equal(venuePayoutCents + platformCents, gross, `gross=${gross} margin=${margin}`);
      assert.ok(venuePayoutCents >= 0 && platformCents >= 0);
    }
  }
});

// =====================================================================
// Happy path: a venue-verified completion settles.
// =====================================================================

test('settleDueVenuePayouts: a completed, venue-redeemed date proposal settles with the correct payout split and an idempotent venue_payout ledger row', async () => {
  const pair = await setupPair(15);
  const dateProposalId = await ticketedFlow(pair);
  await redeemViaStaff(pair, dateProposalId);

  const result = await venueSettlementService.settleDueVenuePayouts(makeCtx(db, systemActor()));
  assert.equal(result.settled, 1);
  assert.equal(result.totalVenuePayoutCents, 600); // floor(4000 * 15 / 100)
  assert.equal(result.totalPlatformCents, 3400);

  const settlement = result.settlements[0]!;
  assert.equal(settlement.dateProposalId, dateProposalId);
  assert.equal(settlement.venueId, pair.venueId);
  assert.equal(settlement.grossEscrowCents, 4000);
  assert.equal(settlement.marginPercentApplied, 15);
  assert.equal(settlement.venuePayoutCents, 600);
  assert.equal(settlement.platformCents, 3400);
  assert.equal(settlement.venuePayoutCents + settlement.platformCents, settlement.grossEscrowCents);
  assert.equal(settlement.status, 'settled');
  assert.ok(settlement.settledAt);

  // A venue_payout ledger row was appended, paying the venue (not a user).
  const { rows: ledgerRows } = await db.pool.query<{ user_id: string | null; venue_id: string | null; type: string; amount_cents: string }>(
    `SELECT user_id, venue_id, type, amount_cents FROM payment_ledger WHERE date_proposal_id = $1 AND type = 'venue_payout'`,
    [dateProposalId],
  );
  assert.equal(ledgerRows.length, 1);
  assert.equal(ledgerRows[0]!.user_id, null);
  assert.equal(ledgerRows[0]!.venue_id, pair.venueId);
  assert.equal(Number(ledgerRows[0]!.amount_cents), 600);

  // Idempotent: a retried run does not double-settle or double-pay.
  const second = await venueSettlementService.settleDueVenuePayouts(makeCtx(db, systemActor()));
  assert.equal(second.settled, 0);
  const { rows: settlementRows } = await db.pool.query<{ count: string }>(
    'SELECT count(*)::text AS count FROM venue_settlements WHERE date_proposal_id = $1',
    [dateProposalId],
  );
  assert.equal(settlementRows[0]!.count, '1');
  const { rows: ledgerAgain } = await db.pool.query<{ count: string }>(
    `SELECT count(*)::text AS count FROM payment_ledger WHERE date_proposal_id = $1 AND type = 'venue_payout'`,
    [dateProposalId],
  );
  assert.equal(ledgerAgain[0]!.count, '1');
});

test('settleOneDateProposalById: settles a specific eligible proposal on demand, idempotently', async () => {
  const pair = await setupPair(20);
  const dateProposalId = await ticketedFlow(pair);
  await redeemViaStaff(pair, dateProposalId);

  const ctx = makeCtx(db, systemActor());
  const first = await venueSettlementService.settleOneDateProposalById(ctx, dateProposalId);
  assert.ok(first);
  assert.equal(first!.venuePayoutCents, 800); // floor(4000 * 20 / 100)

  const second = await venueSettlementService.settleOneDateProposalById(ctx, dateProposalId);
  assert.equal(second, null, 'already settled — idempotent no-op');
});

// =====================================================================
// Admin payout view — access control + listing.
// =====================================================================

test('listVenueSettlements: admin/system can list; a regular user cannot', async () => {
  const pair = await setupPair();
  const dateProposalId = await ticketedFlow(pair);
  await redeemViaStaff(pair, dateProposalId);
  await venueSettlementService.settleDueVenuePayouts(makeCtx(db, systemActor()));

  const asAdmin = await venueSettlementService.listVenueSettlements(makeCtx(db, adminActor()), { venueId: pair.venueId });
  assert.equal(asAdmin.items.length, 1);
  assert.equal(asAdmin.items[0]!.dateProposalId, dateProposalId);

  await assert.rejects(
    () => venueSettlementService.listVenueSettlements(makeCtx(db, userActor(pair.proposerId))),
    ForbiddenError,
  );
});

// =====================================================================
// Negative cases — this is the whole point of §15.4: every one of these
// terminal statuses must NOT settle.
// =====================================================================

test('§15.4: completed_unverified (no-scan fallback) does NOT settle venue payment', async () => {
  const pair = await setupPair();
  const dateProposalId = await ticketedFlow(pair, 2);
  db.clock.advanceHours(3); // past scheduledEnd

  const r1 = await dateProposalService.confirmAttendance(pair.proposerCtx, dateProposalId);
  assert.equal(r1.dateProposal.status, 'ticketed');
  const r2 = await dateProposalService.confirmAttendance(pair.recipientCtx, dateProposalId);
  assert.equal(r2.dateProposal.status, 'completed_unverified');

  const result = await venueSettlementService.settleDueVenuePayouts(makeCtx(db, systemActor()));
  assert.equal(result.settled, 0);
  const settled = await venueSettlementService.settleOneDateProposalById(makeCtx(db, systemActor()), dateProposalId);
  assert.equal(settled, null);

  const { rows } = await db.pool.query<{ count: string }>('SELECT count(*)::text AS count FROM venue_settlements WHERE date_proposal_id = $1', [dateProposalId]);
  assert.equal(rows[0]!.count, '0');
  const { rows: ledgerRows } = await db.pool.query<{ count: string }>(
    `SELECT count(*)::text AS count FROM payment_ledger WHERE date_proposal_id = $1 AND type = 'venue_payout'`,
    [dateProposalId],
  );
  assert.equal(ledgerRows[0]!.count, '0');
});

test('no_show does NOT settle venue payment', async () => {
  const pair = await setupPair();
  const dateProposalId = await ticketedFlow(pair, 200);
  const updated = await dateProposalService.markNoShow(makeCtx(db, adminActor()), dateProposalId, pair.proposerId);
  assert.equal(updated.status, 'no_show');

  const result = await venueSettlementService.settleDueVenuePayouts(makeCtx(db, systemActor()));
  assert.equal(result.settled, 0);
  const { rows } = await db.pool.query<{ count: string }>('SELECT count(*)::text AS count FROM venue_settlements WHERE date_proposal_id = $1', [dateProposalId]);
  assert.equal(rows[0]!.count, '0');
});

test('canceled (inside the full-refund cutoff, post-acceptance) does NOT settle venue payment', async () => {
  const pair = await setupPair();
  const dateProposalId = await ticketedFlow(pair, 10); // inside the 24h default cutoff
  const canceled = await dateProposalService.cancelDateProposal(pair.proposerCtx, dateProposalId);
  assert.equal(canceled.status, 'canceled');

  const result = await venueSettlementService.settleDueVenuePayouts(makeCtx(db, systemActor()));
  assert.equal(result.settled, 0);
  const { rows } = await db.pool.query<{ count: string }>('SELECT count(*)::text AS count FROM venue_settlements WHERE date_proposal_id = $1', [dateProposalId]);
  assert.equal(rows[0]!.count, '0');
});

test('refunded (outside the full-refund cutoff, post-acceptance) does NOT settle venue payment', async () => {
  const pair = await setupPair();
  const dateProposalId = await ticketedFlow(pair, 100);
  db.clock.advanceHours(75); // now 25h before scheduledStart — outside (more than) the 24h cutoff
  const refunded = await dateProposalService.cancelDateProposal(pair.proposerCtx, dateProposalId);
  assert.equal(refunded.status, 'refunded');

  const result = await venueSettlementService.settleDueVenuePayouts(makeCtx(db, systemActor()));
  assert.equal(result.settled, 0);
  const { rows } = await db.pool.query<{ count: string }>('SELECT count(*)::text AS count FROM venue_settlements WHERE date_proposal_id = $1', [dateProposalId]);
  assert.equal(rows[0]!.count, '0');
});

test('disputed (only one confirmation, window elapsed) does NOT settle venue payment', async () => {
  const pair = await setupPair();
  const dateProposalId = await ticketedFlow(pair, 2);
  db.clock.advanceHours(3); // past scheduledEnd
  await dateProposalService.confirmAttendance(pair.proposerCtx, dateProposalId);

  db.clock.advanceHours(75); // past the default 72h no_scan_confirmation_hours window
  const result1 = await dateProposalService.confirmAttendance(pair.proposerCtx, dateProposalId);
  assert.equal(result1.dateProposal.status, 'disputed');

  const result = await venueSettlementService.settleDueVenuePayouts(makeCtx(db, systemActor()));
  assert.equal(result.settled, 0);
  const { rows } = await db.pool.query<{ count: string }>('SELECT count(*)::text AS count FROM venue_settlements WHERE date_proposal_id = $1', [dateProposalId]);
  assert.equal(rows[0]!.count, '0');
});
