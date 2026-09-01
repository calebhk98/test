/**
 * Shared test setup for Agent A's unit tests (auth/profile/photo/photoExperiment).
 * Not part of INTERFACES.md's frozen list — a local helper the three
 * `tests/unit/*.test.ts` files share to avoid duplicating DB bootstrap.
 *
 * Uses a dedicated `odate_agent_a` database (per the build brief — never
 * touches `outcome_dating`/`outcome_dating_test`, which siblings/the
 * foundation smoke test use) so this agent's tests can run independently
 * of, and concurrently with, sibling agents' own test databases on the
 * same shared dev Postgres cluster.
 */
import pg from 'pg';
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
/** Base name for this agent's test databases — each of the (separately-processed, per Node's default test-file isolation) `tests/unit/*.test.ts` files must still pass its own unique `suffix` to `setupTestDatabase`, or two of *this agent's own* test files running concurrently will race DROP/CREATE DATABASE against each other on the shared dev Postgres cluster. */
const AGENT_A_DB_BASE_NAME = 'odate_agent_a';

function withDbName(url: string, dbName: string): string {
  const u = new URL(url);
  u.pathname = `/${dbName}`;
  return u.toString();
}

let adminPool: pg.Pool | undefined;
let testPool: pg.Pool | undefined;
let currentDbName: string | undefined;

/** Ensures `odate_agent_a_<suffix>` exists (fresh schema each run) and runs migrations against it. Call once from a suite's `before`, passing a `suffix` unique to that test file (e.g. `'auth'`, `'profile'`). */
export async function setupTestDatabase(suffix: string): Promise<pg.Pool> {
  const dbName = `${AGENT_A_DB_BASE_NAME}_${suffix}`;
  currentDbName = dbName;

  adminPool = new pg.Pool({ connectionString: BASE_URL });
  await adminPool.query(
    `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = $1 AND pid <> pg_backend_pid()`,
    [dbName],
  );
  await adminPool.query(`DROP DATABASE IF EXISTS ${dbName}`);
  await adminPool.query(`CREATE DATABASE ${dbName}`);

  process.env.DATABASE_URL = withDbName(BASE_URL, dbName);
  await runMigrations(); // uses the shared singleton pool (src/db/pool.ts), now pointed at this file's own database

  testPool = getPool();
  return testPool;
}

/** Call once from a suite's `after`. */
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
}

/** Builds a fresh Ctx bound to the shared test pool. `clock` is a fresh ManualClock per call unless `now` is supplied — pass the same `Date` across calls if a test needs a shared clock instance (use `ctx.clock` directly then). */
export function buildCtx(opts: BuildCtxOptions = {}): Ctx {
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

export function userActor(userId: string, trustLevel: TrustLevel = 'standard'): Actor {
  return { type: 'user', userId, trustLevel };
}

let emailCounter = 0;
export function uniqueEmail(prefix = 'test'): string {
  emailCounter += 1;
  return `${prefix}${emailCounter}.${Date.now()}@example.test`;
}
