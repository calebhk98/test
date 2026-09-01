/**
 * Shared test setup for this build's three suites
 * (tests/unit/retention.test.ts, i18n.test.ts, altText.test.ts) — same
 * shape as tests/unit/testCtx.ts (Agent A's own helper) and
 * tests/unit/testCtxAgentE.ts/testCtxEligibility.ts/testCtxDecisions.ts
 * (every other agent's), just for this build's own tables. Not part of
 * INTERFACES.md's frozen list — a local helper these three files share to
 * avoid duplicating DB bootstrap, following this repo's established
 * per-agent convention.
 *
 * Uses `odate_retention_<suite>_<runSuffix>` databases (task brief: "your
 * own Postgres databases") so this build's tests never collide with any
 * other agent's own `odate_*` databases running concurrently on the same
 * shared dev Postgres cluster (port 55433).
 */
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

const BASE_URL = process.env.DATABASE_URL ?? 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';
const DB_BASE_NAME = 'odate_retention';
/** Per-process random suffix — see testCtx.ts's own longer note on why this closes a cross-run database-name-collision race when this repo's suite is run by more than one agent at once. */
const RUN_SUFFIX = randomUUID().replace(/-/g, '').slice(0, 8);

function withDbName(url: string, dbName: string): string {
  const u = new URL(url);
  u.pathname = `/${dbName}`;
  return u.toString();
}

let adminPool: pg.Pool | undefined;
let testPool: pg.Pool | undefined;
let currentDbName: string | undefined;

/** Ensures `odate_retention_<suffix>_<runSuffix>` exists (fresh schema) and runs migrations against it. Call once from a suite's `before`, passing a `suffix` unique to that test file. */
export async function setupTestDatabase(suffix: string): Promise<pg.Pool> {
  const dbName = `${DB_BASE_NAME}_${suffix}_${RUN_SUFFIX}`;
  currentDbName = dbName;

  adminPool = new pg.Pool({ connectionString: BASE_URL });
  await adminPool.query(
    `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = $1 AND pid <> pg_backend_pid()`,
    [dbName],
  );
  await adminPool.query(`DROP DATABASE IF EXISTS ${dbName}`);
  await adminPool.query(`CREATE DATABASE ${dbName}`);

  process.env.DATABASE_URL = withDbName(BASE_URL, dbName);
  await runMigrations();

  testPool = getPool();
  return testPool;
}

export async function teardownTestDatabase(): Promise<void> {
  await closePool();
  if (adminPool && currentDbName) {
    await adminPool.query(`DROP DATABASE IF EXISTS ${currentDbName}`);
    await adminPool.end();
  }
}

export function getTestPool(): pg.Pool {
  if (!testPool) throw new Error('setupTestDatabase() has not been called yet');
  return testPool;
}

export interface BuildCtxOptions {
  actor?: Actor;
  now?: Date;
  clock?: ManualClock;
}

/** Builds a fresh Ctx bound to the shared test pool. Pass `clock` to share one ManualClock instance across several `buildCtx` calls (so advancing it in one Ctx is visible to another) — otherwise a fresh clock is created from `now` (or the current time). */
export function buildCtx(opts: BuildCtxOptions = {}): Ctx {
  const pool = getTestPool();
  const clock = opts.clock ?? new ManualClock(opts.now ?? new Date());
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

export function systemActor(job = 'test'): Actor {
  return { type: 'system', job };
}

export function userActor(userId: string): Actor {
  return { type: 'user', userId, trustLevel: 'standard' };
}

let emailCounter = 0;
/** Inserts a minimal `users` row and returns its id — every test table this build's suites touch FKs to `users(id)`. */
export async function createUser(pool: pg.Pool, overrides?: { createdAt?: Date }): Promise<string> {
  emailCounter += 1;
  const id = randomUUID();
  await pool.query(
    `INSERT INTO users (id, email, password_hash, birthdate, status, created_at, last_active_at)
     VALUES ($1, $2, 'x', '1995-01-01', 'active', $3, $3)`,
    [id, `retention-${emailCounter}-${Date.now()}@test.local`, overrides?.createdAt ?? new Date()],
  );
  return id;
}

export async function createProfile(pool: pg.Pool, userId: string): Promise<void> {
  await pool.query(
    `INSERT INTO profiles (user_id, display_name, bio, age, gender, seeking, relationship_intention, profile_completeness)
     VALUES ($1, 'Test', 'A long enough bio for completeness purposes.', 25, 'nonbinary', 'everyone', 'long_term', 50)`,
    [userId],
  );
}

export async function createConversation(
  pool: pg.Pool,
  userAId: string,
  userBId: string,
  status: 'active' | 'cooling' | 'archived' | 'established' = 'active',
  overrides?: { archivedAt?: Date; createdAt?: Date },
): Promise<string> {
  const [a, b] = userAId < userBId ? [userAId, userBId] : [userBId, userAId];
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO conversations (user_a_id, user_b_id, status, archived_at, created_at)
     VALUES ($1, $2, $3, $4, $5) RETURNING id`,
    [a, b, status, overrides?.archivedAt ?? null, overrides?.createdAt ?? new Date()],
  );
  return rows[0]!.id;
}

export async function createVenue(pool: pg.Pool): Promise<string> {
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO venues (name, address, latitude, longitude, category, active, margin_percent, time_slot_config, redemption_method)
     VALUES ('Retention Test Venue', '1 St', 0, 0, 'coffee', true, 10, '{"slots":[]}'::jsonb, 'qr_scan')
     RETURNING id`,
  );
  return rows[0]!.id;
}

/** Inserts a minimal `date_proposals` row — `payment_ledger` requires a real (NOT NULL) `date_proposal_id`, so a "financial record survives" test needs one to attach to. */
export async function createDateProposal(pool: pg.Pool, conversationId: string, proposerId: string, recipientId: string, venueId: string): Promise<string> {
  const now = new Date();
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO date_proposals (conversation_id, proposer_id, recipient_id, venue_id, scheduled_start, scheduled_end, status, policy_snapshot, escrow_amount_cents)
     VALUES ($1, $2, $3, $4, $5, $6, 'charged', '{}'::jsonb, 5000)
     RETURNING id`,
    [conversationId, proposerId, recipientId, venueId, now, new Date(now.getTime() + 3600_000)],
  );
  return rows[0]!.id;
}

export async function createPhoto(pool: pg.Pool, userId: string, overrides?: { isPrimary?: boolean }): Promise<string> {
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO user_photos (user_id, image_url, position, is_primary, moderation_status, face_detected)
     VALUES ($1, 'https://example.test/photo.jpg', 0, $2, 'approved', true)
     RETURNING id`,
    [userId, overrides?.isPrimary ?? true],
  );
  return rows[0]!.id;
}
