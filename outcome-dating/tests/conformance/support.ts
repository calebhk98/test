/**
 * Shared scaffolding for `tests/conformance/**`.
 *
 * Deliberately NOT a re-export of `tests/unit/testHarness.ts` or
 * `tests/http/testServer.ts`: this task's brief lists "the shared test
 * support module" among the files other agents are concurrently editing,
 * and instructs this suite to avoid depending on areas under concurrent
 * change where it can. This file is self-contained so a change to those
 * other harnesses cannot break the conformance suite (and vice versa),
 * even though the pattern (per-file database, ManualClock, config/flags
 * seeded once, service-layer calls with a real `Ctx`) is deliberately the
 * same one the rest of the repo already uses, see docs/test-strategy.md.
 *
 * Every database this file creates is named `odate_conf_<suite>_<run>`,
 * per the task's "use odate_conf_<suite>" instruction. `node --test`
 * runs each matched file as its own process, so two conformance test
 * files never contend over the same database even when run concurrently
 * with the rest of the suite (or with other agents' own `npm test` runs
 * against the same shared dev cluster), the `RUN_SUFFIX` below closes
 * that same cross-run race the other harnesses already document.
 */
import pg from 'pg';
import { randomUUID } from 'node:crypto';
import { runMigrations } from '../../src/db/migrate.js';
import { closePool, getPool } from '../../src/db/pool.js';
import { ConfigService } from '../../src/config/config.service.js';
import { FlagsService } from '../../src/config/flags.service.js';
import { ManualClock } from '../../src/lib/time.js';
import { createSilentLogger } from '../../src/lib/logger.js';
import { StubMediaModerationAdapter } from '../../src/services/media/stub.adapter.js';
import { FakeProcessor } from '../../src/services/payments/fake.processor.js';
import type { Actor, Ctx } from '../../src/lib/ctx.js';
import type { TrustLevel } from '../../src/domain/types.js';

const ADMIN_BASE_URL = process.env.DATABASE_URL ?? 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';
const RUN_SUFFIX = randomUUID().replace(/-/g, '').slice(0, 8);

function withDbName(url: string, dbName: string): string {
  const u = new URL(url);
  u.pathname = `/${dbName}`;
  return u.toString();
}

export interface TestDb {
  dbName: string;
  pool: pg.Pool;
  clock: ManualClock;
  config: ConfigService;
  flags: FlagsService;
}

/** Creates a fresh, migrated, config/flag-seeded `odate_conf_<suite>_<run>` database. Call once from a suite's `before`. */
export async function setupConformanceDb(suite: string): Promise<TestDb> {
  const dbName = `odate_conf_${suite}_${RUN_SUFFIX}`;
  const adminPool = new pg.Pool({ connectionString: ADMIN_BASE_URL });
  await adminPool.query(
    `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = $1 AND pid <> pg_backend_pid()`,
    [dbName],
  );
  await adminPool.query(`DROP DATABASE IF EXISTS ${dbName}`);
  await adminPool.query(`CREATE DATABASE ${dbName}`);
  await adminPool.end();

  process.env.DATABASE_URL = withDbName(ADMIN_BASE_URL, dbName);
  await runMigrations();

  const pool = getPool();
  // Fixed historical epoch, never real "now" (docs/test-audit.md flags
  // real-clock construction as a real bug class: it silently reintroduces
  // non-determinism into boundary tests). Wednesday, chosen arbitrarily.
  const clock = new ManualClock(new Date('2026-01-07T12:00:00.000Z'));
  const logger = createSilentLogger();
  const config = new ConfigService(pool, clock, logger);
  const flags = new FlagsService(pool, logger);
  await config.seedDefaults('system:test');
  await flags.seedKnownFlags();

  return { dbName, pool, clock, config, flags };
}

export async function teardownConformanceDb(db: TestDb): Promise<void> {
  await closePool();
  const adminPool = new pg.Pool({ connectionString: ADMIN_BASE_URL });
  await adminPool.query(`DROP DATABASE IF EXISTS ${db.dbName}`);
  await adminPool.end();
}

/** Builds a `Ctx` bound to `db.pool` (or an explicit client/transaction, if passed). */
export function makeCtx(db: TestDb, actor: Actor, opts?: { payments?: FakeProcessor; dbClient?: pg.PoolClient | pg.Pool }): Ctx {
  return {
    db: opts?.dbClient ?? db.pool,
    clock: db.clock,
    config: db.config,
    flags: db.flags,
    logger: createSilentLogger(),
    actor,
    payments: opts?.payments ?? new FakeProcessor(),
    media: new StubMediaModerationAdapter(),
  };
}

export function userActor(userId: string, trustLevel: TrustLevel = 'standard'): Actor {
  return { type: 'user', userId, trustLevel };
}
export function adminActor(adminId = 'admin-1'): Actor {
  return { type: 'admin', adminId };
}
export function systemActor(job = 'conformance-test'): Actor {
  return { type: 'system', job };
}
export function venueStaffActor(venueStaffId: string, venueId: string): Actor {
  return { type: 'venue_staff', venueStaffId, venueId };
}

let userCounter = 0;

/** Inserts a minimal `users` row (active, standard trust, email-verified) and returns its id. */
export async function createUser(db: TestDb, overrides?: { email?: string; trustLevel?: TrustLevel; trustScore?: number; birthdate?: string }): Promise<string> {
  userCounter += 1;
  const email = overrides?.email ?? `conf-user-${userCounter}-${randomUUID()}@example.test`;
  const { rows } = await db.pool.query<{ id: string }>(
    `INSERT INTO users (email, password_hash, birthdate, status, trust_score, trust_level, email_verified_at)
     VALUES ($1, 'x', $2, 'active', $3, $4, now())
     RETURNING id`,
    [email, overrides?.birthdate ?? '1995-01-01', overrides?.trustScore ?? 60, overrides?.trustLevel ?? 'standard'],
  );
  return rows[0]!.id;
}

/** Inserts a payment method row. Use a token containing "fail_authorize"/"fail_capture" to drive `FakeProcessor` failure paths (see fake.processor.ts). */
export async function createPaymentMethod(db: TestDb, userId: string, token: string, opts?: { verified?: boolean }): Promise<string> {
  const { rows } = await db.pool.query<{ id: string }>(
    `INSERT INTO payment_methods (user_id, processor, processor_token, brand, last4, is_default, verified_at)
     VALUES ($1, 'fake', $2, 'visa', '4242', true, $3)
     RETURNING id`,
    [userId, token, opts?.verified === false ? null : new Date()],
  );
  return rows[0]!.id;
}

export async function createConversation(
  db: TestDb,
  userAId: string,
  userBId: string,
  status: 'active' | 'cooling' | 'archived' | 'established' = 'active',
): Promise<string> {
  const [a, b] = userAId < userBId ? [userAId, userBId] : [userBId, userAId];
  const { rows } = await db.pool.query<{ id: string }>(
    `INSERT INTO conversations (user_a_id, user_b_id, status) VALUES ($1, $2, $3) RETURNING id`,
    [a, b, status],
  );
  return rows[0]!.id;
}

export async function createVenue(db: TestDb, overrides?: { active?: boolean; name?: string }): Promise<string> {
  const { rows } = await db.pool.query<{ id: string }>(
    `INSERT INTO venues (name, address, latitude, longitude, category, active, margin_percent, time_slot_config, redemption_method)
     VALUES ($1, '1 Test St', 39.0, -89.0, 'coffee', $2, 15, '{"slots":[]}'::jsonb, 'qr_scan')
     RETURNING id`,
    [overrides?.name ?? 'Test Cafe', overrides?.active ?? true],
  );
  return rows[0]!.id;
}

/** Raw read helper used only to assert on outcomes, never to fabricate them (see this suite's "drive through services" rule). Column list kept narrow on purpose. */
export async function rawRow<T extends Record<string, unknown>>(db: TestDb, sql: string, params: unknown[]): Promise<T | undefined> {
  const { rows } = await db.pool.query<T>(sql, params);
  return rows[0];
}

export async function rawRows<T extends Record<string, unknown>>(db: TestDb, sql: string, params: unknown[]): Promise<T[]> {
  const { rows } = await db.pool.query<T>(sql, params);
  return rows;
}
