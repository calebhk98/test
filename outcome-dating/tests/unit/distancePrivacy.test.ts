/**
 * tests/unit/distancePrivacy.test.ts, SAF-2 fix proof:
 * `domain/units/distance.ts#approximateDistanceBetween` is the single
 * distance function every surface uses, and it actually resists the
 * documented trilateration attack (sample a target's reported distance
 * from several known vantage points, solve the intersecting circles for
 * their real location) rather than merely asserting it's safe in a
 * comment.
 *
 * Most of this file is pure (no I/O) since `approximateDistanceBetween`
 * itself has none, only the final section, proving discovery.service.ts
 * and profile.service.ts report the IDENTICAL number for the same pair,
 * needs a database. Owns its own dedicated database
 * (`odate_safety_distanceprivacy`, per the build brief).
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
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
import { approximateDistanceBetween, DEFAULT_DISTANCE_BUCKET_KM } from '../../src/domain/units/distance.js';
import * as profile from '../../src/services/profile.service.js';
import * as discovery from '../../src/services/discovery.service.js';

// =========================================================================
// Local flat-earth projection + least-squares multilateration, a
// deliberately simple, standard implementation of exactly the attack
// docs/risk-review.md's SAF-2 finding describes ("create N accounts at
// known coordinates, record the reported distance from each, solve").
// Valid for the small (a few km) areas these tests use.
// =========================================================================

const KM_PER_DEG_LAT = 110.574;
function kmPerDegLon(atLatDeg: number): number {
  return 111.320 * Math.cos((atLatDeg * Math.PI) / 180);
}

interface Point { x: number; y: number } // local km-projected coordinates

function project(lat: number, lon: number, originLat: number, originLon: number): Point {
  return {
    x: (lon - originLon) * kmPerDegLon(originLat),
    y: (lat - originLat) * KM_PER_DEG_LAT,
  };
}

/**
 * Least-squares 2D multilateration: given N known points and their
 * (possibly noisy) distances to an unknown point, estimate the unknown
 * point's position. Standard linearization against the first point,
 * solved via normal equations. Returns null if underdetermined.
 */
function multilaterate(points: Point[], distances: number[]): Point | null {
  if (points.length < 3) return null;
  const [p1] = points;
  const [d1] = distances;

  // Build A*[x,y]^T = b for i = 2..N.
  const A: number[][] = [];
  const b: number[] = [];
  for (let i = 1; i < points.length; i++) {
    const pi = points[i]!;
    const di = distances[i]!;
    A.push([2 * (pi.x - p1!.x), 2 * (pi.y - p1!.y)]);
    b.push(d1! * d1! - di * di + pi.x * pi.x - p1!.x * p1!.x + pi.y * pi.y - p1!.y * p1!.y);
  }

  // Normal equations: (A^T A) x = A^T b, solved by Cramer's rule (2x2).
  let ata00 = 0, ata01 = 0, ata11 = 0, atb0 = 0, atb1 = 0;
  for (let i = 0; i < A.length; i++) {
    const [a0, a1] = A[i]!;
    ata00 += a0! * a0!;
    ata01 += a0! * a1!;
    ata11 += a1! * a1!;
    atb0 += a0! * b[i]!;
    atb1 += a1! * b[i]!;
  }
  const det = ata00 * ata11 - ata01 * ata01;
  if (Math.abs(det) < 1e-9) return null;
  const x = (atb0 * ata11 - ata01 * atb1) / det;
  const y = (ata00 * atb1 - ata01 * atb0) / det;
  return { x, y };
}

function distanceBetweenPoints(a: Point, b: Point): number {
  return Math.hypot(a.x - b.x, a.y - b.y);
}

/** 8 vantage points on a ring around the origin, radius km, the attacker's known-coordinate fake accounts. */
function ringOfVantagePoints(centerLat: number, centerLon: number, radiusKm: number, n: number): { lat: number; lon: number }[] {
  const out: { lat: number; lon: number }[] = [];
  for (let i = 0; i < n; i++) {
    const angle = (2 * Math.PI * i) / n;
    const dLat = (radiusKm * Math.cos(angle)) / KM_PER_DEG_LAT;
    const dLon = (radiusKm * Math.sin(angle)) / kmPerDegLon(centerLat);
    out.push({ lat: centerLat + dLat, lon: centerLon + dLon });
  }
  return out;
}

// =========================================================================
// THE adversarial test.
// =========================================================================

test('SAF-2 adversarial: multi-account trilateration (known vantage points, reported approximate distances) cannot recover the target location to a useful precision', () => {
  const targetLat = 40.7128;
  const targetLon = -74.006;
  const targetId = 'target-user';
  const vantages = ringOfVantagePoints(targetLat, targetLon, 1.5, 8);

  const targetPoint = project(targetLat, targetLon, targetLat, targetLon); // {0,0} by construction

  // ---- CONTROL: validate the attack methodology itself is sound,
  // solving with EXACT (unbucketed, unjittered) distances must recover
  // the target's true location almost perfectly. If this control fails,
  // the "attack" below would be meaningless. ----
  const exactPoints = vantages.map((v) => project(v.lat, v.lon, targetLat, targetLon));
  const exactDistances = vantages.map((v) => {
    const p = project(v.lat, v.lon, targetLat, targetLon);
    return distanceBetweenPoints(p, targetPoint);
  });
  const exactEstimate = multilaterate(exactPoints, exactDistances);
  assert.ok(exactEstimate, 'control solve must produce an estimate');
  const exactErrorKm = distanceBetweenPoints(exactEstimate!, targetPoint);
  assert.ok(exactErrorKm < 0.01, `sanity check: exact-distance trilateration must be near-perfect (got ${exactErrorKm}km error)`);

  // ---- THE ATTACK: 8 distinct fake "viewer" accounts, each at a known
  // vantage point, each recording what approximateDistanceBetween reports
  // for this same target. This is exactly docs/risk-review.md's SAF-2
  // precedent ("create 3+ accounts at known coordinates, record the
  // reported distance from each, solve"). ----
  const reportedPoints = vantages.map((v) => project(v.lat, v.lon, targetLat, targetLon));
  const reportedDistances = vantages.map((v, i) =>
    approximateDistanceBetween({ id: `attacker-${i}`, latitude: v.lat, longitude: v.lon }, { id: targetId, latitude: targetLat, longitude: targetLon }),
  );
  assert.ok(reportedDistances.every((d) => d !== null), 'every vantage point has coordinates set, so every call must return a number');

  const attackEstimate = multilaterate(reportedPoints, reportedDistances as number[]);
  assert.ok(attackEstimate, 'the solve itself still produces SOME estimate: that is expected; the point is how far off it is');
  const attackErrorKm = distanceBetweenPoints(attackEstimate!, targetPoint);

  // The fix's job is to make that estimate USELESS, not merely "off by a
  // little". Require it to be off by at least half the bucket width, and
  // by at least an order of magnitude worse than the (near-zero) control
  // error, i.e. street-level recovery has been destroyed, not just
  // slightly degraded.
  assert.ok(
    attackErrorKm >= DEFAULT_DISTANCE_BUCKET_KM / 2,
    `trilateration against the approximate/jittered distance must miss by at least half a bucket width (${DEFAULT_DISTANCE_BUCKET_KM / 2}km), got ${attackErrorKm}km`,
  );
  assert.ok(
    attackErrorKm > exactErrorKm * 10,
    `attack error (${attackErrorKm}km) must be at least an order of magnitude worse than the exact-distance control (${exactErrorKm}km)`,
  );
});

test('SAF-2 adversarial: a SECOND, independently-run attack (different attacker account IDs) against the SAME target recovers a DIFFERENT wrong location, the offsets do not average out into the truth', () => {
  const targetLat = 34.0522;
  const targetLon = -118.2437;
  const targetId = 'target-user-2';
  const vantages = ringOfVantagePoints(targetLat, targetLon, 1.2, 6);
  const targetPoint = project(targetLat, targetLon, targetLat, targetLon);

  function attackWithPrefix(prefix: string): Point | null {
    const points = vantages.map((v) => project(v.lat, v.lon, targetLat, targetLon));
    const distances = vantages.map(
      (v, i) =>
        approximateDistanceBetween(
          { id: `${prefix}-${i}`, latitude: v.lat, longitude: v.lon },
          { id: targetId, latitude: targetLat, longitude: targetLon },
        )!,
    );
    return multilaterate(points, distances);
  }

  const estimateA = attackWithPrefix('campaignA');
  const estimateB = attackWithPrefix('campaignB');
  assert.ok(estimateA && estimateB);

  const errorA = distanceBetweenPoints(estimateA!, targetPoint);
  const errorB = distanceBetweenPoints(estimateB!, targetPoint);
  const disagreement = distanceBetweenPoints(estimateA!, estimateB!);

  assert.ok(errorA >= DEFAULT_DISTANCE_BUCKET_KM / 2 || errorB >= DEFAULT_DISTANCE_BUCKET_KM / 2, 'at least one independent attack campaign must miss substantially');
  assert.ok(disagreement > 0.1, 'two independent attacker account sets must not converge on the same (wrong or right) location, the per-pair offset is what prevents combining campaigns to average out the noise');
});

// =========================================================================
// Supporting pure-function properties.
// =========================================================================

test('approximateDistanceBetween: deterministic for the same (viewer, target) pair and coordinates', () => {
  const a = { id: 'v1', latitude: 10, longitude: 20 };
  const b = { id: 't1', latitude: 10.05, longitude: 20.05 };
  const first = approximateDistanceBetween(a, b);
  const second = approximateDistanceBetween(a, b);
  assert.equal(first, second);
});

test('approximateDistanceBetween: two different viewer accounts standing at the EXACT SAME real spot can be shown different numbers for the same target', () => {
  const target = { id: 'shared-target', latitude: 51.5074, longitude: -0.1278 };
  const sameSpot = { latitude: 51.51, longitude: -0.13 };
  // Not asserting any specific pair MUST differ (a hash collision on the
  // modulus is legitimately possible), asserting the mechanism CAN
  // decorrelate them, proven by trying enough distinct viewer ids that at
  // least one reported value differs from the rest.
  const values = new Set<number>();
  for (let i = 0; i < 20; i++) {
    values.add(approximateDistanceBetween({ id: `viewer-${i}`, ...sameSpot }, target)!);
  }
  assert.ok(values.size > 1, 'at least some of 20 distinct viewer accounts at the identical real position must see different reported numbers');
});

test('approximateDistanceBetween: returns null when either party has no location set', () => {
  const a = { id: 'v', latitude: null, longitude: null };
  const b = { id: 't', latitude: 1, longitude: 1 };
  assert.equal(approximateDistanceBetween(a, b), null);
  assert.equal(approximateDistanceBetween(b, a), null);
});

test('approximateDistanceBetween: a wider bucketKm produces a coarser (never finer) figure', () => {
  const viewer = { id: 'v', latitude: 0, longitude: 0 };
  const target = { id: 't', latitude: 0.09, longitude: 0 }; // ~10km north
  const narrow = approximateDistanceBetween(viewer, target, { bucketKm: 1 });
  const wide = approximateDistanceBetween(viewer, target, { bucketKm: 50 });
  assert.ok(narrow !== null && wide !== null);
  // True distance is ~10km. A 1km bucket (+/- up to 2 jitter steps) must
  // land close to it; a 50km bucket can only land on a multiple of 50
  // (0, 50, 100, ...), necessarily a much worse fit to the true value.
  assert.ok(Math.abs(narrow! - 10) <= 2, `narrow bucket should stay close to the true distance, got ${narrow}`);
  assert.ok(Math.abs(wide! - 10) >= 10, `wide bucket must not resemble 1km precision, got ${wide}`);
});

test('approximateDistanceBetween: never negative', () => {
  const viewer = { id: 'v', latitude: 0, longitude: 0 };
  const target = { id: 't', latitude: 0.0001, longitude: 0.0001 }; // extremely close, a naive offset could go negative without clamping
  for (let i = 0; i < 50; i++) {
    const d = approximateDistanceBetween({ id: `v${i}`, latitude: 0, longitude: 0 }, target);
    assert.ok(d !== null && d >= 0, `distance must never be negative, got ${d}`);
  }
});

// =========================================================================
// Integration: profile.service.ts and discovery.service.ts must report
// the IDENTICAL figure for the same viewer/target pair, the "ONE
// function" requirement, proven end-to-end rather than just by both
// importing the same symbol.
// =========================================================================

const BASE_URL = process.env.DATABASE_URL ?? 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';
const DB_NAME = 'odate_safety_distanceprivacy';

function withDbName(url: string, dbName: string): string {
  const u = new URL(url);
  u.pathname = `/${dbName}`;
  return u.toString();
}

let adminPool: pg.Pool | undefined;
let testPool: pg.Pool | undefined;

before(async () => {
  adminPool = new pg.Pool({ connectionString: BASE_URL });
  await adminPool.query(`SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = $1 AND pid <> pg_backend_pid()`, [DB_NAME]);
  await adminPool.query(`DROP DATABASE IF EXISTS ${DB_NAME}`);
  await adminPool.query(`CREATE DATABASE ${DB_NAME}`);
  process.env.DATABASE_URL = withDbName(BASE_URL, DB_NAME);
  await runMigrations();
  testPool = getPool();
});

after(async () => {
  await closePool();
  if (adminPool) {
    await adminPool.query(`DROP DATABASE IF EXISTS ${DB_NAME}`);
    await adminPool.end();
  }
});

function getTestPool(): pg.Pool {
  if (!testPool) throw new Error('DB not set up yet');
  return testPool;
}

function buildCtx(opts: { actor?: Actor } = {}): Ctx {
  const pool = getTestPool();
  const clock = new ManualClock(new Date());
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

function userActor(userId: string): Actor {
  return { type: 'user', userId, trustLevel: 'standard' };
}

let emailCounter = 0;
function uniqueEmail(): string {
  emailCounter += 1;
  return `dist${emailCounter}.${Date.now()}@example.test`;
}

async function insertDiscoverableUser(ctx: Ctx, lat: number, lon: number): Promise<string> {
  const id = randomUUID();
  await ctx.db.query(
    `INSERT INTO users (id, email, password_hash, birthdate, status, trust_score, trust_level) VALUES ($1, $2, 'x', '1990-01-01', 'active', 50, 'standard')`,
    [id, uniqueEmail()],
  );
  await ctx.db.query(
    `INSERT INTO profiles (user_id, display_name, bio, latitude, longitude, age, gender, seeking, relationship_intention, profile_completeness)
     VALUES ($1, 'Name', 'bio', $2, $3, 28, 'woman', 'man', 'long_term', 100)`,
    [id, lat, lon],
  );
  await ctx.db.query(
    `INSERT INTO user_photos (user_id, image_url, position, is_primary, moderation_status, face_detected) VALUES ($1, 'https://example.test/p.jpg', 0, true, 'approved', true)`,
    [id],
  );
  return id;
}

test('integration: discovery.service.ts and profile.service.ts report the exact same approximateDistanceKm for the same viewer/target pair', async () => {
  const ctx = buildCtx();
  const viewerId = await insertDiscoverableUser(ctx, 40.0, -75.0);
  const targetId = await insertDiscoverableUser(ctx, 40.02, -75.01);

  const viewerCtx = buildCtx({ actor: userActor(viewerId) });
  const grid = await discovery.getDiscoveryGrid(viewerCtx, {});
  const card = grid.items.find((c) => c.userId === targetId);
  assert.ok(card, 'target must appear in the viewer\'s discovery grid');

  const profileView = await profile.buildPublicProfileView(ctx, viewerId, targetId);

  assert.equal(profileView.approximateDistanceKm, card!.approximateDistanceKm, 'discovery grid and profile page must report the IDENTICAL distance figure, one shared function, not two');
});
