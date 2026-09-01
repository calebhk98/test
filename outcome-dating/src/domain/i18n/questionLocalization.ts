/**
 * src/domain/i18n/questionLocalization.ts — attaches locale-keyed text to
 * the NEW typed question bank (db/migrations/008_questions.sql's
 * `question_bank` table) WITHOUT editing that table, `question.service.ts`,
 * or anything under `src/domain/questions/**` — all three are another
 * agent's active, in-flight cutover (see the task brief: "another agent
 * is actively cutting the question system over to a new typed bank right
 * now"). Everything here is purely additive: one new table
 * (`question_bank_translations`, this build's own
 * `db/migrations/021_retention_i18n.sql`) FK'd to `question_bank(id)`, and
 * pure functions that take a `QuestionDefinition` (read-only import of
 * `src/domain/questions/types.js` — a type-only dependency, not a code
 * dependency on that module's behavior) and return a localized copy.
 *
 * WHY KEYED BY `question_bank_id` (the immutable per-VERSION row id) AND
 * NOT `slug`: `question_bank`'s own module doc explains "answer-version
 * pinning" — editing a question inserts a NEW row with a new `id` rather
 * than mutating the old one, specifically so an already-given answer's
 * meaning never silently changes underneath it. A translation attached to
 * a `slug` would break that invariant the moment the English question is
 * edited (the Spanish translation would silently keep showing next to
 * new English text it was never reviewed against). Keying by
 * `question_bank_id` means a translation is pinned to the exact wording
 * it was translated FROM, same as an answer is pinned to the exact
 * wording it was given TO — editing a question's English text simply
 * makes the new version's `question_bank_id` have no translation yet
 * (falls back to English, same as any other missing-translation case),
 * rather than showing stale, wrong Spanish.
 *
 * WHAT THE QUESTION-BANK OWNER NEEDS TO ADOPT — this build cannot wire
 * this in itself (question.service.ts is off limits), so the exact
 * integration point is spelled out here AND in docs/localization.md:
 * wherever `question.service.ts` builds the `QuestionDefinition` it
 * returns to a client (its own DB row -> `QuestionDefinition` mapping),
 * call `getQuestionTranslation(ctx, def.id, locale)` for the caller's
 * negotiated locale (see `resolveLocale` in locales.ts) and pass the
 * result through `localizeQuestionDefinition(def, translation)` before
 * serializing. Two function calls, no schema change on that module's
 * side, no behavior change for a locale with no translation row (falls
 * back to the question's own English text/labels — see
 * `localizeQuestionDefinition`'s doc).
 */
import { z } from 'zod';
import type { Ctx } from '../../lib/ctx.js';
import { ValidationError } from '../../lib/errors.js';
import { fallbackChain } from './locales.js';
import type {
  ChoiceOption,
  FrequencyDefinition,
  MultiChoiceDefinition,
  QuestionDefinition,
  QuestionTypeDefinition,
  ScaleDefinition,
  SingleChoiceDefinition,
} from '../questions/types.js';

export interface QuestionTranslationRow {
  questionBankId: string;
  locale: string;
  /** Overrides `QuestionDefinition.questionText` when present. Absent (not just empty-string) means "not translated yet" — falls back, never renders an empty question. */
  questionText: string | null;
  /**
   * Option/anchor/scale-endpoint label overrides, keyed by:
   *   - scale: the fixed keys `"minLabel"` / `"maxLabel"` / `"midLabel"`.
   *   - single_choice / multi_choice / frequency: each `ChoiceOption.key`
   *     (the STABLE machine key — never the English label itself, so
   *     reordering/relabeling English options never orphans a
   *     translation).
   * Partial by design — a translator can localize option labels before
   * (or without ever) localizing the question text itself, or vice
   * versa; each field degrades independently in
   * `localizeQuestionDefinition`.
   */
  labels: Record<string, string>;
  updatedAt: Date;
}

interface QuestionTranslationDbRow {
  question_bank_id: string;
  locale: string;
  question_text: string | null;
  labels: Record<string, string>;
  updated_at: Date;
}

function mapRow(row: QuestionTranslationDbRow): QuestionTranslationRow {
  return {
    questionBankId: row.question_bank_id,
    locale: row.locale,
    questionText: row.question_text,
    labels: row.labels,
    updatedAt: row.updated_at,
  };
}

const UpsertQuestionTranslationSchema = z
  .object({
    questionText: z.string().trim().min(1).max(2000).optional(),
    labels: z.record(z.string().trim().min(1).max(300)).optional(),
  })
  .refine((v) => v.questionText !== undefined || v.labels !== undefined, {
    message: 'Provide at least one of questionText or labels.',
  });
export type UpsertQuestionTranslationInput = z.infer<typeof UpsertQuestionTranslationSchema>;

/**
 * Creates or updates the translation row for one (question, locale) pair.
 * Never touches `question_bank` itself. Callers (an admin route on the
 * question-bank owner's side, per the integration note above) are
 * responsible for authorizing the caller as an admin before calling this
 * — this function itself only validates shape, not permission, matching
 * how other admin-only mutation helpers in this codebase separate
 * "is this well-formed" from "is this caller allowed" at the route layer.
 */
export async function upsertQuestionTranslation(
  ctx: Ctx,
  questionBankId: string,
  locale: string,
  input: UpsertQuestionTranslationInput,
): Promise<QuestionTranslationRow> {
  const parsed = UpsertQuestionTranslationSchema.parse(input);
  const { rows: existing } = await ctx.db.query<QuestionTranslationDbRow>(
    `SELECT question_bank_id, locale, question_text, labels, updated_at FROM question_bank_translations WHERE question_bank_id = $1 AND locale = $2`,
    [questionBankId, locale],
  );
  const mergedLabels = { ...(existing[0]?.labels ?? {}), ...(parsed.labels ?? {}) };
  const questionText = parsed.questionText ?? existing[0]?.question_text ?? null;
  const now = ctx.clock.now();

  const { rows } = await ctx.db.query<QuestionTranslationDbRow>(
    `INSERT INTO question_bank_translations (question_bank_id, locale, question_text, labels, updated_at)
     VALUES ($1, $2, $3, $4::jsonb, $5)
     ON CONFLICT (question_bank_id, locale) DO UPDATE
       SET question_text = EXCLUDED.question_text, labels = EXCLUDED.labels, updated_at = EXCLUDED.updated_at
     RETURNING question_bank_id, locale, question_text, labels, updated_at`,
    [questionBankId, locale, questionText, JSON.stringify(mergedLabels), now],
  );
  const row = rows[0];
  if (!row) throw new ValidationError('Failed to save question translation.');
  return mapRow(row);
}

/**
 * Resolves the best available translation for `questionBankId` given a
 * requested `locale`, walking the same fallback chain `translate()` uses
 * — EXCEPT the chain's final link (`en`) is deliberately never queried
 * here: `question_bank.question_text`/`type_definition` (base row) IS the
 * English text, so "no row found even after walking the chain" and
 * "found the `en` row" mean the same thing — falling back to the
 * `QuestionDefinition` the caller already has, via
 * `localizeQuestionDefinition(def, null)`, rather than requiring an `en`
 * row to exist in this table too (which would mean translating English
 * to English for every one of 600+ questions for no reason).
 */
export async function getQuestionTranslation(ctx: Ctx, questionBankId: string, locale: string): Promise<QuestionTranslationRow | null> {
  const candidates = fallbackChain(locale).filter((loc) => loc !== 'en');
  if (candidates.length === 0) return null;

  const { rows } = await ctx.db.query<QuestionTranslationDbRow>(
    `SELECT question_bank_id, locale, question_text, labels, updated_at FROM question_bank_translations WHERE question_bank_id = $1 AND locale = ANY($2::text[])`,
    [questionBankId, candidates],
  );
  if (rows.length === 0) return null;

  const byLocale = new Map(rows.map((r) => [r.locale, r]));
  for (const loc of candidates) {
    const row = byLocale.get(loc);
    if (row) return mapRow(row);
  }
  return null;
}

/** Batch form of `getQuestionTranslation` for a page of questions at once (avoids N+1 queries in a listing endpoint) — same fallback semantics per id. */
export async function getQuestionTranslations(ctx: Ctx, questionBankIds: string[], locale: string): Promise<Map<string, QuestionTranslationRow>> {
  const result = new Map<string, QuestionTranslationRow>();
  if (questionBankIds.length === 0) return result;
  const candidates = fallbackChain(locale).filter((loc) => loc !== 'en');
  if (candidates.length === 0) return result;

  const { rows } = await ctx.db.query<QuestionTranslationDbRow>(
    `SELECT question_bank_id, locale, question_text, labels, updated_at FROM question_bank_translations WHERE question_bank_id = ANY($1::uuid[]) AND locale = ANY($2::text[])`,
    [questionBankIds, candidates],
  );
  const byQuestion = new Map<string, QuestionTranslationDbRow[]>();
  for (const row of rows) {
    const list = byQuestion.get(row.question_bank_id) ?? [];
    list.push(row);
    byQuestion.set(row.question_bank_id, list);
  }
  for (const [questionBankId, candidateRows] of byQuestion) {
    const byLocale = new Map(candidateRows.map((r) => [r.locale, r]));
    for (const loc of candidates) {
      const row = byLocale.get(loc);
      if (row) {
        result.set(questionBankId, mapRow(row));
        break;
      }
    }
  }
  return result;
}

function localizeOptions(options: ChoiceOption[], labels: Record<string, string>): ChoiceOption[] {
  return options.map((opt) => (labels[opt.key] ? { ...opt, label: labels[opt.key]! } : opt));
}

function localizeTypeDef(typeDef: QuestionTypeDefinition, labels: Record<string, string>): QuestionTypeDefinition {
  switch (typeDef.type) {
    case 'scale': {
      const t = typeDef as ScaleDefinition;
      return {
        ...t,
        minLabel: labels.minLabel ?? t.minLabel,
        maxLabel: labels.maxLabel ?? t.maxLabel,
        midLabel: labels.midLabel ?? t.midLabel,
      };
    }
    case 'single_choice': {
      const t = typeDef as SingleChoiceDefinition;
      return { ...t, options: localizeOptions(t.options, labels) };
    }
    case 'multi_choice': {
      const t = typeDef as MultiChoiceDefinition;
      return { ...t, options: localizeOptions(t.options, labels) };
    }
    case 'frequency': {
      const t = typeDef as FrequencyDefinition;
      return { ...t, anchors: localizeOptions(t.anchors, labels) };
    }
  }
}

/**
 * Pure function: returns a copy of `def` with its `questionText` and
 * `typeDef` labels overridden by `translation`, field by field.
 * `translation: null` (or any individual missing field within it) leaves
 * the corresponding original English field completely untouched — this
 * is the "missing translation degrades to the fallback" contract applied
 * at the per-field level, not just per-question, so a half-translated
 * question (options localized, question text not yet) still renders
 * correctly rather than looking broken.
 */
export function localizeQuestionDefinition(def: QuestionDefinition, translation: QuestionTranslationRow | null): QuestionDefinition {
  if (!translation) return def;
  return {
    ...def,
    questionText: translation.questionText ?? def.questionText,
    typeDef: localizeTypeDef(def.typeDef, translation.labels),
  };
}
