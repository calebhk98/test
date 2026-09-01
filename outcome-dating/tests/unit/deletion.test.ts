/**
 * tests/unit/deletion.test.ts, PRIV-1 fix proof: `profile.service#
 * deleteMyAccount` actually erases personal data, table by table, rather
 * than merely flipping a status column. See that function's own "PRIV-1
 * FIX" doc comment for the full retention policy this file asserts.
 *
 * Self-contained: owns its own dedicated Postgres database
 * (`odate_safety_deletion`, per the build brief's "use your own Postgres
 * databases odate_safety_<suite>" instruction).
 *
 * Every assertion below reads the ACTUAL ROWS in each table after
 * deletion (never just `users.status`), per the brief's "test what
 * actually remains in each table, table by table".
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import pg from 'pg';
import { randomUUID } from 'node:crypto';
import { runMigrations } from '../../src/db/migrate.js';
import { getPool, closePool } from '../../src/db/pool.js';
import { ConfigService } from '../../src/config/config.service.js';
import { FlagsService } from '../../src/config/flags.service.js';
import { ManualClock } from '../../src/lib/time.js';
import { createSilentLogger } from '../../src/lib/logger.js';
import { FakeProcessor } from '../../src/services/payments/fake.processor.js';
import { StubMediaModerationAdapter } from '../../src/services/media/stub.adapter.js';
import type { Actor, Ctx } from '../../src/lib/ctx.js';
import * as profile from '../../src/services/profile.service.js';
import { DELETED_MESSAGE_PLACEHOLDER } from '../../src/services/profile.service.js';

// ---------------------------------------------------------------------
// Self-contained DB/ctx setup, see module doc.
// ---------------------------------------------------------------------

const BASE_URL = process.env.DATABASE_URL ?? 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';
const DB_NAME = 'odate_safety_deletion';

function withDbName(url: string, dbName: string): string {
  const u = new URL(url);
  u.pathname = `/${dbName}`;
  return u.toString();
}

let adminPool: pg.Pool | undefined;
let testPool: pg.Pool | undefined;

before(async () => {
  adminPool = new pg.Pool({ connectionString: BASE_URL });
  await adminPool.query(`SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = $1 AND pid <> pg_backend_pid()`, [DB_NAME]);
  await adminPool.query(`DROP DATABASE IF EXISTS ${DB_NAME}`);
  await adminPool.query(`CREATE DATABASE ${DB_NAME}`);
  process.env.DATABASE_URL = withDbName(BASE_URL, DB_NAME);
  await runMigrations();
  testPool = getPool();
});

after(async () => {
  await closePool();
  if (adminPool) {
    await adminPool.query(`DROP DATABASE IF EXISTS ${DB_NAME}`);
    await adminPool.end();
  }
});

function getTestPool(): pg.Pool {
  if (!testPool) throw new Error('DB not set up yet');
  return testPool;
}

function buildCtx(opts: { actor?: Actor; now?: Date } = {}): Ctx {
  const pool = getTestPool();
  const clock = new ManualClock(opts.now ?? new Date());
  const logger = createSilentLogger();
  return {
    db: pool,
    clock,
    config: new ConfigService(pool, clock, logger),
    flags: new FlagsService(pool, logger),
    logger,
    actor: opts.actor ?? { type: 'system', job: 'test' },
    payments: new FakeProcessor(),
    media: new StubMediaModerationAdapter(),
  };
}

function userActor(userId: string): Actor {
  return { type: 'user', userId, trustLevel: 'standard' };
}

let emailCounter = 0;
function uniqueEmail(): string {
  emailCounter += 1;
  return `del${emailCounter}.${Date.now()}@example.test`;
}

async function insertUser(ctx: Ctx): Promise<string> {
  const id = randomUUID();
  await ctx.db.query(
    `INSERT INTO users (id, email, password_hash, birthdate, status, trust_score, trust_level)
     VALUES ($1, $2, 'x', '1990-01-01', 'active', 50, 'standard')`,
    [id, uniqueEmail()],
  );
  return id;
}

async function insertProfile(ctx: Ctx, userId: string): Promise<void> {
  await ctx.db.query(
    `INSERT INTO profiles (user_id, display_name, bio, city, latitude, longitude, age, gender, seeking, relationship_intention, distance_precision_floor_km)
     VALUES ($1, 'Real Name', 'A real bio about myself', 'Realtown', 40.0, -75.0, 28, 'woman', 'man', 'long_term', 25)`,
    [userId],
  );
}

// ONE typed question bank (question_bank/user_question_answers,
// db/migrations/008_questions.sql), this used to create a row in the OLD
// `questions` table; that table (and `answers`) is gone as of
// db/migrations/022_drop_old_question_bank.sql, so these fixture helpers
// now target the typed bank `deleteMyAccount` itself was repointed to.
async function insertQuestion(ctx: Ctx, sensitive: boolean): Promise<string> {
  const id = randomUUID();
  const slug = `slug-${id}`;
  await ctx.db.query(
    `INSERT INTO question_bank (id, slug, version, is_current, category, question_type, question_text, type_definition, sensitive, active)
     VALUES ($1, $2, 1, true, 'lifestyle', 'scale', 'q text', $3::jsonb, $4, true)`,
    [id, slug, JSON.stringify({ type: 'scale', min: 1, max: 5, minLabel: 'low', maxLabel: 'high', midLabel: 'mid' }), sensitive],
  );
  return id;
}

/** Returns `questionId`'s slug, the actual key `user_question_answers` is keyed on (see that table's own doc: PK is `(user_id, question_slug)`, not `(user_id, question_bank_id)`). */
async function insertAnswer(ctx: Ctx, userId: string, questionId: string): Promise<void> {
  const { rows } = await ctx.db.query<{ slug: string }>('SELECT slug FROM question_bank WHERE id = $1', [questionId]);
  const slug = rows[0]!.slug;
  await ctx.db.query(
    `INSERT INTO user_question_answers (user_id, question_slug, question_bank_id, status, self_value, preference_value, importance, answered_at, updated_at)
     VALUES ($1, $2, $3, 'answered', '4'::jsonb, '3'::jsonb, 'slight', now(), now())`,
    [userId, slug, questionId],
  );
}

async function insertTag(ctx: Ctx): Promise<string> {
  const id = randomUUID();
  await ctx.db.query(`INSERT INTO interest_tags (id, name, category) VALUES ($1, $2, 'hobby')`, [id, `Tag-${id}`]);
  return id;
}

async function insertUserTag(ctx: Ctx, userId: string, tagId: string, visibility: 'public' | 'private_reciprocal'): Promise<void> {
  await ctx.db.query(`INSERT INTO user_tags (user_id, tag_id, visibility) VALUES ($1, $2, $3)`, [userId, tagId, visibility]);
}

async function insertHardFilter(ctx: Ctx, userId: string): Promise<void> {
  await ctx.db.query(
    `INSERT INTO hard_filters (user_id, filter_key, operator, value) VALUES ($1, 'distance_km', 'lte', '50')`,
    [userId],
  );
}

async function insertConversation(ctx: Ctx, userAId: string, userBId: string): Promise<string> {
  const [a, b] = userAId < userBId ? [userAId, userBId] : [userBId, userAId];
  const id = randomUUID();
  await ctx.db.query(`INSERT INTO conversations (id, user_a_id, user_b_id, status) VALUES ($1, $2, $3, 'active')`, [id, a, b]);
  return id;
}

async function insertMessage(ctx: Ctx, conversationId: string, senderId: string, body: string): Promise<string> {
  const id = randomUUID();
  await ctx.db.query(`INSERT INTO messages (id, conversation_id, sender_id, body) VALUES ($1, $2, $3, $4)`, [id, conversationId, senderId, body]);
  return id;
}

async function insertVenue(ctx: Ctx): Promise<string> {
  const id = randomUUID();
  await ctx.db.query(
    `INSERT INTO venues (id, name, address, latitude, longitude, category) VALUES ($1, 'Cafe', '1 Main St', 40.0, -75.0, 'coffee')`,
    [id],
  );
  return id;
}

async function insertDateProposal(ctx: Ctx, conversationId: string, proposerId: string, recipientId: string, venueId: string): Promise<string> {
  const id = randomUUID();
  await ctx.db.query(
    `INSERT INTO date_proposals (id, conversation_id, proposer_id, recipient_id, venue_id, scheduled_start, scheduled_end, status, policy_snapshot, escrow_amount_cents)
     VALUES ($1, $2, $3, $4, $5, now() + interval '3 days', now() + interval '3 days 1 hour', 'completed', '{}'::jsonb, 2000)`,
    [id, conversationId, proposerId, recipientId, venueId],
  );
  return id;
}

async function insertPaymentHold(ctx: Ctx, dateProposalId: string, userId: string): Promise<string> {
  const id = randomUUID();
  await ctx.db.query(
    `INSERT INTO payment_holds (id, date_proposal_id, user_id, processor, amount_cents, status)
     VALUES ($1, $2, $3, 'fake', 2000, 'captured')`,
    [id, dateProposalId, userId],
  );
  return id;
}

async function insertLedgerEntry(ctx: Ctx, userId: string, dateProposalId: string, holdId: string): Promise<void> {
  await ctx.db.query(
    `INSERT INTO payment_ledger (user_id, date_proposal_id, payment_hold_id, type, amount_cents)
     VALUES ($1, $2, $3, 'capture', 2000)`,
    [userId, dateProposalId, holdId],
  );
}

async function insertReport(ctx: Ctx, reporterId: string, reportedId: string): Promise<string> {
  const id = randomUUID();
  await ctx.db.query(
    `INSERT INTO reports (id, reporter_id, reported_id, category, severity) VALUES ($1, $2, $3, 'spam', 1)`,
    [id, reporterId, reportedId],
  );
  return id;
}

async function insertTrustEvent(ctx: Ctx, userId: string): Promise<void> {
  await ctx.db.query(`INSERT INTO trust_events (user_id, event_type, delta) VALUES ($1, 'no_show', -10)`, [userId]);
}

async function insertModerationAction(ctx: Ctx, userId: string): Promise<void> {
  await ctx.db.query(`INSERT INTO moderation_actions (user_id, action, reason, score) VALUES ($1, 'warning', 'automated_score_threshold_crossed', 10)`, [userId]);
}

// =========================================================================
// Full fixture builder, one user with data in every table PRIV-1 names,
// plus the retained (financial/safety) tables, plus a conversation
// partner whose own data must survive completely untouched.
// =========================================================================

interface Fixture {
  userId: string;
  partnerId: string;
  conversationId: string;
  userMessageId: string;
  partnerMessageId: string;
  sensitiveQuestionId: string;
  tagId: string;
  dateProposalId: string;
}

async function buildFixture(ctx: Ctx): Promise<Fixture> {
  const userId = await insertUser(ctx);
  const partnerId = await insertUser(ctx);
  await insertProfile(ctx, userId);
  await insertProfile(ctx, partnerId);

  const sensitiveQuestionId = await insertQuestion(ctx, true);
  const ordinaryQuestionId = await insertQuestion(ctx, false);
  await insertAnswer(ctx, userId, sensitiveQuestionId);
  await insertAnswer(ctx, userId, ordinaryQuestionId);

  const tagId = await insertTag(ctx);
  await insertUserTag(ctx, userId, tagId, 'private_reciprocal');
  await insertHardFilter(ctx, userId);

  const conversationId = await insertConversation(ctx, userId, partnerId);
  const userMessageId = await insertMessage(ctx, conversationId, userId, 'This is my private message content.');
  const partnerMessageId = await insertMessage(ctx, conversationId, partnerId, "This is the partner's own message.");

  const venueId = await insertVenue(ctx);
  const dateProposalId = await insertDateProposal(ctx, conversationId, userId, partnerId, venueId);
  const holdId = await insertPaymentHold(ctx, dateProposalId, userId);
  await insertLedgerEntry(ctx, userId, dateProposalId, holdId);

  await insertReport(ctx, partnerId, userId); // a report FILED AGAINST userId
  await insertTrustEvent(ctx, userId);
  await insertModerationAction(ctx, userId);

  return { userId, partnerId, conversationId, userMessageId, partnerMessageId, sensitiveQuestionId, tagId, dateProposalId };
}

// =========================================================================
// Tests
// =========================================================================

test('deleteMyAccount: erases answers (including sensitive-flagged), user_tags, and hard_filters entirely', async () => {
  const ctx = buildCtx();
  const fx = await buildFixture(ctx);
  const userCtx = buildCtx({ actor: userActor(fx.userId) });

  await profile.deleteMyAccount(userCtx);

  const { rows: answerRows } = await ctx.db.query('SELECT * FROM user_question_answers WHERE user_id = $1', [fx.userId]);
  assert.equal(answerRows.length, 0, 'every answer, including the sensitive-flagged one, must be gone');

  const { rows: tagRows } = await ctx.db.query('SELECT * FROM user_tags WHERE user_id = $1', [fx.userId]);
  assert.equal(tagRows.length, 0, 'private_reciprocal and public tags alike must be gone');

  const { rows: filterRows } = await ctx.db.query('SELECT * FROM hard_filters WHERE user_id = $1', [fx.userId]);
  assert.equal(filterRows.length, 0);
});

test('deleteMyAccount: erases this user\'s own message content but leaves the conversation row and the partner\'s messages completely intact', async () => {
  const ctx = buildCtx();
  const fx = await buildFixture(ctx);
  const userCtx = buildCtx({ actor: userActor(fx.userId) });

  const conversationBefore = (await ctx.db.query('SELECT * FROM conversations WHERE id = $1', [fx.conversationId])).rows[0];
  const partnerMessageBefore = (await ctx.db.query('SELECT * FROM messages WHERE id = $1', [fx.partnerMessageId])).rows[0];

  await profile.deleteMyAccount(userCtx);

  const { rows: userMsgRows } = await ctx.db.query('SELECT body FROM messages WHERE id = $1', [fx.userMessageId]);
  assert.equal(userMsgRows[0]?.body, DELETED_MESSAGE_PLACEHOLDER, "the deleted user's own message content must be erased");

  const { rows: partnerMsgRows } = await ctx.db.query('SELECT * FROM messages WHERE id = $1', [fx.partnerMessageId]);
  assert.deepEqual(partnerMsgRows[0], partnerMessageBefore, "the OTHER party's own message must be completely untouched");

  const { rows: convRows } = await ctx.db.query('SELECT * FROM conversations WHERE id = $1', [fx.conversationId]);
  assert.deepEqual(convRows[0], conversationBefore, 'the conversation row itself (and thus the partner\'s ability to see their own thread) must not be corrupted');

  // The conversation is still findable/usable by the partner:
  const { rows: stillFindable } = await ctx.db.query(
    'SELECT count(*)::int AS n FROM messages WHERE conversation_id = $1',
    [fx.conversationId],
  );
  assert.equal(stillFindable[0].n, 2, 'both messages still exist as rows, only the deleted user\'s content was scrubbed, nothing was deleted out from under the partner');
});

test('deleteMyAccount: retains financial/ledger records untouched (payment_holds, payment_ledger)', async () => {
  const ctx = buildCtx();
  const fx = await buildFixture(ctx);
  const userCtx = buildCtx({ actor: userActor(fx.userId) });

  const holdsBefore = (await ctx.db.query('SELECT * FROM payment_holds WHERE user_id = $1 ORDER BY id', [fx.userId])).rows;
  const ledgerBefore = (await ctx.db.query('SELECT * FROM payment_ledger WHERE user_id = $1 ORDER BY id', [fx.userId])).rows;
  assert.ok(holdsBefore.length > 0 && ledgerBefore.length > 0, 'fixture sanity check');

  await profile.deleteMyAccount(userCtx);

  const holdsAfter = (await ctx.db.query('SELECT * FROM payment_holds WHERE user_id = $1 ORDER BY id', [fx.userId])).rows;
  const ledgerAfter = (await ctx.db.query('SELECT * FROM payment_ledger WHERE user_id = $1 ORDER BY id', [fx.userId])).rows;
  assert.deepEqual(holdsAfter, holdsBefore, 'payment_holds rows must survive deletion byte-for-byte');
  assert.deepEqual(ledgerAfter, ledgerBefore, 'payment_ledger rows must survive deletion byte-for-byte, §14.8 immutable ledger');
});

test('deleteMyAccount: retains the moderation/safety audit trail (reports, trust_events, moderation_actions) so ban evasion cannot be laundered by self-deleting', async () => {
  const ctx = buildCtx();
  const fx = await buildFixture(ctx);
  const userCtx = buildCtx({ actor: userActor(fx.userId) });

  const reportsBefore = (await ctx.db.query('SELECT count(*)::int AS n FROM reports WHERE reported_id = $1', [fx.userId])).rows[0].n;
  const trustEventsBefore = (await ctx.db.query('SELECT count(*)::int AS n FROM trust_events WHERE user_id = $1', [fx.userId])).rows[0].n;
  const modActionsBefore = (await ctx.db.query('SELECT count(*)::int AS n FROM moderation_actions WHERE user_id = $1', [fx.userId])).rows[0].n;
  assert.ok(reportsBefore > 0 && trustEventsBefore > 0 && modActionsBefore > 0, 'fixture sanity check');

  await profile.deleteMyAccount(userCtx);

  const reportsAfter = (await ctx.db.query('SELECT count(*)::int AS n FROM reports WHERE reported_id = $1', [fx.userId])).rows[0].n;
  const trustEventsAfter = (await ctx.db.query('SELECT count(*)::int AS n FROM trust_events WHERE user_id = $1', [fx.userId])).rows[0].n;
  const modActionsAfter = (await ctx.db.query('SELECT count(*)::int AS n FROM moderation_actions WHERE user_id = $1', [fx.userId])).rows[0].n;
  assert.equal(reportsAfter, reportsBefore);
  assert.equal(trustEventsAfter, trustEventsBefore);
  assert.equal(modActionsAfter, modActionsBefore);
});

test('deleteMyAccount: profile fields (including the new distance_precision_floor_km) are scrubbed, photos removed, sessions revoked, status flips', async () => {
  const ctx = buildCtx();
  const fx = await buildFixture(ctx);
  const userCtx = buildCtx({ actor: userActor(fx.userId) });

  await ctx.db.query(
    `INSERT INTO user_photos (user_id, image_url, position, is_primary, moderation_status, face_detected) VALUES ($1, 'https://example.test/a.jpg', 0, true, 'approved', true)`,
    [fx.userId],
  );
  await ctx.db.query(
    `INSERT INTO refresh_sessions (id, user_id, token_hash, created_at, expires_at) VALUES (gen_random_uuid(), $1, 'h', now(), now() + interval '1 day')`,
    [fx.userId],
  );

  await profile.deleteMyAccount(userCtx);

  const { rows: userRows } = await ctx.db.query('SELECT status FROM users WHERE id = $1', [fx.userId]);
  assert.equal(userRows[0].status, 'deleted');

  const { rows: profileRows } = await ctx.db.query(
    'SELECT display_name, bio, city, latitude, longitude, distance_precision_floor_km FROM profiles WHERE user_id = $1',
    [fx.userId],
  );
  assert.equal(profileRows[0].display_name, 'Deleted user');
  assert.equal(profileRows[0].bio, '');
  assert.equal(profileRows[0].city, null);
  assert.equal(profileRows[0].latitude, null);
  assert.equal(profileRows[0].longitude, null);
  assert.equal(profileRows[0].distance_precision_floor_km, null);

  const { rows: photoRows } = await ctx.db.query('SELECT count(*)::int AS n FROM user_photos WHERE user_id = $1', [fx.userId]);
  assert.equal(photoRows[0].n, 0);

  const { rows: sessionRows } = await ctx.db.query('SELECT revoked_at FROM refresh_sessions WHERE user_id = $1', [fx.userId]);
  assert.notEqual(sessionRows[0].revoked_at, null);
});

test('deleteMyAccount: idempotent, running it twice produces the exact same end state and never errors', async () => {
  const ctx = buildCtx();
  const fx = await buildFixture(ctx);
  const userCtx = buildCtx({ actor: userActor(fx.userId) });

  await profile.deleteMyAccount(userCtx);

  const snapshot = async () => ({
    user: (await ctx.db.query('SELECT * FROM users WHERE id = $1', [fx.userId])).rows[0],
    profile: (await ctx.db.query('SELECT * FROM profiles WHERE user_id = $1', [fx.userId])).rows[0],
    answers: (await ctx.db.query('SELECT * FROM user_question_answers WHERE user_id = $1', [fx.userId])).rows,
    tags: (await ctx.db.query('SELECT * FROM user_tags WHERE user_id = $1', [fx.userId])).rows,
    filters: (await ctx.db.query('SELECT * FROM hard_filters WHERE user_id = $1', [fx.userId])).rows,
    messages: (await ctx.db.query('SELECT * FROM messages WHERE sender_id = $1', [fx.userId])).rows,
  });
  const after1 = await snapshot();

  // Second run must not throw.
  await profile.deleteMyAccount(userCtx);
  const after2 = await snapshot();

  assert.deepEqual(after2, after1, 're-running deletion must be a complete no-op on an already-deleted account');
});

test("deleteMyAccount: does not touch the OTHER party's own account, profile, answers, or tags at all", async () => {
  const ctx = buildCtx();
  const fx = await buildFixture(ctx);
  await insertQuestion(ctx, true).then((qid) => insertAnswer(ctx, fx.partnerId, qid));
  const partnerTag = await insertTag(ctx);
  await insertUserTag(ctx, fx.partnerId, partnerTag, 'public');

  const partnerBefore = {
    user: (await ctx.db.query('SELECT * FROM users WHERE id = $1', [fx.partnerId])).rows[0],
    profile: (await ctx.db.query('SELECT * FROM profiles WHERE user_id = $1', [fx.partnerId])).rows[0],
    answers: (await ctx.db.query('SELECT * FROM user_question_answers WHERE user_id = $1', [fx.partnerId])).rows,
    tags: (await ctx.db.query('SELECT * FROM user_tags WHERE user_id = $1', [fx.partnerId])).rows,
  };

  const userCtx = buildCtx({ actor: userActor(fx.userId) });
  await profile.deleteMyAccount(userCtx);

  const partnerAfter = {
    user: (await ctx.db.query('SELECT * FROM users WHERE id = $1', [fx.partnerId])).rows[0],
    profile: (await ctx.db.query('SELECT * FROM profiles WHERE user_id = $1', [fx.partnerId])).rows[0],
    answers: (await ctx.db.query('SELECT * FROM user_question_answers WHERE user_id = $1', [fx.partnerId])).rows,
    tags: (await ctx.db.query('SELECT * FROM user_tags WHERE user_id = $1', [fx.partnerId])).rows,
  };

  assert.deepEqual(partnerAfter, partnerBefore);
});
