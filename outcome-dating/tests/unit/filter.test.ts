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
  boundingBoxForRadius,
  resolveGeoSearchContext,
  evaluateFilterPairsBatch,
  passesMutualFiltersForCandidates,
  summarizeSampledCount,
  DEFAULT_DISCOVERY_RADIUS_KM,
  type NearbyActiveUsers,
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
// boundingBoxForRadius: pure geo math (SCALE FIX). The one invariant that
// matters most: the box must NEVER be narrower than the true radius —
// every point within `radiusKm` of the center must fall inside the box
// (checked here against the exact `haversineKm`), even though the box is
// allowed to be (and, away from the equator, always is) a bit wider than
// the circle it contains.
// =====================================================================

function pointAtBearing(lat: number, lon: number, distanceKm: number, bearingDeg: number): { lat: number; lon: number } {
  const R = 6371;
  const b = (bearingDeg * Math.PI) / 180;
  const lat1 = (lat * Math.PI) / 180;
  const lon1 = (lon * Math.PI) / 180;
  const d = distanceKm / R;
  const lat2 = Math.asin(Math.sin(lat1) * Math.cos(d) + Math.cos(lat1) * Math.sin(d) * Math.cos(b));
  const lon2 = lon1 + Math.atan2(Math.sin(b) * Math.sin(d) * Math.cos(lat1), Math.cos(d) - Math.sin(lat1) * Math.sin(lat2));
  return { lat: (lat2 * 180) / Math.PI, lon: (((lon2 * 180) / Math.PI + 540) % 360) - 180 };
}

function insideBox(box: ReturnType<typeof boundingBoxForRadius>, lat: number, lon: number): boolean {
  if (lat < box.latMin || lat > box.latMax) return false;
  return (lon >= box.lon1Min && lon <= box.lon1Max) || (lon >= box.lon2Min && lon <= box.lon2Max);
}

test('boundingBoxForRadius: every point within radius of the center falls inside the box (equator)', () => {
  const box = boundingBoxForRadius(0, 0, 100);
  for (const bearing of [0, 45, 90, 135, 180, 225, 270, 315]) {
    const p = pointAtBearing(0, 0, 95, bearing); // just inside the radius
    assert.ok(insideBox(box, p.lat, p.lon), `bearing ${bearing} at 95km should be inside the box`);
  }
});

test('boundingBoxForRadius: widens longitude span at high latitude so it still never under-covers', () => {
  const box = boundingBoxForRadius(60, 10, 100);
  for (const bearing of [0, 45, 90, 135, 180, 225, 270, 315]) {
    const p = pointAtBearing(60, 10, 95, bearing);
    assert.ok(insideBox(box, p.lat, p.lon), `bearing ${bearing} at 95km (lat 60) should be inside the box`);
  }
  // Sanity: the longitude span at lat 60 must be wider (in degrees) than the same radius would need at the equator.
  const equatorBox = boundingBoxForRadius(0, 10, 100);
  assert.ok(box.lon1Max - box.lon1Min > equatorBox.lon1Max - equatorBox.lon1Min);
});

test('boundingBoxForRadius: a box that overruns a pole covers every longitude', () => {
  const box = boundingBoxForRadius(89.5, 0, 200);
  assert.equal(box.lon1Min, -180);
  assert.equal(box.lon1Max, 180);
  assert.ok(box.latMax <= 90 && box.latMin >= -90, 'clamped to valid latitude range');
});

test('boundingBoxForRadius: a box crossing the antimeridian is expressed as two OR-ed ranges, not an inverted one', () => {
  const box = boundingBoxForRadius(10, 179.5, 100);
  assert.ok(box.lon1Min <= 180 && box.lon1Max <= 180, 'first range stays within [-180, 180]');
  assert.ok(box.lon2Min >= -180 && box.lon2Max >= -180, 'second range stays within [-180, 180]');
  // A point just past +180 (i.e. -179.9) must be covered by wrapping into the second range.
  assert.ok(insideBox(box, 10, -179.9), 'a point just across the antimeridian must still be inside the (wrapped) box');
});

test('boundingBoxForRadius: a huge radius collapses to the full box rather than an inverted/empty range', () => {
  const box = boundingBoxForRadius(20, 20, 50_000);
  assert.equal(box.lon1Min, -180);
  assert.equal(box.lon1Max, 180);
});

// =====================================================================
// summarizeSampledCount: the reality-dashboard "honesty under truncation"
// estimator (see filter.service.ts's block comment above
// `DASHBOARD_SCAN_CAP`). Pure math plus a logger call — no DB needed.
// =====================================================================

function fakeCtxWithLogger(): { ctx: Ctx; warnings: string[] } {
  const warnings: string[] = [];
  const logger = {
    debug() {},
    info() {},
    warn(msg: string) {
      warnings.push(msg);
    },
    error() {},
    child() {
      return this as any;
    },
  };
  return { ctx: { ...ctx, logger: logger as any }, warnings };
}

test('summarizeSampledCount: below the cap, returns the exact sample count and never warns', () => {
  const { ctx: fakeCtx, warnings } = fakeCtxWithLogger();
  const nearby: NearbyActiveUsers = { ids: Array(120).fill('x'), truncated: false, totalActiveInRadius: 120 };
  const result = summarizeSampledCount(fakeCtx, 'test', 42, nearby);
  assert.equal(result, 42, 'not truncated -> exact count, unchanged');
  assert.equal(warnings.length, 0, 'must not warn when the count is exact');
});

test('summarizeSampledCount: truncated, scales the sampled match rate up to the true population, and warns', () => {
  const { ctx: fakeCtx, warnings } = fakeCtxWithLogger();
  // 250 of the 1000 sampled candidates matched (25%); the true in-radius
  // population is 20,000 -> honest estimate is 25% of 20,000 = 5,000.
  const nearby: NearbyActiveUsers = { ids: Array(1000).fill('x'), truncated: true, totalActiveInRadius: 20_000 };
  const result = summarizeSampledCount(fakeCtx, 'test', 250, nearby);
  assert.equal(result, 5000);
  assert.equal(warnings.length, 1, 'truncation must be observable server-side (never silently wrong)');
  assert.match(warnings[0]!, /estimate/i);
});

test('summarizeSampledCount: an all-zero sample never divides by zero', () => {
  const { ctx: fakeCtx } = fakeCtxWithLogger();
  const nearby: NearbyActiveUsers = { ids: [], truncated: true, totalActiveInRadius: 10_000 };
  assert.equal(summarizeSampledCount(fakeCtx, 'test', 0, nearby), 0);
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

// =====================================================================
// SCALE FIX: batched filter evaluation must agree, pair for pair, with
// the original single-pair `passesMutualFilters` — the whole point of
// batching is that it computes the SAME answer faster, not a different
// (even if superficially similar) one.
// =====================================================================

test('passesMutualFiltersForCandidates: agrees with passesMutualFilters, one call at a time, across a mixed pool', async () => {
  const viewer = await makeUser({ age: 30, gender: 'woman', latitude: 39.78, longitude: -89.65 });

  const passesAge = await makeUser({ age: 32, gender: 'man', latitude: 39.79, longitude: -89.64 });
  const failsAge = await makeUser({ age: 60, gender: 'man', latitude: 39.79, longitude: -89.64 });
  const failsDistance = await makeUser({ age: 32, gender: 'man', latitude: 40.71, longitude: -74.0 });
  const picky = await makeUser({ age: 32, gender: 'man', latitude: 39.79, longitude: -89.64 });
  const neutral = await makeUser({ age: 32, gender: 'man', latitude: 39.79, longitude: -89.64 });

  await addFilter(viewer, 'age_min', 'gte', 25);
  await addFilter(viewer, 'age_max', 'lte', 40);
  await addFilter(viewer, 'distance_km', 'lte', 50);
  // `picky` rejects the viewer even though the viewer would accept `picky`.
  await addFilter(picky, 'age_max', 'lte', 20);

  const candidateIds = [passesAge, failsAge, failsDistance, picky, neutral];

  const expected = await Promise.all(candidateIds.map((id) => passesMutualFilters(ctx, viewer, id)));
  const batched = await passesMutualFiltersForCandidates(ctx, viewer, candidateIds);

  for (let i = 0; i < candidateIds.length; i++) {
    assert.equal(
      batched.has(candidateIds[i]!),
      expected[i],
      `candidate ${i} (${candidateIds[i]}) must agree between the batched and single-pair paths`,
    );
  }
  assert.deepEqual(
    [...batched].sort(),
    [passesAge, neutral].sort(),
    'sanity: exactly the two candidates with no disqualifying filter should pass',
  );
});

test('evaluateFilterPairsBatch: honors excludeIfUnset per owner filter, matching subjectPassesFiltersOf semantics via passesMutualFilters', async () => {
  const viewer = await makeUser({ age: 30, gender: 'woman', latitude: 10, longitude: 20 });
  const neverAnsweredSmoking = await makeUser({ age: 30, gender: 'man', latitude: 10, longitude: 20 });

  // No `smoking` answer exists for the candidate at all -> unresolved.
  await updateMyFilters(actorFor(viewer), [
    { filterKey: 'smoking', operator: 'lte', value: 2, enabled: true, excludeIfUnset: false },
  ]);
  const lenient = await passesMutualFiltersForCandidates(ctx, viewer, [neverAnsweredSmoking]);
  assert.ok(lenient.has(neverAnsweredSmoking), 'excludeIfUnset:false must still let an unresolved candidate through, batched');

  await updateMyFilters(actorFor(viewer), [
    { filterKey: 'smoking', operator: 'lte', value: 2, enabled: true, excludeIfUnset: true },
  ]);
  const strict = await passesMutualFiltersForCandidates(ctx, viewer, [neverAnsweredSmoking]);
  assert.ok(!strict.has(neverAnsweredSmoking), 'excludeIfUnset:true must exclude an unresolved candidate, batched');
});

// =====================================================================
// SCALE FIX: the reality dashboard's X/Y counts are now geographically
// bounded, like discovery — a deliberate, documented scope change (see
// filter.service.ts's block comment above `DASHBOARD_SCAN_CAP`). This
// proves the bound is real: a candidate far outside the default search
// radius, who would otherwise pass every filter, must NOT count toward X.
// =====================================================================

test('countUsersMatchingMyFilters: geographically bounded — a filter-passing candidate far outside the search radius does not count', async () => {
  // Distinctive age band (76-78) no other test in this file uses, so the
  // count is exact and order-independent — same isolation technique as
  // the "reality dashboard counts (X/Y)" test above.
  const viewer = await makeUser({ age: 40, gender: 'woman', latitude: 39.78, longitude: -89.65 }); // Springfield, IL
  const nearbyMatch = await makeUser({ age: 77, gender: 'man', latitude: 39.8, longitude: -89.6 }); // ~5km away
  const farMatch = await makeUser({ age: 77, gender: 'man', latitude: 35.6762, longitude: 139.6503 }); // Tokyo — thousands of km away

  await addFilter(viewer, 'age_min', 'gte', 76);
  await addFilter(viewer, 'age_max', 'lte', 78);

  const x = await countUsersMatchingMyFilters(ctx, viewer);
  assert.equal(
    x,
    1,
    'only the geographically nearby candidate counts toward X, even though both candidates equally pass the age filter — a deliberate, documented scope change from the pre-fix unbounded scan',
  );
  void farMatch;
});

test('resolveGeoSearchContext: uses the viewer\'s own enabled distance_km (lte) filter as the search radius, not the default', async () => {
  const viewer = await makeUser({ age: 30, gender: 'woman', latitude: 1, longitude: 1 });
  const withoutFilter = await resolveGeoSearchContext(ctx, viewer);
  assert.equal(withoutFilter.radiusKm, DEFAULT_DISCOVERY_RADIUS_KM);

  await addFilter(viewer, 'distance_km', 'lte', 12);
  const withFilter = await resolveGeoSearchContext(ctx, viewer);
  assert.equal(withFilter.radiusKm, 12, 'an explicit lte distance_km filter must size the box, not the fallback default');
});

test('resolveGeoSearchContext: a viewer with no location on file gets no box (falls back to cap-only bounding, never silently excluded)', async () => {
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO users (email, password_hash, birthdate, status) VALUES ($1, 'x', '1995-01-01', 'active') RETURNING id`,
    [`filter-no-profile-${++seq}@test.local`],
  );
  const bareUserId = rows[0]!.id;
  const context = await resolveGeoSearchContext(ctx, bareUserId);
  assert.equal(context.box, null);
});
