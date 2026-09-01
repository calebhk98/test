/**
 * Shared test setup for Agent E's unit tests (trust/moderation/report/appeal).
 * Not part of INTERFACES.md's frozen list — a local helper the
 * `tests/unit/{trust,moderation,report,appeal}.test.ts` files share to
 * avoid duplicating DB bootstrap. Mirrors the shape of Agent A's
 * `tests/unit/testCtx.ts` (same pattern, kept as a separate file rather
 * than a shared import so each agent's test suite stays independently
 * runnable and neither owns a file outside their own list).
 *
 * Uses a dedicated `odate_agent_e` database (per the build brief — never
 * touches `outcome_dating`/`outcome_dating_test`/other agents' `odate_*`
 * databases) so this agent's tests can run independently of, and
 * concurrently with, sibling agents' own test databases on the same
 * shared dev Postgres cluster.
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
import type { TrustLevel } from '../../src/domain/types.js';

const BASE_URL = process.env.DATABASE_URL ?? 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';
/** Base name from the build brief ("Use your OWN database odate_agent_e"). Node's test runner runs separate `*.test.ts` files concurrently in separate processes by default, so each of this agent's four suites gets its own `odate_agent_e_<suite>` database (see `setupTestDatabase`'s `suite` param) rather than racing DROP/CREATE DATABASE against each other on one shared name. */
const AGENT_E_DB_PREFIX = 'odate_agent_e';

function withDbName(url: string, dbName: string): string {
  const u = new URL(url);
  u.pathname = `/${dbName}`;
  return u.toString();
}

let adminPool: pg.Pool | undefined;
let testPool: pg.Pool | undefined;
let dbName: string | undefined;

/** Ensures `odate_agent_e_<suite>` exists (fresh schema each run) and runs migrations against it. Call once from a suite's `before`, with a `suite` name unique per test file (e.g. 'trust', 'moderation') so concurrently-run test files never race on the same database. */
export async function setupTestDatabase(suite: string): Promise<pg.Pool> {
  dbName = `${AGENT_E_DB_PREFIX}_${suite}`;
  adminPool = new pg.Pool({ connectionString: BASE_URL });
  await adminPool.query(
    `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = $1 AND pid <> pg_backend_pid()`,
    [dbName],
  );
  await adminPool.query(`DROP DATABASE IF EXISTS ${dbName}`);
  await adminPool.query(`CREATE DATABASE ${dbName}`);

  process.env.DATABASE_URL = withDbName(BASE_URL, dbName);
  await runMigrations(); // uses the shared singleton pool (src/db/pool.ts), now pointed at odate_agent_e_<suite>

  testPool = getPool();
  return testPool;
}

/** Call once from a suite's `after`. */
export async function teardownTestDatabase(): Promise<void> {
  await closePool();
  if (adminPool && dbName) {
    await adminPool.query(`DROP DATABASE IF EXISTS ${dbName}`);
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

/** Builds a fresh Ctx bound to the shared test pool. Pass `clock` to share one ManualClock instance across calls (needed whenever a test advances time between service calls). */
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

export function userActor(userId: string, trustLevel: TrustLevel = 'standard'): Actor {
  return { type: 'user', userId, trustLevel };
}

let emailCounter = 0;
export function uniqueEmail(prefix = 'test'): string {
  emailCounter += 1;
  return `${prefix}${emailCounter}.${Date.now()}@example.test`;
}

/** Directly inserts a minimal `users` row (bypassing auth.service, which this agent doesn't own) for test fixtures. Returns the new user id. */
export async function insertUser(
  ctx: Ctx,
  opts: { emailVerified?: boolean; createdAt?: Date; trustScore?: number; trustLevel?: TrustLevel; shadowbanned?: boolean; suspended?: boolean; status?: 'active' | 'suspended' | 'deleted' } = {},
): Promise<string> {
  const id = randomUUID();
  await ctx.db.query(
    `INSERT INTO users (id, email, password_hash, birthdate, status, trust_score, trust_level, shadowbanned, suspended, email_verified_at, created_at, last_active_at)
     VALUES ($1, $2, 'x', '1990-01-01', $3, $4, $5, $6, $7, $8, $9, $9)`,
    [
      id,
      uniqueEmail('u'),
      opts.status ?? 'active',
      opts.trustScore ?? 50,
      opts.trustLevel ?? 'standard',
      opts.shadowbanned ?? false,
      opts.suspended ?? false,
      opts.emailVerified ? (opts.createdAt ?? new Date()) : null,
      opts.createdAt ?? new Date(),
    ],
  );
  return id;
}

/** Inserts a minimal `profiles` row for `userId`. */
export async function insertProfile(ctx: Ctx, userId: string, opts: { completeness?: number } = {}): Promise<void> {
  await ctx.db.query(
    `INSERT INTO profiles (user_id, display_name, bio, age, gender, seeking, relationship_intention, profile_completeness)
     VALUES ($1, 'Test User', 'bio', 25, 'nonbinary', 'everyone', 'long_term', $2)`,
    [userId, opts.completeness ?? 0],
  );
}

/** Inserts a verified/unverified `payment_methods` row for `userId`. */
export async function insertPaymentMethod(ctx: Ctx, userId: string, opts: { verified?: boolean } = {}): Promise<string> {
  const id = randomUUID();
  await ctx.db.query(
    `INSERT INTO payment_methods (id, user_id, processor, processor_token, verified_at)
     VALUES ($1, $2, 'fake', 'tok_test', $3)`,
    [id, userId, opts.verified ? new Date() : null],
  );
  return id;
}

/** Inserts a canonically-ordered `conversations` row between two users. */
export async function insertConversation(ctx: Ctx, userAId: string, userBId: string): Promise<string> {
  const [a, b] = userAId < userBId ? [userAId, userBId] : [userBId, userAId];
  const id = randomUUID();
  await ctx.db.query(
    `INSERT INTO conversations (id, user_a_id, user_b_id, status) VALUES ($1, $2, $3, 'active')`,
    [id, a, b],
  );
  return id;
}

/** Inserts a `user_auth_events` row carrying a device fingerprint, for anti-brigading tests. */
export async function insertAuthEvent(ctx: Ctx, userId: string, deviceFingerprint: string): Promise<void> {
  await ctx.db.query(
    `INSERT INTO user_auth_events (user_id, device_fingerprint, success) VALUES ($1, $2, true)`,
    [userId, deviceFingerprint],
  );
}
