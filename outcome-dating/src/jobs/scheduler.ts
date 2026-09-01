/**
 * src/jobs/scheduler.ts — a small in-process scheduler (no Redis/queue,
 * per INTERFACES.md's "no Redis" simplification), with a clean seam for a
 * real queue later: every job is already a plain `(ctx: Ctx) => Promise<T>`
 * (see `src/jobs/types.ts`), so swapping this class for e.g. a BullMQ
 * worker is a matter of re-wiring `JobScheduler#start`'s `setInterval` to
 * a queue consumer — no job body changes.
 *
 * CONCURRENCY SAFETY: each job run is wrapped in a Postgres advisory lock
 * (`pg_try_advisory_lock`), keyed by a hash of the job name. This makes a
 * run safe against BOTH (a) this process's own interval firing again
 * before the previous run finished, and (b) a second process (e.g. a
 * `jobs:start` daemon plus a one-off `jobs:run` CLI invocation, or two
 * horizontally-scaled instances) racing the same job — a run that can't
 * acquire the lock is skipped, not queued or retried, since every job body
 * is itself idempotent (status-guarded UPDATEs — see each `src/jobs/*.job.ts`
 * file's doc) and will simply pick up whatever's still due on its next
 * scheduled tick.
 */
import { createHash } from 'node:crypto';
import type { AppDeps } from '../http/deps.js';
import { systemCtx } from '../http/deps.js';
import type { JobDefinition } from './types.js';
import { ALL_JOBS, findJob } from './registry.js';

export interface JobRunResult {
  name: string;
  startedAt: Date;
  finishedAt: Date;
  durationMs: number;
  skipped: boolean;
  ok: boolean;
  result?: unknown;
  error?: string;
}

/** Deterministic two-int32 advisory-lock key for `pg_try_advisory_lock(int, int)`, derived from the job name. */
function lockKeyFor(name: string): [number, number] {
  const digest = createHash('sha256').update(`odate_job:${name}`).digest();
  return [digest.readInt32BE(0), digest.readInt32BE(4)];
}

export class JobScheduler {
  private timers = new Map<string, NodeJS.Timeout>();

  constructor(
    private readonly deps: AppDeps,
    private readonly jobs: JobDefinition[] = ALL_JOBS,
  ) {}

  /** Runs one job by name, immediately, guarded by its advisory lock. Used by both `jobs:run <name>` and each scheduled tick. */
  async runJob(name: string): Promise<JobRunResult> {
    const job = findJob(name) ?? this.jobs.find((j) => j.name === name);
    if (!job) throw new Error(`Unknown job "${name}". Known jobs: ${this.jobs.map((j) => j.name).join(', ')}`);

    const startedAt = this.deps.clock.now();
    const [k1, k2] = lockKeyFor(job.name);
    const client = await this.deps.pool.connect();
    try {
      const { rows } = await client.query<{ locked: boolean }>('SELECT pg_try_advisory_lock($1, $2) AS locked', [k1, k2]);
      if (!rows[0]?.locked) {
        const finishedAt = this.deps.clock.now();
        return { name: job.name, startedAt, finishedAt, durationMs: finishedAt.getTime() - startedAt.getTime(), skipped: true, ok: true };
      }

      try {
        const ctx = systemCtx(this.deps, `job:${job.name}`);
        const result = await job.run(ctx);
        const finishedAt = this.deps.clock.now();
        return { name: job.name, startedAt, finishedAt, durationMs: finishedAt.getTime() - startedAt.getTime(), skipped: false, ok: true, result };
      } catch (err) {
        const finishedAt = this.deps.clock.now();
        this.deps.logger.error('job.failed', { job: job.name, err: err instanceof Error ? err.message : String(err) });
        return {
          name: job.name,
          startedAt,
          finishedAt,
          durationMs: finishedAt.getTime() - startedAt.getTime(),
          skipped: false,
          ok: false,
          error: err instanceof Error ? err.message : String(err),
        };
      } finally {
        await client.query('SELECT pg_advisory_unlock($1, $2)', [k1, k2]);
      }
    } finally {
      client.release();
    }
  }

  /** Starts every registered job on its own `setInterval`. Returns a stop function. `unref()`s each timer so a bare `jobs:start` process can still be killed cleanly. */
  start(): () => void {
    for (const job of this.jobs) {
      const timer = setInterval(() => {
        void this.runJob(job.name).catch((err) => {
          this.deps.logger.error('job.scheduler_tick_failed', { job: job.name, err: err instanceof Error ? err.message : String(err) });
        });
      }, job.intervalMs);
      timer.unref?.();
      this.timers.set(job.name, timer);
    }
    return () => this.stop();
  }

  stop(): void {
    for (const timer of this.timers.values()) clearInterval(timer);
    this.timers.clear();
  }
}
