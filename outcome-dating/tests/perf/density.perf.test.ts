/**
 * tests/perf/density.perf.test.ts
 *
 * Measured cost of the population-density discovery fix (docs/capacity.md;
 * src/services/discovery.service.ts#loadCandidatePool's DENSITY FIX doc)
 * at a realistically large LOCAL population, all crammed into ONE small
 * area (unlike tests/perf/discovery.perf.test.ts's six-city spread, this
 * is deliberately the worst case that fix targets: one dense neighborhood,
 * not several separate metros).
 *
 * Two things are proven here, both load-bearing for docs/capacity.md's
 * dense-city arithmetic:
 *
 *   1. QUERY COST STAYS FLAT AT HIGH LOCAL DENSITY. A query-counting
 *      `DbClient` (same technique as discovery.perf.test.ts) wraps the
 *      pool; `getDiscoveryGrid` is called against a ~50,000-person local
 *      population (all within the SAME bounding box, not spread across
 *      cities) and the query count is asserted against a fixed ceiling,
 *      the same one discovery.perf.test.ts uses for a normal city. If
 *      density alone ever made this grow, this fails immediately.
 *   2. THE DEFECT DOES NOT REAPPEAR AT SCALE. ~49,000 of those 50,000
 *      people are recently active AND fail the viewer's filter (the
 *      "recency-ordered pool full of filter-failing noise" failure mode);
 *      the other ~1,000 pass the filter but are far less recently active.
 *      The full (paginated) candidate pool is reconstructed and every
 *      single entry in it is asserted to be a real, filter-passing match,
 *      zero crowd members, proving filtering-before-truncation holds at a
 *      scale an order of magnitude past MAX_CANDIDATE_POOL_SIZE, not just
 *      in the small, hand-built tests/unit/density.test.ts fixtures.
 *
 * A true 46,000-people-per-km² neighborhood (docs/capacity.md's own
 * extreme-density figure) would need low millions of rows in a single
 * bounding box to reproduce literally, impractical for a fast test suite;
 * this file's ~50,000-in-one-box scale is the largest that stays fast
 * (seconds, not minutes) while still being an order of magnitude past the
 * pool cap, and the query-count flatness measured here is exactly what
 * makes docs/capacity.md's analytical extrapolation to the literal
 * 46,000/km² case (arithmetic, not re-measured) credible: cost is a
 * function of the WHERE-matched row count and the fixed query budget,
 * neither of which this test's scale-up changes in kind, only in size.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import pg from 'pg';
import { randomUUID } from 'node:crypto';
import { runMigrations } from '../../src/db/migrate.js';
import { closePool, getPool } from '../../src/db/pool.js';
import type { DbClient } from '../../src/db/pool.js';
import { ConfigService } from '../../src/config/config.service.js';
import { FlagsService } from '../../src/config/flags.service.js';
import { ManualClock } from '../../src/lib/time.js';
import { createSilentLogger } from '../../src/lib/logger.js';
import { FakeProcessor } from '../../src/services/payments/fake.processor.js';
import { StubMediaModerationAdapter } from '../../src/services/media/stub.adapter.js';
import type { Ctx } from '../../src/lib/ctx.js';
import { getDiscoveryGrid, MAX_CANDIDATE_POOL_SIZE } from '../../src/services/discovery.service.js';

const BASE_URL = process.env.DATABASE_URL ?? 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';
const TEST_DB_NAME = 'odate_density_perf';

const CROWD_SIZE = Number(process.env.DENSITY_PERF_CROWD_SIZE ?? 49_000);
const REAL_MATCH_SIZE = Number(process.env.DENSITY_PERF_REAL_MATCH_SIZE ?? 1_000);
const VIEWER_LAT = 12.34;
const VIEWER_LON = 56.78;

function withDbName(url: string, dbName: string): string {
  const u = new URL(url);
  u.pathname = `/${dbName}`;
  return u.toString();
}

let adminPool: pg.Pool;
let pool: pg.Pool;
let ctx: Ctx;
let viewerId: string;
let realMatchIds: Set<string>;

function countingDb(realPool: pg.Pool): { db: DbClient; count: () => number; reset: () => void } {
  let n = 0;
  return {
    db: {
      query: ((...args: unknown[]) => {
        n++;
        // @ts-expect-error, forwarding pg.Pool#query's overloaded signature verbatim.
        return realPool.query(...args);
      }) as DbClient['query'],
    },
    count: () => n,
    reset: () => {
      n = 0;
    },
  };
}

/** Bulk (`unnest`) insert, one round trip per table regardless of `count`. */
async function bulkInsertCandidates(opts: { count: number; gender: string; minutesAgo: number }): Promise<string[]> {
  const ids = Array.from({ length: opts.count }, () => randomUUID());
  const CHUNK = 10_000;
  for (let start = 0; start < ids.length; start += CHUNK) {
    const chunk = ids.slice(start, start + CHUNK);
    const emails = chunk.map((id) => `density-perf-${id}@test.local`);
    const minutesAgo = chunk.map(() => opts.minutesAgo);
    await pool.query(
      `INSERT INTO users (id, email, password_hash, birthdate, status, last_active_at)
       SELECT u.id, u.email, 'x', '1995-01-01', 'active', now() - (u.minutes_ago || ' minutes')::interval
       FROM unnest($1::uuid[], $2::text[], $3::int[]) AS u(id, email, minutes_ago)`,
      [chunk, emails, minutesAgo],
    );
    const names = chunk.map((id) => `DensityPerf${id.slice(0, 8)}`);
    await pool.query(
      `INSERT INTO profiles (user_id, display_name, city, latitude, longitude, location_fuzzed, age, gender, seeking, relationship_intention, profile_completeness)
       SELECT t.id, t.name, 'Testville', $2::double precision, $3::double precision, true, 30, $4::text, 'any', 'long_term', 80
       FROM unnest($1::uuid[], $5::text[]) AS t(id, name)`,
      [chunk, VIEWER_LAT, VIEWER_LON, opts.gender, names],
    );
    await pool.query(
      `INSERT INTO user_photos (user_id, image_url, position, is_primary, moderation_status)
       SELECT id, 'https://example.test/' || id || '.jpg', 0, true, 'approved' FROM unnest($1::uuid[]) AS t(id)`,
      [chunk],
    );
  }
  return ids;
}

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

  const seedStart = Date.now();

  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO users (id, email, password_hash, birthdate, status, last_active_at) VALUES ($1, $2, 'x', '1995-01-01', 'active', now()) RETURNING id`,
    [randomUUID(), 'density-perf-viewer@test.local'],
  );
  viewerId = rows[0]!.id;
  await pool.query(
    `INSERT INTO profiles (user_id, display_name, city, latitude, longitude, location_fuzzed, age, gender, seeking, relationship_intention, profile_completeness)
     VALUES ($1, 'DensityPerfViewer', 'Testville', $2, $3, true, 30, 'woman', 'any', 'long_term', 90)`,
    [viewerId, VIEWER_LAT, VIEWER_LON],
  );
  await pool.query(`INSERT INTO hard_filters (user_id, filter_key, operator, value, enabled) VALUES ($1, 'gender_preference', 'eq', '"man"'::jsonb, true)`, [
    viewerId,
  ]);

  // The dense, recently-active crowd: fails the viewer's gender filter.
  await bulkInsertCandidates({ count: CROWD_SIZE, gender: 'woman', minutesAgo: 1 });
  // The real matches: pass the filter, but are far less recently active
  // than every crowd member, exactly the pre-fix failure shape.
  const realIds = await bulkInsertCandidates({ count: REAL_MATCH_SIZE, gender: 'man', minutesAgo: 60 * 24 * 400 });
  realMatchIds = new Set(realIds);

  console.log(
    `[density.perf] seeded ${CROWD_SIZE + REAL_MATCH_SIZE + 1} users in ONE bounding box ` +
      `(${CROWD_SIZE} recently-active filter-failing, ${REAL_MATCH_SIZE} old filter-passing) in ${Date.now() - seedStart}ms`,
  );
}, { timeout: 300_000 });

after(async () => {
  await closePool();
  await adminPool.query(`DROP DATABASE IF EXISTS ${TEST_DB_NAME}`);
  await adminPool.end();
});

function viewerCtx(db: DbClient): Ctx {
  return { ...ctx, db, actor: { type: 'user', userId: viewerId, trustLevel: 'standard' } };
}

// Same ceiling discovery.perf.test.ts uses for a normal (multi-city, much
// smaller local pool) request: the whole point is that this number does
// NOT need to be higher just because this file's local population is ~2x
// bigger and concentrated in one box instead of spread across six.
const MAX_QUERIES_PER_DISCOVERY_PAGE = 30;

test(
  `getDiscoveryGrid: query count stays flat at ~${CROWD_SIZE + REAL_MATCH_SIZE} local candidates in ONE bounding box`,
  { timeout: 120_000 },
  async () => {
    const { db, count, reset } = countingDb(pool);
    const cctx = viewerCtx(db);

    await getDiscoveryGrid(cctx, { limit: 20 }); // warm-up (config cache)
    reset();
    const t0 = Date.now();
    const page = await getDiscoveryGrid(cctx, { limit: 20 });
    const ms = Date.now() - t0;
    const queries = count();

    console.log(`[density.perf] getDiscoveryGrid @ ${CROWD_SIZE + REAL_MATCH_SIZE} local candidates: queries=${queries} latency_ms=${ms} items=${page.items.length}`);
    assert.ok(
      queries <= MAX_QUERIES_PER_DISCOVERY_PAGE,
      `${queries} queries exceeds the ${MAX_QUERIES_PER_DISCOVERY_PAGE} ceiling at high local density, cost must not grow with density`,
    );
    assert.ok(page.items.length > 0, 'real matches exist and must be returned, not silently emptied by the recently-active crowd');
    for (const item of page.items) {
      assert.ok(realMatchIds.has(item.userId), 'every returned candidate must be a real, filter-passing match, never a filter-failing crowd member');
    }
  },
);

test(
  'getDiscoveryGrid: the full (paginated) candidate pool at this density contains ONLY real, filter-passing matches, at a scale far past MAX_CANDIDATE_POOL_SIZE',
  { timeout: 120_000 },
  async () => {
    const { db, count } = countingDb(pool);
    const cctx = viewerCtx(db);

    const t0 = Date.now();
    const allIds: string[] = [];
    let cursor: string | undefined;
    let pages = 0;
    for (let i = 0; i < 10; i++) {
      const page = await getDiscoveryGrid(cctx, { limit: 100, cursor });
      pages++;
      allIds.push(...page.items.map((c) => c.userId));
      if (!page.nextCursor) break;
      cursor = page.nextCursor;
    }
    const ms = Date.now() - t0;

    console.log(
      `[density.perf] full paginated pool @ ${CROWD_SIZE + REAL_MATCH_SIZE} local candidates: ${pages} pages, ${allIds.length} candidates, ${ms}ms total, ${count()} total queries`,
    );

    assert.ok(allIds.length > 0, 'the pool must not be empty');
    assert.ok(allIds.length <= MAX_CANDIDATE_POOL_SIZE, 'the pool must still respect the cap even at this density');
    for (const id of allIds) {
      assert.ok(realMatchIds.has(id), `candidate ${id} is not a real match: a filter-failing crowd member leaked into the pool despite being outnumbered`);
    }
    // REAL_MATCH_SIZE exceeds the cap, so the pool should be entirely
    // real matches AND fully use the cap (nothing wasted on crowd noise).
    assert.equal(allIds.length, Math.min(REAL_MATCH_SIZE, MAX_CANDIDATE_POOL_SIZE));
  },
);
