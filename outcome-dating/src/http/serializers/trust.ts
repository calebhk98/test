/**
 * src/http/serializers/trust.ts, `GET /me/trust`.
 *
 * Spec §6.3: "The exact numeric trustScore is NOT shown to the user unless
 * product explicitly decides otherwise (default: level only)." `trustLevel`
 * is always the primary field; `trustScore` is gated behind
 * `trust.service.ts#shouldExposeRawTrustScore`, which reads the documented
 * `trust.expose_raw_score` config key (default `false`), the ONLY gate for
 * this field. `trustScore` is withheld by default and an operator opts it
 * in by setting that config key, no deploy required.
 *
 * (Fixed per docs/duplication.md finding 1: this serializer used to gate
 * `trustScore` behind an unrelated, unseeded, per-user feature flag
 * `expose_trust_score_to_user`, that the live route never reconciled
 * with `shouldExposeRawTrustScore`'s documented "single source of truth"
 * contract, so the documented `trust.expose_raw_score` config key had zero
 * effect on production responses. That flag-based path has been deleted
 * outright, not left as a second, competing gate.)
 *
 * `TrustSummary.actionableImprovements`/`recentNegativeEvents` are already
 * static template strings with no raw weights (trust.service.ts's own
 * invariant), this serializer passes them through by explicit field name,
 * never a spread, so a future field added to `TrustSummary` cannot leak
 * through unreviewed.
 */
import type { TrustSummary } from '../../domain/types.js';
import type { Ctx } from '../../lib/ctx.js';
import { requireUserActor } from '../../lib/ctx.js';
import { shouldExposeRawTrustScore, can, type CapabilityDecision, type TrustGatedAction } from '../../services/trust.service.js';
import { getDefaultPaymentMethod } from '../../services/payment.service.js';

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

/**
 * `GET /me/capabilities`, `trust.service#can()` was fully built (a
 * capability check with safe, user-displayable `reasonCode`s) but never
 * called from any route (docs/ux-api-review.md §11), so a client had no
 * way to gray out a button with a reason instead of letting a user tap
 * something that would 403. Every `TrustGatedAction` is evaluated up
 * front so a client can pre-render every disabled state in one call.
 */
const TRUST_GATED_ACTIONS: readonly TrustGatedAction[] = ['browse', 'send_interest', 'chat', 'send_links', 'propose_date'];

export type MyCapabilitiesView = Record<TrustGatedAction, CapabilityDecision>;

export async function getMyCapabilities(ctx: Ctx): Promise<MyCapabilitiesView> {
  const { userId, trustLevel } = requireUserActor(ctx);
  const defaultMethod = await getDefaultPaymentMethod(ctx, userId);
  const subject = { trustLevel, hasVerifiedPaymentMethod: defaultMethod?.verifiedAt != null };

  const entries = await Promise.all(TRUST_GATED_ACTIONS.map(async (action) => [action, await can(ctx, action, subject)] as const));
  return Object.fromEntries(entries) as MyCapabilitiesView;
}
