/**
 * `matching_signal_sweep` job, thin wrapper around
 * `postDateFeedback.service#runMatchingSignalSweep`. Full divergence-math
 * / suggestion-creation coverage lives in
 * `tests/unit/postDateFeedback.test.ts` (owned elsewhere); this file
 * proves the job is reachable, runs, considers an eligible user, and is
 * idempotent (a user's `happened_good` rows are marked processed so a
 * second run does not reconsider them).
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestDb, teardownTestDb, makeCtx, createUser, createConversation, createVenue } from './testHarness.js';
import type { TestDb } from './testHarness.js';
import { KNOWN_FLAGS } from '../../src/config/flags.service.js';
import { runMatchingSignalSweepJob } from '../../src/jobs/matchingSignalSweep.job.js';

let db: TestDb;

before(async () => {
  db = await setupTestDb('matching_signal_sweep');
  await db.flags.setFlag(KNOWN_FLAGS.POST_DATE_FEEDBACK, { enabled: true, rolloutPercent: 100 });
  await db.flags.setFlag(KNOWN_FLAGS.BEHAVIORAL_QUESTION_PROMPTS, { enabled: true, rolloutPercent: 100 });
});

after(async () => {
  await teardownTestDb(db);
});

/** `userId` gets 3 `happened_good` post_date_feedback rows against 3 distinct partners/proposals, enough to clear MIN_GOOD_DATES_FOR_MATCHING_SIGNAL. */
async function insertGoodDateHistory(userId: string, count = 3): Promise<void> {
  const venueId = await createVenue(db);
  const now = db.clock.now();
  for (let i = 0; i < count; i++) {
    const partnerId = await createUser(db);
    const conversationId = await createConversation(db, userId, partnerId);
    const scheduledStart = new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000);
    const scheduledEnd = new Date(scheduledStart.getTime() + 60 * 60 * 1000);
    const { rows } = await db.pool.query<{ id: string }>(
      `INSERT INTO date_proposals (conversation_id, proposer_id, recipient_id, venue_id, scheduled_start, scheduled_end, status, policy_snapshot, escrow_amount_cents)
       VALUES ($1, $2, $3, $4, $5, $6, 'completed', '{}'::jsonb, 2000)
       RETURNING id`,
      [conversationId, userId, partnerId, venueId, scheduledStart, scheduledEnd],
    );
    await db.pool.query(
      `INSERT INTO post_date_feedback (date_proposal_id, user_id, positive, outcome) VALUES ($1, $2, true, 'happened_good')`,
      [rows[0]!.id, userId],
    );
  }
}

test('runMatchingSignalSweepJob considers a user with 3+ happened_good check-ins', async () => {
  const ctx = makeCtx(db);
  const userId = await createUser(db);
  await insertGoodDateHistory(userId);

  const result = await runMatchingSignalSweepJob(ctx);
  assert.equal(result.usersConsidered, 1);
});

test('runMatchingSignalSweepJob is idempotent: a second run does not reconsider already-processed feedback', async () => {
  const ctx = makeCtx(db);
  const userId = await createUser(db);
  await insertGoodDateHistory(userId);

  const first = await runMatchingSignalSweepJob(ctx);
  assert.equal(first.usersConsidered, 1);

  const second = await runMatchingSignalSweepJob(ctx);
  assert.equal(second.usersConsidered, 0);

  const { rows } = await db.pool.query<{ count: string }>(
    `SELECT count(*)::text AS count FROM post_date_feedback WHERE user_id = $1 AND matching_signal_processed_at IS NULL`,
    [userId],
  );
  assert.equal(Number(rows[0]!.count), 0);
});
