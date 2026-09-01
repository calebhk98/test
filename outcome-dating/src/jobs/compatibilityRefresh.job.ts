/**
 * §25.4 Compatibility Score Refresh job. "Run nightly or on major answer
 * changes. Update materialized compatibility scores." The on-answer-change
 * path already runs synchronously inside
 * `question.service#putMyAnswers` -> `compatibility.refreshScoresForUser`
 * (see that file); this job is the "nightly" half —
 * `compatibility.service#refreshAllScores`, an idempotent full recompute
 * (upserts every unordered active-user pair's `compatibility_scores` row
 * from current `answers`).
 */
import type { Ctx } from '../lib/ctx.js';
import { refreshAllScores } from '../services/compatibility.service.js';
import type { JobDefinition } from './types.js';

export async function runCompatibilityRefreshJob(ctx: Ctx): Promise<{ updated: number }> {
  return refreshAllScores(ctx);
}

export const compatibilityRefreshJob: JobDefinition = {
  name: 'compatibility_score_refresh',
  description: 'Nightly recompute of every active-user-pair compatibility_scores row (§25.4).',
  intervalMs: 24 * 60 * 60 * 1000, // nightly
  run: runCompatibilityRefreshJob,
};
