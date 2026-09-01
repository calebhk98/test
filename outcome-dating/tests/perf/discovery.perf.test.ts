/**
 * tests/perf/discovery.perf.test.ts
 *
 * The scalability proof for docs/scale-and-sources.md Part 1's discovery/
 * reality-dashboard findings, and the regression guard against
 * reintroducing the N+1 this build removed.
 *
 * Runs against its own dedicated database (`odate_perf_discovery`, per
 * this build's `odate_perf_<suite>` naming convention, see the task
 * brief), seeded with a realistic multi-city dataset via
 * `seedDiscoveryPerf.ts` (tens of thousands of users, several cities,
 * varied hard filters and answered questions, NOT one homogeneous blob).
 *
 * Two things are proven here, both load-bearing for the "worst
 * scalability defect" fix:
 *
 *   1. QUERY COUNT DOES NOT GROW WITH POOL SIZE. A query-counting
 *      `DbClient` wraps the real pool; `getDiscoveryGrid`/
 *      `getRealityDashboard` are called for several different viewers
 *      (different cities, different local population sizes, one
 *      deliberately in the densest seeded metro, see
 *      `seedDiscoveryPerf.ts#pickCity`) and the query count for EACH is
 *      asserted against the same fixed ceiling. If a future change
 *      reintroduces a per-candidate query inside the pool-gating loop,
 *      the ceiling assertion fails long before anyone notices via
 *      latency alone.
 *   2. LATENCY AT REALISTIC SCALE. Wall-clock time for the same calls is
 *      measured and printed (not just asserted under a generous ceiling)
 * this build's report quotes these numbers directly, per the task
 *      brief's "a performance claim without a measurement is not a
 *      result".
 *
 * What this file does NOT do: re-run the ORIGINAL unbounded/N+1 code at
 * this scale to produce a literal "before" measurement, at 20,000+
 * candidates the original code is credibly estimated (see
 * docs/scale-and-sources.md §1.1.2's own worked table) to take tens of
 * seconds to minutes PER REQUEST while holding a connection the whole
 * time, which is exactly the failure mode being fixed; deliberately
 * reproducing that here would make this suite itself slow/flaky for no
 * benefit. The "before" comparison this build's report cites instead
 * comes from a smaller, still-real, still-measured comparison (see the
 * "N+1 elimination, measured directly" test below, which calls the
 * UNCHANGED single-pair `passesMutualFilters`/`isVisibleInDiscovery`
 * functions in a loop, i.e. literally the old per-candidate pattern,
 * still present and used elsewhere in this codebase for single-candidate
 * call sites, against the same seeded data the new batched path uses).
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import pg from 'pg';
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
import { getDiscoveryGrid, getRealityDashboard, MAX_CANDIDATE_POOL_SIZE } from '../../src/services/discovery.service.js';
import { passesMutualFilters, DASHBOARD_SCAN_CAP } from '../../src/services/filter.service.js';
import { isVisibleInDiscovery } from '../../src/services/moderation.service.js';
import { seedDiscoveryPerfData, CITIES, type SeededUser } from './seedDiscoveryPerf.js';

const BASE_URL = process.env.DATABASE_URL ?? 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';
const TEST_DB_NAME = 'odate_perf_discovery';
const USER_COUNT = Number(process.env.DISCOVERY_PERF_USER_COUNT ?? 24_000);

function withDbName(url: string, dbName: string): string {
  const u = new URL(url);
  u.pathname = `/${dbName}`;
  return u.toString();
}

let adminPool: pg.Pool;
let pool: pg.Pool;
let ctx: Ctx;
let seededUsers: SeededUser[] = [];

/** Wraps a real pg.Pool's `query` to count calls, the "queries per page" instrument the task brief asks for. */
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
  const result = await seedDiscoveryPerfData(pool, { userCount: USER_COUNT, seed: 1337 });
  seededUsers = result.users;
  console.log(
    `[discovery.perf] seeded ${USER_COUNT} users across ${CITIES.length} cities in ${Date.now() - seedStart}ms`,
  );
}, { timeout: 300_000 });

after(async () => {
  await closePool();
  await adminPool.query(`DROP DATABASE IF EXISTS ${TEST_DB_NAME}`);
  await adminPool.end();
});

function actorFor(userId: string): Ctx {
  return { ...ctx, actor: { type: 'user', userId, trustLevel: 'standard' } };
}

/** A handful of representative viewers: several from the deliberately-oversized New York population, one from each smaller city, proves the query/latency story holds regardless of local pool size, not just for one lucky sample. */
function sampleViewers(): SeededUser[] {
  const byCity = new Map<string, SeededUser[]>();
  for (const u of seededUsers) {
    const list = byCity.get(u.city.name);
    if (list) list.push(u);
    else byCity.set(u.city.name, [u]);
  }
  const samples: SeededUser[] = [];
  for (const city of CITIES) {
    const list = byCity.get(city.name);
    if (list && list.length > 0) samples.push(list[Math.floor(list.length / 2)]!);
  }
  return samples;
}

// A generous but MEANINGFUL ceiling: comfortably above the actual
// measured cost (see console output / this build's report for the real
// number), but nowhere close to "grows with pool size", the whole point
// is that this number is the same whether the pool has 50 or 12,000
// candidates in it. If a future change makes one query per candidate
// again, this fails almost immediately at this dataset's scale, long
// before anyone notices from latency alone.
const MAX_QUERIES_PER_DISCOVERY_PAGE = 30;
// The dashboard costs roughly 2x a discovery page's query budget (X and Y
// each run their own geo-bounded batched scan, concurrently with Z,
// which IS a full discovery-pool computation), see the measured numbers
// in this build's report.
const MAX_QUERIES_PER_DASHBOARD_CALL = 40;

test(
  `getDiscoveryGrid: query count is bounded and does NOT grow with pool size (seeded ${USER_COUNT} users)`,
  { timeout: 120_000 },
  async () => {
    const viewers = sampleViewers();
    assert.ok(viewers.length >= CITIES.length - 1, 'sanity: sampled at least one viewer per city');

    const { db, count, reset } = countingDb(pool);
    const results: { city: string; queries: number; ms: number; items: number }[] = [];

    for (const viewer of viewers) {
      const viewerCtx = { ...actorFor(viewer.id), db };
      // Warm-up call: primes ConfigService's per-key cache (config rarely
      // changes in production; steady-state is the fair comparison, see
      // the "cold" call measured separately below for the first-ever-call cost).
      await getDiscoveryGrid(viewerCtx, { limit: 20 });

      reset();
      const t0 = Date.now();
      const page = await getDiscoveryGrid(viewerCtx, { limit: 20 });
      const ms = Date.now() - t0;
      const queries = count();

      results.push({ city: viewer.city.name, queries, ms, items: page.items.length });
      assert.ok(
        queries <= MAX_QUERIES_PER_DISCOVERY_PAGE,
        `${viewer.city.name} (pool candidate near ${page.items.length} shown): ${queries} queries exceeds the ${MAX_QUERIES_PER_DISCOVERY_PAGE} ceiling, an N+1 has likely been reintroduced`,
      );
    }

    console.log('[discovery.perf] getDiscoveryGrid, one page per city, steady-state (warmed config cache):');
    for (const r of results) {
      console.log(`  ${r.city.padEnd(14)} queries=${r.queries}  latency_ms=${r.ms}  items=${r.items}`);
    }

    // The core scale claim: New York (the deliberately oversized ~50%-
    // share city, thousands of local candidates before the geographic
    // bound+cap even apply) must cost the SAME NUMBER OF QUERIES as the
    // smallest sampled city, not more. Query count is flat; only the
    // in-Postgres row-scan work (still O(1) round trips) grows with
    // population, and that is measured separately by latency below.
    const queryCounts = new Set(results.map((r) => r.queries));
    assert.equal(
      queryCounts.size,
      1,
      `every sampled viewer must cost the identical number of queries regardless of local pool size, got: ${JSON.stringify(results)}`,
    );
  },
);

test(
  `getDiscoveryGrid: a COLD call (no config cache warm) is still bounded`,
  { timeout: 60_000 },
  async () => {
    // A fresh Ctx (own ConfigService instance -> empty cache) simulates
    // the very first request an app instance serves.
    const coldCtx: Ctx = {
      ...ctx,
      config: new ConfigService(pool, ctx.clock, createSilentLogger()),
      actor: { type: 'user', userId: seededUsers[0]!.id, trustLevel: 'standard' },
    };
    const { db, count } = countingDb(pool);
    const coldCtxCounted = { ...coldCtx, db };

    const t0 = Date.now();
    const page = await getDiscoveryGrid(coldCtxCounted, { limit: 20 });
    const ms = Date.now() - t0;
    const queries = count();

    console.log(`[discovery.perf] getDiscoveryGrid, COLD (unwarmed config cache): queries=${queries} latency_ms=${ms} items=${page.items.length}`);
    assert.ok(queries <= MAX_QUERIES_PER_DISCOVERY_PAGE + 10, `cold-cache first call: ${queries} queries`);
  },
);

test(
  `getRealityDashboard: query count is bounded, including for the densest seeded city (triggers the truncation/estimate path)`,
  { timeout: 120_000 },
  async () => {
    const viewers = sampleViewers();
    const { db, count, reset } = countingDb(pool);
    const results: { city: string; queries: number; ms: number; x: number; y: number; z: number }[] = [];

    for (const viewer of viewers) {
      const viewerCtx = { ...actorFor(viewer.id), db };
      await getRealityDashboard(viewerCtx); // warm-up

      reset();
      const t0 = Date.now();
      const dashboard = await getRealityDashboard(viewerCtx);
      const ms = Date.now() - t0;
      const queries = count();

      results.push({ city: viewer.city.name, queries, ms, x: dashboard.matchesMyFilters, y: dashboard.whoseFiltersIMatch, z: dashboard.mutualMatchPool });
      assert.ok(
        queries <= MAX_QUERIES_PER_DASHBOARD_CALL,
        `${viewer.city.name}: ${queries} queries exceeds the ${MAX_QUERIES_PER_DASHBOARD_CALL} ceiling`,
      );
      assert.ok(Number.isFinite(dashboard.matchesMyFilters) && dashboard.matchesMyFilters >= 0);
      assert.ok(Number.isFinite(dashboard.whoseFiltersIMatch) && dashboard.whoseFiltersIMatch >= 0);
      assert.ok(dashboard.mutualMatchPool <= MAX_CANDIDATE_POOL_SIZE);
    }

    console.log('[discovery.perf] getRealityDashboard, per city, steady-state:');
    for (const r of results) {
      console.log(`  ${r.city.padEnd(14)} queries=${r.queries}  latency_ms=${r.ms}  X=${r.x}  Y=${r.y}  Z=${r.z}`);
    }

    // Same flatness claim as getDiscoveryGrid: New York's dashboard (by
    // far the densest local population, well past DASHBOARD_SCAN_CAP)
    // must cost the same number of queries as every other city's.
    const queryCounts = new Set(results.map((r) => r.queries));
    assert.equal(
      queryCounts.size,
      1,
      `every sampled viewer's dashboard must cost the identical number of queries regardless of local population, got: ${JSON.stringify(results)}`,
    );

    // New York was seeded with ~50% of all users specifically so its
    // in-radius population exceeds DASHBOARD_SCAN_CAP, this is a direct
    // check that the estimator path is real, not just theoretically
    // reachable, by capturing the `logger.warn` `summarizeSampledCount`
    // fires only when truncated.
    const nyResult = results.find((r) => r.city === 'New York');
    assert.ok(nyResult, 'New York must be among the sampled viewers');

    const nyViewer = viewers.find((v) => v.city.name === 'New York')!;
    const warnings: string[] = [];
    const spyLogger = { ...ctx.logger, warn: (msg: string) => warnings.push(msg) };
    await getRealityDashboard({ ...actorFor(nyViewer.id), logger: spyLogger as typeof ctx.logger });
    assert.ok(
      warnings.some((w) => /exceeds the dashboard scan cap/.test(w)),
      `New York's in-radius population (well over DASHBOARD_SCAN_CAP=${DASHBOARD_SCAN_CAP}) must trigger the documented estimate path, observably (logger.warn), not silently`,
    );
  },
);

test(
  'N+1 elimination, measured directly: the OLD per-candidate pattern (still-present single-pair functions, called in a loop) vs the NEW batched pipeline, same seeded pool',
  { timeout: 120_000 },
  async () => {
    // A modest, still-tractable pool size for the legacy loop (thousands
    // of sequential round trips at 24,000-candidate scale would make this
    // one test itself take longer than the rest of the suite combined,
    // see this file's top-of-file doc for why the literal 24k-scale
    // "before" number is cited from docs/scale-and-sources.md's own
    // estimate instead of re-measured here). This still directly proves
    // the N+1 is gone: same data, same gate, two code paths.
    const legacyPoolSize = 300;
    const candidates = seededUsers.filter((u) => u.city.name === 'New York').slice(0, legacyPoolSize);
    assert.ok(candidates.length >= legacyPoolSize, 'sanity: enough New York candidates seeded');
    const viewer = seededUsers.find((u) => u.city.name === 'New York' && !candidates.includes(u))!;

    const { db: legacyDb, count: legacyCount, reset: legacyReset } = countingDb(pool);
    const legacyCtx = { ...actorFor(viewer.id), db: legacyDb };
    legacyReset();
    const legacyStart = Date.now();
    let legacySurvivors = 0;
    for (const c of candidates) {
      if (!(await isVisibleInDiscovery(legacyCtx, c.id))) continue;
      if (!(await passesMutualFilters(legacyCtx, viewer.id, c.id))) continue;
      legacySurvivors++;
    }
    const legacyMs = Date.now() - legacyStart;
    const legacyQueries = legacyCount();

    const { db: batchedDb, count: batchedCount, reset: batchedReset } = countingDb(pool);
    const batchedCtx = { ...actorFor(viewer.id), db: batchedDb };
    await getDiscoveryGrid(batchedCtx, { limit: 20 }); // warm-up (config cache)
    batchedReset();
    const batchedStart = Date.now();
    const page = await getDiscoveryGrid(batchedCtx, { limit: MAX_CANDIDATE_POOL_SIZE });
    const batchedMs = Date.now() - batchedStart;
    const batchedQueries = batchedCount();

    console.log(
      `[discovery.perf] N+1 comparison over ${legacyPoolSize} candidates (New York):\n` +
        `  legacy per-candidate loop (isVisibleInDiscovery + passesMutualFilters): queries=${legacyQueries} latency_ms=${legacyMs} survivors=${legacySurvivors}\n` +
        `  new batched getDiscoveryGrid (full pool, cap=${MAX_CANDIDATE_POOL_SIZE}):    queries=${batchedQueries} latency_ms=${batchedMs} items=${page.items.length}`,
    );

    // The legacy loop's query count scales with pool size (2 functions x
    // up to several queries each, PER candidate); the batched path's does
    // not. This is the same invariant proven statistically above, shown
    // here as a direct head-to-head on identical data.
    assert.ok(
      legacyQueries > candidates.length,
      'sanity: the legacy per-candidate loop really does cost at least one query per candidate',
    );
    assert.ok(
      batchedQueries < legacyQueries,
      `the batched path (${batchedQueries} queries) must cost dramatically fewer queries than the legacy per-candidate loop (${legacyQueries} queries) over the same ${legacyPoolSize}-candidate pool`,
    );
    assert.ok(batchedQueries <= MAX_QUERIES_PER_DISCOVERY_PAGE);
  },
);
