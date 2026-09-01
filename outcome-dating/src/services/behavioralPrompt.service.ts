import type { Ctx } from '../lib/ctx.js';
import { requireUserActor } from '../lib/ctx.js';
import { ConflictError, ForbiddenError, NotFoundError, ValidationError } from '../lib/errors.js';
import { KNOWN_FLAGS } from '../config/flags.service.js';
import type { AnswerValue, BehavioralPromptSuggestion } from '../domain/types.js';
import { putMyAnswers, resolveVisibleTagsFor } from './question.service.js';

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
 *
 * PATTERN DETECTION READING: the spec's own example ("If a user
 * repeatedly accepts profiles with a specific tag...") is about the
 * *reacting* user's accept/decline behavior toward the *other* party's
 * interest tags, on interests where the reacting user is EITHER sender or
 * recipient — "matched with" in the example copy means the interest
 * reached a decision (`accepted`/`declined`), regardless of who sent it.
 * Tags are read through `question.service#resolveVisibleTagsFor` — the
 * §8.4 reciprocal-disclosure gate — so a pattern is only ever built from
 * tags this user was actually allowed to see, never a `private_reciprocal`
 * tag they don't hold themselves. A tag is linked to a candidate question
 * by normalized-name-equals-slug (e.g. interest tag "Hiking" -> question
 * slug "hiking") since 001_init.sql has no explicit tag<->question link
 * table; ungraded/unlinked tags are silently skipped (no crash, no
 * suggestion) rather than invented as a new question, which is out of
 * this function's scope.
 *
 * CUTOVER NOTE (question-system-cutover build, reported — this file is
 * outside that build's file-ownership boundary and was deliberately left
 * fully unmodified): the redesigned typed question bank
 * (db/migrations/008_questions.sql, `question.service.ts`'s
 * `putMyQuestionAnswer`/`question_bank`/`user_question_answers`) is now
 * the ONLY bank every user-reachable route, `compatibility.service.ts`,
 * and `filter.service.ts` use. This file still targets the OLD bank
 * (`questions`/`answers`, via `question.service#putMyAnswers`) — that old
 * bank's tables and this one write path are kept alive (not dropped/
 * removed) specifically because this file depends on them and is off
 * limits to edit. See `question.service.ts`'s own file-level "WHAT COULD
 * NOT BE FULLY RETIRED" doc for the full accounting and the other two
 * off-limits files (`profile.service.ts`, `postDateFeedback.service.ts`)
 * in the same position. Migrating this file's pattern-detection/response
 * flow onto the new typed bank is flagged there as follow-up work for
 * whoever owns this file next.
 */

/**
 * Minimum number of accepted matches sharing a tag, strictly more than the
 * number of declines sharing that same tag, before it's considered a
 * pattern worth asking about. Spec §17 doesn't name a threshold; this is a
 * deliberately conservative placeholder constant (see
 * `compatibility.service.ts#DEFAULT_MIN_SHARED_QUESTIONS` for the parallel
 * note on why this isn't `ctx.config` — same file-ownership boundary).
 */
export const MIN_PATTERN_ACCEPT_COUNT = 3;

/** How many of the user's most recent decided (accepted/declined) interests to scan for a pattern. */
const RECENT_INTEREST_SCAN_LIMIT = 200;

interface SuggestionRow {
  id: string;
  user_id: string;
  question_id: string;
  trigger_kind: string;
  trigger_label: string;
  status: 'pending' | 'skipped' | 'answered';
  created_at: Date;
  responded_at: Date | null;
}

function suggestionFromRow(row: SuggestionRow): BehavioralPromptSuggestion {
  return {
    id: row.id,
    userId: row.user_id,
    questionId: row.question_id,
    triggerKind: row.trigger_kind,
    triggerLabel: row.trigger_label,
    createdAt: row.created_at,
  };
}

function normalizeForSlugMatch(name: string): string {
  return name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '');
}

/** Scans a user's recent accepted/declined interests for a pattern (e.g. a shared interest_tag) worth asking about, and records a suggestion row if one isn't already pending for that trigger. Does not itself notify the user — `notification.service.ts` handles delivery. */
export async function detectPatternsForUser(ctx: Ctx, userId: string): Promise<BehavioralPromptSuggestion[]> {
  const enabled = await ctx.flags.isEnabled(KNOWN_FLAGS.BEHAVIORAL_QUESTION_PROMPTS, { userId });
  if (!enabled) return [];

  const { rows: interestRows } = await ctx.db.query<{ other_user_id: string; status: 'accepted' | 'declined' }>(
    `SELECT
       CASE WHEN sender_id = $1 THEN recipient_id ELSE sender_id END AS other_user_id,
       status
     FROM interests
     WHERE (sender_id = $1 OR recipient_id = $1) AND status IN ('accepted', 'declined')
     ORDER BY created_at DESC
     LIMIT $2`,
    [userId, RECENT_INTEREST_SCAN_LIMIT],
  );
  if (interestRows.length === 0) return [];

  const acceptedCounts = new Map<string, number>();
  const declinedCounts = new Map<string, number>();
  const tagNames = new Map<string, string>();

  for (const row of interestRows) {
    const visibleTags = await resolveVisibleTagsFor(ctx, userId, row.other_user_id);
    const bucket = row.status === 'accepted' ? acceptedCounts : declinedCounts;
    for (const tag of visibleTags) {
      bucket.set(tag.tagId, (bucket.get(tag.tagId) ?? 0) + 1);
      tagNames.set(tag.tagId, tag.name);
    }
  }

  const created: BehavioralPromptSuggestion[] = [];

  for (const [tagId, acceptedCount] of acceptedCounts) {
    const declinedCount = declinedCounts.get(tagId) ?? 0;
    if (acceptedCount < MIN_PATTERN_ACCEPT_COUNT || acceptedCount <= declinedCount) continue;

    const tagName = tagNames.get(tagId)!;
    const slug = normalizeForSlugMatch(tagName);

    const { rows: questionRows } = await ctx.db.query<{ id: string }>(
      'SELECT id FROM questions WHERE slug = $1 AND active = true',
      [slug],
    );
    const question = questionRows[0];
    if (!question) continue; // no linkable question — nothing to suggest asking

    const { rows: insertedRows } = await ctx.db.query<SuggestionRow>(
      `INSERT INTO behavioral_prompt_suggestions (user_id, question_id, trigger_kind, trigger_label, status, created_at)
       VALUES ($1, $2, 'tag', $3, 'pending', $4)
       ON CONFLICT (user_id, question_id) WHERE status = 'pending' DO NOTHING
       RETURNING *`,
      [userId, question.id, tagName, ctx.clock.now()],
    );
    if (insertedRows[0]) created.push(suggestionFromRow(insertedRows[0]));
  }

  return created;
}

export async function listPendingSuggestions(ctx: Ctx): Promise<BehavioralPromptSuggestion[]> {
  const { userId } = requireUserActor(ctx);
  const { rows } = await ctx.db.query<SuggestionRow>(
    `SELECT * FROM behavioral_prompt_suggestions WHERE user_id = $1 AND status = 'pending' ORDER BY created_at DESC`,
    [userId],
  );
  return rows.map(suggestionFromRow);
}

export interface SuggestionResponse {
  skipped: boolean;
  selfValue?: AnswerValue;
  partnerValue?: AnswerValue;
}

/** Records the user's explicit response. If not skipped, forwards to `question.service#putMyAnswers` — this module never writes `answers` directly. */
export async function respondToSuggestion(ctx: Ctx, suggestionId: string, response: SuggestionResponse): Promise<void> {
  const { userId } = requireUserActor(ctx);

  const { rows } = await ctx.db.query<SuggestionRow>('SELECT * FROM behavioral_prompt_suggestions WHERE id = $1', [
    suggestionId,
  ]);
  const suggestion = rows[0];
  if (!suggestion) {
    throw new NotFoundError(`Suggestion "${suggestionId}" not found`, { suggestionId });
  }
  if (suggestion.user_id !== userId) {
    throw new ForbiddenError('This suggestion does not belong to the caller', { suggestionId });
  }
  if (suggestion.status !== 'pending') {
    throw new ConflictError(`Suggestion "${suggestionId}" was already ${suggestion.status}`, { suggestionId, status: suggestion.status });
  }

  if (response.skipped) {
    await ctx.db.query(
      `UPDATE behavioral_prompt_suggestions SET status = 'skipped', responded_at = $2 WHERE id = $1`,
      [suggestionId, ctx.clock.now()],
    );
    return;
  }

  if (response.selfValue === undefined || response.partnerValue === undefined) {
    throw new ValidationError('Please answer both parts of this question, or skip it for now.', {
      suggestionId,
    });
  }

  // Rule 1: the only write to `answers` happens inside `question.putMyAnswers`,
  // driven by this explicit user response — never here directly.
  await putMyAnswers(ctx, [
    { questionId: suggestion.question_id, selfValue: response.selfValue, partnerValue: response.partnerValue },
  ]);

  await ctx.db.query(
    `UPDATE behavioral_prompt_suggestions SET status = 'answered', responded_at = $2 WHERE id = $1`,
    [suggestionId, ctx.clock.now()],
  );
}
