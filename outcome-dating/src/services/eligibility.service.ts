import type { Ctx } from '../lib/ctx.js';
import { passesMutualFilters } from './filter.service.js';

/**
 * eligibility.service — the ONE shared mutual-eligibility evaluation
 * every enforcement layer calls, so the three guarantees the product
 * owner asked for (never let a doomed interest be SENT; if one slips
 * through anyway, REFUSE it; if one is already sitting PENDING when the
 * recipient's filters change, retroactively DECLINE it) can never drift
 * out of sync with each other or with what discovery already does.
 *
 * Spec: §9 (filters), §9.4 (mutual filter requirement), §11 (interests).
 * This build's addition — no single spec section, product-owner request
 * from user testing (see the task brief this build implements).
 *
 * THREE CALLERS, ONE IMPLEMENTATION:
 *   1. Discovery (`discovery.service.ts`, owned by another agent, NOT
 *      modified by this build) already gates on
 *      `filter.service#passesMutualFilters` directly before a candidate
 *      is ever scored — this file wraps that exact same function rather
 *      than reimplementing it, so Layer 1 and Layers 2/3 are provably
 *      the same check. See this build's report for the verification test
 *      (`tests/unit/eligibility.test.ts`) proving discovery's mutual
 *      exclusion holds both directions.
 *   2. `interest.service.ts#sendInterest` (Layer 2) calls
 *      `evaluateMutualEligibility` fresh — never from a cached discovery
 *      grid — immediately before creating the interest row, and refuses
 *      the send (no row created, so no outgoing slot/daily-quota
 *      consumed) if the recipient's hard filters would exclude the
 *      sender, or vice versa.
 *   3. `interest.service.ts#sweepAutoDeclineForRecipient` /
 *      `sweepAutoDeclineAll` (Layer 3) call it again for every PENDING
 *      interest whenever a recipient's filters might have changed, and
 *      auto-decline anything that no longer passes.
 *
 * WHY THIS WRAPS `filter.service#passesMutualFilters` RATHER THAN
 * `discovery.service#isProfileVisibleTo`: the latter also folds in
 * capacity limits, moderation visibility, and blocking (§10.2's full
 * nine-point list) — genuinely relevant to whether a candidate is SHOWN,
 * but not what "would this recipient's own stated deal breakers
 * auto-decline this interest" means. A momentarily-full inbox or an
 * account mid-shadowban-review is not a filter mismatch, and conflating
 * them here would (a) refuse sends for reasons that have nothing to do
 * with the privacy-sensitive filter-probing risk this file exists to
 * prevent, and (b) auto-decline pending interests in Layer 3 every time
 * unrelated capacity/moderation state fluctuates, which is not what "your
 * filters changed" means. `sendInterest` already separately enforces the
 * capacity rules (outgoing/incoming/daily caps) — see that file.
 *
 * CANDIDATE ATTRIBUTE SOURCING / PREFERENCE-MODEL INDEPENDENCE: this
 * function evaluates the durable, enforced `hard_filters` ROWS via
 * `passesMutualFilters` — never raw `answers`/preference rows directly.
 * A concurrent build is replacing how a preference is captured (a VALUE
 * plus an IMPORTANCE, `irrelevant` … `deal_breaker`, with a
 * `deal_breaker` importance deriving a `hard_filters` row). This file
 * makes no assumption about that capture step at all: as long as a
 * deal-breaker preference continues to derive a row in `hard_filters`
 * with the existing `{user_id, filter_key, operator, value, enabled,
 * exclude_if_unset}` shape — which is `filter.service.ts`'s documented
 * contract, unchanged by this build — mutual-eligibility enforcement
 * keeps working with zero changes here, regardless of how many more ways
 * preferences get captured upstream of that row.
 */

/**
 * Result of one fresh mutual-eligibility evaluation between two users.
 * Deliberately just a boolean plus a diagnostic flag — never *which*
 * filter/attribute caused a `false`, so nothing downstream can leak that
 * even if it tried (see `interest.service.ts`'s refusal-copy handling,
 * which never even receives more than this).
 */
export interface EligibilityResult {
  /** True iff `userId` passes `candidateId`'s enabled hard filters AND `candidateId` passes `userId`'s (spec §9.4, both directions). */
  eligible: boolean;
  /**
   * False only when the underlying evaluation itself threw (a transient
   * DB/query error, not "the check ran and said no"). Callers use this to
   * log/alert without changing the fail-open outcome — see this
   * function's own doc for the fail-open reasoning. `eligible` is always
   * `true` when `evaluatedOk` is `false`.
   */
  evaluatedOk: boolean;
}

/**
 * Fresh, uncached §9.4 mutual-filter evaluation between `userId` and
 * `candidateId` — always re-reads `hard_filters` (via
 * `filter.service#passesMutualFilters`) at call time. Never accepts or
 * consults a cached discovery grid, snapshot, or prior result: the whole
 * point of Layers 2/3 is to catch cases where a stale grid, a direct
 * profile link, or a just-tightened filter would otherwise let a doomed
 * interest through.
 *
 * ---------------------------------------------------------------------
 * FAIL-OPEN DECISION (deliberate, not an oversight — task brief asks for
 * this to be documented):
 * ---------------------------------------------------------------------
 * If `passesMutualFilters` throws, this function returns
 * `{ eligible: true, evaluatedOk: false }` rather than propagating the
 * error or treating the pair as ineligible. Reasoning:
 *
 *   - A false REFUSAL at send time (treating an evaluation error as
 *     "ineligible") silently blocks a legitimate interest behind the
 *     exact same generic copy as a real filter mismatch — the sender has
 *     no way to tell a transient bug from a real deal-breaker, and no
 *     recourse. That is a worse outcome than the interest going through.
 *   - A false ALLOW is not a permanent hole: Layer 3 (the retroactive
 *     sweep, `sweepAutoDeclineForRecipient`/`sweepAutoDeclineAll`) is
 *     driven by `ctx.clock`, safe to re-run, and re-evaluates every
 *     PENDING interest's eligibility again on the next filter update or
 *     periodic run. A doomed interest that slipped past Layer 2 only
 *     because of a transient evaluation error gets caught and
 *     auto-declined the moment eligibility can actually be computed —
 *     with the sender's slot freed and (per `interest.service.ts`'s
 *     `decline_origin = 'auto'`) zero trust impact, exactly as if Layer 2
 *     had caught it in the first place.
 *   - This mirrors the codebase's existing posture elsewhere (e.g.
 *     `filter.service.ts`'s `excludeIfUnset` defaulting `false` — "don't
 *     silently vanish a legitimate user" — for optional fields) of
 *     preferring a second, self-correcting layer over a first layer that
 *     blocks everything on any hiccup.
 *
 * Fail-CLOSED (treating an error as ineligible) would be the wrong
 * default here specifically because Layer 3 exists as a backstop; a
 * system with no retroactive sweep would need the opposite default.
 */
export async function evaluateMutualEligibility(
  ctx: Ctx,
  userId: string,
  candidateId: string,
): Promise<EligibilityResult> {
  try {
    const eligible = await passesMutualFilters(ctx, userId, candidateId);
    return { eligible, evaluatedOk: true };
  } catch (err) {
    ctx.logger.warn('eligibility evaluation failed; failing open (see eligibility.service.ts doc)', {
      userId,
      candidateId,
      error: err instanceof Error ? err.message : String(err),
    });
    return { eligible: true, evaluatedOk: false };
  }
}
