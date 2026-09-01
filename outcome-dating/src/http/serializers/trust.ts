/**
 * src/http/serializers/trust.ts — `GET /me/trust`.
 *
 * Spec §6.3: "The exact numeric trustScore is NOT shown to the user unless
 * product explicitly decides otherwise (default: level only)." `trustLevel`
 * is always the primary field; `trustScore` is gated behind
 * `trust.service.ts#shouldExposeRawTrustScore`, which reads the documented
 * `trust.expose_raw_score` config key (default `false`) — the ONLY gate for
 * this field. `trustScore` is withheld by default and an operator opts it
 * in by setting that config key, no deploy required.
 *
 * (Fixed per docs/duplication.md finding 1: this serializer used to gate
 * `trustScore` behind an unrelated, unseeded, per-user feature flag
 * — `expose_trust_score_to_user` — that the live route never reconciled
 * with `shouldExposeRawTrustScore`'s documented "single source of truth"
 * contract, so the documented `trust.expose_raw_score` config key had zero
 * effect on production responses. That flag-based path has been deleted
 * outright, not left as a second, competing gate.)
 *
 * `TrustSummary.actionableImprovements`/`recentNegativeEvents` are already
 * static template strings with no raw weights (trust.service.ts's own
 * invariant) — this serializer passes them through by explicit field name,
 * never a spread, so a future field added to `TrustSummary` cannot leak
 * through unreviewed.
 */
import type { TrustSummary } from '../../domain/types.js';
import type { Ctx } from '../../lib/ctx.js';
import { shouldExposeRawTrustScore } from '../../services/trust.service.js';

export interface TrustSummaryView {
  trustLevel: TrustSummary['trustLevel'];
  trustScore?: number;
  actionableImprovements: string[];
  recentNegativeEvents: string[];
}

export async function serializeTrustSummary(ctx: Ctx, summary: TrustSummary): Promise<TrustSummaryView> {
  const exposeScore = await shouldExposeRawTrustScore(ctx);
  const view: TrustSummaryView = {
    trustLevel: summary.trustLevel,
    actionableImprovements: summary.actionableImprovements,
    recentNegativeEvents: summary.recentNegativeEvents,
  };
  if (exposeScore) view.trustScore = summary.trustScore;
  return view;
}
