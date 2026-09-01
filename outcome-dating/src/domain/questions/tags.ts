/**
 * Interest-tag intensity + avoidance — pure domain logic.
 *
 * Persistence lives in question.service.ts (new `user_tag_intensity` /
 * `user_avoid_tags` tables, db/migrations/008_questions.sql). This module
 * is the pure math/semantics a later agent wires into discovery scoring
 * and filtering — see the file-level notes on each function for exactly
 * what to call and from where.
 */

/**
 * How often/how much a user engages with a tag they hold ("I bake" is not
 * one thing — daily vs. once a quarter are different). Reuses the same
 * five-anchor frequency shape as the `frequency` question type
 * (types.ts/typeHandlers.ts) for one consistent ordinal vocabulary across
 * the whole bank, rather than inventing a second frequency scale.
 */
export const TAG_INTENSITY_LEVELS = ['rarely', 'occasionally', 'regularly', 'frequently', 'daily'] as const;
export type TagIntensity = (typeof TAG_INTENSITY_LEVELS)[number];

const INTENSITY_ORDINAL: Record<TagIntensity, number> = {
  rarely: 0,
  occasionally: 1,
  regularly: 2,
  frequently: 3,
  daily: 4,
};

/**
 * 0..1 match quality between two users' intensity on the SAME shared tag
 * — closer intensities score higher. Distance-based, symmetric, same
 * shape as `typeHandlers.ts`'s scale/frequency `satisfaction`.
 *
 * WHAT A LATER AGENT MUST CALL: `discovery.service.ts` (off limits here)
 * currently surfaces at most one shared tag per candidate via
 * `question.service#resolveVisibleTagsFor` with no notion of "how well do
 * our intensities match" — wiring this in means, for each shared visible
 * tag, calling `scoreTagIntensityMatch(viewerIntensity, candidateIntensity)`
 * (intensities read from the new `user_tag_intensity` table via a new
 * `question.service` export) and using it as a tie-breaker or secondary
 * sort signal alongside `compatibilityScore` — NOT as a replacement for
 * it, since intensity match is a much narrower signal than the full
 * question-bank score.
 */
export function scoreTagIntensityMatch(a: TagIntensity, b: TagIntensity): number {
  const range = TAG_INTENSITY_LEVELS.length - 1;
  return 1 - Math.abs(INTENSITY_ORDINAL[a] - INTENSITY_ORDINAL[b]) / range;
}

// =====================================================================
// Avoidance — "do not show me people who list <tag>". Behaves like a
// hard filter: pure exclusion, never a down-rank.
// =====================================================================

export interface AvoidTagCheckResult {
  passes: boolean;
  /** Tag ids that caused exclusion (from either direction — see doc below). Empty when `passes`. */
  violatingTagIds: string[];
}

/**
 * Bidirectional avoid-tag check between two users' VISIBLE tag sets
 * (already filtered through `question.service#resolveVisibleTagsFor`'s
 * public/private-reciprocal/hidden rules — this function does not itself
 * know about visibility). Fails if:
 *   - the viewer avoids any tag the candidate holds, OR
 *   - the candidate avoids any tag the viewer holds
 * — mirroring `filter.service.ts#passesMutualFilters`'s existing
 * "both directions must pass" shape for hard filters, since an avoid tag
 * is specified to "behave like a hard filter" (task brief).
 *
 * WHAT A LATER AGENT MUST CALL: `discovery.service.ts`'s candidate loop
 * (off limits here) should call this — via a new `question.service`
 * export wrapping this function plus `user_avoid_tags` reads — at the
 * SAME gating point it already calls `filter.service#passesMutualFilters`,
 * before a candidate is scored/shown at all, not as a post-hoc filter on
 * an already-sorted list.
 */
export function passesAvoidTagFilter(
  viewerVisibleTagIds: ReadonlySet<string>,
  viewerAvoidTagIds: ReadonlySet<string>,
  candidateVisibleTagIds: ReadonlySet<string>,
  candidateAvoidTagIds: ReadonlySet<string>,
): AvoidTagCheckResult {
  const violatingTagIds: string[] = [];

  for (const tagId of candidateVisibleTagIds) {
    if (viewerAvoidTagIds.has(tagId)) violatingTagIds.push(tagId);
  }
  for (const tagId of viewerVisibleTagIds) {
    if (candidateAvoidTagIds.has(tagId)) violatingTagIds.push(tagId);
  }

  return { passes: violatingTagIds.length === 0, violatingTagIds: [...new Set(violatingTagIds)] };
}
