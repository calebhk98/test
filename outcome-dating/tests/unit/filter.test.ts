/**
 * Unit tests for filter.service.ts.
 *
 * `evaluateFilter`/`haversineKm` are pure (no I/O). Everything else here
 * (`passesMutualFilters`, the reality-dashboard counts) needs real
 * `hard_filters`/`profiles`/`answers` rows, so it runs against a dedicated
 * Postgres database (`outcome_dating_test_filter`), same pattern as
 * `tests/foundation.test.ts`.
 *
 * The headline invariant this file exists to prove (spec §9.1 / the task
 * brief's "hard filters beat a perfect compatibility score"): a candidate
 * who fails a hard filter must never pass `passesMutualFilters`, no matter
 * how compatible they would otherwise be — see the last test below.
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
import {
  evaluateFilter,
  haversineKm,
  passesMutualFilters,
  countUsersMatchingMyFilters,
  countUsersWhoseFiltersIMatch,
  getMyFilters,
  updateMyFilters,
} from '../../src/services/filter.service.js';
import { computePairScore } from '../../src/services/compatibility.service.js';

// =====================================================================
// Pure evaluateFilter tests
// =====================================================================

test('evaluateFilter: gte/lte/gt/lt numeric operators', () => {
  assert.equal(evaluateFilter({ operator: 'gte', value: 21 }, 25), true);
  assert.equal(evaluateFilter({ operator: 'gte', value: 21 }, 21), true);
  assert.equal(evaluateFilter({ operator: 'gte', value: 21 }, 20), false);

  assert.equal(evaluateFilter({ operator: 'lte', value: 35 }, 35), true);
  assert.equal(evaluateFilter({ operator: 'lte', value: 35 }, 36), false);

  assert.equal(evaluateFilter({ operator: 'gt', value: 21 }, 22), true);
  assert.equal(evaluateFilter({ operator: 'gt', value: 21 }, 21), false);

  assert.equal(evaluateFilter({ operator: 'lt', value: 5 }, 4), true);
  assert.equal(evaluateFilter({ operator: 'lt', value: 5 }, 5), false);
});

test('evaluateFilter: eq/neq operators', () => {
  assert.equal(evaluateFilter({ operator: 'eq', value: 'woman' }, 'woman'), true);
  assert.equal(evaluateFilter({ operator: 'eq', value: 'woman' }, 'man'), false);
  assert.equal(evaluateFilter({ operator: 'neq', value: 'woman' }, 'man'), true);
  assert.equal(evaluateFilter({ operator: 'neq', value: 'woman' }, 'woman'), false);
});

test('evaluateFilter: in operator', () => {
  assert.equal(evaluateFilter({ operator: 'in', value: ['woman', 'nonbinary'] }, 'woman'), true);
  assert.equal(evaluateFilter({ operator: 'in', value: ['woman', 'nonbinary'] }, 'man'), false);
  assert.equal(evaluateFilter({ operator: 'in', value: 'not-an-array' }, 'woman'), false);
});

// UPDATED by the units/physical-attributes build (product-owner
// correction — see filter.service.ts's file-level "MISSING/UNRESOLVED
// VALUES" note): an unresolved candidate value no longer fails closed
// UNCONDITIONALLY. `evaluateFilter` gained a third `excludeIfUnset`
// parameter; passing it explicitly still gives EXACTLY the original
// fail-closed behavior this test used to assert unconditionally (see the
// first two assertions below, unchanged in spirit), but the DEFAULT when
// it is omitted flipped from "always fails closed" to "never excludes on
// an unresolved value" — a brand-new account that hasn't filled a field
// in yet must not silently vanish from every other user's results. The
// original two-argument assertions are kept, retitled and re-pointed at
// the new default, rather than deleted, so this file still proves both
// halves of the toggle in one place.
test('evaluateFilter: excludeIfUnset:true still fails closed on an unresolved (undefined) candidate value', () => {
  assert.equal(evaluateFilter({ operator: 'gte', value: 0 }, undefined, true), false);
  assert.equal(evaluateFilter({ operator: 'in', value: ['a', 'b'] }, undefined, true), false);
});

test('evaluateFilter: the default (excludeIfUnset omitted) no longer fails closed on an unresolved value — it passes', () => {
  assert.equal(evaluateFilter({ operator: 'gte', value: 0 }, undefined), true);
  assert.equal(evaluateFilter({ operator: 'in', value: ['a', 'b'] }, undefined), true);
  // Explicit false is identical to the default, spelled out.
  assert.equal(evaluateFilter({ operator: 'gte', value: 0 }, undefined, false), true);
});

test('evaluateFilter: excludeIfUnset never affects a RESOLVED value — only undefined is special-cased', () => {
  assert.equal(evaluateFilter({ operator: 'gte', value: 21 }, 25, true), true);
  assert.equal(evaluateFilter({ operator: 'gte', value: 21 }, 15, true), false);
  assert.equal(evaluateFilter({ operator: 'eq', value: null }, null, true), true, 'a resolved null is compared normally, not treated as unresolved');
});

test('haversineKm: symmetric and zero for identical points', () => {
  assert.equal(haversineKm(39.78, -89.65, 39.78, -89.65), 0);
  const ab = haversineKm(39.78, -89.65, 40.71, -74.0);
  const ba = haversineKm(40.71, -74.0, 39.78, -89.65);
  assert.ok(Math.abs(ab - ba) < 1e-9);
  assert.ok(ab > 1000 && ab < 2000, `Springfield IL to NYC should be roughly 1000-2000km, got ${ab}`);
});

// =====================================================================
// DB-backed tests
// =====================================================================

const BASE_URL = process.env.DATABASE_URL ?? 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';
const TEST_DB_NAME = 'outcome_dating_test_filter';

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
async function makeUser(opts: {
  age: number;
  gender: string;
  relationshipIntention?: string;
  latitude: number;
  longitude: number;
}): Promise<string> {
  seq++;
  const email = `filter-user-${seq}@test.local`;
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO users (email, password_hash, birthdate, status) VALUES ($1, 'x', '1995-01-01', 'active') RETURNING id`,
    [email],
  );
  const userId = rows[0]!.id;
  await pool.query(
    `INSERT INTO profiles (user_id, display_name, city, latitude, longitude, location_fuzzed, age, gender, seeking, relationship_intention, profile_completeness)
     VALUES ($1, $2, 'Testville', $3, $4, true, $5, $6, 'any', $7, 80)`,
    [userId, `User${seq}`, opts.latitude, opts.longitude, opts.age, opts.gender, opts.relationshipIntention ?? 'long_term'],
  );
  return userId;
}

async function addFilter(userId: string, filterKey: string, operator: string, value: unknown): Promise<void> {
  await pool.query(
    `INSERT INTO hard_filters (user_id, filter_key, operator, value, enabled) VALUES ($1, $2, $3, $4::jsonb, true)`,
    [userId, filterKey, operator, JSON.stringify(value)],
  );
}

test('getMyFilters / updateMyFilters: unlimited slots, upserts, and round-trips', async () => {
  const userId = await makeUser({ age: 30, gender: 'woman', latitude: 39.78, longitude: -89.65 });
  const userCtx = actorFor(userId);

  const initial = await getMyFilters(userCtx);
  assert.equal(initial.length, 0);

  const many = Array.from({ length: 12 }, (_, i) => ({
    filterKey: `custom_key_${i}`,
    operator: 'eq' as const,
    value: i,
    enabled: true,
  }));
  const updated = await updateMyFilters(userCtx, many);
  assert.equal(updated.length, 12, 'updateMyFilters must not cap the number of filter slots (§9.2)');

  // Upsert semantics: re-submitting the same key changes it in place, not duplicates it.
  await updateMyFilters(userCtx, [{ filterKey: 'custom_key_0', operator: 'neq', value: 99, enabled: false }]);
  const after = await getMyFilters(userCtx);
  assert.equal(after.length, 12);
  const changed = after.find((f) => f.filterKey === 'custom_key_0')!;
  assert.equal(changed.operator, 'neq');
  assert.equal(changed.enabled, false);
});

test('passesMutualFilters: age/distance/gender filters gate correctly in both directions', async () => {
  const viewer = await makeUser({ age: 30, gender: 'woman', latitude: 39.78, longitude: -89.65 });
  const inRangeClose = await makeUser({ age: 32, gender: 'man', latitude: 39.79, longitude: -89.64 });
  const tooFarAway = await makeUser({ age: 32, gender: 'man', latitude: 40.71, longitude: -74.0 });
  const tooOld = await makeUser({ age: 60, gender: 'man', latitude: 39.79, longitude: -89.64 });

  await addFilter(viewer, 'age_min', 'gte', 25);
  await addFilter(viewer, 'age_max', 'lte', 40);
  await addFilter(viewer, 'distance_km', 'lte', 50);

  assert.equal(await passesMutualFilters(ctx, viewer, inRangeClose), true);
  assert.equal(await passesMutualFilters(ctx, viewer, tooFarAway), false, 'candidate outside distance_km must fail');
  assert.equal(await passesMutualFilters(ctx, viewer, tooOld), false, 'candidate outside age_max must fail');
});

test('passesMutualFilters: mutual — candidate\'s own filters can reject the viewer even when the viewer\'s filters would accept the candidate', async () => {
  const viewer = await makeUser({ age: 45, gender: 'woman', latitude: 39.78, longitude: -89.65 });
  const picky = await makeUser({ age: 30, gender: 'man', latitude: 39.79, longitude: -89.64 });

  // viewer has no filters at all (trivially passes anyone).
  // picky only wants partners 25-35.
  await addFilter(picky, 'age_min', 'gte', 25);
  await addFilter(picky, 'age_max', 'lte', 35);

  assert.equal(
    await passesMutualFilters(ctx, viewer, picky),
    false,
    'viewer (age 45) fails candidate\'s age_max=35 filter, so the mutual check must fail even though the candidate passes the viewer\'s (empty) filters',
  );
});

test('reality dashboard counts (X/Y) are genuinely different queries, not the same number reused', async () => {
  // A distinctive, narrow age band (91-95) that no other test in this file
  // uses, so counts are computed against a known, order-independent set
  // regardless of what earlier tests already inserted into the shared
  // per-file test database.
  const userId = await makeUser({ age: 93, gender: 'woman', latitude: 10, longitude: 10 });
  const matching: string[] = [];
  for (let i = 0; i < 3; i++) {
    matching.push(await makeUser({ age: 91 + i, gender: 'man', latitude: 10, longitude: 10 }));
  }
  const nonMatching: string[] = [];
  for (let i = 0; i < 2; i++) {
    nonMatching.push(await makeUser({ age: 20, gender: 'man', latitude: 10, longitude: 10 }));
  }
  await addFilter(userId, 'age_min', 'gte', 91);
  await addFilter(userId, 'age_max', 'lte', 95);

  const x = await countUsersMatchingMyFilters(ctx, userId);
  const y = await countUsersWhoseFiltersIMatch(ctx, userId);

  // X is exactly this test's 3 in-band users, PLUS any earlier test's users
  // who happen to also fall in 91-95 (there are none — no other test in
  // this file uses that age band) — assert against a live count rather
  // than a hardcoded total, so the test is robust to run order/other tests'
  // fixtures while still proving X counts a real, narrow, filter-gated set.
  const { rows: expectedXRows } = await pool.query<{ count: string }>(
    `SELECT count(*)::text AS count FROM profiles WHERE age BETWEEN 91 AND 95 AND user_id <> $1`,
    [userId],
  );
  assert.equal(x, Number(expectedXRows[0]!.count), 'X = people who match my filters');
  assert.ok(matching.length === 3 && Number(expectedXRows[0]!.count) === 3, 'sanity: exactly the 3 in-band users created here');

  // No candidate has any filters of their own, so every other active user
  // in the whole database (not just this test's 5) trivially passes an
  // empty filter set for Y — genuinely a different query/answer than X,
  // and strictly larger since it also includes the 2 out-of-band users.
  assert.ok(y > x, 'Y = people whose (empty) filters I match must include the out-of-band users too, so Y > X here');
  assert.notEqual(x, y);
  void nonMatching;
});

test('INVARIANT: a hard filter rejection beats a perfect compatibility score', async () => {
  const viewer = await makeUser({ age: 30, gender: 'woman', latitude: 39.78, longitude: -89.65 });
  const candidate = await makeUser({ age: 50, gender: 'man', latitude: 39.78, longitude: -89.65 }); // outside viewer's age filter

  // Give both users identical answers on 3 questions -> a perfect (1.0) compatibility score.
  const questionIds: string[] = [];
  for (let i = 0; i < 3; i++) {
    const { rows } = await pool.query<{ id: string }>(
      `INSERT INTO questions (slug, category, question_text, self_left_label, self_right_label, partner_left_label, partner_right_label, weight, polarity, sensitive, active)
       VALUES ($1, 'test', $1, 'l', 'r', 'l', 'r', 1, 'standard', false, true) RETURNING id`,
      [`invariant-q${i}-${seq}`],
    );
    questionIds.push(rows[0]!.id);
    for (const userId of [viewer, candidate]) {
      await pool.query('INSERT INTO answers (user_id, question_id, self_value, partner_value) VALUES ($1, $2, 5, 5)', [
        userId,
        questionIds[questionIds.length - 1],
      ]);
    }
  }

  // Confirm the compatibility score really is perfect (1.0) — the filter
  // rejection below must win despite this, not because compatibility also
  // happens to be low.
  const { rows: qRows } = await pool.query(
    'SELECT id, slug, category, question_text, self_left_label, self_right_label, partner_left_label, partner_right_label, weight, polarity, sensitive, active, created_at, updated_at FROM questions WHERE id = ANY($1::uuid[])',
    [questionIds],
  );
  const { rows: aRows } = await pool.query('SELECT * FROM answers WHERE user_id = $1', [viewer]);
  const { rows: bRows } = await pool.query('SELECT * FROM answers WHERE user_id = $1', [candidate]);
  const toAnswer = (r: any) => ({ userId: r.user_id, questionId: r.question_id, selfValue: r.self_value, partnerValue: r.partner_value, updatedAt: r.updated_at });
  const toQuestion = (r: any) => ({
    id: r.id,
    slug: r.slug,
    category: r.category,
    questionText: r.question_text,
    selfLeftLabel: r.self_left_label,
    selfRightLabel: r.self_right_label,
    partnerLeftLabel: r.partner_left_label,
    partnerRightLabel: r.partner_right_label,
    weight: r.weight,
    polarity: r.polarity,
    sensitive: r.sensitive,
    active: r.active,
    createdAt: r.created_at,
    updatedAt: r.updated_at,
  });
  const breakdown = computePairScore(aRows.map(toAnswer), bRows.map(toAnswer), qRows.map(toQuestion), 1);
  assert.ok(Math.abs(breakdown.score - 1) < 1e-9, 'sanity check: compatibility really is perfect (1.0)');

  await addFilter(viewer, 'age_max', 'lte', 40);

  const passes = await passesMutualFilters(ctx, viewer, candidate);
  assert.equal(passes, false, 'a perfect compatibility score must NOT override a failed hard filter (§9.1)');
});
