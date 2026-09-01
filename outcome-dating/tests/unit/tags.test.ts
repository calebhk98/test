/**
 * DB-backed unit tests for question.service.ts's tag intensity +
 * avoidance CRUD (setMyTagIntensity/getMyTagIntensities/setMyAvoidTags/
 * getMyAvoidTagIds/passesAvoidTagFilterFor). The pure math
 * (scoreTagIntensityMatch/passesAvoidTagFilter) is tested directly,
 * without a database, in tests/unit/questionScoring.test.ts.
 *
 * Runs against its own dedicated `odate_questions_tags` database.
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
import { NotFoundError } from '../../src/lib/errors.js';
import type { Actor, Ctx } from '../../src/lib/ctx.js';
import * as questionService from '../../src/services/question.service.js';

const BASE_URL = process.env.DATABASE_URL ?? 'postgres://outcome_dating@127.0.0.1:55433/outcome_dating';
const TEST_DB_NAME = 'odate_questions_tags';

function withDbName(url: string, dbName: string): string {
  const u = new URL(url);
  u.pathname = `/${dbName}`;
  return u.toString();
}

let adminPool: pg.Pool;
let pool: pg.Pool;
let clock: ManualClock;

before(async () => {
  adminPool = new pg.Pool({ connectionString: BASE_URL });
  await adminPool.query(`DROP DATABASE IF EXISTS ${TEST_DB_NAME}`);
  await adminPool.query(`CREATE DATABASE ${TEST_DB_NAME}`);

  process.env.DATABASE_URL = withDbName(BASE_URL, TEST_DB_NAME);
  await runMigrations();
  pool = getPool();
  clock = new ManualClock(new Date('2026-06-01T12:00:00Z'));
});

after(async () => {
  await closePool();
  await adminPool.query(`DROP DATABASE IF EXISTS ${TEST_DB_NAME}`);
  await adminPool.end();
});

function userActor(userId: string): Actor {
  return { type: 'user', userId, trustLevel: 'standard' };
}

function ctxFor(actor: Actor): Ctx {
  const logger = createSilentLogger();
  return {
    db: pool,
    clock,
    config: new ConfigService(pool, clock, logger),
    flags: new FlagsService(pool, logger),
    logger,
    actor,
    payments: new FakeProcessor(),
    media: new StubMediaModerationAdapter(),
  };
}

let userCounter = 0;
async function makeUser(): Promise<string> {
  userCounter += 1;
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO users (email, password_hash, birthdate, status) VALUES ($1, 'x', '1995-01-01', 'active') RETURNING id`,
    [`tags-${userCounter}-${Date.now()}@test.local`],
  );
  return rows[0]!.id;
}

let tagCounter = 0;
async function makeTag(name: string): Promise<string> {
  tagCounter += 1;
  const uniqueName = `${name} ${tagCounter}`;
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO interest_tags (name, category, public_description) VALUES ($1, 'hobbies', $1) RETURNING id`,
    [uniqueName],
  );
  return rows[0]!.id;
}

async function grantTag(userId: string, tagId: string): Promise<void> {
  await pool.query(`INSERT INTO user_tags (user_id, tag_id, visibility) VALUES ($1, $2, 'public')`, [userId, tagId]);
}

// =====================================================================
// Tag intensity
// =====================================================================

test('setMyTagIntensity / getMyTagIntensities: round-trips and upserts', async () => {
  const userId = await makeUser();
  const tagId = await makeTag('Baking');
  await grantTag(userId, tagId);

  await questionService.setMyTagIntensity(ctxFor(userActor(userId)), tagId, 'occasionally');
  let intensities = await questionService.getMyTagIntensities(ctxFor(userActor(userId)));
  assert.equal(intensities.length, 1);
  assert.equal(intensities[0]!.intensity, 'occasionally');

  // "I bake" daily vs. once a quarter are different, updating must
  // overwrite, not accumulate a second row for the same tag.
  await questionService.setMyTagIntensity(ctxFor(userActor(userId)), tagId, 'daily');
  intensities = await questionService.getMyTagIntensities(ctxFor(userActor(userId)));
  assert.equal(intensities.length, 1);
  assert.equal(intensities[0]!.intensity, 'daily');
});

test('setMyTagIntensity: unknown tag id is a NotFoundError', async () => {
  const userId = await makeUser();
  await assert.rejects(
    () => questionService.setMyTagIntensity(ctxFor(userActor(userId)), '00000000-0000-0000-0000-000000000000', 'daily'),
    NotFoundError,
  );
});

// =====================================================================
// Avoid tags
// =====================================================================

test('setMyAvoidTags / getMyAvoidTagIds: full-replace semantics', async () => {
  const userId = await makeUser();
  const astrology = await makeTag('Astrology');
  const crossfit = await makeTag('CrossFit');

  await questionService.setMyAvoidTags(ctxFor(userActor(userId)), [astrology, crossfit]);
  let ids = await questionService.getMyAvoidTagIds(ctxFor(userActor(userId)));
  assert.deepEqual(new Set(ids), new Set([astrology, crossfit]));

  // Replacing with a smaller set drops what's no longer listed.
  await questionService.setMyAvoidTags(ctxFor(userActor(userId)), [astrology]);
  ids = await questionService.getMyAvoidTagIds(ctxFor(userActor(userId)));
  assert.deepEqual(ids, [astrology]);
});

test('setMyAvoidTags: unknown tag id is a NotFoundError, and nothing is written', async () => {
  const userId = await makeUser();
  const real = await makeTag('Reading');
  await assert.rejects(
    () => questionService.setMyAvoidTags(ctxFor(userActor(userId)), [real, '00000000-0000-0000-0000-000000000000']),
    NotFoundError,
  );
  const ids = await questionService.getMyAvoidTagIds(ctxFor(userActor(userId)));
  assert.deepEqual(ids, [], 'a rejected batch must not partially apply');
});

// =====================================================================
// passesAvoidTagFilterFor, "do not show me people who list astrology"
// behaves like a hard filter (exclusion), tested end-to-end against real
// user_tags/user_avoid_tags rows.
// =====================================================================

test('passesAvoidTagFilterFor: excludes a candidate who holds a tag the viewer avoids', async () => {
  const viewer = await makeUser();
  const candidate = await makeUser();
  const astrology = await makeTag('Astrology');

  await grantTag(candidate, astrology);
  await questionService.setMyAvoidTags(ctxFor(userActor(viewer)), [astrology]);

  const result = await questionService.passesAvoidTagFilterFor(ctxFor(userActor(viewer)), viewer, candidate);
  assert.equal(result.passes, false);
  assert.deepEqual(result.violatingTagIds, [astrology]);
});

test('passesAvoidTagFilterFor: passes when there is no overlap between either side\'s avoid list and the other\'s tags', async () => {
  const viewer = await makeUser();
  const candidate = await makeUser();
  const hiking = await makeTag('Hiking');
  const astrology = await makeTag('Astrology');

  await grantTag(viewer, hiking);
  await grantTag(candidate, astrology); // candidate holds astrology, but viewer never avoided it here

  const result = await questionService.passesAvoidTagFilterFor(ctxFor(userActor(viewer)), viewer, candidate);
  assert.equal(result.passes, true);
});

test('passesAvoidTagFilterFor: bidirectional, a candidate avoiding the viewer\'s tag also excludes', async () => {
  const viewer = await makeUser();
  const candidate = await makeUser();
  const crossfit = await makeTag('CrossFit');

  await grantTag(viewer, crossfit);
  await questionService.setMyAvoidTags(ctxFor(userActor(candidate)), [crossfit]);

  const result = await questionService.passesAvoidTagFilterFor(ctxFor(userActor(viewer)), viewer, candidate);
  assert.equal(result.passes, false);
});
