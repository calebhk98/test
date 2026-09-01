/**
 * tests/perf/scaleCurve.perf.test.ts
 *
 * docs/capacity.md's empirical backbone. Two separate claims, both
 * measured (not asserted) here:
 *
 *   1. POPULATION INDEPENDENCE (docs/capacity.md "measured vs
 *      extrapolated" table). For every user-facing read path this build
 *      could reach (discovery grid, reality dashboard, a profile view,
 *      the matches list, a conversation timeline, and both stats calls),
 *      the SAME fixed home-city population is seeded at three different
 *      TOTAL platform sizes (1,000 / 10,000 / 50,000 — the rest of each
 *      total lives in cities >1,000km from the viewer's own, so it can
 *      never enter the viewer's geographic box — see
 *      `seedScaleCurve.ts`'s file doc for why Chicago). If a path's cost
 *      is genuinely a function of "people near me," not "people," its
 *      latency curve across these three runs should be flat. This is the
 *      generalization of `discovery.perf.test.ts`'s "same city, different
 *      total pool" proof to the actual axis the capacity task asks about:
 *      "same viewer, different REST-OF-PLATFORM size."
 *   2. GROWTH CURVE FOR EXTRAPOLATION. `getSeedingMs`/the printed table
 *      also gives docs/capacity.md real numbers to extrapolate FROM (e.g.
 *      seed throughput, row counts) rather than assert from nothing — see
 *      that doc's arithmetic, which cites this file's console output
 *      directly.
 *
 * Each scale gets its own database (`odate_scale_curve_<n>`, per this
 * task's `odate_scale_<suite>` naming convention). Kept to three scales
 * and modest per-scale fixtures (see `seedScaleCurve.ts`) specifically so
 * the whole suite finishes in minutes, not the ~20-minute ceiling the task
 * brief allows.
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
import { getDiscoveryGrid, getRealityDashboard } from '../../src/services/discovery.service.js';
import { getPublicProfile } from '../../src/services/profile.service.js';
import { listMyMatches } from '../../src/services/matches.service.js';
import { getConversationTimeline } from '../../src/services/timeline.service.js';
import { getMyStatsOverview, getMyFilterCosts } from '../../src/services/stats.service.js';
import { seedScaleCurveData, type ScaleCurveSeed } from './seedScaleCurve.js';

const BASE_URL = process.env.DATABASE_URL ?? 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';

// Overridable for a faster/slower local run; default is the task brief's
// own suggested scale ladder.
const SCALES: number[] = (process.env.SCALE_CURVE_SCALES ?? '1000,10000,50000')
  .split(',')
  .map((s) => Number(s.trim()))
  .filter((n) => Number.isFinite(n) && n > 0);

function withDbName(url: string, dbName: string): string {
  const u = new URL(url);
  u.pathname = `/${dbName}`;
  return u.toString();
}

function countingDb(realPool: pg.Pool): { db: DbClient; count: () => number; reset: () => void } {
  let n = 0;
  return {
    db: {
      query: ((...args: unknown[]) => {
        n++;
        // @ts-expect-error — forwarding pg.Pool#query's overloaded signature verbatim.
        return realPool.query(...args);
      }) as DbClient['query'],
    },
    count: () => n,
    reset: () => {
      n = 0;
    },
  };
}

interface Measurement {
  scale: number;
  path: string;
  ms: number;
  queries: number;
}

const results: Measurement[] = [];

async function measure(
  scale: number,
  path: string,
  pool: pg.Pool,
  fn: (ctx: Ctx) => Promise<unknown>,
  baseCtx: Ctx,
): Promise<void> {
  const { db, count, reset } = countingDb(pool);
  const ctx = { ...baseCtx, db };
  await fn(ctx); // warm-up (config cache, connection)
  reset();
  const t0 = Date.now();
  await fn(ctx);
  const ms = Date.now() - t0;
  const queries = count();
  results.push({ scale, path, ms, queries });
}

const adminPool = new pg.Pool({ connectionString: BASE_URL });

after(async () => {
  await adminPool.end();
});

for (const scale of SCALES) {
  test(
    `scale curve @ ${scale} total users (home city fixed at 400)`,
    { timeout: 10 * 60_000 },
    async () => {
      const dbName = `odate_scale_curve_${scale}`;
      await adminPool.query(`DROP DATABASE IF EXISTS ${dbName}`);
      await adminPool.query(`CREATE DATABASE ${dbName}`);
      process.env.DATABASE_URL = withDbName(BASE_URL, dbName);
      await runMigrations();
      const pool = getPool();

      const logger = createSilentLogger();
      const clock = new ManualClock(new Date('2026-06-01T12:00:00Z'));
      const baseCtx: Ctx = {
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
      const seed: ScaleCurveSeed = await seedScaleCurveData(pool, scale);
      const seedMs = Date.now() - seedStart;
      console.log(
        `[scale-curve] scale=${scale} seeded (home=${seed.homeUserCount}, elsewhere=${seed.elsewhereUserCount}) in ${seedMs}ms`,
      );

      const viewerCtx: Ctx = { ...baseCtx, actor: { type: 'user', userId: seed.viewerId, trustLevel: 'standard' } };

      await measure(scale, 'discoveryGrid', pool, (ctx) => getDiscoveryGrid(ctx, { limit: 20 }), viewerCtx);
      await measure(scale, 'realityDashboard', pool, (ctx) => getRealityDashboard(ctx), viewerCtx);
      await measure(scale, 'publicProfile', pool, (ctx) => getPublicProfile(ctx, seed.candidateId), viewerCtx);
      await measure(scale, 'listMyMatches', pool, (ctx) => listMyMatches(ctx, { limit: 20 }), viewerCtx);
      await measure(
        scale,
        'conversationTimeline',
        pool,
        (ctx) => getConversationTimeline(ctx, seed.timelineConversationId, { limit: 50 }),
        viewerCtx,
      );
      await measure(scale, 'statsOverview', pool, (ctx) => getMyStatsOverview(ctx), viewerCtx);
      await measure(scale, 'filterCosts', pool, (ctx) => getMyFilterCosts(ctx, pool, { forceRefresh: true }), viewerCtx);

      await closePool();
      process.env.DATABASE_URL = BASE_URL;
      await adminPool.query(`DROP DATABASE IF EXISTS ${dbName}`);

      assert.ok(true, 'scale point recorded — flatness is asserted once, after every scale has run');
    },
  );
}

test('scale curve: print the measured table and assert flatness across population sizes', () => {
  assert.equal(results.length, SCALES.length * 7, 'sanity: every scale produced every measurement');

  console.log('\n[scale-curve] measured latency (ms) and query count, by read path and total population:');
  const paths = [...new Set(results.map((r) => r.path))];
  for (const path of paths) {
    const rows = results.filter((r) => r.path === path).sort((a, b) => a.scale - b.scale);
    const line = rows.map((r) => `N=${r.scale}: ${r.ms}ms/${r.queries}q`).join('  ->  ');
    console.log(`  ${path.padEnd(20)} ${line}`);
  }

  // FLATNESS ASSERTION: query count must never grow with total population
  // (it may vary slightly path-to-path for reasons unrelated to N, e.g.
  // cache warm state, but must not trend upward across scales) and
  // latency must stay within a generous constant-factor band — generous
  // because real Postgres latency at fixed row counts still has run to
  // run noise, disk cache warmth, and (as total DB size grows across
  // scales) marginally larger indexes to plan around even for a query
  // that touches the same NUMBER of rows. The claim under test is
  // "doesn't scale with N," not "zero variance."
  const MAX_LATENCY_RATIO = 6;
  for (const path of paths) {
    const rows = results.filter((r) => r.path === path).sort((a, b) => a.scale - b.scale);
    const first = rows[0]!;
    const last = rows[rows.length - 1]!;

    assert.ok(
      last.queries <= first.queries + 2,
      `${path}: query count grew from ${first.queries} (N=${first.scale}) to ${last.queries} (N=${last.scale}) — cost should not grow with total population`,
    );

    const minMs = Math.max(1, Math.min(...rows.map((r) => r.ms)));
    const maxMs = Math.max(...rows.map((r) => r.ms));
    assert.ok(
      maxMs / minMs <= MAX_LATENCY_RATIO,
      `${path}: latency ranged from ${minMs}ms to ${maxMs}ms across scales ${JSON.stringify(rows.map((r) => [r.scale, r.ms]))} — ratio ${(maxMs / minMs).toFixed(1)}x exceeds the ${MAX_LATENCY_RATIO}x flatness ceiling`,
    );
  }
});
