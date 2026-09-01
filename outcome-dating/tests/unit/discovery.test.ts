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
  // `moderation.service#isVisibleInDiscovery` at all.
  assert.equal(await isProfileVisibleTo(ctx, viewer, suspendedCandidate), false);
});

// =====================================================================
// SCALE FIX end-to-end coverage: getDiscoveryGrid / getRealityDashboard
// through the real, batched `computeRankedCandidatePool` pipeline.
// =====================================================================

interface FullUserOptions {
  age?: number;
  gender?: string;
  relationshipIntention?: string;
  latitude?: number | null;
  longitude?: number | null;
  completeness?: number;
  photo?: 'approved' | 'pending' | 'none';
  status?: 'active' | 'suspended';
  shadowbanned?: boolean;
}

/** A full user + profile (+ approved primary photo by default) — everything `loadCandidatePool`'s weak gate requires, so a candidate is excluded ONLY by whatever this test deliberately varies. */
async function makeFullUser(opts: FullUserOptions = {}): Promise<string> {
  seq++;
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO users (email, password_hash, birthdate, status, shadowbanned)
     VALUES ($1, 'x', '1995-01-01', $2, $3) RETURNING id`,
    [`disc-full-${seq}@test.local`, opts.status ?? 'active', opts.shadowbanned ?? false],
  );
  const userId = rows[0]!.id;
  await pool.query(
    `INSERT INTO profiles (user_id, display_name, city, latitude, longitude, location_fuzzed, age, gender, seeking, relationship_intention, profile_completeness)
     VALUES ($1, $2, 'Testville', $3, $4, true, $5, $6, 'any', $7, $8)`,
    [
      userId,
      `FullUser${seq}`,
      opts.latitude === undefined ? 39.78 : opts.latitude,
      opts.longitude === undefined ? -89.65 : opts.longitude,
      opts.age ?? 30,
      opts.gender ?? 'woman',
      opts.relationshipIntention ?? 'long_term',
      opts.completeness ?? 80,
    ],
  );
  const photo = opts.photo ?? 'approved';
  if (photo !== 'none') {
    await pool.query(
      `INSERT INTO user_photos (user_id, image_url, position, is_primary, moderation_status) VALUES ($1, $2, 0, true, $3)`,
      [userId, 'https://example.test/photo.jpg', photo],
    );
  }
  return userId;
}

async function setHardFilter(userId: string, filterKey: string, operator: string, value: unknown): Promise<void> {
  await pool.query(
    `INSERT INTO hard_filters (user_id, filter_key, operator, value, enabled) VALUES ($1, $2, $3, $4::jsonb, true)`,
    [userId, filterKey, operator, JSON.stringify(value)],
  );
}

async function makeConversation(a: string, b: string, status = 'active'): Promise<void> {
  const [userA, userB] = a < b ? [a, b] : [b, a];
  await pool.query(`INSERT INTO conversations (user_a_id, user_b_id, status) VALUES ($1, $2, $3)`, [userA, userB, status]);
}

async function sendPendingInterest(senderId: string, recipientId: string): Promise<void> {
  await pool.query(
    `INSERT INTO interests (sender_id, recipient_id, status, policy_snapshot, expires_at)
     VALUES ($1, $2, 'pending', '{}'::jsonb, now() + interval '7 days')`,
    [senderId, recipientId],
  );
}

test('getDiscoveryGrid: all nine §10.2 visibility rules are still enforced by the batched pipeline, and agree with isProfileVisibleTo', async () => {
  const viewer = await makeFullUser({ gender: 'woman' });

  const valid = await makeFullUser({ gender: 'man' });
  const rule1Inactive = await makeFullUser({ gender: 'man', status: 'suspended' });
  const rule2Shadowbanned = await makeFullUser({ gender: 'man', shadowbanned: true });
  const rule3Incomplete = await makeFullUser({ gender: 'man', completeness: 10 });
  const rule4NoApprovedPhoto = await makeFullUser({ gender: 'man', photo: 'pending' });

  const rule5IncomingCapped = await makeFullUser({ gender: 'man' });
  for (let i = 0; i < 10; i++) {
    const sender = await makeFullUser({ gender: 'man' });
    await sendPendingInterest(sender, rule5IncomingCapped);
  }

  const rule6ConvoCapped = await makeFullUser({ gender: 'man' });
  for (let i = 0; i < 15; i++) {
    const partner = await makeFullUser({ gender: 'man' });
    await makeConversation(rule6ConvoCapped, partner, 'active');
  }

  const rule7FailsViewerFilter = await makeFullUser({ gender: 'nonbinary' }); // viewer will require gender_preference = 'man'
  const rule8RejectsViewer = await makeFullUser({ gender: 'man' });
  await setHardFilter(rule8RejectsViewer, 'gender_preference', 'eq', 'nonbinary'); // candidate only wants nonbinary; viewer is a woman

  const rule9Blocked = await makeFullUser({ gender: 'man' });
  await blockUser(actorFor(viewer), rule9Blocked);

  await setHardFilter(viewer, 'gender_preference', 'eq', 'man');

  const grid = await getDiscoveryGrid(actorFor(viewer), { limit: 50 });
  const shownIds = new Set(grid.items.map((c) => c.userId));

  assert.ok(shownIds.has(valid), 'the fully-qualifying candidate must appear');

  const excluded: Record<string, string> = {
    rule1_inactive: rule1Inactive,
    rule2_shadowbanned: rule2Shadowbanned,
    rule3_incomplete_profile: rule3Incomplete,
    rule4_no_approved_photo: rule4NoApprovedPhoto,
    rule5_incoming_interest_cap: rule5IncomingCapped,
    rule6_active_conversation_cap: rule6ConvoCapped,
    rule7_fails_viewer_filter: rule7FailsViewerFilter,
    rule8_rejects_viewer: rule8RejectsViewer,
    rule9_blocked: rule9Blocked,
  };

  for (const [label, candidateId] of Object.entries(excluded)) {
    assert.ok(!shownIds.has(candidateId), `${label}: must NOT appear in the discovery grid`);
    // The batched pool-gate must agree with the traceable single-candidate
    // path for the same rule (rule 1 is checked separately above — its own
    // isProfileVisibleTo test already covers it without shadowban/photo
    // noise; skip it here to avoid a redundant, slower assertion).
    if (label !== 'rule1_inactive') {
      assert.equal(
        await isProfileVisibleTo(ctx, viewer, candidateId),
        false,
        `${label}: isProfileVisibleTo must also say false (batched path must not diverge from the traceable one)`,
      );
    }
  }

  assert.equal(await isProfileVisibleTo(ctx, viewer, valid), true, 'the fully-qualifying candidate must also pass isProfileVisibleTo');
});

test('getDiscoveryGrid: a zero-compatibility candidate who passes every filter still appears, sorted last (§10.3/§16.1)', async () => {
  const viewer = await makeFullUser({ gender: 'woman' });

  const goodMatch = await makeFullUser({ gender: 'man' });
  const zeroMatch = await makeFullUser({ gender: 'man' });

  const questionIds: string[] = [];
  for (let i = 0; i < 3; i++) {
    const { rows } = await pool.query<{ id: string }>(
      `INSERT INTO questions (slug, category, question_text, self_left_label, self_right_label, partner_left_label, partner_right_label, weight, polarity, sensitive, active)
       VALUES ($1, 'test', $1, 'l', 'r', 'l', 'r', 1, 'standard', false, true) RETURNING id`,
      [`disc-zero-q${i}-${seq}`],
    );
    questionIds.push(rows[0]!.id);
  }
  for (const qId of questionIds) {
    await pool.query('INSERT INTO answers (user_id, question_id, self_value, partner_value) VALUES ($1, $2, 5, 5)', [viewer, qId]);
    await pool.query('INSERT INTO answers (user_id, question_id, self_value, partner_value) VALUES ($1, $2, 5, 5)', [goodMatch, qId]);
  }
  // zeroMatch never answers anything -> fewer than `minSharedQuestions`
  // shared answers -> compatibility.service's documented default score (0),
  // not a filter failure.

  const grid = await getDiscoveryGrid(actorFor(viewer), { limit: 50 });
  const byId = new Map(grid.items.map((c, i) => [c.userId, i]));

  assert.ok(byId.has(goodMatch), 'the well-matched candidate must appear');
  assert.ok(byId.has(zeroMatch), 'the zero-compatibility candidate must still appear — no compatibility threshold hides anyone');
  assert.ok(byId.get(zeroMatch)! > byId.get(goodMatch)!, 'the zero-compatibility candidate must sort after the well-matched one');
  const zeroCandidate = grid.items.find((c) => c.userId === zeroMatch)!;
  assert.equal(zeroCandidate.compatibilityScore, 0);
});

test('getDiscoveryGrid: a perfect compatibility score never overrides a failed hard filter, through the real batched pipeline', async () => {
  const viewer = await makeFullUser({ age: 30, gender: 'woman' });
  const candidate = await makeFullUser({ age: 50, gender: 'man' }); // outside the age filter set below

  const questionIds: string[] = [];
  for (let i = 0; i < 3; i++) {
    const { rows } = await pool.query<{ id: string }>(
      `INSERT INTO questions (slug, category, question_text, self_left_label, self_right_label, partner_left_label, partner_right_label, weight, polarity, sensitive, active)
       VALUES ($1, 'test', $1, 'l', 'r', 'l', 'r', 1, 'standard', false, true) RETURNING id`,
      [`disc-invariant-q${i}-${seq}`],
    );
    questionIds.push(rows[0]!.id);
  }
  for (const qId of questionIds) {
    for (const userId of [viewer, candidate]) {
      await pool.query('INSERT INTO answers (user_id, question_id, self_value, partner_value) VALUES ($1, $2, 5, 5)', [userId, qId]);
    }
  }

  await setHardFilter(viewer, 'age_max', 'lte', 40);

  const grid = await getDiscoveryGrid(actorFor(viewer), { limit: 50 });
  assert.ok(
    !grid.items.some((c) => c.userId === candidate),
    'a perfect compatibility score must NOT let a hard-filter-failing candidate into the grid',
  );
});

test('getDiscoveryGrid: geographic bounding — a candidate far outside the search radius is excluded, a nearby one is included', async () => {
  const viewer = await makeFullUser({ latitude: 39.78, longitude: -89.65 }); // Springfield, IL, no distance_km filter -> DEFAULT_DISCOVERY_RADIUS_KM
  const nearby = await makeFullUser({ gender: 'man', latitude: 39.8, longitude: -89.6 }); // ~5km away
  const farAway = await makeFullUser({ gender: 'man', latitude: 35.6762, longitude: 139.6503 }); // Tokyo

  const grid = await getDiscoveryGrid(actorFor(viewer), { limit: 50 });
  const shownIds = new Set(grid.items.map((c) => c.userId));

  assert.ok(shownIds.has(nearby), 'a candidate within the default search radius must be included');
  assert.ok(!shownIds.has(farAway), `a candidate thousands of km away (Tokyo) must be excluded by the ${DEFAULT_DISCOVERY_RADIUS_KM}km default radius`);
});

test('getDiscoveryGrid: geographic bounding uses the viewer\'s OWN distance_km filter, not just the default, so it never narrows below what the viewer asked for', async () => {
  const viewer = await makeFullUser({ latitude: 0, longitude: 0 });
  // ~200km from (0,0) — inside a 300km viewer preference, outside the DEFAULT_DISCOVERY_RADIUS_KM (160km) default.
  const farButWithinViewersOwnFilter = await makeFullUser({ gender: 'man', latitude: 1.8, longitude: 0 });
  await setHardFilter(viewer, 'distance_km', 'lte', 300);

  const grid = await getDiscoveryGrid(actorFor(viewer), { limit: 50 });
  assert.ok(
    grid.items.some((c) => c.userId === farButWithinViewersOwnFilter),
    'a candidate beyond the default radius, but within the viewer\'s own larger distance_km preference, must still be reachable',
  );
});

test('getDiscoveryGrid: the geographic bounding-box prefilter does not make a shown distance any more precise than before (SAF-2 stays intact)', async () => {
  const viewer = await makeFullUser({ latitude: 39.78, longitude: -89.65 });
  const candidate = await makeFullUser({ gender: 'man', latitude: 39.8, longitude: -89.66 });

  const grid = await getDiscoveryGrid(actorFor(viewer), { limit: 50 });
  const card = grid.items.find((c) => c.userId === candidate);
  assert.ok(card, 'candidate must be visible for this assertion to be meaningful');

  const expected = approximateDistanceBetween(
    { id: viewer, latitude: 39.78, longitude: -89.65 },
    { id: candidate, latitude: 39.8, longitude: -89.66 },
    {},
  );
  assert.equal(
    card!.approximateDistanceKm,
    expected,
    'must be exactly the SAF-2 coarse-bucketed + pair-jittered value — same function, same inputs, unaffected by the new SQL bounding box',
  );

  // The precision guarantee this test exists to prove: the exposed value
  // must land on the documented coarse bucket grid (a multiple of the
  // effective bucket width — `approximateDistanceBetween` always rounds to
  // one), never an arbitrary-precision exact figure. If the SQL bounding
  // box change had somehow leaked real coordinates into what's shown,
  // this would fail (the exact haversine distance essentially never lands
  // exactly on an 8km grid line).
  const bucketKm = 8; // privacy.distance_bucket_km default (see config.service.ts)
  const shownKm = card!.approximateDistanceKm;
  assert.ok(shownKm !== null, 'both parties have a location on file, so a distance must be shown');
  assert.equal(
    Math.round(shownKm! / bucketKm) * bucketKm,
    shownKm,
    'shown distance must fall exactly on the coarse bucket grid, never a raw exact figure',
  );
});

test('getDiscoveryGrid: pagination — two pages of limit 1 cover the same candidates, in the same order, as one page of limit 2', async () => {
  // Distinctive age band, isolating this test's pool from every other
  // makeFullUser candidate already sitting in this shared per-file test
  // database (same isolation technique as filter.test.ts's reality-
  // dashboard test) — this test cares about ORDERING STABILITY across
  // pages, which an accidental extra leftover candidate could otherwise
  // shuffle in or out of a 2-item page non-deterministically.
  const viewer = await makeFullUser({ gender: 'woman', age: 40 });
  const a = await makeFullUser({ gender: 'man', age: 84 });
  const b = await makeFullUser({ gender: 'man', age: 84 });
  await setHardFilter(viewer, 'age_min', 'gte', 83);
  await setHardFilter(viewer, 'age_max', 'lte', 85);

  const whole = await getDiscoveryGrid(actorFor(viewer), { limit: 2 });
  assert.equal(whole.items.length, 2, 'sanity: exactly this test\'s 2 in-band candidates');
  assert.ok(whole.items.map((c) => c.userId).includes(a));
  assert.ok(whole.items.map((c) => c.userId).includes(b));

  const page1 = await getDiscoveryGrid(actorFor(viewer), { limit: 1 });
  assert.equal(page1.items.length, 1);
  assert.ok(page1.nextCursor, 'a second page must be available');
  const page2 = await getDiscoveryGrid(actorFor(viewer), { limit: 1, cursor: page1.nextCursor! });
  assert.equal(page2.items.length, 1);

  assert.deepEqual(
    [page1.items[0]!.userId, page2.items[0]!.userId],
    whole.items.map((c) => c.userId),
    'paging one-at-a-time must reproduce the same order as a single larger page (stable ordering across pages, data unchanged in between)',
  );
});

test('getDiscoveryGrid: never returns more than MAX_CANDIDATE_POOL_SIZE candidates worth of ranking work', async () => {
  const viewer = await makeFullUser({ gender: 'woman' });
  await makeFullUser({ gender: 'man' });
  const grid = await getDiscoveryGrid(actorFor(viewer), { limit: 100 });
  assert.ok(grid.items.length <= MAX_CANDIDATE_POOL_SIZE);
  assert.ok(MAX_CANDIDATE_POOL_SIZE > 0);
});

test('getRealityDashboard: end-to-end — Z (mutualMatchPool) matches the same batched pool getDiscoveryGrid ranks', async () => {
  const viewer = await makeFullUser({ gender: 'woman' });
  await makeFullUser({ gender: 'man' });
  await makeFullUser({ gender: 'man' });

  const dashboard = await getRealityDashboard(actorFor(viewer));
  const fullGrid = await getDiscoveryGrid(actorFor(viewer), { limit: 100 });

  assert.equal(dashboard.mutualMatchPool, fullGrid.items.length, 'Z must equal the same ranked pool getDiscoveryGrid paginates');
  assert.ok(dashboard.matchesMyFilters >= 0);
  assert.ok(dashboard.whoseFiltersIMatch >= 0);
});
