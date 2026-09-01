/**
 * Unit tests for compatibility.service.ts.
 *
 * `computePairScore` is pure — most of this file exercises it directly
 * with hand-computed arithmetic (worked in comments, matching spec §16.2)
 * and no I/O. A smaller DB-backed section at the bottom exercises
 * `getScore`/`getScoresForCandidates`/`refreshAllScores` against a real,
 * dedicated Postgres database (`outcome_dating_test_compat`), following
 * the same pattern as `tests/foundation.test.ts`.
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
import type { Answer, AnswerValue, Question } from '../../src/domain/types.js';
import {
  computePairScore,
  getScore,
  getScoresForCandidates,
  refreshAllScores,
  DEFAULT_MIN_SHARED_QUESTIONS,
} from '../../src/services/compatibility.service.js';

// =====================================================================
// Fixtures
// =====================================================================

function question(overrides: Partial<Question> & { id: string; weight: number }): Question {
  return {
    slug: overrides.id,
    category: 'test',
    questionText: 'test question',
    selfLeftLabel: 'left',
    selfRightLabel: 'right',
    partnerLeftLabel: 'left',
    partnerRightLabel: 'right',
    polarity: 'standard',
    sensitive: false,
    active: true,
    createdAt: new Date('2026-01-01T00:00:00Z'),
    updatedAt: new Date('2026-01-01T00:00:00Z'),
    ...overrides,
  };
}

function answer(userId: string, questionId: string, selfValue: Answer['selfValue'], partnerValue: Answer['partnerValue']): Answer {
  return { userId, questionId, selfValue, partnerValue, updatedAt: new Date('2026-01-01T00:00:00Z') };
}

// =====================================================================
// Pure computePairScore tests
// =====================================================================

test('computePairScore: worked 3-question example (hand-computed)', () => {
  // Q1 — weight 1, standard polarity. A: self=5 partner=5. B: self=5 partner=5.
  //   satisfaction_A_with_B = 1 - |A.partner(5) - B.self(5)| / 4 = 1 - 0/4 = 1
  //   satisfaction_B_with_A = 1 - |B.partner(5) - A.self(5)| / 4 = 1 - 0/4 = 1
  //   pair_satisfaction = (1 + 1) / 2 = 1
  //   importance_A = 1 + |5 - 3| * 0.25 = 1.5 ; importance_B = 1.5
  //   importance_multiplier = (1.5 + 1.5) / 2 = 1.5
  //   question_weight = base_weight(1) * 1.5 = 1.5
  //
  // Q2 — weight 1, standard polarity. A: self=1 partner=1. B: self=5 partner=5.
  //   satisfaction_A_with_B = 1 - |1 - 5| / 4 = 1 - 1 = 0
  //   satisfaction_B_with_A = 1 - |5 - 1| / 4 = 1 - 1 = 0
  //   pair_satisfaction = 0
  //   importance_A = 1 + |1 - 3| * 0.25 = 1.5 ; importance_B = 1 + |5 - 3| * 0.25 = 1.5
  //   importance_multiplier = 1.5 ; question_weight = 1 * 1.5 = 1.5
  //
  // Q3 — weight 3, standard polarity. A: self=3 partner=3. B: self=3 partner=3.
  //   satisfaction_A_with_B = 1 - |3 - 3| / 4 = 1 ; satisfaction_B_with_A = 1
  //   pair_satisfaction = 1
  //   importance_A = 1 + |3 - 3| * 0.25 = 1 ; importance_B = 1
  //   importance_multiplier = 1 ; question_weight = 3 * 1 = 3
  //
  // compatibility_score = sum(pair_satisfaction * weight) / sum(weight)
  //   = (1*1.5 + 0*1.5 + 1*3) / (1.5 + 1.5 + 3)
  //   = (1.5 + 0 + 3) / 6
  //   = 4.5 / 6
  //   = 0.75
  const questions = [
    question({ id: 'q1', weight: 1 }),
    question({ id: 'q2', weight: 1 }),
    question({ id: 'q3', weight: 3 }),
  ];
  const a: Answer[] = [answer('A', 'q1', 5, 5), answer('A', 'q2', 1, 1), answer('A', 'q3', 3, 3)];
  const b: Answer[] = [answer('B', 'q1', 5, 5), answer('B', 'q2', 5, 5), answer('B', 'q3', 3, 3)];

  const result = computePairScore(a, b, questions, 1);

  assert.equal(result.sharedAnsweredQuestionCount, 3);
  assert.equal(result.perQuestion.length, 3);
  assert.ok(Math.abs(result.score - 0.75) < 1e-9, `expected 0.75, got ${result.score}`);

  const q1 = result.perQuestion.find((p) => p.questionId === 'q1')!;
  assert.ok(Math.abs(q1.pairSatisfaction - 1) < 1e-9);
  assert.ok(Math.abs(q1.questionWeight - 1.5) < 1e-9);

  const q2 = result.perQuestion.find((p) => p.questionId === 'q2')!;
  assert.ok(Math.abs(q2.pairSatisfaction - 0) < 1e-9);
  assert.ok(Math.abs(q2.questionWeight - 1.5) < 1e-9);

  const q3 = result.perQuestion.find((p) => p.questionId === 'q3')!;
  assert.ok(Math.abs(q3.pairSatisfaction - 1) < 1e-9);
  assert.ok(Math.abs(q3.questionWeight - 3) < 1e-9);
});

test('computePairScore: symmetric under swapping the two users\' argument order', () => {
  const questions = [question({ id: 'q1', weight: 1 }), question({ id: 'q2', weight: 1 })];
  const a: Answer[] = [answer('A', 'q1', 2, 5), answer('A', 'q2', 1, 1)];
  const b: Answer[] = [answer('B', 'q1', 4, 3), answer('B', 'q2', 1, 5)];

  const forward = computePairScore(a, b, questions, 1);
  const backward = computePairScore(b, a, questions, 1);

  assert.ok(
    Math.abs(forward.score - backward.score) < 1e-9,
    `computePairScore(a,b) [${forward.score}] must equal computePairScore(b,a) [${backward.score}]`,
  );
  // Sanity: this fixture is specifically constructed so that a *single-sided*
  // (e.g. "always use the first argument's partner_answer") importance-
  // multiplier implementation would NOT be swap-invariant here — a
  // single-sided reading gives 0.625 forward / 0.6 backward, not equal.
  // The averaged-both-sides reading documented in compatibility.service.ts
  // gives ~0.6136 both ways, which is what's asserted above.
});

test('computePairScore: reversed-polarity transform matches mirrored raw values on a standard question', () => {
  // Standard-polarity question with raw values A: self=5 partner=5, B: self=5 partner=5
  // (same as Q1 in the worked example above -> pairSatisfaction=1, weight=1.5).
  const standardQuestions = [question({ id: 'q1', weight: 1, polarity: 'standard' })];
  const standardA: Answer[] = [answer('A', 'q1', 5, 5)];
  const standardB: Answer[] = [answer('B', 'q1', 5, 5)];
  const standardResult = computePairScore(standardA, standardB, standardQuestions, 1);

  // The same question marked `reversed`, fed the *mirrored* raw values
  // (6 - x for every one of the four stored values: 6-5=1). The reversed
  // transform (`transformed = 6 - original`) applied inside computePairScore
  // should exactly undo the mirroring, reproducing the standard-polarity
  // question's pairSatisfaction/weight/score.
  const reversedQuestions = [question({ id: 'q1', weight: 1, polarity: 'reversed' })];
  const reversedA: Answer[] = [answer('A', 'q1', 1, 1)];
  const reversedB: Answer[] = [answer('B', 'q1', 1, 1)];
  const reversedResult = computePairScore(reversedA, reversedB, reversedQuestions, 1);

  assert.ok(Math.abs(reversedResult.score - standardResult.score) < 1e-9);
  assert.ok(
    Math.abs(reversedResult.perQuestion[0]!.pairSatisfaction - standardResult.perQuestion[0]!.pairSatisfaction) < 1e-9,
  );
  assert.ok(
    Math.abs(reversedResult.perQuestion[0]!.questionWeight - standardResult.perQuestion[0]!.questionWeight) < 1e-9,
  );
});

test('computePairScore: importance multiplier — extreme partner preference weighs a question more than a neutral one', () => {
  // Two otherwise-identical-satisfaction questions (pairSatisfaction=1 for
  // both), differing only in how extreme the partner_answer is.
  //   Q_extreme: A.partner=5, B.partner=5 -> importance = (1.5+1.5)/2 = 1.5
  //   Q_neutral: A.partner=3, B.partner=3 -> importance = (1+1)/2 = 1
  const questions = [
    question({ id: 'extreme', weight: 1, polarity: 'standard' }),
    question({ id: 'neutral', weight: 1, polarity: 'standard' }),
  ];
  const a: Answer[] = [answer('A', 'extreme', 5, 5), answer('A', 'neutral', 3, 3)];
  const b: Answer[] = [answer('B', 'extreme', 5, 5), answer('B', 'neutral', 3, 3)];

  const result = computePairScore(a, b, questions, 1);
  const extreme = result.perQuestion.find((p) => p.questionId === 'extreme')!;
  const neutral = result.perQuestion.find((p) => p.questionId === 'neutral')!;

  assert.ok(Math.abs(extreme.pairSatisfaction - 1) < 1e-9);
  assert.ok(Math.abs(neutral.pairSatisfaction - 1) < 1e-9);
  assert.ok(extreme.questionWeight > neutral.questionWeight, 'extreme partner preference must weigh more than neutral');
  assert.ok(Math.abs(extreme.questionWeight - 1.5) < 1e-9);
  assert.ok(Math.abs(neutral.questionWeight - 1) < 1e-9);
});

test('computePairScore: too few shared answered questions defaults score to 0', () => {
  const questions = [
    question({ id: 'q1', weight: 1 }),
    question({ id: 'q2', weight: 1 }),
    question({ id: 'q3', weight: 1 }),
  ];
  // Only q1 is answered by both — 1 shared question, but minSharedQuestions=3.
  const a: Answer[] = [answer('A', 'q1', 5, 5), answer('A', 'q2', 5, 5)]; // q2 not shared (B never answered it)
  const b: Answer[] = [answer('B', 'q1', 5, 5)];

  const result = computePairScore(a, b, questions, DEFAULT_MIN_SHARED_QUESTIONS);
  assert.equal(result.sharedAnsweredQuestionCount, 1);
  assert.equal(result.score, 0);
});

test('computePairScore: null ("prefer not to say") values are excluded from shared count and contribute nothing', () => {
  const questions = [question({ id: 'q1', weight: 1, sensitive: true }), question({ id: 'q2', weight: 1 }), question({ id: 'q3', weight: 1 })];
  const a: Answer[] = [
    answer('A', 'q1', null, 4), // A prefers not to say on q1's self value
    answer('A', 'q2', 5, 5),
    answer('A', 'q3', 5, 5),
  ];
  const b: Answer[] = [
    answer('B', 'q1', 3, 3),
    answer('B', 'q2', 5, 5),
    answer('B', 'q3', 5, 5),
  ];

  const result = computePairScore(a, b, questions, 2);
  // q1 excluded (A.selfValue is null); q2 and q3 both fully answered -> shared count 2.
  assert.equal(result.sharedAnsweredQuestionCount, 2);
  assert.ok(!result.perQuestion.some((p) => p.questionId === 'q1'));
});

// =====================================================================
// DB-backed tests
// =====================================================================

const BASE_URL = process.env.DATABASE_URL ?? 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';
const TEST_DB_NAME = 'outcome_dating_test_compat';

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

async function makeQuestion(slug: string, weight = 1): Promise<string> {
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO questions (slug, category, question_text, self_left_label, self_right_label, partner_left_label, partner_right_label, weight, polarity, sensitive, active)
     VALUES ($1, 'test', $1, 'l', 'r', 'l', 'r', $2, 'standard', false, true)
     RETURNING id`,
    [slug, weight],
  );
  return rows[0]!.id;
}

async function setAnswer(userId: string, questionId: string, selfValue: number, partnerValue: number): Promise<void> {
  await pool.query(
    `INSERT INTO answers (user_id, question_id, self_value, partner_value) VALUES ($1, $2, $3, $4)`,
    [userId, questionId, selfValue, partnerValue],
  );
}

/** Like `makeUser`, but also gives the user a located profile and an explicit `last_active_at` — what the bounded refresh (see compatibility.service.ts's SCALE FIX doc) needs to consider someone eligible/geographically placeable. */
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
  const qs = await Promise.all([makeQuestion('cs-q1'), makeQuestion('cs-q2'), makeQuestion('cs-q3')]);
  for (const q of qs) {
    await setAnswer(userA, q, 5, 5);
    await setAnswer(userB, q, 5, 5);
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

test('getScoresForCandidates: batches multiple candidates and upserts each row', async () => {
  const viewer = await makeUser('batch-viewer@test.local');
  const c1 = await makeUser('batch-c1@test.local');
  const c2 = await makeUser('batch-c2@test.local');
  const qs = await Promise.all([makeQuestion('batch-q1'), makeQuestion('batch-q2'), makeQuestion('batch-q3')]);
  for (const q of qs) {
    await setAnswer(viewer, q, 5, 5);
    await setAnswer(c1, q, 5, 5); // perfect match
    await setAnswer(c2, q, 1, 1); // worst match
  }

  const scores = await getScoresForCandidates(ctx, viewer, [c1, c2]);
  assert.equal(scores.size, 2);
  assert.ok(scores.get(c1)! > scores.get(c2)!, 'c1 (matching) should score higher than c2 (opposite)');
});

// =====================================================================
// Bounded-refresh tests (this build's SCALE FIX — see compatibility.service.ts's
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
  // One user in Sydney — thousands of km outside the default refresh radius of the New York cluster.
  const far = await makeUserWithLocation('sem-far@test.local', -33.8688, 151.2093, now);

  const qIds = await Promise.all([makeQuestion('sem-q1', 1), makeQuestion('sem-q2', 2), makeQuestion('sem-q3', 1)]);
  const weights = [1, 2, 1];
  const questions: Question[] = qIds.map((id, i) => question({ id, weight: weights[i]! }));

  const raw: Record<string, [AnswerValue, AnswerValue][]> = {
    [near1]: [[5, 4], [2, 3], [4, 5]],
    [near2]: [[3, 5], [4, 2], [5, 1]],
    [near3]: [[1, 1], [5, 5], [2, 4]],
    [far]: [[4, 4], [1, 2], [3, 3]],
  };
  for (const [userId, values] of Object.entries(raw)) {
    for (let i = 0; i < qIds.length; i++) {
      await setAnswer(userId, qIds[i]!, values[i]![0]! as number, values[i]![1]! as number);
    }
  }
  function answersFor(userId: string): Answer[] {
    return qIds.map((qId, i) => answer(userId, qId, raw[userId]![i]![0]!, raw[userId]![i]![1]!));
  }

  await refreshAllScores(ctx);

  // Every pair within the New York cluster must be materialized, BOTH
  // directions, and must match `computePairScore` invoked directly on the
  // exact same `Answer[]`/`Question[]` inputs — proving the bounded
  // refresh's SQL/orchestration routes the right two users' answers into
  // the unchanged scoring formula, not just that the formula itself is
  // correct (already covered by the pure tests above).
  for (const [a, b] of [[near1, near2], [near1, near3], [near2, near3]] as const) {
    const expected = computePairScore(answersFor(a), answersFor(b), questions, DEFAULT_MIN_SHARED_QUESTIONS).score;
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
  // by the bounded nightly refresh — this is the whole point of the
  // bound, and the thing this test would catch regressing back to
  // unbounded O(n^2) behavior.
  const { rows: farRowBefore } = await pool.query(
    'SELECT 1 FROM compatibility_scores WHERE user_id = $1 AND candidate_id = $2',
    [near1, far],
  );
  assert.equal(farRowBefore.length, 0, 'a geographically distant pair must not be pre-materialized by the bounded nightly refresh');

  // COLD PATH: it must still be exactly scoreable on demand (hard
  // requirement — "anything evicted or never materialized must still be
  // scoreable on demand"), and the on-demand value must match the exact
  // same pure computation used above.
  const expectedFar = computePairScore(answersFor(near1), answersFor(far), questions, DEFAULT_MIN_SHARED_QUESTIONS).score;
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

  const qs = await Promise.all([makeQuestion('evict-q1'), makeQuestion('evict-q2'), makeQuestion('evict-q3')]);
  for (const q of qs) {
    await setAnswer(a, q, 4, 4);
    await setAnswer(b, q, 4, 4);
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

  // Move the clock forward past the activity window — `a`/`b`'s
  // `last_active_at` (fixed at the earlier `now`) is now stale, so both
  // fall out of eligibility. Every row touching either of them must be
  // evicted, not merely left un-refreshed (hard requirement: this is what
  // keeps `compatibility_scores`'s size bounded by the ACTIVE population
  // rather than the platform's total historical user count — see
  // compatibility.service.ts's file-level SCALE FIX doc).
  clock.advanceDays(45);
  await refreshAllScores(ctx);
  assert.equal(await countTouching(a), 0, 'a user who fell outside the activity window must have every materialized row evicted');
  assert.equal(await countTouching(b), 0, 'same for their formerly-near partner, once they too are outside the window');
});

test('refreshAllScores: writes symmetric rows for every active pair', async () => {
  const u1 = await makeUser('refresh-1@test.local');
  const u2 = await makeUser('refresh-2@test.local');
  const qs = await Promise.all([makeQuestion('refresh-q1'), makeQuestion('refresh-q2'), makeQuestion('refresh-q3')]);
  for (const q of qs) {
    await setAnswer(u1, q, 4, 4);
    await setAnswer(u2, q, 2, 2);
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
