/**
 * Shared test scaffolding for `tests/http/*.test.ts`.
 *
 * Mirrors the pattern every other agent's `tests/unit/testCtx*.ts` already
 * uses (fresh per-suite database, migrated, config/flags seeded) but boots
 * a real `FastifyInstance` via `buildServer` instead of a bare `Ctx`, so
 * tests drive the API exactly as documented in the task brief: via
 * `app.inject(...)`, never a real network socket.
 *
 * Per the task's "use your own Postgres databases (`odate_http_<suite>`)"
 * instruction, every db name is namespaced under `odate_http_*`, and each
 * test FILE passes its own unique `suite` (node runs each test file in its
 * own process, so two files never race DROP/CREATE DATABASE against the
 * same name).
 */
import pg from 'pg';
import { randomUUID } from 'node:crypto';
import type { FastifyInstance } from 'fastify';
import { runMigrations } from '../../src/db/migrate.js';
import { closePool, getPool } from '../../src/db/pool.js';
import { ConfigService } from '../../src/config/config.service.js';
import { FlagsService } from '../../src/config/flags.service.js';
import { ManualClock } from '../../src/lib/time.js';
import { createSilentLogger } from '../../src/lib/logger.js';
import { FakeProcessor } from '../../src/services/payments/fake.processor.js';
import { StubMediaModerationAdapter } from '../../src/services/media/stub.adapter.js';
import { buildServer } from '../../src/http/server.js';
import type { AppDeps } from '../../src/http/deps.js';

const ADMIN_BASE_URL = process.env.DATABASE_URL ?? 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';
/** Per-process random suffix (see `tests/unit/testCtx.ts`'s longer note) — closes the cross-run database-name-collision race (test-audit.md's database-race item): this suite is routinely run by more than one agent at once against the same shared dev Postgres cluster, and a bare `odate_http_<suite>` name is only unique within a single run. */
const RUN_SUFFIX = randomUUID().replace(/-/g, '').slice(0, 8);

function withDbName(url: string, dbName: string): string {
  const u = new URL(url);
  u.pathname = `/${dbName}`;
  return u.toString();
}

export interface TestApp {
  dbName: string;
  pool: pg.Pool;
  clock: ManualClock;
  deps: AppDeps;
  app: FastifyInstance;
}

/** Creates a fresh, migrated, config/flag-seeded database named `odate_http_<suite>` and boots a Fastify instance bound to it. Call once from a suite's `before`. */
export async function setupTestApp(suite: string): Promise<TestApp> {
  const dbName = `odate_http_${suite}_${RUN_SUFFIX}`;
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

  const deps: AppDeps = { pool, clock, config, flags, logger, payments: new FakeProcessor(), media: new StubMediaModerationAdapter() };
  const app = buildServer(deps);
  await app.ready();

  return { dbName, pool, clock, deps, app };
}

/** Call once from a suite's `after`. */
export async function teardownTestApp(t: TestApp): Promise<void> {
  await t.app.close();
  await closePool();
  const adminPool = new pg.Pool({ connectionString: ADMIN_BASE_URL });
  await adminPool.query(`DROP DATABASE IF EXISTS ${t.dbName}`);
  await adminPool.end();
}

let emailCounter = 0;
export function uniqueEmail(prefix = 'http'): string {
  emailCounter += 1;
  return `${prefix}${emailCounter}.${Date.now()}@example.test`;
}

export interface RegisteredUser {
  userId: string;
  email: string;
  accessToken: string;
  refreshToken: string;
}

/** Registers a fresh account via the real `/auth/register` route and returns its tokens — the realistic path every other helper builds on. */
export async function registerUser(t: TestApp, overrides?: { email?: string; city?: string }): Promise<RegisteredUser> {
  const email = overrides?.email ?? uniqueEmail();
  const res = await t.app.inject({
    method: 'POST',
    url: '/auth/register',
    payload: {
      email,
      password: 'Passw0rd!12345',
      birthdate: '1995-06-15',
      termsAccepted: true,
      city: overrides?.city ?? 'Springfield',
    },
  });
  if (res.statusCode !== 201) {
    throw new Error(`registerUser failed: ${res.statusCode} ${res.body}`);
  }
  const body = JSON.parse(res.body) as { user: { id: string }; tokens: { accessToken: string; refreshToken: string } };
  return { userId: body.user.id, email, accessToken: body.tokens.accessToken, refreshToken: body.tokens.refreshToken };
}

export function authHeader(token: string): { authorization: string } {
  return { authorization: `Bearer ${token}` };
}

/** Clears the app's shared §19.2 rate-limit counters — call between test cases in any suite that registers/logs-in more accounts than the per-IP limits allow (the limiter's own behavior is exercised by `tests/http/rateLimit.test.ts`, not by every other suite incidentally hitting it). */
export function resetRateLimiter(t: TestApp): void {
  t.app.rateLimiter.reset();
}

/** Grants `userId` the admin role (direct DB write — there is no self-service "become admin" HTTP route, by design; §4.3 admins are provisioned operationally). */
export async function makeAdmin(t: TestApp, userId: string): Promise<void> {
  await t.pool.query(`INSERT INTO admin_users (user_id, active) VALUES ($1, true) ON CONFLICT DO NOTHING`, [userId]);
}

/** Creates a venue and grants `userId` venue-staff access to it. Returns the venue id. */
export async function makeVenueStaff(t: TestApp, userId: string, venueId?: string): Promise<string> {
  const vId = venueId ?? (await createVenue(t));
  await t.pool.query(
    `INSERT INTO venue_staff (user_id, venue_id, active) VALUES ($1, $2, true) ON CONFLICT (user_id, venue_id) DO UPDATE SET active = true`,
    [userId, vId],
  );
  return vId;
}

export async function createVenue(t: TestApp, overrides?: { active?: boolean; name?: string }): Promise<string> {
  const { rows } = await t.pool.query<{ id: string }>(
    `INSERT INTO venues (name, address, latitude, longitude, category, active, margin_percent, time_slot_config, redemption_method)
     VALUES ($1, '1 Test St', 39.78, -89.65, 'coffee', $2, 15,
       '{"slots":[{"dayOfWeek":0,"startMinute":0,"endMinute":1439},{"dayOfWeek":1,"startMinute":0,"endMinute":1439},{"dayOfWeek":2,"startMinute":0,"endMinute":1439},{"dayOfWeek":3,"startMinute":0,"endMinute":1439},{"dayOfWeek":4,"startMinute":0,"endMinute":1439},{"dayOfWeek":5,"startMinute":0,"endMinute":1439},{"dayOfWeek":6,"startMinute":0,"endMinute":1439}]}'::jsonb,
       'qr_scan')
     RETURNING id`,
    [overrides?.name ?? 'Test Venue', overrides?.active ?? true],
  );
  return rows[0]!.id;
}

/** Inserts a question directly (bypassing admin routes) for tests that need answers on the books quickly. */
export async function insertQuestion(
  t: TestApp,
  overrides: { slug: string; weight?: number; sensitive?: boolean },
): Promise<string> {
  const { rows } = await t.pool.query<{ id: string }>(
    `INSERT INTO questions (slug, category, question_text, self_left_label, self_right_label, partner_left_label, partner_right_label, weight, polarity, sensitive, active)
     VALUES ($1, 'test', $1, 'left', 'right', 'left', 'right', $2, 'standard', $3, true)
     RETURNING id`,
    [overrides.slug, overrides.weight ?? 1, overrides.sensitive ?? false],
  );
  return rows[0]!.id;
}

/** Fills in a minimally-complete profile + a verified payment method + enough answers/photos for `userId` to be discoverable and able to propose a paid date — used by the end-to-end happy-path test so it doesn't have to re-derive discovery's completeness/photo gates inline. */
export async function completeOnboarding(
  t: TestApp,
  token: string,
  opts: { displayName: string; gender: string; seeking: string },
): Promise<void> {
  const profileRes = await t.app.inject({
    method: 'PATCH',
    url: '/me/profile',
    headers: authHeader(token),
    payload: {
      displayName: opts.displayName,
      bio: 'A person who enjoys hiking, coffee, and good conversation on dates.',
      city: 'Springfield',
      latitude: 39.78,
      longitude: -89.65,
      age: 28,
      gender: opts.gender,
      seeking: opts.seeking,
      relationshipIntention: 'long_term',
    },
  });
  if (profileRes.statusCode !== 200) throw new Error(`profile update failed: ${profileRes.statusCode} ${profileRes.body}`);

  for (let i = 0; i < 3; i++) {
    const res = await t.app.inject({
      method: 'POST',
      url: '/me/photos',
      headers: authHeader(token),
      payload: { imageUrl: `https://example.test/photo-${opts.displayName}-${i}.jpg` },
    });
    if (res.statusCode !== 201) throw new Error(`photo upload failed: ${res.statusCode} ${res.body}`);
  }

  const questionsRes = await t.app.inject({ method: 'GET', url: '/questions', headers: authHeader(token) });
  const questions = JSON.parse(questionsRes.body) as Array<{ id: string }>;
  const answers = questions.slice(0, Math.max(5, questions.length)).map((q) => ({ questionId: q.id, selfValue: 3, partnerValue: 3 }));
  if (answers.length > 0) {
    const answersRes = await t.app.inject({ method: 'PUT', url: '/me/answers', headers: authHeader(token), payload: answers });
    if (answersRes.statusCode !== 200) throw new Error(`answers failed: ${answersRes.statusCode} ${answersRes.body}`);
  }

  const pmRes = await t.app.inject({
    method: 'POST',
    url: '/payment-methods',
    headers: authHeader(token),
    payload: { processorToken: `tok_${opts.displayName}`, brand: 'visa', last4: '4242', makeDefault: true },
  });
  if (pmRes.statusCode !== 201) throw new Error(`payment method failed: ${pmRes.statusCode} ${pmRes.body}`);
}
