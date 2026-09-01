/**
 * `venue_payout_settlement` job — thin wrapper around
 * `venueSettlement.service#settleDueVenuePayouts` (§15.4/§13.2). The
 * settlement math itself is unit-tested in `tests/unit/venueSettlement.test.ts`
 * (owned elsewhere); this file only proves the job is reachable, actually
 * runs, and is idempotent across two runs.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestDb, teardownTestDb, makeCtx, createUser, createConversation, createVenue } from './testHarness.js';
import type { TestDb } from './testHarness.js';
import { runVenuePayoutSettlementJob } from '../../src/jobs/venuePayoutSettlement.job.js';

let db: TestDb;

before(async () => {
  db = await setupTestDb('venue_payout_settlement');
});

after(async () => {
  await teardownTestDb(db);
});

async function insertCompletedRedeemedProposal(grossPerSideCents = 2000): Promise<string> {
  const a = await createUser(db);
  const b = await createUser(db);
  const conversationId = await createConversation(db, a, b);
  const venueId = await createVenue(db);
  const now = db.clock.now();
  const scheduledStart = new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000);
  const scheduledEnd = new Date(scheduledStart.getTime() + 60 * 60 * 1000);
  const completedAt = new Date(now.getTime() - 2 * 24 * 60 * 60 * 1000);

  const { rows } = await db.pool.query<{ id: string }>(
    `INSERT INTO date_proposals (conversation_id, proposer_id, recipient_id, venue_id, scheduled_start, scheduled_end, status, policy_snapshot, escrow_amount_cents, completed_at)
     VALUES ($1, $2, $3, $4, $5, $6, 'completed', '{}'::jsonb, $7, $8)
     RETURNING id`,
    [conversationId, a, b, venueId, scheduledStart, scheduledEnd, grossPerSideCents, completedAt],
  );
  const dateProposalId = rows[0]!.id;

  for (const userId of [a, b]) {
    await db.pool.query(
      `INSERT INTO payment_holds (date_proposal_id, user_id, processor, amount_cents, currency, status, captured_at)
       VALUES ($1, $2, 'fake', $3, 'usd', 'captured', $4)`,
      [dateProposalId, userId, grossPerSideCents, now],
    );
  }

  const expiresAt = new Date(now.getTime() + 24 * 60 * 60 * 1000);
  const { rows: voucherRows } = await db.pool.query<{ id: string }>(
    `INSERT INTO vouchers (date_proposal_id, venue_id, code, qr_payload, status, expires_at, redeemed_at)
     VALUES ($1, $2, $3, 'payload', 'redeemed', $4, $5)
     RETURNING id`,
    [dateProposalId, venueId, `VPS${dateProposalId.slice(0, 8)}`, expiresAt, now],
  );
  await db.pool.query(
    `INSERT INTO venue_redemptions (voucher_id, venue_id, method) VALUES ($1, $2, 'manual_code')`,
    [voucherRows[0]!.id, venueId],
  );

  return dateProposalId;
}

test('runVenuePayoutSettlementJob settles a completed, venue-redeemed date proposal and inserts a venue_settlements row', async () => {
  const ctx = makeCtx(db);
  const dateProposalId = await insertCompletedRedeemedProposal();

  const result = await runVenuePayoutSettlementJob(ctx);
  assert.equal(result.settled, 1);
  assert.equal(result.settlements[0]!.dateProposalId, dateProposalId);
  assert.equal(result.settlements[0]!.venuePayoutCents + result.settlements[0]!.platformCents, result.settlements[0]!.grossEscrowCents);

  const { rows } = await db.pool.query<{ count: string }>(
    `SELECT count(*)::text AS count FROM venue_settlements WHERE date_proposal_id = $1`,
    [dateProposalId],
  );
  assert.equal(Number(rows[0]!.count), 1);
});

test('runVenuePayoutSettlementJob is idempotent: a second run settles nothing new for the same proposal', async () => {
  const ctx = makeCtx(db);
  await insertCompletedRedeemedProposal();

  const first = await runVenuePayoutSettlementJob(ctx);
  assert.ok(first.settled >= 1);
  const second = await runVenuePayoutSettlementJob(ctx);
  assert.equal(second.settled, 0);
});
