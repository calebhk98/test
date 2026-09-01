import { z } from 'zod';
import type { Ctx } from '../lib/ctx.js';
import { requireUserActor } from '../lib/ctx.js';
import { ConflictError, NotFoundError, ValidationError } from '../lib/errors.js';
import { refreshScoresForUser } from './compatibility.service.js';
import { getMyFilters, updateMyFilters } from './filter.service.js';
import type { UpdateFilterInput } from './filter.service.js';
import {
  IMPORTANCE_LEVELS,
  TAG_INTENSITY_LEVELS,
  deriveDealBreakerFilterRows,
  getTypeHandler,
  ladderPositionToPreference,
  presentationFor,
  selectNextQuestions,
} from '../domain/questions/index.js';
import type {
  DealBreakerFilterRow,
  ImportanceLevel,
  LadderPosition,
  QuestionAnswerState,
  QuestionDefinition,
  QuestionType,
  QuestionTypeDefinition,
  SelectableQuestion,
  SingleChoiceDefinition,
  TagIntensity,
} from '../domain/questions/index.js';
import { passesAvoidTagFilter } from '../domain/questions/tags.js';

/**
 * question.service, THE compatibility question bank and per-user answers.
 * Spec: §8, §24.3 (routes), §27 (admin question manager).
 *
 * Owning agent: B (question-system cutover build); finished by the
 * follow-up retirement build (see below).
 *
 * CUTOVER (question-system unification), COMPLETE. This file used to
 * also own a SECOND, OLDER question bank (`questions`/`answers`, a flat
 * 1-5 self/partner pair with no type or importance information). Every
 * surface now uses the ONE typed bank below exclusively:
 *   - `GET /questions`, `GET/PUT /me/answers` (src/http/routes/questions.routes.ts)
 *     serve the typed bank.
 *   - `compatibility.service.ts` scores exclusively from the typed bank
 *     (`user_question_answers`).
 *   - `filter.service.ts` resolves every non-structured filter key
 *     exclusively against the typed bank (`qb:`-prefixed filter keys),
 *     the old bank's bare-slug resolution shim has been removed.
 *   - `src/http/routes/admin.routes.ts`'s §27 admin question-manager panel
 *     (`GET/POST /admin/questions`, `PATCH /admin/questions/:id`) now
 *     calls `adminListQuestionBank`/`adminCreateQuestionBankEntry`/
 *     `adminUpdateQuestionBankEntry` below, an admin can no longer create
 *     or edit a question in a bank the product never scores.
 *   - `src/services/behavioralPrompt.service.ts` detects patterns and
 *     records/answers suggestions against the typed bank
 *     (`putMyQuestionAnswer`, via `getQuestionBankSlugById` below).
 *   - `src/services/profile.service.ts` counts/erases
 *     `user_question_answers` rows (profile completeness, account
 *     deletion) instead of `answers`.
 *   - `src/services/postDateFeedback.service.ts`'s matching-signal sweep
 *     joins `user_question_answers`/`question_bank` and scores divergence
 *     via `src/domain/questions/typeHandlers.ts#satisfaction` (generalizes
 *     to every question type, not just `scale`) instead of a raw 1-5
 *     numeric diff on the old bank.
 *   - `src/seed.ts` seeds ONLY the typed bank.
 *   - The old `putMyAnswers`/`adminListQuestions`/`adminCreateQuestion`/
 *     `adminUpdateQuestion` functions and their `questions`/`answers` row
 *     mappings are deleted outright, nothing in this codebase calls the
 *     old bank's read or write path anymore, and
 *     `db/migrations/022_drop_old_question_bank.sql` drops both tables.
 *     See that migration's header for the full retirement accounting.
 *
 * Invariants:
 *  - A question's PREFERENCE is always a VALUE + an IMPORTANCE, never a
 *    bare number pretending to be both (see src/domain/questions/types.ts).
 *  - Every question is skippable, and every question accepts an explicit
 *    `prefer_not_to_say` refusal, regardless of whether it's flagged
 *    `sensitive`, see `putMyQuestionAnswer`'s own doc.
 *  - `putMyQuestionAnswer` is the ONLY write path for a new-bank answer,
 *    and it is what drives BOTH side effects spec §25.4/the deal-breaker
 *    design require: refreshing this user's materialized compatibility
 *    scores (`compatibility.service#refreshScoresForUser`), and syncing
 *    this user's deal-breaker-derived hard filters
 *    (`filter.service#updateMyFilters`, via `getMyDealBreakerFilterRows`
 *    below), see `syncDealBreakerFilters`.
 *
 * SIGNATURE ADDITION (flagged per "Keep stub signatures; minimal changes
 * only, flagged loudly"): `resolveVisibleTagsFor` below is NOT one of the
 * six functions INTERFACES.md's module table lists for `question.service`.
 * It exists because the task brief assigns §8.4 (private/reciprocal
 * interest tags) to this file ("Implement the reciprocal disclosure as a
 * single function others must go through"), but no module in
 * INTERFACES.md's table owns `user_tags`/`interest_tags` CRUD or
 * visibility at all, and `discovery.service.ts`'s `DiscoveryCandidate`
 * type has a `sharedInterestTag` field that needs exactly this logic to
 * populate. `discovery.service.ts` (also owned by this agent) calls it,
 * that edge is not in INTERFACES.md's authoritative call-graph diagram
 * either. Both additions are confined to files this agent owns and change
 * no frozen signature; flagged in the handoff report as a coordination
 * point for whoever finalizes INTERFACES.md's graph (either add a
 * `discovery -> question` edge, or give tags their own module next time).
 */

// =====================================================================
// §8.4 private tags, reciprocal disclosure (see SIGNATURE ADDITION note
// at the top of this file).
// =====================================================================

export interface VisibleTag {
  tagId: string;
  name: string;
  category: string;
}

/**
 * The single function anything displaying `targetUserId`'s interest tags
 * to `viewerUserId` MUST go through (§8.4). Visibility rules per
 * `user_tags.visibility`:
 *   - `public`, always visible to anyone.
 *   - `private_reciprocal`, visible to `viewerUserId` only if `viewerUserId`
 *     also holds a `user_tags` row for that same tag (any visibility level
 *     of their own copy, reciprocity is about the shared fact of holding
 *     the tag, not about the viewer's own privacy choice for it).
 *   - `hidden`, never visible to anyone else.
 * `viewerUserId === targetUserId` is treated as the profile owner viewing
 * their own tags: everything is returned, including `hidden` ones.
 */
export async function resolveVisibleTagsFor(ctx: Ctx, viewerUserId: string, targetUserId: string): Promise<VisibleTag[]> {
  const { rows: targetRows } = await ctx.db.query<{
    tag_id: string;
    name: string;
    category: string;
    visibility: 'public' | 'private_reciprocal' | 'hidden';
  }>(
    `SELECT ut.tag_id, it.name, it.category, ut.visibility
     FROM user_tags ut
     JOIN interest_tags it ON it.id = ut.tag_id
     WHERE ut.user_id = $1
     ORDER BY it.name`,
    [targetUserId],
  );

  if (viewerUserId === targetUserId) {
    return targetRows.map((r) => ({ tagId: r.tag_id, name: r.name, category: r.category }));
  }

  const reciprocalTagIds = targetRows.some((r) => r.visibility === 'private_reciprocal')
    ? new Set(
        (
          await ctx.db.query<{ tag_id: string }>('SELECT tag_id FROM user_tags WHERE user_id = $1', [viewerUserId])
        ).rows.map((r) => r.tag_id),
      )
    : new Set<string>();

  return targetRows
    .filter((r) => {
      if (r.visibility === 'hidden') return false;
      if (r.visibility === 'private_reciprocal') return reciprocalTagIds.has(r.tag_id);
      return true; // public
    })
    .map((r) => ({ tagId: r.tag_id, name: r.name, category: r.category }));
}

// =====================================================================
// NEW QUESTION BANK (typed questions, value+importance preferences).
//
// Everything below this line is ADDITIVE, it does not change any
// function/type above. The old `questions`/`answers` tables and every
// function above keep working exactly as before for
// `compatibility.service.ts` / `filter.service.ts` /
// `behavioralPrompt.service.ts` (all off limits to this build; see
// db/migrations/008_questions.sql's migration-choice note for why this
// is a clean break rather than an in-place migration).
//
// New tables: `question_bank` (versioned, typed definitions),
// `user_question_answers` (value + importance, three non-answer states),
// `user_tag_intensity`, `user_avoid_tags`.
// =====================================================================

const NO_SECTION_MARK = /§/;

/** Every user-visible string in the new bank goes through this, see task brief "no question text, option label, or any other user-visible string may contain a section mark". */
function userFacingText(maxLen: number) {
  return z
    .string()
    .min(1)
    .max(maxLen)
    .refine((s) => !NO_SECTION_MARK.test(s), {
      message: 'Question and label text must not contain a section mark or refer to an internal document.',
    });
}

const choiceOptionInputSchema = z.object({
  key: z
    .string()
    .min(1)
    .max(64)
    .regex(/^[a-z0-9_]+$/, 'option key must be lowercase snake_case'),
  label: userFacingText(200),
});

// NOTE: `.refine()` on an individual member would wrap it in `ZodEffects`,
// which `z.discriminatedUnion` rejects (it requires every member to stay a
// plain `ZodObject` so it can read `.shape` for the discriminant), so the
// scale-specific "max > min" / "even span" checks are applied to the
// UNION as a whole below instead, gated on `d.type !== 'scale'`.
const scaleTypeDefSchema = z.object({
  type: z.literal('scale'),
  min: z.number().int(),
  max: z.number().int(),
  minLabel: userFacingText(100),
  maxLabel: userFacingText(100),
  midLabel: userFacingText(100),
});

const singleChoiceTypeDefSchema = z.object({
  type: z.literal('single_choice'),
  options: z.array(choiceOptionInputSchema).min(2),
});

const multiChoiceTypeDefSchema = z.object({
  type: z.literal('multi_choice'),
  options: z.array(choiceOptionInputSchema).min(2),
});

const frequencyTypeDefSchema = z.object({
  type: z.literal('frequency'),
  anchors: z.array(choiceOptionInputSchema).min(2),
});

const typeDefinitionSchema = z
  .discriminatedUnion('type', [scaleTypeDefSchema, singleChoiceTypeDefSchema, multiChoiceTypeDefSchema, frequencyTypeDefSchema])
  .refine((d) => d.type !== 'scale' || d.max > d.min, { message: 'scale: max must be greater than min' })
  .refine((d) => d.type !== 'scale' || (d.max - d.min) % 2 === 0, {
    message: 'scale: span (max - min) must be even so a midpoint exists',
  });

// ---- row <-> domain mapping --------------------------------------------

interface QuestionBankRow {
  id: string;
  slug: string;
  version: number;
  is_current: boolean;
  category: string;
  subcategory: string | null;
  tags: string[];
  question_type: QuestionType;
  question_text: string;
  type_definition: QuestionTypeDefinition;
  base_weight: number;
  sensitive: boolean;
  active: boolean;
  answer_rate_hint: number;
  created_at: Date;
  updated_at: Date;
}

function questionDefinitionFromRow(row: QuestionBankRow): QuestionDefinition {
  return {
    id: row.id,
    slug: row.slug,
    version: row.version,
    category: row.category,
    subcategory: row.subcategory,
    tags: row.tags,
    questionText: row.question_text,
    typeDef: row.type_definition,
    presentation: presentationFor(row.type_definition),
    baseWeight: row.base_weight,
    sensitive: row.sensitive,
    active: row.active,
    answerRateHint: row.answer_rate_hint,
  };
}

async function loadCurrentQuestionsBySlug(ctx: Ctx, slugs: string[]): Promise<Map<string, QuestionDefinition>> {
  if (slugs.length === 0) return new Map();
  const { rows } = await ctx.db.query<QuestionBankRow>(
    'SELECT * FROM question_bank WHERE slug = ANY($1::text[]) AND is_current = true',
    [slugs],
  );
  return new Map(rows.map((r) => [r.slug, questionDefinitionFromRow(r)]));
}

// =====================================================================
// Client-facing paged listing, "paging/lookup must not load the whole
// bank per request" (task brief). Cursor is the last-seen row id;
// O(log n) index lookup via idx_question_bank_paging / the primary key,
// not an offset scan, so page N costs the same as page 1 regardless of
// how deep into a 600+ row bank N is.
// =====================================================================

export interface QuestionBankPage {
  items: QuestionDefinition[];
  nextCursor: string | null;
}

const DEFAULT_PAGE_SIZE = 50;
const MAX_PAGE_SIZE = 200;

export async function listActiveQuestionBank(
  ctx: Ctx,
  opts?: { category?: string; cursor?: string | null; limit?: number },
): Promise<QuestionBankPage> {
  const limit = Math.min(Math.max(opts?.limit ?? DEFAULT_PAGE_SIZE, 1), MAX_PAGE_SIZE);
  const conditions = ['is_current = true', 'active = true'];
  const params: unknown[] = [];

  if (opts?.category) {
    params.push(opts.category);
    conditions.push(`category = $${params.length}`);
  }
  if (opts?.cursor) {
    params.push(opts.cursor);
    conditions.push(`id > $${params.length}`);
  }
  params.push(limit + 1);

  const { rows } = await ctx.db.query<QuestionBankRow>(
    `SELECT * FROM question_bank WHERE ${conditions.join(' AND ')} ORDER BY id LIMIT $${params.length}`,
    params,
  );

  const hasMore = rows.length > limit;
  const items = rows.slice(0, limit).map(questionDefinitionFromRow);
  return { items, nextCursor: hasMore ? items[items.length - 1]!.id : null };
}

export async function getCurrentQuestionBySlug(ctx: Ctx, slug: string): Promise<QuestionDefinition | null> {
  const found = await loadCurrentQuestionsBySlug(ctx, [slug]);
  return found.get(slug) ?? null;
}

/**
 * Resolves a `question_bank.id` (ANY version, not necessarily the current
 * one) back to its stable slug. For a caller that only ever stored a
 * `question_bank` id at some earlier point (e.g.
 * `behavioralPrompt.service.ts` pinning a suggestion to the version that
 * was current when the pattern was detected) and later needs to act on
 * "whatever is current for that question now", the normal
 * `getCurrentQuestionBySlug` lookup, keyed off the slug this returns.
 * Returns `null` if no `question_bank` row has ever had this id.
 */
export async function getQuestionBankSlugById(ctx: Ctx, id: string): Promise<string | null> {
  const { rows } = await ctx.db.query<{ slug: string }>('SELECT slug FROM question_bank WHERE id = $1', [id]);
  return rows[0]?.slug ?? null;
}

// =====================================================================
// Answers, value + importance, three non-answer states.
// =====================================================================

export interface QuestionAnswerRecord {
  userId: string;
  questionSlug: string;
  questionBankId: string;
  status: 'skipped' | 'prefer_not_to_say' | 'answered';
  selfValue: unknown | null;
  preferenceValue: unknown | null;
  importance: ImportanceLevel | null;
  answeredAt: Date;
  updatedAt: Date;
}

interface UserQuestionAnswerRow {
  user_id: string;
  question_slug: string;
  question_bank_id: string;
  status: 'skipped' | 'prefer_not_to_say' | 'answered';
  self_value: unknown | null;
  preference_value: unknown | null;
  importance: ImportanceLevel | null;
  answered_at: Date;
  updated_at: Date;
}

function answerRecordFromRow(row: UserQuestionAnswerRow): QuestionAnswerRecord {
  return {
    userId: row.user_id,
    questionSlug: row.question_slug,
    questionBankId: row.question_bank_id,
    status: row.status,
    selfValue: row.self_value,
    preferenceValue: row.preference_value,
    importance: row.importance,
    answeredAt: row.answered_at,
    updatedAt: row.updated_at,
  };
}

/** Converts a persisted answer record into the pure domain's `QuestionAnswerState` shape (src/domain/questions/types.ts), what `scoreQuestionContribution`/`evaluateDealBreakers`/the selector all consume. */
export function toAnswerState(record: Pick<QuestionAnswerRecord, 'status' | 'selfValue' | 'preferenceValue' | 'importance'>): QuestionAnswerState {
  return {
    status: record.status,
    selfValue: record.selfValue,
    preferenceValue: record.preferenceValue,
    importance: record.importance,
  };
}

export async function getMyQuestionAnswers(ctx: Ctx): Promise<QuestionAnswerRecord[]> {
  const { userId } = requireUserActor(ctx);
  const { rows } = await ctx.db.query<UserQuestionAnswerRow>('SELECT * FROM user_question_answers WHERE user_id = $1', [userId]);
  return rows.map(answerRecordFromRow);
}

/**
 * Every new-bank answer for one user, keyed by question slug, in the
 * pure domain's `QuestionAnswerState` shape. A slug with no row is
 * simply absent from the map, callers (the selector wrapper, a later
 * compatibility-scoring integration) treat an absent entry as
 * `unanswered`, matching `types.ts`'s "absence of a row IS the
 * unanswered state" convention.
 *
 * A later agent wiring `compatibility.service.ts` to
 * `src/domain/questions/scoring.ts` would call this for both users in a
 * pair, then `aggregateQuestionScores(questions, statesA, statesB)`.
 */
export async function getAnswerStatesForUser(ctx: Ctx, userId: string): Promise<Map<string, QuestionAnswerState>> {
  const { rows } = await ctx.db.query<UserQuestionAnswerRow>('SELECT * FROM user_question_answers WHERE user_id = $1', [userId]);
  const map = new Map<string, QuestionAnswerState>();
  for (const row of rows) map.set(row.question_slug, toAnswerState(answerRecordFromRow(row)));
  return map;
}

const nonAnsweredStatusSchema = z.enum(['skipped', 'prefer_not_to_say']);
const ladderPositionSchema = z.union([z.literal(0), z.literal(1), z.literal(2), z.literal(3), z.literal(4)]);

const putQuestionAnswerSchema = z.object({
  slug: z.string().min(1).max(100),
  status: z.enum(['answered', 'skipped', 'prefer_not_to_say']),
  selfValue: z.unknown().optional(),
  preferenceValue: z.unknown().optional(),
  importance: z.enum(IMPORTANCE_LEVELS).optional(),
  ladderPosition: ladderPositionSchema.optional(),
});

export type PutQuestionAnswerInput = z.infer<typeof putQuestionAnswerSchema>;

async function persistAnswer(
  ctx: Ctx,
  userId: string,
  question: QuestionDefinition,
  status: 'answered' | 'skipped' | 'prefer_not_to_say',
  selfValue: unknown | null,
  preferenceValue: unknown | null,
  importance: ImportanceLevel | null,
  now: Date,
): Promise<QuestionAnswerRecord> {
  const { rows } = await ctx.db.query<UserQuestionAnswerRow>(
    `INSERT INTO user_question_answers
       (user_id, question_slug, question_bank_id, status, self_value, preference_value, importance, answered_at, updated_at)
     VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7, $8, $8)
     ON CONFLICT (user_id, question_slug) DO UPDATE SET
       question_bank_id = EXCLUDED.question_bank_id,
       status = EXCLUDED.status,
       self_value = EXCLUDED.self_value,
       preference_value = EXCLUDED.preference_value,
       importance = EXCLUDED.importance,
       answered_at = EXCLUDED.answered_at,
       updated_at = EXCLUDED.updated_at
     RETURNING *`,
    [
      userId,
      question.slug,
      question.id,
      status,
      selfValue === null ? null : JSON.stringify(selfValue),
      preferenceValue === null ? null : JSON.stringify(preferenceValue),
      importance,
      now,
    ],
  );
  return answerRecordFromRow(rows[0]!);
}

/**
 * Records one answer to a new-bank question, `status: 'answered'`
 * requires `selfValue` plus EITHER (`preferenceValue` + `importance`) OR
 * `ladderPosition` (only accepted when the question's `presentation` is
 * `'ladder'`, see src/domain/questions/ladder.ts). `status: 'skipped'`
 * or `'prefer_not_to_say'` must not include any of those four fields,
 * "always skippable" carries no value/importance to reject or coerce.
 *
 * Every question is always skippable/refusable regardless of `sensitive`
 * there is no sensitive-questions-only gate on `prefer_not_to_say` here
 * (task brief: "This applies to ALL questions, not just ones flagged
 * sensitive").
 *
 * SIDE EFFECTS (both now wired, spec §25.4 "on major answer changes" and
 * the deal-breaker filter seam, previously left for "a later agent"; that
 * agent is this build):
 *   1. `compatibility.service#refreshScoresForUser`, recomputes this
 *      user's materialized compatibility scores against their bounded
 *      geographic/activity-window neighbor set (see that function's own
 *      doc). Mirrors exactly how the old `putMyAnswers` used to trigger
 *      this.
 *   2. `syncDealBreakerFilters` (below), re-derives this user's
 *      deal-breaker-implied hard filters via `getMyDealBreakerFilterRows`
 *      and persists them through `filter.service#updateMyFilters`,
 *      retracting (disabling, not deleting) any previously-derived `qb:*`
 *      filter that no longer corresponds to a current deal breaker (e.g.
 *      the user softened a deal breaker to "critical", or changed their
 *      answer entirely), see that function's own doc for exactly how the
 *      retraction diff works.
 * Both run unconditionally (every status, not just `'answered'`) because
 * EITHER side effect can matter no matter which direction an edit goes:
 * turning a deal breaker OFF (by skipping, refusing, or softening the
 * previous answer) must retract its filter just as reliably as turning one
 * ON must create it, and any answer change can shift a compatibility
 * score.
 */
export async function putMyQuestionAnswer(ctx: Ctx, input: PutQuestionAnswerInput): Promise<QuestionAnswerRecord> {
  const { userId } = requireUserActor(ctx);
  const parsed = putQuestionAnswerSchema.parse(input);

  const question = await getCurrentQuestionBySlug(ctx, parsed.slug);
  if (!question) throw new NotFoundError(`Unknown question "${parsed.slug}"`, { slug: parsed.slug });
  if (!question.active) throw new ValidationError(`Question "${parsed.slug}" is not active`, { slug: parsed.slug });

  const now = ctx.clock.now();

  let result: QuestionAnswerRecord;

  if (parsed.status !== 'answered') {
    nonAnsweredStatusSchema.parse(parsed.status);
    if (
      parsed.selfValue !== undefined ||
      parsed.preferenceValue !== undefined ||
      parsed.importance !== undefined ||
      parsed.ladderPosition !== undefined
    ) {
      throw new ValidationError(
        `A "${parsed.status}" response must not include a value, preference, importance, or ladder position`,
        { slug: parsed.slug },
      );
    }
    result = await persistAnswer(ctx, userId, question, parsed.status, null, null, null, now);
  } else {
    if (parsed.selfValue === undefined) {
      throw new ValidationError('selfValue is required for an "answered" response', { slug: parsed.slug });
    }

    let rawPreferenceValue: unknown;
    let importance: ImportanceLevel;

    if (parsed.ladderPosition !== undefined) {
      if (question.presentation !== 'ladder') {
        throw new ValidationError(`Question "${parsed.slug}" does not use the ladder presentation`, {
          slug: parsed.slug,
          presentation: question.presentation,
        });
      }
      if (parsed.preferenceValue !== undefined || parsed.importance !== undefined) {
        throw new ValidationError('Provide either ladderPosition or preferenceValue+importance, not both', { slug: parsed.slug });
      }
      const ladderResult = ladderPositionToPreference(
        question.typeDef as SingleChoiceDefinition,
        parsed.ladderPosition as LadderPosition,
      );
      rawPreferenceValue = ladderResult.preferenceValue;
      importance = ladderResult.importance;
    } else {
      if (parsed.preferenceValue === undefined || parsed.importance === undefined) {
        throw new ValidationError(
          'preferenceValue and importance are required for an "answered" response (or use ladderPosition on a ladder-presentation question)',
          { slug: parsed.slug },
        );
      }
      rawPreferenceValue = parsed.preferenceValue;
      importance = parsed.importance;
    }

    const handler = getTypeHandler(question.typeDef.type);
    const selfResult = handler.validateSelfValue(question.typeDef, parsed.selfValue);
    if (!selfResult.valid) {
      throw new ValidationError(`Invalid selfValue for "${parsed.slug}": ${selfResult.reason}`, { slug: parsed.slug });
    }
    const prefResult = handler.validatePreferenceValue(question.typeDef, rawPreferenceValue);
    if (!prefResult.valid) {
      throw new ValidationError(`Invalid preferenceValue for "${parsed.slug}": ${prefResult.reason}`, { slug: parsed.slug });
    }

    result = await persistAnswer(ctx, userId, question, 'answered', selfResult.value, prefResult.value, importance, now);
  }

  // spec §25.4 "on major answer changes", refresh this user's materialized
  // compatibility scores.
  await refreshScoresForUser(ctx, userId);
  // Deal-breaker filter seam (src/domain/questions/dealBreakers.ts's file
  // doc), keep `hard_filters` in sync with this user's CURRENT
  // deal-breaker answers, including retracting one that just stopped being
  // a deal breaker.
  await syncDealBreakerFilters(ctx);

  return result;
}

// =====================================================================
// "What should we ask next?", I/O wrapper around
// src/domain/questions/selector.ts#selectNextQuestions.
// =====================================================================

export interface NextQuestionsOptions {
  count?: number;
  skipCooldownDays?: number;
}

const DEFAULT_NEXT_QUESTIONS_COUNT = 10;
const MAX_NEXT_QUESTIONS_COUNT = 50;

/**
 * Loads the whole active current bank's selector-relevant columns
 * (see `SelectableQuestion`, never the heavier `type_definition` jsonb)
 * plus this one user's answer/skip history, and returns up to
 * `opts.count` full `QuestionDefinition`s (definitions ARE fetched in
 * full here, but only for the handful actually selected, see
 * selector.ts's COMPLEXITY note for why the bank-wide pass stays cheap).
 */
export async function selectNextQuestionsForMe(ctx: Ctx, opts?: NextQuestionsOptions): Promise<QuestionDefinition[]> {
  const { userId } = requireUserActor(ctx);
  const count = Math.min(Math.max(opts?.count ?? DEFAULT_NEXT_QUESTIONS_COUNT, 1), MAX_NEXT_QUESTIONS_COUNT);

  const { rows: bankRows } = await ctx.db.query<{
    id: string;
    slug: string;
    category: string;
    active: boolean;
    base_weight: number;
    answer_rate_hint: number;
  }>('SELECT id, slug, category, active, base_weight, answer_rate_hint FROM question_bank WHERE is_current = true AND active = true');

  const selectable: SelectableQuestion[] = bankRows.map((r) => ({
    id: r.id,
    slug: r.slug,
    category: r.category,
    active: r.active,
    baseWeight: r.base_weight,
    answerRateHint: r.answer_rate_hint,
  }));

  const { rows: historyRows } = await ctx.db.query<{
    question_slug: string;
    status: 'skipped' | 'prefer_not_to_say' | 'answered';
    updated_at: Date;
  }>('SELECT question_slug, status, updated_at FROM user_question_answers WHERE user_id = $1', [userId]);

  const history = new Map(historyRows.map((r) => [r.question_slug, { status: r.status, at: r.updated_at }]));

  const selected = selectNextQuestions({
    questions: selectable,
    history,
    now: ctx.clock.now(),
    count,
    skipCooldownDays: opts?.skipCooldownDays,
  });

  const definitions = await loadCurrentQuestionsBySlug(ctx, selected.map((s) => s.question.slug));
  return selected.map((s) => definitions.get(s.question.slug)).filter((d): d is QuestionDefinition => d !== undefined);
}

// =====================================================================
// Deal-breaker filter derivation, THE FILTER SEAM (see
// src/domain/questions/dealBreakers.ts's file doc for exactly what a
// later agent must call to persist these against filter.service.ts).
// =====================================================================

/**
 * Every hard-filter row this user's CURRENT `deal_breaker`-importance
 * answers imply, in `filter.service#UpdateFilterInput`'s exact shape
 * (plus `excludeIfUnset: true`, which that file's `UpdateFilterInput`
 * already accepts). Pure derivation lives in
 * `src/domain/questions/dealBreakers.ts#deriveDealBreakerFilterRows`;
 * this is just the I/O to load the inputs it needs. Does NOT call
 * `filter.service.ts` itself, see that module's file doc for exactly
 * what a later agent must call with this function's result.
 */
export async function getMyDealBreakerFilterRows(ctx: Ctx): Promise<DealBreakerFilterRow[]> {
  const { userId } = requireUserActor(ctx);
  const { rows } = await ctx.db.query<{
    question_slug: string;
    question_bank_id: string;
    importance: ImportanceLevel | null;
    preference_value: unknown;
  }>(
    `SELECT question_slug, question_bank_id, importance, preference_value
     FROM user_question_answers
     WHERE user_id = $1 AND importance = 'deal_breaker'`,
    [userId],
  );
  if (rows.length === 0) return [];

  const bankIds = [...new Set(rows.map((r) => r.question_bank_id))];
  const { rows: questionRows } = await ctx.db.query<QuestionBankRow>('SELECT * FROM question_bank WHERE id = ANY($1::uuid[])', [bankIds]);
  const questionsById = new Map(questionRows.map((r) => [r.id, questionDefinitionFromRow(r)]));

  const questions: QuestionDefinition[] = [];
  const answersBySlug = new Map<string, QuestionAnswerState>();
  for (const row of rows) {
    const question = questionsById.get(row.question_bank_id);
    if (!question) continue; // question_bank row somehow missing; skip rather than throw on a derived/best-effort read
    questions.push(question);
    answersBySlug.set(row.question_slug, {
      status: 'answered',
      selfValue: null, // unused by deal-breaker derivation (see dealBreakers.ts)
      preferenceValue: row.preference_value,
      importance: row.importance,
    });
  }

  return deriveDealBreakerFilterRows(questions, answersBySlug);
}

/**
 * Persists the caller's CURRENT deal-breaker-implied filters through
 * `filter.service#updateMyFilters`, and RETRACTS (disables, never
 * deletes, `updateMyFilters` only ever upserts) any previously-derived
 * `qb:*` filter that no longer corresponds to a current deal breaker.
 *
 * This is the "wiring agent" call `src/domain/questions/dealBreakers.ts`'s
 * file doc describes: `getMyDealBreakerFilterRows` derives what SHOULD be
 * enabled right now; every OTHER `qb:`-prefixed row already sitting in
 * `hard_filters` for this user is, by construction, only ever written by
 * this same function (the `qb:` namespace exists specifically so nothing
 * else writes it, see dealBreakers.ts's FILTER-KEY NAMESPACE note), so
 * any such row not in the current derived set is stale and gets
 * `enabled: false` here rather than being left in place, a stale
 * deal-breaker filter that used to be "critical" and is now merely
 * "important" must stop excluding candidates, not keep doing so silently.
 * A user's non-`qb:` filters (age, distance, gender, ...) are never
 * touched by this function.
 *
 * A no-op (no `updateMyFilters` call at all) when there is nothing to
 * enable and nothing to retract, so calling this on every answer change,
 * even one with no deal-breaker involvement at all, costs one extra read
 * and no write in the common case.
 */
async function syncDealBreakerFilters(ctx: Ctx): Promise<void> {
  const [currentRows, existingFilters] = await Promise.all([getMyDealBreakerFilterRows(ctx), getMyFilters(ctx)]);

  const currentKeys = new Set(currentRows.map((r) => r.filterKey));
  const staleQbFilters = existingFilters.filter(
    (f) => f.filterKey.startsWith('qb:') && f.enabled && !currentKeys.has(f.filterKey),
  );

  if (currentRows.length === 0 && staleQbFilters.length === 0) return;

  const updates: UpdateFilterInput[] = [
    ...currentRows.map((r) => ({
      filterKey: r.filterKey,
      operator: r.operator,
      value: r.value,
      enabled: true,
      excludeIfUnset: r.excludeIfUnset,
    })),
    // Retraction: same operator/value (irrelevant once disabled), enabled: false.
    ...staleQbFilters.map((f) => ({
      filterKey: f.filterKey,
      operator: f.operator,
      value: f.value,
      enabled: false,
      excludeIfUnset: f.excludeIfUnset,
    })),
  ];

  await updateMyFilters(ctx, updates);
}

// =====================================================================
// Tag intensity + avoidance, see src/domain/questions/tags.ts for the
// pure math and exactly what a later agent must call from
// discovery.service.ts to enforce/use these.
// =====================================================================

export interface TagIntensityRecord {
  userId: string;
  tagId: string;
  intensity: TagIntensity;
  updatedAt: Date;
}

interface TagIntensityRow {
  user_id: string;
  tag_id: string;
  intensity: TagIntensity;
  updated_at: Date;
}

function tagIntensityFromRow(row: TagIntensityRow): TagIntensityRecord {
  return { userId: row.user_id, tagId: row.tag_id, intensity: row.intensity, updatedAt: row.updated_at };
}

const tagIdSchema = z.string().uuid();
const tagIntensitySchema = z.enum(TAG_INTENSITY_LEVELS);

export async function setMyTagIntensity(ctx: Ctx, tagId: string, intensity: TagIntensity): Promise<TagIntensityRecord> {
  const { userId } = requireUserActor(ctx);
  const parsedTagId = tagIdSchema.parse(tagId);
  const parsedIntensity = tagIntensitySchema.parse(intensity);

  const { rows: tagRows } = await ctx.db.query('SELECT id FROM interest_tags WHERE id = $1', [parsedTagId]);
  if (tagRows.length === 0) throw new NotFoundError(`Unknown interest tag "${parsedTagId}"`, { tagId: parsedTagId });

  const now = ctx.clock.now();
  const { rows } = await ctx.db.query<TagIntensityRow>(
    `INSERT INTO user_tag_intensity (user_id, tag_id, intensity, updated_at)
     VALUES ($1, $2, $3, $4)
     ON CONFLICT (user_id, tag_id) DO UPDATE SET intensity = EXCLUDED.intensity, updated_at = EXCLUDED.updated_at
     RETURNING *`,
    [userId, parsedTagId, parsedIntensity, now],
  );
  return tagIntensityFromRow(rows[0]!);
}

export async function getMyTagIntensities(ctx: Ctx): Promise<TagIntensityRecord[]> {
  const { userId } = requireUserActor(ctx);
  const { rows } = await ctx.db.query<TagIntensityRow>('SELECT * FROM user_tag_intensity WHERE user_id = $1', [userId]);
  return rows.map(tagIntensityFromRow);
}

/** Full-replace semantics (same shape as `filter.service#updateMyFilters`'s upsert-the-whole-set pattern): after this call, the caller's avoid list is exactly `tagIds`. */
export async function setMyAvoidTags(ctx: Ctx, tagIds: string[]): Promise<string[]> {
  const { userId } = requireUserActor(ctx);
  const parsed = z.array(tagIdSchema).parse(tagIds);

  if (parsed.length > 0) {
    const { rows: tagRows } = await ctx.db.query<{ id: string }>('SELECT id FROM interest_tags WHERE id = ANY($1::uuid[])', [parsed]);
    const found = new Set(tagRows.map((r) => r.id));
    const missing = parsed.filter((id) => !found.has(id));
    if (missing.length > 0) throw new NotFoundError(`Unknown interest tag(s): ${missing.join(', ')}`, { tagIds: missing });
  }

  await ctx.db.query('DELETE FROM user_avoid_tags WHERE user_id = $1', [userId]);
  for (const tagId of parsed) {
    await ctx.db.query('INSERT INTO user_avoid_tags (user_id, tag_id) VALUES ($1, $2) ON CONFLICT (user_id, tag_id) DO NOTHING', [userId, tagId]);
  }
  return parsed;
}

export async function getMyAvoidTagIds(ctx: Ctx): Promise<string[]> {
  const { userId } = requireUserActor(ctx);
  const { rows } = await ctx.db.query<{ tag_id: string }>('SELECT tag_id FROM user_avoid_tags WHERE user_id = $1', [userId]);
  return rows.map((r) => r.tag_id);
}

/**
 * I/O wrapper around `src/domain/questions/tags.ts#passesAvoidTagFilter`
 * for one candidate pair. See that function's doc for exactly where a
 * later agent should call this from `discovery.service.ts` (the same
 * gating point as `filter.service#passesMutualFilters`, before scoring,
 * never as a post-hoc filter over an already-sorted/scored list).
 */
export async function passesAvoidTagFilterFor(ctx: Ctx, userId: string, otherUserId: string): Promise<{ passes: boolean; violatingTagIds: string[] }> {
  const [userTags, otherTags, userAvoid, otherAvoid] = await Promise.all([
    ctx.db.query<{ tag_id: string }>('SELECT tag_id FROM user_tags WHERE user_id = $1', [userId]),
    ctx.db.query<{ tag_id: string }>('SELECT tag_id FROM user_tags WHERE user_id = $1', [otherUserId]),
    ctx.db.query<{ tag_id: string }>('SELECT tag_id FROM user_avoid_tags WHERE user_id = $1', [userId]),
    ctx.db.query<{ tag_id: string }>('SELECT tag_id FROM user_avoid_tags WHERE user_id = $1', [otherUserId]),
  ]);
  return passesAvoidTagFilter(
    new Set(userTags.rows.map((r) => r.tag_id)),
    new Set(userAvoid.rows.map((r) => r.tag_id)),
    new Set(otherTags.rows.map((r) => r.tag_id)),
    new Set(otherAvoid.rows.map((r) => r.tag_id)),
  );
}

// =====================================================================
// Admin bank management, versioned create/update. Editing NEVER mutates
// a `question_bank` row in place; it inserts a new version and flips
// `is_current` (see db/migrations/008_questions.sql) so answers already
// pinned to the old version keep their original meaning.
// =====================================================================

export interface CreateQuestionBankInput {
  slug: string;
  category: string;
  subcategory?: string | null;
  tags?: string[];
  questionText: string;
  typeDef: QuestionTypeDefinition;
  baseWeight?: number;
  sensitive?: boolean;
  answerRateHint?: number;
}

const createQuestionBankSchema = z.object({
  slug: z
    .string()
    .min(1)
    .max(100)
    .regex(/^[a-z0-9_]+$/, 'slug must be lowercase snake_case'),
  category: z.string().min(1).max(100),
  subcategory: z.string().min(1).max(100).nullable().optional(),
  tags: z.array(z.string().min(1).max(50)).max(20).optional(),
  questionText: userFacingText(500),
  typeDef: typeDefinitionSchema,
  baseWeight: z.number().min(0).optional(),
  sensitive: z.boolean().optional(),
  answerRateHint: z.number().min(0).max(1).optional(),
});

export type UpdateQuestionBankInput = Partial<Omit<CreateQuestionBankInput, 'slug'>> & { active?: boolean };

const updateQuestionBankSchema = createQuestionBankSchema.omit({ slug: true }).partial().extend({ active: z.boolean().optional() });

function requireQuestionBankAdmin(ctx: Ctx): void {
  if (ctx.actor.type !== 'admin') {
    throw new ValidationError('Only admins may manage the question bank', { actorType: ctx.actor.type });
  }
}

export async function adminListQuestionBank(ctx: Ctx, opts?: { includeInactive?: boolean }): Promise<QuestionDefinition[]> {
  requireQuestionBankAdmin(ctx);
  const conditions = ['is_current = true'];
  if (!opts?.includeInactive) conditions.push('active = true');
  const { rows } = await ctx.db.query<QuestionBankRow>(
    `SELECT * FROM question_bank WHERE ${conditions.join(' AND ')} ORDER BY category, slug`,
  );
  return rows.map(questionDefinitionFromRow);
}

export async function adminCreateQuestionBankEntry(ctx: Ctx, input: CreateQuestionBankInput): Promise<QuestionDefinition> {
  requireQuestionBankAdmin(ctx);
  const parsed = createQuestionBankSchema.parse(input);

  const { rows: existing } = await ctx.db.query('SELECT 1 FROM question_bank WHERE slug = $1', [parsed.slug]);
  if (existing.length > 0) {
    throw new ConflictError(`Question slug "${parsed.slug}" already exists`, { slug: parsed.slug });
  }

  const now = ctx.clock.now();
  const { rows } = await ctx.db.query<QuestionBankRow>(
    `INSERT INTO question_bank
       (slug, version, is_current, category, subcategory, tags, question_type, question_text, type_definition, base_weight, sensitive, active, answer_rate_hint, created_at, updated_at)
     VALUES ($1, 1, true, $2, $3, $4, $5, $6, $7::jsonb, $8, $9, true, $10, $11, $11)
     RETURNING *`,
    [
      parsed.slug,
      parsed.category,
      parsed.subcategory ?? null,
      parsed.tags ?? [],
      parsed.typeDef.type,
      parsed.questionText,
      JSON.stringify(parsed.typeDef),
      parsed.baseWeight ?? 1.0,
      parsed.sensitive ?? false,
      parsed.answerRateHint ?? 0.5,
      now,
    ],
  );
  return questionDefinitionFromRow(rows[0]!);
}

/**
 * Creates a new version of `slug`, flips the previous version's
 * `is_current` to false, and returns the new current definition. This is
 * two sequential statements, not one atomic transaction (matching the
 * rest of this file's, and the codebase's, established pattern of not
 * wrapping every multi-statement service write in `withTransaction`; see
 * `src/db/tx.ts`). Acceptable here because this is an admin-only, rare,
 * append-mostly operation: the narrow failure window between the two
 * statements leaves at worst a slug with zero current rows, which the
 * next read/selector pass simply treats as "question not found" rather
 * than corrupting any existing answer (every existing answer's
 * `question_bank_id` FK is unaffected either way).
 */
export async function adminUpdateQuestionBankEntry(ctx: Ctx, slug: string, patch: UpdateQuestionBankInput): Promise<QuestionDefinition> {
  requireQuestionBankAdmin(ctx);
  const parsed = updateQuestionBankSchema.parse(patch);

  const { rows: currentRows } = await ctx.db.query<QuestionBankRow>('SELECT * FROM question_bank WHERE slug = $1 AND is_current = true', [slug]);
  const current = currentRows[0];
  if (!current) throw new NotFoundError(`Question "${slug}" not found`, { slug });

  const merged = {
    category: parsed.category ?? current.category,
    subcategory: parsed.subcategory !== undefined ? parsed.subcategory : current.subcategory,
    tags: parsed.tags ?? current.tags,
    questionText: parsed.questionText ?? current.question_text,
    typeDef: parsed.typeDef ?? current.type_definition,
    baseWeight: parsed.baseWeight ?? current.base_weight,
    sensitive: parsed.sensitive ?? current.sensitive,
    active: parsed.active ?? current.active,
    answerRateHint: parsed.answerRateHint ?? current.answer_rate_hint,
  };

  const now = ctx.clock.now();
  await ctx.db.query('UPDATE question_bank SET is_current = false, updated_at = $2 WHERE id = $1', [current.id, now]);

  const { rows } = await ctx.db.query<QuestionBankRow>(
    `INSERT INTO question_bank
       (slug, version, is_current, category, subcategory, tags, question_type, question_text, type_definition, base_weight, sensitive, active, answer_rate_hint, created_at, updated_at)
     VALUES ($1, $2, true, $3, $4, $5, $6, $7, $8::jsonb, $9, $10, $11, $12, $13, $13)
     RETURNING *`,
    [
      slug,
      current.version + 1,
      merged.category,
      merged.subcategory,
      merged.tags,
      merged.typeDef.type,
      merged.questionText,
      JSON.stringify(merged.typeDef),
      merged.baseWeight,
      merged.sensitive,
      merged.active,
      merged.answerRateHint,
      now,
    ],
  );
  return questionDefinitionFromRow(rows[0]!);
}

