/**
 * src/jobs/types.ts, the shape every §25 background job conforms to.
 *
 * Each job is a PLAIN exported async function `(ctx: Ctx) => Promise<T>`,
 * no class, no hidden state, so a test can call it directly with a
 * `ManualClock`-driven `Ctx` and assert on its return value, with zero
 * dependency on the scheduler (task brief: "tests invoke it directly with
 * a controlled clock rather than waiting"). `JobDefinition` is only the
 * scheduler's own registration wrapper around that function.
 */
import type { Ctx } from '../lib/ctx.js';

export type JobFn<T = unknown> = (ctx: Ctx) => Promise<T>;

export interface JobDefinition {
  /** Stable name, used by `jobs:run <name>` (CLI) and the advisory-lock key. */
  name: string;
  description: string;
  /** How often the scheduler re-runs this job while `jobs:start` is active. */
  intervalMs: number;
  run: JobFn;
}
