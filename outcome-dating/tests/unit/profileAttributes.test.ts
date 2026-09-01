/**
 * Unit tests for this build's physical-attribute + units additions to
 * profile.service.ts and filter.service.ts: height/weight/body-type
 * profile fields, the unit preference, hidden weight, and the
 * `excludeIfUnset` per-filter toggle (including its pool-count preview).
 *
 * Uses its own dedicated Postgres database (`odate_units_profileattributes`
 * — lowercase: an unquoted `CREATE DATABASE` identifier is case-folded by
 * Postgres, so the name used to reconnect must already be lowercase — per
 * the build brief: one database per test file, `odate_units_<suite>`
 * naming, never shared with a sibling agent's own test database).
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
import * as profile from '../../src/services/profile.service.js';
import {
  updateMyFilters,
  passesMutualFilters,
  previewPoolSizeWithUnsetPolicy,
  defaultExcludeIfUnset,
} from '../../src/services/filter.service.js';
import { ValidationError } from '../../src/lib/errors.js';
import { ZodError } from 'zod';

const BASE_URL = process.env.DATABASE_URL ?? 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';
const TEST_DB_NAME = 'odate_units_profileattributes';

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
async function makeBareUser(): Promise<string> {
  seq++;
  const email = `attrs-user-${seq}@test.local`;
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO users (email, password_hash, birthdate, status) VALUES ($1, 'x', '1995-01-01', 'active') RETURNING id`,
    [email],
  );
  return rows[0]!.id;
}

/** Full profile via the service (not raw SQL) so completeness/validation paths are exercised. */
async function makeUserWithProfile(overrides: Partial<profile.UpdateProfileInput> = {}): Promise<string> {
  const userId = await makeBareUser();
  const userCtx = actorFor(userId);
  await profile.updateMyProfile(userCtx, {
    displayName: `Attrs${seq}`,
    age: 30,
    gender: 'woman',
    seeking: 'man',
    relationshipIntention: 'long_term',
    latitude: 10,
    longitude: 10,
    ...overrides,
  });
  return userId;
}

// =====================================================================
// Profile fields: storage, optionality.
// =====================================================================

test('updateMyProfile: height/weight/bodyType/unitPreference are optional — a profile with none of them set is valid', async () => {
  const userId = await makeUserWithProfile();
  const p = await profile.getMyProfile(actorFor(userId));
  assert.equal(p.heightCm, null);
  assert.equal(p.weightG, null);
  assert.equal(p.bodyType, null);
  assert.equal(p.weightVisible, true, 'defaults to visible');
  assert.equal(p.unitPreference, 'metric', 'documented default: no locale signal exists, so metric');
});

test('updateMyProfile: stores height/weight/bodyType canonically and round-trips through getMyProfile', async () => {
  const userId = await makeUserWithProfile({ heightCm: 178, weightG: 68000, bodyType: 'athletic' });
  const p = await profile.getMyProfile(actorFor(userId));
  assert.equal(p.heightCm, 178);
  assert.equal(p.weightG, 68000);
  assert.equal(p.bodyType, 'athletic');
});

test('updateMyProfile: rejects an out-of-range height/weight and an unknown bodyType', async () => {
  // `UpdateProfileSchema.parse(...)` (not `safeParse`) is this codebase's
  // established convention across every service — see auth.service.ts,
  // appeal.service.ts, dateProposal.service.ts, filter.service.ts, etc.,
  // all of which let a raw `ZodError` propagate on invalid input rather
  // than wrapping it in `ValidationError`. This build's new fields follow
  // the same convention rather than inventing a different one.
  const userId = await makeBareUser();
  const userCtx = actorFor(userId);
  await assert.rejects(
    () => profile.updateMyProfile(userCtx, { displayName: 'X', age: 30, gender: 'woman', seeking: 'man', relationshipIntention: 'long_term', heightCm: 5 }),
    ZodError,
  );
  await assert.rejects(
    () => profile.updateMyProfile(userCtx, { displayName: 'X', age: 30, gender: 'woman', seeking: 'man', relationshipIntention: 'long_term', weightG: 1 }),
    ZodError,
  );
  await assert.rejects(
    () =>
      profile.updateMyProfile(userCtx, {
        displayName: 'X',
        age: 30,
        gender: 'woman',
        seeking: 'man',
        relationshipIntention: 'long_term',
        // @ts-expect-error — deliberately an invalid bodyType to prove the zod schema rejects it at runtime.
        bodyType: 'not-a-real-body-type',
      }),
    ZodError,
  );
});

test('changing unitPreference does not alter any stored measurement value', async () => {
  const userId = await makeUserWithProfile({ heightCm: 165, weightG: 55000, unitPreference: 'metric' });
  const userCtx = actorFor(userId);

  const before = await profile.getMyProfile(userCtx);
  assert.equal(before.heightCm, 165);
  assert.equal(before.weightG, 55000);
  assert.equal(before.unitPreference, 'metric');

  await profile.updateMyProfile(userCtx, { unitPreference: 'imperial' });

  const after = await profile.getMyProfile(userCtx);
  assert.equal(after.unitPreference, 'imperial');
  assert.equal(after.heightCm, 165, 'stored height must be untouched by a preference change');
  assert.equal(after.weightG, 55000, 'stored weight must be untouched by a preference change');
});

// =====================================================================
// Hidden weight: structurally absent from PublicProfileView, not masked.
// =====================================================================

test('PublicProfileView: weightG is present when visible, and structurally ABSENT (not null, not present) when hidden', async () => {
  const viewerId = await makeUserWithProfile();
  const visibleId = await makeUserWithProfile({ weightG: 72000, weightVisible: true });
  const hiddenId = await makeUserWithProfile({ weightG: 72000, weightVisible: false });
  const viewerCtx = actorFor(viewerId);

  const visibleView = await profile.buildPublicProfileView(viewerCtx, viewerId, visibleId);
  assert.equal(visibleView.weightG, 72000);
  assert.ok(Object.prototype.hasOwnProperty.call(visibleView, 'weightG'));

  const hiddenView = await profile.buildPublicProfileView(viewerCtx, viewerId, hiddenId);
  assert.equal(
    Object.prototype.hasOwnProperty.call(hiddenView, 'weightG'),
    false,
    'a hidden weight must be omitted from the view entirely, not sent as null/masked',
  );
  assert.equal((hiddenView as unknown as Record<string, unknown>).weightG, undefined);
});

test('PublicProfileView: an unset (never-provided) weight is also structurally absent, distinct from "hidden but set"', async () => {
  const viewerId = await makeUserWithProfile();
  const neverSetId = await makeUserWithProfile(); // weightVisible defaults true, but weightG was never set
  const view = await profile.buildPublicProfileView(actorFor(viewerId), viewerId, neverSetId);
  assert.equal(Object.prototype.hasOwnProperty.call(view, 'weightG'), false);
});

test('PublicProfileView: height and bodyType are always present (no hide toggle for either) once set', async () => {
  const viewerId = await makeUserWithProfile();
  const targetId = await makeUserWithProfile({ heightCm: 190, bodyType: 'muscular' });
  const view = await profile.buildPublicProfileView(actorFor(viewerId), viewerId, targetId);
  assert.equal(view.heightCm, 190);
  assert.equal(view.bodyType, 'muscular');
});

// =====================================================================
// Filters: compare canonically, ignore either party's display preference.
// =====================================================================

test('height filter compares canonical centimetres regardless of either user\'s unitPreference', async () => {
  // Viewer prefers imperial, candidate prefers metric — neither preference
  // may leak into the comparison, which must be pure centimetres either way.
  const viewer = await makeUserWithProfile({ unitPreference: 'imperial' });
  const tallEnough = await makeUserWithProfile({ heightCm: 183, unitPreference: 'metric' }); // 6'0"
  const tooShort = await makeUserWithProfile({ heightCm: 160, unitPreference: 'metric' });

  await updateMyFilters(actorFor(viewer), [{ filterKey: 'height_cm', operator: 'gte', value: 180, enabled: true }]);

  assert.equal(await passesMutualFilters(ctx, viewer, tallEnough), true);
  assert.equal(await passesMutualFilters(ctx, viewer, tooShort), false);
});

test('weight filter compares canonical grams regardless of either user\'s unitPreference', async () => {
  const viewer = await makeUserWithProfile({ unitPreference: 'metric' });
  const lightEnough = await makeUserWithProfile({ weightG: 60000, unitPreference: 'imperial' }); // ~132 lb
  const tooHeavy = await makeUserWithProfile({ weightG: 110000, unitPreference: 'imperial' }); // ~242 lb

  await updateMyFilters(actorFor(viewer), [{ filterKey: 'weight_g', operator: 'lte', value: 90000, enabled: true }]);

  assert.equal(await passesMutualFilters(ctx, viewer, lightEnough), true);
  assert.equal(await passesMutualFilters(ctx, viewer, tooHeavy), false);
});

test('body type preference is a SET of acceptable values (the `in` operator), never a numeric midpoint', async () => {
  const viewer = await makeUserWithProfile();
  const athletic = await makeUserWithProfile({ bodyType: 'athletic' });
  const slim = await makeUserWithProfile({ bodyType: 'slim' });
  const curvy = await makeUserWithProfile({ bodyType: 'curvy' });

  await updateMyFilters(actorFor(viewer), [
    { filterKey: 'body_type', operator: 'in', value: ['athletic', 'slim'], enabled: true },
  ]);

  assert.equal(await passesMutualFilters(ctx, viewer, athletic), true);
  assert.equal(await passesMutualFilters(ctx, viewer, slim), true);
  assert.equal(await passesMutualFilters(ctx, viewer, curvy), false);
});

test('updateMyFilters: rejects a body_type filter value outside the canonical BODY_TYPES list', async () => {
  const viewer = await makeUserWithProfile();
  await assert.rejects(
    () =>
      updateMyFilters(actorFor(viewer), [
        { filterKey: 'body_type', operator: 'in', value: ['not-a-real-type'], enabled: true },
      ]),
    ValidationError,
  );
});

// =====================================================================
// Missing optional attributes + excludeIfUnset: default false (included)
// for every filter key, toggled true (excluded) only on explicit request
// — including a simulated deal-breaker-derived filter.
// =====================================================================

for (const key of ['height_cm', 'weight_g', 'body_type'] as const) {
  test(`${key} filter: defaultExcludeIfUnset is false, and a candidate with the attribute unset is INCLUDED by default`, async () => {
    assert.equal(defaultExcludeIfUnset(key), false);

    const viewer = await makeUserWithProfile();
    const unset = await makeUserWithProfile(); // never sets height/weight/bodyType

    const filterValue = key === 'body_type' ? ['athletic'] : 100000; // an unreachable-but-well-formed threshold; irrelevant since candidateValue resolves to undefined either way
    const operator = key === 'body_type' ? ('in' as const) : ('lte' as const);

    await updateMyFilters(actorFor(viewer), [{ filterKey: key, operator, value: filterValue, enabled: true }]);

    assert.equal(
      await passesMutualFilters(ctx, viewer, unset),
      true,
      `${key}: a candidate who never set this attribute must not be excluded by default`,
    );
  });

  test(`${key} filter: turning excludeIfUnset ON excludes a candidate with the attribute unset`, async () => {
    const viewer = await makeUserWithProfile();
    const unset = await makeUserWithProfile();

    const filterValue = key === 'body_type' ? ['athletic'] : 100000;
    const operator = key === 'body_type' ? ('in' as const) : ('lte' as const);

    await updateMyFilters(actorFor(viewer), [
      { filterKey: key, operator, value: filterValue, enabled: true, excludeIfUnset: true },
    ]);

    assert.equal(
      await passesMutualFilters(ctx, viewer, unset),
      false,
      `${key}: excludeIfUnset:true must exclude a candidate with the attribute unset`,
    );
  });
}

test('excludeIfUnset toggle never mutates any stored profile attribute value', async () => {
  const viewer = await makeUserWithProfile();
  const candidate = await makeUserWithProfile({ heightCm: 170 });

  await updateMyFilters(actorFor(viewer), [
    { filterKey: 'height_cm', operator: 'gte', value: 150, enabled: true, excludeIfUnset: false },
  ]);
  const before = await profile.getMyProfile(actorFor(candidate));

  await updateMyFilters(actorFor(viewer), [
    { filterKey: 'height_cm', operator: 'gte', value: 150, enabled: true, excludeIfUnset: true },
  ]);
  const after = await profile.getMyProfile(actorFor(candidate));

  assert.equal(after.heightCm, before.heightCm, 'flipping the toggle must not touch the candidate\'s stored height');
});

test('a simulated deal-breaker-derived filter defaults to INCLUDING an unset value, and only excludes once the toggle is explicitly turned on', async () => {
  // "Deal breaker" filters are derived by another agent's code
  // (src/domain/questions/), but from filter.service's point of view a
  // deal-breaker-derived row is just an UpdateFilterInput like any other
  // — this simulates that derivation calling updateMyFilters directly.
  const viewer = await makeUserWithProfile();
  const neverAnswered = await makeUserWithProfile(); // no user_question_answers row at all -> unresolved for any qb:-prefixed key

  await updateMyFilters(actorFor(viewer), [
    { filterKey: 'qb:smoking', operator: 'lte', value: 2, enabled: true }, // excludeIfUnset omitted entirely, as a fresh derivation might do before the user opts in
  ]);
  assert.equal(
    await passesMutualFilters(ctx, viewer, neverAnswered),
    true,
    'a brand-new account that has not answered the underlying question must still be discoverable',
  );

  await updateMyFilters(actorFor(viewer), [{ filterKey: 'qb:smoking', operator: 'lte', value: 2, enabled: true, excludeIfUnset: true }]);
  assert.equal(
    await passesMutualFilters(ctx, viewer, neverAnswered),
    false,
    'once the user explicitly asks this deal-breaker to be strict about unknowns, it must exclude them',
  );
});

// =====================================================================
// Pool-count preview: the toggle's effect must be visible before commit.
// =====================================================================

test('previewPoolSizeWithUnsetPolicy: shows the cost of turning excludeIfUnset on, without writing anything', async () => {
  const viewer = await makeUserWithProfile();
  const withHeight = await makeUserWithProfile({ heightCm: 200 });
  const unset1 = await makeUserWithProfile();
  const unset2 = await makeUserWithProfile();

  await updateMyFilters(actorFor(viewer), [{ filterKey: 'height_cm', operator: 'gte', value: 150, enabled: true }]);

  const poolIncluding = await previewPoolSizeWithUnsetPolicy(ctx, viewer, 'height_cm', false);
  const poolExcluding = await previewPoolSizeWithUnsetPolicy(ctx, viewer, 'height_cm', true);

  assert.ok(poolExcluding < poolIncluding, 'turning exclusion on must shrink (never grow) the pool');

  // The viewer's only enabled filter is height_cm, so the delta between
  // the two previews is EXACTLY the count of other active users whose
  // height_cm is unresolved (NULL) — flipping excludeIfUnset changes
  // nothing about how a RESOLVED height is compared, only how an
  // unresolved one is treated. Computed live (not hardcoded) because
  // this is a per-FILE shared database: earlier tests in this file have
  // already created other users, most of them also height-unset, so the
  // real delta is larger than just this test's own 2 fixtures — the
  // point being tested is that it equals the live count, not a fixed
  // small number (mirrors filter.test.ts's own "reality dashboard"
  // test's live-query style for the same reason).
  // LEFT JOIN (not JOIN): a user with NO profile row at all also resolves
  // as unset for height_cm (loadProfile returns undefined), and a couple
  // of earlier tests in this file create bare users with no profile —
  // those must be counted here too, or this query would undercount
  // relative to what previewPoolSizeWithUnsetPolicy actually iterates
  // (every active user, profile or not).
  const { rows } = await pool.query<{ count: string }>(
    `SELECT count(*)::text AS count FROM users u LEFT JOIN profiles p ON p.user_id = u.id
     WHERE u.status = 'active' AND u.id <> $1 AND p.height_cm IS NULL`,
    [viewer],
  );
  const expectedDelta = Number(rows[0]!.count);
  assert.equal(poolIncluding - poolExcluding, expectedDelta, 'the delta must equal exactly the count of other active users with an unresolved height');
  assert.ok(expectedDelta >= 2, 'sanity: at least this test\'s own 2 unset-height fixtures are among them');

  // Nothing was written: the filter's actual persisted excludeIfUnset is
  // still whatever updateMyFilters set it to (the default: false).
  const stillIncluded = await passesMutualFilters(ctx, viewer, unset1);
  assert.equal(stillIncluded, true, 'previewing must not have persisted the excludeIfUnset:true override');
  void withHeight;
  void unset2;
});
