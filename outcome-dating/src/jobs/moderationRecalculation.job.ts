/**
 * §25.7 Moderation Score Recalculation job. "Aggregate reports and
 * automated flags. Apply restrictions/shadowbans when thresholds crossed."
 * exactly `moderation.service#runModerationRecalculation`, which already
 * does the full select-every-flagged-user + `applyThresholds` loop
 * (idempotent: `applyThresholds` only writes a new `moderation_actions` row
 * when the target severity is strictly higher than the user's current
 * level, see that function's doc).
 */
import type { Ctx } from '../lib/ctx.js';
import { runModerationRecalculation } from '../services/moderation.service.js';
import type { JobDefinition } from './types.js';

export async function runModerationRecalculationJob(ctx: Ctx): Promise<{ usersEvaluated: number; actionsApplied: number }> {
  return runModerationRecalculation(ctx);
}

export const moderationRecalculationJob: JobDefinition = {
  name: 'moderation_score_recalculation',
  description: 'Aggregate reports/automated flags and apply restrictions/shadowbans/suspensions when thresholds are crossed, fully automated (§25.7, §18.1).',
  intervalMs: 15 * 60 * 1000,
  run: runModerationRecalculationJob,
};
