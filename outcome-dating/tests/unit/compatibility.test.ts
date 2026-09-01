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
import type { Answer, Question } from '../../src/domain/types.js';
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
