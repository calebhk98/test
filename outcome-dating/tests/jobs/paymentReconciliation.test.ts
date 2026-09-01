/**
 * §25.9 Payment Reconciliation job, flags (never auto-corrects) mismatches
 * between local `payment_holds`/`payment_ledger` state, mirroring
 * C-25.9.1.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestDb, teardownTestDb, makeCtx, createUser, createConversation, createVenue } from './testHarness.js';
import type { TestDb } from './testHarness.js';
import { runPaymentReconciliationJob } from '../../src/jobs/paymentReconciliation.job.js';

let db: TestDb;

before(async () => {
  db = await setupTestDb('payment_reconciliation');
});

after(async () => {
  await teardownTestDb(db);
});

async function insertDateProposalAndHold(status: 'captured' | 'authorized'): Promise<{ dateProposalId: string; holdId: string; userId: string }> {
  const a = await createUser(db);
  const b = await createUser(db);
  const conversationId = await createConversation(db, a, b);
  const venueId = await createVenue(db);
  const { rows: dpRows } = await db.pool.query<{ id: string }>(
    `INSERT INTO date_proposals (conversation_id, proposer_id, recipient_id, venue_id, scheduled_start, scheduled_end, status, policy_snapshot, escrow_amount_cents)
     VALUES ($1, $2, $3, $4, now() + interval '1 day', now() + interval '1 day 1 hour', 'accepted', '{}'::jsonb, 2000)
     RETURNING id`,
    [conversationId, a, b, venueId],
  );
  const dateProposalId = dpRows[0]!.id;
  const { rows: holdRows } = await db.pool.query<{ id: string }>(
    `INSERT INTO payment_holds (date_proposal_id, user_id, processor, processor_intent_id, amount_cents, currency, status, authorized_at, captured_at)
     VALUES ($1, $2, 'fake', $3, 2000, 'usd', $4, now(), $5)
     RETURNING id`,
    [dateProposalId, a, `pi_recon_${dateProposalId}`, status, status === 'captured' ? new Date() : null],
  );
  return { dateProposalId, holdId: holdRows[0]!.id, userId: a };
}

test('a hold marked captured with no matching capture ledger entry is flagged as a mismatch, never auto-corrected', async () => {
  const ctx = makeCtx(db);
  const { holdId } = await insertDateProposalAndHold('captured');
  // Deliberately no payment_ledger row inserted for this hold.

  const result = await runPaymentReconciliationJob(ctx);
  const mismatch = result.mismatches.find((m) => m.paymentHoldId === holdId);
  assert.ok(mismatch, 'the mismatch must be flagged');
  assert.match(mismatch!.reason, /no capture ledger entry/);

  // Never auto-corrected -- hold status is untouched by the job.
  const { rows } = await db.pool.query<{ status: string }>(`SELECT status FROM payment_holds WHERE id = $1`, [holdId]);
  assert.equal(rows[0]!.status, 'captured');
});

test('a hold with a matching capture ledger entry is NOT flagged', async () => {
  const ctx = makeCtx(db);
  const { dateProposalId, holdId, userId } = await insertDateProposalAndHold('captured');
  await db.pool.query(
    `INSERT INTO payment_ledger (user_id, date_proposal_id, payment_hold_id, type, amount_cents, currency, processor_reference)
     VALUES ($1, $2, $3, 'capture', 2000, 'usd', 'pi_ok')`,
    [userId, dateProposalId, holdId],
  );

  const result = await runPaymentReconciliationJob(ctx);
  assert.equal(result.mismatches.some((m) => m.paymentHoldId === holdId), false);
});

test('idempotent re-run: the same mismatch is reported consistently, not duplicated or escalated', async () => {
  const ctx = makeCtx(db);
  const { holdId } = await insertDateProposalAndHold('captured');

  const first = await runPaymentReconciliationJob(ctx);
  const second = await runPaymentReconciliationJob(ctx);

  const firstCount = first.mismatches.filter((m) => m.paymentHoldId === holdId).length;
  const secondCount = second.mismatches.filter((m) => m.paymentHoldId === holdId).length;
  assert.equal(firstCount, 1);
  assert.equal(secondCount, 1);
});
