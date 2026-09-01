/**
 * Shared test setup for Agent C's unit tests (interest/chat/textscan).
 * Not part of INTERFACES.md's frozen list — a local helper the
 * `tests/unit/{interest,chat,notification}.test.ts` files share to avoid
 * duplicating DB bootstrap (`textscan.test.ts` needs none of this — it
 * tests pure functions only).
 *
 * Uses a dedicated `odate_agent_c` database (per the build brief — never
 * touches `outcome_dating`/`outcome_dating_test`/other agents' `odate_*`
 * databases). Node's built-in test runner runs separate `*.test.ts` files
 * concurrently in separate processes by default, so each suite gets its
 * own `odate_agent_c_<suite>` database rather than racing DROP/CREATE
 * DATABASE against a shared name.
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
const AGENT_C_DB_PREFIX = 'odate_agent_c';

function withDbName(url: string, dbName: string): string {
  const u = new URL(url);
  u.pathname = `/${dbName}`;
  return u.toString();
}

let adminPool: pg.Pool | undefined;
let testPool: pg.Pool | undefined;
let dbName: string | undefined;

/** Ensures `odate_agent_c_<suite>` exists (fresh schema each run) and runs migrations against it. Call once from a suite's `before`, with a `suite` name unique per test file so concurrently-run test files never race on the same database. */
export async function setupTestDatabase(suite: string): Promise<pg.Pool> {
  dbName = `${AGENT_C_DB_PREFIX}_${suite}`;
  adminPool = new pg.Pool({ connectionString: BASE_URL });
  await adminPool.query(
    `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = $1 AND pid <> pg_backend_pid()`,
    [dbName],
  );
  await adminPool.query(`DROP DATABASE IF EXISTS ${dbName}`);
  await adminPool.query(`CREATE DATABASE ${dbName}`);

  process.env.DATABASE_URL = withDbName(BASE_URL, dbName);
  await runMigrations(); // uses the shared singleton pool (src/db/pool.ts), now pointed at odate_agent_c_<suite>

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
  const clock = opts.clock ?? new ManualClock(opts.now ?? new Date('2026-01-01T00:00:00.000Z'));
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

let userSeq = 0;

/** Inserts a minimal `users` row (no profile — none of Agent C's tables FK to `profiles`) and returns its id. */
export async function insertUser(pool: pg.Pool, opts: { trustLevel?: TrustLevel; email?: string } = {}): Promise<string> {
  userSeq += 1;
  const email = opts.email ?? `agent-c-user-${userSeq}-${Date.now()}@test.local`;
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO users (email, password_hash, birthdate, status, trust_score, trust_level)
     VALUES ($1, 'x', '1995-01-01', 'active', 50, $2)
     RETURNING id`,
    [email, opts.trustLevel ?? 'standard'],
  );
  return rows[0]!.id;
}
