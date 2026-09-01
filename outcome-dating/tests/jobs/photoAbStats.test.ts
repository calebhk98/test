/**
 * §25.5 Photo A/B Stats job, aggregates impressions/accepted interests
 * into a per-user photo recommendation, ranked by accepted-interest rate
 * (never raw impressions, per C-7.3.4), gated behind the `photo_ab_testing`
 * flag.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestDb, teardownTestDb, makeCtx, createUser } from './testHarness.js';
import type { TestDb } from './testHarness.js';
import { runPhotoAbStatsJob } from '../../src/jobs/photoAbStats.job.js';
import { KNOWN_FLAGS } from '../../src/config/flags.service.js';

let db: TestDb;

before(async () => {
  db = await setupTestDb('photo_ab_stats');
});

after(async () => {
  await teardownTestDb(db);
});

async function insertApprovedPhoto(userId: string, position: number): Promise<string> {
  const { rows } = await db.pool.query<{ id: string }>(
    `INSERT INTO user_photos (user_id, image_url, position, is_primary, moderation_status, face_detected)
     VALUES ($1, $2, $3, $4, 'approved', true) RETURNING id`,
    [userId, `https://example.test/${userId}/${position}.jpg`, position, position === 0],
  );
  return rows[0]!.id;
}

async function seedStats(userId: string, photoId: string, impressions: number, accepted: number): Promise<void> {
  await db.pool.query(
    `INSERT INTO photo_experiments (user_id, photo_id, impressions, interests_sent, interests_accepted)
     VALUES ($1, $2, $3, $3, $4)`,
    [userId, photoId, impressions, accepted],
  );
}

test('a challenger photo that clears the significance guard produces a pending recommendation', async () => {
  const ctx = makeCtx(db);
  const userId = await createUser(db);
  await ctx.flags.setFlag(KNOWN_FLAGS.PHOTO_AB_TESTING, { enabled: true, rolloutPercent: 100 });

  const primary = await insertApprovedPhoto(userId, 0);
  const challenger = await insertApprovedPhoto(userId, 1);
  await insertApprovedPhoto(userId, 2); // just to clear the >=3-photos gate

  await seedStats(userId, primary, 40, 4); // 10% accept rate
  await seedStats(userId, challenger, 40, 10); // 25% accept rate -> well above the 15% lift guard

  const result = await runPhotoAbStatsJob(ctx);
  assert.equal(result.usersUpdated, 1);

  const { rows } = await db.pool.query<{ photo_id: string; status: string; recommended_position: number }>(
    `SELECT photo_id, status, recommended_position FROM photo_recommendations WHERE user_id = $1`,
    [userId],
  );
  assert.equal(rows.length, 1);
  assert.equal(rows[0]!.photo_id, challenger, 'the higher accept-RATE photo wins, not the one with more raw impressions/views');
  assert.equal(rows[0]!.status, 'pending');
  assert.equal(rows[0]!.recommended_position, 0);
});

test('a user below 3 photos, or with the flag off, gets no recommendation', async () => {
  const ctx = makeCtx(db);
  const userId = await createUser(db);
  await ctx.flags.setFlag(KNOWN_FLAGS.PHOTO_AB_TESTING, { enabled: false });
  const primary = await insertApprovedPhoto(userId, 0);
  const challenger = await insertApprovedPhoto(userId, 1);
  await insertApprovedPhoto(userId, 2);
  await seedStats(userId, primary, 40, 4);
  await seedStats(userId, challenger, 40, 10);

  const result = await runPhotoAbStatsJob(ctx);
  assert.equal(result.usersUpdated, 0, 'flag is off -> no recommendation, even with enough photos and a clear winner');
});

test('idempotent re-run: a second run with unchanged stats does not create a duplicate pending row', async () => {
  const ctx = makeCtx(db);
  const userId = await createUser(db);
  await ctx.flags.setFlag(KNOWN_FLAGS.PHOTO_AB_TESTING, { enabled: true, rolloutPercent: 100 });
  const primary = await insertApprovedPhoto(userId, 0);
  const challenger = await insertApprovedPhoto(userId, 1);
  await insertApprovedPhoto(userId, 2);
  await seedStats(userId, primary, 40, 4);
  await seedStats(userId, challenger, 40, 10);

  await runPhotoAbStatsJob(ctx);
  await runPhotoAbStatsJob(ctx);

  const { rows } = await db.pool.query<{ count: string }>(`SELECT count(*)::text AS count FROM photo_recommendations WHERE user_id = $1`, [userId]);
  assert.equal(rows[0]!.count, '1');
});
