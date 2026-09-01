/**
 * Unit tests for filter.service.ts's age-range suggested default ("half
 * your age plus seven" — product decision, no § reference).
 *
 * Uses its own dedicated Postgres database (`odate_units_ageDefault`, per
 * the build brief: one database per test file, `odate_units_<suite>`
 * naming). Not shared with `profileAttributes.test.ts` or any sibling
 * agent's test database.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import pg from 'pg';
import { runMigrations } from '../../src/db/migrate.js';
import { closePool, getPool } from '../../src/db/pool.js';
import { ConfigService } from '../../src/config/config.service.js';
import { FlagsService } from '../../src/config/flags.service.js';
import { ManualClock } from '../../src/lib/time.js';
import { createSilentLogger } from '../../src/lib/logger.js';
import { FakeProcessor } from '../../src/services/payments/fake.processor.js';
import { StubMediaModerationAdapter } from '../../src/services/media/stub.adapter.js';
import type { Ctx } from '../../src/lib/ctx.js';
import { suggestedAgeRange, applySuggestedAgeRangeIfUnset, getMyFilters, updateMyFilters } from '../../src/services/filter.service.js';

const BASE_URL = process.env.DATABASE_URL ?? 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';
// Lowercase: an unquoted CREATE DATABASE identifier is case-folded by
// Postgres, but the `dbname` connection parameter used to reconnect below
// is taken literally — a mixed-case name here would create one database
// and then fail to find it on reconnect.
const TEST_DB_NAME = 'odate_units_agedefault';

function withDbName(url: string, dbName: string): string {
  const u = new URL(url);
  u.pathname = `/${dbName}`;
  return u.toString();
}

let adminPool: pg.Pool;
let pool: pg.Pool;
let ctx: Ctx;

before(async () => {
  adminPool = new pg.Pool({ connectionString: BASE_URL });
  await adminPool.query(`DROP DATABASE IF EXISTS ${TEST_DB_NAME}`);
  await adminPool.query(`CREATE DATABASE ${TEST_DB_NAME}`);

  process.env.DATABASE_URL = withDbName(BASE_URL, TEST_DB_NAME);
  await runMigrations();
  pool = getPool();

  const logger = createSilentLogger();
  const clock = new ManualClock(new Date('2026-06-01T12:00:00Z'));
  ctx = {
    db: pool,
    clock,
    config: new ConfigService(pool, clock, logger),
    flags: new FlagsService(pool, logger),
    logger,
    actor: { type: 'system', job: 'test' },
    payments: new FakeProcessor(),
    media: new StubMediaModerationAdapter(),
  };
});

after(async () => {
  await closePool();
  await adminPool.query(`DROP DATABASE IF EXISTS ${TEST_DB_NAME}`);
  await adminPool.end();
});

function actorFor(userId: string): Ctx {
  return { ...ctx, actor: { type: 'user', userId, trustLevel: 'standard' } };
}

let seq = 0;
async function makeUser(age: number): Promise<string> {
  seq++;
  const email = `agedefault-user-${seq}@test.local`;
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO users (email, password_hash, birthdate, status) VALUES ($1, 'x', '1995-01-01', 'active') RETURNING id`,
    [email],
  );
  const userId = rows[0]!.id;
  await pool.query(
    `INSERT INTO profiles (user_id, display_name, latitude, longitude, location_fuzzed, age, gender, seeking, relationship_intention, profile_completeness)
     VALUES ($1, $2, 10, 10, true, $3, 'woman', 'man', 'long_term', 50)`,
    [userId, `User${seq}`, age],
  );
  return userId;
}

// =====================================================================
// Pure arithmetic.
// =====================================================================

test('suggestedAgeRange: half-your-age-plus-seven arithmetic at several ages', () => {
  // min = floor(age/2) + 7, max = (age-7) * 2
  assert.deepEqual(suggestedAgeRange(20), { min: 17, max: 26 });
  assert.deepEqual(suggestedAgeRange(24), { min: 19, max: 34 });
  assert.deepEqual(suggestedAgeRange(30), { min: 22, max: 46 });
  assert.deepEqual(suggestedAgeRange(40), { min: 27, max: 66 });
  assert.deepEqual(suggestedAgeRange(50), { min: 32, max: 86 });
  assert.deepEqual(suggestedAgeRange(65), { min: 39, max: 116 });
  // floor() matters for odd ages.
  assert.deepEqual(suggestedAgeRange(31), { min: 22, max: 48 });
  assert.deepEqual(suggestedAgeRange(33), { min: 23, max: 52 });
});

// =====================================================================
// applySuggestedAgeRangeIfUnset: applies once, never reapplied.
// =====================================================================

test('applySuggestedAgeRangeIfUnset: writes the suggested age_min/age_max when the user has never set either', async () => {
  const userId = await makeUser(30);
  const userCtx = actorFor(userId);

  const before = await getMyFilters(userCtx);
  assert.equal(before.length, 0, 'sanity: no filters yet');

  const applied = await applySuggestedAgeRangeIfUnset(userCtx);
  assert.deepEqual(applied, { min: 22, max: 46 });

  const after = await getMyFilters(userCtx);
  const ageMin = after.find((f) => f.filterKey === 'age_min');
  const ageMax = after.find((f) => f.filterKey === 'age_max');
  assert.ok(ageMin && ageMax, 'both age_min and age_max were written');
  assert.equal(ageMin!.operator, 'gte');
  assert.equal(ageMin!.value, 22);
  assert.equal(ageMax!.operator, 'lte');
  assert.equal(ageMax!.value, 46);
  assert.equal(ageMin!.enabled, true);
});

test('applySuggestedAgeRangeIfUnset: is a no-op once the user has an age_min/age_max filter (their own value, or a prior suggestion) — never silently reapplied', async () => {
  const userId = await makeUser(30);
  const userCtx = actorFor(userId);

  // The user sets their OWN age range, deliberately different from what
  // the formula would suggest for age 30 (22-46).
  await updateMyFilters(userCtx, [
    { filterKey: 'age_min', operator: 'gte', value: 25, enabled: true },
    { filterKey: 'age_max', operator: 'lte', value: 35, enabled: true },
  ]);

  const applied = await applySuggestedAgeRangeIfUnset(userCtx);
  assert.equal(applied, null, 'no-op: the user already has age filters set');

  const after = await getMyFilters(userCtx);
  const ageMin = after.find((f) => f.filterKey === 'age_min')!;
  const ageMax = after.find((f) => f.filterKey === 'age_max')!;
  assert.equal(ageMin.value, 25, "the user's own value must survive, not be overwritten by the suggestion");
  assert.equal(ageMax.value, 35);

  // Calling it again (idempotent no-op) still does not touch anything.
  const appliedAgain = await applySuggestedAgeRangeIfUnset(userCtx);
  assert.equal(appliedAgain, null);
  const afterAgain = await getMyFilters(userCtx);
  assert.equal(afterAgain.find((f) => f.filterKey === 'age_min')!.value, 25);
});

test('applySuggestedAgeRangeIfUnset: also a no-op after the user edits away ONLY one of the two keys (either key existing counts as "set")', async () => {
  const userId = await makeUser(40);
  const userCtx = actorFor(userId);

  await updateMyFilters(userCtx, [{ filterKey: 'age_max', operator: 'lte', value: 99, enabled: true }]);

  const applied = await applySuggestedAgeRangeIfUnset(userCtx);
  assert.equal(applied, null);

  const after = await getMyFilters(userCtx);
  assert.equal(after.find((f) => f.filterKey === 'age_min'), undefined, 'age_min must still not exist — it was never silently added');
  assert.equal(after.find((f) => f.filterKey === 'age_max')!.value, 99);
});

test('applySuggestedAgeRangeIfUnset: a prior application blocks a later one from a different (hypothetical re-derived) suggestion', async () => {
  const userId = await makeUser(20);
  const userCtx = actorFor(userId);

  const first = await applySuggestedAgeRangeIfUnset(userCtx);
  assert.deepEqual(first, { min: 17, max: 26 });

  // Even though nothing here changes the user's age, a second call must
  // still be a no-op purely because age_min/age_max now exist.
  const second = await applySuggestedAgeRangeIfUnset(userCtx);
  assert.equal(second, null);
});

test('applySuggestedAgeRangeIfUnset: no-op (null) for a user with no profile/age to suggest from', async () => {
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO users (email, password_hash, birthdate, status) VALUES ($1, 'x', '1995-01-01', 'active') RETURNING id`,
    [`agedefault-noprofile-${++seq}@test.local`],
  );
  const userId = rows[0]!.id;
  const userCtx = actorFor(userId);

  const applied = await applySuggestedAgeRangeIfUnset(userCtx);
  assert.equal(applied, null);
  const after = await getMyFilters(userCtx);
  assert.equal(after.length, 0);
});
