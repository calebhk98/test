/**
 * dateProposal.service.ts unit tests. Spec §13, §14, §15.4, §21.3, §30.5.
 *
 * `conversation.service.ts`, `notification.service.ts`, and
 * `trust.service.ts` are now fully implemented and are each independently
 * tested elsewhere (`tests/unit/{chat,notification,trust}.test.ts`). This
 * file used to substitute hand-written `mock.module()` fakes for those
 * three services (a workaround from when they were still
 * `NotImplementedError` stubs mid-parallel-build); that justification no
 * longer holds, and the fakes were never revisited once the real services
 * shipped, so every trust/notification assertion below was only proving
 * `dateProposal.service.ts` called *something* shaped like the fake, not
 * that it was correctly wired to production code (test-audit.md Finding
 * 1). The mocks are gone — every service this file exercises
 * (`conversation`, `notification`, `trust`, `venue`, `payment`, `ledger`,
 * `voucher`) is the real, fully-implemented code; nothing is faked.
 *
 * IMPORTANT test-construction note: `ctx.payments` is a stateful fake
 * (`FakeProcessor`) representing ONE external processor account. Every
 * `Ctx` built for actors who share a date proposal (proposer, recipient,
 * the admin/system/venue-staff actor that later acts on it) MUST be given
 * the SAME `FakeProcessor` instance — two different instances would be two
 * different "processors" that don't know about each other's intents. Every
 * helper below threads one shared `processor` through a whole flow.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import type { Ctx } from '../../src/lib/ctx.js';
import { FakeProcessor } from '../../src/services/payments/fake.processor.js';
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
  type TestDb,
} from './testHarness.js';
import * as dateProposalService from '../../src/services/dateProposal.service.js';
import * as redemptionService from '../../src/services/redemption.service.js';
import * as voucherService from '../../src/services/voucher.service.js';
import * as ledgerService from '../../src/services/ledger.service.js';
import { ConflictError, NotFoundError, ValidationError } from '../../src/lib/errors.js';
import { ConfigService } from '../../src/config/config.service.js';

// ---------------------------------------------------------------------

let db: TestDb;

before(async () => {
  db = await setupTestDb('dateproposal');
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
  proposerCtx: Ctx;
  recipientCtx: Ctx;
}

async function setupPair(tokens?: { proposer?: string; recipient?: string }): Promise<Pair> {
  const proposerId = await createUser(db);
  const recipientId = await createUser(db);
  await createPaymentMethod(db, proposerId, tokens?.proposer ?? 'tok_good');
  await createPaymentMethod(db, recipientId, tokens?.recipient ?? 'tok_good');
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

function futureRange(hoursFromNow: number): { scheduledStart: Date; scheduledEnd: Date } {
  const start = new Date(db.clock.now().getTime() + hoursFromNow * 60 * 60 * 1000);
  return { scheduledStart: start, scheduledEnd: new Date(start.getTime() + 2 * 60 * 60 * 1000) };
}

async function holdRow(userId: string, dateProposalId: string): Promise<{ status: string; amount_cents: string } | undefined> {
  const { rows } = await db.pool.query<{ status: string; amount_cents: string }>(
    `SELECT status, amount_cents FROM payment_holds WHERE date_proposal_id = $1 AND user_id = $2`,
    [dateProposalId, userId],
  );
  return rows[0];
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

// =====================================================================
// §21.3 policy snapshot immutability
// =====================================================================

test('proposeDate: policy snapshot is captured at creation and never re-read from live config', async () => {
  const pair = await setupPair();

  const first = await dateProposalService.proposeDate(pair.proposerCtx, { conversationId: pair.conversationId, venueId: pair.venueId, ...futureRange(100) });
  assert.equal(first.escrowAmountCents, 2000);
  assert.equal(first.policySnapshot['date.accept_expiry_hours'], 48);

  // Change live config after the snapshot was captured.
  await db.config.set('date.escrow_amount_cents', 5000, 'test-admin');
  await db.config.set('date.accept_expiry_hours', 12, 'test-admin');

  const reloaded = await dateProposalService.getDateProposal(pair.proposerCtx, first.id);
  assert.equal(reloaded.escrowAmountCents, 2000, 'an existing proposal must keep its original escrow amount');
  assert.equal(reloaded.policySnapshot['date.accept_expiry_hours'], 48, 'an existing proposal must keep its original accept-expiry policy');

  // A brand new proposal, created after the config change, sees the new value.
  const pair2 = await setupPair();
  const second = await dateProposalService.proposeDate(pair2.proposerCtx, {
    conversationId: pair2.conversationId,
    venueId: pair2.venueId,
    ...futureRange(100),
  });
  assert.equal(second.escrowAmountCents, 5000, 'a proposal created after the config change should use the new value');

  // restore defaults for subsequent tests
  await db.config.set('date.escrow_amount_cents', 2000, 'test-admin');
  await db.config.set('date.accept_expiry_hours', 48, 'test-admin');
});

// =====================================================================
// Gating: active conversation, participant, active venue
// =====================================================================

test('proposeDate: rejects a conversation that is not active', async () => {
  const pair = await setupPair();
  await db.pool.query(`UPDATE conversations SET status = 'archived' WHERE id = $1`, [pair.conversationId]);
  await assert.rejects(
    () => dateProposalService.proposeDate(pair.proposerCtx, { conversationId: pair.conversationId, venueId: pair.venueId, ...futureRange(100) }),
    ConflictError,
  );
});

test('proposeDate: rejects a non-participant, and an inactive venue', async () => {
  const pair = await setupPair();
  const strangerId = await createUser(db);
  const strangerCtx = makeCtx(db, userActor(strangerId), { payments: pair.processor });
  // NotFoundError, not ForbiddenError: conversation.service#getConversation
  // deliberately returns the same "not found" error for "doesn't exist" and
  // "exists but you're not a participant" (its own doc comment: "don't leak
  // existence of a conversation the caller isn't part of"), and proposeDate
  // calls getConversation before it can ever reach its own participant
  // check. This assertion used to expect ForbiddenError, which only held
  // under this file's old mock.module() fake for conversation.service.ts
  // (a fake that, unlike the real service, returned the row regardless of
  // participant) — real code was never exercised. Removing that stale mock
  // (test-audit.md Finding 1) surfaced the mismatch; the real, real-service
  // behavior below is the intended, more enumeration-safe one, so the test
  // is updated to match it rather than weakened or the production code
  // changed to leak existence.
  await assert.rejects(
    () => dateProposalService.proposeDate(strangerCtx, { conversationId: pair.conversationId, venueId: pair.venueId, ...futureRange(100) }),
    NotFoundError,
  );

  const inactiveVenue = await createVenue(db, { active: false });
  await assert.rejects(
    () => dateProposalService.proposeDate(pair.proposerCtx, { conversationId: pair.conversationId, venueId: inactiveVenue, ...futureRange(100) }),
    ValidationError,
  );
});

// =====================================================================
// Happy path end-to-end: propose -> accept -> capture -> ticket -> redeem
// -> completed + established
// =====================================================================

test('happy path: propose -> accept -> capture -> ticket -> redeem -> completed + conversation established', async () => {
  const pair = await setupPair();

  const proposed = await dateProposalService.proposeDate(pair.proposerCtx, { conversationId: pair.conversationId, venueId: pair.venueId, ...futureRange(72) });
  assert.equal(proposed.status, 'pending_acceptance');

  const proposerHoldAfterPropose = await holdRow(pair.proposerId, proposed.id);
  assert.equal(proposerHoldAfterPropose?.status, 'authorized');
  const recipientHoldAfterPropose = await holdRow(pair.recipientId, proposed.id);
  assert.equal(recipientHoldAfterPropose, undefined, 'recipient must not be touched until acceptance (spec §14.2 Step 1: no charge yet)');

  const accepted = await dateProposalService.acceptDateProposal(pair.recipientCtx, proposed.id);
  assert.equal(accepted.status, 'ticketed');
  assert.ok(accepted.chargedAt);
  assert.ok(accepted.ticketedAt);

  const proposerHold = await holdRow(pair.proposerId, proposed.id);
  const recipientHold = await holdRow(pair.recipientId, proposed.id);
  assert.equal(proposerHold?.status, 'captured');
  assert.equal(recipientHold?.status, 'captured');

  const vouchers = await voucherService.listMyVouchers(pair.proposerCtx);
  const voucher = vouchers.find((v) => v.dateProposalId === proposed.id);
  assert.ok(voucher, 'a voucher must exist once ticketed');
  assert.equal(voucher!.status, 'issued');

  // Venue staff redeems.
  const venueStaffUserId = await createUser(db);
  const { rows: staffRows } = await db.pool.query<{ id: string }>(
    `INSERT INTO venue_staff (user_id, venue_id, active) VALUES ($1, $2, true) RETURNING id`,
    [venueStaffUserId, pair.venueId],
  );
  const staffCtx = makeCtx(db, venueStaffActor(staffRows[0]!.id, pair.venueId), { payments: pair.processor });

  const result = await redemptionService.redeemByStaff(staffCtx, { qrPayload: voucher!.qrPayload });
  assert.equal(result.voucher.status, 'redeemed');
  assert.equal(result.dateProposal.status, 'completed');
  assert.equal(result.redemption.method, 'qr_scan');
  assert.equal(result.redemption.venueStaffId, staffRows[0]!.id);

  const finalProposal = await dateProposalService.getDateProposal(pair.proposerCtx, proposed.id);
  assert.equal(finalProposal.status, 'completed');
  assert.ok(finalProposal.completedAt);

  const { rows: convRows } = await db.pool.query<{ status: string }>(`SELECT status FROM conversations WHERE id = $1`, [pair.conversationId]);
  assert.equal(convRows[0]!.status, 'established', 'conversation must be established on redemption (spec §15.3)');

  // Ledger reconciles: both users captured exactly the escrow amount, nothing refunded.
  assert.equal(await captureLedgerTotal(proposed.id, pair.proposerId), 2000);
  assert.equal(await captureLedgerTotal(proposed.id, pair.recipientId), 2000);

  // Staff-facing result carries no chat/email/card data (spec §4.2) — the
  // fields simply don't exist on these types.
  assert.deepEqual(Object.keys(result).sort(), ['dateProposal', 'redemption', 'voucher'].sort());
});

// =====================================================================
// §14.5 failure paths — nobody is ever charged alone
// =====================================================================

test('§14.5: proposer authorization fails -> payment_failed, nobody captured', async () => {
  const pair = await setupPair({ proposer: 'tok_fail_authorize' });

  const proposed = await dateProposalService.proposeDate(pair.proposerCtx, { conversationId: pair.conversationId, venueId: pair.venueId, ...futureRange(72) });
  assert.equal(proposed.status, 'payment_failed');

  const proposerHold = await holdRow(pair.proposerId, proposed.id);
  assert.equal(proposerHold?.status, 'failed');
  assert.equal(await captureLedgerTotal(proposed.id, pair.proposerId), 0);
});

test('§14.5/§30.5: recipient authorization fails -> payment_failed AND the proposer hold is released', async () => {
  const pair = await setupPair({ recipient: 'tok_fail_authorize' });

  const proposed = await dateProposalService.proposeDate(pair.proposerCtx, { conversationId: pair.conversationId, venueId: pair.venueId, ...futureRange(72) });
  assert.equal(proposed.status, 'pending_acceptance');
  assert.equal((await holdRow(pair.proposerId, proposed.id))?.status, 'authorized');

  const result = await dateProposalService.acceptDateProposal(pair.recipientCtx, proposed.id);
  assert.equal(result.status, 'payment_failed');

  assert.equal((await holdRow(pair.proposerId, proposed.id))?.status, 'released', 'the proposer must never be left holding an authorized-but-abandoned hold');
  assert.equal((await holdRow(pair.recipientId, proposed.id))?.status, 'failed');
  assert.equal(await captureLedgerTotal(proposed.id, pair.proposerId), 0);
  assert.equal(await captureLedgerTotal(proposed.id, pair.recipientId), 0);
});

test('§14.5: capture fails for the proposer -> payment_failed AND the recipient hold is released (nobody captured)', async () => {
  const pair = await setupPair({ proposer: 'tok_fail_capture' });

  const proposed = await dateProposalService.proposeDate(pair.proposerCtx, { conversationId: pair.conversationId, venueId: pair.venueId, ...futureRange(72) });
  assert.equal(proposed.status, 'pending_acceptance'); // authorize succeeded — fail_capture only trips capture()

  const result = await dateProposalService.acceptDateProposal(pair.recipientCtx, proposed.id);
  assert.equal(result.status, 'payment_failed');

  assert.equal((await holdRow(pair.proposerId, proposed.id))?.status, 'failed');
  assert.equal((await holdRow(pair.recipientId, proposed.id))?.status, 'released');
  assert.equal(await captureLedgerTotal(proposed.id, pair.proposerId), 0);
  assert.equal(await captureLedgerTotal(proposed.id, pair.recipientId), 0, 'the recipient was released before ever being captured');
});

test('§14.5/§30.5: capture fails for the recipient AFTER the proposer already captured -> the proposer is REFUNDED, not left charged alone', async () => {
  const pair = await setupPair({ recipient: 'tok_fail_capture' });

  const proposed = await dateProposalService.proposeDate(pair.proposerCtx, { conversationId: pair.conversationId, venueId: pair.venueId, ...futureRange(72) });
  const result = await dateProposalService.acceptDateProposal(pair.recipientCtx, proposed.id);
  assert.equal(result.status, 'payment_failed');

  const proposerHold = await holdRow(pair.proposerId, proposed.id);
  assert.equal(proposerHold?.status, 'refunded', 'money moved for the proposer, so undoing it must be a refund, not a release');
  assert.equal((await holdRow(pair.recipientId, proposed.id))?.status, 'failed');

  assert.equal(await captureLedgerTotal(proposed.id, pair.proposerId), 0, 'captured then fully refunded nets to zero — the proposer was not left charged alone');
  assert.equal(await captureLedgerTotal(proposed.id, pair.recipientId), 0);
});

// =====================================================================
// §14.6 acceptance expiry
// =====================================================================

test('§14.6: an un-accepted proposal expires after accept_expiry_hours and releases the proposer hold', async () => {
  const pair = await setupPair();
  const proposed = await dateProposalService.proposeDate(pair.proposerCtx, { conversationId: pair.conversationId, venueId: pair.venueId, ...futureRange(200) });
  assert.equal((await holdRow(pair.proposerId, proposed.id))?.status, 'authorized');

  const systemCtx = makeCtx(db, systemActor(), { payments: pair.processor });

  db.clock.advanceHours(47);
  await dateProposalService.expireDuePendingProposals(systemCtx);
  const stillPending = await dateProposalService.getDateProposal(pair.proposerCtx, proposed.id);
  assert.equal(stillPending.status, 'pending_acceptance', 'must not expire before the 48h default window elapses');

  db.clock.advanceHours(2); // now 49h total
  const { expired } = await dateProposalService.expireDuePendingProposals(systemCtx);
  assert.ok(expired >= 1);

  const reloaded = await dateProposalService.getDateProposal(pair.proposerCtx, proposed.id);
  assert.equal(reloaded.status, 'expired');
  assert.ok(reloaded.expiredAt);
  assert.equal((await holdRow(pair.proposerId, proposed.id))?.status, 'released');
});

// =====================================================================
// §14.7 cancellation — the 24h full-refund cutoff boundary, both sides
// =====================================================================

interface Flow {
  proposalId: string;
  scheduledStart: Date;
  proposerId: string;
  recipientId: string;
  processor: FakeProcessor;
}

async function ticketedFlow(hoursUntilDateAtCreation: number): Promise<Flow> {
  const pair = await setupPair();
  const { scheduledStart, scheduledEnd } = futureRange(hoursUntilDateAtCreation);
  const proposed = await dateProposalService.proposeDate(pair.proposerCtx, { conversationId: pair.conversationId, venueId: pair.venueId, scheduledStart, scheduledEnd });
  const accepted = await dateProposalService.acceptDateProposal(pair.recipientCtx, proposed.id);
  assert.equal(accepted.status, 'ticketed');
  return { proposalId: proposed.id, scheduledStart, proposerId: pair.proposerId, recipientId: pair.recipientId, processor: pair.processor };
}

test('§14.7 boundary: canceling at EXACTLY 24h before the date is a full refund for both sides', async () => {
  const flow = await ticketedFlow(100);
  // Move the clock to precisely 24.0 hours before scheduledStart.
  db.clock.set(new Date(flow.scheduledStart.getTime() - 24 * 60 * 60 * 1000));

  const ctx = makeCtx(db, userActor(flow.proposerId), { payments: flow.processor });
  const canceled = await dateProposalService.cancelDateProposal(ctx, flow.proposalId);
  assert.equal(canceled.status, 'refunded', 'exactly 24h out must land on the full-refund side of the ">= cutoff" boundary');

  assert.equal((await holdRow(flow.proposerId, flow.proposalId))?.status, 'refunded');
  assert.equal((await holdRow(flow.recipientId, flow.proposalId))?.status, 'refunded');
  assert.equal(await captureLedgerTotal(flow.proposalId, flow.proposerId), 0, 'fully refunded nets to zero for the proposer');
  assert.equal(await captureLedgerTotal(flow.proposalId, flow.recipientId), 0, 'fully refunded nets to zero for the recipient too — both sides');
});

test('§14.7 boundary: canceling just INSIDE 24h before the date applies the (default 0%) late-cancel policy instead', async () => {
  const flow = await ticketedFlow(100);
  // 23.5 hours before scheduledStart — inside the cutoff.
  db.clock.set(new Date(flow.scheduledStart.getTime() - 23.5 * 60 * 60 * 1000));

  const ctx = makeCtx(db, userActor(flow.recipientId), { payments: flow.processor });
  const canceled = await dateProposalService.cancelDateProposal(ctx, flow.proposalId);
  assert.equal(canceled.status, 'canceled', 'inside the cutoff, the outcome is "canceled", not "refunded"');

  assert.equal((await holdRow(flow.proposerId, flow.proposalId))?.status, 'captured', 'default late_cancel_refund_percent is 0 — no refund is issued, the hold stays captured');
  assert.equal((await holdRow(flow.recipientId, flow.proposalId))?.status, 'captured');
  assert.equal(await captureLedgerTotal(flow.proposalId, flow.proposerId), 2000);
  assert.equal(await captureLedgerTotal(flow.proposalId, flow.recipientId), 2000);
});

test('cancelDateProposal before acceptance releases only the proposer hold', async () => {
  const pair = await setupPair();
  const proposed = await dateProposalService.proposeDate(pair.proposerCtx, { conversationId: pair.conversationId, venueId: pair.venueId, ...futureRange(100) });

  const canceled = await dateProposalService.cancelDateProposal(pair.proposerCtx, proposed.id);
  assert.equal(canceled.status, 'canceled');
  assert.equal((await holdRow(pair.proposerId, proposed.id))?.status, 'released');
});

// =====================================================================
// Illegal transitions are rejected
// =====================================================================

test('illegal transitions are rejected with ConflictError', async () => {
  const pair = await setupPair();
  const proposed = await dateProposalService.proposeDate(pair.proposerCtx, { conversationId: pair.conversationId, venueId: pair.venueId, ...futureRange(100) });

  const declined = await dateProposalService.declineDateProposal(pair.recipientCtx, proposed.id);
  assert.equal(declined.status, 'declined');

  await assert.rejects(() => dateProposalService.acceptDateProposal(pair.recipientCtx, proposed.id), ConflictError);
  await assert.rejects(() => dateProposalService.declineDateProposal(pair.recipientCtx, proposed.id), ConflictError);
  await assert.rejects(() => dateProposalService.cancelDateProposal(pair.proposerCtx, proposed.id), ConflictError);
});

// =====================================================================
// markNoShow — asymmetric refund (no-show forfeits, the other party is
// made whole)
// =====================================================================

test('markNoShow: the no-show party forfeits per policy, the other party is refunded in full', async () => {
  const flow = await ticketedFlow(200);
  const adminCtx = makeCtx(db, adminActor(), { payments: flow.processor });

  const updated = await dateProposalService.markNoShow(adminCtx, flow.proposalId, flow.proposerId);
  assert.equal(updated.status, 'no_show');

  assert.equal((await holdRow(flow.proposerId, flow.proposalId))?.status, 'captured', 'default no_show_refund_percent is 0 — the no-show party is not refunded');
  assert.equal((await holdRow(flow.recipientId, flow.proposalId))?.status, 'refunded', 'the party who showed up is made whole');
  assert.equal(await captureLedgerTotal(flow.proposalId, flow.recipientId), 0);
  assert.equal(await captureLedgerTotal(flow.proposalId, flow.proposerId), 2000);

  const { rows } = await db.pool.query<{ count: string }>(
    `SELECT count(*)::text AS count FROM trust_events WHERE user_id = $1 AND event_type = 'no_show'`,
    [flow.proposerId],
  );
  assert.equal(rows[0]!.count, '1', 'a no-show trust event must be recorded for the no-show party');
});

// =====================================================================
// §15.4 no-scan fallback: completed_unverified vs disputed
// =====================================================================

test('§15.4: both users confirming within the window yields completed_unverified + established conversation, without a venue redemption row', async () => {
  const flow = await ticketedFlow(2); // date already effectively "now"
  db.clock.advanceHours(3); // past scheduledEnd
  const proposerCtx = makeCtx(db, userActor(flow.proposerId), { payments: flow.processor });
  const recipientCtx = makeCtx(db, userActor(flow.recipientId), { payments: flow.processor });

  const r1 = await dateProposalService.confirmAttendance(proposerCtx, flow.proposalId);
  assert.equal(r1.dateProposal.status, 'ticketed', 'only one confirmation so far');

  const r2 = await dateProposalService.confirmAttendance(recipientCtx, flow.proposalId);
  assert.equal(r2.dateProposal.status, 'completed_unverified');
  assert.ok(r2.dateProposal.completedAt);

  const { rows: convRows } = await db.pool.query<{ status: string }>(
    `SELECT status FROM conversations WHERE id = (SELECT conversation_id FROM date_proposals WHERE id = $1)`,
    [flow.proposalId],
  );
  assert.equal(convRows[0]!.status, 'established');

  // §15.4 "does not automatically settle venue payment": no venue_redemptions row was ever created for this path.
  const { rows: redemptionRows } = await db.pool.query<{ count: string }>(
    `SELECT count(*)::text AS count FROM venue_redemptions vr JOIN vouchers v ON v.id = vr.voucher_id WHERE v.date_proposal_id = $1`,
    [flow.proposalId],
  );
  assert.equal(redemptionRows[0]!.count, '0');

  // Both users' escrow is still fully captured — the fallback path never touches payment.
  assert.equal(await captureLedgerTotal(flow.proposalId, flow.proposerId), 2000);
  assert.equal(await captureLedgerTotal(flow.proposalId, flow.recipientId), 2000);
});

test('§15.4: only one user confirming, after the confirmation window elapses, yields disputed', async () => {
  const flow = await ticketedFlow(2);
  db.clock.advanceHours(3); // past scheduledEnd
  const proposerCtx = makeCtx(db, userActor(flow.proposerId), { payments: flow.processor });
  await dateProposalService.confirmAttendance(proposerCtx, flow.proposalId);

  db.clock.advanceHours(75); // comfortably past the default 72h no_scan_confirmation_hours window (measured from scheduledEnd, itself 2h after this flow's already-3h-advanced "now")
  const result = await dateProposalService.confirmAttendance(proposerCtx, flow.proposalId);
  assert.equal(result.dateProposal.status, 'disputed');
});

test('proposeDate: config service default sanity (§21.4 escrow default is $20)', async () => {
  const config = new ConfigService(db.pool, db.clock, makeCtx(db, systemActor()).logger);
  assert.equal(await config.get('date.escrow_amount_cents'), 2000);
});
