/**
 * Shared test scaffolding for `tests/unit/matches.test.ts` and
 * `tests/unit/timeline.test.ts`. Not a `*.test.ts` file itself, so
 * `node --test` never tries to run it directly.
 *
 * Every service this build's tests exercise (`interest`, `conversation`,
 * `message`, `profile`, `venue`, `payment`, `dateProposal`, `discovery`)
 * is the real, fully-implemented sibling-agent code — no mocking. Per the
 * task brief ("use your own Postgres databases (`odate_match_<suite>`)"),
 * every db name is namespaced under `odate_match_*`, one per test FILE
 * (each gets its own `suite` string) so concurrently-run test files never
 * race DROP/CREATE DATABASE against the same name.
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
import * as profileService from '../../src/services/profile.service.js';
import * as paymentService from '../../src/services/payment.service.js';
import type { Actor, Ctx } from '../../src/lib/ctx.js';
import type { TrustLevel } from '../../src/domain/types.js';

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

/** Creates a fresh, migrated, config/flag-seeded database named `odate_match_<suite>`. */
export async function setupTestDb(suite: string): Promise<TestDb> {
  const dbName = `odate_match_${suite}`;
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
export function systemActor(job = 'test-job'): Actor {
  return { type: 'system', job };
}
export function venueStaffActor(venueStaffId: string, venueId: string): Actor {
  return { type: 'venue_staff', venueStaffId, venueId };
}

let userCounter = 0;

/** Inserts a minimal `users` row and returns its id — no profile (see `createUserWithProfile` for that). */
export async function createUser(db: TestDb, overrides?: { email?: string; trustLevel?: TrustLevel }): Promise<string> {
  userCounter += 1;
  const email = overrides?.email ?? `test-match-user-${userCounter}-${Date.now()}@example.test`;
  const { rows } = await db.pool.query<{ id: string }>(
    `INSERT INTO users (email, password_hash, birthdate, status, trust_score, trust_level, email_verified_at)
     VALUES ($1, 'x', '1995-01-01', 'active', 60, $2, now())
     RETURNING id`,
    [email, overrides?.trustLevel ?? 'standard'],
  );
  return rows[0]!.id;
}

/**
 * Inserts a user AND a complete-enough profile (via the real
 * `profile.service#updateMyProfile`, never a hand-rolled `profiles`
 * INSERT — so it can never drift from what that service actually expects
 * on the row). Returns the userId; `lat`/`lon` default apart so
 * `approximateDistanceKm` is a real, non-null, non-zero number by default.
 */
export async function createUserWithProfile(
  db: TestDb,
  overrides?: { displayName?: string; gender?: string; seeking?: string; lat?: number; lon?: number; trustLevel?: TrustLevel },
): Promise<string> {
  const userId = await createUser(db, { trustLevel: overrides?.trustLevel });
  const ctx = makeCtx(db, userActor(userId));
  await profileService.updateMyProfile(ctx, {
    displayName: overrides?.displayName ?? `Match Test User ${userId.slice(0, 8)}`,
    bio: 'Enjoys coffee, board games, and long walks.',
    city: 'Springfield',
    latitude: overrides?.lat ?? 39.78,
    longitude: overrides?.lon ?? -89.65,
    age: 28,
    gender: overrides?.gender ?? 'woman',
    seeking: overrides?.seeking ?? 'men',
    relationshipIntention: 'long_term',
  });
  return userId;
}

/** Adds an approved photo directly (bypassing the moderation port for test speed) and optionally makes it primary. */
export async function addApprovedPhoto(db: TestDb, userId: string, imageUrl: string, opts?: { primary?: boolean; position?: number }): Promise<string> {
  const { rows } = await db.pool.query<{ id: string }>(
    `INSERT INTO user_photos (user_id, image_url, position, is_primary, moderation_status)
     VALUES ($1, $2, $3, $4, 'approved') RETURNING id`,
    [userId, imageUrl, opts?.position ?? 0, opts?.primary ?? true],
  );
  return rows[0]!.id;
}

/** Verified, default payment method for `userId` via the real `payment.service#addPaymentMethod`. Pass a token containing `fail_authorize`/`fail_capture` to drive `FakeProcessor` failure paths (see that class's doc). */
export async function addPaymentMethod(db: TestDb, userId: string, token: string, processor: FakeProcessor): Promise<void> {
  const ctx = makeCtx(db, userActor(userId), { payments: processor });
  await paymentService.addPaymentMethod(ctx, { processorToken: token, brand: 'visa', last4: '4242', makeDefault: true });
}

export async function createVenue(db: TestDb, overrides?: { active?: boolean; name?: string }): Promise<string> {
  const { rows } = await db.pool.query<{ id: string }>(
    `INSERT INTO venues (name, address, latitude, longitude, category, active, margin_percent, time_slot_config, redemption_method)
     VALUES ($1, '1 Test St', 39.78, -89.65, 'coffee', $2, 15, '{"slots":[]}'::jsonb, 'qr_scan')
     RETURNING id`,
    [overrides?.name ?? 'Test Cafe', overrides?.active ?? true],
  );
  return rows[0]!.id;
}
