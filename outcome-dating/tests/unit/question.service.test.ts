/**
 * DB-backed unit tests for question.service.ts's NEW question-bank
 * surface (putMyQuestionAnswer, listActiveQuestionBank,
 * selectNextQuestionsForMe, getMyDealBreakerFilterRows, admin
 * versioning + answer-version pinning). Pure-function tests for
 * src/domain/questions/** live in tests/unit/questionScoring.test.ts;
 * tag intensity/avoidance CRUD lives in tests/unit/tags.test.ts.
 *
 * Runs against a dedicated `odate_questions_service` database (its own
 * DB per the task brief — "one database per test file").
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
import { ConflictError, NotFoundError, ValidationError } from '../../src/lib/errors.js';
import type { Actor, Ctx } from '../../src/lib/ctx.js';
import * as questionService from '../../src/services/question.service.js';
import type { CreateQuestionBankInput } from '../../src/services/question.service.js';

const BASE_URL = process.env.DATABASE_URL ?? 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';
const TEST_DB_NAME = 'odate_questions_service';

function withDbName(url: string, dbName: string): string {
  const u = new URL(url);
  u.pathname = `/${dbName}`;
  return u.toString();
}

let adminPool: pg.Pool;
let pool: pg.Pool;
let clock: ManualClock;

before(async () => {
  adminPool = new pg.Pool({ connectionString: BASE_URL });
  await adminPool.query(`DROP DATABASE IF EXISTS ${TEST_DB_NAME}`);
  await adminPool.query(`CREATE DATABASE ${TEST_DB_NAME}`);

  process.env.DATABASE_URL = withDbName(BASE_URL, TEST_DB_NAME);
  await runMigrations();
  pool = getPool();
  clock = new ManualClock(new Date('2026-06-01T12:00:00Z'));

  // family_closeness is used by several independent tests below (selector,
  // deal-breaker derivation, versioning) — seeded once up front so test
  // order doesn't matter for which test happens to create it first.
  await questionService.adminCreateQuestionBankEntry(ctxFor(adminActor()), CLOSENESS_INPUT);
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
    [`qsvc-${userCounter}-${Date.now()}@test.local`],
  );
  return rows[0]!.id;
}

const KIDS_INPUT: CreateQuestionBankInput = {
  slug: 'children_intention',
  category: 'family',
  questionText: 'Where are you on children?',
  typeDef: {
    type: 'single_choice',
    options: [
      { key: 'no_kids_no_want', label: 'No children, and do not want any' },
      { key: 'no_kids_want', label: 'No children, but want them' },
      { key: 'has_kids_want_more', label: 'Have children and want more' },
      { key: 'has_kids_no_more', label: 'Have children and do not want more' },
      { key: 'still_deciding', label: 'Still deciding' },
    ],
  },
  baseWeight: 2,
  sensitive: false,
};

const SMOKING_INPUT: CreateQuestionBankInput = {
  slug: 'smoking_binary',
  category: 'lifestyle',
  questionText: 'Do you smoke?',
  typeDef: {
    type: 'single_choice',
    options: [
      { key: 'no', label: 'I do not smoke' },
      { key: 'yes', label: 'I smoke' },
    ],
  },
  baseWeight: 1,
};

const CLOSENESS_INPUT: CreateQuestionBankInput = {
  slug: 'family_closeness',
  category: 'family',
  questionText: 'How close are you with your family?',
  typeDef: {
    type: 'scale',
    min: 1,
    max: 5,
    minLabel: 'Not close at all',
    maxLabel: 'Extremely close',
    midLabel: 'Moderately close',
  },
  baseWeight: 1,
};

// =====================================================================
// putMyQuestionAnswer
// =====================================================================

test('putMyQuestionAnswer: persists an "answered" response with explicit value + importance', async () => {
  await questionService.adminCreateQuestionBankEntry(ctxFor(adminActor()), KIDS_INPUT);
  const userId = await makeUser();

  const record = await questionService.putMyQuestionAnswer(ctxFor(userActor(userId)), {
    slug: 'children_intention',
    status: 'answered',
    selfValue: 'has_kids_want_more',
    preferenceValue: ['has_kids_want_more', 'has_kids_no_more'],
    importance: 'critical',
  });

  assert.equal(record.status, 'answered');
  assert.equal(record.selfValue, 'has_kids_want_more');
  assert.deepEqual(record.preferenceValue, ['has_kids_want_more', 'has_kids_no_more']);
  assert.equal(record.importance, 'critical');
});

test('putMyQuestionAnswer: rejects a selfValue outside the option set', async () => {
  const userId = await makeUser();
  await assert.rejects(
    () =>
      questionService.putMyQuestionAnswer(ctxFor(userActor(userId)), {
        slug: 'children_intention',
        status: 'answered',
        selfValue: 'not_a_real_option',
        preferenceValue: ['has_kids_want_more'],
        importance: 'important',
      }),
    ValidationError,
  );
});

test('putMyQuestionAnswer: skipped/prefer_not_to_say must not carry a value, preference, importance, or ladder position', async () => {
  const userId = await makeUser();
  await assert.rejects(
    () =>
      questionService.putMyQuestionAnswer(ctxFor(userActor(userId)), {
        slug: 'children_intention',
        status: 'skipped',
        importance: 'important',
      }),
    ValidationError,
  );
});

test('putMyQuestionAnswer: prefer_not_to_say works on ANY question, not just ones flagged sensitive', async () => {
  const userId = await makeUser();
  const record = await questionService.putMyQuestionAnswer(ctxFor(userActor(userId)), {
    slug: 'children_intention', // sensitive: false
    status: 'prefer_not_to_say',
  });
  assert.equal(record.status, 'prefer_not_to_say');
  assert.equal(record.selfValue, null);
  assert.equal(record.importance, null);
});

test('putMyQuestionAnswer: skip then re-answer overwrites (one row per user+slug)', async () => {
  const userId = await makeUser();
  await questionService.putMyQuestionAnswer(ctxFor(userActor(userId)), { slug: 'children_intention', status: 'skipped' });
  await questionService.putMyQuestionAnswer(ctxFor(userActor(userId)), {
    slug: 'children_intention',
    status: 'answered',
    selfValue: 'still_deciding',
    preferenceValue: ['still_deciding', 'no_kids_want'],
    importance: 'slight',
  });
  const answers = await questionService.getMyQuestionAnswers(ctxFor(userActor(userId)));
  const kidsAnswers = answers.filter((a) => a.questionSlug === 'children_intention');
  assert.equal(kidsAnswers.length, 1);
  assert.equal(kidsAnswers[0]!.status, 'answered');
});

// ---- ladder presentation ----

test('putMyQuestionAnswer: ladderPosition on a ladder-presentation question sets preference + importance', async () => {
  await questionService.adminCreateQuestionBankEntry(ctxFor(adminActor()), SMOKING_INPUT);
  const userId = await makeUser();

  const record = await questionService.putMyQuestionAnswer(ctxFor(userActor(userId)), {
    slug: 'smoking_binary',
    status: 'answered',
    selfValue: 'no',
    ladderPosition: 0, // "Deal breaker: I do not smoke"
  });

  assert.equal(record.importance, 'deal_breaker');
  assert.deepEqual(record.preferenceValue, ['no']);
});

test('putMyQuestionAnswer: ladderPosition rejected on a non-ladder (5-option) question', async () => {
  const userId = await makeUser();
  await assert.rejects(
    () =>
      questionService.putMyQuestionAnswer(ctxFor(userActor(userId)), {
        slug: 'children_intention',
        status: 'answered',
        selfValue: 'still_deciding',
        ladderPosition: 2,
      }),
    ValidationError,
  );
});

test('putMyQuestionAnswer: cannot combine ladderPosition with explicit preferenceValue/importance', async () => {
  const userId = await makeUser();
  await assert.rejects(
    () =>
      questionService.putMyQuestionAnswer(ctxFor(userActor(userId)), {
        slug: 'smoking_binary',
        status: 'answered',
        selfValue: 'no',
        ladderPosition: 2,
        importance: 'important',
      }),
    ValidationError,
  );
});

// =====================================================================
// listActiveQuestionBank — paging
// =====================================================================

test('listActiveQuestionBank: pages without duplicates or gaps', async () => {
  const first = await questionService.listActiveQuestionBank(ctxFor(adminActor()), { limit: 2 });
  assert.ok(first.items.length >= 1);
  if (first.nextCursor) {
    const second = await questionService.listActiveQuestionBank(ctxFor(adminActor()), { limit: 2, cursor: first.nextCursor });
    const firstIds = new Set(first.items.map((q) => q.id));
    for (const item of second.items) assert.ok(!firstIds.has(item.id), 'page 2 must not repeat a page 1 item');
  }
});

// =====================================================================
// selectNextQuestionsForMe
// =====================================================================

test('selectNextQuestionsForMe: never returns a question the user already answered', async () => {
  const userId = await makeUser();
  await questionService.putMyQuestionAnswer(ctxFor(userActor(userId)), {
    slug: 'family_closeness',
    status: 'answered',
    selfValue: 3,
    preferenceValue: 3,
    importance: 'important',
  });

  const next = await questionService.selectNextQuestionsForMe(ctxFor(userActor(userId)), { count: 20 });
  assert.ok(!next.some((q) => q.slug === 'family_closeness'));
});

// =====================================================================
// Deal-breaker filter row derivation (I/O wrapper)
// =====================================================================

test('getMyDealBreakerFilterRows: reflects only this user\'s current deal-breaker answers', async () => {
  const userId = await makeUser();
  await questionService.putMyQuestionAnswer(ctxFor(userActor(userId)), {
    slug: 'children_intention',
    status: 'answered',
    selfValue: 'has_kids_want_more',
    preferenceValue: ['has_kids_want_more'],
    importance: 'deal_breaker',
  });
  await questionService.putMyQuestionAnswer(ctxFor(userActor(userId)), {
    slug: 'family_closeness',
    status: 'answered',
    selfValue: 3,
    preferenceValue: 3,
    importance: 'important', // not a deal breaker -> must not appear
  });

  const rows = await questionService.getMyDealBreakerFilterRows(ctxFor(userActor(userId)));
  assert.equal(rows.length, 1);
  assert.equal(rows[0]!.filterKey, 'qb:children_intention');
  assert.equal(rows[0]!.operator, 'in');
  assert.deepEqual(rows[0]!.value, ['has_kids_want_more']);
  assert.equal(rows[0]!.excludeIfUnset, true);
});

test('getMyDealBreakerFilterRows: empty for a user with no deal breakers', async () => {
  const userId = await makeUser();
  const rows = await questionService.getMyDealBreakerFilterRows(ctxFor(userActor(userId)));
  assert.deepEqual(rows, []);
});

// =====================================================================
// Admin versioning + answer-version pinning
// =====================================================================

test('adminCreateQuestionBankEntry: rejects a duplicate slug', async () => {
  await assert.rejects(() => questionService.adminCreateQuestionBankEntry(ctxFor(adminActor()), KIDS_INPUT), ConflictError);
});

test('adminUpdateQuestionBankEntry: creates a new version, keeps old version rows intact, and pins existing answers to their original version', async () => {
  const userId = await makeUser();

  const before = await questionService.putMyQuestionAnswer(ctxFor(userActor(userId)), {
    slug: 'family_closeness',
    status: 'answered',
    selfValue: 4,
    preferenceValue: 4,
    importance: 'critical',
  });

  const originalDef = await questionService.getCurrentQuestionBySlug(ctxFor(adminActor()), 'family_closeness');
  assert.ok(originalDef);
  assert.equal(originalDef!.version, 1);
  assert.equal(before.questionBankId, originalDef!.id);

  // Edit the question — new midpoint label, new version.
  const updated = await questionService.adminUpdateQuestionBankEntry(ctxFor(adminActor()), 'family_closeness', {
    typeDef: {
      type: 'scale',
      min: 1,
      max: 5,
      minLabel: 'Not close at all',
      maxLabel: 'Extremely close',
      midLabel: 'Somewhat close', // edited wording
    },
  });
  assert.equal(updated.version, 2);
  assert.notEqual(updated.id, originalDef!.id);

  // The CURRENT definition is now v2.
  const currentDef = await questionService.getCurrentQuestionBySlug(ctxFor(adminActor()), 'family_closeness');
  assert.equal(currentDef!.version, 2);

  // The user's EXISTING answer, taken before the edit, must still be
  // pinned to the ORIGINAL (v1) question_bank row — editing a question
  // must not silently change what an existing answer meant.
  const answers = await questionService.getMyQuestionAnswers(ctxFor(userActor(userId)));
  const closenessAnswer = answers.find((a) => a.questionSlug === 'family_closeness')!;
  assert.equal(closenessAnswer.questionBankId, originalDef!.id, 'existing answer must stay pinned to the version it was given under');
  assert.notEqual(closenessAnswer.questionBankId, updated.id);

  // A NEW answer from a different user is pinned to the NEW (v2) version.
  const otherUserId = await makeUser();
  const afterEditAnswer = await questionService.putMyQuestionAnswer(ctxFor(userActor(otherUserId)), {
    slug: 'family_closeness',
    status: 'answered',
    selfValue: 2,
    preferenceValue: 2,
    importance: 'slight',
  });
  assert.equal(afterEditAnswer.questionBankId, updated.id);
});

test('adminUpdateQuestionBankEntry: unknown slug is a NotFoundError', async () => {
  await assert.rejects(() => questionService.adminUpdateQuestionBankEntry(ctxFor(adminActor()), 'not-a-real-slug', { baseWeight: 2 }), NotFoundError);
});

test('non-admin actor cannot create or update the bank', async () => {
  const userId = await makeUser();
  await assert.rejects(() =>
    questionService.adminCreateQuestionBankEntry(ctxFor(userActor(userId)), {
      slug: 'nope',
      category: 'lifestyle',
      questionText: 'Nope?',
      typeDef: { type: 'single_choice', options: [{ key: 'a', label: 'A' }, { key: 'b', label: 'B' }] },
    }),
  );
});
