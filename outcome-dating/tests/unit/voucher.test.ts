/**
 * voucher.service.ts unit tests. Spec §15.1, §15.2, §15's state machine.
 *
 * Covers: issuance is idempotent per date proposal, the QR payload signed
 * token's shape (§15.2's exact field list, no PII/card data), a tampered
 * payload is rejected, an expired voucher is rejected at redemption time,
 * and the issued/redeemed/expired/canceled lifecycle.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import * as voucherService from '../../src/services/voucher.service.js';
import { InvalidSignatureError } from '../../src/lib/signing.js';
import { ConflictError, ForbiddenError, NotFoundError } from '../../src/lib/errors.js';
import {
  setupTestDb,
  teardownTestDb,
  makeCtx,
  userActor,
  systemActor,
  createUser,
  createVenue,
  createConversation,
  type TestDb,
} from './testHarness.js';

let db: TestDb;

before(async () => {
  db = await setupTestDb('voucher');
});

after(async () => {
  await teardownTestDb(db);
});

async function ticketedProposal(overrides?: { scheduledEnd?: Date }): Promise<{ id: string; proposerId: string; recipientId: string; venueId: string }> {
  const proposerId = await createUser(db);
  const recipientId = await createUser(db);
  const venueId = await createVenue(db);
  const conversationId = await createConversation(db, proposerId, recipientId);
  const scheduledEnd = overrides?.scheduledEnd ?? new Date(db.clock.now().getTime() + 2 * 60 * 60 * 1000);
  const { rows } = await db.pool.query<{ id: string }>(
    `INSERT INTO date_proposals (conversation_id, proposer_id, recipient_id, venue_id, scheduled_start, scheduled_end, status, policy_snapshot, escrow_amount_cents, charged_at, ticketed_at)
     VALUES ($1, $2, $3, $4, $5, $6, 'ticketed', '{}'::jsonb, 2000, now(), now())
     RETURNING id`,
    [conversationId, proposerId, recipientId, venueId, new Date(scheduledEnd.getTime() - 2 * 60 * 60 * 1000), scheduledEnd],
  );
  return { id: rows[0]!.id, proposerId, recipientId, venueId };
}

test('issueVoucher: creates a voucher with a signed QR payload matching §15.2 exactly, no PII', async () => {
  const proposal = await ticketedProposal();
  const ctx = makeCtx(db, systemActor());

  const voucher = await voucherService.issueVoucher(ctx, proposal.id);
  assert.equal(voucher.status, 'issued');
  assert.equal(voucher.dateProposalId, proposal.id);
  assert.equal(voucher.venueId, proposal.venueId);
  assert.ok(voucher.code.length > 0);
  assert.ok(voucher.qrPayload.length > 0);

  const decoded = voucherService.verifyQrPayload(ctx, voucher.qrPayload);
  assert.deepEqual(Object.keys(decoded).sort(), ['date_proposal_id', 'expires_at', 'venue_id', 'voucher_id'].sort());
  assert.equal(decoded.voucher_id, voucher.id);
  assert.equal(decoded.venue_id, proposal.venueId);
  assert.equal(decoded.date_proposal_id, proposal.id);

  const serialized = JSON.stringify(decoded);
  assert.ok(!serialized.includes('@'), 'no email address should ever appear in the QR payload');
  assert.ok(!/card|last4|token/i.test(serialized), 'no payment card data should ever appear in the QR payload');
});

test('issueVoucher: idempotent, a second call for the same date proposal returns the same voucher', async () => {
  const proposal = await ticketedProposal();
  const ctx = makeCtx(db, systemActor());

  const first = await voucherService.issueVoucher(ctx, proposal.id);
  const second = await voucherService.issueVoucher(ctx, proposal.id);
  assert.equal(second.id, first.id);
  assert.equal(second.qrPayload, first.qrPayload);

  const { rows } = await db.pool.query<{ count: string }>(`SELECT count(*)::text AS count FROM vouchers WHERE date_proposal_id = $1`, [proposal.id]);
  assert.equal(rows[0]!.count, '1');
});

test('verifyQrPayload: a tampered payload is rejected', async () => {
  const proposal = await ticketedProposal();
  const ctx = makeCtx(db, systemActor());
  const voucher = await voucherService.issueVoucher(ctx, proposal.id);

  const [payloadPart, sigPart] = voucher.qrPayload.split('.');
  // Flip the decoded payload's voucher_id but keep the original signature,
  // a forged/tampered token.
  const decodedPayload = JSON.parse(Buffer.from(payloadPart!, 'base64url').toString('utf8'));
  decodedPayload.voucher_id = 'attacker-controlled-id';
  const tampered = `${Buffer.from(JSON.stringify(decodedPayload)).toString('base64url')}.${sigPart}`;

  assert.throws(() => voucherService.verifyQrPayload(ctx, tampered), InvalidSignatureError);
});

test('verifyQrPayload: a structurally invalid token is rejected', () => {
  const ctx = makeCtx(db, systemActor());
  assert.throws(() => voucherService.verifyQrPayload(ctx, 'not-a-real-token'), InvalidSignatureError);
});

test('markRedeemed: rejects an expired voucher even though the expiry job has not swept it yet', async () => {
  // Schedule the date in the past relative to the clock so the computed
  // expires_at (scheduled_end + voucher.expiry_hours_after_date_end) is
  // already behind "now".
  const past = new Date(db.clock.now().getTime() - 200 * 60 * 60 * 1000);
  const proposal = await ticketedProposal({ scheduledEnd: past });
  const ctx = makeCtx(db, systemActor());
  const voucher = await voucherService.issueVoucher(ctx, proposal.id);
  assert.ok(voucher.expiresAt.getTime() < db.clock.now().getTime(), 'test setup: voucher should already be past its expiry');

  await assert.rejects(() => voucherService.markRedeemed(ctx, voucher.id), ConflictError);
});

test('expireDueVouchers: sweeps issued-but-expired vouchers to expired', async () => {
  const past = new Date(db.clock.now().getTime() - 300 * 60 * 60 * 1000);
  const proposal = await ticketedProposal({ scheduledEnd: past });
  const ctx = makeCtx(db, systemActor());
  const voucher = await voucherService.issueVoucher(ctx, proposal.id);

  const { expired } = await voucherService.expireDueVouchers(ctx);
  assert.ok(expired >= 1);

  const reloaded = await voucherService.getVoucher(ctx, voucher.id);
  assert.equal(reloaded.status, 'expired');
});

test('markRedeemed: happy path transitions issued -> redeemed', async () => {
  const proposal = await ticketedProposal();
  const ctx = makeCtx(db, systemActor());
  const voucher = await voucherService.issueVoucher(ctx, proposal.id);

  const redeemed = await voucherService.markRedeemed(ctx, voucher.id);
  assert.equal(redeemed.status, 'redeemed');
  assert.ok(redeemed.redeemedAt);

  await assert.rejects(() => voucherService.markRedeemed(ctx, voucher.id), ConflictError, 'cannot redeem twice');
});

test('cancelVoucher: cancels an issued voucher; rejects canceling an already-redeemed one', async () => {
  const proposal = await ticketedProposal();
  const ctx = makeCtx(db, systemActor());
  const voucher = await voucherService.issueVoucher(ctx, proposal.id);

  const canceled = await voucherService.cancelVoucher(ctx, voucher.id);
  assert.equal(canceled.status, 'canceled');
  // idempotent
  const canceledAgain = await voucherService.cancelVoucher(ctx, voucher.id);
  assert.equal(canceledAgain.status, 'canceled');

  const proposal2 = await ticketedProposal();
  const voucher2 = await voucherService.issueVoucher(ctx, proposal2.id);
  await voucherService.markRedeemed(ctx, voucher2.id);
  await assert.rejects(() => voucherService.cancelVoucher(ctx, voucher2.id), ConflictError);
});

test('getVoucher / listMyVouchers: access control, a non-participant cannot view the voucher, participants can', async () => {
  const proposal = await ticketedProposal();
  const systemCtx = makeCtx(db, systemActor());
  const voucher = await voucherService.issueVoucher(systemCtx, proposal.id);

  const proposerCtx = makeCtx(db, userActor(proposal.proposerId));
  const fetched = await voucherService.getVoucher(proposerCtx, voucher.id);
  assert.equal(fetched.id, voucher.id);

  const strangerId = await createUser(db);
  const strangerCtx = makeCtx(db, userActor(strangerId));
  await assert.rejects(() => voucherService.getVoucher(strangerCtx, voucher.id), ForbiddenError);

  const mine = await voucherService.listMyVouchers(makeCtx(db, userActor(proposal.recipientId)));
  assert.ok(mine.some((v) => v.id === voucher.id));
});

test('getVoucher: unknown id is NotFoundError', async () => {
  const ctx = makeCtx(db, systemActor());
  await assert.rejects(() => voucherService.getVoucher(ctx, '00000000-0000-0000-0000-000000000000'), NotFoundError);
});
