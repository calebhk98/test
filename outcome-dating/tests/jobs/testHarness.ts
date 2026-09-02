/**
 * Shared test scaffolding for `tests/jobs/*.test.ts`.
 *
 * Every §25 job is a plain `(ctx: Ctx) => Promise<T>` (see
 * `src/jobs/types.ts`), so tests call it directly against a `Ctx` built
 * here with a `ManualClock`, no scheduler, no waiting on real time, per
 * the task brief ("tests invoke it directly with a controlled clock rather
 * than waiting"). `JobScheduler` itself (advisory locking, interval
 * wiring) is exercised separately in `tests/jobs/scheduler.test.ts`.
 *
 * Per the task's "use your own Postgres databases" instruction, every db
 * name is namespaced under `odate_jobs_<suite>`.
 */
import pg from 'pg';
import { randomUUID } from 'node:crypto';
import { runMigrations } from '../../src/db/migrate.js';
import { closePool, getPool } from '../../src/db/pool.js';
import { ConfigService } from '../../src/config/config.service.js';
import { FlagsService } from '../../src/config/flags.service.js';
import { ManualClock } from '../../src/lib/time.js';
import { createSilentLogger } from '../../src/lib/logger.js';
import { FakeProcessor } from '../../src/services/payments/fake.processor.js';
import { StubMediaModerationAdapter } from '../../src/services/media/stub.adapter.js';
import type { Actor, Ctx } from '../../src/lib/ctx.js';
import type { TrustLevel } from '../../src/domain/types.js';
import { pinTrustLevel } from '../support/trustFixtures.js';

const ADMIN_BASE_URL = process.env.DATABASE_URL ?? 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';
/** Per-process random suffix (see `tests/unit/testCtx.ts`'s longer note), closes the cross-run database-name-collision race (test-audit.md's database-race item). */
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

export async function setupTestDb(suite: string): Promise<TestDb> {
  const dbName = `odate_jobs_${suite}_${RUN_SUFFIX}`;
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
  const clock = new ManualClock(new Date('2026-01-05T12:00:00.000Z'));
  const logger = createSilentLogger();
  const config = new ConfigService(pool, clock, logger);
  const flags = new FlagsService(pool, logger);
  await config.seedDefaults('system:test');
  await flags.seedKnownFlags();

  return { dbName, pool, clock, config, flags };
}

export async function teardownTestDb(db: TestDb): Promise<void> {
  await closePool();
  const adminPool = new pg.Pool({ connectionString: ADMIN_BASE_URL });
  await adminPool.query(`DROP DATABASE IF EXISTS ${db.dbName}`);
  await adminPool.end();
}

export function makeCtx(db: TestDb, actor: Actor = { type: 'system', job: 'test' }): Ctx {
  return {
    db: db.pool,
    clock: db.clock,
    config: db.config,
    flags: db.flags,
    logger: createSilentLogger(),
    actor,
    payments: new FakeProcessor(),
    media: new StubMediaModerationAdapter(),
  };
}

export function userActor(userId: string, trustLevel: TrustLevel = 'standard'): Actor {
  return { type: 'user', userId, trustLevel };
}

let emailCounter = 0;

/**
 * `trustLevel`, if given, is NOT written to the row directly (see
 * db/migrations/029_trust_invariant.sql). Reached via
 * `tests/support/trustFixtures.ts#pinTrustLevel` instead, the real
 * trust.service.ts path.
 */
export async function createUser(db: TestDb, overrides?: { trustLevel?: TrustLevel; createdAt?: Date }): Promise<string> {
  emailCounter += 1;
  const id = randomUUID();
  await db.pool.query(
    `INSERT INTO users (id, email, password_hash, birthdate, status, created_at, last_active_at)
     VALUES ($1, $2, 'x', '1995-01-01', 'active', $3, $3)`,
    [id, `jobs-user-${emailCounter}-${Date.now()}@test.local`, overrides?.createdAt ?? new Date()],
  );
  if (overrides?.trustLevel) {
    await pinTrustLevel(makeCtx(db, { type: 'system', job: 'test-fixture' }), id, overrides.trustLevel);
  }
  return id;
}

export async function createProfile(db: TestDb, userId: string, completeness = 100): Promise<void> {
  await db.pool.query(
    `INSERT INTO profiles (user_id, display_name, bio, age, gender, seeking, relationship_intention, profile_completeness)
     VALUES ($1, 'Test', 'A long enough bio for completeness purposes.', 25, 'nonbinary', 'everyone', 'long_term', $2)`,
    [userId, completeness],
  );
}

export async function createConversation(db: TestDb, userAId: string, userBId: string, status: 'active' | 'cooling' | 'archived' | 'established' = 'active'): Promise<string> {
  const [a, b] = userAId < userBId ? [userAId, userBId] : [userBId, userAId];
  const { rows } = await db.pool.query<{ id: string }>(
    `INSERT INTO conversations (user_a_id, user_b_id, status) VALUES ($1, $2, $3) RETURNING id`,
    [a, b, status],
  );
  return rows[0]!.id;
}

export async function createVenue(db: TestDb): Promise<string> {
  const { rows } = await db.pool.query<{ id: string }>(
    `INSERT INTO venues (name, address, latitude, longitude, category, active, margin_percent, time_slot_config, redemption_method)
     VALUES ('Jobs Test Venue', '1 St', 0, 0, 'coffee', true, 10, '{"slots":[]}'::jsonb, 'qr_scan')
     RETURNING id`,
  );
  return rows[0]!.id;
}

export async function createPaymentMethod(db: TestDb, userId: string, token = 'tok_ok'): Promise<void> {
  await db.pool.query(
    `INSERT INTO payment_methods (user_id, processor, processor_token, is_default, verified_at) VALUES ($1, 'fake', $2, true, now())`,
    [userId, token],
  );
}
