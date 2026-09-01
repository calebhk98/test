import type { QuestionDefinition } from './types.js';

/**
 * The selector only ever reads these five fields, never a question's
 * full type definition/labels/options. `QuestionDefinition` satisfies
 * this structurally, so a caller with full definitions in hand can pass
 * them straight through, but `question.service.ts`'s selector wrapper
 * queries only these columns for the whole active bank rather than
 * pulling every row's `type_definition` jsonb (irrelevant to selection,
 * and the more expensive column at 600+ rows), see the module's
 * COMPLEXITY note below.
 */
export type SelectableQuestion = Pick<QuestionDefinition, 'id' | 'slug' | 'category' | 'active' | 'baseWeight' | 'answerRateHint'>;

/**
 * "What should we ask this user next?", a prioritized, pure, in-memory
 * selector. No I/O: `question.service.ts`'s wrapper loads the active
 * question bank plus this one user's answer/skip history and calls
 * `selectNextQuestions` with plain data.
 *
 * PRIORITIZATION, per question still eligible (see exclusion rules
 * below):
 *
 *   score = ANSWER_RATE_WEIGHT   * question.answerRateHint
 *         + INFO_VALUE_WEIGHT    * normalizedInfoValue(question)
 *         + CATEGORY_BALANCE_WEIGHT * categoryDeficit(question.category)
 *
 *   - `answerRateHint` (0-1, on `QuestionDefinition`, see types.ts):
 *     "high-answer-rate", a question most users actually answer (rather
 *     than skip) is worth asking sooner, since a skipped question earns
 *     nothing.
 *   - `normalizedInfoValue`: `question.baseWeight` scaled into 0-1 across
 *     the candidate set (min-max normalized within THIS call, not a
 *     global constant, so it stays meaningful regardless of what scale
 *     `baseWeight` happens to be authored on), "high-information":
 *     product has already told us via `baseWeight` how much a question
 *     matters to matching.
 *   - `categoryDeficit(category)`: how under-represented `category` is in
 *     this user's answered set relative to its share of the whole active
 *     bank, `max(0, bankShare(category) - answeredShare(category))`.
 *     Keeps the asked set roughly proportional to the bank's category mix
 *     ("category-balanced") instead of exhausting one category before
 *     ever touching another.
 *
 * EXCLUSION (never returned):
 *   - inactive questions,
 *   - already `answered` or `prefer_not_to_say` (settled, the three
 *     non-answer states in types.ts do NOT include these; only a real
 *     answer or an explicit refusal retires a question from the queue),
 *   - `skipped` more recently than `skipCooldownDays` ago (default
 *     `DEFAULT_SKIP_COOLDOWN_DAYS`), "never repeating skipped questions
 *     too soon". A skip older than the cooldown becomes eligible again
 *     (people's willingness to answer changes) but is not further
 *     boosted or penalized beyond that.
 *
 * COMPLEXITY: let Q = number of active questions in the bank (the task's
 * "600+" scenario) and H = size of this one user's answer/skip history
 * (bounded by however many of those Q questions they've touched, so
 * H <= Q always, the task's "40 answered" is comfortably inside that).
 * `selectNextQuestions` is O(Q log Q) time (one pass building per-category
 * aggregates in O(Q), one score computation per candidate in O(Q), one
 * sort of the surviving candidates in O(Q log Q)) and O(Q) space. It does
 * NOT scan any other user's data and does NOT depend on total answer
 * volume across the whole user base, only on the size of the bank and of
 * the single caller's own history. See
 * tests/unit/questionScoring.test.ts's "600+ question bank" perf test,
 * which asserts wall-clock time stays low and roughly linear-ish as Q
 * grows from 600 to several thousand.
 */

export const DEFAULT_SKIP_COOLDOWN_DAYS = 14;

const ANSWER_RATE_WEIGHT = 0.4;
const INFO_VALUE_WEIGHT = 0.4;
const CATEGORY_BALANCE_WEIGHT = 0.2;

export type SettledStatus = 'answered' | 'prefer_not_to_say';

export interface UserQuestionHistoryEntry {
  status: SettledStatus | 'skipped';
  at: Date;
}

export interface SelectNextQuestionsInput {
  /** The full active question bank (or at least every question this user could plausibly be shown). */
  questions: SelectableQuestion[];
  /** This user's history, keyed by question slug. Absent slug = never shown/never answered (fully eligible). */
  history: Map<string, UserQuestionHistoryEntry>;
  now: Date;
  count: number;
  skipCooldownDays?: number;
}

export interface SelectedQuestion {
  question: SelectableQuestion;
  score: number;
}

function daysBetween(a: Date, b: Date): number {
  return Math.abs(b.getTime() - a.getTime()) / (1000 * 60 * 60 * 24);
}

function isEligible(question: SelectableQuestion, history: Map<string, UserQuestionHistoryEntry>, now: Date, skipCooldownDays: number): boolean {
  if (!question.active) return false;
  const entry = history.get(question.slug);
  if (!entry) return true;
  if (entry.status === 'answered' || entry.status === 'prefer_not_to_say') return false;
  // status === 'skipped'
  return daysBetween(entry.at, now) >= skipCooldownDays;
}

export function selectNextQuestions(input: SelectNextQuestionsInput): SelectedQuestion[] {
  const { questions, history, now, count } = input;
  const skipCooldownDays = input.skipCooldownDays ?? DEFAULT_SKIP_COOLDOWN_DAYS;
  if (count <= 0) return [];

  // ---- one pass: bank category sizes + eligibility filter ----
  const bankCategoryCounts = new Map<string, number>();
  let activeCount = 0;
  const eligible: SelectableQuestion[] = [];
  for (const q of questions) {
    if (!q.active) continue;
    activeCount += 1;
    bankCategoryCounts.set(q.category, (bankCategoryCounts.get(q.category) ?? 0) + 1);
    if (isEligible(q, history, now, skipCooldownDays)) eligible.push(q);
  }
  if (eligible.length === 0) return [];

  // ---- one pass over history: answered-category counts ----
  const answeredCategoryCounts = new Map<string, number>();
  let answeredTotal = 0;
  const categoryBySlug = new Map<string, string>();
  for (const q of questions) categoryBySlug.set(q.slug, q.category);
  for (const [slug, entry] of history) {
    if (entry.status !== 'answered') continue;
    const category = categoryBySlug.get(slug);
    if (!category) continue;
    answeredCategoryCounts.set(category, (answeredCategoryCounts.get(category) ?? 0) + 1);
    answeredTotal += 1;
  }

  function categoryDeficit(category: string): number {
    const bankShare = (bankCategoryCounts.get(category) ?? 0) / Math.max(1, activeCount);
    const answeredShare = answeredTotal === 0 ? 0 : (answeredCategoryCounts.get(category) ?? 0) / answeredTotal;
    return Math.max(0, bankShare - answeredShare);
  }

  // ---- min-max normalize baseWeight across the eligible set ----
  let minWeight = Infinity;
  let maxWeight = -Infinity;
  for (const q of eligible) {
    if (q.baseWeight < minWeight) minWeight = q.baseWeight;
    if (q.baseWeight > maxWeight) maxWeight = q.baseWeight;
  }
  const weightRange = maxWeight - minWeight;
  function normalizedInfoValue(q: SelectableQuestion): number {
    return weightRange <= 0 ? 1 : (q.baseWeight - minWeight) / weightRange;
  }

  const scored: SelectedQuestion[] = eligible.map((question) => ({
    question,
    score:
      ANSWER_RATE_WEIGHT * question.answerRateHint +
      INFO_VALUE_WEIGHT * normalizedInfoValue(question) +
      CATEGORY_BALANCE_WEIGHT * categoryDeficit(question.category),
  }));

  scored.sort((a, b) => b.score - a.score || a.question.slug.localeCompare(b.question.slug));

  return scored.slice(0, count);
}
