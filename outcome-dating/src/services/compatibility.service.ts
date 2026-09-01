import type { Ctx } from '../lib/ctx.js';
import type { Answer, AnswerValue, CompatibilityScoreRow, Question, QuestionPolarity } from '../domain/types.js';

/**
 * compatibility.service — the §16.2 scoring formula and its storage.
 * Spec: §16, §25.4 (nightly refresh job).
 *
 * Owning agent: B.
 *
 * INVARIANT: this module SORTS; it never decides who is eligible to be
 * seen. `discovery.service.ts` calls `getScore`/`getScoresForCandidates`
 * only after `filter.service.ts#passesMutualFilters` has already gated the
 * candidate pool (spec §16.1, §9.1).
 *
 * `computePairScore` is a pure function of two users' answers + the
 * question bank — no I/O — so it's directly unit-testable against the
 * worked example in spec §16.2. `getScore`/`refreshScoresForUser` are the
 * I/O-performing wrappers that read `answers`, call `computePairScore`,
 * and read/write the `compatibility_scores` materialization (spec §16.3).
 *
 * LEAF MODULE: per INTERFACES.md's module table, `compatibility.service`'s
 * "May call" column is blank — it is a leaf that reads `answers`/
 * `questions` directly and calls no other service module. In particular it
 * does NOT call `filter.service` even though the stub JSDoc for
 * `refreshScoresForUser` (frozen, written before this file was
 * implemented) says "against every candidate that currently passes their
 * mutual filters" — that would require importing `filter.service`, which
 * the authoritative call-graph forbids for this module. Read literally:
 * `refreshScoresForUser`/`refreshAllScores` (re)compute the score for every
 * *other active user*, unfiltered; `discovery.service.ts` (which is
 * sanctioned to call both `filter` and `compatibility`) is what actually
 * combines a filter-passed candidate set with these scores at read time.
 * Flagged in the handoff report as a stub-doc/call-graph conflict I
 * resolved in favor of the call-graph (the document says it is
 * authoritative).
 */

// =====================================================================
// Row <-> domain mapping (reads `answers`/`questions` directly — this
// module owns no other service dependency, see LEAF MODULE note above).
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

async function loadActiveQuestions(ctx: Ctx): Promise<Question[]> {
  const { rows } = await ctx.db.query<QuestionRow>('SELECT * FROM questions WHERE active = true');
  return rows.map(questionFromRow);
}

async function loadAnswersForUser(ctx: Ctx, userId: string): Promise<Answer[]> {
  const { rows } = await ctx.db.query<AnswerRow>('SELECT * FROM answers WHERE user_id = $1', [userId]);
  return rows.map(answerFromRow);
}

/**
 * Minimum number of questions both users must have *fully* answered
 * (non-null self AND partner value on both sides) before a score is
 * computed at all — below this, score defaults to
 * `compatibility.no_data_default_score` (spec §16.2 last paragraph;
 * Open Question OQ-2's resolution: `0`, not an ambiguous "neutral" — see
 * docs/conformance.md).
 *
 * DECISION-LAYER UPDATE: this used to be a local constant because
 * `src/config/config.service.ts` was outside this agent's file-ownership
 * boundary during the parallel build. It is now backed by the real
 * `compatibility.min_shared_questions` config key (default still `3`,
 * unchanged) — `getScore`/`getScoresForCandidates`/`refreshScoresForUser`/
 * `refreshAllScores` all read it from `ctx.config`. This constant is kept,
 * still equal to the config default, purely so `computePairScore` (a pure
 * function with no `ctx`) stays directly unit-testable without a DB —
 * `tests/unit/compatibility.test.ts` uses it that way.
 */
export const DEFAULT_MIN_SHARED_QUESTIONS = 3;

/** Config default for `compatibility.no_data_default_score` — see the same note above; kept for `computePairScore`'s pure-function default parameter. */
export const DEFAULT_NO_DATA_SCORE = 0;

export interface PerQuestionSatisfaction {
  questionId: string;
  pairSatisfaction: number; // 0-1
  questionWeight: number; // base_weight * importance_multiplier
}

export interface CompatibilityBreakdown {
  score: number; // 0-1; 0 if too few shared answered questions (§16.2 last paragraph)
  perQuestion: PerQuestionSatisfaction[];
  sharedAnsweredQuestionCount: number;
}

/**
 * §16.2 reversed-polarity transform, applied to a raw 1-5 value.
 * `transformed = 6 - original`.
 */
function applyPolarity(value: number, polarity: QuestionPolarity): number {
  return polarity === 'reversed' ? 6 - value : value;
}

/**
 * Pure implementation of the §16.2 formula for one ordered pair (A, B).
 * Symmetric by construction (`pair_satisfaction` averages both
 * directions), so `computePairScore(a, b, qs) === computePairScore(b, a, qs)`
 * is an expected property for tests. `null` self/partner values
 * ("prefer not to say", §8.5) are excluded from `sharedAnsweredQuestionCount`
 * and do not contribute to the weighted sum.
 *
 * A question only contributes if BOTH users answered BOTH sides of it
 * (A.self, A.partner, B.self, B.partner all non-null) — that is what
 * "shared answered question" means here. If any of the four is null (or
 * either user has no `answers` row for the question at all), the question
 * is skipped entirely: no partial/one-sided contribution.
 *
 * READING OF THE §16.2 REVERSED-POLARITY TRANSFORM: applied to *all four*
 * values (both users' self AND partner answers) for a reversed-polarity
 * question, before any arithmetic. Note this is mathematically invariant
 * for the final numbers — `abs((6-x)-(6-y)) === abs(x-y)` and
 * `abs((6-x)-3) === abs(x-3)` — so a question's contribution to the score
 * is identical whether or not it is marked reversed, PROVIDED the raw
 * stored values are consistently on whichever scale the flag implies. That
 * is the point of the flag: it lets a question be authored/entered on
 * either scale convention (e.g. "1 = no smoking" vs "1 = smokes heavily")
 * and still combine correctly with every other question — the invariance
 * is what makes `reversed` *safe* to get right or wrong for any single
 * question without it silently corrupting the pair's total score, while
 * still being something the code must apply correctly per-question (get it
 * wrong on `self` values but not `partner` values, for example, and the
 * invariance breaks). Verified in `tests/unit/compatibility.test.ts` by
 * comparing a reversed-polarity question fed mirrored raw values (`6 - x`
 * for every stored value) against the equivalent standard-polarity
 * question fed the original values, and asserting identical scores.
 *
 * READING OF "importance_multiplier ... based on extremity of partner
 * preference" (§16.2): the spec does not say *whose* partner_answer feeds
 * `1 + abs(partner_answer - 3) * 0.25` for a given question, and this
 * function's docstring requires `computePairScore(a,b,qs) ===
 * computePairScore(b,a,qs)` (argument-order symmetry). A single-sided
 * reading (e.g. always A's partner_answer) is NOT symmetric under swapping
 * the two callers' argument order, so it is rejected. This implementation
 * computes the importance multiplier for EACH user's partner_answer to the
 * question and averages the two: `question_weight = base_weight *
 * mean(importance_multiplier(A.partner), importance_multiplier(B.partner))`
 * — i.e. a question is weighted more heavily when *either* party has a
 * strong (non-neutral) preference about it, which also happens to be the
 * only reading consistent with the required symmetry.
 */
export function computePairScore(
  userAAnswers: Answer[],
  userBAnswers: Answer[],
  questions: Question[],
  minSharedQuestions: number,
  noDataDefaultScore: number = DEFAULT_NO_DATA_SCORE,
): CompatibilityBreakdown {
  const aByQuestion = new Map(userAAnswers.map((a) => [a.questionId, a]));
  const bByQuestion = new Map(userBAnswers.map((a) => [a.questionId, a]));

  const perQuestion: PerQuestionSatisfaction[] = [];
  let weightedSum = 0;
  let weightTotal = 0;

  for (const q of questions) {
    if (!q.active) continue;
    const a = aByQuestion.get(q.id);
    const b = bByQuestion.get(q.id);
    if (!a || !b) continue;
    if (a.selfValue == null || a.partnerValue == null || b.selfValue == null || b.partnerValue == null) continue;

    const aSelf = applyPolarity(a.selfValue, q.polarity);
    const aPartner = applyPolarity(a.partnerValue, q.polarity);
    const bSelf = applyPolarity(b.selfValue, q.polarity);
    const bPartner = applyPolarity(b.partnerValue, q.polarity);

    // satisfaction_A_with_B = 1 - abs(A.partner_answer - B.self_answer) / 4
    const satisfactionAWithB = 1 - Math.abs(aPartner - bSelf) / 4;
    // satisfaction_B_with_A = 1 - abs(B.partner_answer - A.self_answer) / 4
    const satisfactionBWithA = 1 - Math.abs(bPartner - aSelf) / 4;
    const pairSatisfaction = (satisfactionAWithB + satisfactionBWithA) / 2;

    // importance_multiplier = 1 + abs(partner_answer - 3) * 0.25, averaged
    // across both users' partner_answer — see docstring "READING OF
    // importance_multiplier" above for why.
    const importanceA = 1 + Math.abs(aPartner - 3) * 0.25;
    const importanceB = 1 + Math.abs(bPartner - 3) * 0.25;
    const importanceMultiplier = (importanceA + importanceB) / 2;

    const questionWeight = q.weight * importanceMultiplier;

    perQuestion.push({ questionId: q.id, pairSatisfaction, questionWeight });
    weightedSum += pairSatisfaction * questionWeight;
    weightTotal += questionWeight;
  }

  const sharedAnsweredQuestionCount = perQuestion.length;
  const score =
    sharedAnsweredQuestionCount < minSharedQuestions || weightTotal <= 0
      ? noDataDefaultScore
      : weightedSum / weightTotal;

  return { score, perQuestion, sharedAnsweredQuestionCount };
}

async function upsertScore(ctx: Ctx, userId: string, candidateId: string, score: number): Promise<void> {
  await ctx.db.query(
    `INSERT INTO compatibility_scores (user_id, candidate_id, score, computed_at)
     VALUES ($1, $2, $3, $4)
     ON CONFLICT (user_id, candidate_id) DO UPDATE SET
       score = EXCLUDED.score,
       computed_at = EXCLUDED.computed_at`,
    [userId, candidateId, score, ctx.clock.now()],
  );
}

/**
 * SCALE FIX (docs/scale-and-sources.md Part 1, §1.2.1 last paragraph):
 * `getScoresForCandidates` used to call `upsertScore` once per candidate,
 * sequentially, inside its loop — one write round trip per candidate on
 * EVERY discovery request, riding along with (and adding to) §1.1.2's
 * per-candidate read cost. This writes the whole batch as ONE
 * multi-row upsert (`unnest` over the candidate/score arrays) instead,
 * so this function's write cost is O(1) round trips regardless of how
 * many candidates it scored — same fix shape as
 * `filter.service#evaluateFilterPairsBatch`, applied to a write instead
 * of a read. Also used by `refreshScoresForUser` (this file, still
 * O(all-active-users) rows read/scored — geographically bounding THAT
 * candidate list is out of this build's scope, see this build's report —
 * but its write side is now batched too, for free, since it calls this
 * same function).
 */
async function upsertScoresBatch(ctx: Ctx, userId: string, scores: Map<string, number>): Promise<void> {
  if (scores.size === 0) return;
  const candidateIds = [...scores.keys()];
  const values = candidateIds.map((id) => scores.get(id)!);
  await ctx.db.query(
    `INSERT INTO compatibility_scores (user_id, candidate_id, score, computed_at)
     SELECT $1, c.candidate_id, c.score, $4
     FROM unnest($2::uuid[], $3::double precision[]) AS c(candidate_id, score)
     ON CONFLICT (user_id, candidate_id) DO UPDATE SET
       score = EXCLUDED.score,
       computed_at = EXCLUDED.computed_at`,
    [userId, candidateIds, values, ctx.clock.now()],
  );
}

/**
 * On-demand score for one candidate pair (spec §16.3: "For MVP, compute
 * score on demand for candidates"). Always recomputes from current
 * `answers` — this module deliberately does not implement a staleness
 * window (that would need a new config key; see `DEFAULT_MIN_SHARED_QUESTIONS`
 * comment on the file-ownership constraint) — and upserts the materialized
 * `compatibility_scores` row as a side effect so `refreshAllScores`/direct
 * reads of the table stay consistent with the latest on-demand computation.
 */
/** Reads the two decision-layer config keys this module's scoring depends on (see `DEFAULT_MIN_SHARED_QUESTIONS`/`DEFAULT_NO_DATA_SCORE` docs above). */
async function loadScoringConfig(ctx: Ctx): Promise<{ minSharedQuestions: number; noDataDefaultScore: number }> {
  const values = await ctx.config.getMany(['compatibility.min_shared_questions', 'compatibility.no_data_default_score'] as const);
  return {
    minSharedQuestions: values['compatibility.min_shared_questions'],
    noDataDefaultScore: values['compatibility.no_data_default_score'],
  };
}

export async function getScore(ctx: Ctx, userId: string, candidateId: string): Promise<number> {
  const [questions, userAAnswers, userBAnswers, scoringConfig] = await Promise.all([
    loadActiveQuestions(ctx),
    loadAnswersForUser(ctx, userId),
    loadAnswersForUser(ctx, candidateId),
    loadScoringConfig(ctx),
  ]);
  const { score } = computePairScore(userAAnswers, userBAnswers, questions, scoringConfig.minSharedQuestions, scoringConfig.noDataDefaultScore);
  await upsertScore(ctx, userId, candidateId, score);
  return score;
}

/** Batch variant used by `discovery.service.ts` to sort a whole candidate page in one call. */
export async function getScoresForCandidates(ctx: Ctx, userId: string, candidateIds: string[]): Promise<Map<string, number>> {
  const result = new Map<string, number>();
  if (candidateIds.length === 0) return result;

  const questions = await loadActiveQuestions(ctx);
  const userAAnswers = await loadAnswersForUser(ctx, userId);
  const scoringConfig = await loadScoringConfig(ctx);

  const { rows } = await ctx.db.query<AnswerRow>(
    'SELECT * FROM answers WHERE user_id = ANY($1::uuid[])',
    [candidateIds],
  );
  const answersByCandidate = new Map<string, Answer[]>();
  for (const row of rows) {
    const answer = answerFromRow(row);
    const list = answersByCandidate.get(answer.userId);
    if (list) list.push(answer);
    else answersByCandidate.set(answer.userId, [answer]);
  }

  for (const candidateId of candidateIds) {
    const candidateAnswers = answersByCandidate.get(candidateId) ?? [];
    const { score } = computePairScore(userAAnswers, candidateAnswers, questions, scoringConfig.minSharedQuestions, scoringConfig.noDataDefaultScore);
    result.set(candidateId, score);
  }
  await upsertScoresBatch(ctx, userId, result);

  return result;
}

/**
 * Recomputes and upserts `compatibility_scores` rows for one user against
 * every other active user (see LEAF MODULE note at the top of this file
 * for why this does not filter by mutual hard filters despite the stub
 * JSDoc's original wording — that filtering happens in
 * `discovery.service.ts`, which is sanctioned to call both `filter` and
 * `compatibility`). Called after an answer change (spec §25.4 "on major
 * answer changes") via `question.service#putMyAnswers`.
 */
export async function refreshScoresForUser(ctx: Ctx, userId: string): Promise<{ updated: number }> {
  const { rows } = await ctx.db.query<{ id: string }>(
    `SELECT id FROM users WHERE status = 'active' AND id <> $1`,
    [userId],
  );
  const candidateIds = rows.map((r) => r.id);
  const scores = await getScoresForCandidates(ctx, userId, candidateIds);
  return { updated: scores.size };
}

/** §25.4 nightly job: refresh every user's `compatibility_scores`, both directions per pair, computed once per unordered pair. */
export async function refreshAllScores(ctx: Ctx): Promise<{ updated: number }> {
  const { rows } = await ctx.db.query<{ id: string }>(`SELECT id FROM users WHERE status = 'active'`);
  const ids = rows.map((r) => r.id);
  if (ids.length < 2) return { updated: 0 };

  const questions = await loadActiveQuestions(ctx);
  const scoringConfig = await loadScoringConfig(ctx);
  const answersByUser = new Map<string, Answer[]>();
  for (const id of ids) {
    answersByUser.set(id, await loadAnswersForUser(ctx, id));
  }

  let updated = 0;
  for (let i = 0; i < ids.length; i++) {
    for (let j = i + 1; j < ids.length; j++) {
      const idA = ids[i]!;
      const idB = ids[j]!;
      const { score } = computePairScore(
        answersByUser.get(idA) ?? [],
        answersByUser.get(idB) ?? [],
        questions,
        scoringConfig.minSharedQuestions,
        scoringConfig.noDataDefaultScore,
      );
      await upsertScore(ctx, idA, idB, score);
      await upsertScore(ctx, idB, idA, score);
      updated += 2;
    }
  }
  return { updated };
}

export type { CompatibilityScoreRow };
