import type { Ctx } from '../lib/ctx.js';
import { requireUserActor } from '../lib/ctx.js';
import { ConflictError, ForbiddenError, NotFoundError, ValidationError } from '../lib/errors.js';
import { KNOWN_FLAGS } from '../config/flags.service.js';
import type { BehavioralPromptSuggestion } from '../domain/types.js';
import type { ImportanceLevel, LadderPosition } from '../domain/questions/index.js';
import {
  getCurrentQuestionBySlug,
  getQuestionBankSlugById,
  putMyQuestionAnswer,
  resolveVisibleTagsFor,
} from './question.service.js';

/**
 * behavioralPrompt.service — §17 behavioral question triggers.
 * Spec: §17.
 *
 * Owning agent: B.
 *
 * Invariants (spec §17 rules 1-4, restated because they're easy to
 * violate accidentally):
 *  1. Never write a new-bank answer from a detected pattern — only
 *     `question.service#putMyQuestionAnswer` (driven by an explicit user
 *     response) may do that.
 *  2. Never change compatibility sorting based on a detected pattern
 *     alone — `compatibility.service.ts` only ever scores from
 *     `user_question_answers` rows a user themselves wrote via
 *     `putMyQuestionAnswer`.
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
 * CUTOVER NOTE (question-system retirement build): this file now targets
 * the ONE typed question bank (db/migrations/008_questions.sql,
 * `question.service.ts`'s `question_bank`/`user_question_answers`)
 * exclusively — the old `questions`/`answers` tables it used to read/write
 * via `question.service#putMyAnswers` are gone (see
 * `db/migrations/022_drop_old_question_bank.sql`). Two consequences of the
 * new model worth flagging explicitly rather than papering over:
 *
 *   1. LINKABLE QUESTION LOOKUP: `detectPatternsForUser` now resolves a
 *      candidate tag-linked slug via `question.service#getCurrentQuestionBySlug`
 *      (current + active row in `question_bank`) instead of the old
 *      `SELECT id FROM questions WHERE slug = $1 AND active = true`. Same
 *      "no linkable question -> skip, don't invent one" behavior.
 *
 *   2. ANSWERING A SUGGESTION NOW NEEDS AN IMPORTANCE THE OLD MODEL NEVER
 *      HAD, AND THE ONE LIVE HTTP CALLER CANNOT SUPPLY IT — flagged rather
 *      than papered over with a fabricated default (see
 *      `question.service.ts`'s own `008_questions.sql` migration-choice
 *      doc for why this codebase specifically refuses to invent importance
 *      data). `src/http/routes/profile.routes.ts` (outside this build's
 *      ownership boundary, not touched) still calls `respondToSuggestion`
 *      with only `{ skipped, selfValue, partnerValue }` — its own
 *      `RespondSuggestionBodySchema` has no `importance` field and cannot
 *      be extended from here. `SuggestionResponse` below keeps those exact
 *      field names for that caller to keep compiling (`partnerValue` is
 *      treated as the new bank's `preferenceValue` — the same "what you
 *      want in a partner" meaning it always had), and adds the new,
 *      genuinely-required `importance`/`ladderPosition` fields the old
 *      shape has no way to populate. Concretely:
 *        - Skipping a suggestion still works exactly as before through
 *          that endpoint.
 *        - ANSWERING one through that endpoint no longer succeeds:
 *          `respondToSuggestion` throws a `ValidationError` naming exactly
 *          what's missing, rather than silently defaulting `importance` to
 *          some invented value. This is a genuine, reported behavior gap —
 *          the fix is extending `profile.routes.ts`'s schema to collect
 *          `importance` (and, for a ladder-presentation question,
 *          `ladderPosition`) from the client, which is outside this
 *          build's file-ownership boundary.
 *        - A caller that CAN supply `importance`/`ladderPosition` (a
 *          future client update, or a direct `question.service` caller)
 *          gets the full, real typed-bank answer recorded, including the
 *          usual `refreshScoresForUser`/`syncDealBreakerFilters` side
 *          effects — see `putMyQuestionAnswer`'s own doc.
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

    // Current + active row in the ONE typed bank — see this file's
    // CUTOVER NOTE. Same "no linkable question -> skip, don't invent one"
    // behavior as the old `SELECT id FROM questions WHERE slug = $1 AND
    // active = true` lookup this replaces.
    const question = await getCurrentQuestionBySlug(ctx, slug);
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
  /**
   * Field names (`selfValue`/`partnerValue`) deliberately kept from the OLD
   * 1-5 shape — see this file's CUTOVER NOTE: `src/http/routes/profile.routes.ts`
   * (outside this build's ownership boundary) constructs this object with
   * exactly these two field names, and renaming them would break that
   * caller's compile. `partnerValue` is treated as the new bank's
   * `preferenceValue` — the same "what you want in a partner" meaning it
   * always had.
   */
  selfValue?: unknown;
  partnerValue?: unknown;
  /**
   * The new bank's required third axis (see `question.service#putMyQuestionAnswer`'s
   * "value + importance, never a bare number" invariant) — genuinely new,
   * not something the old model had an equivalent of. NOT settable through
   * `profile.routes.ts`'s current body schema; see this file's CUTOVER
   * NOTE for the resulting, reported behavior gap.
   */
  importance?: ImportanceLevel;
  /** Alternative to `partnerValue`+`importance` for a ladder-presentation question — see `putMyQuestionAnswer`'s doc. Same "not reachable from `profile.routes.ts` today" caveat as `importance`. */
  ladderPosition?: LadderPosition;
}

/**
 * Records the user's explicit response. If not skipped, forwards to
 * `question.service#putMyQuestionAnswer` — this module never writes a
 * new-bank answer directly (rule 1).
 *
 * See this file's CUTOVER NOTE for why a response driven purely by the OLD
 * `{selfValue, partnerValue}` shape (i.e. no `importance`/`ladderPosition`
 * supplied) throws rather than silently inventing an importance level.
 */
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

  if (response.selfValue === undefined) {
    throw new ValidationError('Please answer this question, or skip it for now.', { suggestionId });
  }
  if (response.ladderPosition === undefined && (response.partnerValue === undefined || response.importance === undefined)) {
    throw new ValidationError(
      'Answering this suggestion requires an importance (or a ladder position, on a ladder-presentation question) — ' +
        'this caller only supplied a value, which the typed question bank can no longer accept on its own.',
      { suggestionId },
    );
  }

  // `suggestion.question_id` is the question_bank id that was CURRENT when
  // this suggestion was created — resolve it back to its stable slug so we
  // can answer against whatever is current NOW (the bank may have been
  // re-versioned since), exactly like every other `putMyQuestionAnswer`
  // caller.
  const slug = await getQuestionBankSlugById(ctx, suggestion.question_id);
  if (!slug) {
    throw new NotFoundError('The question behind this suggestion no longer exists.', { suggestionId });
  }

  // Rule 1: the only write to a new-bank answer happens inside
  // `question.service#putMyQuestionAnswer`, driven by this explicit user
  // response — never here directly.
  await putMyQuestionAnswer(ctx, {
    slug,
    status: 'answered',
    selfValue: response.selfValue,
    preferenceValue: response.partnerValue,
    importance: response.importance,
    ladderPosition: response.ladderPosition,
  });

  await ctx.db.query(
    `UPDATE behavioral_prompt_suggestions SET status = 'answered', responded_at = $2 WHERE id = $1`,
    [suggestionId, ctx.clock.now()],
  );
}
