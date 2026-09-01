/**
 * §25.7 Moderation Score Recalculation job — aggregates automated flags
 * and applies restrictions/shadowbans/suspensions fully automatically
 * (mirrors C-25.7.1 / C-18.5.W1), with an idempotent re-run that does not
 * re-apply an already-applied action.
 */
import { test, before, after, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestDb, teardownTestDb, makeCtx, createUser } from './testHarness.js';
import type { TestDb } from './testHarness.js';
import { runModerationRecalculationJob } from '../../src/jobs/moderationRecalculation.job.js';

let db: TestDb;

before(async () => {
  db = await setupTestDb('moderation_recalculation');
});

after(async () => {
  await teardownTestDb(db);
});

// The job scans every user with any recorded flag/report — reset between
// tests so an earlier test's fixture user doesn't inflate a later test's
// `usersEvaluated`/`actionsApplied` aggregate counts. Per-row assertions
// (a specific user's own `moderation_actions`) are unaffected either way.
afterEach(async () => {
  await db.pool.query('DELETE FROM moderation_actions');
  await db.pool.query('DELETE FROM automated_moderation_flags');
  await db.pool.query('DELETE FROM reports');
});

test('a user whose flagged weight crosses the restriction threshold gets an automated restriction, with zero admin involvement', async () => {
  const ctx = makeCtx(db);
  const userId = await createUser(db);

  // Default moderation.auto_restriction_score = 50.
  await db.pool.query(
    `INSERT INTO automated_moderation_flags (user_id, signal_type, weight) VALUES ($1, 'message_velocity', 60)`,
    [userId],
  );

  const result = await runModerationRecalculationJob(ctx);
  assert.equal(result.usersEvaluated, 1);
  assert.equal(result.actionsApplied, 1);

  const { rows } = await db.pool.query<{ action: string }>(
    `SELECT action FROM moderation_actions WHERE user_id = $1 ORDER BY created_at DESC LIMIT 1`,
    [userId],
  );
  assert.equal(rows[0]!.action, 'restriction');
});

test('idempotent re-run: a user already at the action level their score warrants is not re-actioned', async () => {
  const ctx = makeCtx(db);
  const userId = await createUser(db);
  await db.pool.query(`INSERT INTO automated_moderation_flags (user_id, signal_type, weight) VALUES ($1, 'device_reputation', 55)`, [userId]);

  const first = await runModerationRecalculationJob(ctx);
  assert.equal(first.actionsApplied, 1);
  const second = await runModerationRecalculationJob(ctx);
  assert.equal(second.actionsApplied, 0, 'a second run at the same score must not duplicate the action');

  const { rows } = await db.pool.query<{ count: string }>(`SELECT count(*)::text AS count FROM moderation_actions WHERE user_id = $1`, [userId]);
  assert.equal(rows[0]!.count, '1');
});

test('a user below every threshold is evaluated but receives no action', async () => {
  const ctx = makeCtx(db);
  const userId = await createUser(db);
  await db.pool.query(`INSERT INTO automated_moderation_flags (user_id, signal_type, weight) VALUES ($1, 'no_show', 2)`, [userId]);

  const result = await runModerationRecalculationJob(ctx);
  assert.equal(result.usersEvaluated, 1);
  assert.equal(result.actionsApplied, 0);
});
