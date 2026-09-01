/**
 * Post-date check-in prompt sweep. Thin wrapper around
 * `postDateFeedback.service#runCheckInPromptSweep`, prompts both
 * participants of a date whose `scheduled_end` has passed to submit their
 * check-in, and sends a reminder if they haven't responded (see that
 * function's own doc). No domain logic here.
 */
import type { Ctx } from '../lib/ctx.js';
import { runCheckInPromptSweep } from '../services/postDateFeedback.service.js';
import type { CheckInPromptSweepResult } from '../services/postDateFeedback.service.js';
import type { JobDefinition } from './types.js';

export async function runCheckInPromptSweepJob(ctx: Ctx): Promise<CheckInPromptSweepResult> {
  return runCheckInPromptSweep(ctx);
}

export const checkInPromptSweepJob: JobDefinition = {
  name: 'check_in_prompt_sweep',
  description: 'Prompt and remind both participants of a past date to submit their post-date check-in.',
  intervalMs: 30 * 60 * 1000,
  run: runCheckInPromptSweepJob,
};
