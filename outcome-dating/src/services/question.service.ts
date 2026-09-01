import type { Ctx } from '../lib/ctx.js';
import { NotImplementedError } from '../lib/errors.js';
import type { Answer, AnswerValue, Question } from '../domain/types.js';

/**
 * question.service — the compatibility question bank and per-user answers.
 * Spec: §8, §24.3 (routes), §27 (admin question manager).
 *
 * Owning agent: B.
 *
 * Invariants:
 *  - Every question has both a self answer and a partner answer (§8.1) —
 *    `putMyAnswers` accepts pairs, never a bare value.
 *  - `null` is a legal `selfValue`/`partnerValue` ("prefer not to say",
 *    §8.5) and MUST be treated as neutral by `compatibility.service.ts`,
 *    not coerced to 3.
 *  - Changing an already-answered question that is "critical" (weight
 *    above a threshold, or flagged sensitive) should be flagged by the
 *    caller (HTTP layer) for a confirmation step (§30.8) — this service
 *    just persists what it's given; the confirmation UX is not its job.
 */

export async function listActiveQuestions(ctx: Ctx): Promise<Question[]> {
  throw new NotImplementedError('question.listActiveQuestions');
}

export async function getMyAnswers(ctx: Ctx): Promise<Answer[]> {
  throw new NotImplementedError('question.getMyAnswers');
}

export interface AnswerInput {
  questionId: string;
  selfValue: AnswerValue;
  partnerValue: AnswerValue;
}

/** Upserts one or more answers for the caller. Triggers `compatibility.service.ts#refreshScoresForUser` as a side effect (spec §25.4 "on major answer changes"). */
export async function putMyAnswers(ctx: Ctx, answers: AnswerInput[]): Promise<Answer[]> {
  throw new NotImplementedError('question.putMyAnswers');
}

// ---- Admin (§27 question manager) ----

export interface CreateQuestionInput {
  slug: string;
  category: string;
  questionText: string;
  selfLeftLabel: string;
  selfRightLabel: string;
  partnerLeftLabel: string;
  partnerRightLabel: string;
  weight: number;
  polarity: 'standard' | 'reversed';
  sensitive: boolean;
}

export async function adminListQuestions(ctx: Ctx): Promise<Question[]> {
  throw new NotImplementedError('question.adminListQuestions');
}

export async function adminCreateQuestion(ctx: Ctx, input: CreateQuestionInput): Promise<Question> {
  throw new NotImplementedError('question.adminCreateQuestion');
}

export async function adminUpdateQuestion(ctx: Ctx, questionId: string, patch: Partial<CreateQuestionInput> & { active?: boolean }): Promise<Question> {
  throw new NotImplementedError('question.adminUpdateQuestion');
}
