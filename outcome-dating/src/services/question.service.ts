import { z } from 'zod';
import type { Ctx } from '../lib/ctx.js';
import { requireUserActor } from '../lib/ctx.js';
import { NotFoundError, ValidationError } from '../lib/errors.js';
import type { Answer, AnswerValue, Question, QuestionPolarity } from '../domain/types.js';
import { refreshScoresForUser } from './compatibility.service.js';

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
