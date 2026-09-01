/**
 * `JobScheduler` — the advisory-lock concurrency guard (a job run that
 * can't acquire its lock is skipped, not queued/retried) and the job
 * registry (`jobs:run <name>` lookup surface).
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestDb, teardownTestDb } from './testHarness.js';
import type { TestDb } from './testHarness.js';
import { JobScheduler } from '../../src/jobs/scheduler.js';
import { ALL_JOBS, findJob } from '../../src/jobs/registry.js';
import type { AppDeps } from '../../src/http/deps.js';
import { FakeProcessor } from '../../src/services/payments/fake.processor.js';
import { StubMediaModerationAdapter } from '../../src/services/media/stub.adapter.js';
import { createSilentLogger } from '../../src/lib/logger.js';

let db: TestDb;

before(async () => {
  db = await setupTestDb('scheduler');
});

after(async () => {
  await teardownTestDb(db);
});

function makeDeps(): AppDeps {
  return {
    pool: db.pool,
    clock: db.clock,
    config: db.config,
    flags: db.flags,
    logger: createSilentLogger(),
    payments: new FakeProcessor(),
    media: new StubMediaModerationAdapter(),
  };
}

test('the registry lists all 17 jobs by their spec-stable names', () => {
  const names = ALL_JOBS.map((j) => j.name).sort();
  assert.deepEqual(names, [
    'chat_decay',
    'check_in_prompt_sweep',
    'compatibility_score_refresh',
    'date_proposal_expiry',
    'dispute_auto_resolution',
    'interest_expiry',
    'matching_signal_sweep',
    'moderation_score_recalculation',
    'notification_delivery',
    'payment_reconciliation',
    'photo_ab_stats',
    'retention_sweep',
    'stats_aggregation',
    'ticketed_completion_sweep',
    'trust_score_recalculation',
    'venue_payout_settlement',
    'voucher_expiry',
  ]);
});

test('runJob runs a known job to completion and reports ok:true, not skipped', async () => {
  const scheduler = new JobScheduler(makeDeps());
  const result = await scheduler.runJob('interest_expiry');
  assert.equal(result.ok, true);
  assert.equal(result.skipped, false);
  assert.equal(result.name, 'interest_expiry');
});

test('runJob on an unknown name throws, listing the known jobs', async () => {
  const scheduler = new JobScheduler(makeDeps());
  await assert.rejects(() => scheduler.runJob('not_a_real_job'), /Unknown job/);
});

test('advisory lock: a job run already holding the lock causes a concurrent run to be skipped, not to duplicate work', async () => {
  // Simulate "another process/run already has the lock" by acquiring the
  // same two-int32 advisory-lock key this scheduler will compute for
  // 'voucher_expiry', on a separate connection held open for the duration
  // of the test.
  const holderClient = await db.pool.connect();
  try {
    const { createHash } = await import('node:crypto');
    const digest = createHash('sha256').update('odate_job:voucher_expiry').digest();
    const k1 = digest.readInt32BE(0);
    const k2 = digest.readInt32BE(4);
    const { rows } = await holderClient.query<{ locked: boolean }>('SELECT pg_try_advisory_lock($1, $2) AS locked', [k1, k2]);
    assert.equal(rows[0]!.locked, true, 'fixture: the test harness itself must acquire the lock first');

    const scheduler = new JobScheduler(makeDeps());
    const result = await scheduler.runJob('voucher_expiry');
    assert.equal(result.skipped, true, 'a run that cannot acquire the advisory lock must be skipped');
    assert.equal(result.ok, true, 'skipping is not itself an error');
  } finally {
    await holderClient.query('SELECT pg_advisory_unlock_all()');
    holderClient.release();
  }
});

test('two concurrent runJob calls for the SAME job never both execute the body at once (one runs, one is skipped)', async () => {
  const scheduler = new JobScheduler(makeDeps());
  const [a, b] = await Promise.all([scheduler.runJob('chat_decay'), scheduler.runJob('chat_decay')]);
  const skippedCount = [a, b].filter((r) => r.skipped).length;
  const ranCount = [a, b].filter((r) => !r.skipped).length;
  assert.equal(ranCount, 1, 'exactly one of the two concurrent runs should actually execute');
  assert.equal(skippedCount, 1, 'the other must be skipped, never double-run');
});

test('findJob resolves every registered job by name', () => {
  for (const job of ALL_JOBS) {
    assert.equal(findJob(job.name), job);
  }
  assert.equal(findJob('nope'), undefined);
});
