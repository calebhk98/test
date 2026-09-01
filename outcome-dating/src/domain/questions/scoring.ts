import { importanceMultiplier, isScoringExcludedImportance } from './importance.js';
import { getTypeHandler } from './typeHandlers.js';
import type { QuestionAnswerState, QuestionDefinition } from './types.js';

/**
 * THE INTEGRATION SEAM (see task brief "put the new per-question scoring
 * contribution in a PURE, exported, fully-tested function ... A later
 * agent will wire compatibility.service to call it").
 *
 * `compatibility.service.ts` (owned by another agent, off limits here)
 * still computes its own score against the OLD `questions`/`answers`
 * schema for now. `scoreQuestionContribution` below is the pure function
 * a later agent should call ONCE PER QUESTION, per candidate pair, to
 * replace that computation for questions living in the new typed bank
 * (`question_bank` / `user_question_answers` — db/migrations/008_questions.sql).
 * It performs no I/O and imports nothing from `src/services/**`.
 *
 * EXACT CALL SIGNATURE:
 *
 *   scoreQuestionContribution(
 *     question: QuestionDefinition,      // from src/domain/questions/types.ts
 *     userA: QuestionAnswerState,        // A's answer to this question
 *     userB: QuestionAnswerState,        // B's answer to this question
 *   ): QuestionScoreContribution
 *
 * `QuestionAnswerState` bundles status + selfValue + preferenceValue +
 * importance for one user on one question (see types.ts) — "two users'
 * typed answers + importance + question definition" from the brief is
 * exactly `(question, userA, userB)`.
 *
 * A caller wiring this into `compatibility.service.ts` would, per shared
 * question, do roughly:
 *
 *   const contribution = scoreQuestionContribution(questionDef, aState, bState);
 *   if (!contribution.excluded) {
 *     weightedSum += contribution.satisfaction! * contribution.weight;
 *     weightTotal += contribution.weight;
 *   }
 *
 * and sum across every question in the bank, same accumulation shape
 * `computePairScore` already uses today.
 */

export type ExclusionReason =
  | 'not_active'
  | 'unanswered'
  | 'skipped'
  | 'prefer_not_to_say'
  | 'irrelevant'
  | 'deal_breaker';

export interface QuestionScoreContribution {
  /** True iff this question contributes nothing to a weighted score — see `reason`. */
  excluded: boolean;
  /** Why excluded; undefined when `excluded` is false. */
  reason?: ExclusionReason;
  /** 0..1 symmetric pair satisfaction for this question; `null` when excluded. */
  satisfaction: number | null;
  /** `question.baseWeight * mean(importanceMultiplier(A), importanceMultiplier(B))`; `0` when excluded. */
  weight: number;
}

function excluded(reason: ExclusionReason): QuestionScoreContribution {
  return { excluded: true, reason, satisfaction: null, weight: 0 };
}

/**
 * One question's contribution to a compatibility score between two users.
 *
 * Exclusion rules (in order):
 *   1. An inactive question never contributes (`reason: 'not_active'`).
 *   2. Any of the three non-answer states (`unanswered`, `skipped`,
 *      `prefer_not_to_say`) on EITHER side excludes the question — "None
 *      of the three contribute to scoring... This applies to ALL
 *      questions" (task brief). `prefer_not_to_say` is neutral for
 *      SCORING specifically; it can still fail another user's
 *      deal-breaker filter (see dealBreakers.ts) — that's a separate,
 *      upstream mechanism, not something this function does.
 *   3. `irrelevant` importance on either side excludes the question — "I
 *      don't care" must not contribute weight or satisfaction, full stop.
 *   4. `deal_breaker` importance on either side excludes the question
 *      from WEIGHTED SCORING — it is enforced as a hard filter instead
 *      (see dealBreakers.ts), never as a very-heavy scoring term. This is
 *      what keeps "filters are strictly enforced and never overridden by
 *      scoring" true: scoring simply never sees a deal breaker.
 *
 * When not excluded, satisfaction and weight are computed symmetrically
 * (matching `compatibility.service.ts#computePairScore`'s existing
 * argument-order-symmetry property, which its own tests assert):
 *
 *   satisfaction = mean(
 *     handler.satisfaction(A.selfValue, B.preferenceValue),  // does A satisfy what B wants?
 *     handler.satisfaction(B.selfValue, A.preferenceValue),  // does B satisfy what A wants?
 *   )
 *   weight = question.baseWeight * mean(
 *     importanceMultiplier(A.importance),
 *     importanceMultiplier(B.importance),
 *   )
 *
 * so `scoreQuestionContribution(q, a, b)` and `scoreQuestionContribution(q, b, a)`
 * always produce identical `satisfaction`/`weight` — verified directly in
 * tests/unit/questionScoring.test.ts.
 */
export function scoreQuestionContribution(
  question: QuestionDefinition,
  userA: QuestionAnswerState,
  userB: QuestionAnswerState,
): QuestionScoreContribution {
  if (!question.active) return excluded('not_active');

  for (const state of [userA, userB]) {
    if (state.status === 'unanswered') return excluded('unanswered');
    if (state.status === 'skipped') return excluded('skipped');
    if (state.status === 'prefer_not_to_say') return excluded('prefer_not_to_say');
  }

  // Both are now guaranteed status === 'answered', so importance is non-null.
  const importanceA = userA.importance!;
  const importanceB = userB.importance!;

  if (isScoringExcludedImportance(importanceA)) {
    return excluded(importanceA === 'irrelevant' ? 'irrelevant' : 'deal_breaker');
  }
  if (isScoringExcludedImportance(importanceB)) {
    return excluded(importanceB === 'irrelevant' ? 'irrelevant' : 'deal_breaker');
  }

  const handler = getTypeHandler(question.typeDef.type);

  const satisfactionAToB = handler.satisfaction(question.typeDef, userA.selfValue, userB.preferenceValue);
  const satisfactionBToA = handler.satisfaction(question.typeDef, userB.selfValue, userA.preferenceValue);
  const satisfaction = (satisfactionAToB + satisfactionBToA) / 2;

  const weight = question.baseWeight * ((importanceMultiplier(importanceA) + importanceMultiplier(importanceB)) / 2);

  return { excluded: false, satisfaction, weight };
}

/**
 * Convenience accumulator over a whole question set — sums
 * `scoreQuestionContribution` the same way `computePairScore` sums its
 * per-question terms, so a caller (or test) can get a single 0-1 score
 * without hand-rolling the reduction. `compatibility.service.ts` is free
 * to inline this shape itself instead of importing it — it's provided so
 * the accumulation logic itself is pure-tested here rather than only ever
 * exercised inline inside someone else's file.
 */
export interface AggregateScore {
  score: number;
  contributions: Array<{ questionId: string; contribution: QuestionScoreContribution }>;
  scoredQuestionCount: number;
}

export function aggregateQuestionScores(
  questions: QuestionDefinition[],
  answersA: Map<string, QuestionAnswerState>,
  answersB: Map<string, QuestionAnswerState>,
  noDataDefaultScore = 0,
): AggregateScore {
  const contributions: Array<{ questionId: string; contribution: QuestionScoreContribution }> = [];
  let weightedSum = 0;
  let weightTotal = 0;
  let scoredQuestionCount = 0;

  for (const question of questions) {
    const a = answersA.get(question.id) ?? { status: 'unanswered' as const, selfValue: null, preferenceValue: null, importance: null };
    const b = answersB.get(question.id) ?? { status: 'unanswered' as const, selfValue: null, preferenceValue: null, importance: null };
    const contribution = scoreQuestionContribution(question, a, b);
    contributions.push({ questionId: question.id, contribution });
    if (!contribution.excluded) {
      weightedSum += contribution.satisfaction! * contribution.weight;
      weightTotal += contribution.weight;
      scoredQuestionCount += 1;
    }
  }

  const score = weightTotal > 0 ? weightedSum / weightTotal : noDataDefaultScore;
  return { score, contributions, scoredQuestionCount };
}
