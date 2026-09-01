/**
 * src/http/serializers/questions.ts, the typed question bank's wire
 * shapes.
 *
 * Explicit allowlist (same discipline as src/http/serializers/discovery.ts):
 * a client sees exactly what it needs to render and answer a question, and
 * nothing product/selector-internal. In particular `baseWeight` (the raw
 * scoring weight, spec-internal tuning, not something a client should
 * infer meaning from, e.g. "this question is worth more so answer
 * carefully") and `answerRateHint` (a selector-internal analytics signal)
 * are deliberately NEVER included below.
 *
 * `presentation` IS always included, every question tells the client
 * which control to render (`ladder` vs `value_importance`); a client must
 * never infer this itself from `type`/option count (see
 * src/domain/questions/types.ts `QuestionPresentation`'s own doc).
 */
import type { QuestionAnswerRecord } from '../../services/question.service.js';
import type { QuestionBankPage } from '../../services/question.service.js';
import type { QuestionDefinition } from '../../domain/questions/index.js';

export interface QuestionCardView {
  id: string;
  slug: string;
  version: number;
  category: string;
  subcategory: string | null;
  tags: string[];
  questionText: string;
  typeDef: QuestionDefinition['typeDef'];
  /** See module doc, the single source of truth for which control to render. */
  presentation: QuestionDefinition['presentation'];
  sensitive: boolean;
}

export function serializeQuestionCard(q: QuestionDefinition): QuestionCardView {
  return {
    id: q.id,
    slug: q.slug,
    version: q.version,
    category: q.category,
    subcategory: q.subcategory,
    tags: q.tags,
    questionText: q.questionText,
    typeDef: q.typeDef,
    presentation: q.presentation,
    sensitive: q.sensitive,
    // Deliberately NOT included: baseWeight, answerRateHint, active (see
    // module doc), internal scoring/selector signals a client never
    // needs and must never be seen inferring meaning from.
  };
}

export interface QuestionBankPageView {
  items: QuestionCardView[];
  nextCursor: string | null;
}

export function serializeQuestionBankPage(page: QuestionBankPage): QuestionBankPageView {
  return { items: page.items.map(serializeQuestionCard), nextCursor: page.nextCursor };
}

// =====================================================================
// Admin question-manager view (§27 item 3), repointed to the ONE typed
// question bank per the question-system cutover (see
// src/services/question.service.ts's file-level CUTOVER doc). Unlike
// `QuestionCardView` (the end-user-facing card, which deliberately
// withholds `baseWeight`/`answerRateHint`/`active`), an admin managing the
// bank needs the FULL definition, including versioning, active state,
// and the scoring-tuning fields end users never see, so this is a
// separate, deliberately wider, allowlist rather than reusing
// `QuestionCardView`.
// =====================================================================

export interface AdminQuestionView {
  id: string;
  slug: string;
  version: number;
  category: string;
  subcategory: string | null;
  tags: string[];
  questionText: string;
  typeDef: QuestionDefinition['typeDef'];
  presentation: QuestionDefinition['presentation'];
  baseWeight: number;
  sensitive: boolean;
  active: boolean;
  answerRateHint: number;
}

export function serializeAdminQuestion(q: QuestionDefinition): AdminQuestionView {
  return {
    id: q.id,
    slug: q.slug,
    version: q.version,
    category: q.category,
    subcategory: q.subcategory,
    tags: q.tags,
    questionText: q.questionText,
    typeDef: q.typeDef,
    presentation: q.presentation,
    baseWeight: q.baseWeight,
    sensitive: q.sensitive,
    active: q.active,
    answerRateHint: q.answerRateHint,
  };
}

export interface MyAnswerView {
  questionSlug: string;
  status: QuestionAnswerRecord['status'];
  selfValue: unknown | null;
  preferenceValue: unknown | null;
  importance: QuestionAnswerRecord['importance'];
  answeredAt: Date;
  updatedAt: Date;
}

/** The caller's own answer, `questionBankId` (an internal pin, not meaningful to a client) is deliberately dropped; everything else is the user's own data. */
export function serializeMyAnswer(record: QuestionAnswerRecord): MyAnswerView {
  return {
    questionSlug: record.questionSlug,
    status: record.status,
    selfValue: record.selfValue,
    preferenceValue: record.preferenceValue,
    importance: record.importance,
    answeredAt: record.answeredAt,
    updatedAt: record.updatedAt,
  };
}
