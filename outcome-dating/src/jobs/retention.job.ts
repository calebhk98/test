/**
 * Data-retention sweep job, runs every registered `RetentionPolicy`
 * (src/services/retention.service.ts) once, each internally bounded and
 * batched. See that file's module doc for the full design; see
 * docs/retention.md for the per-class window/reasoning table this job
 * enforces.
 *
 * Same `(ctx: Ctx) => Promise<T>` shape as every other §25-style job in
 * this codebase (src/jobs/types.ts), a test calls
 * `runRetentionSweepJob(ctx)` directly against a `Ctx` built on a
 * `ManualClock`, no scheduler involved, per this repo's established job-
 * testing convention (tests/jobs/testHarness.ts's own doc).
 */
import type { Ctx } from '../lib/ctx.js';
import { runRetentionSweep } from '../services/retention.service.js';
import type { RetentionSweepResult } from '../services/retention.service.js';
import type { JobDefinition } from './types.js';

export async function runRetentionSweepJob(ctx: Ctx): Promise<RetentionSweepResult> {
  return runRetentionSweep(ctx);
}

/**
 * Hourly, retention windows are measured in days at the shortest (verification
 * codes, 7 days), so there is no correctness reason to run more often;
 * hourly just keeps any one run's backlog (bounded by `maxBatchesPerRun`
 * per policy, see retention.service.ts) small in practice.
 */
export const retentionSweepJob: JobDefinition = {
  name: 'retention_sweep',
  description: 'Enforces every data-retention policy (delete or anonymize past its window), batched and capped per run, see docs/retention.md.',
  intervalMs: 60 * 60 * 1000,
  run: runRetentionSweepJob,
};
