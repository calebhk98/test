/**
 * tests/unit/integrity.test.ts, proves every constraint added by
 * db/migrations/025_integrity.sql actually rejects the bad state it
 * names, not merely that the good state still works. See that file and
 * docs/normalization.md for the full reasoning behind each choice
 * (including the two ranked items that are deliberately NOT closed with
 * a hard constraint here, and why).
 *
 * Item 1 (`post_date_feedback`: `positive` vs `outcome` agreement) is no
 * longer covered here: `positive`, and the
 * `post_date_feedback_positive_outcome_agree` CHECK that used to tie it
 * to `outcome`, are both dropped in db/migrations/028_remove_legacy.sql
 * (this is a prototype, no backward compatibility; the historical
 * corruption risk this constraint guarded against no longer exists once
 * there is no second column left for `outcome` to disagree with). Items
 * 2-4 below are untouched, they belong to constraints this build did not
 * add and did not remove.
 *
 * Self-contained database setup (own `odate_integrity_<suite>` database,
 * per the build brief), independent of the other agents' shared test
 * harnesses, this file spans tables/constraints that cut across more
 * than one agent's usual territory (users, interests, date_proposals,
 * payment_holds, post_date_feedback), so it does not adopt any one of
 * them.
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
import type { Ctx } from '../../src/lib/ctx.js';
import * as trustService from '../../src/services/trust.service.js';

const BASE_URL = process.env.DATABASE_URL ?? 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';
const DB_PREFIX = 'odate_integrity';
const RUN_SUFFIX = randomUUID().replace(/-/g, '').slice(0, 8);

function withDbName(url: string, dbName: string): string {
  const u = new URL(url);
  u.pathname = `/${dbName}`;
  return u.toString();
}

let adminPool: pg.Pool | undefined;
let pool: pg.Pool;
let dbName: string;
let clock: ManualClock;
let ctx: Ctx;

before(async () => {
  dbName = `${DB_PREFIX}_main_${RUN_SUFFIX}`;
  adminPool = new pg.Pool({ connectionString: BASE_URL });
  await adminPool.query(`DROP DATABASE IF EXISTS ${dbName}`);
  await adminPool.query(`CREATE DATABASE ${dbName}`);
  process.env.DATABASE_URL = withDbName(BASE_URL, dbName);
  await runMigrations();
  pool = getPool();

  clock = new ManualClock(new Date('2026-01-05T12:00:00.000Z'));
  const logger = createSilentLogger();
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
  if (adminPool) {
    await adminPool.query(`DROP DATABASE IF EXISTS ${dbName}`);
    await adminPool.end();
  }
});

/** Asserts `fn` rejects with a Postgres check_violation (SQLSTATE 23514). */
async function assertCheckViolation(fn: () => Promise<unknown>, label: string): Promise<void> {
  await assert.rejects(
    fn,
    (err: unknown) => {
      const code = (err as { code?: string }).code;
      assert.equal(code, '23514', `${label}: expected a check_violation (23514), got ${code}, ${(err as Error).message}`);
      return true;
    },
    `${label}: expected the insert/update to be rejected, but it succeeded`,
  );
}

let userCounter = 0;
async function insertUser(opts: { status?: string; suspended?: boolean; trustScore?: number; trustLevel?: string } = {}): Promise<string> {
  userCounter += 1;
  const id = randomUUID();
  await pool.query(
    `INSERT INTO users (id, email, password_hash, birthdate, status, trust_score, trust_level, suspended)
     VALUES ($1, $2, 'x', '1990-01-01', $3, $4, $5, $6)`,
    [id, `integrity-${userCounter}-${Date.now()}@example.test`, opts.status ?? 'active', opts.trustScore ?? 50, opts.trustLevel ?? 'standard', opts.suspended ?? false],
  );
  return id;
}

let venueIdCache: string | undefined;
async function venueId(): Promise<string> {
  if (venueIdCache) return venueIdCache;
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO venues (name, address, latitude, longitude, category, active, margin_percent, time_slot_config, redemption_method)
     VALUES ('Integrity Test Venue', '1 Test St', 0, 0, 'coffee', true, 10, '{"slots":[]}'::jsonb, 'qr_scan')
     RETURNING id`,
  );
  venueIdCache = rows[0]!.id;
  return venueIdCache;
}

async function insertDateProposal(
  proposerId: string,
  recipientId: string,
  opts: { status?: string } = {},
): Promise<string> {
  const [a, b] = proposerId < recipientId ? [proposerId, recipientId] : [recipientId, proposerId];
  const { rows: convRows } = await pool.query<{ id: string }>(
    `INSERT INTO conversations (user_a_id, user_b_id, status) VALUES ($1, $2, 'active')
     ON CONFLICT (user_a_id, user_b_id) DO UPDATE SET status = conversations.status
     RETURNING id`,
    [a, b],
  );
  const venue = await venueId();
  const now = clock.now();
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO date_proposals (conversation_id, proposer_id, recipient_id, venue_id, scheduled_start, scheduled_end, status, policy_snapshot, escrow_amount_cents)
     VALUES ($1, $2, $3, $4, $5, $6, $7, '{}'::jsonb, 2000)
     RETURNING id`,
    [convRows[0]!.id, proposerId, recipientId, venue, new Date(now.getTime() - 3600_000), now, opts.status ?? 'completed'],
  );
  return rows[0]!.id;
}

// =====================================================================
// 2. users: status / suspended agreement
// =====================================================================

test('users CHECK rejects status=suspended with suspended=false', async () => {
  await assertCheckViolation(
    () => pool.query(`INSERT INTO users (email, password_hash, birthdate, status, suspended) VALUES ($1, 'x', '1990-01-01', 'suspended', false)`, [`bad-a-${randomUUID()}@example.test`]),
    'users status=suspended/suspended=false',
  );
});

test('users CHECK rejects suspended=true with status=active', async () => {
  await assertCheckViolation(
    () => pool.query(`INSERT INTO users (email, password_hash, birthdate, status, suspended) VALUES ($1, 'x', '1990-01-01', 'active', true)`, [`bad-b-${randomUUID()}@example.test`]),
    'users suspended=true/status=active',
  );
});

test('users CHECK allows the two agreeing pairs', async () => {
  await insertUser({ status: 'active', suspended: false });
  await insertUser({ status: 'suspended', suspended: true });
});

// =====================================================================
// 3. trust_level derived from trust_score, config-aware
// =====================================================================

test('trust_level_for_score reflects the CURRENT config bands, not a fixed table baked in at creation time', async () => {
  const { rows: before } = await pool.query<{ level: string }>(`SELECT trust_level_for_score(65) AS level`);
  assert.equal(before[0]!.level, 'standard', 'default trust.level_trusted_min is 70, so 65 starts out standard');

  await ctx.config.set('trust.level_trusted_min', 60, 'test-admin');
  const { rows: after } = await pool.query<{ level: string }>(`SELECT trust_level_for_score(65) AS level`);
  assert.equal(after[0]!.level, 'trusted', 'lowering the config bound must change the SAME score\'s derived level without any migration');

  await ctx.config.set('trust.level_trusted_min', 70, 'test-admin'); // restore default for later tests
});

test('recalculateTrustScore always writes a trust_score/trust_level pair the DB itself derives, even after the config bands change', async () => {
  const userId = await insertUser({ trustScore: 50, trustLevel: 'standard' });
  const userCtx: Ctx = { ...ctx, actor: { type: 'user', userId, trustLevel: 'standard' } };

  const result1 = await trustService.recalculateTrustScore(userCtx, userId);
  const { rows: row1 } = await pool.query<{ trust_score: number; trust_level: string }>(`SELECT trust_score, trust_level FROM users WHERE id = $1`, [userId]);
  assert.equal(row1[0]!.trust_level, result1.trustLevel);
  const { rows: expected1 } = await pool.query<{ level: string }>(`SELECT trust_level_for_score($1) AS level`, [row1[0]!.trust_score]);
  assert.equal(row1[0]!.trust_level, expected1[0]!.level, 'the stored trust_level must always equal what trust_level_for_score derives from the stored trust_score');

  // Retune the bands, then recalculate again, the newly-written pair must reflect the NEW bands, not the ones at insert time.
  await ctx.config.set('trust.level_standard_min', 0, 'test-admin');
  await ctx.config.set('trust.level_trusted_min', row1[0]!.trust_score, 'test-admin'); // exactly at the user's current score
  const result2 = await trustService.recalculateTrustScore(userCtx, userId);
  assert.equal(result2.trustLevel, 'trusted', 'the same trust_score now crosses the (lowered) trusted band');
  const { rows: row2 } = await pool.query<{ trust_score: number; trust_level: string }>(`SELECT trust_score, trust_level FROM users WHERE id = $1`, [userId]);
  assert.equal(row2[0]!.trust_level, 'trusted');

  await ctx.config.set('trust.level_standard_min', 40, 'test-admin');
  await ctx.config.set('trust.level_trusted_min', 70, 'test-admin');
});

// =====================================================================
// 4. interests / date_proposals / payment_holds: status vs timestamps
// =====================================================================

test('interests CHECK rejects a pending row with accepted_at set', async () => {
  const alice = await insertUser();
  const bob = await insertUser();
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO interests (sender_id, recipient_id, status, policy_snapshot, expires_at) VALUES ($1, $2, 'pending', '{}'::jsonb, now() + interval '7 days') RETURNING id`,
    [alice, bob],
  );
  await assertCheckViolation(
    () => pool.query(`UPDATE interests SET accepted_at = now() WHERE id = $1`, [rows[0]!.id]),
    'interests pending + accepted_at',
  );
});

test('interests CHECK rejects an accepted row with accepted_at still null', async () => {
  const alice = await insertUser();
  const bob = await insertUser();
  await assertCheckViolation(
    () => pool.query(`INSERT INTO interests (sender_id, recipient_id, status, policy_snapshot, expires_at) VALUES ($1, $2, 'accepted', '{}'::jsonb, now() + interval '7 days')`, [alice, bob]),
    'interests accepted + accepted_at IS NULL',
  );
});

test('interests CHECK allows a well-formed pending row and a well-formed accepted row', async () => {
  const alice = await insertUser();
  const bob = await insertUser();
  await pool.query(`INSERT INTO interests (sender_id, recipient_id, status, policy_snapshot, expires_at) VALUES ($1, $2, 'pending', '{}'::jsonb, now() + interval '7 days')`, [alice, bob]);
  const carol = await insertUser();
  await pool.query(`INSERT INTO interests (sender_id, recipient_id, status, policy_snapshot, expires_at, accepted_at) VALUES ($1, $2, 'accepted', '{}'::jsonb, now() + interval '7 days', now())`, [alice, carol]);
});

test('date_proposals CHECK rejects a pending_acceptance row with accepted_at set', async () => {
  const alice = await insertUser();
  const bob = await insertUser();
  const dp = await insertDateProposal(alice, bob, { status: 'pending_acceptance' });
  await assertCheckViolation(
    () => pool.query(`UPDATE date_proposals SET accepted_at = now() WHERE id = $1`, [dp]),
    'date_proposals pending_acceptance + accepted_at',
  );
});

test('date_proposals CHECK rejects status=declined with declined_at still null', async () => {
  const alice = await insertUser();
  const bob = await insertUser();
  await assertCheckViolation(
    () => insertDateProposal(alice, bob, { status: 'declined' }),
    'date_proposals declined + declined_at IS NULL',
  );
});

test('date_proposals CHECK rejects status=refunded with canceled_at still null', async () => {
  const alice = await insertUser();
  const bob = await insertUser();
  await assertCheckViolation(
    () => insertDateProposal(alice, bob, { status: 'refunded' }),
    'date_proposals refunded + canceled_at IS NULL',
  );
});

test('date_proposals CHECK allows a well-formed declined row and a well-formed refunded row', async () => {
  const alice = await insertUser();
  const bob = await insertUser();
  const [a, b] = alice < bob ? [alice, bob] : [bob, alice];
  const { rows: convRows } = await pool.query<{ id: string }>(
    `INSERT INTO conversations (user_a_id, user_b_id, status) VALUES ($1, $2, 'active') RETURNING id`,
    [a, b],
  );
  const venue = await venueId();
  await pool.query(
    `INSERT INTO date_proposals (conversation_id, proposer_id, recipient_id, venue_id, scheduled_start, scheduled_end, status, policy_snapshot, escrow_amount_cents, declined_at)
     VALUES ($1, $2, $3, $4, now(), now() + interval '1 hour', 'declined', '{}'::jsonb, 2000, now())`,
    [convRows[0]!.id, alice, bob, venue],
  );
  const carol = await insertUser();
  const dp2 = await insertDateProposal(alice, carol, { status: 'accepted' });
  await pool.query(`UPDATE date_proposals SET accepted_at = now(), status = 'refunded', canceled_at = now() WHERE id = $1`, [dp2]);
});

test('payment_holds CHECK rejects a pending hold with authorized_at set', async () => {
  const alice = await insertUser();
  const bob = await insertUser();
  const dp = await insertDateProposal(alice, bob);
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO payment_holds (date_proposal_id, user_id, processor, amount_cents, status) VALUES ($1, $2, 'fake', 2000, 'pending') RETURNING id`,
    [dp, alice],
  );
  await assertCheckViolation(
    () => pool.query(`UPDATE payment_holds SET authorized_at = now() WHERE id = $1`, [rows[0]!.id]),
    'payment_holds pending + authorized_at',
  );
});

test('payment_holds CHECK rejects status=authorized with authorized_at still null', async () => {
  const alice = await insertUser();
  const bob = await insertUser();
  const dp = await insertDateProposal(alice, bob);
  await assertCheckViolation(
    () => pool.query(`INSERT INTO payment_holds (date_proposal_id, user_id, processor, amount_cents, status) VALUES ($1, $2, 'fake', 2000, 'authorized')`, [dp, alice]),
    'payment_holds authorized + authorized_at IS NULL',
  );
});

test('payment_holds CHECK allows a well-formed authorized hold', async () => {
  const alice = await insertUser();
  const bob = await insertUser();
  const dp = await insertDateProposal(alice, bob);
  await pool.query(`INSERT INTO payment_holds (date_proposal_id, user_id, processor, amount_cents, status, authorized_at) VALUES ($1, $2, 'fake', 2000, 'authorized', now())`, [dp, alice]);
});
