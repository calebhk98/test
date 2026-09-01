/**
 * Future-matching-signal sweep. Thin wrapper around
 * `postDateFeedback.service#runMatchingSignalSweep` — for a user with
 * enough `happened_good` post-date check-ins, generates a behavioral
 * question-answer suggestion (see that function's own doc). No domain
 * logic here.
 */
import type { Ctx } from '../lib/ctx.js';
import { runMatchingSignalSweep } from '../services/postDateFeedback.service.js';
import type { MatchingSignalSweepResult } from '../services/postDateFeedback.service.js';
import type { JobDefinition } from './types.js';

export async function runMatchingSignalSweepJob(ctx: Ctx): Promise<MatchingSignalSweepResult> {
  return runMatchingSignalSweep(ctx);
}

export const matchingSignalSweepJob: JobDefinition = {
  name: 'matching_signal_sweep',
  description: 'Generate behavioral question-answer suggestions from a run of happened_good post-date check-ins.',
  intervalMs: 60 * 60 * 1000,
  run: runMatchingSignalSweepJob,
};
