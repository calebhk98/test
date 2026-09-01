import type { Ctx } from '../lib/ctx.js';
import { NotImplementedError } from '../lib/errors.js';
import type { AnswerValue, BehavioralPromptSuggestion } from '../domain/types.js';

/**
 * behavioralPrompt.service — §17 behavioral question triggers.
 * Spec: §17.
 *
 * Owning agent: B.
 *
 * Invariants (spec §17 rules 1-4, restated because they're easy to
 * violate accidentally):
 *  1. Never write to `answers` from a detected pattern — only
 *     `question.service#putMyAnswers` (driven by an explicit user
 *     response) may do that.
 *  2. Never change compatibility sorting based on a detected pattern
 *     alone — `compatibility.service.ts` only reads `answers`.
 *  3. A suggestion must be surfaced to the user, not applied silently.
 *  4. The user can skip; skipping records that the suggestion was shown
 *     and dismissed, not an answer.
 *
 * Gated behind the `behavioral_question_prompts` feature flag (spec §22).
 */

/** Scans a user's recent accepted/declined interests for a pattern (e.g. a shared interest_tag) worth asking about, and records a suggestion row if one isn't already pending for that trigger. Does not itself notify the user — `notification.service.ts` handles delivery. */
export async function detectPatternsForUser(ctx: Ctx, userId: string): Promise<BehavioralPromptSuggestion[]> {
  throw new NotImplementedError('behavioralPrompt.detectPatternsForUser');
}

export async function listPendingSuggestions(ctx: Ctx): Promise<BehavioralPromptSuggestion[]> {
  throw new NotImplementedError('behavioralPrompt.listPendingSuggestions');
}

export interface SuggestionResponse {
  skipped: boolean;
  selfValue?: AnswerValue;
  partnerValue?: AnswerValue;
}

/** Records the user's explicit response. If not skipped, forwards to `question.service#putMyAnswers` — this module never writes `answers` directly. */
export async function respondToSuggestion(ctx: Ctx, suggestionId: string, response: SuggestionResponse): Promise<void> {
  throw new NotImplementedError('behavioralPrompt.respondToSuggestion');
}
