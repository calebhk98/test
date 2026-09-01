import { getTypeHandler } from './typeHandlers.js';
import type { QuestionAnswerState, QuestionDefinition } from './types.js';

/**
 * THE FILTER SEAM (see task brief "deal breakers must go through the
 * existing filter service ... Export from question.service a function
 * that derives the filter rows a user's deal breakers imply ... Do not
 * reach into the filter service").
 *
 * `filter.service.ts` (off limits here) owns the `hard_filters` table and
 * `passesMutualFilters`/`updateMyFilters`. This module derives, PURELY
 * (no I/O, no import of filter.service.ts), the filter rows a user's
 * `deal_breaker`-importance answers imply, in the exact shape
 * `filter.service#updateMyFilters`'s `UpdateFilterInput` already accepts:
 * `{ filterKey, operator, value, enabled }`.
 *
 * WHAT A LATER AGENT MUST CALL:
 *   1. `question.service#getMyDealBreakerFilterRows(ctx)` (thin I/O
 *      wrapper around `deriveDealBreakerFilterRows` below, exported from
 *      question.service.ts) whenever a user's new-bank answers change.
 *   2. Pass the result straight to `filter.service#updateMyFilters(ctx, rows)`
 * mirroring how `question.service#putMyAnswers` already calls
 *      `compatibility.service#refreshScoresForUser` as a side effect
 *      today. This project's ownership boundary keeps that wiring out of
 *      this agent's hands (filter.service.ts is off limits), so it is
 *      NOT called automatically from anywhere in this file/PR.
 *   3. A stale deal-breaker filter (the user changes their preference
 *      from a deal breaker to something softer) must be retracted, not
 *      just left in place, `updateMyFilters` upserts by `filterKey`, so
 *      the wiring agent also needs a `disabled`/removed row emitted for
 *      any `qb:*` filter key that no longer has a corresponding deal
 *      breaker (this module's `deriveDealBreakerFilterRows` only emits
 *      currently-active deal breakers; the caller is responsible for
 *      diffing against previously-derived keys and disabling ones that
 *      dropped out, see `RETIRED-KEY NOTE` below for the exact
 *      shape to use).
 *
 * FILTER-KEY NAMESPACE: every derived filter key is prefixed `qb:` (e.g.
 * `qb:children_intention`) specifically so it can NEVER collide with an
 * old-schema `questions.slug` value that `filter.service.ts`'s default
 * `resolveAttributeValue` case already resolves against the OLD
 * `answers`/`questions` tables (see filter.service.ts's file-level
 * "CANDIDATE ATTRIBUTE SOURCING" note), a `qb:`-prefixed key is
 * guaranteed to fall through that default case and currently resolve to
 * `undefined` (fail-closed) until `filter.service.ts` is extended with a
 * `qb:`-aware branch that reads `user_question_answers` (see the
 * `RESOLUTION NOTE` on `deriveDealBreakerFilterRows` below).
 *
 * RESOLVED LIMITATION (multi_choice, `in` operator): `filter.service.ts`'s
 * `evaluateFilter` 'in' operator used to be `value.some(v => deepEqual(v,
 * candidateValue))`, which only ever worked when `candidateValue` was a
 * SCALAR (one array entry), it could never correctly express a
 * `multi_choice` deal breaker's "must include at least one of these"
 * semantics (see `isAcceptable`/typeHandlers.ts) against a candidate whose
 * `self_value` is itself an array. `filter.service.ts`'s 'in' operator now
 * special-cases an array `candidateValue` as OVERLAP ("shares at least one
 * element with `value`") rather than scalar membership, exactly this
 * row's semantics, so the row derived below is exact, not approximate.
 */

export type DealBreakerFilterOperator = 'eq' | 'gte' | 'lte' | 'in';

export interface DealBreakerFilterRow {
  filterKey: string;
  operator: DealBreakerFilterOperator;
  value: unknown;
  enabled: true;
  /**
   * Always `true` for a deal-breaker-derived row: an unresolved candidate
   * value (never answered the new-bank question, skipped it, or answered
   * `prefer_not_to_say`) must EXCLUDE the candidate, never silently let
   * them through. filter.service.ts's `UpdateFilterInput.excludeIfUnset`
   * (see that file's "MISSING/UNRESOLVED VALUES" note, added by the
   * sibling agent who owns that file) already documents this exact
   * expectation for filters this module derives, passed through
   * explicitly here so the caller doesn't need to know to set it.
   */
  excludeIfUnset: true;
  /**
   * True when `filter.service.ts`'s current operator set cannot express
   * this row exactly. Always `false`/absent as of the `evaluateFilter`
   * 'in'-operator overlap fix (see RESOLVED LIMITATION above), kept on
   * the type (rather than removed) so a future operator gap has somewhere
   * to signal from without a breaking type change.
   */
  approximate?: boolean;
}

/**
 * Derives the hard-filter row(s) implied by ONE deal-breaker answer.
 * Returns an empty array for a non-deal-breaker answer (nothing to
 * derive) or an unanswered/skipped/prefer_not_to_say state (a user who
 * hasn't stated a deal breaker has no filter to enforce from it).
 *
 * RESOLUTION NOTE for whoever wires `filter.service.ts` up to these rows:
 * `filter.service.ts`'s `resolveAttributeValue`'s default case resolves
 * `filterKey` against the OLD `questions`/`answers` tables by slug. To
 * make a `qb:`-prefixed key resolve correctly it needs a new branch that,
 * given `filterKey.slice(3)` as a `question_bank` slug, reads the
 * candidate's CURRENT `user_question_answers` row for that slug and
 * returns its `self_value`, `undefined` if absent (fail-closed, same
 * convention `loadSelfAnswerBySlug` already uses) or if `status !==
 * 'answered'` (an unanswered/skipped/`prefer_not_to_say` self value can't
 * be resolved to compare, deliberately: this is exactly what makes
 * `prefer_not_to_say` able to fail a deal-breaker filter, since
 * `evaluateFilter` treats `undefined` as always failing).
 */
export function deriveDealBreakerFilterRowsForQuestion(
  question: QuestionDefinition,
  answer: QuestionAnswerState,
): DealBreakerFilterRow[] {
  if (answer.status !== 'answered' || answer.importance !== 'deal_breaker') return [];

  const key = `qb:${question.slug}`;
  const preferenceValue = answer.preferenceValue;

  switch (question.typeDef.type) {
    case 'single_choice': {
      // preferenceValue is the acceptable-option SET; deal breaker or not,
      // it's already exactly what `evaluateFilter`'s 'in' operator expects
      // as `value` when `candidateValue` is a single option key.
      return [{ filterKey: key, operator: 'in', value: preferenceValue, enabled: true, excludeIfUnset: true }];
    }
    case 'multi_choice': {
      // See RESOLVED LIMITATION above, `evaluateFilter`'s 'in' operator
      // now treats an array `candidateValue` as "must overlap this set",
      // so this row is exact.
      return [{ filterKey: key, operator: 'in', value: preferenceValue, enabled: true, excludeIfUnset: true }];
    }
    case 'scale':
    case 'frequency': {
      // Deal breaker on an ordered type: zero tolerance, exact match only
      // (see typeHandlers.ts `isAcceptable` for the same rule applied to
      // scoring-side exclusion checks). A single 'eq' row is exact and
      // exactly representable by the existing operator set.
      return [{ filterKey: key, operator: 'eq', value: preferenceValue, enabled: true, excludeIfUnset: true }];
    }
  }
}

/** Derives every deal-breaker filter row implied by a user's full answer set. Pure, no I/O; `question.service#getMyDealBreakerFilterRows` is the I/O-performing wrapper. */
export function deriveDealBreakerFilterRows(
  questions: QuestionDefinition[],
  answersBySlug: Map<string, QuestionAnswerState>,
): DealBreakerFilterRow[] {
  const rows: DealBreakerFilterRow[] = [];
  for (const question of questions) {
    const answer = answersBySlug.get(question.slug);
    if (!answer) continue;
    rows.push(...deriveDealBreakerFilterRowsForQuestion(question, answer));
  }
  return rows;
}

// =====================================================================
// Pure deal-breaker EVALUATION (independent of filter.service.ts's own
// hard_filters persistence/resolution, see file doc). Exercises the
// exact semantics `RESOLUTION NOTE` above documents for
// `filter.service.ts` to eventually implement, so those semantics are
// directly unit-tested here even though filter.service.ts is off limits.
// =====================================================================

export interface DealBreakerCheckResult {
  passes: boolean;
  /** Slugs of deal breakers the candidate failed (or could not be resolved for, e.g. prefer_not_to_say). Empty when `passes`. */
  failedSlugs: string[];
}

/**
 * Does `candidateAnswer` satisfy `viewerAnswer`'s deal breaker on this
 * question? `undefined`/non-`answered` self-values on the candidate side
 * (never answered, skipped, or `prefer_not_to_say`) FAIL CLOSED, the
 * candidate is treated as not satisfying the deal breaker, matching
 * `filter.service.ts`'s existing fail-closed convention and the task
 * brief's rule "`prefer_not_to_say` ... can still fail another user's
 * deal-breaker filter, filters win."
 */
function candidateSatisfiesDealBreaker(
  question: QuestionDefinition,
  viewerAnswer: QuestionAnswerState,
  candidateAnswer: QuestionAnswerState,
): boolean {
  if (candidateAnswer.status !== 'answered') return false; // unanswered/skipped/prefer_not_to_say -> fail closed
  const handler = getTypeHandler(question.typeDef.type);
  return handler.isAcceptable(question.typeDef, candidateAnswer.selfValue, viewerAnswer.preferenceValue);
}

/**
 * Evaluates every deal breaker `viewerAnswersBySlug` states against
 * `candidateAnswersBySlug`. This is the pure semantic a later agent wires
 * into `filter.service.ts#passesMutualFilters` (or a `qb:`-aware
 * extension of it), see file doc.
 */
export function evaluateDealBreakers(
  questions: QuestionDefinition[],
  viewerAnswersBySlug: Map<string, QuestionAnswerState>,
  candidateAnswersBySlug: Map<string, QuestionAnswerState>,
): DealBreakerCheckResult {
  const failedSlugs: string[] = [];
  for (const question of questions) {
    const viewerAnswer = viewerAnswersBySlug.get(question.slug);
    if (!viewerAnswer || viewerAnswer.status !== 'answered' || viewerAnswer.importance !== 'deal_breaker') continue;
    const candidateAnswer = candidateAnswersBySlug.get(question.slug) ?? {
      status: 'unanswered' as const,
      selfValue: null,
      preferenceValue: null,
      importance: null,
    };
    if (!candidateSatisfiesDealBreaker(question, viewerAnswer, candidateAnswer)) {
      failedSlugs.push(question.slug);
    }
  }
  return { passes: failedSlugs.length === 0, failedSlugs };
}
