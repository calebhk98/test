/**
 * Type system for the redesigned compatibility question bank.
 *
 * Replaces the old "every question is a 1-5 self/partner pair" model
 * (still live, unmodified, in db/migrations/001_init.sql's `questions`/
 * `answers` tables and compatibility.service.ts / filter.service.ts /
 * behavioralPrompt.service.ts) with a typed bank: a question has a
 * `QuestionType`, and a user's preference on it is always a VALUE (what
 * they want) plus an IMPORTANCE (how much it matters) — never a bare
 * number pretending to be both.
 *
 * Extensibility: scoring (scoring.ts), the pure functions in this
 * directory, and the DB schema (db/migrations/008_questions.sql) never
 * switch on `QuestionType` with a hardcoded list of cases outside of
 * `typeHandlers.ts`. Adding a new question type means: add a definition
 * shape here, add one entry to `TYPE_HANDLERS` in typeHandlers.ts, done —
 * scoring.ts, selector.ts, and question.service.ts's persistence code
 * never need to change.
 */

// =====================================================================
// Question types
// =====================================================================

/**
 * `scale` is the ONLY type with a meaningful midpoint — that's why it's
 * the only one that gets one. Everything else is categorical/ordinal
 * data that a 1-5 Likert scale was previously forced onto, which is
 * exactly the bug this redesign fixes (see module doc above).
 */
export type QuestionType = 'scale' | 'single_choice' | 'multi_choice' | 'frequency';

export const QUESTION_TYPES: readonly QuestionType[] = ['scale', 'single_choice', 'multi_choice', 'frequency'];

/** An ordered Likert scale. The midpoint MUST be labelled — an unlabelled midpoint is exactly what testers flagged as meaningless. */
export interface ScaleDefinition {
  type: 'scale';
  min: number; // typically 1
  max: number; // typically 5; must be min + an even number so a midpoint exists
  minLabel: string;
  maxLabel: string;
  midLabel: string;
}

export interface ChoiceOption {
  /** Stable machine key — never renumbered; this is what gets stored on an answer row and referenced by filters. */
  key: string;
  /** Concrete, non-judgemental, user-visible label. No bare numbers, no vague adverbs. */
  label: string;
}

/** Categorical, mutually exclusive (kids, religion, relationship intention). A user picks exactly one option; a partner PREFERENCE over this question is a SET of acceptable options, not a number. */
export interface SingleChoiceDefinition {
  type: 'single_choice';
  options: ChoiceOption[];
}

/** Pick any number of options (languages spoken, activities enjoyed). */
export interface MultiChoiceDefinition {
  type: 'multi_choice';
  options: ChoiceOption[];
}

/** An ordered frequency scale with concrete behavioural anchors (never / a few times a year / monthly / weekly / daily), not a vague 1-5. `anchors` is ordered least -> most frequent; that order is the ordinal scale scoring uses. */
export interface FrequencyDefinition {
  type: 'frequency';
  anchors: ChoiceOption[];
}

export type QuestionTypeDefinition = ScaleDefinition | SingleChoiceDefinition | MultiChoiceDefinition | FrequencyDefinition;

/**
 * A single immutable version of a question. Editing a question's text or
 * options creates a NEW row with an incremented `version`; the previous
 * row keeps existing (see db/migrations/008_questions.sql
 * `question_bank` table) so answers already pinned to it keep their
 * original meaning (see AnswerRecord.questionBankId).
 */
export interface QuestionDefinition {
  /** The specific (slug, version) row's id — this is what an answer pins to, not the slug alone. */
  id: string;
  slug: string;
  version: number;
  category: string;
  subcategory: string | null;
  tags: string[];
  questionText: string;
  typeDef: QuestionTypeDefinition;
  /** Base weight before the importance multiplier (see importance.ts). Product-tunable per question, same role as the old `questions.weight` column. */
  baseWeight: number;
  sensitive: boolean;
  active: boolean;
  /** Selector priority signal — the fraction of users shown this question who go on to answer it (vs. skip). Product/analytics-owned; defaults to 0.5 for a question with no observed data yet. See selector.ts. */
  answerRateHint: number;
}

export function questionType(def: QuestionDefinition): QuestionType {
  return def.typeDef.type;
}

// =====================================================================
// Importance
// =====================================================================

export const IMPORTANCE_LEVELS = ['irrelevant', 'slight', 'important', 'critical', 'deal_breaker'] as const;
export type ImportanceLevel = (typeof IMPORTANCE_LEVELS)[number];

// =====================================================================
// Answer state — the three non-answer states plus a real answer.
// =====================================================================

/**
 * `unanswered` — never shown, or shown and never acted on. In practice
 * this is represented by the ABSENCE of a `user_question_answers` row
 * (see db/migrations/008_questions.sql), never a persisted row — it's
 * included here as an explicit tag so pure functions (scoring, tests)
 * can represent "no data" without needing a sentinel `null`.
 *
 * `skipped` — shown, user explicitly moved on without answering. Gets a
 * row (so the selector can apply a skip cooldown — see selector.ts) but
 * carries no value/importance.
 *
 * `prefer_not_to_say` — deliberate refusal to answer. Gets a row, may be
 * surfaced on the profile as "prefers not to say" (question.service.ts),
 * and — per spec — is treated as neutral for SCORING (contributes
 * nothing, same as skipped/unanswered) but can still fail another user's
 * deal-breaker filter (see dealBreakers.ts) — filters win over the
 * "treat as neutral" rule.
 *
 * `answered` — a real value + importance were given.
 */
export type AnswerStatus = 'unanswered' | 'skipped' | 'prefer_not_to_say' | 'answered';

/**
 * `selfValue` describes the user (what they ARE / DO); `preferenceValue`
 * describes what they WANT in a partner. Both are typed per
 * `QuestionType`:
 *   - scale / frequency: a number (scale) or an anchor key (frequency)
 *     for BOTH self and preference — matched by ordinal distance.
 *   - single_choice: selfValue is one option key; preferenceValue is a
 *     SET (string[]) of acceptable option keys — this is the fix for
 *     "what does a midpoint of 3 mean" (§ the redesign brief).
 *   - multi_choice: both self and preference are string[] option-key
 *     sets, matched by overlap.
 * Only meaningful when `status === 'answered'`; both are `null`
 * otherwise.
 */
export interface QuestionAnswerState {
  status: AnswerStatus;
  selfValue: unknown | null;
  preferenceValue: unknown | null;
  importance: ImportanceLevel | null;
}

export function unansweredState(): QuestionAnswerState {
  return { status: 'unanswered', selfValue: null, preferenceValue: null, importance: null };
}

export function skippedState(): QuestionAnswerState {
  return { status: 'skipped', selfValue: null, preferenceValue: null, importance: null };
}

export function preferNotToSayState(): QuestionAnswerState {
  return { status: 'prefer_not_to_say', selfValue: null, preferenceValue: null, importance: null };
}

export function answeredState(selfValue: unknown, preferenceValue: unknown, importance: ImportanceLevel): QuestionAnswerState {
  return { status: 'answered', selfValue, preferenceValue, importance };
}
