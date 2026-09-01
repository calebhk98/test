import type { ImportanceLevel } from './types.js';

/**
 * Replaces the old `1 + abs(partner_answer - 3) * 0.25` extremity
 * heuristic (compatibility.service.ts), importance is now STATED by the
 * user, not inferred from how extreme their preference value looks.
 *
 * Documented multiplier per level, applied as
 * `questionWeight = baseWeight * multiplier(importance)` (see
 * scoring.ts):
 *
 *   irrelevant   -> 0    "I don't care", removes the question from
 *                        scoring entirely (zero weight AND excluded, so
 *                        it can never contribute even a zero-weighted
 *                        term that some averaging formula might treat
 *                        specially).
 *   slight       -> 0.5  Mild preference, counts, but half as much as
 *                        the baseline.
 *   important    -> 1.0  Baseline, the "I have a real preference"
 *                        default, equivalent to the old model's neutral
 *                        weight.
 *   critical     -> 2.0  Strong preference, double weight, but still a
 *                        matter of degree (a bad match here can be
 *                        outweighed by enough other good matches).
 *   deal_breaker -> 0    NOT a very-large weight. A deal breaker is not
 *                        "critical but more so", it is a different KIND
 *                        of preference: pass/fail, not gradation. It
 *                        contributes zero weight to the weighted-average
 *                        score (see scoring.ts `excluded: true`,
 *                        `reason: 'deal_breaker'`) and instead becomes a
 *                        hard filter (see dealBreakers.ts) that excludes
 *                        a non-matching candidate outright, upstream of
 *                        scoring, "filters are strictly enforced and
 *                        never overridden by scoring" only holds if
 *                        scoring never gets a vote on a deal breaker.
 *
 * Ordering irrelevant(0) < slight(0.5) < important(1) < critical(2) is a
 * documented invariant `tests/unit/questionScoring.test.ts` asserts
 * directly; deal_breaker is intentionally NOT part of that ordering (it
 * is off the scoring axis entirely, not "higher than critical").
 */
export const IMPORTANCE_MULTIPLIER: Record<ImportanceLevel, number> = {
  irrelevant: 0,
  slight: 0.5,
  important: 1.0,
  critical: 2.0,
  deal_breaker: 0,
};

/** Importance levels that remove a question from weighted scoring outright (zero weight, `excluded: true`). Both share multiplier 0, but for different reasons, see the module doc above. */
export function isScoringExcludedImportance(importance: ImportanceLevel): boolean {
  return importance === 'irrelevant' || importance === 'deal_breaker';
}

export function importanceMultiplier(importance: ImportanceLevel): number {
  return IMPORTANCE_MULTIPLIER[importance];
}
