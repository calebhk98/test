/**
 * §25.8 Voucher Expiry job — boundary + idempotent re-run (mirrors
 * C-25.8.1 / C-15.SM.L2).
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestDb, teardownTestDb, makeCtx, createUser, createConversation, createVenue } from './testHarness.js';
import type { TestDb } from './testHarness.js';
import { runVoucherExpiryJob } from '../../src/jobs/voucherExpiry.job.js';

let db: TestDb;

before(async () => {
  db = await setupTestDb('voucher_expiry');
});

after(async () => {
  await teardownTestDb(db);
});

async function insertTicketedProposal(): Promise<string> {
  const a = await createUser(db);
  const b = await createUser(db);
  const conversationId = await createConversation(db, a, b);
  const venueId = await createVenue(db);
  const { rows } = await db.pool.query<{ id: string }>(
    `INSERT INTO date_proposals (conversation_id, proposer_id, recipient_id, venue_id, scheduled_start, scheduled_end, status, policy_snapshot, escrow_amount_cents)
     VALUES ($1, $2, $3, $4, now() - interval '3 days', now() - interval '3 days' + interval '1 hour', 'ticketed', '{}'::jsonb, 2000)
     RETURNING id`,
    [conversationId, a, b, venueId],
  );
  return rows[0]!.id;
}

async function insertVoucher(dateProposalId: string, venueId: string, expiresAt: Date, code: string): Promise<string> {
  const { rows } = await db.pool.query<{ id: string }>(
    `INSERT INTO vouchers (date_proposal_id, venue_id, code, qr_payload, status, expires_at) VALUES ($1, $2, $3, 'x', 'issued', $4) RETURNING id`,
    [dateProposalId, venueId, code, expiresAt],
  );
  return rows[0]!.id;
}

test('boundary: a not-yet-expired voucher is untouched, a past-expiry one is expired', async () => {
  const ctx = makeCtx(db);
  const now = ctx.clock.now();

  const dpA = await insertTicketedProposal();
  const { rows: venueRowA } = await db.pool.query<{ venue_id: string }>(`SELECT venue_id FROM date_proposals WHERE id = $1`, [dpA]);
  const dueVoucherId = await insertVoucher(dpA, venueRowA[0]!.venue_id, new Date(now.getTime() - 1000), 'DUE00001');

  const dpB = await insertTicketedProposal();
  const { rows: venueRowB } = await db.pool.query<{ venue_id: string }>(`SELECT venue_id FROM date_proposals WHERE id = $1`, [dpB]);
  const notDueVoucherId = await insertVoucher(dpB, venueRowB[0]!.venue_id, new Date(now.getTime() + 1000), 'NOTDUE001');

  const result = await runVoucherExpiryJob(ctx);
  assert.equal(result.expired, 1);

  const { rows } = await db.pool.query<{ id: string; status: string }>(`SELECT id, status FROM vouchers WHERE id = ANY($1::uuid[])`, [
    [dueVoucherId, notDueVoucherId],
  ]);
  const byId = new Map(rows.map((r) => [r.id, r.status]));
  assert.equal(byId.get(dueVoucherId), 'expired');
  assert.equal(byId.get(notDueVoucherId), 'issued');
});

test('idempotent re-run: running twice does not error and expires nothing new', async () => {
  const ctx = makeCtx(db);
  const dp = await insertTicketedProposal();
  const { rows: venueRow } = await db.pool.query<{ venue_id: string }>(`SELECT venue_id FROM date_proposals WHERE id = $1`, [dp]);
  await insertVoucher(dp, venueRow[0]!.venue_id, new Date(ctx.clock.now().getTime() - 1000), 'RERUN0001');

  const first = await runVoucherExpiryJob(ctx);
  assert.equal(first.expired, 1);
  const second = await runVoucherExpiryJob(ctx);
  assert.equal(second.expired, 0);
});

test('a REDEEMED voucher is never touched even if its expires_at has passed (terminal state, C-15.SM.I1)', async () => {
  const ctx = makeCtx(db);
  const dp = await insertTicketedProposal();
  const { rows: venueRow } = await db.pool.query<{ venue_id: string }>(`SELECT venue_id FROM date_proposals WHERE id = $1`, [dp]);
  const voucherId = await insertVoucher(dp, venueRow[0]!.venue_id, new Date(ctx.clock.now().getTime() - 1000), 'REDEEMED1');
  await db.pool.query(`UPDATE vouchers SET status = 'redeemed', redeemed_at = now() WHERE id = $1`, [voucherId]);

  await runVoucherExpiryJob(ctx);

  const { rows } = await db.pool.query<{ status: string }>(`SELECT status FROM vouchers WHERE id = $1`, [voucherId]);
  assert.equal(rows[0]!.status, 'redeemed');
});
