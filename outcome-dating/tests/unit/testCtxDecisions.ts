/**
 * Shared test scaffolding for the decision-layer's own unit tests
 * (venue settlement, no_show/disputed automated resolution, and the
 * misc config/threshold decisions). Mirrors `tests/unit/testHarness.ts`'s
 * shape (Agent D's dateProposal/payment/voucher harness) — each test FILE
 * gets its own dedicated Postgres database, created fresh in `before` and
 * dropped in `after`, namespaced under `odate_decisions_*` per the task's
 * "use your own database" instruction (this harness is NOT
 * `testHarness.ts` itself because that file hardcodes the
 * `odate_agent_d_*` prefix).
 *
 * Not itself a `*.test.ts` file, so `node --test` does not try to run it.
 */
import pg from 'pg';
import { runMigrations } from '../../src/db/migrate.js';
import { closePool, getPool } from '../../src/db/pool.js';
import { ConfigService } from '../../src/config/config.service.js';
import { FlagsService } from '../../src/config/flags.service.js';
import { ManualClock } from '../../src/lib/time.js';
import { createSilentLogger } from '../../src/lib/logger.js';
import { StubMediaModerationAdapter } from '../../src/services/media/stub.adapter.js';
import { FakeProcessor } from '../../src/services/payments/fake.processor.js';
import type { Actor, Ctx } from '../../src/lib/ctx.js';

const ADMIN_BASE_URL = process.env.DATABASE_URL ?? 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';

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

/** Creates a fresh, migrated, config-seeded database named `odate_decisions_<suffix>`. */
export async function setupTestDb(suffix: string): Promise<TestDb> {
  const dbName = `odate_decisions_${suffix}`;
  const adminPool = new pg.Pool({ connectionString: ADMIN_BASE_URL });
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

/** Builds a `Ctx` bound to `db.pool` (or a transaction client, if passed explicitly). */
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

export function userActor(userId: string, trustLevel: 'limited' | 'standard' | 'trusted' | 'elite' = 'standard'): Actor {
  return { type: 'user', userId, trustLevel };
}

export function adminActor(adminId = 'admin-1'): Actor {
  return { type: 'admin', adminId };
}

export function systemActor(job = 'test-job'): Actor {
  return { type: 'system', job };
}

export function venueStaffActor(venueStaffId: string, venueId: string): Actor {
  return { type: 'venue_staff', venueStaffId, venueId };
}

let userCounter = 0;

/** Inserts a minimal `users` row and returns its id. */
export async function createUser(db: TestDb, overrides?: { email?: string; trustLevel?: 'limited' | 'standard' | 'trusted' | 'elite' }): Promise<string> {
  userCounter += 1;
  const email = overrides?.email ?? `test-user-${userCounter}-${Date.now()}@example.test`;
  const { rows } = await db.pool.query<{ id: string }>(
    `INSERT INTO users (email, password_hash, birthdate, status, trust_score, trust_level, email_verified_at)
     VALUES ($1, 'x', '1995-01-01', 'active', 60, $2, now())
     RETURNING id`,
    [email, overrides?.trustLevel ?? 'standard'],
  );
  return rows[0]!.id;
}

/** Inserts a payment method row for `userId` with the given processor token (use "fail_authorize"/"fail_capture" substrings to drive `FakeProcessor` failure paths). */
export async function createPaymentMethod(db: TestDb, userId: string, token: string, opts?: { processor?: string }): Promise<string> {
  const { rows } = await db.pool.query<{ id: string }>(
    `INSERT INTO payment_methods (user_id, processor, processor_token, brand, last4, is_default, verified_at)
     VALUES ($1, $2, $3, 'visa', '4242', true, now())
     RETURNING id`,
    [userId, opts?.processor ?? 'fake', token],
  );
  return rows[0]!.id;
}

export async function createConversation(db: TestDb, userAId: string, userBId: string, status: 'active' | 'cooling' | 'archived' | 'established' = 'active'): Promise<string> {
  const [a, b] = userAId < userBId ? [userAId, userBId] : [userBId, userAId];
  const { rows } = await db.pool.query<{ id: string }>(
    `INSERT INTO conversations (user_a_id, user_b_id, status) VALUES ($1, $2, $3) RETURNING id`,
    [a, b, status],
  );
  return rows[0]!.id;
}

export async function createVenue(db: TestDb, overrides?: { active?: boolean; marginPercent?: number }): Promise<string> {
  const { rows } = await db.pool.query<{ id: string }>(
    `INSERT INTO venues (name, address, latitude, longitude, category, active, margin_percent, time_slot_config, redemption_method)
     VALUES ('Test Cafe', '1 Test St', 39.0, -89.0, 'coffee', $1, $2, '{"slots":[]}'::jsonb, 'qr_scan')
     RETURNING id`,
    [overrides?.active ?? true, overrides?.marginPercent ?? 15],
  );
  return rows[0]!.id;
}

export async function createVenueStaff(db: TestDb, venueId: string): Promise<{ staffId: string; userId: string }> {
  const userId = await createUser(db);
  const { rows } = await db.pool.query<{ id: string }>(
    `INSERT INTO venue_staff (user_id, venue_id, active) VALUES ($1, $2, true) RETURNING id`,
    [userId, venueId],
  );
  return { staffId: rows[0]!.id, userId };
}
