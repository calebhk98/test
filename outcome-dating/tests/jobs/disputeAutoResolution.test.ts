/**
 * `dispute_auto_resolution` job, thin wrapper around
 * `disputeResolution.service#resolveDueDisputes` (§15.4). Full behavior
 * (implicit report filing, trust event recording) is covered by
 * `tests/unit/dateOutcomeSweep.test.ts` (owned elsewhere); this file
 * proves the job is reachable, runs, and is idempotent.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestDb, teardownTestDb, makeCtx, createUser, createConversation, createVenue } from './testHarness.js';
import type { TestDb } from './testHarness.js';
import { runDisputeAutoResolutionJob } from '../../src/jobs/disputeAutoResolution.job.js';

let db: TestDb;

before(async () => {
  db = await setupTestDb('dispute_auto_resolution');
});

after(async () => {
  await teardownTestDb(db);
});

// Deadline = scheduled_end + no_scan_confirmation_hours + dispute_auto_resolve_hours.
// scheduled_end is 30h in the past, so a 2h + 4h window is well past due.
const POLICY = JSON.stringify({ 'date.no_scan_confirmation_hours': 2, 'date.dispute_auto_resolve_hours': 4 });

async function insertDisputedProposal(): Promise<{ id: string; confirming: string; nonConfirming: string }> {
  const a = await createUser(db);
  const b = await createUser(db);
  const conversationId = await createConversation(db, a, b);
  const venueId = await createVenue(db);
  const now = db.clock.now();
  const scheduledStart = new Date(now.getTime() - 31 * 60 * 60 * 1000);
  const scheduledEnd = new Date(now.getTime() - 30 * 60 * 60 * 1000);

  const { rows } = await db.pool.query<{ id: string }>(
    `INSERT INTO date_proposals (conversation_id, proposer_id, recipient_id, venue_id, scheduled_start, scheduled_end, status, policy_snapshot, escrow_amount_cents)
     VALUES ($1, $2, $3, $4, $5, $6, 'disputed', $7::jsonb, 2000)
     RETURNING id`,
    [conversationId, a, b, venueId, scheduledStart, scheduledEnd, POLICY],
  );
  const id = rows[0]!.id;
  // `a` confirmed attendance, `b` did not, the report targets `b`.
  await db.pool.query(`INSERT INTO date_attendance_confirmations (date_proposal_id, user_id) VALUES ($1, $2)`, [id, a]);
  return { id, confirming: a, nonConfirming: b };
}

test('runDisputeAutoResolutionJob resolves a due dispute exactly once, filing a report against the non-confirming party', async () => {
  const ctx = makeCtx(db);
  const { id, nonConfirming } = await insertDisputedProposal();

  const result = await runDisputeAutoResolutionJob(ctx);
  assert.equal(result.resolved, 1);

  const { rows } = await db.pool.query<{ dispute_resolved_at: Date | null }>(
    'SELECT dispute_resolved_at FROM date_proposals WHERE id = $1',
    [id],
  );
  assert.ok(rows[0]!.dispute_resolved_at !== null);

  const { rows: reportRows } = await db.pool.query<{ count: string }>(
    `SELECT count(*)::text AS count FROM reports WHERE reported_id = $1 AND category = 'no_show'`,
    [nonConfirming],
  );
  assert.equal(Number(reportRows[0]!.count), 1);
});

test('runDisputeAutoResolutionJob is idempotent: a second run resolves nothing new for the same dispute', async () => {
  const ctx = makeCtx(db);
  await insertDisputedProposal();

  const first = await runDisputeAutoResolutionJob(ctx);
  assert.equal(first.resolved, 1);
  const second = await runDisputeAutoResolutionJob(ctx);
  assert.equal(second.resolved, 0);
});
