/**
 * src/http/serializers/trust.ts — `GET /me/trust`.
 *
 * Spec §6.3: "The exact numeric trustScore is NOT shown to the user unless
 * product explicitly decides otherwise (default: level only)." `trustLevel`
 * is always the primary field; `trustScore` is gated behind an ad-hoc
 * feature flag (same pattern as `photoExperiment.service.ts`'s
 * `photo_ab_auto_reorder` — an unseeded flag key defaults to disabled, see
 * `flags.service.ts#isEnabled`), so it is withheld by default and an
 * operator can opt a rollout in without a deploy.
 *
 * `TrustSummary.actionableImprovements`/`recentNegativeEvents` are already
 * static template strings with no raw weights (trust.service.ts's own
 * invariant) — this serializer passes them through by explicit field name,
 * never a spread, so a future field added to `TrustSummary` cannot leak
 * through unreviewed.
 */
import type { TrustSummary } from '../../domain/types.js';
import type { FlagsService } from '../../config/flags.service.js';

/** Ad-hoc flag key (unseeded => defaults off) gating exposure of the raw numeric trustScore, per spec §6.3's "unless product explicitly decides otherwise". */
export const EXPOSE_TRUST_SCORE_FLAG = 'expose_trust_score_to_user';

export interface TrustSummaryView {
  trustLevel: TrustSummary['trustLevel'];
  trustScore?: number;
  actionableImprovements: string[];
  recentNegativeEvents: string[];
}

export async function serializeTrustSummary(
  flags: FlagsService,
  userId: string,
  summary: TrustSummary,
): Promise<TrustSummaryView> {
  const exposeScore = await flags.isEnabled(EXPOSE_TRUST_SCORE_FLAG, { userId });
  const view: TrustSummaryView = {
    trustLevel: summary.trustLevel,
    actionableImprovements: summary.actionableImprovements,
    recentNegativeEvents: summary.recentNegativeEvents,
  };
  if (exposeScore) view.trustScore = summary.trustScore;
  return view;
}
