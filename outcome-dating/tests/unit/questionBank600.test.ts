/**
 * Bank-at-scale test: generates 600+ questions directly via SQL (bypassing
 * the admin zod-validation path purely for fixture-generation speed,
 * production writes always go through adminCreateQuestionBankEntry, which
 * question.service.test.ts already exercises) and proves:
 *   - `listActiveQuestionBank` pages the bank without loading it all at
 *     once and stays fast regardless of how deep a page is,
 *   - `selectNextQuestionsForMe` (the DB-backed selector wrapper) stays
 *     fast for a user with 600 available / ~40 answered,
 *   - sparse cross-user overlap scores correctly via
 *     `getAnswerStatesForUser` + `aggregateQuestionScores` at this scale.
 *
 * Runs against its own dedicated `odate_questions_bank600` database.
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
import type { Actor, Ctx } from '../../src/lib/ctx.js';
import * as questionService from '../../src/services/question.service.js';
import { aggregateQuestionScores, type QuestionAnswerState, type QuestionDefinition } from '../../src/domain/questions/index.js';

const BASE_URL = process.env.DATABASE_URL ?? 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';
const TEST_DB_NAME = 'odate_questions_bank600';

function withDbName(url: string, dbName: string): string {
  const u = new URL(url);
  u.pathname = `/${dbName}`;
  return u.toString();
}

let adminPool: pg.Pool;
let pool: pg.Pool;
let clock: ManualClock;

const CATEGORIES = ['lifestyle', 'values', 'family', 'social', 'health', 'interests', 'communication', 'logistics'];
const BANK_SIZE = 650;

before(async () => {
  adminPool = new pg.Pool({ connectionString: BASE_URL });
  await adminPool.query(`DROP DATABASE IF EXISTS ${TEST_DB_NAME}`);
  await adminPool.query(`CREATE DATABASE ${TEST_DB_NAME}`);

  process.env.DATABASE_URL = withDbName(BASE_URL, TEST_DB_NAME);
  await runMigrations();
  pool = getPool();
  clock = new ManualClock(new Date('2026-06-01T12:00:00Z'));

  // Bulk-insert 650 scale questions directly (fast fixture setup, the
  // admin zod path is already covered elsewhere).
  const values: string[] = [];
  const params: unknown[] = [];
  for (let i = 0; i < BANK_SIZE; i++) {
    const category = CATEGORIES[i % CATEGORIES.length]!;
    const base = params.length;
    values.push(`($${base + 1}, 1, true, $${base + 2}, 'scale', $${base + 3}, $${base + 4}::jsonb, $${base + 5}, true, $${base + 6})`);
    params.push(
      `bulk_q_${i}`,
      category,
      `Bulk question ${i}?`,
      JSON.stringify({ type: 'scale', min: 1, max: 5, minLabel: 'Not important', maxLabel: 'Very important', midLabel: 'Somewhat important' }),
      1 + (i % 3),
      0.3 + (i % 5) * 0.1,
    );
  }
  await pool.query(
    `INSERT INTO question_bank (slug, version, is_current, category, question_type, question_text, type_definition, base_weight, active, answer_rate_hint)
     VALUES ${values.join(',')}`,
    params,
  );
});

after(async () => {
  await closePool();
  await adminPool.query(`DROP DATABASE IF EXISTS ${TEST_DB_NAME}`);
  await adminPool.end();
});

function userActor(userId: string): Actor {
  return { type: 'user', userId, trustLevel: 'standard' };
}
function adminActor(): Actor {
  return { type: 'admin', adminId: 'admin-1' };
}

function ctxFor(actor: Actor): Ctx {
  const logger = createSilentLogger();
  return {
    db: pool,
    clock,
    config: new ConfigService(pool, clock, logger),
    flags: new FlagsService(pool, logger),
    logger,
    actor,
    payments: new FakeProcessor(),
    media: new StubMediaModerationAdapter(),
  };
}

let userCounter = 0;
async function makeUser(): Promise<string> {
  userCounter += 1;
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO users (email, password_hash, birthdate, status) VALUES ($1, 'x', '1995-01-01', 'active') RETURNING id`,
    [`bank600-${userCounter}-${Date.now()}@test.local`],
  );
  return rows[0]!.id;
}

test('question_bank holds 650 active current questions', async () => {
  const { rows } = await pool.query<{ count: string }>(`SELECT count(*) FROM question_bank WHERE is_current = true AND active = true`);
  assert.equal(Number(rows[0]!.count), BANK_SIZE);
});

test('listActiveQuestionBank: paging through all 650 rows visits each exactly once and stays fast per page', async () => {
  const seen = new Set<string>();
  let cursor: string | null = null;
  let pages = 0;
  let maxPageMs = 0;

  do {
    const t0 = performance.now();
    const page = await questionService.listActiveQuestionBank(ctxFor(adminActor()), { cursor, limit: 50 });
    maxPageMs = Math.max(maxPageMs, performance.now() - t0);
    for (const item of page.items) {
      assert.ok(!seen.has(item.id), 'paging must never repeat a row');
      seen.add(item.id);
    }
    cursor = page.nextCursor;
    pages += 1;
    assert.ok(pages < 100, 'sanity bound on page count');
  } while (cursor);

  assert.equal(seen.size, BANK_SIZE);
  assert.ok(maxPageMs < 200, `a single page took ${maxPageMs}ms, paging must not be scanning the whole bank per request`);
});

test('selectNextQuestionsForMe: fast for a user with 650 available / 40 answered', async () => {
  const userId = await makeUser();
  // Answer 40 of them directly (skip the full validation path for speed,
  // putMyQuestionAnswer's validation itself is covered in
  // question.service.test.ts).
  const { rows: toAnswer } = await pool.query<{ id: string; slug: string }>(
    `SELECT id, slug FROM question_bank WHERE is_current = true ORDER BY slug LIMIT 40`,
  );
  for (const q of toAnswer) {
    await pool.query(
      `INSERT INTO user_question_answers (user_id, question_slug, question_bank_id, status, self_value, preference_value, importance, answered_at, updated_at)
       VALUES ($1, $2, $3, 'answered', '3'::jsonb, '3'::jsonb, 'important', now(), now())`,
      [userId, q.slug, q.id],
    );
  }

  const t0 = performance.now();
  const next = await questionService.selectNextQuestionsForMe(ctxFor(userActor(userId)), { count: 10 });
  const elapsedMs = performance.now() - t0;

  assert.equal(next.length, 10);
  const answeredSlugs = new Set(toAnswer.map((q) => q.slug));
  for (const q of next) assert.ok(!answeredSlugs.has(q.slug));
  assert.ok(elapsedMs < 300, `selectNextQuestionsForMe took ${elapsedMs}ms for a 650-question bank`);
});

test('sparse cross-user scoring at scale: two users overlapping on only ~5 of 650 questions score correctly and quickly', async () => {
  const userA = await makeUser();
  const userB = await makeUser();

  const { rows: bank } = await pool.query<{ id: string; slug: string }>(`SELECT id, slug FROM question_bank WHERE is_current = true ORDER BY slug`);

  async function answer(userId: string, slug: string, id: string, self: number, pref: number): Promise<void> {
    await pool.query(
      `INSERT INTO user_question_answers (user_id, question_slug, question_bank_id, status, self_value, preference_value, importance, answered_at, updated_at)
       VALUES ($1, $2, $3, 'answered', $4::jsonb, $5::jsonb, 'important', now(), now())`,
      [userId, slug, id, JSON.stringify(self), JSON.stringify(pref)],
    );
  }

  // A answers questions 0-9; B answers questions 5-9 (5 shared) plus 100-104 (disjoint from A).
  for (let i = 0; i < 10; i++) await answer(userA, bank[i]!.slug, bank[i]!.id, 4, 4);
  for (let i = 5; i < 10; i++) await answer(userB, bank[i]!.slug, bank[i]!.id, 4, 4);
  for (let i = 100; i < 105; i++) await answer(userB, bank[i]!.slug, bank[i]!.id, 2, 2);

  async function fetchAllDefinitions(): Promise<QuestionDefinition[]> {
    const all: QuestionDefinition[] = [];
    let cursor: string | null = null;
    do {
      const page = await questionService.listActiveQuestionBank(ctxFor(adminActor()), { cursor, limit: 200 });
      all.push(...page.items);
      cursor = page.nextCursor;
    } while (cursor);
    return all;
  }

  const t0 = performance.now();
  const [definitions, statesA, statesB] = await Promise.all([
    fetchAllDefinitions(),
    questionService.getAnswerStatesForUser(ctxFor(userActor(userA)), userA),
    questionService.getAnswerStatesForUser(ctxFor(userActor(userB)), userB),
  ]);

  // aggregateQuestionScores keys per-question by QuestionDefinition.id,
  // but getAnswerStatesForUser keys by slug, bridge via a slug->id map
  // (exactly what a real caller scoring a pair would also need to do).
  function reindexBySlugToId(definitions: QuestionDefinition[], states: Map<string, QuestionAnswerState>): Map<string, QuestionAnswerState> {
    const out = new Map<string, QuestionAnswerState>();
    for (const def of definitions) {
      const state = states.get(def.slug);
      if (state) out.set(def.id, state);
    }
    return out;
  }
  const aById = reindexBySlugToId(definitions, statesA);
  const bById = reindexBySlugToId(definitions, statesB);

  const result = aggregateQuestionScores(definitions, aById, bById);
  const elapsedMs = performance.now() - t0;

  assert.equal(result.scoredQuestionCount, 5, 'only the 5 genuinely shared questions should score');
  assert.ok(Math.abs(result.score - 1) < 1e-9, 'both answered self=4/pref=4 on the shared 5 -> perfect satisfaction');
  assert.ok(elapsedMs < 500, `sparse scoring over a 650-question bank took ${elapsedMs}ms`);
});
