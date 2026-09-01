/**
 * §25.5 Photo A/B Stats job. "Aggregate impressions and accepted interests.
 * Update photo ranking." — exactly
 * `photoExperiment.service#refreshAllRecommendations`: for every user with
 * >=3 approved photos and the `photo_ab_testing` flag on, recomputes the
 * significance-guarded recommendation (ranked by accepted-interest rate,
 * never raw impressions — see that module's `computeRecommendation` doc)
 * and upserts a `pending` `photo_recommendations` row.
 */
import type { Ctx } from '../lib/ctx.js';
import { refreshAllRecommendations } from '../services/photoExperiment.service.js';
import type { JobDefinition } from './types.js';

export async function runPhotoAbStatsJob(ctx: Ctx): Promise<{ usersUpdated: number }> {
  return refreshAllRecommendations(ctx);
}

export const photoAbStatsJob: JobDefinition = {
  name: 'photo_ab_stats',
  description: 'Aggregate photo impressions/accepted-interests and refresh per-user photo recommendations (§25.5).',
  intervalMs: 60 * 60 * 1000, // hourly
  run: runPhotoAbStatsJob,
};
