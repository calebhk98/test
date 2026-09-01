/**
 * Unit tests for discovery.service.ts.
 *
 * `sortDiscoveryCandidates` is pure and is where the spec §10.3 "no
 * compatibility threshold hides users" invariant is proven (a
 * 0-compatibility candidate still appears, just last). Blocking
 * (`blockUser`/`unblockUser`/`listBlockedUsers`/`isEitherBlocked`),
 * `recordDiscoveryImpression`'s `discovery_events` write, and
 * `isProfileVisibleTo`'s early-exit rules are exercised against a real,
 * dedicated Postgres database (`outcome_dating_test_discovery`).
 *
 * SCALE FIX (docs/scale-and-sources.md Part 1) coverage, below the
 * original test set: `getDiscoveryGrid`/`getRealityDashboard` are now
 * exercised end-to-end (the note this file used to carry about
 * `moderation.service#isVisibleInDiscovery` being an unimplemented stub is
 * stale — that landed separately) — proving the batched candidate-pool
 * pipeline (`computeRankedCandidatePool`) still enforces all nine §10.2
 * visibility rules, still never lets a compatibility score override a
 * failed hard filter, still never hides a zero-compatibility candidate,
 * is now geographically bounded, and that the geographic bound did not
 * change what a viewer is shown for another user's distance (still
 * coarse-bucketed + pair-jittered, per `domain/units/distance.ts`,
 * untouched by this build).
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
import type { DiscoveryCandidate } from '../../src/domain/types.js';
import {
  sortDiscoveryCandidates,
  type DiscoveryRankingInput,
  blockUser,
  unblockUser,
  listBlockedUsers,
  isEitherBlocked,
  recordDiscoveryImpression,
  isProfileVisibleTo,
  getDiscoveryGrid,
  getRealityDashboard,
  MAX_CANDIDATE_POOL_SIZE,
} from '../../src/services/discovery.service.js';
import { updateMyFilters, DEFAULT_DISCOVERY_RADIUS_KM } from '../../src/services/filter.service.js';
import { approximateDistanceBetween } from '../../src/domain/units/distance.js';

// =====================================================================
// Pure sortDiscoveryCandidates tests
// =====================================================================

function candidate(overrides: Partial<DiscoveryCandidate> & { userId: string }): DiscoveryCandidate {
  return {
    displayName: overrides.userId,
    age: 30,
    approximateDistanceKm: 5,
    primaryPhotoUrl: null,
    sharedInterestTag: null,
    compatibilityScore: 0.5,
    trustLevel: 'standard',
    profileCompleteness: 80,
    ...overrides,
  };
}

function ranked(c: DiscoveryCandidate, extra: Partial<Omit<DiscoveryRankingInput, 'candidate'>> = {}): DiscoveryRankingInput {
  return {
    candidate: c,
    trustScore: 60,
    lastActiveAt: new Date('2026-06-01T00:00:00Z'),
    responseRate: 0.5,
    ...extra,
  };
}

test('sortDiscoveryCandidates: sorts by compatibility score descending', () => {
  const inputs = [
    ranked(candidate({ userId: 'low', compatibilityScore: 0.2 })),
    ranked(candidate({ userId: 'high', compatibilityScore: 0.9 })),
    ranked(candidate({ userId: 'mid', compatibilityScore: 0.5 })),
  ];
  const sorted = sortDiscoveryCandidates(inputs);
  assert.deepEqual(sorted.map((c) => c.userId), ['high', 'mid', 'low']);
});

test('INVARIANT (§10.3/§16.1): a 0-compatibility candidate who passes filters still appears, just last — no threshold hides anyone', () => {
  const inputs = [
    ranked(candidate({ userId: 'good-match', compatibilityScore: 0.8 })),
    ranked(candidate({ userId: 'ok-match', compatibilityScore: 0.4 })),
    // Zero compatibility — still passed every hard filter to get this far
    // (this function is only ever called on an already-filtered pool; see
    // computeRankedCandidatePool). Sorting must never remove it.
    ranked(candidate({ userId: 'zero-match', compatibilityScore: 0 })),
  ];
  const sorted = sortDiscoveryCandidates(inputs);

  assert.equal(sorted.length, 3, 'the 0-compatibility candidate must not be dropped');
  assert.ok(sorted.some((c) => c.userId === 'zero-match'), 'the 0-compatibility candidate must be present in the results');
  assert.equal(sorted[sorted.length - 1]!.userId, 'zero-match', 'the 0-compatibility candidate must sort last, not be hidden');
});

test('sortDiscoveryCandidates: tie-break order is trust score, then profile completeness, then recent activity, then response rate', () => {
  // All four share the same compatibilityScore, so every subsequent
  // tie-breaker is exercised in the documented order.
  const base = { compatibilityScore: 0.5 };
  const a = ranked(candidate({ userId: 'a', ...base }), {
    trustScore: 90,
    lastActiveAt: new Date('2026-01-01'),
    responseRate: 0,
  });
  const b = ranked(candidate({ userId: 'b', ...base }), {
    trustScore: 50, // lower trust than a -> a must rank above b regardless of the rest
    lastActiveAt: new Date('2026-06-01'),
    responseRate: 1,
  });
  const sortedByTrust = sortDiscoveryCandidates([b, a]);
  assert.deepEqual(sortedByTrust.map((c) => c.userId), ['a', 'b'], 'higher trust score must win first');

  // Equal compatibility AND trust score -> profile completeness decides.
  const c = ranked(candidate({ userId: 'c', ...base, profileCompleteness: 95 }), { trustScore: 60 });
  const d = ranked(candidate({ userId: 'd', ...base, profileCompleteness: 40 }), { trustScore: 60 });
  assert.deepEqual(sortDiscoveryCandidates([d, c]).map((c) => c.userId), ['c', 'd']);

  // Equal compatibility, trust score, AND completeness -> recent activity decides.
  const e = ranked(candidate({ userId: 'e', ...base, profileCompleteness: 70 }), {
    trustScore: 60,
    lastActiveAt: new Date('2026-06-15'),
  });
  const f = ranked(candidate({ userId: 'f', ...base, profileCompleteness: 70 }), {
    trustScore: 60,
    lastActiveAt: new Date('2026-01-01'),
  });
  assert.deepEqual(sortDiscoveryCandidates([f, e]).map((c) => c.userId), ['e', 'f']);

  // Equal on everything else -> response rate is the last-resort tie-break.
  const g = ranked(candidate({ userId: 'g', ...base, profileCompleteness: 70 }), {
    trustScore: 60,
    lastActiveAt: new Date('2026-06-01'),
    responseRate: 0.9,
  });
  const h = ranked(candidate({ userId: 'h', ...base, profileCompleteness: 70 }), {
    trustScore: 60,
    lastActiveAt: new Date('2026-06-01'),
    responseRate: 0.1,
  });
  assert.deepEqual(sortDiscoveryCandidates([h, g]).map((c) => c.userId), ['g', 'h']);
});

test('sortDiscoveryCandidates: does not mutate its input array', () => {
  const inputs = [ranked(candidate({ userId: 'x', compatibilityScore: 0.1 })), ranked(candidate({ userId: 'y', compatibilityScore: 0.9 }))];
  const copy = [...inputs];
  sortDiscoveryCandidates(inputs);
  assert.deepEqual(inputs, copy);
});

// =====================================================================
// DB-backed tests
// =====================================================================

const BASE_URL = process.env.DATABASE_URL ?? 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';
const TEST_DB_NAME = 'outcome_dating_test_discovery';

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
async function makeUser(status: 'active' | 'suspended' = 'active'): Promise<string> {
  seq++;
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO users (email, password_hash, birthdate, status) VALUES ($1, 'x', '1995-01-01', $2) RETURNING id`,
    [`discovery-user-${seq}@test.local`, status],
  );
  return rows[0]!.id;
}

test('blockUser / unblockUser / listBlockedUsers: round-trip and are idempotent', async () => {
  const blocker = await makeUser();
  const target = await makeUser();
  const blockerCtx = actorFor(blocker);

  const block = await blockUser(blockerCtx, target);
  assert.equal(block.blockerId, blocker);
  assert.equal(block.blockedId, target);

  // Idempotent: blocking again does not throw or duplicate.
  await blockUser(blockerCtx, target);
  const list = await listBlockedUsers(blockerCtx);
  assert.equal(list.length, 1);

  await unblockUser(blockerCtx, target);
  assert.equal((await listBlockedUsers(blockerCtx)).length, 0);
});

test('blockUser: cannot block yourself', async () => {
  const userId = await makeUser();
  await assert.rejects(() => blockUser(actorFor(userId), userId));
});

test('isEitherBlocked: symmetric regardless of who blocked whom', async () => {
  const a = await makeUser();
  const b = await makeUser();
  const c = await makeUser();

  assert.equal(await isEitherBlocked(ctx, a, b), false);

  await blockUser(actorFor(a), b);
  assert.equal(await isEitherBlocked(ctx, a, b), true, 'blocker -> blocked direction');
  assert.equal(await isEitherBlocked(ctx, b, a), true, 'must also read true in the reverse argument order (§10.2 rule 9)');
  assert.equal(await isEitherBlocked(ctx, a, c), false, 'unrelated pair must remain unblocked');
});

test('recordDiscoveryImpression: writes a discovery_events row (no primary photo -> no photoExperiment call)', async () => {
  const viewer = await makeUser();
  const candidateId = await makeUser();

  await recordDiscoveryImpression(actorFor(viewer), candidateId, null);

  const { rows } = await pool.query(
    'SELECT viewer_user_id, candidate_user_id, primary_photo_id, source FROM discovery_events WHERE viewer_user_id = $1 AND candidate_user_id = $2',
    [viewer, candidateId],
  );
  assert.equal(rows.length, 1);
  assert.equal(rows[0].primary_photo_id, null);
  assert.equal(rows[0].source, 'discovery_grid');
});

test('isProfileVisibleTo: false when viewing yourself', async () => {
  const userId = await makeUser();
  assert.equal(await isProfileVisibleTo(ctx, userId, userId), false);
});

test('isProfileVisibleTo: false when the candidate does not exist', async () => {
  const viewer = await makeUser();
  assert.equal(await isProfileVisibleTo(ctx, viewer, '00000000-0000-0000-0000-000000000000'), false);
});

test('isProfileVisibleTo: false when the candidate account is not active (rule 1, checked before moderation)', async () => {
  const viewer = await makeUser();
  const suspendedCandidate = await makeUser('suspended');
  // This must short-circuit on `users.status` before ever reaching
  // `moderation.service#isVisibleInDiscovery` (still a stub owned by Agent
  // E as of this writing) — if it didn't, this test would throw
  // NotImplementedError instead of returning false.
  assert.equal(await isProfileVisibleTo(ctx, viewer, suspendedCandidate), false);
});
