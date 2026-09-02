/**
 * tests/unit/density.test.ts
 *
 * The population-density discovery fix (docs/capacity.md;
 * src/services/discovery.service.ts#loadCandidatePool's DENSITY FIX doc,
 * src/services/filter.service.ts's matching DENSITY FIX note above
 * `buildStructuredFilterPushdownClause`). Two parts:
 *
 *   1. Pure, no-DB coverage of `buildStructuredFilterPushdownClause`'s
 *      per-operator SQL-generation logic (the "push the cheap, indexable
 *      parts of hard filtering into the SQL" half of the fix).
 *   2. DB-backed tests, against a dedicated `odate_density_unit`
 *      database, that FAIL against the pre-fix behaviour
 *      (`ORDER BY last_active_at DESC ... LIMIT` applied BEFORE hard
 *      filters): a dense, recently-active, filter-failing crowd larger
 *      than the pool cap must never be able to hide a smaller set of
 *      real, filter-passing matches (consequence #2, "filters are
 *      strictly enforced"), and the single highest-compatibility
 *      candidate must appear and rank first regardless of how recently
 *      they were active (consequence #1, "sorts, doesn't hide"). A third
 *      test proves, statistically (large margin, not a coin-flip), that
 *      pool selection is no longer systematically biased toward
 *      recently-active users even when no hard filter differentiates the
 *      population at all.
 *
 * A smaller, cheaper variant of test #1 above also lives in
 * tests/unit/discovery.test.ts, alongside the rest of that pipeline's
 * regression coverage; this file is where the fuller, density-specific
 * suite (including the two DB tests that need populations larger than
 * MAX_CANDIDATE_POOL_SIZE) lives.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import pg from 'pg';
import { randomUUID } from 'node:crypto';
import { runMigrations } from '../../src/db/migrate.js';
import { closePool, getPool } from '../../src/db/pool.js';
import { ConfigService } from '../../src/config/config.service.js';
import { FlagsService } from '../../src/config/flags.service.js';
import { ManualClock } from '../../src/lib/time.js';
import { createSilentLogger } from '../../src/lib/logger.js';
import { FakeProcessor } from '../../src/services/payments/fake.processor.js';
import { StubMediaModerationAdapter } from '../../src/services/media/stub.adapter.js';
import type { Ctx } from '../../src/lib/ctx.js';
import { getDiscoveryGrid, MAX_CANDIDATE_POOL_SIZE } from '../../src/services/discovery.service.js';
import { buildStructuredFilterPushdownClause, type OwnerStructuredFilterRow } from '../../src/services/filter.service.js';

// =====================================================================
// Pure: buildStructuredFilterPushdownClause
// =====================================================================

function filterRow(overrides: Partial<OwnerStructuredFilterRow> & Pick<OwnerStructuredFilterRow, 'filterKey' | 'operator' | 'value'>): OwnerStructuredFilterRow {
  return { excludeIfUnset: false, ...overrides };
}

test('buildStructuredFilterPushdownClause: no filters -> no clause', () => {
  const result = buildStructuredFilterPushdownClause([], 3);
  assert.equal(result.sql, '');
  assert.deepEqual(result.params, []);
});

test('buildStructuredFilterPushdownClause: eq on a text key (gender_preference)', () => {
  const result = buildStructuredFilterPushdownClause([filterRow({ filterKey: 'gender_preference', operator: 'eq', value: 'man' })], 3);
  assert.match(result.sql, /p\.gender IS NULL AND TRUE/);
  assert.match(result.sql, /p\.gender = \$3::text/);
  assert.deepEqual(result.params, ['man']);
});

test('buildStructuredFilterPushdownClause: neq on a text key', () => {
  const result = buildStructuredFilterPushdownClause([filterRow({ filterKey: 'relationship_intention', operator: 'neq', value: 'casual' })], 5);
  assert.match(result.sql, /p\.relationship_intention <> \$5::text/);
  assert.deepEqual(result.params, ['casual']);
});

test('buildStructuredFilterPushdownClause: gte/lte on numeric keys (age_min/age_max), sequential param indices', () => {
  const result = buildStructuredFilterPushdownClause(
    [filterRow({ filterKey: 'age_min', operator: 'gte', value: 25 }), filterRow({ filterKey: 'age_max', operator: 'lte', value: 40 })],
    1,
  );
  assert.match(result.sql, /p\.age >= \$1::numeric/);
  assert.match(result.sql, /p\.age <= \$2::numeric/);
  assert.deepEqual(result.params, [25, 40]);
});

test('buildStructuredFilterPushdownClause: gt/lt on height_cm', () => {
  const result = buildStructuredFilterPushdownClause([filterRow({ filterKey: 'height_cm', operator: 'gt', value: 170 })], 2);
  assert.match(result.sql, /p\.height_cm > \$2::numeric/);
});

test('buildStructuredFilterPushdownClause: in on a numeric key (weight_g), wrapped in the weight_visible guard', () => {
  const result = buildStructuredFilterPushdownClause([filterRow({ filterKey: 'weight_g', operator: 'in', value: [60000, 70000] })], 4);
  assert.match(result.sql, /CASE WHEN p\.weight_visible THEN p\.weight_g ELSE NULL END/);
  assert.match(result.sql, /= ANY\(\$4::numeric\[\]\)/);
  assert.deepEqual(result.params, [[60000, 70000]]);
});

test('buildStructuredFilterPushdownClause: in on a text key (body_type)', () => {
  const result = buildStructuredFilterPushdownClause([filterRow({ filterKey: 'body_type', operator: 'in', value: ['athletic', 'slim'] })], 1);
  assert.match(result.sql, /p\.body_type = ANY\(\$1::text\[\]\)/);
  assert.deepEqual(result.params, [['athletic', 'slim']]);
});

test('buildStructuredFilterPushdownClause: unresolved handling mirrors evaluateFilter (excludeIfUnset true -> unresolved fails, false -> unresolved passes)', () => {
  const strict = buildStructuredFilterPushdownClause([filterRow({ filterKey: 'height_cm', operator: 'gte', value: 170, excludeIfUnset: true })], 1);
  assert.match(strict.sql, /p\.height_cm IS NULL AND FALSE/, 'excludeIfUnset: true -> an unresolved (NULL) column must NOT satisfy the OR-branch');

  const lenient = buildStructuredFilterPushdownClause([filterRow({ filterKey: 'height_cm', operator: 'gte', value: 170, excludeIfUnset: false })], 1);
  assert.match(lenient.sql, /p\.height_cm IS NULL AND TRUE/, 'excludeIfUnset: false (the universal default) -> an unresolved column must satisfy the OR-branch');
});

test('buildStructuredFilterPushdownClause: skips (never pushes) gte/lte/gt/lt against a text key, evaluateFilter never resolves those either', () => {
  const result = buildStructuredFilterPushdownClause([filterRow({ filterKey: 'gender_preference', operator: 'gte', value: 'man' })], 1);
  assert.equal(result.sql, '', 'a nonsensical comparison must be left to the exact downstream check, never guessed at in SQL');
});

test('buildStructuredFilterPushdownClause: skips a malformed `in` value (not an array), matching evaluateFilter\'s "malformed -> always fails"', () => {
  const result = buildStructuredFilterPushdownClause([filterRow({ filterKey: 'body_type', operator: 'in', value: 'not-an-array' })], 1);
  assert.equal(result.sql, '');
});

test('buildStructuredFilterPushdownClause: skips a non-numeric value against a numeric key rather than emitting a broken comparison', () => {
  const result = buildStructuredFilterPushdownClause([filterRow({ filterKey: 'age_min', operator: 'gte', value: 'not-a-number' })], 1);
  assert.equal(result.sql, '');
});

test('buildStructuredFilterPushdownClause: distance_km and qb:-prefixed keys are never pushed (no column expression exists for either)', () => {
  const result = buildStructuredFilterPushdownClause(
    [
      filterRow({ filterKey: 'distance_km', operator: 'lte', value: 50 }),
      filterRow({ filterKey: 'qb:wants_children', operator: 'eq', value: 3 }),
    ],
    1,
  );
  assert.equal(result.sql, '', 'distance_km is handled by the geo box, qb: keys need a join this pushdown deliberately does not attempt');
});

test('buildStructuredFilterPushdownClause: multiple filters AND together with sequential, non-colliding param indices', () => {
  const result = buildStructuredFilterPushdownClause(
    [
      filterRow({ filterKey: 'gender_preference', operator: 'eq', value: 'man' }),
      filterRow({ filterKey: 'age_min', operator: 'gte', value: 25 }),
    ],
    7,
  );
  assert.match(result.sql, /\$7::text/);
  assert.match(result.sql, /\$8::numeric/);
  assert.ok(result.sql.includes(' AND ('), 'the two predicates must be ANDed together');
  assert.deepEqual(result.params, ['man', 25]);
});

// =====================================================================
// DB-backed: the defect, reproduced at density
// =====================================================================

const BASE_URL = process.env.DATABASE_URL ?? 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';
const TEST_DB_NAME = 'odate_density_unit';

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
}, { timeout: 60_000 });

after(async () => {
  await closePool();
  await adminPool.query(`DROP DATABASE IF EXISTS ${TEST_DB_NAME}`);
  await adminPool.end();
});

function actorFor(userId: string): Ctx {
  return { ...ctx, actor: { type: 'user', userId, trustLevel: 'standard' } };
}

async function makeCandidate(opts: {
  gender?: string;
  latitude?: number;
  longitude?: number;
  minutesAgo?: number;
  completeness?: number;
}): Promise<string> {
  const id = randomUUID();
  await pool.query(
    `INSERT INTO users (id, email, password_hash, birthdate, status, last_active_at)
     VALUES ($1, $2, 'x', '1995-01-01', 'active', now() - ($3 || ' minutes')::interval)`,
    [id, `density-cand-${id}@test.local`, opts.minutesAgo ?? 0],
  );
  await pool.query(
    `INSERT INTO profiles (user_id, display_name, city, latitude, longitude, location_fuzzed, age, gender, seeking, relationship_intention, profile_completeness)
     VALUES ($1, $2, 'Testville', $3, $4, true, 30, $5, 'any', 'long_term', $6)`,
    [id, `Cand${id.slice(0, 8)}`, opts.latitude ?? 0, opts.longitude ?? 0, opts.gender ?? 'man', opts.completeness ?? 80],
  );
  await pool.query(
    `INSERT INTO user_photos (user_id, image_url, position, is_primary, moderation_status) VALUES ($1, $2, 0, true, 'approved')`,
    [id, 'https://example.test/photo.jpg'],
  );
  return id;
}

/** Bulk (`unnest`) equivalent of `makeCandidate` for populations too large to insert one row at a time in a reasonable test runtime. */
async function bulkMakeCandidates(opts: { count: number; gender: string; latitude: number; longitude: number; minutesAgo: number }): Promise<string[]> {
  const ids = Array.from({ length: opts.count }, () => randomUUID());
  const emails = ids.map((id) => `density-bulk-${id}@test.local`);
  const minutesAgo = ids.map(() => opts.minutesAgo);
  await pool.query(
    `INSERT INTO users (id, email, password_hash, birthdate, status, last_active_at)
     SELECT u.id, u.email, 'x', '1995-01-01', 'active', now() - (u.minutes_ago || ' minutes')::interval
     FROM unnest($1::uuid[], $2::text[], $3::int[]) AS u(id, email, minutes_ago)`,
    [ids, emails, minutesAgo],
  );
  const names = ids.map((id) => `Bulk${id.slice(0, 8)}`);
  await pool.query(
    `INSERT INTO profiles (user_id, display_name, city, latitude, longitude, location_fuzzed, age, gender, seeking, relationship_intention, profile_completeness)
     SELECT t.id, t.name, 'Testville', $2::double precision, $3::double precision, true, 30, $4::text, 'any', 'long_term', 80
     FROM unnest($1::uuid[], $5::text[]) AS t(id, name)`,
    [ids, opts.latitude, opts.longitude, opts.gender, names],
  );
  await pool.query(
    `INSERT INTO user_photos (user_id, image_url, position, is_primary, moderation_status)
     SELECT id, 'https://example.test/' || id || '.jpg', 0, true, 'approved' FROM unnest($1::uuid[]) AS t(id)`,
    [ids],
  );
  return ids;
}

async function setHardFilter(userId: string, filterKey: string, operator: string, value: unknown): Promise<void> {
  await pool.query(`INSERT INTO hard_filters (user_id, filter_key, operator, value, enabled) VALUES ($1, $2, $3, $4::jsonb, true)`, [
    userId,
    filterKey,
    operator,
    JSON.stringify(value),
  ]);
}

let qSeq = 0;
/** Gives every user in `userIds` matching, high-value answers to `count` freshly-created scale questions, so they score well against each other in compatibility.service.ts (unchanged, not owned by this build). */
async function giveMatchingAnswers(userIds: string[], count: number): Promise<void> {
  for (let i = 0; i < count; i++) {
    qSeq++;
    const slug = `density-q${qSeq}`;
    const { rows } = await pool.query<{ id: string }>(
      `INSERT INTO question_bank (slug, version, is_current, category, subcategory, tags, question_type, question_text, type_definition, base_weight, sensitive, active, answer_rate_hint)
       VALUES ($1, 1, true, 'test', NULL, '{}', 'scale', $1, $2::jsonb, 1, false, true, 0.5) RETURNING id`,
      [slug, JSON.stringify({ type: 'scale', min: 1, max: 5, minLabel: 'low', maxLabel: 'high', midLabel: 'mid' })],
    );
    const questionBankId = rows[0]!.id;
    for (const userId of userIds) {
      await pool.query(
        `INSERT INTO user_question_answers (user_id, question_slug, question_bank_id, status, self_value, preference_value, importance, answered_at, updated_at)
         VALUES ($1, $2, $3, 'answered', '5'::jsonb, '5'::jsonb, 'important', now(), now())`,
        [userId, slug, questionBankId],
      );
    }
  }
}

/** Walks every page of getDiscoveryGrid (capped at MAX_PAGE_LIMIT=100 per call) to reconstruct the full, up-to-MAX_CANDIDATE_POOL_SIZE ranked pool. */
async function collectFullPool(viewerCtx: Ctx): Promise<string[]> {
  const ids: string[] = [];
  let cursor: string | undefined;
  for (let i = 0; i < 10; i++) {
    const page = await getDiscoveryGrid(viewerCtx, { limit: 100, cursor });
    ids.push(...page.items.map((c) => c.userId));
    if (!page.nextCursor) break;
    cursor = page.nextCursor;
  }
  return ids;
}

test(
  'getDiscoveryGrid: the highest-compatibility candidate appears and ranks FIRST even though they are the least recently active in the whole pool (consequence #1 + #2)',
  { timeout: 60_000 },
  async () => {
    const viewer = await makeCandidate({ gender: 'woman', latitude: 20, longitude: 20, completeness: 90 });
    await setHardFilter(viewer, 'gender_preference', 'eq', 'man');

    // A crowd larger than the pool cap, recently active, but failing the
    // viewer's gender filter: pre-fix, this alone fills the entire
    // recency-ordered LIMIT before the filter is ever applied.
    await bulkMakeCandidates({ count: MAX_CANDIDATE_POOL_SIZE + 10, gender: 'woman', latitude: 20, longitude: 20, minutesAgo: 1 });

    // Real, filter-passing matches, all far less recently active than
    // every crowd member above. `bestMatch` shares answers with the
    // viewer (real compatibility); `otherReal` do not (zero compatibility,
    // same as the pre-existing §10.3 "zero score still shown" invariant).
    const bestMatch = await makeCandidate({ gender: 'man', latitude: 20, longitude: 20, minutesAgo: 60 * 24 * 400 });
    const otherReal = await Promise.all(
      Array.from({ length: 3 }, () => makeCandidate({ gender: 'man', latitude: 20, longitude: 20, minutesAgo: 60 * 24 * 400 })),
    );
    await giveMatchingAnswers([viewer, bestMatch], 3);

    const grid = await getDiscoveryGrid(actorFor(viewer), { limit: 50 });
    const shownIds = new Set(grid.items.map((c) => c.userId));

    assert.ok(shownIds.has(bestMatch), 'the best-compatibility candidate must appear, not be truncated away by a larger, more recently active, filter-failing crowd');
    for (const id of otherReal) {
      assert.ok(shownIds.has(id), 'every filter-passing candidate must appear, not just the single best one');
    }

    const bestCard = grid.items.find((c) => c.userId === bestMatch)!;
    assert.ok(bestCard.compatibilityScore > 0, 'sanity: the shared answers must actually produce a nonzero compatibility score');
    assert.equal(grid.items[0]!.userId, bestMatch, 'the highest-compatibility candidate must sort FIRST, exactly as if recency had never been a factor in whether they were even considered');
  },
);

test(
  'getDiscoveryGrid: candidate-pool selection is not systematically biased toward recently-active users when the eligible population exceeds the pool cap, even with no hard filter to distinguish anyone (statistical, large margin)',
  { timeout: 60_000 },
  async () => {
    const viewer = await makeCandidate({ gender: 'woman', latitude: 30, longitude: 30 });
    // No hard filters at all: every candidate below is equally eligible,
    // isolating the pool-SELECTION ordering itself (not the filter
    // pushdown, covered by the other DB tests in this file and in
    // discovery.test.ts) as the only thing that can bias who is seen.

    const RECENT_COUNT = MAX_CANDIDATE_POOL_SIZE; // exactly fills the cap on its own
    const OLD_COUNT = 100;
    const oldGroup = await bulkMakeCandidates({ count: OLD_COUNT, gender: 'man', latitude: 30, longitude: 30, minutesAgo: 60 * 24 * 400 });
    await bulkMakeCandidates({ count: RECENT_COUNT, gender: 'man', latitude: 30, longitude: 30, minutesAgo: 1 });
    const oldGroupSet = new Set(oldGroup);

    const pooled = await collectFullPool(actorFor(viewer));
    assert.ok(pooled.length <= MAX_CANDIDATE_POOL_SIZE, 'the pool must still respect the cap');

    const oldShown = pooled.filter((id) => oldGroupSet.has(id)).length;

    // Pre-fix (recency DESC, LIMIT MAX_CANDIDATE_POOL_SIZE), the RECENT_COUNT
    // group alone exactly fills the cap: this specific construction makes
    // the old-code failure mode deterministic (oldShown === 0), not just
    // likely. Post-fix, pool order is a static per-row shuffle key
    // uncorrelated with recency: the expected old-group representation is
    // ~83 (500 draws out of 600, ~16.7% old), and the probability of
    // drawing fewer than 20 by chance is astronomically small (many
    // standard deviations from the mean), so this assertion is safe, not
    // a coin flip.
    assert.ok(
      oldShown >= 20,
      `expected substantial representation from the least-recently-active group (got ${oldShown}/${OLD_COUNT}); ` +
        'a low or zero count here means pool selection is still effectively recency-ordered',
    );
  },
);
