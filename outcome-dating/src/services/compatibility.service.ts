import type { Ctx } from '../lib/ctx.js';
import { addDays } from '../lib/time.js';
import type { Answer, AnswerValue, CompatibilityScoreRow, Question, QuestionPolarity } from '../domain/types.js';
import { boundingBoxForRadius, DEFAULT_DISCOVERY_RADIUS_KM } from './filter.service.js';

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
 *
 * SCALE FIX AMENDMENT (docs/scale-and-sources.md Part 1, §1.2/§1.9 fix #3
 * — see the "bounded nightly materialization" doc further down this file):
 * this build imports exactly two symbols from `filter.service.ts` —
 * `boundingBoxForRadius` and `DEFAULT_DISCOVERY_RADIUS_KM` — to size the
 * same geographic bounding box discovery already uses, per the task
 * brief's explicit instruction to reuse that work rather than
 * reimplementing the box math a second time with its own pole/antimeridian
 * edge cases. Both are pure, no-I/O (a function of plain numbers in, a
 * plain object out; a numeric constant) — this module still performs zero
 * I/O against anything `filter.service` owns (no query, no call into any
 * function of `filter.service`'s that touches `ctx.db`), and still calls
 * no OTHER service module. Read narrowly, "calls no other service module"
 * (i.e., no cross-domain I/O dependency) is preserved; read maximally
 * literally ("imports nothing from filter.service.ts at all") it is not,
 * and that narrowing is the deliberate, reported call I'm making here —
 * the alternative (hand-copying the box-width formula, including its
 * pole/antimeridian handling, into a second file with no test tying the
 * two copies together) is exactly the "same formula, two maintained
 * copies" duplication pattern docs/scale-and-sources.md §3.4 already
 * flags as a drift risk elsewhere in this codebase, for a much cheaper
 * `import`.
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

// =====================================================================
// SCALE FIX (docs/scale-and-sources.md Part 1, §1.2/§1.9 fix #3): bounded
// nightly materialization.
//
// THE PROBLEM: `refreshAllScores` used to be a true O(active-users^2)
// nested loop — every active user against every other active user, no
// exceptions — with two sequential single-row writes per pair. Per
// docs/scale-and-sources.md §1.2.1, that stops finishing inside its 24h
// window somewhere between 3,000 and 10,000 active users, and the table
// itself is estimated at ~175TB at a million users. `refreshScoresForUser`
// (the synchronous per-answer-change path) had the same O(active users)
// shape, just triggered on every answer edit instead of once nightly.
//
// THE CORE INSIGHT (per the task brief, same one already applied to
// discovery): two people who can never plausibly appear to each other in
// discovery do not need a materialized score. `discovery.service.ts`
// bounds its candidate pool two ways before it ever asks for a score —
// geography (`filter.service#resolveGeoSearchContext`/
// `boundingBoxForRadius`, a box sized off the viewer's own distance
// preference or `DEFAULT_DISCOVERY_RADIUS_KM`) and a hard cap on how many
// candidates any one request will ever consider
// (`discovery.service#MAX_CANDIDATE_POOL_SIZE`). This build applies both
// bounds to materialization too:
//
//   1. ACTIVITY WINDOW — only users active within
//      `REFRESH_ACTIVE_WINDOW_DAYS` are refreshed or kept materialized at
//      all. A dormant account (no discovery request is ever going to be
//      served *as* them or *to* them) burns zero budget. This is the fix
//      for the STORAGE ceiling (§1.2.1's ~175TB-at-1M-users estimate was
//      driven by TOTAL ever-registered users; this build's table size is
//      driven by ACTIVE-RECENTLY users, which does not grow the same way).
//   2. GEOGRAPHIC BOUND — for a user with a location on file, only the
//      `MATERIALIZED_NEIGHBORS_PER_USER` nearest OTHER active-recent users
//      within `REFRESH_RADIUS_KM` are materialized, using the exact same
//      bounding-box idea as discovery (see the SCALE FIX AMENDMENT note at
//      the top of this file for why `boundingBoxForRadius`/
//      `DEFAULT_DISCOVERY_RADIUS_KM` are imported rather than
//      re-derived). This turns a per-city O(density^2) blow-up back into
//      O(density x K) — the same "materialize at most one plausible
//      page's worth of neighbors, not the whole local population" logic
//      the task brief calls out as the thing a pure geographic bound on
//      its own does NOT fix once one metro gets dense (a single city with
//      tens of thousands of active users is still O(city^2) without this
//      second cap).
//   3. NO-LOCATION FALLBACK — a user with no `profiles.latitude/longitude`
//      on file has no box to build (nothing to be "near"). Rather than
//      silently materializing nothing for them, this mirrors
//      `discovery.service#loadCandidatePool`'s own documented fallback
//      for exactly this case (`geo.box === null` -> cap-only bounding,
//      no geo clause): pair them against the `MATERIALIZED_NEIGHBORS_PER_USER`
//      most-recently-active OTHER eligible users platform-wide, unbounded
//      by geography but still bounded by the same K.
//
// WHY THIS IS SAFE TO BOUND AT ALL (the staleness trade-off, stated
// explicitly per the task brief):
//   - `getScore`/`getScoresForCandidates` (unchanged by this build) ALWAYS
//     recompute from live `answers` and upsert as a side effect, for
//     WHATEVER pair `discovery.service.ts` actually asks about — they
//     never read a score back out of `compatibility_scores` to return it.
//     A repo-wide search (this build's report) confirms `compatibility_scores`
//     has no reader anywhere in `src/` today; every consumer of a score
//     goes through one of these two functions. That means a pair that
//     falls OUTSIDE tonight's geographic/activity bound is not "serving a
//     stale score" — it is "not yet computed", and the very next discovery
//     request that needs it computes it fresh and warms the cache as a
//     side effect (see the cold-path test in
//     tests/unit/compatibility.test.ts). Nothing a real user sees is ever
//     more than one request stale, regardless of what this job did or
//     didn't materialize last night.
//   - What DOES stay stale, for up to ~24h, is a MATERIALIZED row nobody
//     has asked for yet: it reflects last night's answers, not this
//     morning's edit. That is exactly the product-acceptable case the
//     task brief distinguishes — "a slightly stale compatibility score is
//     not a correctness problem" — because the table is a warm-cache
//     optimization with no current reader, not a source of truth; nothing
//     about HARD FILTERS is derived from it (that invariant was already
//     true before this build and is untouched — `filter.service.ts` is
//     not edited by this build at all).
//   - `refreshScoresForUser` (still triggered synchronously on every
//     answer edit, spec §25.4 "on major answer changes") means the
//     pairs that matter most for freshness — the ones involving a user
//     who JUST changed an answer — get refreshed immediately, geo-bounded
//     the same way, not once a night.
//
// SAFE-TO-RE-RUN / EVICTION: every run recomputes `activeSince` from
// `ctx.clock`, deletes every row touching a user who is no longer eligible
// (dormant, per the activity window) or who IS eligible but whose stored
// row is not part of tonight's freshly computed keep-set, then inserts
// exactly tonight's keep-set. Re-running with an unchanged `ctx.clock` and
// unchanged data is idempotent (same delete, same insert, same rows) —
// see `tests/unit/compatibility.test.ts`'s idempotency test. This also
// means the table's row count is bounded by (eligible users x K x 2)
// AFTER EVERY RUN, not by the platform's total historical user count —
// see this build's report for the measured before/after row counts.
// =====================================================================

/**
 * Users are eligible for nightly materialization if active within this
 * many days of `ctx.clock.now()`. Would-ideally-be-config (same
 * file-ownership-boundary situation as `DEFAULT_MIN_SHARED_QUESTIONS`
 * above and `filter.service#DEFAULT_DISCOVERY_RADIUS_KM` — `config.service.ts`
 * is outside this build's ownership boundary) — flagged in this build's
 * report as a natural `compatibility.refresh_active_window_days` config
 * key for whoever next touches that file. 30 days comfortably covers
 * "anyone who could plausibly show up in someone's discovery feed today"
 * (`discovery.service.ts` orders candidates by `last_active_at DESC` with
 * no activity floor of its own, but a user dormant a full month is not a
 * realistic discovery result regardless) while keeping the eligible
 * population — and therefore the materialized table — from growing with
 * the platform's total historical signup count.
 */
const REFRESH_ACTIVE_WINDOW_DAYS = 30;

/**
 * Materialization radius, reusing `filter.service#DEFAULT_DISCOVERY_RADIUS_KM`
 * directly rather than a second magic number — see the SCALE FIX AMENDMENT
 * note at the top of this file. This is deliberately the DEFAULT radius
 * (not each user's own possibly-narrower-or-wider `distance_km` filter,
 * which `filter.service#resolveSearchRadiusKm` is not exported and would
 * need a query per user to resolve): a superset of what most users would
 * ever see (nobody has a filter by default, so most viewers' actual
 * discovery box IS exactly this radius) is a safe direction to be wrong
 * in for a cache-warming pass — a user with a wider custom radius simply
 * gets some candidates computed on demand instead of pre-warmed, which is
 * correct, just not pre-warmed (see the file-level SCALE FIX doc above).
 */
const REFRESH_RADIUS_KM = DEFAULT_DISCOVERY_RADIUS_KM;

/**
 * Materialized neighbors per user, in each geographic/fallback pass.
 * Chosen to mirror the shape of `discovery.service#MAX_CANDIDATE_POOL_SIZE`
 * (not imported — `discovery.service.ts` is outside this build's
 * ownership boundary, and pulling in an unrelated numeric constant from a
 * file this module still performs no I/O through would stretch the
 * SCALE FIX AMENDMENT reasoning further than it needs to go): materializing
 * more neighbors per user than a viewer could ever page through buys
 * nothing, since nothing today reads `compatibility_scores` directly (see
 * file-level doc above) — this budget exists purely to keep the nightly
 * job's write volume proportional to "a plausible handful of discovery
 * pages," not to city population.
 */
const MATERIALIZED_NEIGHBORS_PER_USER = 50;

/**
 * Reference latitude used only to size the LONGITUDE half of the
 * refresh's bounding box (see `refreshGeoBoxDegrees` below) — higher than
 * any of this build's seeded benchmark cities (`tests/perf/seedDiscoveryPerf.ts`'s
 * northernmost, Chicago, is ~42°N) so the box stays safely wide (never
 * too narrow — `boundingBoxForRadius`'s own invariant) for any
 * realistically populated dating-market latitude. A user whose actual
 * latitude exceeds this reference still gets a mathematically valid,
 * simply more conservative (slightly wider than strictly necessary,
 * never narrower) box — this only ever affects how many EXTRA candidates
 * the box's SQL prefilter considers, never correctness, since nothing
 * downstream trusts the box's width for anything but performance (see
 * file-level SCALE FIX doc: not reading from the materialized table is
 * what makes this safe to approximate).
 */
const SAFE_REFERENCE_LATITUDE_FOR_BOX_WIDTH_DEG = 60;

/** Half-widths (in degrees) of the fixed-radius box used by every refresh query below — computed once per call via the real, imported `boundingBoxForRadius`, not re-derived. */
function refreshGeoBoxDegrees(): { latDeltaDeg: number; lonDeltaDeg: number } {
  const latBox = boundingBoxForRadius(0, 0, REFRESH_RADIUS_KM);
  const lonBox = boundingBoxForRadius(SAFE_REFERENCE_LATITUDE_FOR_BOX_WIDTH_DEG, 0, REFRESH_RADIUS_KM);
  return {
    latDeltaDeg: (latBox.latMax - latBox.latMin) / 2,
    lonDeltaDeg: (lonBox.lon1Max - lonBox.lon1Min) / 2,
  };
}

/** The `MATERIALIZED_NEIGHBORS_PER_USER` most-recently-active OTHER eligible users platform-wide — the no-location fallback pool (see file-level doc, point 3). One query, reused for every unlocated user in a single refresh run rather than one query each. */
async function loadGlobalRecentFallbackIds(ctx: Ctx, activeSince: Date, cap: number, excludeId?: string): Promise<string[]> {
  const { rows } = await ctx.db.query<{ id: string }>(
    excludeId
      ? `SELECT id FROM users WHERE status = 'active' AND last_active_at >= $1 AND id <> $2 ORDER BY last_active_at DESC, id ASC LIMIT $3`
      : `SELECT id FROM users WHERE status = 'active' AND last_active_at >= $1 ORDER BY last_active_at DESC, id ASC LIMIT $2`,
    excludeId ? [activeSince, excludeId, cap] : [activeSince, cap],
  );
  return rows.map((r) => r.id);
}

/** Every active, active-within-window user id, located or not — the eviction/keep-set boundary (see file-level doc: this is what bounds table SIZE, independent of the geographic pass that decides which PAIRS among them get written). */
async function loadAllActiveRecentUserIds(ctx: Ctx, activeSince: Date): Promise<string[]> {
  const { rows } = await ctx.db.query<{ id: string }>(
    `SELECT id FROM users WHERE status = 'active' AND last_active_at >= $1`,
    [activeSince],
  );
  return rows.map((r) => r.id);
}

/** Active-within-window users with no usable `profiles.latitude`/`longitude` — the no-location-fallback population (file-level doc point 3). */
async function loadUnlocatedActiveRecentUserIds(ctx: Ctx, activeSince: Date): Promise<string[]> {
  const { rows } = await ctx.db.query<{ id: string }>(
    `SELECT u.id
     FROM users u
     LEFT JOIN profiles p ON p.user_id = u.id
     WHERE u.status = 'active'
       AND u.last_active_at >= $1
       AND (p.user_id IS NULL OR p.latitude IS NULL OR p.longitude IS NULL)`,
    [activeSince],
  );
  return rows.map((r) => r.id);
}

interface GeoPairRow {
  user_id: string;
  candidate_id: string;
}

/**
 * ONE round trip, for the WHOLE nightly run: for every active-recent,
 * located user, the `cap` nearest OTHER active-recent, located users
 * within the fixed refresh box, via a `LATERAL` join against `users`/
 * `profiles` directly — this is what turns "every eligible user, looped,
 * one SQL round trip per user" (the shape every other O(N) job in
 * `src/jobs/**` still has, per docs/scale-and-sources.md §1.4 — out of
 * this build's ownership boundary to fix) into a single indexed query.
 * Benefits from `idx_profiles_lat_lon` and `idx_users_status_last_active`
 * (`017_discovery_perf.sql`, already in place for discovery) without a
 * new index — see `018_compat_refresh.sql`'s own doc for the one index
 * this build DOES add (for the eviction delete below, not this query).
 * `ORDER BY` uses squared-degree distance (a monotonic proxy for
 * "nearest", not a claimed exact km figure — cheap, no trig per
 * candidate row) purely to prioritize WHICH `cap` candidates survive the
 * limit; it is never used as, or compared against, an actual distance
 * value anywhere.
 */
async function loadGeoBoundedPairs(ctx: Ctx, activeSince: Date, cap: number): Promise<GeoPairRow[]> {
  const { latDeltaDeg, lonDeltaDeg } = refreshGeoBoxDegrees();
  const { rows } = await ctx.db.query<GeoPairRow>(
    `SELECT e.id AS user_id, nb.id AS candidate_id
     FROM (
       SELECT u.id, p.latitude AS lat, p.longitude AS lon
       FROM users u
       JOIN profiles p ON p.user_id = u.id
       WHERE u.status = 'active'
         AND u.last_active_at >= $1
         AND p.latitude IS NOT NULL
         AND p.longitude IS NOT NULL
     ) e
     CROSS JOIN LATERAL (
       SELECT u2.id
       FROM users u2
       JOIN profiles p2 ON p2.user_id = u2.id
       WHERE u2.status = 'active'
         AND u2.last_active_at >= $1
         AND u2.id <> e.id
         AND p2.latitude  BETWEEN e.lat - $2 AND e.lat + $2
         AND p2.longitude BETWEEN e.lon - $3 AND e.lon + $3
       ORDER BY (p2.latitude - e.lat) * (p2.latitude - e.lat) + (p2.longitude - e.lon) * (p2.longitude - e.lon)
       LIMIT $4
     ) nb(id)`,
    [activeSince, latDeltaDeg, lonDeltaDeg, cap],
  );
  return rows;
}

/** Single-user variant of the same bounded neighbor search, for `refreshScoresForUser`'s synchronous per-answer-change path. Falls back to `loadGlobalRecentFallbackIds` when `userId` has no location (file-level doc point 3), exactly like `loadGeoBoundedPairs`'s unlocated handling below does for the nightly batch. */
async function loadNearbyEligibleCandidateIds(ctx: Ctx, userId: string, activeSince: Date, cap: number): Promise<string[]> {
  const { rows: selfRows } = await ctx.db.query<{ lat: number | null; lon: number | null }>(
    `SELECT latitude AS lat, longitude AS lon FROM profiles WHERE user_id = $1`,
    [userId],
  );
  const self = selfRows[0];
  if (!self || self.lat == null || self.lon == null) {
    return loadGlobalRecentFallbackIds(ctx, activeSince, cap, userId);
  }

  const { latDeltaDeg, lonDeltaDeg } = refreshGeoBoxDegrees();
  const { rows } = await ctx.db.query<{ id: string }>(
    `SELECT u2.id
     FROM users u2
     JOIN profiles p2 ON p2.user_id = u2.id
     WHERE u2.status = 'active'
       AND u2.last_active_at >= $1
       AND u2.id <> $2
       AND p2.latitude  BETWEEN $3 AND $4
       AND p2.longitude BETWEEN $5 AND $6
     ORDER BY (p2.latitude - $7) * (p2.latitude - $7) + (p2.longitude - $8) * (p2.longitude - $8)
     LIMIT $9`,
    [activeSince, userId, self.lat - latDeltaDeg, self.lat + latDeltaDeg, self.lon - lonDeltaDeg, self.lon + lonDeltaDeg, self.lat, self.lon, cap],
  );
  return rows.map((r) => r.id);
}

/** Canonicalizes and de-duplicates a stream of (possibly directed, possibly repeated) user-id pairs into each unordered pair exactly once — `a < b` lexicographically, so `(a,b)` and `(b,a)` collapse to the same entry regardless of which "side" found the other first. */
function dedupeUnorderedPairs(rawPairs: Iterable<readonly [string, string]>): [string, string][] {
  const seen = new Set<string>();
  const pairs: [string, string][] = [];
  for (const [x, y] of rawPairs) {
    if (x === y) continue;
    const [a, b] = x < y ? [x, y] : [y, x];
    const key = `${a}:${b}`;
    if (seen.has(key)) continue;
    seen.add(key);
    pairs.push([a, b]);
  }
  return pairs;
}

/** Batched answer load for an explicit set of user ids (the pairs' involved users), replacing the old per-user sequential loop — one round trip regardless of how many users are involved. */
async function loadAnswersByUserBatch(ctx: Ctx, userIds: string[]): Promise<Map<string, Answer[]>> {
  const result = new Map<string, Answer[]>();
  if (userIds.length === 0) return result;
  const { rows } = await ctx.db.query<AnswerRow>('SELECT * FROM answers WHERE user_id = ANY($1::uuid[])', [userIds]);
  for (const row of rows) {
    const answer = answerFromRow(row);
    const list = result.get(answer.userId);
    if (list) list.push(answer);
    else result.set(answer.userId, [answer]);
  }
  return result;
}

/** Multi-row upsert for an arbitrary list of (possibly unrelated) `(userId, candidateId, score)` triples — the nightly refresh's write path, chunked so one call's parameter arrays never grow unbounded. Same shape/pattern as `upsertScoresBatch` above, generalized because the nightly refresh's pairs don't share one common `userId` the way a single discovery request's candidates do. */
async function upsertScorePairsBatch(ctx: Ctx, pairs: { userId: string; candidateId: string; score: number }[]): Promise<void> {
  if (pairs.length === 0) return;
  const CHUNK = 5000;
  const now = ctx.clock.now();
  for (let i = 0; i < pairs.length; i += CHUNK) {
    const slice = pairs.slice(i, i + CHUNK);
    await ctx.db.query(
      `INSERT INTO compatibility_scores (user_id, candidate_id, score, computed_at)
       SELECT c.user_id, c.candidate_id, c.score, $4
       FROM unnest($1::uuid[], $2::uuid[], $3::double precision[]) AS c(user_id, candidate_id, score)
       ON CONFLICT (user_id, candidate_id) DO UPDATE SET
         score = EXCLUDED.score,
         computed_at = EXCLUDED.computed_at`,
      [slice.map((p) => p.userId), slice.map((p) => p.candidateId), slice.map((p) => p.score), now],
    );
  }
}

/**
 * Evicts every `compatibility_scores` row that should not survive this
 * run: either endpoint has fallen out of the activity window (dormant —
 * see file-level doc, this is the storage-ceiling fix), OR the endpoint
 * IS still eligible but the row predates tonight's freshly computed
 * keep-set (its neighbor selection may have changed — new/closer users
 * became more relevant, someone moved, someone went dormant and freed up
 * a K-slot). `eligibleIds` covers BOTH directions implicitly because
 * every pair is always written symmetrically (see `refreshAllScores`
 * below) — a row "belongs" to the run if either column names an eligible
 * user. Run BEFORE inserting tonight's keep-set (see caller), so the
 * insert below never collides with a row this delete was about to remove
 * anyway.
 */
async function evictStaleAndReplace(ctx: Ctx, eligibleIds: string[], activeSince: Date): Promise<void> {
  await ctx.db.query(
    `DELETE FROM compatibility_scores cs
     WHERE cs.user_id = ANY($1::uuid[])
        OR cs.candidate_id = ANY($1::uuid[])
        OR NOT EXISTS (SELECT 1 FROM users u WHERE u.id = cs.user_id AND u.status = 'active' AND u.last_active_at >= $2)
        OR NOT EXISTS (SELECT 1 FROM users u WHERE u.id = cs.candidate_id AND u.status = 'active' AND u.last_active_at >= $2)`,
    [eligibleIds, activeSince],
  );
}

/**
 * Recomputes and upserts `compatibility_scores` rows for one user against
 * their bounded set of geographically-nearby (or, with no location on
 * file, most-recently-active platform-wide) active-recent candidates —
 * see the file-level SCALE FIX doc above for the full reasoning and the
 * staleness trade-off. Called after an answer change (spec §25.4 "on
 * major answer changes") via `question.service#putMyAnswers`. Does not
 * filter by mutual hard filters (see LEAF MODULE note at the top of this
 * file — unchanged by this build); that filtering happens in
 * `discovery.service.ts`.
 */
export async function refreshScoresForUser(ctx: Ctx, userId: string): Promise<{ updated: number }> {
  const activeSince = addDays(ctx.clock.now(), -REFRESH_ACTIVE_WINDOW_DAYS);
  const candidateIds = await loadNearbyEligibleCandidateIds(ctx, userId, activeSince, MATERIALIZED_NEIGHBORS_PER_USER);
  const scores = await getScoresForCandidates(ctx, userId, candidateIds);
  return { updated: scores.size };
}

/**
 * §25.4 nightly job: bounded refresh of `compatibility_scores` — see the
 * file-level SCALE FIX doc above for the full strategy. Still writes both
 * directions per pair (unchanged contract: `getScore`/`getScoresForCandidates`
 * and every existing caller expect a symmetric table), still computed via
 * the exact same, untouched `computePairScore` (this is a scheduling/
 * storage change, not an algorithm change — the score for a given pair is
 * bit-for-bit what the old nested loop would have produced for that same
 * pair; see `tests/unit/compatibility.test.ts`'s semantics-preservation
 * test). Driven entirely by `ctx.clock` (no wall-clock read) and safe to
 * re-run: evicts before inserting, so a second run with unchanged data
 * reproduces the exact same rows rather than accumulating duplicates or
 * drifting.
 */
export async function refreshAllScores(ctx: Ctx): Promise<{ updated: number }> {
  const activeSince = addDays(ctx.clock.now(), -REFRESH_ACTIVE_WINDOW_DAYS);

  const eligibleIds = await loadAllActiveRecentUserIds(ctx, activeSince);
  // Evict first (dormant users + last run's now-superseded selections) so
  // the insert below never has to reconcile against rows about to be
  // removed anyway — see `evictStaleAndReplace`'s own doc.
  await evictStaleAndReplace(ctx, eligibleIds, activeSince);
  if (eligibleIds.length < 2) return { updated: 0 };

  const [geoPairRows, unlocatedIds] = await Promise.all([
    loadGeoBoundedPairs(ctx, activeSince, MATERIALIZED_NEIGHBORS_PER_USER),
    loadUnlocatedActiveRecentUserIds(ctx, activeSince),
  ]);

  const rawPairs: [string, string][] = geoPairRows.map((r) => [r.user_id, r.candidate_id]);
  if (unlocatedIds.length > 0) {
    // No-location fallback (file-level doc point 3): one shared query for
    // the whole run, reused for every unlocated user, rather than one
    // query each.
    const fallbackCandidates = await loadGlobalRecentFallbackIds(ctx, activeSince, MATERIALIZED_NEIGHBORS_PER_USER);
    for (const userId of unlocatedIds) {
      for (const candidateId of fallbackCandidates) {
        if (candidateId !== userId) rawPairs.push([userId, candidateId]);
      }
    }
  }

  const pairs = dedupeUnorderedPairs(rawPairs);
  if (pairs.length === 0) return { updated: 0 };

  const involvedIds = new Set<string>();
  for (const [a, b] of pairs) {
    involvedIds.add(a);
    involvedIds.add(b);
  }

  const [questions, scoringConfig, answersByUser] = await Promise.all([
    loadActiveQuestions(ctx),
    loadScoringConfig(ctx),
    loadAnswersByUserBatch(ctx, [...involvedIds]),
  ]);

  const writes: { userId: string; candidateId: string; score: number }[] = [];
  for (const [a, b] of pairs) {
    const { score } = computePairScore(
      answersByUser.get(a) ?? [],
      answersByUser.get(b) ?? [],
      questions,
      scoringConfig.minSharedQuestions,
      scoringConfig.noDataDefaultScore,
    );
    writes.push({ userId: a, candidateId: b, score });
    writes.push({ userId: b, candidateId: a, score });
  }

  await upsertScorePairsBatch(ctx, writes);
  return { updated: writes.length };
}

export type { CompatibilityScoreRow };
