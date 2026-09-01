/**
 * TEST-ONLY helper. Not imported by any production code path — exists
 * here (inside `src/services/notifications/**`, this build's owned
 * directory) rather than under `tests/unit/` because this build's file
 * ownership only extends to three specific new test files there
 * (`notificationDelivery.test.ts`, `devices.test.ts`,
 * `quietHours.test.ts`) and not to a shared fourth helper file. Mirrors
 * the shape every other agent's own `tests/unit/testCtxAgent*.ts` /
 * `testHarness.ts` uses: a dedicated `odate_notif_<suite>` database per
 * test file (per the build brief), created fresh in `before` and dropped
 * in `after`.
 */
import pg from 'pg';
import { runMigrations } from '../../db/migrate.js';
import { getPool, closePool } from '../../db/pool.js';
import { ConfigService } from '../../config/config.service.js';
import { FlagsService } from '../../config/flags.service.js';
import { ManualClock } from '../../lib/time.js';
import { createSilentLogger } from '../../lib/logger.js';
import { FakeProcessor } from '../payments/fake.processor.js';
import { StubMediaModerationAdapter } from '../media/stub.adapter.js';
import type { Actor, Ctx } from '../../lib/ctx.js';
import type { TrustLevel } from '../../domain/types.js';

const BASE_URL = process.env.DATABASE_URL ?? 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';
const DB_PREFIX = 'odate_notif';

function withDbName(url: string, dbName: string): string {
  const u = new URL(url);
  u.pathname = `/${dbName}`;
  return u.toString();
}

let adminPool: pg.Pool | undefined;
let testPool: pg.Pool | undefined;
let dbName: string | undefined;

/** Ensures `odate_notif_<suite>` exists (fresh schema) and runs migrations against it. Call once from a suite's `before`. */
export async function setupTestDatabase(suite: string): Promise<pg.Pool> {
  dbName = `${DB_PREFIX}_${suite}`;
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

export function buildCtx(opts: BuildCtxOptions = {}): Ctx {
  const pool = getTestPool();
  const clock = opts.clock ?? new ManualClock(opts.now ?? new Date('2026-01-01T12:00:00.000Z'));
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

export async function insertUser(pool: pg.Pool, opts: { email?: string } = {}): Promise<string> {
  userSeq += 1;
  const email = opts.email ?? `notif-user-${userSeq}-${Date.now()}@test.local`;
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO users (email, password_hash, birthdate, status, trust_score, trust_level)
     VALUES ($1, 'x', '1995-01-01', 'active', 50, 'standard')
     RETURNING id`,
    [email],
  );
  return rows[0]!.id;
}
