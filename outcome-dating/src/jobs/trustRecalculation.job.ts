/**
 * §25.6 Trust Score Recalculation job. "Recalculate trust scores when
 * major events occur: report, date completed, payment failure, profile
 * change, verification change."
 *
 * The synchronous paths already exist for SOME of these five triggers —
 * `moderation.service#applyThresholds` and `appeal.service#resolveAppeal`
 * call `trust.recalculateTrustScore` immediately after writing their
 * `trust_events` row. But `dateProposal.service.ts` (date-completed,
 * no-show, payment-failure-adjacent trust signals) and
 * `redemption.service.ts` (date-completed) only call
 * `trust.service#recordTrustEvent` — appending the event — and never
 * `recalculateTrustScore` (see those two files' own trust-event call
 * sites), so a user's `users.trust_score`/`trust_level` can silently drift
 * behind their actual `trust_events` history between an admin-facing
 * moderation action and this job's next run. This job is that catch-up
 * pass: every user with at least one `trust_events` row gets a fresh,
 * idempotent `trust.recalculateTrustScore` — safe to re-run constantly
 * since that function is a pure "recompute from history and persist"
 * operation, not an incremental delta.
 *
 * This file selects WHO needs recalculating (a plain read, not scoring
 * logic); the actual recalculation formula lives entirely in
 * `trust.service.ts`, never reimplemented here.
 */
import type { Ctx } from '../lib/ctx.js';
import { recalculateTrustScore } from '../services/trust.service.js';
import type { JobDefinition } from './types.js';

export async function runTrustRecalculationJob(ctx: Ctx): Promise<{ usersRecalculated: number }> {
  const { rows } = await ctx.db.query<{ user_id: string }>(`SELECT DISTINCT user_id FROM trust_events`);

  for (const { user_id: userId } of rows) {
    await recalculateTrustScore(ctx, userId);
  }
  return { usersRecalculated: rows.length };
}

export const trustRecalculationJob: JobDefinition = {
  name: 'trust_score_recalculation',
  description: 'Recompute trust_score/trust_level for every user with recorded trust_events, catching up on non-synchronous triggers (§25.6).',
  intervalMs: 15 * 60 * 1000,
  run: runTrustRecalculationJob,
};
