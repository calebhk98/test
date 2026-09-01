/**
 * True concurrency test for voucher redemption (spec §15.3, §24.9): two
 * simultaneous redemption attempts against the SAME voucher must never
 * both succeed.
 *
 * Unlike `dateProposal.service.ts`'s accept/cancel (see
 * `dateProposalRace.test.ts`), `redemption.service.ts#runRedemption`
 * already does this correctly: the whole redemption runs inside one
 * `withTransaction`, opened with `SELECT ... FROM vouchers WHERE id = $1
 * FOR UPDATE` — a real row lock, not a read-then-write race. This test is
 * the genuine-concurrency proof of that (test-audit.md Finding 3's
 * pattern, copied from `tests/jobs/scheduler.test.ts`), and — unlike the
 * dateProposal accept/cancel races — is expected to pass against the
 * code exactly as it already stands; no source change was needed here.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { ConflictError } from '../../src/lib/errors.js';
import { FakeProcessor } from '../../src/services/payments/fake.processor.js';
import * as dateProposalService from '../../src/services/dateProposal.service.js';
import * as voucherService from '../../src/services/voucher.service.js';
import * as redemptionService from '../../src/services/redemption.service.js';
import {
  setupTestDb,
  teardownTestDb,
  makeCtx,
  userActor,
  venueStaffActor,
  createUser,
  createPaymentMethod,
  createConversation,
  createVenue,
  type TestDb,
} from '../unit/testHarness.js';

let db: TestDb;

before(async () => {
  db = await setupTestDb('concurrency_redemption');
});

after(async () => {
  await teardownTestDb(db);
});

function futureRange(hoursFromNow: number): { scheduledStart: Date; scheduledEnd: Date } {
  const start = new Date(db.clock.now().getTime() + hoursFromNow * 60 * 60 * 1000);
  return { scheduledStart: start, scheduledEnd: new Date(start.getTime() + 2 * 60 * 60 * 1000) };
}

test('concurrent redemption of the SAME voucher: exactly one winner, never double-redeemed', async () => {
  const proposerId = await createUser(db);
  const recipientId = await createUser(db);
  await createPaymentMethod(db, proposerId, 'tok_good');
  await createPaymentMethod(db, recipientId, 'tok_good');
  const conversationId = await createConversation(db, proposerId, recipientId, 'active');
  const venueId = await createVenue(db);
  const processor = new FakeProcessor();
  const proposerCtx = makeCtx(db, userActor(proposerId), { payments: processor });
  const recipientCtx = makeCtx(db, userActor(recipientId), { payments: processor });

  const proposed = await dateProposalService.proposeDate(proposerCtx, { conversationId, venueId, ...futureRange(72) });
  await dateProposalService.acceptDateProposal(recipientCtx, proposed.id);

  const vouchers = await voucherService.listMyVouchers(proposerCtx);
  const voucher = vouchers.find((v) => v.dateProposalId === proposed.id);
  assert.ok(voucher, 'a voucher must exist once ticketed');
  assert.equal(voucher!.status, 'issued');

  const venueStaffUserId = await createUser(db);
  const { rows: staffRows } = await db.pool.query<{ id: string }>(
    `INSERT INTO venue_staff (user_id, venue_id, active) VALUES ($1, $2, true) RETURNING id`,
    [venueStaffUserId, venueId],
  );
  const staffCtx = makeCtx(db, venueStaffActor(staffRows[0]!.id, venueId), { payments: processor });

  // Two venue-staff devices scan the SAME QR at (effectively) the same
  // instant — a real scenario (a phone double-tap, two staff terminals).
  const [a, b] = await Promise.allSettled([
    redemptionService.redeemByStaff(staffCtx, { qrPayload: voucher!.qrPayload }),
    redemptionService.redeemByStaff(staffCtx, { qrPayload: voucher!.qrPayload }),
  ]);

  const fulfilled = [a, b].filter((r) => r.status === 'fulfilled');
  const rejected = [a, b].filter((r) => r.status === 'rejected');
  assert.equal(fulfilled.length, 1, 'exactly one of the two concurrent scans should succeed');
  assert.equal(rejected.length, 1, 'the loser must fail fast with a typed conflict, not silently no-op or double-redeem');
  assert.ok(
    (rejected[0] as PromiseRejectedResult).reason instanceof ConflictError,
    'the loser must get ConflictError from the voucher row lock, not a generic exception',
  );

  const { rows: redemptionRows } = await db.pool.query<{ count: string }>(
    `SELECT count(*)::text AS count FROM venue_redemptions WHERE voucher_id = $1`,
    [voucher!.id],
  );
  assert.equal(redemptionRows[0]!.count, '1', 'exactly one venue_redemptions row must exist, never two from the race');

  const reloadedVoucher = await voucherService.getVoucher(proposerCtx, voucher!.id);
  assert.equal(reloadedVoucher.status, 'redeemed');

  const reloadedProposal = await dateProposalService.getDateProposal(proposerCtx, proposed.id);
  assert.equal(reloadedProposal.status, 'completed', 'the date proposal must land on exactly one completion, not be double-processed');
});
