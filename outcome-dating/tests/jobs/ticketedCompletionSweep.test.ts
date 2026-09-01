/**
 * `ticketed_completion_sweep` job, thin wrapper around
 * `dateProposal.service#sweepTicketedCompletionWindows` (§15.4). Full
 * outcome-math coverage lives in `tests/unit/dateOutcomeSweep.test.ts`
 * (owned elsewhere); this file proves the job is reachable, runs, and is
 * idempotent.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestDb, teardownTestDb, makeCtx, createUser, createConversation, createVenue } from './testHarness.js';
import type { TestDb } from './testHarness.js';
import { runTicketedCompletionSweepJob } from '../../src/jobs/ticketedCompletionSweep.job.js';

let db: TestDb;

before(async () => {
  db = await setupTestDb('ticketed_completion_sweep');
});

after(async () => {
  await teardownTestDb(db);
});

const POLICY = JSON.stringify({ 'date.no_scan_confirmation_hours': 2, 'date.no_show_refund_percent': 0 });

async function insertTicketedProposal(): Promise<{ id: string; a: string; b: string }> {
  const a = await createUser(db);
  const b = await createUser(db);
  const conversationId = await createConversation(db, a, b);
  const venueId = await createVenue(db);
  const now = db.clock.now();
  const scheduledStart = new Date(now.getTime() - 10 * 60 * 60 * 1000);
  const scheduledEnd = new Date(now.getTime() - 9 * 60 * 60 * 1000);

  const { rows } = await db.pool.query<{ id: string }>(
    `INSERT INTO date_proposals (conversation_id, proposer_id, recipient_id, venue_id, scheduled_start, scheduled_end, status, policy_snapshot, escrow_amount_cents)
     VALUES ($1, $2, $3, $4, $5, $6, 'ticketed', $7::jsonb, 2000)
     RETURNING id`,
    [conversationId, a, b, venueId, scheduledStart, scheduledEnd, POLICY],
  );
  return { id: rows[0]!.id, a, b };
}

test('runTicketedCompletionSweepJob: a ticketed proposal past its window with zero confirmations becomes no_show', async () => {
  const ctx = makeCtx(db);
  const { id } = await insertTicketedProposal();

  const result = await runTicketedCompletionSweepJob(ctx);
  assert.equal(result.autoNoShow, 1);
  assert.equal(result.autoDisputed, 0);

  const { rows } = await db.pool.query<{ status: string }>('SELECT status FROM date_proposals WHERE id = $1', [id]);
  assert.equal(rows[0]!.status, 'no_show');
});

test('runTicketedCompletionSweepJob: exactly one confirmation past the window becomes disputed', async () => {
  const ctx = makeCtx(db);
  const { id, a } = await insertTicketedProposal();
  await db.pool.query(`INSERT INTO date_attendance_confirmations (date_proposal_id, user_id) VALUES ($1, $2)`, [id, a]);

  const result = await runTicketedCompletionSweepJob(ctx);
  assert.equal(result.autoDisputed, 1);

  const { rows } = await db.pool.query<{ status: string }>('SELECT status FROM date_proposals WHERE id = $1', [id]);
  assert.equal(rows[0]!.status, 'disputed');
});

test('runTicketedCompletionSweepJob is idempotent: a proposal already resolved out of ticketed is never touched again', async () => {
  const ctx = makeCtx(db);
  const { id } = await insertTicketedProposal();

  const first = await runTicketedCompletionSweepJob(ctx);
  assert.equal(first.autoNoShow, 1);
  const second = await runTicketedCompletionSweepJob(ctx);
  assert.equal(second.autoNoShow, 0);
  assert.equal(second.autoDisputed, 0);

  const { rows } = await db.pool.query<{ status: string }>('SELECT status FROM date_proposals WHERE id = $1', [id]);
  assert.equal(rows[0]!.status, 'no_show');
});
