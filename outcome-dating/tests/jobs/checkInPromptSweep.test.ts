/**
 * `check_in_prompt_sweep` job, thin wrapper around
 * `postDateFeedback.service#runCheckInPromptSweep`. Full timing-matrix
 * coverage lives in `tests/unit/postDateFeedback.test.ts` (owned
 * elsewhere); this file proves the job is reachable, runs, and is
 * idempotent (a participant already prompted is not prompted again on a
 * second run inside the same tick).
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestDb, teardownTestDb, makeCtx, createUser, createConversation, createVenue } from './testHarness.js';
import type { TestDb } from './testHarness.js';
import { KNOWN_FLAGS } from '../../src/config/flags.service.js';
import { runCheckInPromptSweepJob } from '../../src/jobs/checkInPromptSweep.job.js';

let db: TestDb;

before(async () => {
  db = await setupTestDb('check_in_prompt_sweep');
  await db.flags.setFlag(KNOWN_FLAGS.POST_DATE_FEEDBACK, { enabled: true, rolloutPercent: 100 });
});

after(async () => {
  await teardownTestDb(db);
});

async function insertTicketedProposal(): Promise<string> {
  const a = await createUser(db);
  const b = await createUser(db);
  const conversationId = await createConversation(db, a, b);
  const venueId = await createVenue(db);
  const now = db.clock.now();
  // scheduled_end 4 hours ago, past the 3h initial-prompt delay, well
  // inside the 14-day prompt window.
  const scheduledStart = new Date(now.getTime() - 5 * 60 * 60 * 1000);
  const scheduledEnd = new Date(now.getTime() - 4 * 60 * 60 * 1000);

  const { rows } = await db.pool.query<{ id: string }>(
    `INSERT INTO date_proposals (conversation_id, proposer_id, recipient_id, venue_id, scheduled_start, scheduled_end, status, policy_snapshot, escrow_amount_cents)
     VALUES ($1, $2, $3, $4, $5, $6, 'ticketed', '{}'::jsonb, 2000)
     RETURNING id`,
    [conversationId, a, b, venueId, scheduledStart, scheduledEnd],
  );
  return rows[0]!.id;
}

test('runCheckInPromptSweepJob sends an initial prompt to both participants of a past date', async () => {
  const ctx = makeCtx(db);
  const dateProposalId = await insertTicketedProposal();

  const result = await runCheckInPromptSweepJob(ctx);
  assert.equal(result.promptsSent, 2);
  assert.equal(result.remindersSent, 0);

  const { rows } = await db.pool.query<{ count: string }>(
    `SELECT count(*)::text AS count FROM post_date_feedback_prompts WHERE date_proposal_id = $1`,
    [dateProposalId],
  );
  assert.equal(Number(rows[0]!.count), 2);
});

test('runCheckInPromptSweepJob is idempotent: a second run in the same tick prompts nobody again', async () => {
  const ctx = makeCtx(db);
  await insertTicketedProposal();

  const first = await runCheckInPromptSweepJob(ctx);
  assert.equal(first.promptsSent, 2);
  const second = await runCheckInPromptSweepJob(ctx);
  assert.equal(second.promptsSent, 0);
  assert.equal(second.remindersSent, 0);
});
