import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestDatabase, teardownTestDatabase, getTestPool, buildCtx, userActor, insertUser } from './testCtx.js';
import * as photo from '../../src/services/photo.service.js';
import * as photoExperiment from '../../src/services/photoExperiment.service.js';
import { computeRecommendation } from '../../src/services/photoExperiment.service.js';
import { KNOWN_FLAGS } from '../../src/config/flags.service.js';
import { ForbiddenError, NotFoundError, ValidationError } from '../../src/lib/errors.js';

before(async () => {
  await setupTestDatabase('photoexperiment');
});

after(async () => {
  await teardownTestDatabase();
});

const NOW = new Date();
let urlCounter = 0;
function uniqueUrl(tag: string): string {
  urlCounter += 1;
  return `https://example.test/${tag}-${urlCounter}.jpg`;
}

async function createUser(): Promise<string> {
  return insertUser('experimentuser');
}

/** Uploads `count` distinct approved photos for `userId` and returns them in position order. */
async function uploadApprovedPhotos(userId: string, count: number) {
  const ctx = buildCtx({ now: NOW, actor: userActor(userId) });
  const photos = [];
  for (let i = 0; i < count; i++) {
    photos.push(await photo.uploadPhoto(ctx, { imageUrl: uniqueUrl(`p${i}`) }));
  }
  return photos;
}

async function enablePhotoAbTesting(): Promise<void> {
  const pool = getTestPool();
  await pool.query(
    `INSERT INTO feature_flags (key, enabled, rollout_percent, segments, updated_at)
     VALUES ($1, true, 100, '{}', now())
     ON CONFLICT (key) DO UPDATE SET enabled = true, rollout_percent = 100`,
    [KNOWN_FLAGS.PHOTO_AB_TESTING],
  );
}

// =====================================================================
// computeRecommendation, pure significance-guard logic
// =====================================================================

test('computeRecommendation: requires at least 3 photos', () => {
  const rec = computeRecommendation([
    { photoId: 'a', position: 0, impressions: 100, interestsAccepted: 20 },
    { photoId: 'b', position: 1, impressions: 100, interestsAccepted: 5 },
  ]);
  assert.equal(rec, null);
});

test('computeRecommendation: below the impression floor produces no recommendation, regardless of apparent lift', () => {
  const rec = computeRecommendation([
    { photoId: 'primary', position: 0, impressions: 2, interestsAccepted: 0 },
    { photoId: 'challenger', position: 1, impressions: 2, interestsAccepted: 1 }, // 50% "rate" on n=2, noise, not signal
    { photoId: 'third', position: 2, impressions: 100, interestsAccepted: 10 },
  ]);
  assert.equal(rec, null, 'the primary itself lacks enough impressions to establish a baseline');
});

test('computeRecommendation: a challenger with too few accepted interests is not recommended even with high apparent lift', () => {
  const rec = computeRecommendation([
    { photoId: 'primary', position: 0, impressions: 100, interestsAccepted: 5 },
    { photoId: 'challenger', position: 1, impressions: 100, interestsAccepted: 2 }, // rate 2% < primary's 5% anyway, but also under MIN_ACCEPTED
    { photoId: 'third', position: 2, impressions: 100, interestsAccepted: 10 },
  ]);
  // 'third': rate 10% vs primary 5% -> lift 100%, accepted=10 >= floor -> should win.
  assert.ok(rec);
  assert.equal(rec!.photoId, 'third');
});

test('computeRecommendation: recommends the photo with the best significant lift, never on raw impressions/views', () => {
  const rec = computeRecommendation([
    // Primary: high impressions, mediocre accept rate.
    { photoId: 'primary', position: 0, impressions: 200, interestsAccepted: 10 }, // 5%
    // Huge raw impressions/views but a WORSE rate, must never win on views alone.
    { photoId: 'high-views-low-rate', position: 1, impressions: 1000, interestsAccepted: 20 }, // 2%
    // Fewer impressions than the "high views" one, but a clearly better rate.
    { photoId: 'best-rate', position: 2, impressions: 150, interestsAccepted: 30 }, // 20%
  ]);
  assert.ok(rec);
  assert.equal(rec!.photoId, 'best-rate');
  assert.equal(rec!.currentPosition, 2);
  assert.equal(rec!.recommendedPosition, 0);
  // (0.20 - 0.05) / 0.05 = 3.0 -> 300%
  assert.equal(rec!.acceptedInterestLiftPercent, 300);
});

test('computeRecommendation: a lift below the significance threshold is not recommended', () => {
  const rec = computeRecommendation([
    { photoId: 'primary', position: 0, impressions: 200, interestsAccepted: 20 }, // 10%
    { photoId: 'challenger', position: 1, impressions: 200, interestsAccepted: 21 }, // 10.5% -> ~5% lift, below the 15% floor
  ]);
  assert.equal(rec, null);
});

test('computeRecommendation: no lift is reported when the primary and challenger tie', () => {
  const rec = computeRecommendation([
    { photoId: 'primary', position: 0, impressions: 200, interestsAccepted: 20 },
    { photoId: 'challenger', position: 1, impressions: 200, interestsAccepted: 20 },
    { photoId: 'third', position: 2, impressions: 200, interestsAccepted: 20 },
  ]);
  assert.equal(rec, null);
});

// =====================================================================
// recordImpression / recordInterestSent / recordInterestAccepted
// =====================================================================

test('recordImpression/recordInterestSent/recordInterestAccepted: accumulate per (user, photo)', async () => {
  const userId = await createUser();
  const [photo1] = await uploadApprovedPhotos(userId, 1);
  const viewerId = await createUser();
  const viewerCtx = buildCtx({ now: NOW, actor: userActor(viewerId) });

  await photoExperiment.recordImpression(viewerCtx, { candidateUserId: userId, photoId: photo1!.id });
  await photoExperiment.recordImpression(viewerCtx, { candidateUserId: userId, photoId: photo1!.id });
  await photoExperiment.recordInterestSent(viewerCtx, { candidateUserId: userId, photoId: photo1!.id });
  await photoExperiment.recordInterestAccepted(viewerCtx, { candidateUserId: userId, photoId: photo1!.id });

  const ownerCtx = buildCtx({ now: NOW, actor: userActor(userId) });
  const stats = await photoExperiment.listStatsForUser(ownerCtx, userId);
  assert.equal(stats.length, 1);
  assert.equal(stats[0]!.impressions, 2);
  assert.equal(stats[0]!.interestsSent, 1);
  assert.equal(stats[0]!.interestsAccepted, 1);
});

test('recordImpression: rejects a photoId that does not belong to candidateUserId', async () => {
  const userA = await createUser();
  const userB = await createUser();
  const [photoA] = await uploadApprovedPhotos(userA, 1);
  const ctx = buildCtx({ now: NOW });

  await assert.rejects(
    () => photoExperiment.recordImpression(ctx, { candidateUserId: userB, photoId: photoA!.id }),
    ValidationError,
  );
});

test('listStatsForUser: a user cannot view another user’s stats', async () => {
  const userA = await createUser();
  const userB = await createUser();
  const ctxB = buildCtx({ now: NOW, actor: userActor(userB) });

  await assert.rejects(() => photoExperiment.listStatsForUser(ctxB, userA), ForbiddenError);
});

// =====================================================================
// refreshAllRecommendations / getMyPhotoTestResults / approve/reject
// =====================================================================

test('refreshAllRecommendations: does nothing for a user with the photo_ab_testing flag off', async () => {
  const userId = await createUser();
  const photos = await uploadApprovedPhotos(userId, 3);
  await seedStats(userId, photos[0]!.id, 200, 10); // primary, 5%
  await seedStats(userId, photos[1]!.id, 200, 60); // 30%, would clearly win if the flag were on
  await seedStats(userId, photos[2]!.id, 200, 10);

  const systemCtx = buildCtx({ now: NOW });
  await photoExperiment.refreshAllRecommendations(systemCtx);

  const ownerCtx = buildCtx({ now: NOW, actor: userActor(userId) });
  const results = await photoExperiment.getMyPhotoTestResults(ownerCtx);
  assert.deepEqual(results, []);
});

test('refreshAllRecommendations: produces a recommendation once flagged in and enough data exists; getMyPhotoTestResults reads it back', async () => {
  await enablePhotoAbTesting();
  const userId = await createUser();
  const photos = await uploadApprovedPhotos(userId, 3);
  await seedStats(userId, photos[0]!.id, 200, 10); // primary, 5%
  await seedStats(userId, photos[1]!.id, 200, 60); // 30% -> big lift
  await seedStats(userId, photos[2]!.id, 200, 10);

  const systemCtx = buildCtx({ now: NOW });
  const { usersUpdated } = await photoExperiment.refreshAllRecommendations(systemCtx);
  assert.ok(usersUpdated >= 1);

  const ownerCtx = buildCtx({ now: NOW, actor: userActor(userId) });
  const results = await photoExperiment.getMyPhotoTestResults(ownerCtx);
  assert.equal(results.length, 1);
  assert.equal(results[0]!.photoId, photos[1]!.id);
  assert.equal(results[0]!.recommendedPosition, 0);
  assert.ok(results[0]!.acceptedInterestLiftPercent > 0);
});

test('approveRecommendation: reorders photos, making the recommended photo primary', async () => {
  await enablePhotoAbTesting();
  const userId = await createUser();
  const photos = await uploadApprovedPhotos(userId, 3);
  await seedStats(userId, photos[0]!.id, 200, 10);
  await seedStats(userId, photos[1]!.id, 200, 60);
  await seedStats(userId, photos[2]!.id, 200, 10);

  const systemCtx = buildCtx({ now: NOW });
  await photoExperiment.refreshAllRecommendations(systemCtx);

  const ownerCtx = buildCtx({ now: NOW, actor: userActor(userId) });
  await photoExperiment.approveRecommendation(ownerCtx, photos[1]!.id);

  const myPhotos = await photo.listMyPhotos(ownerCtx);
  const newPrimary = myPhotos.find((p) => p.isPrimary);
  assert.equal(newPrimary?.id, photos[1]!.id);
  assert.equal(newPrimary?.position, 0);

  // The recommendation is no longer pending.
  const results = await photoExperiment.getMyPhotoTestResults(ownerCtx);
  assert.deepEqual(results, []);
});

test('rejectRecommendation: dismisses without reordering, and refreshAllRecommendations never re-surfaces it', async () => {
  await enablePhotoAbTesting();
  const userId = await createUser();
  const photos = await uploadApprovedPhotos(userId, 3);
  await seedStats(userId, photos[0]!.id, 200, 10);
  await seedStats(userId, photos[1]!.id, 200, 60);
  await seedStats(userId, photos[2]!.id, 200, 10);

  const systemCtx = buildCtx({ now: NOW });
  await photoExperiment.refreshAllRecommendations(systemCtx);

  const ownerCtx = buildCtx({ now: NOW, actor: userActor(userId) });
  await photoExperiment.rejectRecommendation(ownerCtx, photos[1]!.id);

  const myPhotosAfterReject = await photo.listMyPhotos(ownerCtx);
  assert.equal(myPhotosAfterReject.find((p) => p.isPrimary)?.id, photos[0]!.id, 'rejecting must not reorder anything');

  // Re-running the nightly job must not resurrect the same (user, photo)
  // recommendation once the user has explicitly rejected it.
  await photoExperiment.refreshAllRecommendations(systemCtx);
  const results = await photoExperiment.getMyPhotoTestResults(ownerCtx);
  assert.deepEqual(results, []);
});

test('approveRecommendation: throws NotFoundError when there is no pending recommendation for that photo', async () => {
  const userId = await createUser();
  const [onlyPhoto] = await uploadApprovedPhotos(userId, 1);
  const ownerCtx = buildCtx({ now: NOW, actor: userActor(userId) });

  await assert.rejects(() => photoExperiment.approveRecommendation(ownerCtx, onlyPhoto!.id), NotFoundError);
});

async function seedStats(userId: string, photoId: string, impressions: number, interestsAccepted: number): Promise<void> {
  const pool = getTestPool();
  await pool.query(
    `INSERT INTO photo_experiments (user_id, photo_id, impressions, interests_sent, interests_accepted, created_at, updated_at)
     VALUES ($1, $2, $3, 0, $4, now(), now())`,
    [userId, photoId, impressions, interestsAccepted],
  );
}
