/**
 * Shared test setup for this build's mutual-eligibility-enforcement unit
 * tests (`eligibility.test.ts`, `autoDecline.test.ts`). Not part of
 * INTERFACES.md's frozen list — a local helper, same pattern as
 * `testCtxAgentC.ts`/`testCtx.ts` (one per agent/build), so these two
 * files don't duplicate DB bootstrap.
 *
 * Uses dedicated `odate_elig_<suite>` databases (per this build's task
 * brief — never touches `outcome_dating`/`outcome_dating_test`/other
 * agents' `odate_*` databases) — one database per test FILE (`suite`
 * unique per file) since Node's test runner runs separate `*.test.ts`
 * files concurrently in separate processes by default.
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
const DB_PREFIX = 'odate_elig';
/** Per-process random suffix (see `tests/unit/testCtx.ts`'s longer note) — closes the cross-run database-name-collision race (test-audit.md's database-race item). */
const RUN_SUFFIX = randomUUID().replace(/-/g, '').slice(0, 8);

function withDbName(url: string, dbName: string): string {
  const u = new URL(url);
  u.pathname = `/${dbName}`;
  return u.toString();
}

let adminPool: pg.Pool | undefined;
let testPool: pg.Pool | undefined;
let dbName: string | undefined;

/** Ensures `odate_elig_<suite>` exists (fresh schema each run) and runs migrations against it. Call once from a suite's `before`, with a `suite` name unique per test file. */
export async function setupTestDatabase(suite: string): Promise<pg.Pool> {
  dbName = `${DB_PREFIX}_${suite}_${RUN_SUFFIX}`;
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
  clock?: ManualClock;
  now?: Date;
}

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

export interface MakeUserOpts {
  age?: number;
  gender?: string;
  seeking?: string;
  relationshipIntention?: string;
  latitude?: number;
  longitude?: number;
  trustLevel?: TrustLevel;
}

/**
 * Inserts a `users` + `profiles` row (both are needed here, unlike
 * `testCtxAgentC.ts`'s `insertUser`, because filter evaluation reads
 * `profiles` — see `filter.service.ts`'s "CANDIDATE ATTRIBUTE SOURCING"
 * note) and returns the new user's id.
 */
export async function makeUser(pool: pg.Pool, opts: MakeUserOpts = {}): Promise<string> {
  userSeq += 1;
  const email = `elig-user-${userSeq}-${Date.now()}@test.local`;
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO users (email, password_hash, birthdate, status, trust_score, trust_level)
     VALUES ($1, 'x', '1995-01-01', 'active', 50, $2)
     RETURNING id`,
    [email, opts.trustLevel ?? 'standard'],
  );
  const userId = rows[0]!.id;
  await pool.query(
    `INSERT INTO profiles (user_id, display_name, city, latitude, longitude, location_fuzzed, age, gender, seeking, relationship_intention, profile_completeness)
     VALUES ($1, $2, 'Testville', $3, $4, true, $5, $6, $7, $8, 90)`,
    [
      userId,
      `User${userSeq}`,
      opts.latitude ?? 40.0,
      opts.longitude ?? -75.0,
      opts.age ?? 30,
      opts.gender ?? 'woman',
      opts.seeking ?? 'any',
      opts.relationshipIntention ?? 'long_term',
    ],
  );
  // An approved photo — every user in these fixtures needs one to be
  // visible in discovery at all (§10.2 rule 4), so the Layer-1
  // verification test's discovery calls behave realistically.
  await pool.query(
    `INSERT INTO user_photos (user_id, image_url, position, is_primary, moderation_status)
     VALUES ($1, 'https://example.test/photo.jpg', 0, true, 'approved')`,
    [userId],
  );
  return userId;
}

/** Sets/replaces one enabled hard filter row for `userId` directly (bypassing `filter.service.ts#updateMyFilters`, which is another agent's file this build only calls, never edits — but a raw insert is equally valid per `hard_filters`' schema and lets tests set up fixtures without going through the full Zod-validated service call). `excludeIfUnset` defaults to `true` (fail-closed), matching a deal-breaker-derived filter row per this build's task brief. */
export async function setHardFilter(
  pool: pg.Pool,
  userId: string,
  filterKey: string,
  operator: 'eq' | 'neq' | 'gte' | 'lte' | 'gt' | 'lt' | 'in',
  value: unknown,
  opts: { excludeIfUnset?: boolean; enabled?: boolean } = {},
): Promise<void> {
  await pool.query(
    `INSERT INTO hard_filters (user_id, filter_key, operator, value, enabled, exclude_if_unset, updated_at)
     VALUES ($1, $2, $3, $4::jsonb, $5, $6, now())
     ON CONFLICT (user_id, filter_key) DO UPDATE SET
       operator = EXCLUDED.operator, value = EXCLUDED.value, enabled = EXCLUDED.enabled,
       exclude_if_unset = EXCLUDED.exclude_if_unset, updated_at = now()`,
    [userId, filterKey, operator, JSON.stringify(value), opts.enabled ?? true, opts.excludeIfUnset ?? true],
  );
}

/** Inserts a `has_children`/`wants_children`/etc self-answer for `userId` — creates the backing `questions` row too if it doesn't exist yet (test DBs run migrations only, no seed data). `selfValue` is the 1-5 scale `answers.self_value` uses (spec §8.1); most boolean-shaped filters in these tests use 1 = "no"/false, 5 = "yes"/true by convention. */
export async function setSelfAnswer(pool: pg.Pool, userId: string, slug: string, selfValue: number): Promise<void> {
  const { rows } = await pool.query<{ id: string }>(`SELECT id FROM questions WHERE slug = $1`, [slug]);
  let questionId = rows[0]?.id;
  if (!questionId) {
    const inserted = await pool.query<{ id: string }>(
      `INSERT INTO questions (slug, category, question_text, self_left_label, self_right_label, partner_left_label, partner_right_label)
       VALUES ($1, 'lifestyle', $1, 'low', 'high', 'low', 'high')
       RETURNING id`,
      [slug],
    );
    questionId = inserted.rows[0]!.id;
  }
  await pool.query(
    `INSERT INTO answers (user_id, question_id, self_value, updated_at)
     VALUES ($1, $2, $3, now())
     ON CONFLICT (user_id, question_id) DO UPDATE SET self_value = EXCLUDED.self_value, updated_at = now()`,
    [userId, questionId, selfValue],
  );
}
