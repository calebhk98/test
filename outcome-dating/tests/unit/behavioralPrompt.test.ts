/**
 * behavioralPrompt.service.ts unit tests.
 *
 * Self-contained: this file owns its own tiny test harness (same pattern
 * as `tests/unit/postDateFeedback.test.ts`), using a dedicated Postgres
 * database (`odate_retire_behavioral`, per this build's task brief). Every
 * dependency exercised here (`question.service.ts`'s
 * `getCurrentQuestionBySlug`/`getQuestionBankSlugById`/`putMyQuestionAnswer`,
 * `resolveVisibleTagsFor`) is the real sibling code, nothing mocked.
 *
 * Covers, per this file's CUTOVER NOTE:
 *   1. Pattern detection resolves the linkable question against the ONE
 *      typed bank (question_bank/user_question_answers), not the OLD
 *      `questions` table.
 *   2. Skipping a suggestion still works exactly as before.
 *   3. Answering a suggestion through the OLD `{selfValue, partnerValue}`
 *      shape ALONE (no importance/ladderPosition) now throws — the
 *      reported, genuine behavior gap this build could not paper over
 *      without inventing an importance value.
 *   4. Answering with a real importance (or ladderPosition) succeeds and
 *      writes a real `user_question_answers` row via `putMyQuestionAnswer`.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import pg from 'pg';
import { runMigrations } from '../../src/db/migrate.js';
import { getPool, closePool } from '../../src/db/pool.js';
import { ConfigService } from '../../src/config/config.service.js';
import { FlagsService, KNOWN_FLAGS } from '../../src/config/flags.service.js';
import { ManualClock } from '../../src/lib/time.js';
import { createSilentLogger } from '../../src/lib/logger.js';
import { FakeProcessor } from '../../src/services/payments/fake.processor.js';
import { StubMediaModerationAdapter } from '../../src/services/media/stub.adapter.js';
import type { Actor, Ctx } from '../../src/lib/ctx.js';
import * as behavioralPrompt from '../../src/services/behavioralPrompt.service.js';
import { ConflictError, ForbiddenError, NotFoundError, ValidationError } from '../../src/lib/errors.js';

// ---------------------------------------------------------------------
// Self-contained harness
// ---------------------------------------------------------------------

const BASE_URL = process.env.DATABASE_URL ?? 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';
const DB_NAME = 'odate_retire_behavioral';

function withDbName(url: string, dbName: string): string {
  const u = new URL(url);
  u.pathname = `/${dbName}`;
  return u.toString();
}

let adminPool: pg.Pool;
let pool: pg.Pool;
let clock: ManualClock;
let config: ConfigService;
let flags: FlagsService;

before(async () => {
  adminPool = new pg.Pool({ connectionString: BASE_URL });
  await adminPool.query(`SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = $1 AND pid <> pg_backend_pid()`, [DB_NAME]);
  await adminPool.query(`DROP DATABASE IF EXISTS ${DB_NAME}`);
  await adminPool.query(`CREATE DATABASE ${DB_NAME}`);

  process.env.DATABASE_URL = withDbName(BASE_URL, DB_NAME);
  await runMigrations();

  pool = getPool();
  clock = new ManualClock(new Date('2026-01-05T12:00:00.000Z'));
  const logger = createSilentLogger();
  config = new ConfigService(pool, clock, logger);
  flags = new FlagsService(pool, logger);
  await config.seedDefaults('system:test');
  await flags.seedKnownFlags();
  await flags.setFlag(KNOWN_FLAGS.BEHAVIORAL_QUESTION_PROMPTS, { enabled: true, rolloutPercent: 100 });
});

after(async () => {
  await closePool();
  await adminPool.query(`DROP DATABASE IF EXISTS ${DB_NAME}`);
  await adminPool.end();
});

function ctxFor(actor: Actor): Ctx {
  return {
    db: pool,
    clock,
    config,
    flags,
    logger: createSilentLogger(),
    actor,
    payments: new FakeProcessor(),
    media: new StubMediaModerationAdapter(),
  };
}

function userActor(userId: string): Actor {
  return { type: 'user', userId, trustLevel: 'standard' };
}

let userCounter = 0;
async function insertUser(): Promise<string> {
  userCounter += 1;
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO users (email, password_hash, birthdate, status, trust_score, trust_level, email_verified_at)
     VALUES ($1, 'x', '1995-01-01', 'active', 60, 'standard', now())
     RETURNING id`,
    [`bp-user-${userCounter}-${Date.now()}@example.test`],
  );
  return rows[0]!.id;
}

async function insertTag(name: string): Promise<string> {
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO interest_tags (name, category) VALUES ($1, 'hobby') RETURNING id`,
    [name],
  );
  return rows[0]!.id;
}

async function grantPublicTag(userId: string, tagId: string): Promise<void> {
  await pool.query(`INSERT INTO user_tags (user_id, tag_id, visibility) VALUES ($1, $2, 'public')`, [userId, tagId]);
}

async function insertInterest(senderId: string, recipientId: string, status: 'accepted' | 'declined'): Promise<void> {
  await pool.query(
    `INSERT INTO interests (sender_id, recipient_id, status, policy_snapshot, expires_at, accepted_at, declined_at)
     VALUES ($1, $2, $3, '{}'::jsonb, now() + interval '7 days', $4, $5)`,
    [senderId, recipientId, status, status === 'accepted' ? new Date() : null, status === 'declined' ? new Date() : null],
  );
}

interface TestQuestion {
  id: string;
  slug: string;
}

const SCALE_TYPE_DEF = { type: 'scale', min: 1, max: 5, minLabel: 'low', maxLabel: 'high', midLabel: 'mid' };
const LADDER_TYPE_DEF = {
  type: 'single_choice',
  options: [
    { key: 'no', label: 'No' },
    { key: 'yes', label: 'Yes' },
  ],
};

/** Inserts a `question_bank` row directly — bypasses the admin routes (`tests/http/admin.test.ts` covers those). */
async function insertBankQuestion(slug: string, typeDef: unknown = SCALE_TYPE_DEF): Promise<TestQuestion> {
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO question_bank (slug, version, is_current, category, question_type, question_text, type_definition, active)
     VALUES ($1, 1, true, 'test', $2, $1, $3::jsonb, true)
     RETURNING id`,
    [slug, (typeDef as { type: string }).type, JSON.stringify(typeDef)],
  );
  return { id: rows[0]!.id, slug };
}

// =====================================================================
// detectPatternsForUser
// =====================================================================

test('detectPatternsForUser: an accepted-more-than-declined tag pattern past the threshold creates a pending suggestion linked to the current typed-bank question', async () => {
  const user = await insertUser();
  const tagName = `Hiking-${Date.now()}`;
  const slug = tagName.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
  const question = await insertBankQuestion(slug);
  const tagId = await insertTag(tagName);

  // 3 accepted, 0 declined (threshold: MIN_PATTERN_ACCEPT_COUNT, strictly > declined).
  for (let i = 0; i < behavioralPrompt.MIN_PATTERN_ACCEPT_COUNT; i++) {
    const other = await insertUser();
    await grantPublicTag(other, tagId);
    await insertInterest(user, other, 'accepted');
  }

  const created = await behavioralPrompt.detectPatternsForUser(ctxFor({ type: 'system', job: 'test' }), user);
  assert.equal(created.length, 1, 'exactly one pattern-triggered suggestion should be created');
  assert.equal(created[0]!.questionId, question.id, 'the suggestion must be linked to the CURRENT typed-bank question_bank id, not an old-bank id');
  assert.equal(created[0]!.triggerKind, 'tag');
  assert.equal(created[0]!.triggerLabel, tagName);

  const pending = await behavioralPrompt.listPendingSuggestions(ctxFor(userActor(user)));
  assert.equal(pending.length, 1);
  assert.equal(pending[0]!.id, created[0]!.id);
});

test('detectPatternsForUser: no linkable question in the typed bank -> no suggestion, no crash', async () => {
  const user = await insertUser();
  const tagName = `Unlinked-${Date.now()}`;
  const tagId = await insertTag(tagName); // deliberately: no matching question_bank row for this slug

  for (let i = 0; i < behavioralPrompt.MIN_PATTERN_ACCEPT_COUNT; i++) {
    const other = await insertUser();
    await grantPublicTag(other, tagId);
    await insertInterest(user, other, 'accepted');
  }

  const created = await behavioralPrompt.detectPatternsForUser(ctxFor({ type: 'system', job: 'test' }), user);
  assert.equal(created.length, 0);
});

test('detectPatternsForUser: disabled feature flag -> returns nothing, creates nothing', async () => {
  await flags.setFlag(KNOWN_FLAGS.BEHAVIORAL_QUESTION_PROMPTS, { enabled: false });
  try {
    const user = await insertUser();
    const tagName = `Flagged-${Date.now()}`;
    const slug = tagName.toLowerCase();
    await insertBankQuestion(slug);
    const tagId = await insertTag(tagName);
    for (let i = 0; i < behavioralPrompt.MIN_PATTERN_ACCEPT_COUNT; i++) {
      const other = await insertUser();
      await grantPublicTag(other, tagId);
      await insertInterest(user, other, 'accepted');
    }

    const created = await behavioralPrompt.detectPatternsForUser(ctxFor({ type: 'system', job: 'test' }), user);
    assert.equal(created.length, 0);
  } finally {
    await flags.setFlag(KNOWN_FLAGS.BEHAVIORAL_QUESTION_PROMPTS, { enabled: true, rolloutPercent: 100 });
  }
});

// =====================================================================
// respondToSuggestion
// =====================================================================

async function makePendingSuggestion(userId: string, question: TestQuestion, triggerLabel = 'test-trigger'): Promise<string> {
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO behavioral_prompt_suggestions (user_id, question_id, trigger_kind, trigger_label, status, created_at)
     VALUES ($1, $2, 'tag', $3, 'pending', now())
     RETURNING id`,
    [userId, question.id, triggerLabel],
  );
  return rows[0]!.id;
}

test('respondToSuggestion: skipping records status=skipped and writes no answer', async () => {
  const user = await insertUser();
  const question = await insertBankQuestion(`skip-${Date.now()}`);
  const suggestionId = await makePendingSuggestion(user, question);

  await behavioralPrompt.respondToSuggestion(ctxFor(userActor(user)), suggestionId, { skipped: true });

  const { rows } = await pool.query<{ status: string; responded_at: Date | null }>(
    'SELECT status, responded_at FROM behavioral_prompt_suggestions WHERE id = $1',
    [suggestionId],
  );
  assert.equal(rows[0]!.status, 'skipped');
  assert.ok(rows[0]!.responded_at);

  const { rows: answerRows } = await pool.query('SELECT 1 FROM user_question_answers WHERE user_id = $1 AND question_slug = $2', [
    user,
    question.slug,
  ]);
  assert.equal(answerRows.length, 0, 'skipping must never write an answer');
});

test(
  'respondToSuggestion: answering with only the OLD {selfValue, partnerValue} shape (no importance/ladderPosition) throws — ' +
    'the typed bank cannot accept a value-only answer, and this build refuses to invent an importance to paper over it (see CUTOVER NOTE)',
  async () => {
    const user = await insertUser();
    const question = await insertBankQuestion(`no-importance-${Date.now()}`);
    const suggestionId = await makePendingSuggestion(user, question);

    await assert.rejects(
      () => behavioralPrompt.respondToSuggestion(ctxFor(userActor(user)), suggestionId, { skipped: false, selfValue: 4, partnerValue: 3 }),
      ValidationError,
    );

    const { rows } = await pool.query<{ status: string }>('SELECT status FROM behavioral_prompt_suggestions WHERE id = $1', [suggestionId]);
    assert.equal(rows[0]!.status, 'pending', 'a rejected response must not change the suggestion out of pending');
  },
);

test('respondToSuggestion: answering with a real importance writes a real typed-bank answer and flips status to answered', async () => {
  const user = await insertUser();
  const question = await insertBankQuestion(`with-importance-${Date.now()}`);
  const suggestionId = await makePendingSuggestion(user, question);

  await behavioralPrompt.respondToSuggestion(ctxFor(userActor(user)), suggestionId, {
    skipped: false,
    selfValue: 4,
    partnerValue: 3,
    importance: 'important',
  });

  const { rows } = await pool.query<{ status: string }>('SELECT status FROM behavioral_prompt_suggestions WHERE id = $1', [suggestionId]);
  assert.equal(rows[0]!.status, 'answered');

  const { rows: answerRows } = await pool.query<{
    status: string;
    self_value: unknown;
    preference_value: unknown;
    importance: string;
  }>('SELECT status, self_value, preference_value, importance FROM user_question_answers WHERE user_id = $1 AND question_slug = $2', [
    user,
    question.slug,
  ]);
  assert.equal(answerRows.length, 1);
  assert.equal(answerRows[0]!.status, 'answered');
  assert.equal(answerRows[0]!.self_value, 4);
  assert.equal(answerRows[0]!.preference_value, 3);
  assert.equal(answerRows[0]!.importance, 'important');
});

test('respondToSuggestion: a ladder-presentation question accepts ladderPosition in place of partnerValue+importance', async () => {
  const user = await insertUser();
  const question = await insertBankQuestion(`ladder-${Date.now()}`, LADDER_TYPE_DEF);
  const suggestionId = await makePendingSuggestion(user, question);

  await behavioralPrompt.respondToSuggestion(ctxFor(userActor(user)), suggestionId, {
    skipped: false,
    selfValue: 'yes',
    ladderPosition: 4, // "Deal breaker: yes"
  });

  const { rows: answerRows } = await pool.query<{ importance: string; preference_value: unknown }>(
    'SELECT importance, preference_value FROM user_question_answers WHERE user_id = $1 AND question_slug = $2',
    [user, question.slug],
  );
  assert.equal(answerRows[0]!.importance, 'deal_breaker');
  assert.deepEqual(answerRows[0]!.preference_value, ['yes']);
});

test('respondToSuggestion: NotFoundError for an unknown suggestion id', async () => {
  const user = await insertUser();
  await assert.rejects(
    () => behavioralPrompt.respondToSuggestion(ctxFor(userActor(user)), '00000000-0000-0000-0000-000000000000', { skipped: true }),
    NotFoundError,
  );
});

test('respondToSuggestion: ForbiddenError when the suggestion belongs to a different user', async () => {
  const owner = await insertUser();
  const stranger = await insertUser();
  const question = await insertBankQuestion(`forbidden-${Date.now()}`);
  const suggestionId = await makePendingSuggestion(owner, question);

  await assert.rejects(() => behavioralPrompt.respondToSuggestion(ctxFor(userActor(stranger)), suggestionId, { skipped: true }), ForbiddenError);
});

test('respondToSuggestion: ConflictError when responding to an already-resolved suggestion', async () => {
  const user = await insertUser();
  const question = await insertBankQuestion(`conflict-${Date.now()}`);
  const suggestionId = await makePendingSuggestion(user, question);

  await behavioralPrompt.respondToSuggestion(ctxFor(userActor(user)), suggestionId, { skipped: true });

  await assert.rejects(() => behavioralPrompt.respondToSuggestion(ctxFor(userActor(user)), suggestionId, { skipped: true }), ConflictError);
});
