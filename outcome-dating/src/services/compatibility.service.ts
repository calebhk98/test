import type { Ctx } from '../lib/ctx.js';
import { NotImplementedError } from '../lib/errors.js';
import type { Answer, CompatibilityScoreRow, Question } from '../domain/types.js';

/**
 * compatibility.service — the §16.2 scoring formula and its storage.
 * Spec: §16, §25.4 (nightly refresh job).
 *
 * Owning agent: B.
 *
 * INVARIANT: this module SORTS; it never decides who is eligible to be
 * seen. `discovery.service.ts` calls `getScore`/`getScoresForCandidates`
 * only after `filter.service.ts#passesMutualFilters` has already gated the
 * candidate pool (spec §16.1, §9.1).
 *
 * `computePairScore` is a pure function of two users' answers + the
 * question bank — no I/O — so it's directly unit-testable against the
 * worked example in spec §16.2. `getScore`/`refreshScoresForUser` are the
 * I/O-performing wrappers that read `answers`, call `computePairScore`,
 * and read/write the `compatibility_scores` materialization (spec §16.3).
 */

export interface PerQuestionSatisfaction {
  questionId: string;
  pairSatisfaction: number; // 0-1
  questionWeight: number; // base_weight * importance_multiplier
}

export interface CompatibilityBreakdown {
  score: number; // 0-1; 0 if too few shared answered questions (§16.2 last paragraph)
  perQuestion: PerQuestionSatisfaction[];
  sharedAnsweredQuestionCount: number;
}

/**
 * Pure implementation of the §16.2 formula for one ordered pair (A, B).
 * Symmetric by construction (`pair_satisfaction` averages both
 * directions), so `computePairScore(a, b, qs) === computePairScore(b, a, qs)`
 * is an expected property for tests. `null` self/partner values
 * ("prefer not to say", §8.5) are excluded from `sharedAnsweredQuestionCount`
 * and do not contribute to the weighted sum.
 */
export function computePairScore(
  userAAnswers: Answer[],
  userBAnswers: Answer[],
  questions: Question[],
  minSharedQuestions: number,
): CompatibilityBreakdown {
  throw new NotImplementedError('compatibility.computePairScore');
}

/** On-demand score for one candidate pair, reading from `compatibility_scores` if fresh, else computing and upserting it (spec §16.3 "For MVP, compute score on demand"). */
export async function getScore(ctx: Ctx, userId: string, candidateId: string): Promise<number> {
  throw new NotImplementedError('compatibility.getScore');
}

/** Batch variant used by `discovery.service.ts` to sort a whole candidate page in one call. */
export async function getScoresForCandidates(ctx: Ctx, userId: string, candidateIds: string[]): Promise<Map<string, number>> {
  throw new NotImplementedError('compatibility.getScoresForCandidates');
}

/** Recomputes and upserts `compatibility_scores` rows for one user against every candidate that currently passes their mutual filters. Called after an answer change (spec §25.4 "on major answer changes"). */
export async function refreshScoresForUser(ctx: Ctx, userId: string): Promise<{ updated: number }> {
  throw new NotImplementedError('compatibility.refreshScoresForUser');
}

/** §25.4 nightly job: refresh every user's `compatibility_scores`. */
export async function refreshAllScores(ctx: Ctx): Promise<{ updated: number }> {
  throw new NotImplementedError('compatibility.refreshAllScores');
}

export type { CompatibilityScoreRow };
