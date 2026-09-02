/**
 * Unit tests for compatibility.service.ts.
 *
 * `computePairScore` is pure, most of this file exercises it directly
 * with hand-computed arithmetic against
 * `src/domain/questions/scoring.ts#scoreQuestionContribution`'s documented
 * formula (satisfaction = mean of both directions' handler.satisfaction;
 * weight = baseWeight * mean of both sides' importanceMultiplier) and no
 * I/O. A smaller DB-backed section at the bottom exercises
 * `getScore`/`getScoresForCandidates`/`refreshAllScores` against a real,
 * dedicated Postgres database (`odate_cutover_compat`), following the same
 * pattern as `tests/foundation.test.ts`.
 *
 * CUTOVER: this file used to build `Question`/`Answer` fixtures (the OLD
 * flat 1-5 self/partner-pair bank) and assert against the OLD §16.2
 * formula. `compatibility.service.ts` now scores exclusively from the
 * typed question bank (`question_bank`/`user_question_answers`,
 * db/migrations/008_questions.sql) via
 * `src/domain/questions/scoring.ts#aggregateQuestionScores`, every
 * fixture below is a `QuestionDefinition` + `QuestionAnswerState` instead.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import pg from 'pg';
import { runMigrations } from '../../src/db/migrate.js';
import { closePool, getPool } from '../../src/db/pool.js';
import { ConfigService } from '../../src/config/config.service.js';
import { FlagsService } from '../../src/config/flags.service.js';
import { ManualClock } from '../../src/lib/time.js';
import { createSilentLogger } from '../../src/lib/logger.js';
import { FakeProcessor } from '../../src/services/payments/fake.processor.js';
import { StubMediaModerationAdapter } from '../../src/services/media/stub.adapter.js';
import type { Ctx } from '../../src/lib/ctx.js';
import { addDays } from '../../src/lib/time.js';
import { answeredState } from '../../src/domain/questions/index.js';
import type { QuestionAnswerState, QuestionDefinition } from '../../src/domain/questions/index.js';
import { boundingBoxForRadius, DEFAULT_DISCOVERY_RADIUS_KM } from '../../src/services/filter.service.js';
import {
  computePairScore,
  getScore,
  getScoresForCandidates,
  refreshAllScores,
  DEFAULT_MIN_SHARED_QUESTIONS,
} from '../../src/services/compatibility.service.js';

// =====================================================================
// Fixtures, a `scale` (min=1,max=5) QuestionDefinition, matching the old
// worked-example fixtures' 1-5 shape closely enough to keep the hand-
// computed arithmetic below easy to follow, but going through the real
// typed-bank type system (typeHandlers.ts's scale `satisfaction` is
// `1 - abs(self-pref)/range`, exactly the old per-side satisfaction term).
// =====================================================================

function scaleQuestion(overrides: Partial<QuestionDefinition> & { id: string; baseWeight: number }): QuestionDefinition {
  return {
    slug: overrides.id,
    version: 1,
    category: 'test',
    subcategory: null,
    tags: [],
    questionText: 'test question',
    typeDef: { type: 'scale', min: 1, max: 5, minLabel: 'low', maxLabel: 'high', midLabel: 'mid' },
    presentation: 'value_importance',
    sensitive: false,
    active: true,
    answerRateHint: 0.5,
    ...overrides,
  };
}

/** `answeredState(self, preference, importance)` keyed by question id, the shape `computePairScore` expects (see compatibility.service.ts's own `reKeyAnswersBySlugToCurrentId` doc). */
function answers(pairs: Array<[string, number, number, QuestionAnswerState['importance']]>): Map<string, QuestionAnswerState> {
  const map = new Map<string, QuestionAnswerState>();
  for (const [questionId, self, pref, importance] of pairs) {
    map.set(questionId, answeredState(self, pref, importance!));
  }
  return map;
}

// =====================================================================
// Pure computePairScore tests
// =====================================================================

test('computePairScore: worked 3-question example (hand-computed against scoring.ts\'s documented formula)', () => {
  // Q1, baseWeight 1, importance 'important' both sides (multiplier 1 each).
  //   A: self=5 pref=5. B: self=5 pref=5.
  //   satisfaction(A.self,B.pref) = 1 - |5-5|/4 = 1 ; satisfaction(B.self,A.pref) = 1
  //   satisfaction = (1+1)/2 = 1 ; weight = 1 * (1+1)/2 = 1
  //
  // Q2, baseWeight 1, importance 'important' both sides.
  //   A: self=1 pref=1. B: self=5 pref=5.
  //   satisfaction(A.self=1,B.pref=5) = 1 - 4/4 = 0 ; satisfaction(B.self=5,A.pref=1) = 0
  //   satisfaction = 0 ; weight = 1
  //
  // Q3, baseWeight 3, importance 'important' both sides.
  //   A: self=3 pref=3. B: self=3 pref=3. satisfaction = 1 ; weight = 3
  //
  // score = sum(satisfaction*weight) / sum(weight) = (1*1 + 0*1 + 1*3) / (1+1+3) = 4/5 = 0.8
  const questions = [
    scaleQuestion({ id: 'q1', baseWeight: 1 }),
    scaleQuestion({ id: 'q2', baseWeight: 1 }),
    scaleQuestion({ id: 'q3', baseWeight: 3 }),
  ];
  const a = answers([
    ['q1', 5, 5, 'important'],
    ['q2', 1, 1, 'important'],
    ['q3', 3, 3, 'important'],
  ]);
  const b = answers([
    ['q1', 5, 5, 'important'],
    ['q2', 5, 5, 'important'],
    ['q3', 3, 3, 'important'],
  ]);

  const result = computePairScore(questions, a, b, 1);

  assert.equal(result.sharedAnsweredQuestionCount, 3);
  assert.equal(result.perQuestion.length, 3);
  assert.ok(Math.abs(result.score - 0.8) < 1e-9, `expected 0.8, got ${result.score}`);

  const q1 = result.perQuestion.find((p) => p.questionId === 'q1')!;
  assert.ok(Math.abs(q1.pairSatisfaction - 1) < 1e-9);
  assert.ok(Math.abs(q1.questionWeight - 1) < 1e-9);
  assert.equal(q1.slug, 'q1');

  const q2 = result.perQuestion.find((p) => p.questionId === 'q2')!;
  assert.ok(Math.abs(q2.pairSatisfaction - 0) < 1e-9);
  assert.ok(Math.abs(q2.questionWeight - 1) < 1e-9);

  const q3 = result.perQuestion.find((p) => p.questionId === 'q3')!;
  assert.ok(Math.abs(q3.pairSatisfaction - 1) < 1e-9);
  assert.ok(Math.abs(q3.questionWeight - 3) < 1e-9);
});

test('computePairScore: symmetric under swapping the two users\' argument order', () => {
  const questions = [scaleQuestion({ id: 'q1', baseWeight: 1 }), scaleQuestion({ id: 'q2', baseWeight: 1 })];
  const a = answers([
    ['q1', 2, 5, 'critical'],
    ['q2', 1, 1, 'important'],
  ]);
  const b = answers([
    ['q1', 4, 3, 'important'],
    ['q2', 1, 5, 'important'],
  ]);

  const forward = computePairScore(questions, a, b, 1);
  const backward = computePairScore(questions, b, a, 1);

  assert.ok(
    Math.abs(forward.score - backward.score) < 1e-9,
    `computePairScore(qs,a,b) [${forward.score}] must equal computePairScore(qs,b,a) [${backward.score}]`,
  );
});

test('computePairScore: importance multiplier, a critical preference weighs a question more than an important one, and irrelevant contributes nothing', () => {
  // Two otherwise-identical-satisfaction questions (satisfaction=1 for
  // both), differing only in stated importance.
  //   Q_critical: both sides 'critical' (multiplier 2) -> weight = 1*2 = 2
  //   Q_important: both sides 'important' (multiplier 1) -> weight = 1*1 = 1
  //   Q_irrelevant: either side 'irrelevant' -> EXCLUDED entirely (scoring.ts).
  const questions = [
    scaleQuestion({ id: 'critical', baseWeight: 1 }),
    scaleQuestion({ id: 'important', baseWeight: 1 }),
    scaleQuestion({ id: 'irrelevant', baseWeight: 1 }),
  ];
  const a = answers([
    ['critical', 5, 5, 'critical'],
    ['important', 3, 3, 'important'],
    ['irrelevant', 4, 4, 'irrelevant'],
  ]);
  const b = answers([
    ['critical', 5, 5, 'critical'],
    ['important', 3, 3, 'important'],
    ['irrelevant', 4, 4, 'important'],
  ]);

  const result = computePairScore(questions, a, b, 1);
  const critical = result.perQuestion.find((p) => p.questionId === 'critical')!;
  const important = result.perQuestion.find((p) => p.questionId === 'important')!;

  assert.ok(critical.questionWeight > important.questionWeight, 'a critical preference must weigh more than an important one');
  assert.ok(Math.abs(critical.questionWeight - 2) < 1e-9);
  assert.ok(Math.abs(important.questionWeight - 1) < 1e-9);
  assert.ok(!result.perQuestion.some((p) => p.questionId === 'irrelevant'), '"irrelevant" on either side must exclude the question entirely, not just zero-weight it');
  assert.equal(result.sharedAnsweredQuestionCount, 2);
});

test('computePairScore: deal_breaker is excluded from weighted scoring, never a very-large weight', () => {
  const questions = [scaleQuestion({ id: 'q1', baseWeight: 1 }), scaleQuestion({ id: 'q2', baseWeight: 1 })];
  const a = answers([
    ['q1', 5, 5, 'deal_breaker'],
    ['q2', 3, 3, 'important'],
  ]);
  const b = answers([
    ['q1', 5, 5, 'important'],
    ['q2', 3, 3, 'important'],
  ]);

  const result = computePairScore(questions, a, b, 1);
  assert.ok(!result.perQuestion.some((p) => p.questionId === 'q1'), 'a deal_breaker-importance answer must be EXCLUDED from weighted scoring, not just heavily weighted');
  assert.equal(result.sharedAnsweredQuestionCount, 1);
});

test('computePairScore: too few shared scoreable questions defaults score to 0', () => {
  const questions = [scaleQuestion({ id: 'q1', baseWeight: 1 }), scaleQuestion({ id: 'q2', baseWeight: 1 }), scaleQuestion({ id: 'q3', baseWeight: 1 })];
  // Only q1 is answered by both, 1 shared question, but minSharedQuestions=3.
  const a = answers([
    ['q1', 5, 5, 'important'],
    ['q2', 5, 5, 'important'],
  ]);
  const b = answers([['q1', 5, 5, 'important']]); // q2 not shared (B never answered it)

  const result = computePairScore(questions, a, b, DEFAULT_MIN_SHARED_QUESTIONS);
  assert.equal(result.sharedAnsweredQuestionCount, 1);
  assert.equal(result.score, 0);
});

test('computePairScore: unanswered/skipped/prefer_not_to_say on either side excludes the question from scoring and the shared count', () => {
  const questions = [scaleQuestion({ id: 'q1', baseWeight: 1, sensitive: true }), scaleQuestion({ id: 'q2', baseWeight: 1 }), scaleQuestion({ id: 'q3', baseWeight: 1 })];
  const a = new Map<string, QuestionAnswerState>([
    ['q1', { status: 'prefer_not_to_say', selfValue: null, preferenceValue: null, importance: null }], // A refuses q1
    ['q2', answeredState(5, 5, 'important')],
    ['q3', answeredState(5, 5, 'important')],
  ]);
  const b = new Map<string, QuestionAnswerState>([
    ['q1', answeredState(3, 3, 'important')],
    ['q2', answeredState(5, 5, 'important')],
    ['q3', answeredState(5, 5, 'important')],
    // q3 present but B never got a q1 row at all is covered implicitly,
    // q1 is excluded here purely by A's prefer_not_to_say, regardless of B.
  ]);

  const result = computePairScore(questions, a, b, 2);
  // q1 excluded (A's status isn't 'answered'); q2 and q3 both fully answered -> shared count 2.
  assert.equal(result.sharedAnsweredQuestionCount, 2);
  assert.ok(!result.perQuestion.some((p) => p.questionId === 'q1'));
});

test('computePairScore: a question absent from either user\'s answer map (never shown/never answered) is treated as unanswered, not a crash', () => {
  const questions = [scaleQuestion({ id: 'q1', baseWeight: 1 }), scaleQuestion({ id: 'q2', baseWeight: 1 })];
  const a = answers([['q1', 5, 5, 'important']]); // never touched q2 at all
  const b = answers([
    ['q1', 5, 5, 'important'],
    ['q2', 5, 5, 'important'],
  ]);

  const result = computePairScore(questions, a, b, 1);
  assert.equal(result.sharedAnsweredQuestionCount, 1);
  assert.ok(Math.abs(result.score - 1) < 1e-9);
});

// =====================================================================
// DB-backed tests
// =====================================================================

const BASE_URL = process.env.DATABASE_URL ?? 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';
const TEST_DB_NAME = 'odate_cutover_compat';

function withDbName(url: string, dbName: string): string {
  const u = new URL(url);
  u.pathname = `/${dbName}`;
  return u.toString();
}

let adminPool: pg.Pool;
let pool: pg.Pool;
let ctx: Ctx;

before(async () => {
  adminPool = new pg.Pool({ connectionString: BASE_URL });
  await adminPool.query(`DROP DATABASE IF EXISTS ${TEST_DB_NAME}`);
  await adminPool.query(`CREATE DATABASE ${TEST_DB_NAME}`);

  process.env.DATABASE_URL = withDbName(BASE_URL, TEST_DB_NAME);
  await runMigrations();
  pool = getPool();

  const logger = createSilentLogger();
  const clock = new ManualClock(new Date('2026-06-01T12:00:00Z'));
  ctx = {
    db: pool,
    clock,
    config: new ConfigService(pool, clock, logger),
    flags: new FlagsService(pool, logger),
    logger,
    actor: { type: 'system', job: 'test' },
    payments: new FakeProcessor(),
    media: new StubMediaModerationAdapter(),
  };
});

after(async () => {
  await closePool();
  await adminPool.query(`DROP DATABASE IF EXISTS ${TEST_DB_NAME}`);
  await adminPool.end();
});

async function makeUser(email: string): Promise<string> {
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO users (email, password_hash, birthdate, status) VALUES ($1, 'x', '1995-01-01', 'active') RETURNING id`,
    [email],
  );
  return rows[0]!.id;
}

let qSeq = 0;
/** Inserts a `scale` (min=1,max=5) `question_bank` row and returns its (id, slug). */
async function makeQuestion(baseWeight = 1): Promise<{ id: string; slug: string }> {
  qSeq++;
  const slug = `compat-q-${qSeq}`;
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO question_bank (slug, version, is_current, category, subcategory, tags, question_type, question_text, type_definition, base_weight, sensitive, active, answer_rate_hint)
     VALUES ($1, 1, true, 'test', NULL, '{}', 'scale', $1, $2::jsonb, $3, false, true, 0.5)
     RETURNING id`,
    [slug, JSON.stringify({ type: 'scale', min: 1, max: 5, minLabel: 'low', maxLabel: 'high', midLabel: 'mid' }), baseWeight],
  );
  return { id: rows[0]!.id, slug };
}

async function setAnswer(userId: string, slug: string, questionBankId: string, selfValue: number, partnerValue: number): Promise<void> {
  await pool.query(
    `INSERT INTO user_question_answers (user_id, question_slug, question_bank_id, status, self_value, preference_value, importance, answered_at, updated_at)
     VALUES ($1, $2, $3, 'answered', $4::jsonb, $5::jsonb, 'important', now(), now())`,
    [userId, slug, questionBankId, JSON.stringify(selfValue), JSON.stringify(partnerValue)],
  );
}

/** Like `makeUser`, but also gives the user a located profile and an explicit `last_active_at`, what the bounded refresh (see compatibility.service.ts's SCALE FIX doc) needs to consider someone eligible/geographically placeable. */
async function makeUserWithLocation(email: string, lat: number, lon: number, lastActiveAt: Date): Promise<string> {
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO users (email, password_hash, birthdate, status, last_active_at) VALUES ($1, 'x', '1995-01-01', 'active', $2) RETURNING id`,
    [email, lastActiveAt],
  );
  const userId = rows[0]!.id;
  await pool.query(
    `INSERT INTO profiles (user_id, display_name, bio, age, gender, seeking, relationship_intention, profile_completeness, latitude, longitude)
     VALUES ($1, 'Test', 'A long enough bio for completeness purposes.', 25, 'nonbinary', 'everyone', 'long_term', 100, $2, $3)`,
    [userId, lat, lon],
  );
  return userId;
}

test('getScore: computes and upserts a compatibility_scores row for a pair with enough shared questions', async () => {
  const userA = await makeUser('compat-a@test.local');
  const userB = await makeUser('compat-b@test.local');
  const qs = await Promise.all([makeQuestion(), makeQuestion(), makeQuestion()]);
  for (const q of qs) {
    await setAnswer(userA, q.slug, q.id, 5, 5);
    await setAnswer(userB, q.slug, q.id, 5, 5);
  }

  const score = await getScore(ctx, userA, userB);
  assert.ok(Math.abs(score - 1) < 1e-9, `perfectly matched answers should score 1, got ${score}`);

  const { rows } = await pool.query<{ score: number }>(
    'SELECT score FROM compatibility_scores WHERE user_id = $1 AND candidate_id = $2',
    [userA, userB],
  );
  assert.equal(rows.length, 1);
  assert.ok(Math.abs(rows[0]!.score - 1) < 1e-9);
});

test('getScore: a deal-breaker mismatch scores like any other excluded question, hard exclusion happens in filter.service.ts, not here', async () => {
  const userA = await makeUser('compat-db-a@test.local');
  const userB = await makeUser('compat-db-b@test.local');
  const qs = await Promise.all([makeQuestion(), makeQuestion(), makeQuestion()]);
  for (const q of qs) {
    await setAnswer(userA, q.slug, q.id, 5, 5);
    await setAnswer(userB, q.slug, q.id, 5, 5);
  }
  // Overwrite one question as a deal breaker on A's side.
  await pool.query(
    `UPDATE user_question_answers SET importance = 'deal_breaker' WHERE user_id = $1 AND question_slug = $2`,
    [userA, qs[0]!.slug],
  );

  // Fewer than DEFAULT_MIN_SHARED_QUESTIONS(3) scoreable questions remain (2), so score defaults to 0,
  // proving the deal breaker was excluded from the weighted average rather than counted as a perfect or terrible term.
  const score = await getScore(ctx, userA, userB);
  assert.equal(score, 0);
});

test('getScoresForCandidates: batches multiple candidates and upserts each row', async () => {
  const viewer = await makeUser('batch-viewer@test.local');
  const c1 = await makeUser('batch-c1@test.local');
  const c2 = await makeUser('batch-c2@test.local');
  const qs = await Promise.all([makeQuestion(), makeQuestion(), makeQuestion()]);
  for (const q of qs) {
    await setAnswer(viewer, q.slug, q.id, 5, 5);
    await setAnswer(c1, q.slug, q.id, 5, 5); // perfect match
    await setAnswer(c2, q.slug, q.id, 1, 1); // worst match
  }

  const scores = await getScoresForCandidates(ctx, viewer, [c1, c2]);
  assert.equal(scores.size, 2);
  assert.ok(scores.get(c1)! > scores.get(c2)!, 'c1 (matching) should score higher than c2 (opposite)');
});

// =====================================================================
// Bounded-refresh tests (this build's SCALE FIX, see compatibility.service.ts's
// file-level doc). Perf/scale is measured separately in
// tests/perf/compatRefresh.perf.test.ts; these prove the four hard
// requirements at DB-verifiable (not just estimated) scale: semantics
// unchanged, the cold path works, eviction bounds storage, and re-running
// is idempotent.
// =====================================================================

test('refreshAllScores: materialized scores match computePairScore run directly on the same inputs (semantics-preservation proof), and a geographically distant pair is left for the cold path', async () => {
  const now = ctx.clock.now();
  // Three users clustered in New York (well within the default refresh radius of each other).
  const near1 = await makeUserWithLocation('sem-near1@test.local', 40.7128, -74.006, now);
  const near2 = await makeUserWithLocation('sem-near2@test.local', 40.72, -74.01, now);
  const near3 = await makeUserWithLocation('sem-near3@test.local', 40.7, -73.99, now);
  // One user in Sydney, thousands of km outside the default refresh radius of the New York cluster.
  const far = await makeUserWithLocation('sem-far@test.local', -33.8688, 151.2093, now);

  const qs = await Promise.all([makeQuestion(1), makeQuestion(2), makeQuestion(1)]);
  const questions: QuestionDefinition[] = qs.map((q, i) => scaleQuestion({ id: q.id, baseWeight: [1, 2, 1][i]! }));
  // Re-key by the REAL question_bank id (scaleQuestion's `id` param IS the id here).
  for (let i = 0; i < questions.length; i++) questions[i]!.slug = qs[i]!.slug;

  const raw: Record<string, [number, number][]> = {
    [near1]: [[5, 4], [2, 3], [4, 5]],
    [near2]: [[3, 5], [4, 2], [5, 1]],
    [near3]: [[1, 1], [5, 5], [2, 4]],
    [far]: [[4, 4], [1, 2], [3, 3]],
  };
  for (const [userId, values] of Object.entries(raw)) {
    for (let i = 0; i < qs.length; i++) {
      await setAnswer(userId, qs[i]!.slug, qs[i]!.id, values[i]![0]!, values[i]![1]!);
    }
  }
  function answersFor(userId: string): Map<string, QuestionAnswerState> {
    const map = new Map<string, QuestionAnswerState>();
    for (let i = 0; i < qs.length; i++) {
      const [self, pref] = raw[userId]![i]!;
      map.set(qs[i]!.id, answeredState(self, pref, 'important'));
    }
    return map;
  }

  await refreshAllScores(ctx);

  // Every pair within the New York cluster must be materialized, BOTH
  // directions, and must match `computePairScore` invoked directly on the
  // exact same inputs, proving the bounded refresh's SQL/orchestration
  // routes the right two users' answers into the unchanged scoring
  // formula, not just that the formula itself is correct (already covered
  // by the pure tests above).
  for (const [a, b] of [[near1, near2], [near1, near3], [near2, near3]] as const) {
    const expected = computePairScore(questions, answersFor(a), answersFor(b), DEFAULT_MIN_SHARED_QUESTIONS).score;
    const { rows: fwd } = await pool.query<{ score: number }>(
      'SELECT score FROM compatibility_scores WHERE user_id = $1 AND candidate_id = $2',
      [a, b],
    );
    const { rows: bwd } = await pool.query<{ score: number }>(
      'SELECT score FROM compatibility_scores WHERE user_id = $1 AND candidate_id = $2',
      [b, a],
    );
    assert.equal(fwd.length, 1, `${a} -> ${b} should be materialized by the bounded refresh (both geographically near)`);
    assert.equal(bwd.length, 1, `${b} -> ${a} should be materialized (symmetric)`);
    assert.ok(Math.abs(fwd[0]!.score - expected) < 1e-9, `forward score mismatch: got ${fwd[0]!.score}, expected ${expected}`);
    assert.ok(Math.abs(bwd[0]!.score - expected) < 1e-9, `backward score mismatch: got ${bwd[0]!.score}, expected ${expected}`);
  }

  // The geographically distant (Sydney) pair must NOT be pre-materialized
  // by the bounded nightly refresh, this is the whole point of the
  // bound, and the thing this test would catch regressing back to
  // unbounded O(n^2) behavior.
  const { rows: farRowBefore } = await pool.query(
    'SELECT 1 FROM compatibility_scores WHERE user_id = $1 AND candidate_id = $2',
    [near1, far],
  );
  assert.equal(farRowBefore.length, 0, 'a geographically distant pair must not be pre-materialized by the bounded nightly refresh');

  // COLD PATH: it must still be exactly scoreable on demand (hard
  // requirement, "anything evicted or never materialized must still be
  // scoreable on demand"), and the on-demand value must match the exact
  // same pure computation used above.
  const expectedFar = computePairScore(questions, answersFor(near1), answersFor(far), DEFAULT_MIN_SHARED_QUESTIONS).score;
  const onDemand = await getScore(ctx, near1, far);
  assert.ok(Math.abs(onDemand - expectedFar) < 1e-9, `cold-path on-demand score mismatch: got ${onDemand}, expected ${expectedFar}`);

  // ...and computing it on demand must warm the cache as a side effect
  // (getScore's documented contract, unchanged by this build).
  const { rows: farRowAfter } = await pool.query<{ score: number }>(
    'SELECT score FROM compatibility_scores WHERE user_id = $1 AND candidate_id = $2',
    [near1, far],
  );
  assert.equal(farRowAfter.length, 1, 'on-demand getScore must upsert the row as a caching side effect once computed');
  assert.ok(Math.abs(farRowAfter[0]!.score - expectedFar) < 1e-9);
});

test('refreshAllScores: idempotent re-run, and a user who falls outside the activity window has every materialized row evicted', async () => {
  const clock = ctx.clock as ManualClock;
  const now = clock.now();
  const a = await makeUserWithLocation('evict-a@test.local', 34.0522, -118.2437, now); // Los Angeles
  const b = await makeUserWithLocation('evict-b@test.local', 34.05, -118.25, now); // Los Angeles, near a

  const qs = await Promise.all([makeQuestion(), makeQuestion(), makeQuestion()]);
  for (const q of qs) {
    await setAnswer(a, q.slug, q.id, 4, 4);
    await setAnswer(b, q.slug, q.id, 4, 4);
  }

  const countTouching = async (userId: string): Promise<number> => {
    const { rows } = await pool.query<{ count: string }>(
      'SELECT count(*)::text AS count FROM compatibility_scores WHERE user_id = $1 OR candidate_id = $1',
      [userId],
    );
    return Number(rows[0]!.count);
  };

  const first = await refreshAllScores(ctx);
  assert.ok(first.updated >= 2, 'the near pair must be materialized, both directions');
  const countAfterFirst = await countTouching(a);
  assert.ok(countAfterFirst >= 1);

  const { rows: scoreRows } = await pool.query<{ score: number }>(
    'SELECT score FROM compatibility_scores WHERE user_id = $1 AND candidate_id = $2',
    [a, b],
  );
  assert.equal(scoreRows.length, 1);
  assert.ok(Math.abs(scoreRows[0]!.score - 1) < 1e-9, 'identical answers on every shared question -> perfect satisfaction');

  // Re-running with an UNCHANGED clock and unchanged data must be
  // idempotent: same row count, same score, driven entirely by
  // `ctx.clock` (hard requirement: "idempotent and safe to re-run, driven
  // by ctx.clock").
  await refreshAllScores(ctx);
  const countAfterSecond = await countTouching(a);
  assert.equal(countAfterSecond, countAfterFirst, 're-running with unchanged data must not accumulate duplicate rows');
  const { rows: scoreRowsAfterRerun } = await pool.query<{ score: number }>(
    'SELECT score FROM compatibility_scores WHERE user_id = $1 AND candidate_id = $2',
    [a, b],
  );
  assert.ok(Math.abs(scoreRowsAfterRerun[0]!.score - 1) < 1e-9);

  // Move the clock forward past the activity window, `a`/`b`'s
  // `last_active_at` (fixed at the earlier `now`) is now stale, so both
  // fall out of eligibility. Every row touching either of them must be
  // evicted, not merely left un-refreshed (hard requirement: this is what
  // keeps `compatibility_scores`'s size bounded by the ACTIVE population
  // rather than the platform's total historical user count, see
  // compatibility.service.ts's file-level SCALE FIX doc).
  clock.advanceDays(45);
  await refreshAllScores(ctx);
  assert.equal(await countTouching(a), 0, 'a user who fell outside the activity window must have every materialized row evicted');
  assert.equal(await countTouching(b), 0, 'same for their formerly-near partner, once they too are outside the window');
});

test('refreshAllScores: writes symmetric rows for every active pair', async () => {
  const u1 = await makeUser('refresh-1@test.local');
  const u2 = await makeUser('refresh-2@test.local');
  const qs = await Promise.all([makeQuestion(), makeQuestion(), makeQuestion()]);
  for (const q of qs) {
    await setAnswer(u1, q.slug, q.id, 4, 4);
    await setAnswer(u2, q.slug, q.id, 2, 2);
  }

  const { updated } = await refreshAllScores(ctx);
  assert.ok(updated >= 2);

  const { rows: forward } = await pool.query<{ score: number }>(
    'SELECT score FROM compatibility_scores WHERE user_id = $1 AND candidate_id = $2',
    [u1, u2],
  );
  const { rows: backward } = await pool.query<{ score: number }>(
    'SELECT score FROM compatibility_scores WHERE user_id = $1 AND candidate_id = $2',
    [u2, u1],
  );
  assert.equal(forward.length, 1);
  assert.equal(backward.length, 1);
  assert.ok(Math.abs(forward[0]!.score - backward[0]!.score) < 1e-9, 'score must be symmetric between the two directions');
});

// =====================================================================
// Block-refresh grouping tests (matrix scoring adoption, see
// compatibility.service.ts's BLOCK REFRESH doc). These exercise the ONE
// thing that changed about `refreshAllScores`, how the already-selected
// pairs get GROUPED for batched scoring, not which pairs get selected
// (that SQL is untouched, see `loadGeoBoundedPairs`'s own doc).
// =====================================================================

/**
 * The same lat-delta the internal scoring-bucket grid uses (cell size =
 * `2 * latDeltaDeg`, see `bucketRowsByLocation`'s call site in
 * `refreshAllScores`), computed here independently via the same public,
 * pure `boundingBoxForRadius` helper compatibility.service.ts itself
 * calls, so this test can choose coordinates that provably straddle a
 * grid line without importing any internal (unexported) constant.
 */
function scoringCellLatSizeDeg(): number {
  const box = boundingBoxForRadius(0, 0, DEFAULT_DISCOVERY_RADIUS_KM);
  return box.latMax - box.latMin; // (latMax - latMin) is already the full cell size, latDeltaDeg is half of it.
}

test('refreshAllScores: a candidate pair whose two users land in different scoring buckets (grid-cell boundary) is still materialized, both directions, matching computePairScore exactly', async () => {
  const now = ctx.clock.now();
  const cellLatSize = scoringCellLatSizeDeg();
  // An arbitrary grid line the scoring-batch grid actually uses (any
  // multiple of the cell size), then two users placed a few kilometres on
  // either side of it, well inside the refresh radius of each other, but,
  // by construction, in different `floor(lat / cellLatSize)` buckets.
  const boundaryLat = 3 * cellLatSize;
  const lat1 = boundaryLat - 0.05;
  const lat2 = boundaryLat + 0.05;
  assert.notEqual(
    Math.floor(lat1 / cellLatSize),
    Math.floor(lat2 / cellLatSize),
    'sanity: the two coordinates chosen for this test must actually fall in different scoring buckets, or this test exercises nothing',
  );
  // A quiet corner of the globe no other test in this file (or its shared,
  // accumulating fixture database) places a user near, so this test's
  // geographic isolation, and therefore its pair-set assertions, cannot be
  // contaminated by another test's users.
  const lon = 12.5;

  const edgeA = await makeUserWithLocation('edge-a@test.local', lat1, lon, now);
  const edgeB = await makeUserWithLocation('edge-b@test.local', lat2, lon, now);
  // A control, geographically distant from both (same latitude band, tens
  // of degrees of longitude away): it must NOT be materialized as a
  // candidate of either just because a refresh run touches it too.
  const farControl = await makeUserWithLocation('edge-far@test.local', lat1, lon + 40, now);

  const qs = await Promise.all([makeQuestion(1), makeQuestion(2)]);
  const questions: QuestionDefinition[] = qs.map((q, i) => scaleQuestion({ id: q.id, baseWeight: [1, 2][i]! }));
  const raw: Record<string, [number, number][]> = {
    [edgeA]: [[5, 2], [1, 4]],
    [edgeB]: [[3, 4], [5, 1]],
    [farControl]: [[2, 2], [3, 3]],
  };
  for (const [userId, values] of Object.entries(raw)) {
    for (let i = 0; i < qs.length; i++) {
      await setAnswer(userId, qs[i]!.slug, qs[i]!.id, values[i]![0]!, values[i]![1]!);
    }
  }
  function answersFor(userId: string): Map<string, QuestionAnswerState> {
    const map = new Map<string, QuestionAnswerState>();
    for (let i = 0; i < qs.length; i++) {
      const [self, pref] = raw[userId]![i]!;
      map.set(qs[i]!.id, answeredState(self, pref, 'important'));
    }
    return map;
  }

  await refreshAllScores(ctx);

  const expected = computePairScore(questions, answersFor(edgeA), answersFor(edgeB), DEFAULT_MIN_SHARED_QUESTIONS).score;
  const { rows: fwd } = await pool.query<{ score: number }>(
    'SELECT score FROM compatibility_scores WHERE user_id = $1 AND candidate_id = $2',
    [edgeA, edgeB],
  );
  const { rows: bwd } = await pool.query<{ score: number }>(
    'SELECT score FROM compatibility_scores WHERE user_id = $1 AND candidate_id = $2',
    [edgeB, edgeA],
  );
  assert.equal(fwd.length, 1, 'a pair straddling a scoring-bucket boundary must still be materialized (row user_id=edgeA)');
  assert.equal(bwd.length, 1, 'and the symmetric direction too');
  assert.ok(Math.abs(fwd[0]!.score - expected) < 1e-9, `forward score mismatch: got ${fwd[0]!.score}, expected ${expected}`);
  assert.ok(Math.abs(bwd[0]!.score - expected) < 1e-9, `backward score mismatch: got ${bwd[0]!.score}, expected ${expected}`);

  const { rows: farRow } = await pool.query(
    'SELECT 1 FROM compatibility_scores WHERE user_id = $1 AND candidate_id = $2',
    [edgeA, farControl],
  );
  assert.equal(farRow.length, 0, 'a geographically distant control must not be materialized just because a refresh run also touched it');
});

/** Canonical, order-independent key for comparing unordered user-id pairs, mirrors `compatibility.service.ts#pairKey` (not exported) so this test's own independent bookkeeping stays consistent. */
function testPairKey(a: string, b: string): string {
  return a < b ? `${a}:${b}` : `${b}:${a}`;
}

/**
 * An INDEPENDENT reference implementation of "the `cap` nearest other
 * users within the fixed refresh box", brute force, O(n^2), no SQL, no
 * grid, no bucketing, reusing none of compatibility.service.ts's internal
 * code, this is what makes the comparison below meaningful rather than
 * tautological: it exercises exactly the geometric relationship
 * `loadGeoBoundedPairs`'s SQL is supposed to implement, computed a
 * completely different way, using only the pure, exported
 * `boundingBoxForRadius`.
 */
function bruteForceGeoPairs(users: { id: string; lat: number; lon: number }[], latDeltaDeg: number, lonDeltaDeg: number, cap: number): Set<string> {
  const pairs = new Set<string>();
  for (const u of users) {
    const nearest = users
      .filter((v) => v.id !== u.id)
      .filter((v) => v.lat >= u.lat - latDeltaDeg && v.lat <= u.lat + latDeltaDeg && v.lon >= u.lon - lonDeltaDeg && v.lon <= u.lon + lonDeltaDeg)
      .map((v) => ({ id: v.id, d2: (v.lat - u.lat) * (v.lat - u.lat) + (v.lon - u.lon) * (v.lon - u.lon) }))
      .sort((x, y) => x.d2 - y.d2 || (x.id < y.id ? -1 : x.id > y.id ? 1 : 0))
      .slice(0, cap);
    for (const c of nearest) pairs.add(testPairKey(u.id, c.id));
  }
  return pairs;
}

test('refreshAllScores: the materialized geo-bounded pair set matches an independent brute-force reference exactly (old-shape vs new-shape agreement)', async () => {
  const now = ctx.clock.now();
  const cap = 50; // MATERIALIZED_NEIGHBORS_PER_USER, not exported; every cluster below stays well under it, so capping never trims this fixture (the LIMIT itself is unchanged SQL, not something this build's grouping could affect either way).

  // A quiet, geographically isolated part of the globe (see the boundary
  // test above for why isolation matters in this file's shared, DB):
  // three clusters, well over 500km apart from each other and from every
  // other coordinate any other test in this file uses, so this test's own
  // brute-force reference is a closed, exact answer for these users, not
  // an approximation of it.
  const clusterCenters = [
    { name: 'A', lat: 2.0, lon: 2.0 },
    { name: 'B', lat: 2.0, lon: 10.0 },
    { name: 'C', lat: -8.0, lon: 2.0 },
  ];
  const located: { id: string; lat: number; lon: number }[] = [];
  for (const c of clusterCenters) {
    for (let i = 0; i < 4; i++) {
      const lat = c.lat + (i - 1.5) * 0.05;
      const lon = c.lon + (i - 1.5) * 0.05;
      const id = await makeUserWithLocation(`pairset-${c.name}-${i}@test.local`, lat, lon, now);
      located.push({ id, lat, lon });
    }
  }
  // A straggler close enough to cluster A's edge to be a real candidate of
  // at least some of its members (deliberately not part of the tight
  // in-cluster jitter above), exercising the same "close but not in the
  // same tight group" shape as the dedicated boundary test, inside a
  // larger, noisier fixture this time.
  const stragglerLoc = { lat: clusterCenters[0]!.lat + 0.9, lon: clusterCenters[0]!.lon + 0.9 };
  const stragglerId = await makeUserWithLocation('pairset-straggler@test.local', stragglerLoc.lat, stragglerLoc.lon, now);
  located.push({ id: stragglerId, ...stragglerLoc });
  // A genuine outlier: within the same broad region but far enough (many
  // hundreds of km) that it must not be anyone's candidate.
  const outlierLoc = { lat: 60.0, lon: 60.0 };
  const outlierId = await makeUserWithLocation('pairset-outlier@test.local', outlierLoc.lat, outlierLoc.lon, now);
  located.push({ id: outlierId, ...outlierLoc });

  const unlocatedIds: string[] = [];
  for (let i = 0; i < 3; i++) {
    unlocatedIds.push(await makeUser(`pairset-unlocated-${i}@test.local`));
  }

  await refreshAllScores(ctx);

  // ---- GEO portion: exact set equality against the independent brute-force reference. ----
  const latBox = boundingBoxForRadius(0, 0, DEFAULT_DISCOVERY_RADIUS_KM);
  const latDeltaDeg = (latBox.latMax - latBox.latMin) / 2;
  // 60 here mirrors compatibility.service.ts's own SAFE_REFERENCE_LATITUDE_FOR_BOX_WIDTH_DEG
  // (not exported; a fixed, documented reference latitude, not derived from
  // this fixture's own coordinates), so this reference box matches the
  // production one exactly rather than approximately.
  const lonBox = boundingBoxForRadius(60, 0, DEFAULT_DISCOVERY_RADIUS_KM);
  const lonDeltaDeg = (lonBox.lon1Max - lonBox.lon1Min) / 2;
  const expectedGeoPairs = bruteForceGeoPairs(located, latDeltaDeg, lonDeltaDeg, cap);

  const locatedIds = located.map((u) => u.id);
  const { rows: geoRows } = await pool.query<{ user_id: string; candidate_id: string }>(
    'SELECT user_id, candidate_id FROM compatibility_scores WHERE user_id = ANY($1::uuid[]) AND candidate_id = ANY($1::uuid[])',
    [locatedIds],
  );
  const materializedGeoPairs = new Set(geoRows.map((r) => testPairKey(r.user_id, r.candidate_id)));

  const missing = [...expectedGeoPairs].filter((k) => !materializedGeoPairs.has(k));
  const extra = [...materializedGeoPairs].filter((k) => !expectedGeoPairs.has(k));
  assert.deepEqual(missing, [], `pairs the brute-force reference expects but the block refresh did not materialize: ${missing.join(', ')}`);
  assert.deepEqual(extra, [], `pairs the block refresh materialized but the brute-force reference does not expect: ${extra.join(', ')}`);

  // Sanity: the fixture actually exercises something (in-cluster pairs
  // present, the outlier present for nobody), not a vacuous empty-set match.
  assert.ok(expectedGeoPairs.size > 0);
  assert.ok(materializedGeoPairs.has(testPairKey(located[0]!.id, located[1]!.id)), 'sanity: cluster A members must be candidates of each other');
  assert.ok(!materializedGeoPairs.has(testPairKey(outlierId, located[0]!.id)), 'the outlier must not be a candidate of anyone');

  // ---- FALLBACK (unlocated) portion: presence-only check, not exact
  // set equality. `loadGlobalRecentFallbackIds` (unchanged by this build)
  // draws from the WHOLE platform's active-recent users, which in this
  // shared, accumulating test-fixture database includes users created by
  // EARLIER tests in this file, so an exact-set comparison here would be
  // asserting facts about other tests' fixtures, not about this build's
  // grouping logic. What IS specific to this build, and what this checks:
  // every one of THIS test's unlocated users must have been paired with
  // the platform's actual top-recently-active list, the same real query
  // `loadGlobalRecentFallbackIds` runs, reproduced here only to know what
  // to check for, not as an independent oracle. ----
  const activeSince = addDays(ctx.clock.now(), -30); // REFRESH_ACTIVE_WINDOW_DAYS, not exported; matches compatibility.service.ts's own constant, documented there.
  const { rows: fallbackRows } = await pool.query<{ id: string }>(
    `SELECT id FROM users WHERE status = 'active' AND last_active_at >= $1 ORDER BY last_active_at DESC, id ASC LIMIT $2`,
    [activeSince, cap],
  );
  const fallbackIds = fallbackRows.map((r) => r.id);
  assert.ok(fallbackIds.length > 0, 'sanity: the platform-wide fallback pool must be non-empty for this assertion to mean anything');
  for (const u of unlocatedIds) {
    const { rows: touching } = await pool.query<{ user_id: string; candidate_id: string }>(
      'SELECT user_id, candidate_id FROM compatibility_scores WHERE user_id = $1',
      [u],
    );
    const materializedForU = new Set(touching.map((r) => r.candidate_id));
    const expectedForU = fallbackIds.filter((id) => id !== u);
    const missingForU = expectedForU.filter((id) => !materializedForU.has(id));
    assert.deepEqual(missingForU, [], `unlocated user ${u} is missing expected fallback candidates: ${missingForU.join(', ')}`);
  }
});

// NOTE: "answering a new-bank question refreshes materialized scores" (the
// `refreshScoresForUser` side effect `question.service#putMyQuestionAnswer`
// now triggers) is exercised end-to-end in tests/unit/question.service.test.ts
// and tests/http/questions.test.ts, not here, this file only covers the
// pure/DB primitives compatibility.service.ts itself exports.
