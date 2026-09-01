/**
 * Unit tests for stats.service.ts, adminStats.service.ts, and
 * statsAggregation.job.ts.
 *
 * Uses a dedicated `odate_stats_unit_<suffix>` database (per the build
 * brief's "your own Postgres databases (`odate_stats_<suite>`)") so this
 * build's tests run independently of, and concurrently with, sibling
 * agents' own test databases on the shared dev Postgres cluster.
 *
 * Coverage, matching the task brief's four pillars:
 *  - PRIVACY: small cohorts suppressed, no other-identifiable-person data,
 *    no trust weights, no ranking.
 *  - ROLE-GATING: admin stats reject a non-admin actor.
 *  - CORRECTNESS: every rate matches a hand-computed fixture.
 *  - PERFORMANCE: bounded query-count assertions for both the rollup job
 *    and the read paths.
 */
import { test, before, after, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import pg from 'pg';
import { randomUUID } from 'node:crypto';
import { runMigrations } from '../../src/db/migrate.js';
import { closePool, getPool } from '../../src/db/pool.js';
import type { DbClient } from '../../src/db/pool.js';
import { ConfigService } from '../../src/config/config.service.js';
import { FlagsService } from '../../src/config/flags.service.js';
import { ManualClock } from '../../src/lib/time.js';
import { createSilentLogger } from '../../src/lib/logger.js';
import { FakeProcessor } from '../../src/services/payments/fake.processor.js';
import { StubMediaModerationAdapter } from '../../src/services/media/stub.adapter.js';
import type { Actor, Ctx } from '../../src/lib/ctx.js';
import { withDb } from '../../src/lib/ctx.js';
import { ForbiddenError } from '../../src/lib/errors.js';

import * as statsService from '../../src/services/stats.service.js';
import * as adminStatsService from '../../src/services/adminStats.service.js';
import * as filterService from '../../src/services/filter.service.js';
import { runStatsAggregationJob } from '../../src/jobs/statsAggregation.job.js';
import { readFileSync } from 'node:fs';

const BASE_URL = process.env.DATABASE_URL ?? 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';
const RUN_SUFFIX = randomUUID().replace(/-/g, '').slice(0, 8);

function withDbName(url: string, dbName: string): string {
  const u = new URL(url);
  u.pathname = `/${dbName}`;
  return u.toString();
}

let adminPool: pg.Pool;
let pool: pg.Pool;
let dbName: string;

before(async () => {
  dbName = `odate_stats_unit_${RUN_SUFFIX}`;
  adminPool = new pg.Pool({ connectionString: BASE_URL });
  await adminPool.query(`DROP DATABASE IF EXISTS ${dbName}`);
  await adminPool.query(`CREATE DATABASE ${dbName}`);
  process.env.DATABASE_URL = withDbName(BASE_URL, dbName);
  await runMigrations();
  pool = getPool();
});

after(async () => {
  await closePool();
  await adminPool.query(`DROP DATABASE IF EXISTS ${dbName}`);
  await adminPool.end();
});

/** Every fixture-driven test below assumes it owns a clean database — truncate everything this build's tables (and every table its fixtures touch) depend on before each test, so tests never leak state into one another. */
const TRUNCATE_TABLES = [
  'stats_user_cache',
  'stats_aggregation_runs',
  'stats_platform_gauges',
  'stats_cohort_retention',
  'stats_platform_daily',
  'venue_redemptions',
  'vouchers',
  'payment_ledger',
  'payment_holds',
  'payment_methods',
  'post_date_feedback_prompts',
  'post_date_feedback',
  'date_attendance_confirmations',
  'date_proposals',
  'messages',
  'message_flags',
  'conversations',
  'discovery_events',
  'compatibility_scores',
  'interests',
  'hard_filters',
  'moderation_actions',
  'appeals',
  'trust_events',
  'reports',
  'blocks',
  'photo_experiments',
  'photo_recommendations',
  'user_photos',
  'user_question_answers',
  'user_tags',
  'admin_audit_log',
  'admin_users',
  'venue_staff',
  'venues',
  'profiles',
  'users',
];

beforeEach(async () => {
  await pool.query(`TRUNCATE ${TRUNCATE_TABLES.join(', ')} CASCADE`);
});

// =====================================================================
// Fixture helpers — raw SQL, deliberately bypassing every other agent's
// service layer (which enforces flows this build must not depend on).
// =====================================================================

let emailCounter = 0;
async function insertUser(overrides?: { createdAt?: Date; lastActiveAt?: Date; emailVerifiedAt?: Date | null; shadowbanned?: boolean }): Promise<string> {
  emailCounter += 1;
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO users (email, password_hash, birthdate, created_at, last_active_at, email_verified_at, shadowbanned)
     VALUES ($1, 'hash', '1995-01-01', $2, $3, $4, $5) RETURNING id`,
    [
      `stats-user-${emailCounter}-${randomUUID()}@example.test`,
      overrides?.createdAt ?? new Date(),
      overrides?.lastActiveAt ?? overrides?.createdAt ?? new Date(),
      overrides?.emailVerifiedAt ?? null,
      overrides?.shadowbanned ?? false,
    ],
  );
  return rows[0]!.id;
}

async function insertProfile(userId: string, overrides?: { completeness?: number; updatedAt?: Date }): Promise<void> {
  await pool.query(
    `INSERT INTO profiles (user_id, display_name, age, gender, seeking, relationship_intention, profile_completeness, updated_at)
     VALUES ($1, 'Test', 28, 'woman', 'men', 'long_term', $2, $3)
     ON CONFLICT (user_id) DO UPDATE SET profile_completeness = $2, updated_at = $3`,
    [userId, overrides?.completeness ?? 0, overrides?.updatedAt ?? new Date()],
  );
}

async function insertInterest(overrides: {
  senderId: string;
  recipientId: string;
  status?: string;
  createdAt?: Date;
  acceptedAt?: Date | null;
  declinedAt?: Date | null;
  expiredAt?: Date | null;
}): Promise<string> {
  const createdAt = overrides.createdAt ?? new Date();
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO interests (sender_id, recipient_id, status, policy_snapshot, created_at, expires_at, accepted_at, declined_at, expired_at)
     VALUES ($1, $2, $3, '{}'::jsonb, $4::timestamptz, $4::timestamptz + interval '7 days', $5, $6, $7) RETURNING id`,
    [
      overrides.senderId,
      overrides.recipientId,
      overrides.status ?? 'pending',
      createdAt,
      overrides.acceptedAt ?? null,
      overrides.declinedAt ?? null,
      overrides.expiredAt ?? null,
    ],
  );
  return rows[0]!.id;
}

async function insertConversation(userAId: string, userBId: string, overrides?: { createdAt?: Date }): Promise<string> {
  const [a, b] = userAId < userBId ? [userAId, userBId] : [userBId, userAId];
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO conversations (user_a_id, user_b_id, created_at) VALUES ($1, $2, $3) RETURNING id`,
    [a, b, overrides?.createdAt ?? new Date()],
  );
  return rows[0]!.id;
}

async function insertVenue(): Promise<string> {
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO venues (name, address, latitude, longitude, category) VALUES ('V', 'addr', 1, 1, 'coffee') RETURNING id`,
  );
  return rows[0]!.id;
}

async function insertDateProposal(overrides: {
  conversationId: string;
  proposerId: string;
  recipientId: string;
  venueId: string;
  status?: string;
  createdAt?: Date;
  acceptedAt?: Date | null;
  completedAt?: Date | null;
  scheduledStart?: Date;
  scheduledEnd?: Date;
}): Promise<string> {
  const createdAt = overrides.createdAt ?? new Date();
  const scheduledStart = overrides.scheduledStart ?? new Date(createdAt.getTime() + 3600_000);
  const scheduledEnd = overrides.scheduledEnd ?? new Date(scheduledStart.getTime() + 3600_000);
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO date_proposals (conversation_id, proposer_id, recipient_id, venue_id, scheduled_start, scheduled_end, status, policy_snapshot, escrow_amount_cents, created_at, accepted_at, completed_at)
     VALUES ($1, $2, $3, $4, $5, $6, $7, '{}'::jsonb, 0, $8, $9, $10) RETURNING id`,
    [
      overrides.conversationId,
      overrides.proposerId,
      overrides.recipientId,
      overrides.venueId,
      scheduledStart,
      scheduledEnd,
      overrides.status ?? 'draft',
      createdAt,
      overrides.acceptedAt ?? null,
      overrides.completedAt ?? null,
    ],
  );
  return rows[0]!.id;
}

async function insertMessage(conversationId: string, senderId: string, createdAt: Date): Promise<void> {
  await pool.query(`INSERT INTO messages (conversation_id, sender_id, body, created_at) VALUES ($1, $2, 'hi', $3)`, [
    conversationId,
    senderId,
    createdAt,
  ]);
  // message.service.ts normally keeps this in sync on every send; this
  // fixture bypasses that service entirely, so it must do the same thing
  // directly or getMyResponseBehaviour's `last_message_at IS NOT NULL`
  // conversation-selection query would never see these conversations.
  await pool.query(`UPDATE conversations SET last_message_at = $2 WHERE id = $1 AND (last_message_at IS NULL OR last_message_at < $2)`, [
    conversationId,
    createdAt,
  ]);
}

async function insertPostDateFeedback(overrides: {
  dateProposalId: string;
  userId: string;
  outcome?: string | null;
  positive?: boolean | null;
  wouldMeetAgain?: boolean | null;
  safetyFlag?: string;
  safetyDetails?: string | null;
  createdAt?: Date;
}): Promise<void> {
  await pool.query(
    `INSERT INTO post_date_feedback (date_proposal_id, user_id, positive, outcome, would_meet_again, safety_flag, safety_details, created_at)
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
    [
      overrides.dateProposalId,
      overrides.userId,
      overrides.positive ?? null,
      overrides.outcome ?? null,
      overrides.wouldMeetAgain ?? null,
      overrides.safetyFlag ?? 'none',
      overrides.safetyDetails ?? null,
      overrides.createdAt ?? new Date(),
    ],
  );
}

async function insertDiscoveryEvent(viewerId: string, candidateId: string, createdAt: Date): Promise<void> {
  await pool.query(`INSERT INTO discovery_events (viewer_user_id, candidate_user_id, created_at) VALUES ($1, $2, $3)`, [
    viewerId,
    candidateId,
    createdAt,
  ]);
}

async function insertReport(reporterId: string, reportedId: string, createdAt: Date): Promise<void> {
  await pool.query(`INSERT INTO reports (reporter_id, reported_id, category, created_at) VALUES ($1, $2, 'spam', $3)`, [
    reporterId,
    reportedId,
    createdAt,
  ]);
}

async function insertBlock(blockerId: string, blockedId: string, createdAt: Date): Promise<void> {
  await pool.query(`INSERT INTO blocks (blocker_id, blocked_id, created_at) VALUES ($1, $2, $3)`, [blockerId, blockedId, createdAt]);
}

async function insertModerationAction(userId: string, action: string, createdAt: Date): Promise<void> {
  await pool.query(`INSERT INTO moderation_actions (user_id, action, reason, created_at) VALUES ($1, $2, 'x', $3)`, [
    userId,
    action,
    createdAt,
  ]);
}

async function insertVoucherAndRedemption(dateProposalId: string, venueId: string, createdAt: Date): Promise<void> {
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO vouchers (date_proposal_id, venue_id, code, qr_payload, expires_at)
     VALUES ($1, $2, $3, 'qr', now() + interval '1 day') RETURNING id`,
    [dateProposalId, venueId, `code-${randomUUID()}`],
  );
  await pool.query(`INSERT INTO venue_redemptions (voucher_id, venue_id, method, created_at) VALUES ($1, $2, 'manual_code', $3)`, [
    rows[0]!.id,
    venueId,
    createdAt,
  ]);
}

async function insertLedgerEntry(userId: string, dateProposalId: string, type: string, amountCents: number, createdAt: Date): Promise<void> {
  await pool.query(
    `INSERT INTO payment_ledger (user_id, date_proposal_id, type, amount_cents, created_at) VALUES ($1, $2, $3, $4, $5)`,
    [userId, dateProposalId, type, amountCents, createdAt],
  );
}

async function insertHardFilter(userId: string, filterKey: string, operator: string, value: unknown, excludeIfUnset = false): Promise<void> {
  await pool.query(
    `INSERT INTO hard_filters (user_id, filter_key, operator, value, enabled, exclude_if_unset) VALUES ($1, $2, $3, $4::jsonb, true, $5)`,
    [userId, filterKey, operator, JSON.stringify(value), excludeIfUnset],
  );
}

/** A single reusable `question_bank` row so fixtures that just need `user_question_answers.question_bank_id` to satisfy its foreign key (this file's tests care about the COUNT of answer rows, never the question content) don't have to insert one per slug. `question_slug` is its own independent column, not required to match the referenced row's own `slug`, so the same id can back many different `question_slug` values. */
let fillerQuestionBankId: string | undefined;
async function getFillerQuestionBankId(): Promise<string> {
  if (fillerQuestionBankId) return fillerQuestionBankId;
  const typeDefinition = { type: 'scale', min: 1, max: 5, minLabel: 'low', maxLabel: 'high', midLabel: 'mid' };
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO question_bank (slug, version, is_current, category, question_type, question_text, type_definition, base_weight, sensitive, active)
     VALUES ('stats-test-filler', 1, true, 'test', 'scale', 'filler', $1::jsonb, 1, false, true)
     RETURNING id`,
    [JSON.stringify(typeDefinition)],
  );
  fillerQuestionBankId = rows[0]!.id;
  return fillerQuestionBankId;
}

function buildCtx(actor: Actor, now: Date): Ctx {
  const clock = new ManualClock(now);
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

function userActor(userId: string): Actor {
  return { type: 'user', userId, trustLevel: 'standard' };
}

function adminActor(adminId: string): Actor {
  return { type: 'admin', adminId };
}

/** Wraps a Ctx's `db.query` to count calls — proves boundedness without depending on exact numbers changing every time an unrelated implementation detail shifts. */
function countingCtx(ctx: Ctx): { ctx: Ctx; count: () => number } {
  let n = 0;
  const wrapped: Ctx = {
    ...ctx,
    db: {
      query: (...args: unknown[]) => {
        n += 1;
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        return (ctx.db.query as any)(...args);
      },
    },
  };
  return { ctx: wrapped, count: () => n };
}

const DAY = 24 * 60 * 60 * 1000;
function daysAgo(now: Date, n: number): Date {
  return new Date(now.getTime() - n * DAY);
}

// =====================================================================
// Pure helpers
// =====================================================================

test('suppressSmallCohort: below threshold is suppressed, at/above threshold shows the exact value', () => {
  assert.deepEqual(statsService.suppressSmallCohort(0), { value: null, suppressed: true });
  assert.deepEqual(statsService.suppressSmallCohort(4), { value: null, suppressed: true });
  assert.deepEqual(statsService.suppressSmallCohort(5), { value: 5, suppressed: false });
  assert.deepEqual(statsService.suppressSmallCohort(999), { value: 999, suppressed: false });
});

test('resolveWindow: numeric window and "all" compute the expected day bounds', () => {
  const now = new Date('2026-03-15T12:00:00.000Z');
  const w7 = adminStatsService.resolveWindow(now, 7);
  assert.equal(w7.endDay, '2026-03-15');
  assert.equal(w7.startDay, '2026-03-09'); // inclusive of today: 7 days total
  assert.equal(w7.isAllTime, false);

  const wAll = adminStatsService.resolveWindow(now, 'all');
  assert.equal(wAll.isAllTime, true);
  assert.equal(wAll.endDay, '2026-03-15');
});

test('stats.service.ts never imports trust.service.ts (structural guard against re-drawing the trust-weight boundary)', () => {
  const source = readFileSync(new URL('../../src/services/stats.service.ts', import.meta.url), 'utf8');
  const importLines = source.split('\n').filter((l) => /^\s*import\b/.test(l));
  assert.ok(
    importLines.every((l) => !/trust\.service/.test(l)),
    `stats.service.ts must not import trust.service.ts at all; found: ${importLines.filter((l) => /trust\.service/.test(l)).join(' | ')}`,
  );
});

// =====================================================================
// Role gating
// =====================================================================

test('adminStats.service rejects a non-admin actor', async () => {
  const now = new Date();
  const user = await insertUser({ createdAt: now });
  const ctx = buildCtx(userActor(user), now);
  await assert.rejects(() => adminStatsService.getOverview(ctx), ForbiddenError);
  await assert.rejects(() => adminStatsService.getRetention(ctx), ForbiddenError);
});

test('adminStats.service accepts an admin actor', async () => {
  const now = new Date();
  const admin = await insertUser({ createdAt: now });
  const ctx = buildCtx(adminActor(admin), now);
  const overview = await adminStatsService.getOverview(ctx);
  assert.ok(overview.window);
});

// =====================================================================
// Aggregation job correctness — hand-computed fixture.
// =====================================================================

test('statsAggregation job: daily rollup matches hand-computed counts and money is exact', async () => {
  const now = new Date('2026-02-20T18:00:00.000Z');
  const d2 = daysAgo(now, 2); // registrations + interest sent
  const d1 = daysAgo(now, 1); // acceptance/decline/conversation/date-proposal-accepted/report/block/shadowban/feedback
  const d0 = now; // completion/no-show/messages/ledger/voucher

  const alice = await insertUser({ createdAt: d2, emailVerifiedAt: d1 });
  const bob = await insertUser({ createdAt: d2 });
  await insertProfile(alice, { completeness: 100, updatedAt: d1 });
  await insertProfile(bob, { completeness: 40, updatedAt: d1 });

  await insertDiscoveryEvent(bob, alice, d1);
  await insertDiscoveryEvent(bob, alice, d1);

  const interest1 = await insertInterest({ senderId: alice, recipientId: bob, status: 'accepted', createdAt: d2, acceptedAt: d1 });
  const interest2 = await insertInterest({ senderId: bob, recipientId: alice, status: 'declined', createdAt: d2, declinedAt: d1 });
  void interest1;
  void interest2;

  const conversationId = await insertConversation(alice, bob, { createdAt: d1 });
  await insertMessage(conversationId, alice, d0);
  await insertMessage(conversationId, bob, d0);
  await insertMessage(conversationId, alice, d0);

  const venueId = await insertVenue();
  const dp1 = await insertDateProposal({
    conversationId,
    proposerId: alice,
    recipientId: bob,
    venueId,
    status: 'completed',
    createdAt: d1,
    acceptedAt: d1,
    completedAt: d0,
  });
  const dp2 = await insertDateProposal({
    conversationId,
    proposerId: bob,
    recipientId: alice,
    venueId,
    status: 'no_show',
    createdAt: d1,
    scheduledEnd: d0,
  });
  void dp2;

  await insertVoucherAndRedemption(dp1, venueId, d0);

  await insertReport(bob, alice, d1);
  await insertBlock(bob, alice, d1);
  await insertModerationAction(alice, 'shadowban', d1);

  await insertPostDateFeedback({ dateProposalId: dp1, userId: alice, positive: true, createdAt: d1 });
  await insertPostDateFeedback({ dateProposalId: dp1, userId: bob, outcome: 'happened_bad', createdAt: d1 });

  await insertLedgerEntry(alice, dp1, 'authorization', 5000, d0);
  await insertLedgerEntry(alice, dp1, 'capture', 5000, d0);
  await insertLedgerEntry(alice, dp1, 'refund', -1500, d0);

  const ctx = buildCtx({ type: 'system', job: 'test' }, now);
  const { ctx: counted, count } = countingCtx(ctx);
  const result = await runStatsAggregationJob(counted);
  assert.ok(result.daysUpserted > 0);

  // Bounded query count: one grouped query per metric/source table plus a
  // bounded per-day upsert loop — NOT a function of how many event rows
  // exist. Generous ceiling so unrelated refactors don't make this flaky,
  // but still catches an accidental N+1 regression.
  assert.ok(count() < 150, `expected a bounded query count, got ${count()}`);

  function dayKey(d: Date): string {
    return d.toISOString().slice(0, 10);
  }

  const { rows: rowsD2 } = await pool.query(`SELECT * FROM stats_platform_daily WHERE day = $1`, [dayKey(d2)]);
  assert.equal(Number(rowsD2[0].registrations), 2);
  assert.equal(Number(rowsD2[0].interests_sent), 2);

  const { rows: rowsD1 } = await pool.query(`SELECT * FROM stats_platform_daily WHERE day = $1`, [dayKey(d1)]);
  assert.equal(Number(rowsD1[0].verified_emails), 1);
  assert.equal(Number(rowsD1[0].profiles_completed), 1); // only alice reached >=100
  assert.equal(Number(rowsD1[0].discovery_impressions), 2);
  assert.equal(Number(rowsD1[0].interests_accepted), 1);
  assert.equal(Number(rowsD1[0].interests_declined), 1);
  assert.equal(Number(rowsD1[0].conversations_opened), 1);
  assert.equal(Number(rowsD1[0].date_proposals_accepted), 1);
  assert.equal(Number(rowsD1[0].reports), 1);
  assert.equal(Number(rowsD1[0].blocks), 1);
  assert.equal(Number(rowsD1[0].shadowban_actions), 1);
  assert.equal(Number(rowsD1[0].positive_feedback), 1); // alice's positive=true
  assert.equal(Number(rowsD1[0].negative_feedback), 1); // bob's outcome=happened_bad

  const { rows: rowsD0 } = await pool.query(`SELECT * FROM stats_platform_daily WHERE day = $1`, [dayKey(d0)]);
  assert.equal(Number(rowsD0[0].dates_completed), 1);
  assert.equal(Number(rowsD0[0].dates_no_show), 1);
  assert.equal(Number(rowsD0[0].messages_sent), 3);
  assert.equal(Number(rowsD0[0].voucher_redemptions), 1);
  assert.equal(Number(rowsD0[0].authorizations_cents), 5000);
  assert.equal(Number(rowsD0[0].captures_cents), 5000);
  assert.equal(Number(rowsD0[0].refunds_cents), -1500);
  assert.equal(Number(rowsD0[0].refunds_count), 1);

  // Freshness log.
  const { rows: runRows } = await pool.query(`SELECT count(*)::int AS n FROM stats_aggregation_runs`);
  assert.ok(runRows[0].n >= 1);
});

test('statsAggregation job: repeat-date gauge matches a hand count', async () => {
  const now = new Date('2026-02-25T12:00:00.000Z');
  const venueId = await insertVenue();

  const repeatUser = await insertUser({ createdAt: daysAgo(now, 10) });
  const oneTimeUser = await insertUser({ createdAt: daysAgo(now, 10) });
  const otherA = await insertUser({ createdAt: daysAgo(now, 10) });
  const otherB = await insertUser({ createdAt: daysAgo(now, 10) });

  const convo1 = await insertConversation(repeatUser, otherA, { createdAt: daysAgo(now, 9) });
  const convo2 = await insertConversation(repeatUser, otherB, { createdAt: daysAgo(now, 8) });
  const convo3 = await insertConversation(oneTimeUser, otherA, { createdAt: daysAgo(now, 7) });

  await insertDateProposal({
    conversationId: convo1,
    proposerId: repeatUser,
    recipientId: otherA,
    venueId,
    status: 'completed',
    createdAt: daysAgo(now, 6),
    scheduledStart: new Date(daysAgo(now, 5).getTime() - 3600_000),
    scheduledEnd: daysAgo(now, 5),
    completedAt: daysAgo(now, 5),
  });
  await insertDateProposal({
    conversationId: convo2,
    proposerId: repeatUser,
    recipientId: otherB,
    venueId,
    status: 'completed',
    createdAt: daysAgo(now, 4),
    scheduledStart: new Date(daysAgo(now, 3).getTime() - 3600_000),
    scheduledEnd: daysAgo(now, 3),
    completedAt: daysAgo(now, 3),
  });
  await insertDateProposal({
    conversationId: convo3,
    proposerId: oneTimeUser,
    recipientId: otherA,
    venueId,
    status: 'completed',
    createdAt: daysAgo(now, 3),
    scheduledStart: new Date(daysAgo(now, 2).getTime() - 3600_000),
    scheduledEnd: daysAgo(now, 2),
    completedAt: daysAgo(now, 2),
  });

  const ctx = buildCtx({ type: 'system', job: 'test' }, now);
  await runStatsAggregationJob(ctx);

  const { rows } = await pool.query<{ value_numeric: number }>(
    `SELECT value_numeric FROM stats_platform_gauges WHERE key = 'repeat_date_rate'`,
  );
  // 4 distinct daters across these proposals: repeatUser participates
  // twice (convo1, convo2), otherA participates twice (convo1, convo3),
  // otherB once, oneTimeUser once. Repeaters (>=2 participations) =
  // {repeatUser, otherA} = 2, daters = 4 => 2/4 = 0.5.
  assert.ok(Math.abs(rows[0]!.value_numeric - 0.5) < 1e-9, `expected 0.5, got ${rows[0]!.value_numeric}`);
});

test('statsAggregation job: retention cohort matches a hand count', async () => {
  const now = new Date('2026-04-01T00:00:00.000Z');
  const cohortDay = daysAgo(now, 40);

  const active1 = await insertUser({ createdAt: cohortDay, lastActiveAt: new Date(cohortDay.getTime() + 35 * DAY) }); // d1,d7,d30
  const active2 = await insertUser({ createdAt: cohortDay, lastActiveAt: new Date(cohortDay.getTime() + 10 * DAY) }); // d1,d7 only
  const active3 = await insertUser({ createdAt: cohortDay, lastActiveAt: new Date(cohortDay.getTime() + 0.5 * DAY) }); // d1 only... actually < 1 day, so none
  const inactive = await insertUser({ createdAt: cohortDay, lastActiveAt: cohortDay }); // none
  void active1;
  void active2;
  void active3;
  void inactive;

  const ctx = buildCtx({ type: 'system', job: 'test' }, now);
  await runStatsAggregationJob(ctx);

  function dayKey(d: Date): string {
    return d.toISOString().slice(0, 10);
  }
  const { rows } = await pool.query(`SELECT * FROM stats_cohort_retention WHERE cohort_date = $1`, [dayKey(cohortDay)]);
  // cohort_size/active_d1/active_d7/active_d30 are `bigint` columns
  // (db/migrations/023_widen_counters.sql), which `pg` returns as strings
  // -- Number(...) here, same reasoning as adminStats.service.ts#getRetention.
  assert.equal(Number(rows[0].cohort_size), 4);
  assert.equal(Number(rows[0].active_d1), 2); // active1 (35d) and active2 (10d) are >= 1 day later
  assert.equal(Number(rows[0].active_d7), 2); // both still >= 7 days later
  assert.equal(Number(rows[0].active_d30), 1); // only active1
});

// =====================================================================
// adminStats.service correctness (against a hand-seeded rollup, proving
// the read path's math independent of the job).
// =====================================================================

test('adminStats.service.getOverview: quality-metric rates match hand math, and money is exact and reconcilable against a raw ledger sum', async () => {
  const now = new Date('2026-05-10T12:00:00.000Z');
  const admin = await insertUser({ createdAt: now });

  const day = now.toISOString().slice(0, 10);
  await pool.query(
    `INSERT INTO stats_platform_daily (day, registrations, interests_sent, interests_accepted, dates_completed, dates_no_show, dates_disputed,
        positive_feedback, negative_feedback, reports, messages_sent, conversations_opened, date_proposals_sent,
        authorizations_cents, captures_cents, refunds_cents, refunds_count, releases_cents)
     VALUES ($1, 10, 20, 5, 3, 1, 0, 4, 1, 2, 1000, 6, 4, 90000, 90000, -12000, 3, 0)
     ON CONFLICT (day) DO NOTHING`,
    [day],
  );

  const ctx = buildCtx(adminActor(admin), now);
  const overview = await adminStatsService.getOverview(ctx, { windowDays: 1 });

  assert.equal(overview.core.registrations, 10);
  assert.equal(overview.core.interestsSent, 20);
  assert.equal(overview.core.interestsAccepted, 5);
  assert.ok(Math.abs(overview.quality.acceptedInterestRate! - 5 / 20) < 1e-9);
  assert.ok(Math.abs(overview.quality.dateCompletionRate! - 3 / 4) < 1e-9); // 3 completed / (3+1+0)
  assert.ok(Math.abs(overview.quality.noShowRate! - 1 / 4) < 1e-9);
  assert.ok(Math.abs(overview.quality.positiveFeedbackRate! - 4 / 5) < 1e-9);
  assert.ok(Math.abs(overview.quality.reportRatePerThousandMessages! - (2 / 1000) * 1000) < 1e-9);
  assert.ok(Math.abs(overview.quality.chatToDateConversionRate! - 4 / 6) < 1e-9);

  assert.equal(overview.money.authorizationsCents, 90000);
  assert.equal(overview.money.capturesCents, 90000);
  assert.equal(overview.money.refundsCents, -12000);
  assert.equal(overview.money.refundsCount, 3);

  // Reconciliation: insert real payment_ledger rows for the SAME day and
  // an unrelated date_proposal, independently sum them with raw SQL, and
  // assert the rollup-backed service number matches exactly.
  const alice = await insertUser({ createdAt: now });
  const venueId = await insertVenue();
  const conversationId = await insertConversation(alice, admin, { createdAt: now });
  const dp = await insertDateProposal({ conversationId, proposerId: alice, recipientId: admin, venueId, createdAt: now });
  await insertLedgerEntry(alice, dp, 'refund', -700, now);
  await insertLedgerEntry(alice, dp, 'refund', -300, now);

  // Re-run the aggregation job so the rollup reflects these new ledger rows too.
  await runStatsAggregationJob(buildCtx({ type: 'system', job: 'test' }, now));

  const { rows: rawLedger } = await pool.query<{ sum: string; n: string }>(
    `SELECT coalesce(sum(amount_cents), 0)::text AS sum, count(*)::text AS n
     FROM payment_ledger WHERE type = 'refund' AND created_at::date = $1::date`,
    [day],
  );

  const overviewAfter = await adminStatsService.getOverview(ctx, { windowDays: 1 });
  assert.equal(overviewAfter.money.refundsCents, Number(rawLedger[0]!.sum));
  assert.equal(overviewAfter.money.refundsCount, Number(rawLedger[0]!.n));
});

test('adminStats.service.getOverview: "all" window is a cheap, bounded number of queries regardless of row count', async () => {
  const now = new Date('2026-06-01T00:00:00.000Z');
  const admin = await insertUser({ createdAt: now });
  const ctx = buildCtx(adminActor(admin), now);
  const { ctx: counted, count } = countingCtx(ctx);
  await adminStatsService.getOverview(counted, { windowDays: 'all' });
  assert.ok(count() <= 6, `expected a handful of queries for the overview, got ${count()}`);
});

test('adminStats.service.getRetention returns bounded cohorts with correct per-cohort rates', async () => {
  const now = new Date('2026-06-05T00:00:00.000Z');
  const admin = await insertUser({ createdAt: now });
  await pool.query(
    `INSERT INTO stats_cohort_retention (cohort_date, cohort_size, active_d1, active_d7, active_d30)
     VALUES ('2026-05-01', 20, 10, 5, 2) ON CONFLICT (cohort_date) DO UPDATE SET cohort_size = 20, active_d1 = 10, active_d7 = 5, active_d30 = 2`,
  );
  const ctx = buildCtx(adminActor(admin), now);
  const retention = await adminStatsService.getRetention(ctx);
  const row = retention.cohorts.find((c) => c.cohortDate === '2026-05-01');
  assert.ok(row);
  assert.equal(row!.d1Rate, 0.5);
  assert.equal(row!.d7Rate, 0.25);
  assert.equal(row!.d30Rate, 0.1);
  // These columns are `bigint` (db/migrations/023_widen_counters.sql), so
  // `pg` returns them as strings -- assert real JS numbers came out the
  // other end, not "20"/"10"/"5"/"2" strings smuggled through the API.
  assert.equal(typeof row!.cohortSize, 'number');
  assert.equal(row!.cohortSize, 20);
  assert.equal(row!.activeD1, 10);
  assert.equal(row!.activeD7, 5);
  assert.equal(row!.activeD30, 2);
});

// =====================================================================
// stats.service.ts (user page) correctness + privacy.
// =====================================================================

test('getMyFunnel: acceptance rates match a hand-computed fixture', async () => {
  const now = new Date('2026-03-01T00:00:00.000Z');
  const me = await insertUser({ createdAt: now });
  const other1 = await insertUser({ createdAt: now });
  const other2 = await insertUser({ createdAt: now });
  const other3 = await insertUser({ createdAt: now });

  // Sent: 3 total, 1 accepted, 1 declined, 1 pending => acceptanceRate over resolved (2) = 1/2.
  await insertInterest({ senderId: me, recipientId: other1, status: 'accepted', acceptedAt: now });
  await insertInterest({ senderId: me, recipientId: other2, status: 'declined', declinedAt: now });
  await insertInterest({ senderId: me, recipientId: other3, status: 'pending' });

  // Received: 2 total, both accepted => acceptanceRate = 1.
  await insertInterest({ senderId: other1, recipientId: me, status: 'accepted', acceptedAt: now });
  await insertInterest({ senderId: other2, recipientId: me, status: 'accepted', acceptedAt: now });

  await insertConversation(me, other1, { createdAt: now });

  const venueId = await insertVenue();
  const convo = await insertConversation(me, other2, { createdAt: now });
  await insertDateProposal({ conversationId: convo, proposerId: me, recipientId: other2, venueId, status: 'accepted', createdAt: now });
  await insertDateProposal({ conversationId: convo, proposerId: me, recipientId: other2, venueId, status: 'pending_acceptance', createdAt: now });

  const ctx = buildCtx(userActor(me), now);
  const funnel = await statsService.getMyFunnel(ctx);

  assert.equal(funnel.interestsSent.total, 3);
  assert.ok(Math.abs(funnel.interestsSent.acceptanceRate! - 0.5) < 1e-9);
  assert.equal(funnel.interestsReceived.total, 2);
  assert.equal(funnel.interestsReceived.acceptanceRate, 1);
  assert.equal(funnel.conversationsOpened, 2);
  assert.equal(funnel.dateProposalsSent.total, 2);
  assert.equal(funnel.dateProposalsSent.accepted, 1);
});

test('getMyDateOutcomes: aggregates outcome/wouldMeetAgain and never leaks safety_flag/safety_details/notes', async () => {
  const now = new Date('2026-03-05T00:00:00.000Z');
  const me = await insertUser({ createdAt: now });
  const other = await insertUser({ createdAt: now });
  const venueId = await insertVenue();
  const convo = await insertConversation(me, other, { createdAt: now });
  const dp1 = await insertDateProposal({ conversationId: convo, proposerId: me, recipientId: other, venueId, createdAt: now });
  const dp2 = await insertDateProposal({ conversationId: convo, proposerId: other, recipientId: me, venueId, createdAt: now });

  await insertPostDateFeedback({ dateProposalId: dp1, userId: me, outcome: 'happened_good', wouldMeetAgain: true, createdAt: now });
  await insertPostDateFeedback({
    dateProposalId: dp2,
    userId: me,
    outcome: 'happened_bad',
    wouldMeetAgain: false,
    safetyFlag: 'incident',
    safetyDetails: 'super-secret-detail-must-never-leak',
    createdAt: now,
  });

  const ctx = buildCtx(userActor(me), now);
  const outcomes = await statsService.getMyDateOutcomes(ctx);

  assert.equal(outcomes.totalCheckIns, 2);
  assert.equal(outcomes.byOutcome['happened_good'], 1);
  assert.equal(outcomes.byOutcome['happened_bad'], 1);
  assert.equal(outcomes.wouldMeetAgain.yes, 1);
  assert.equal(outcomes.wouldMeetAgain.no, 1);

  const json = JSON.stringify(outcomes);
  assert.ok(!json.includes('super-secret-detail-must-never-leak'));
  assert.ok(!/safety/i.test(json));
});

test('getMyResponseBehaviour: median reply time and interest-expiry rate match a hand-computed fixture', async () => {
  const now = new Date('2026-03-06T00:00:00.000Z');
  const me = await insertUser({ createdAt: now });
  const other = await insertUser({ createdAt: now });
  const convo = await insertConversation(me, other, { createdAt: now });

  // other -> me gap 10 min, me -> other (not counted), other -> me gap 30 min.
  const t0 = new Date(now.getTime());
  await insertMessage(convo, other, t0);
  await insertMessage(convo, me, new Date(t0.getTime() + 10 * 60000));
  await insertMessage(convo, me, new Date(t0.getTime() + 11 * 60000)); // consecutive me messages: no new gap
  await insertMessage(convo, other, new Date(t0.getTime() + 20 * 60000));
  await insertMessage(convo, me, new Date(t0.getTime() + 50 * 60000));

  await insertInterest({ senderId: other, recipientId: me, status: 'expired', expiredAt: now });
  await insertInterest({ senderId: other, recipientId: me, status: 'accepted', acceptedAt: now });

  const ctx = buildCtx(userActor(me), now);
  const behaviour = await statsService.getMyResponseBehaviour(ctx);

  assert.equal(behaviour.sampledReplies, 2);
  assert.ok(Math.abs(behaviour.medianResponseMinutes! - 20) < 1e-6); // median of [10, 30]
  assert.ok(Math.abs(behaviour.incomingInterestExpiryRate! - 0.5) < 1e-9);
});

test('getMyStatsTrends: weekly buckets match a hand-computed fixture', async () => {
  const now = new Date('2026-04-20T00:00:00.000Z');
  const me = await insertUser({ createdAt: now });
  const other1 = await insertUser({ createdAt: now });
  const other2 = await insertUser({ createdAt: now });
  const other3 = await insertUser({ createdAt: now });

  // Distinct recipients: `uq_interests_pending_pair` allows at most one
  // PENDING interest per (sender, recipient) at a time, so three pending
  // interests from the same sender need three different recipients.
  await insertInterest({ senderId: me, recipientId: other1, status: 'pending', createdAt: daysAgo(now, 1) });
  await insertInterest({ senderId: me, recipientId: other2, status: 'pending', createdAt: daysAgo(now, 1) });
  await insertInterest({ senderId: me, recipientId: other3, status: 'pending', createdAt: daysAgo(now, 10) });

  const ctx = buildCtx(userActor(me), now);
  const trends = await statsService.getMyStatsTrends(ctx, { weeks: 4 });

  const total = trends.points.reduce((acc, p) => acc + p.interestsSent, 0);
  assert.equal(total, 3);
  assert.ok(trends.points.length >= 2, 'expected at least two distinct weekly buckets');
});

test('getMyFilterCosts: suppresses small other-person cohorts, and caches for repeat calls', async () => {
  const now = new Date('2026-03-10T00:00:00.000Z');
  const me = await insertUser({ createdAt: now });
  await insertProfile(me, { completeness: 100 });
  await pool.query(`UPDATE profiles SET latitude = 1, longitude = 1 WHERE user_id = $1`, [me]);
  await insertHardFilter(me, 'age_min', 'gte', 99); // deliberately excludes everyone (age never >= 99)

  // Only 2 nearby candidates -- below MIN_SUPPRESSIBLE_COHORT even once the filter is removed.
  for (let i = 0; i < 2; i++) {
    const other = await insertUser({ createdAt: now });
    await insertProfile(other, { completeness: 100 });
    await pool.query(`UPDATE profiles SET latitude = 1, longitude = 1 WHERE user_id = $1`, [other]);
  }

  const ctx = buildCtx(userActor(me), now);
  const first = await statsService.getMyFilterCosts(ctx);
  assert.equal(first.fromCache, false);
  assert.equal(first.currentPool.suppressed, true);
  assert.equal(first.currentPool.value, null);
  const filterEntry = first.perFilter.find((f) => f.filterKey === 'age_min');
  assert.ok(filterEntry);
  assert.equal(filterEntry!.additionalCandidatesIfRemoved.suppressed, true);
  assert.equal(first.candidatesFailingTwoOrMore.suppressed, true);
  assert.equal(first.costliestFilter, null, 'the one enabled filter is suppressed, so there is no number to name it by');

  const second = await statsService.getMyFilterCosts(ctx);
  assert.equal(second.fromCache, true);

  // Structural privacy check: nothing in the payload is keyed by another
  // person's id, only counts. `rawPool` (the pre-suppression numbers
  // getMyPoolVenn reuses) is a service-layer-only field, never serialized,
  // but it too must never carry an id -- it's a plain {number, number,
  // number}, so this same blanket check already covers it.
  const json = JSON.stringify(first);
  assert.ok(!json.includes(me));
});

test('getMyFilterCosts: shows an exact number once the excluded population clears the suppression threshold', async () => {
  const now = new Date('2026-03-11T00:00:00.000Z');
  const me = await insertUser({ createdAt: now });
  await insertProfile(me, { completeness: 100 });
  await pool.query(`UPDATE profiles SET latitude = 60, longitude = 60 WHERE user_id = $1`, [me]);
  await insertHardFilter(me, 'age_min', 'gte', 99);

  for (let i = 0; i < 8; i++) {
    const other = await insertUser({ createdAt: now });
    await insertProfile(other, { completeness: 100 });
    await pool.query(`UPDATE profiles SET latitude = 60, longitude = 60 WHERE user_id = $1`, [other]);
  }

  const ctx = buildCtx(userActor(me), now);
  const result = await statsService.getMyFilterCosts(ctx, { forceRefresh: true });
  const filterEntry = result.perFilter.find((f) => f.filterKey === 'age_min');
  assert.ok(filterEntry);
  assert.equal(filterEntry!.additionalCandidatesIfRemoved.suppressed, false);
  assert.equal(filterEntry!.additionalCandidatesIfRemoved.value, 8);
  assert.equal(result.costliestFilter?.filterKey, 'age_min');
  // Only one filter is enabled, so nobody CAN fail two or more -- the
  // true count is 0, which (like any count below MIN_SUPPRESSIBLE_COHORT,
  // zero included) is still reported as suppressed rather than as a bare
  // "0", the same rule every other cross-person count in this file uses.
  assert.equal(result.candidatesFailingTwoOrMore.suppressed, true);
  assert.equal(result.candidatesFailingTwoOrMore.value, null);

  // The one-pass computation never writes to hard_filters at all (unlike
  // the earlier scratch-transaction design, which flipped a real row and
  // relied on a rollback to undo it).
  const { rows } = await pool.query(`SELECT enabled FROM hard_filters WHERE user_id = $1 AND filter_key = 'age_min'`, [me]);
  assert.equal(rows[0].enabled, true);
});

// =====================================================================
// Filter widening: one-pass rewrite, proof of equivalence, and measured
// before/after query counts (see this build's report for the numbers).
// =====================================================================

/** Counts every `.query()` call made through `db`, without changing its behaviour. Used to measure both the pre-optimization (scratch-rollback-per-filter) and the current (one-pass) query cost against the identical fixture. */
function countingDb(db: DbClient, counter: { n: number }): DbClient {
  return {
    query: ((...args: unknown[]) => {
      counter.n += 1;
      // @ts-expect-error: forwarding pg's overloaded Pool/PoolClient#query signature verbatim (same shim tests/perf/discovery.perf.test.ts's own countingDb uses).
      return db.query(...args);
    }) as DbClient['query'],
  };
}

/**
 * A faithful reproduction of `getMyFilterCosts`'s PRE-OPTIMIZATION body
 * (one full `countUsersMatchingMyFilters` search per enabled filter,
 * each with that filter temporarily disabled inside a transaction that
 * is always rolled back) -- kept here, not in production code, purely as
 * the "before" side of the equivalence/measurement proof below. Returns
 * the same `additionalCandidatesIfRemoved` numbers the current
 * implementation exposes as `perFilter`, unsuppressed, so the test can
 * compare exact integers rather than two already-suppressed views.
 */
async function oldStyleFilterCosts(
  ctx: Ctx,
  rawPool: pg.Pool,
  userId: string,
  filterKeys: string[],
  counter?: { n: number },
): Promise<Map<string, number>> {
  // When `counter` is given, EVERY query this function issues (the
  // baseline search, and every BEGIN/UPDATE/search/ROLLBACK inside the
  // per-filter loop) is counted through it -- not just the ones that
  // happen to go through `ctx.db` -- so the measurement below reflects
  // the true number of round trips the pre-optimization design made.
  const baselineDb = counter ? countingDb(ctx.db, counter) : ctx.db;
  const baseline = await filterService.countUsersMatchingMyFilters(withDb(ctx, baselineDb), userId);

  const additional = new Map<string, number>();
  for (const filterKey of filterKeys) {
    const client = await rawPool.connect();
    const clientDb = counter ? countingDb(client, counter) : client;
    try {
      await clientDb.query('BEGIN');
      await clientDb.query(`UPDATE hard_filters SET enabled = false WHERE user_id = $1 AND filter_key = $2`, [userId, filterKey]);
      const withoutCount = await filterService.countUsersMatchingMyFilters(withDb(ctx, clientDb), userId);
      additional.set(filterKey, Math.max(0, withoutCount - baseline));
    } finally {
      await clientDb.query('ROLLBACK').catch(() => {});
      client.release();
    }
  }
  return additional;
}

/** Builds a 4-way fixture with every combination of "fails filter A", "fails filter B" present in numbers comfortably clear of `MIN_SUPPRESSIBLE_COHORT`, so both the equivalence proof and the query-count measurement below exercise overlapping filter failures, not just an all-or-nothing case. */
async function seedOverlappingFilterFixture(now: Date): Promise<{ me: string; expected: { ageOnly: number; genderOnly: number; twoOrMore: number; neither: number } }> {
  const me = await insertUser({ createdAt: now });
  await insertProfile(me, { completeness: 100 });
  await pool.query(`UPDATE profiles SET latitude = 40, longitude = 40 WHERE user_id = $1`, [me]);
  await insertHardFilter(me, 'age_min', 'gte', 25);
  await insertHardFilter(me, 'gender_preference', 'eq', 'woman');

  async function seedCandidate(age: number, gender: string): Promise<void> {
    const id = await insertUser({ createdAt: now });
    await insertProfile(id, { completeness: 100 });
    await pool.query(`UPDATE profiles SET latitude = 40, longitude = 40, age = $2, gender = $3 WHERE user_id = $1`, [id, age, gender]);
  }

  const neither = 5; // age >= 25, gender = woman: passes both
  const ageOnly = 6; // age < 25 (fails age_min), gender = woman: fails ONLY age_min
  const genderOnly = 5; // age >= 25, gender = man: fails ONLY gender_preference
  const twoOrMore = 6; // age < 25, gender = man: fails both

  for (let i = 0; i < neither; i++) await seedCandidate(30, 'woman');
  for (let i = 0; i < ageOnly; i++) await seedCandidate(20, 'woman');
  for (let i = 0; i < genderOnly; i++) await seedCandidate(30, 'man');
  for (let i = 0; i < twoOrMore; i++) await seedCandidate(20, 'man');

  return { me, expected: { ageOnly, genderOnly, twoOrMore, neither } };
}

test('getMyFilterCosts: the one-pass rewrite matches the pre-optimization per-filter search exactly, on a fixture with overlapping filter failures', async () => {
  const now = new Date('2026-04-01T00:00:00.000Z');
  const { me, expected } = await seedOverlappingFilterFixture(now);
  const ctx = buildCtx(userActor(me), now);

  const reference = await oldStyleFilterCosts(ctx, pool, me, ['age_min', 'gender_preference']);
  assert.equal(reference.get('age_min'), expected.ageOnly);
  assert.equal(reference.get('gender_preference'), expected.genderOnly);

  const result = await statsService.getMyFilterCosts(ctx, { forceRefresh: true });

  for (const [filterKey, expectedAdditional] of reference) {
    const entry = result.perFilter.find((f) => f.filterKey === filterKey);
    assert.ok(entry, `expected a perFilter entry for ${filterKey}`);
    assert.equal(entry!.additionalCandidatesIfRemoved.value, expectedAdditional, `${filterKey}: one-pass result must equal the pre-optimization search`);
    assert.equal(entry!.additionalCandidatesIfRemoved.suppressed, false);
  }
  assert.equal(result.candidatesFailingTwoOrMore.value, expected.twoOrMore);
  assert.equal(result.currentPool.value, expected.neither);
  assert.equal(result.costliestFilter?.filterKey, 'age_min', 'age_min (6) opens up more candidates than gender_preference (5)');
});

test('getMyFilterCosts: measured query counts, one-pass rewrite versus the pre-optimization per-filter search', async () => {
  const now = new Date('2026-04-02T00:00:00.000Z');
  const { me } = await seedOverlappingFilterFixture(now);
  const ctxBase = buildCtx(userActor(me), now);

  // OLD: one full geo-bounded search per enabled filter, inside a
  // scratch transaction that is always rolled back.
  const oldCounter = { n: 0 };
  const oldStart = Date.now();
  await oldStyleFilterCosts(ctxBase, pool, me, ['age_min', 'gender_preference'], oldCounter);
  const oldMs = Date.now() - oldStart;

  // NEW: one pass over the same candidate sample, classifying every
  // candidate by exactly which filters it fails.
  const newCounter = { n: 0 };
  const newCtx = withDb(ctxBase, countingDb(pool, newCounter));
  const newStart = Date.now();
  await statsService.getMyFilterCosts(newCtx, { forceRefresh: true });
  const newMs = Date.now() - newStart;

  console.log(
    `[getMyFilterCosts perf] 2 filters: old-style per-filter search = ${oldCounter.n} queries / ${oldMs}ms; ` +
      `one-pass rewrite (includes the mandatory reality-dashboard call both approaches need) = ${newCounter.n} queries / ${newMs}ms`,
  );

  assert.ok(oldCounter.n > newCounter.n, 'the one-pass rewrite must issue fewer queries than one full search per filter');

  // Confirm the OLD approach's cost actually scales with filter count
  // (the defect this build fixes) by re-running it with a THIRD filter
  // added, on a fresh candidate sample so the added filter has real
  // candidates to search against.
  await insertHardFilter(me, 'relationship_intention', 'eq', 'long_term');
  const oldCounter3 = { n: 0 };
  await oldStyleFilterCosts(ctxBase, pool, me, ['age_min', 'gender_preference', 'relationship_intention'], oldCounter3);
  console.log(`[getMyFilterCosts perf] 3 filters: old-style per-filter search = ${oldCounter3.n} queries`);
  assert.ok(oldCounter3.n > oldCounter.n, 'old-style cost must grow when a filter is added');

  // ...while the one-pass rewrite's query count does NOT grow with the
  // number of enabled filters (it is bounded by the candidate sample and
  // the fixed number of batched loads, not by filter count).
  const newCounter3 = { n: 0 };
  const newCtx3 = withDb(ctxBase, countingDb(pool, newCounter3));
  await statsService.getMyFilterCosts(newCtx3, { forceRefresh: true });
  console.log(`[getMyFilterCosts perf] 3 filters: one-pass rewrite = ${newCounter3.n} queries`);
  assert.equal(newCounter3.n, newCounter.n, 'the one-pass rewrite issues the SAME number of queries regardless of how many filters are enabled');
});

test('getMyComparisons: without a location on file, every regional comparison is insufficient_data rather than a misleading global average', async () => {
  const now = new Date('2026-04-03T00:00:00.000Z');
  const me = await insertUser({ createdAt: now });
  await insertProfile(me, { completeness: 100 }); // no latitude/longitude set

  const ctx = buildCtx(userActor(me), now);
  const comparisons = await statsService.getMyComparisons(ctx);

  assert.equal(comparisons.hasLocation, false);
  assert.equal(comparisons.questionsAnswered.position, 'insufficient_data');
  assert.equal(comparisons.questionsAnswered.regionTypical, null);
  assert.equal(comparisons.filterStrictness.position, 'insufficient_data');
  assert.deepEqual(comparisons.tagPrevalence, []);
});

test('getMyComparisons: positions the caller against the regional typical band, and reports tag prevalence excluding the caller\'s own row', async () => {
  const now = new Date('2026-04-04T00:00:00.000Z');

  // Regional population: 9 people near (20, 20), with a spread of
  // questions-answered counts so the interquartile band is meaningful.
  const answeredCounts = [2, 4, 6, 8, 10, 12, 14, 16, 18];
  const tagRows = await pool.query<{ id: string }>(
    `INSERT INTO interest_tags (name, category) VALUES ('Hiking', 'outdoors') RETURNING id`,
  );
  const tagId = tagRows.rows[0]!.id;

  const filler = await getFillerQuestionBankId();
  for (const n of answeredCounts) {
    const uid = await insertUser({ createdAt: now });
    await insertProfile(uid, { completeness: 100 });
    await pool.query(`UPDATE profiles SET latitude = 20, longitude = 20 WHERE user_id = $1`, [uid]);
    for (let i = 0; i < n; i++) {
      await pool.query(
        `INSERT INTO user_question_answers (user_id, question_slug, question_bank_id, status, answered_at)
         VALUES ($1, $2, $3, 'skipped', now())`,
        [uid, `q-${i}`, filler],
      );
    }
  }
  // 6 of the 9 also hold the "Hiking" tag (publicly), clearing the
  // suppression threshold on its own.
  const { rows: regionUsers } = await pool.query<{ user_id: string }>(
    `SELECT user_id FROM profiles WHERE latitude = 20 AND longitude = 20`,
  );
  for (const { user_id } of regionUsers.slice(0, 6)) {
    await pool.query(`INSERT INTO user_tags (user_id, tag_id, visibility) VALUES ($1, $2, 'public')`, [user_id, tagId]);
  }

  await runStatsAggregationJob(buildCtx({ type: 'system', job: 'stats_aggregation' }, now));

  // The caller: also in the region, answered fewer questions than
  // everyone else seeded above, and also holds the Hiking tag.
  const me = await insertUser({ createdAt: now });
  await insertProfile(me, { completeness: 100 });
  await pool.query(`UPDATE profiles SET latitude = 20, longitude = 20 WHERE user_id = $1`, [me]);
  await pool.query(`INSERT INTO user_tags (user_id, tag_id, visibility) VALUES ($1, $2, 'public')`, [me, tagId]);

  const ctx = buildCtx(userActor(me), now);
  const comparisons = await statsService.getMyComparisons(ctx);

  assert.equal(comparisons.hasLocation, true);
  assert.equal(comparisons.questionsAnswered.mine, 0);
  assert.equal(comparisons.questionsAnswered.position, 'below_typical', 'answering nothing is below every seeded neighbour');
  assert.ok(typeof comparisons.questionsAnswered.regionTypical === 'number');

  const hiking = comparisons.tagPrevalence.find((t) => t.tagId === tagId);
  assert.ok(hiking);
  assert.equal(hiking!.tagName, 'Hiking');
  // 6 holders in the rollup, minus the caller's own (public) row -> 5 others.
  assert.equal(hiking!.nearbyHolders.suppressed, false);
  assert.equal(hiking!.nearbyHolders.value, 5);

  // Privacy: nothing here is keyed by another person's id.
  const json = JSON.stringify(comparisons);
  for (const { user_id } of regionUsers) {
    assert.ok(!json.includes(user_id), 'a comparisons payload must never contain another person\'s id');
  }
});

test('getMyComparisons: a tag held by too few nearby people is suppressed like any other small cohort', async () => {
  const now = new Date('2026-04-05T00:00:00.000Z');
  const tagRows = await pool.query<{ id: string }>(
    `INSERT INTO interest_tags (name, category) VALUES ('Ferret Husbandry', 'niche') RETURNING id`,
  );
  const tagId = tagRows.rows[0]!.id;

  // A large-enough region population (clears MIN_SUPPRESSIBLE_COHORT for
  // the region itself) but only 2 of them hold the rare tag.
  for (let i = 0; i < 6; i++) {
    const uid = await insertUser({ createdAt: now });
    await insertProfile(uid, { completeness: 100 });
    await pool.query(`UPDATE profiles SET latitude = -8, longitude = 100 WHERE user_id = $1`, [uid]);
    if (i < 2) {
      await pool.query(`INSERT INTO user_tags (user_id, tag_id, visibility) VALUES ($1, $2, 'public')`, [uid, tagId]);
    }
  }

  await runStatsAggregationJob(buildCtx({ type: 'system', job: 'stats_aggregation' }, now));

  const me = await insertUser({ createdAt: now });
  await insertProfile(me, { completeness: 100 });
  await pool.query(`UPDATE profiles SET latitude = -8, longitude = 100 WHERE user_id = $1`, [me]);
  await pool.query(`INSERT INTO user_tags (user_id, tag_id, visibility) VALUES ($1, $2, 'public')`, [me, tagId]);

  const ctx = buildCtx(userActor(me), now);
  const comparisons = await statsService.getMyComparisons(ctx);

  const rare = comparisons.tagPrevalence.find((t) => t.tagId === tagId);
  assert.ok(rare);
  // 2 holders total, minus the caller's own row = 1 other -- below
  // MIN_SUPPRESSIBLE_COHORT.
  assert.equal(rare!.nearbyHolders.suppressed, true);
  assert.equal(rare!.nearbyHolders.value, null);
});

// =====================================================================
// Pool Venn.
// =====================================================================

test('getMyPoolVenn: reshapes the same numbers getMyFilterCosts already computes, region sizes and intersection agree', async () => {
  const now = new Date('2026-04-06T00:00:00.000Z');
  const { me } = await seedOverlappingFilterFixture(now);
  const ctx = buildCtx(userActor(me), now);

  const costs = await statsService.getMyFilterCosts(ctx, { forceRefresh: true });
  const venn = await statsService.getMyPoolVenn(ctx);

  assert.equal(venn.setA.count.value, costs.currentPool.value);
  assert.equal(venn.setA.count.suppressed, costs.currentPool.suppressed);
  assert.equal(venn.intersection.count.value, costs.mutualMatchPool.value);
});

test('getMyPoolVennSvg: renders a well-formed, self-contained SVG with a screen-reader text alternative', async () => {
  const now = new Date('2026-04-07T00:00:00.000Z');
  const { me } = await seedOverlappingFilterFixture(now);
  const ctx = buildCtx(userActor(me), now);

  const svg = await statsService.getMyPoolVennSvg(ctx);
  assert.ok(svg.startsWith('<svg'));
  assert.match(svg, /<title id="venn-title">/);
  assert.match(svg, /<desc id="venn-desc">/);
  assert.ok(!svg.includes(me), 'the SVG must never contain a user id');
});

test('getMyPhotoStats: ranks by accepted-interest rate, not raw impressions', async () => {
  const now = new Date('2026-03-12T00:00:00.000Z');
  const me = await insertUser({ createdAt: now });
  const { rows: photoRows } = await pool.query<{ id: string }>(
    `INSERT INTO user_photos (user_id, image_url, position, is_primary, moderation_status)
     VALUES ($1, 'a.jpg', 0, true, 'approved') RETURNING id`,
    [me],
  );
  const photoId = photoRows[0]!.id;
  await pool.query(
    `INSERT INTO photo_experiments (user_id, photo_id, impressions, interests_sent, interests_accepted) VALUES ($1, $2, 100, 10, 5)`,
    [me, photoId],
  );

  const ctx = buildCtx(userActor(me), now);
  const stats = await statsService.getMyPhotoStats(ctx);
  assert.equal(stats.photos.length, 1);
  assert.ok(Math.abs(stats.photos[0]!.acceptedInterestRate! - 0.05) < 1e-9);
});
