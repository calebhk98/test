/**
 * §25.6 Trust Score Recalculation job, catches up `users.trust_score`/
 * `trust_level` from `trust_events` history for users whose triggering
 * service call only appended an event without recalculating synchronously
 * (see the job file's own doc for which paths those are). Idempotent
 * re-run producing no further drift once caught up.
 */
import { test, before, after, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestDb, teardownTestDb, makeCtx, createUser } from './testHarness.js';
import type { TestDb } from './testHarness.js';
import { runTrustRecalculationJob } from '../../src/jobs/trustRecalculation.job.js';

let db: TestDb;

before(async () => {
  db = await setupTestDb('trust_recalculation');
});

after(async () => {
  await teardownTestDb(db);
});

// The job scans every user with any recorded trust_events row, reset
// between tests so an earlier test's fixture user doesn't inflate a later
// test's `usersRecalculated` aggregate count.
afterEach(async () => {
  await db.pool.query('DELETE FROM trust_events');
});

test('a user with a recorded negative trust_event but a stale users.trust_score is caught up by the job', async () => {
  const ctx = makeCtx(db);
  const userId = await createUser(db); // starts at trust_score 50 (default)

  await db.pool.query(
    `INSERT INTO trust_events (user_id, event_type, delta, metadata) VALUES ($1, 'no_show', -8, '{}'::jsonb)`,
    [userId],
  );

  const beforeRow = await db.pool.query<{ trust_score: number }>('SELECT trust_score FROM users WHERE id = $1', [userId]);
  assert.equal(beforeRow.rows[0]!.trust_score, 50, 'fixture: no synchronous recalculation happened yet');

  const result = await runTrustRecalculationJob(ctx);
  assert.equal(result.usersRecalculated, 1);

  const afterRow = await db.pool.query<{ trust_score: number }>('SELECT trust_score FROM users WHERE id = $1', [userId]);
  assert.notEqual(afterRow.rows[0]!.trust_score, 50, 'trust_score must reflect the recorded event after the job runs');
});

test('idempotent re-run: a second run with no new events produces the same score, not further drift', async () => {
  const ctx = makeCtx(db);
  const userId = await createUser(db);
  await db.pool.query(
    `INSERT INTO trust_events (user_id, event_type, delta, metadata) VALUES ($1, 'payment_failed', -5, '{}'::jsonb)`,
    [userId],
  );

  await runTrustRecalculationJob(ctx);
  const first = await db.pool.query<{ trust_score: number }>('SELECT trust_score FROM users WHERE id = $1', [userId]);

  await runTrustRecalculationJob(ctx);
  const second = await db.pool.query<{ trust_score: number }>('SELECT trust_score FROM users WHERE id = $1', [userId]);

  assert.equal(second.rows[0]!.trust_score, first.rows[0]!.trust_score);
});

test('a user with no trust_events at all is not touched (only users with recorded events are recalculated)', async () => {
  const ctx = makeCtx(db);
  const untouchedUser = await createUser(db);
  const eventfulUser = await createUser(db);
  await db.pool.query(`INSERT INTO trust_events (user_id, event_type, delta) VALUES ($1, 'date_completed', 5)`, [eventfulUser]);

  const result = await runTrustRecalculationJob(ctx);
  assert.equal(result.usersRecalculated, 1);

  const { rows } = await db.pool.query<{ trust_score: number }>('SELECT trust_score FROM users WHERE id = $1', [untouchedUser]);
  assert.equal(rows[0]!.trust_score, 50, 'default, unrecalculated');
});
