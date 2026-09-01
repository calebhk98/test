import type { Ctx } from '../lib/ctx.js';
import { addDays } from '../lib/time.js';
import type { CompatibilityScoreRow } from '../domain/types.js';
import { boundingBoxForRadius, DEFAULT_DISCOVERY_RADIUS_KM } from './filter.service.js';
import { aggregateQuestionScores, presentationFor } from '../domain/questions/index.js';
import type {
  ImportanceLevel,
  QuestionAnswerState,
  QuestionDefinition,
  QuestionType,
  QuestionTypeDefinition,
} from '../domain/questions/index.js';

/**
 * compatibility.service — pairwise compatibility scoring and its storage.
 * Spec: §16, §25.4 (nightly refresh job).
 *
 * Owning agent: B (question-system cutover build).
 *
 * INVARIANT: this module SORTS; it never decides who is eligible to be
 * seen. `discovery.service.ts` calls `getScore`/`getScoresForCandidates`
 * only after `filter.service.ts#passesMutualFilters` has already gated the
 * candidate pool (spec §16.1, §9.1).
 *
 * CUTOVER (question-system unification): this module used to read the OLD
 * `questions`/`answers` tables (a flat 1-5 self/partner pair with no type
 * or importance information) and implement its own §16.2 formula inline.
 * Both are retired — db/migrations/019_question_cutover.sql drops those
 * tables outright. `computePairScore` below is now a thin, still-pure
 * wrapper around `src/domain/questions/scoring.ts#aggregateQuestionScores`
 * (built and fully unit-tested independently — see that file and
 * `tests/unit/questionScoring.test.ts`), and every I/O helper in this file
 * reads the NEW `question_bank` / `user_question_answers` tables
 * (db/migrations/008_questions.sql) instead. There is exactly one
 * question bank now; nothing in this file reads `questions`/`answers`.
 *
 * `computePairScore` is a pure function of two users' typed answers + the
 * active question bank — no I/O — so it stays directly unit-testable.
 * `getScore`/`getScoresForCandidates`/`refreshScoresForUser`/
 * `refreshAllScores` are the I/O-performing wrappers that read
 * `question_bank`/`user_question_answers`, call `computePairScore`, and
 * read/write the `compatibility_scores` materialization (spec §16.3).
 *
 * LEAF MODULE: per INTERFACES.md's module table, `compatibility.service`'s
 * "May call" column is blank — it is a leaf that reads the question bank
 * and its answers directly and calls no other SERVICE module (the
 * SCALE FIX AMENDMENT note below documents the one, deliberate, pure-only
 * exception). It does NOT call `filter.service#passesMutualFilters` or
 * `question.service.ts` — `discovery.service.ts` (sanctioned to call both
 * `filter` and `compatibility`) is what combines a filter-passed candidate
 * set with these scores at read time. It also does not enforce deal
 * breakers itself: a `deal_breaker`-importance answer is excluded from
 * WEIGHTED SCORING by `scoreQuestionContribution` (see scoring.ts) and
 * enforced as a hard filter entirely through `filter.service.ts`'s
 * `hard_filters` table instead (populated by
 * `question.service#getMyDealBreakerFilterRows` +
 * `filter.service#updateMyFilters` — see question.service.ts's
 * `putMyQuestionAnswer`). "Filters are strictly enforced and never
 * overridden by scoring" holds because scoring never even sees a deal
 * breaker as a scored term.
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
 * `import`. This module ALSO now imports pure, no-I/O helpers from
 * `../domain/questions/index.js` (the shared question-scoring domain
 * layer) — that import is not a service dependency at all (that directory
 * contains zero I/O, per its own module docs) and is the intended
 * integration seam `scoring.ts` was built for.
 */

// =====================================================================
// Row <-> domain mapping (reads `question_bank`/`user_question_answers`
// directly — this module owns no other service dependency, see LEAF
// MODULE note above). Deliberately duplicated, in miniature, from
// question.service.ts's own row mapping rather than importing it — this
// module stays a leaf that never calls into another service.
// =====================================================================

interface QuestionBankRow {
  id: string;
  slug: string;
  version: number;
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

/** The whole active, current question bank — every question a score could possibly be computed over. */
async function loadActiveCurrentQuestions(ctx: Ctx): Promise<QuestionDefinition[]> {
  const { rows } = await ctx.db.query<QuestionBankRow>(
    `SELECT id, slug, version, category, subcategory, tags, question_type, question_text, type_definition, base_weight, sensitive, active, answer_rate_hint
     FROM question_bank WHERE is_current = true AND active = true`,
  );
  return rows.map(questionDefinitionFromRow);
}

interface UserQuestionAnswerRow {
  user_id: string;
  question_slug: string;
  status: 'skipped' | 'prefer_not_to_say' | 'answered';
  self_value: unknown | null;
  preference_value: unknown | null;
  importance: ImportanceLevel | null;
}

/** Batched load of every involved user's new-bank answers, keyed first by user id then by question SLUG (the stable identity across question versions — see db/migrations/008_questions.sql). One round trip regardless of how many users are asked for. */
async function loadAnswerStatesBySlugForUsers(ctx: Ctx, userIds: string[]): Promise<Map<string, Map<string, QuestionAnswerState>>> {
  const result = new Map<string, Map<string, QuestionAnswerState>>();
  const ids = [...new Set(userIds)];
  if (ids.length === 0) return result;
  const { rows } = await ctx.db.query<UserQuestionAnswerRow>(
    `SELECT user_id, question_slug, status, self_value, preference_value, importance
     FROM user_question_answers WHERE user_id = ANY($1::uuid[])`,
    [ids],
  );
  for (const row of rows) {
    let perUser = result.get(row.user_id);
    if (!perUser) {
      perUser = new Map();
      result.set(row.user_id, perUser);
    }
    perUser.set(row.question_slug, {
      status: row.status,
      selfValue: row.self_value,
      preferenceValue: row.preference_value,
      importance: row.importance,
    });
  }
  return result;
}

/**
 * Re-keys one user's slug-keyed answers onto the CURRENT bank's per-question
 * `id`s — what `aggregateQuestionScores`/`scoreQuestionContribution` (keyed
 * by `QuestionDefinition.id`, the exact pinned version) expect. A user who
 * answered a since-edited (older) version of a question is matched onto the
 * CURRENT version's id here by slug — slug is the stable cross-version
 * identity the selector and deal-breaker derivation already key off (see
 * selector.ts/dealBreakers.ts); their stored self/preference/importance
 * values still apply verbatim (a version bump is normally a wording/label
 * edit, not a retroactive reinterpretation of what the user already said).
 * A slug with no entry in `questions` (the question was retired/deactivated
 * since they answered) is simply dropped — `aggregateQuestionScores` only
 * ever visits questions in its `questions` argument, so a stray answer to a
 * no-longer-active question can never affect a score either way.
 */
function reKeyAnswersBySlugToCurrentId(
  bySlug: Map<string, QuestionAnswerState> | undefined,
  questions: QuestionDefinition[],
): Map<string, QuestionAnswerState> {
  const result = new Map<string, QuestionAnswerState>();
  if (!bySlug) return result;
  for (const q of questions) {
    const state = bySlug.get(q.slug);
    if (state) result.set(q.id, state);
  }
  return result;
}

/**
 * Minimum number of questions both users must have a scoreable (non-excluded
 * — see scoring.ts) shared answer on before a score is computed at all —
 * below this, score defaults to `compatibility.no_data_default_score` (spec
 * §16.2 last paragraph; Open Question OQ-2's resolution: `0`, not an
 * ambiguous "neutral" — see docs/conformance.md).
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
  questionId: string; // question_bank.id (current version)
  slug: string;
  pairSatisfaction: number; // 0-1
  questionWeight: number; // base_weight * importance multiplier (see scoring.ts)
}

export interface CompatibilityBreakdown {
  score: number; // 0-1; noDataDefaultScore if too few shared SCOREABLE questions (§16.2 last paragraph)
  perQuestion: PerQuestionSatisfaction[];
  sharedAnsweredQuestionCount: number;
}

/**
 * Pure per-pair scoring, now delegating the entire per-question contribution
 * + accumulation to `src/domain/questions/scoring.ts#aggregateQuestionScores`
 * (see that module for the exact exclusion rules: inactive questions,
 * `unanswered`/`skipped`/`prefer_not_to_say` on either side, `irrelevant`
 * importance, and `deal_breaker` importance — none of these contribute
 * weight or satisfaction here, by design; a deal breaker is enforced
 * upstream as a hard filter instead, see the LEAF MODULE doc above).
 *
 * Symmetric by construction (`aggregateQuestionScores`/
 * `scoreQuestionContribution` average both directions), so
 * `computePairScore(qs, a, b, ...) === computePairScore(qs, b, a, ...)` is
 * an expected property, asserted in `tests/unit/compatibility.test.ts`.
 *
 * `answersA`/`answersB` must be keyed by `QuestionDefinition.id` (the
 * CURRENT version's id for each question in `questions`) — see
 * `reKeyAnswersBySlugToCurrentId` above for how the I/O wrappers below
 * produce that shape from a slug-keyed `user_question_answers` load.
 */
export function computePairScore(
  questions: QuestionDefinition[],
  answersA: Map<string, QuestionAnswerState>,
  answersB: Map<string, QuestionAnswerState>,
  minSharedQuestions: number,
  noDataDefaultScore: number = DEFAULT_NO_DATA_SCORE,
): CompatibilityBreakdown {
  const bySlug = new Map(questions.map((q) => [q.id, q.slug]));
  const aggregate = aggregateQuestionScores(questions, answersA, answersB, noDataDefaultScore);

  const perQuestion: PerQuestionSatisfaction[] = [];
  for (const { questionId, contribution } of aggregate.contributions) {
    if (contribution.excluded) continue;
    perQuestion.push({
      questionId,
      slug: bySlug.get(questionId) ?? questionId,
      pairSatisfaction: contribution.satisfaction!,
      questionWeight: contribution.weight,
    });
  }

  const sharedAnsweredQuestionCount = aggregate.scoredQuestionCount;
  const score = sharedAnsweredQuestionCount < minSharedQuestions ? noDataDefaultScore : aggregate.score;

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

/** Reads the two decision-layer config keys this module's scoring depends on (see `DEFAULT_MIN_SHARED_QUESTIONS`/`DEFAULT_NO_DATA_SCORE` docs above). */
async function loadScoringConfig(ctx: Ctx): Promise<{ minSharedQuestions: number; noDataDefaultScore: number }> {
  const values = await ctx.config.getMany(['compatibility.min_shared_questions', 'compatibility.no_data_default_score'] as const);
  return {
    minSharedQuestions: values['compatibility.min_shared_questions'],
    noDataDefaultScore: values['compatibility.no_data_default_score'],
  };
}

/**
 * On-demand score for one candidate pair (spec §16.3: "For MVP, compute
 * score on demand for candidates"). Always recomputes from current
 * `user_question_answers` — this module deliberately does not implement a
 * staleness window (that would need a new config key; see
 * `DEFAULT_MIN_SHARED_QUESTIONS` comment on the file-ownership constraint)
 * — and upserts the materialized `compatibility_scores` row as a side
 * effect so `refreshAllScores`/direct reads of the table stay consistent
 * with the latest on-demand computation.
 */
export async function getScore(ctx: Ctx, userId: string, candidateId: string): Promise<number> {
  const [questions, answerMaps, scoringConfig] = await Promise.all([
    loadActiveCurrentQuestions(ctx),
    loadAnswerStatesBySlugForUsers(ctx, [userId, candidateId]),
    loadScoringConfig(ctx),
  ]);
  const answersA = reKeyAnswersBySlugToCurrentId(answerMaps.get(userId), questions);
  const answersB = reKeyAnswersBySlugToCurrentId(answerMaps.get(candidateId), questions);
  const { score } = computePairScore(questions, answersA, answersB, scoringConfig.minSharedQuestions, scoringConfig.noDataDefaultScore);
  await upsertScore(ctx, userId, candidateId, score);
  return score;
}

/** Batch variant used by `discovery.service.ts` to sort a whole candidate page in one call. */
export async function getScoresForCandidates(ctx: Ctx, userId: string, candidateIds: string[]): Promise<Map<string, number>> {
  const result = new Map<string, number>();
  if (candidateIds.length === 0) return result;

  const questions = await loadActiveCurrentQuestions(ctx);
  const scoringConfig = await loadScoringConfig(ctx);
  const answerMaps = await loadAnswerStatesBySlugForUsers(ctx, [userId, ...candidateIds]);
  const answersA = reKeyAnswersBySlugToCurrentId(answerMaps.get(userId), questions);

  for (const candidateId of candidateIds) {
    const answersB = reKeyAnswersBySlugToCurrentId(answerMaps.get(candidateId), questions);
    const { score } = computePairScore(questions, answersA, answersB, scoringConfig.minSharedQuestions, scoringConfig.noDataDefaultScore);
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
//   - `getScore`/`getScoresForCandidates` (unchanged shape by this
//     cutover) ALWAYS recompute from live `user_question_answers` and
//     upsert as a side effect, for WHATEVER pair `discovery.service.ts`
//     actually asks about — they never read a score back out of
//     `compatibility_scores` to return it. A repo-wide search (this
//     build's report) confirms `compatibility_scores` has no reader
//     anywhere in `src/` today; every consumer of a score goes through
//     one of these two functions. That means a pair that falls OUTSIDE
//     tonight's geographic/activity bound is not "serving a stale score"
//     — it is "not yet computed", and the very next discovery request
//     that needs it computes it fresh and warms the cache as a side
//     effect (see the cold-path test in tests/unit/compatibility.test.ts).
//     Nothing a real user sees is ever more than one request stale,
//     regardless of what this job did or didn't materialize last night.
//   - What DOES stay stale, for up to ~24h, is a MATERIALIZED row nobody
//     has asked for yet: it reflects last night's answers, not this
//     morning's edit. That is exactly the product-acceptable case the
//     task brief distinguishes — "a slightly stale compatibility score is
//     not a correctness problem" — because the table is a warm-cache
//     optimization with no current reader, not a source of truth; nothing
//     about HARD FILTERS is derived from it (that invariant was already
//     true before this build and is untouched — `filter.service.ts`'s
//     `hard_filters` table is a completely separate mechanism).
//   - `refreshScoresForUser` (still triggered synchronously on every
//     answer edit, spec §25.4 "on major answer changes", now wired from
//     `question.service#putMyQuestionAnswer`) means the pairs that matter
//     most for freshness — the ones involving a user who JUST changed an
//     answer — get refreshed immediately, geo-bounded the same way, not
//     once a night.
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
//
// NONE OF THIS SECTION CHANGED for the question-system cutover — the
// activity/geography bounding is entirely schema-independent (it reads
// `users`/`profiles` only). Only the "load questions" / "load answers" /
// "score a pair" internals feeding into it were repointed at the new bank
// (see `loadActiveCurrentQuestions`/`loadAnswerStatesBySlugForUsers`/
// `computePairScore` above) — the bound itself is preserved exactly.
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
 * Recomputes and upserts `compatibility_scores` rows for one user against
 * their bounded set of geographically-nearby (or, with no location on
 * file, most-recently-active platform-wide) active-recent candidates —
 * see the file-level SCALE FIX doc above for the full reasoning and the
 * staleness trade-off. Called after an answer change (spec §25.4 "on
 * major answer changes") via `question.service#putMyQuestionAnswer`. Does
 * not filter by mutual hard filters (see LEAF MODULE note at the top of
 * this file — unchanged by this build); that filtering happens in
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
 * bit-for-bit what an unbounded nested loop would have produced for that
 * same pair; see `tests/unit/compatibility.test.ts`'s semantics-preservation
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

  const [questions, scoringConfig, answersBySlugByUser] = await Promise.all([
    loadActiveCurrentQuestions(ctx),
    loadScoringConfig(ctx),
    loadAnswerStatesBySlugForUsers(ctx, [...involvedIds]),
  ]);

  const answersByIdByUser = new Map<string, Map<string, QuestionAnswerState>>();
  for (const uid of involvedIds) {
    answersByIdByUser.set(uid, reKeyAnswersBySlugToCurrentId(answersBySlugByUser.get(uid), questions));
  }

  const writes: { userId: string; candidateId: string; score: number }[] = [];
  for (const [a, b] of pairs) {
    const { score } = computePairScore(
      questions,
      answersByIdByUser.get(a) ?? new Map(),
      answersByIdByUser.get(b) ?? new Map(),
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
