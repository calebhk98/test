import { z } from 'zod';
import type { Ctx } from '../lib/ctx.js';
import { requireUserActor } from '../lib/ctx.js';
import { ConflictError, NotFoundError, ValidationError } from '../lib/errors.js';
import type { Answer, AnswerValue, Question, QuestionPolarity } from '../domain/types.js';
import { refreshScoresForUser } from './compatibility.service.js';
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
  AnswerStatus,
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
 * populate. `discovery.service.ts` (also owned by this agent) calls it —
 * that edge is not in INTERFACES.md's authoritative call-graph diagram
 * either. Both additions are confined to files this agent owns and change
 * no frozen signature; flagged in the handoff report as a coordination
 * point for whoever finalizes INTERFACES.md's graph (either add a
 * `discovery -> question` edge, or give tags their own module next time).
 */

// =====================================================================
// Row <-> domain mapping
// =====================================================================

interface QuestionRow {
  id: string;
  slug: string;
  category: string;
  question_text: string;
  self_left_label: string;
  self_right_label: string;
  partner_left_label: string;
  partner_right_label: string;
  weight: number;
  polarity: QuestionPolarity;
  sensitive: boolean;
  active: boolean;
  created_at: Date;
  updated_at: Date;
}

function questionFromRow(row: QuestionRow): Question {
  return {
    id: row.id,
    slug: row.slug,
    category: row.category,
    questionText: row.question_text,
    selfLeftLabel: row.self_left_label,
    selfRightLabel: row.self_right_label,
    partnerLeftLabel: row.partner_left_label,
    partnerRightLabel: row.partner_right_label,
    weight: row.weight,
    polarity: row.polarity,
    sensitive: row.sensitive,
    active: row.active,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
  };
}

interface AnswerRow {
  user_id: string;
  question_id: string;
  self_value: AnswerValue;
  partner_value: AnswerValue;
  updated_at: Date;
}

function answerFromRow(row: AnswerRow): Answer {
  return {
    userId: row.user_id,
    questionId: row.question_id,
    selfValue: row.self_value,
    partnerValue: row.partner_value,
    updatedAt: row.updated_at,
  };
}

export async function listActiveQuestions(ctx: Ctx): Promise<Question[]> {
  const { rows } = await ctx.db.query<QuestionRow>(
    'SELECT * FROM questions WHERE active = true ORDER BY category, question_text',
  );
  return rows.map(questionFromRow);
}

export async function getMyAnswers(ctx: Ctx): Promise<Answer[]> {
  const { userId } = requireUserActor(ctx);
  const { rows } = await ctx.db.query<AnswerRow>('SELECT * FROM answers WHERE user_id = $1', [userId]);
  return rows.map(answerFromRow);
}

export interface AnswerInput {
  questionId: string;
  selfValue: AnswerValue;
  partnerValue: AnswerValue;
}

// §8.1: every question MUST have two answers, both on the 5-point scale.
// §8.5: "prefer not to say" (null) is allowed only for questions the bank
// marks `sensitive` — non-sensitive questions must be answered on 1-5 for
// BOTH sides, so "only one side answered" (or both left as prefer-not-to-say
// on a non-sensitive question) is rejected below the shape-level zod check.
const answerValueSchema = z.union([
  z.literal(1),
  z.literal(2),
  z.literal(3),
  z.literal(4),
  z.literal(5),
  z.null(),
]);

const answerInputSchema = z.object({
  questionId: z.string().uuid(),
  // Both keys are required (not `.optional()`) so a payload supplying only
  // one side of the pair fails validation before it ever reaches the DB —
  // this is the "reject any answer that supplies only one side" rule.
  selfValue: answerValueSchema,
  partnerValue: answerValueSchema,
});

const putMyAnswersSchema = z.array(answerInputSchema).min(1);

/** Upserts one or more answers for the caller. Triggers `compatibility.service.ts#refreshScoresForUser` as a side effect (spec §25.4 "on major answer changes"). */
export async function putMyAnswers(ctx: Ctx, answers: AnswerInput[]): Promise<Answer[]> {
  const { userId } = requireUserActor(ctx);
  const parsed = putMyAnswersSchema.parse(answers);

  const questionIds = parsed.map((a) => a.questionId);
  const { rows: questionRows } = await ctx.db.query<Pick<QuestionRow, 'id' | 'sensitive' | 'active'>>(
    'SELECT id, sensitive, active FROM questions WHERE id = ANY($1::uuid[])',
    [questionIds],
  );
  const questionsById = new Map(questionRows.map((q) => [q.id, q]));

  for (const input of parsed) {
    const question = questionsById.get(input.questionId);
    if (!question) {
      throw new NotFoundError(`Unknown question id "${input.questionId}"`, { questionId: input.questionId });
    }
    if (!question.active) {
      throw new ValidationError(`Question "${input.questionId}" is not active`, { questionId: input.questionId });
    }
    if (!question.sensitive && (input.selfValue === null || input.partnerValue === null)) {
      throw new ValidationError(
        '"Prefer not to say" is only available on sensitive questions (§8.5); both self and partner answers are required here.',
        { questionId: input.questionId },
      );
    }
  }

  const results: Answer[] = [];
  for (const input of parsed) {
    const { rows } = await ctx.db.query<AnswerRow>(
      `INSERT INTO answers (user_id, question_id, self_value, partner_value, updated_at)
       VALUES ($1, $2, $3, $4, $5)
       ON CONFLICT (user_id, question_id) DO UPDATE SET
         self_value = EXCLUDED.self_value,
         partner_value = EXCLUDED.partner_value,
         updated_at = EXCLUDED.updated_at
       RETURNING *`,
      [userId, input.questionId, input.selfValue, input.partnerValue, ctx.clock.now()],
    );
    results.push(answerFromRow(rows[0]!));
  }

  // spec §25.4 "on major answer changes" — refresh this user's materialized
  // compatibility scores. `question -> compatibility` is a sanctioned edge
  // (INTERFACES.md call graph).
  await refreshScoresForUser(ctx, userId);

  return results;
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

const createQuestionSchema = z.object({
  slug: z.string().min(1).max(100),
  category: z.string().min(1).max(100),
  questionText: z.string().min(1),
  selfLeftLabel: z.string().min(1),
  selfRightLabel: z.string().min(1),
  partnerLeftLabel: z.string().min(1),
  partnerRightLabel: z.string().min(1),
  weight: z.number().min(0),
  polarity: z.enum(['standard', 'reversed']),
  sensitive: z.boolean(),
});

function requireAdmin(ctx: Ctx): void {
  if (ctx.actor.type !== 'admin') {
    throw new ValidationError('Only admins may manage the question bank', { actorType: ctx.actor.type });
  }
}

export async function adminListQuestions(ctx: Ctx): Promise<Question[]> {
  requireAdmin(ctx);
  const { rows } = await ctx.db.query<QuestionRow>('SELECT * FROM questions ORDER BY category, question_text');
  return rows.map(questionFromRow);
}

export async function adminCreateQuestion(ctx: Ctx, input: CreateQuestionInput): Promise<Question> {
  requireAdmin(ctx);
  const parsed = createQuestionSchema.parse(input);

  const { rows } = await ctx.db.query<QuestionRow>(
    `INSERT INTO questions
       (slug, category, question_text, self_left_label, self_right_label, partner_left_label, partner_right_label, weight, polarity, sensitive, active, created_at, updated_at)
     VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,true,$11,$11)
     RETURNING *`,
    [
      parsed.slug,
      parsed.category,
      parsed.questionText,
      parsed.selfLeftLabel,
      parsed.selfRightLabel,
      parsed.partnerLeftLabel,
      parsed.partnerRightLabel,
      parsed.weight,
      parsed.polarity,
      parsed.sensitive,
      ctx.clock.now(),
    ],
  );
  return questionFromRow(rows[0]!);
}

const updateQuestionSchema = createQuestionSchema.partial().extend({ active: z.boolean().optional() });

export async function adminUpdateQuestion(
  ctx: Ctx,
  questionId: string,
  patch: Partial<CreateQuestionInput> & { active?: boolean },
): Promise<Question> {
  requireAdmin(ctx);
  const parsed = updateQuestionSchema.parse(patch);

  const { rows: existingRows } = await ctx.db.query<QuestionRow>('SELECT * FROM questions WHERE id = $1', [questionId]);
  const existing = existingRows[0];
  if (!existing) {
    throw new NotFoundError(`Question "${questionId}" not found`, { questionId });
  }

  const merged = {
    slug: parsed.slug ?? existing.slug,
    category: parsed.category ?? existing.category,
    question_text: parsed.questionText ?? existing.question_text,
    self_left_label: parsed.selfLeftLabel ?? existing.self_left_label,
    self_right_label: parsed.selfRightLabel ?? existing.self_right_label,
    partner_left_label: parsed.partnerLeftLabel ?? existing.partner_left_label,
    partner_right_label: parsed.partnerRightLabel ?? existing.partner_right_label,
    weight: parsed.weight ?? existing.weight,
    polarity: parsed.polarity ?? existing.polarity,
    sensitive: parsed.sensitive ?? existing.sensitive,
    active: parsed.active ?? existing.active,
  };

  const { rows } = await ctx.db.query<QuestionRow>(
    `UPDATE questions SET
       slug = $2, category = $3, question_text = $4, self_left_label = $5, self_right_label = $6,
       partner_left_label = $7, partner_right_label = $8, weight = $9, polarity = $10, sensitive = $11,
       active = $12, updated_at = $13
     WHERE id = $1
     RETURNING *`,
    [
      questionId,
      merged.slug,
      merged.category,
      merged.question_text,
      merged.self_left_label,
      merged.self_right_label,
      merged.partner_left_label,
      merged.partner_right_label,
      merged.weight,
      merged.polarity,
      merged.sensitive,
      merged.active,
      ctx.clock.now(),
    ],
  );
  return questionFromRow(rows[0]!);
}

// =====================================================================
// §8.4 private tags — reciprocal disclosure (see SIGNATURE ADDITION note
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
 *   - `public` — always visible to anyone.
 *   - `private_reciprocal` — visible to `viewerUserId` only if `viewerUserId`
 *     also holds a `user_tags` row for that same tag (any visibility level
 *     of their own copy — reciprocity is about the shared fact of holding
 *     the tag, not about the viewer's own privacy choice for it).
 *   - `hidden` — never visible to anyone else.
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
// Everything below this line is ADDITIVE — it does not change any
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

/** Every user-visible string in the new bank goes through this — see task brief "no question text, option label, or any other user-visible string may contain a section mark". */
function userFacingText(maxLen: number) {
  return z
    .string()
    .min(1)
    .max(maxLen)
    .refine((s) => !NO_SECTION_MARK.test(s), {
      message: 'user-facing text must not contain a section mark (§) or reference a spec document',
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
// plain `ZodObject` so it can read `.shape` for the discriminant) — so the
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
// Client-facing paged listing — "paging/lookup must not load the whole
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

// =====================================================================
// Answers — value + importance, three non-answer states.
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

/** Converts a persisted answer record into the pure domain's `QuestionAnswerState` shape (src/domain/questions/types.ts) — what `scoreQuestionContribution`/`evaluateDealBreakers`/the selector all consume. */
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
 * simply absent from the map — callers (the selector wrapper, a later
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
 * Records one answer to a new-bank question — `status: 'answered'`
 * requires `selfValue` plus EITHER (`preferenceValue` + `importance`) OR
 * `ladderPosition` (only accepted when the question's `presentation` is
 * `'ladder'` — see src/domain/questions/ladder.ts). `status: 'skipped'`
 * or `'prefer_not_to_say'` must not include any of those four fields —
 * "always skippable" carries no value/importance to reject or coerce.
 *
 * Every question is always skippable/refusable regardless of `sensitive`
 * — unlike the OLD `putMyAnswers` above, there is no
 * sensitive-questions-only gate on `prefer_not_to_say` here (task brief:
 * "This applies to ALL questions, not just ones flagged sensitive").
 *
 * Does NOT call `compatibility.service#refreshScoresForUser` — that
 * service does not yet read the new tables (see the integration-seam doc
 * on `src/domain/questions/scoring.ts`); wiring that refresh in is a
 * later agent's job once compatibility.service.ts is updated to consume
 * the new bank. Also does not itself persist any deal-breaker hard
 * filter — see `getMyDealBreakerFilterRows` below for that seam.
 */
export async function putMyQuestionAnswer(ctx: Ctx, input: PutQuestionAnswerInput): Promise<QuestionAnswerRecord> {
  const { userId } = requireUserActor(ctx);
  const parsed = putQuestionAnswerSchema.parse(input);

  const question = await getCurrentQuestionBySlug(ctx, parsed.slug);
  if (!question) throw new NotFoundError(`Unknown question "${parsed.slug}"`, { slug: parsed.slug });
  if (!question.active) throw new ValidationError(`Question "${parsed.slug}" is not active`, { slug: parsed.slug });

  const now = ctx.clock.now();

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
    return persistAnswer(ctx, userId, question, parsed.status, null, null, null, now);
  }

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

  return persistAnswer(ctx, userId, question, 'answered', selfResult.value, prefResult.value, importance, now);
}

// =====================================================================
// "What should we ask next?" — I/O wrapper around
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
 * (see `SelectableQuestion` — never the heavier `type_definition` jsonb)
 * plus this one user's answer/skip history, and returns up to
 * `opts.count` full `QuestionDefinition`s (definitions ARE fetched in
 * full here, but only for the handful actually selected — see
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
// Deal-breaker filter derivation — THE FILTER SEAM (see
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
 * `filter.service.ts` itself — see that module's file doc for exactly
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

// =====================================================================
// Tag intensity + avoidance — see src/domain/questions/tags.ts for the
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
 * gating point as `filter.service#passesMutualFilters`, before scoring —
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
// Admin bank management — versioned create/update. Editing NEVER mutates
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
 * rest of this file's — and the codebase's — established pattern of not
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

