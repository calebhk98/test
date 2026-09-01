import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestDatabase, teardownTestDatabase, getTestPool, buildCtx, userActor, uniqueEmail } from './testCtx.js';
import * as photo from '../../src/services/photo.service.js';
import { NotFoundError, ValidationError } from '../../src/lib/errors.js';

before(async () => {
  await setupTestDatabase('photo');
});

after(async () => {
  await teardownTestDatabase();
});

const NOW = new Date();

async function createUser(): Promise<string> {
  const pool = getTestPool();
  const { rows } = await pool.query<{ id: string }>(
    `INSERT INTO users (email, password_hash, birthdate, status, trust_score, trust_level)
     VALUES ($1, 'x', '1990-01-01', 'active', 60, 'standard') RETURNING id`,
    [uniqueEmail('photouser')],
  );
  return rows[0]!.id;
}

// `photo.service`'s duplicate/scam detection (§7.2 rule 4) keys off the
// image URL's perceptual hash — the stub adapter hashes the URL itself
// when it's not a `dup:<n>` URL (see stub.adapter.ts's doc comment). Two
// *different* tests uploading the literal same plain URL would therefore
// look like a cross-user duplicate to the very code under test. Every
// non-`dup:`-tagged URL below goes through this helper so tests stay
// independent of each other, while still embedding whichever magic
// substring (`noface`, `nsfw`, `weapon`, `illegal`, `blurry`, `group`) a
// given test needs the stub adapter to key off of.
let urlCounter = 0;
function uniqueUrl(tag: string): string {
  urlCounter += 1;
  return `https://example.test/${tag}-${urlCounter}.jpg`;
}

test('uploadPhoto: first photo is the primary-candidate — a clean photo with a face is approved and primary', async () => {
  const userId = await createUser();
  const ctx = buildCtx({ now: NOW, actor: userActor(userId) });

  const uploaded = await photo.uploadPhoto(ctx, { imageUrl: uniqueUrl('clean-face') });

  assert.equal(uploaded.moderationStatus, 'approved');
  assert.equal(uploaded.isPrimary, true);
  assert.equal(uploaded.faceDetected, true);
  assert.equal(uploaded.position, 0);
});

test('uploadPhoto: first photo without a detected face is rejected, never queued for human review', async () => {
  const userId = await createUser();
  const ctx = buildCtx({ now: NOW, actor: userActor(userId) });

  const uploaded = await photo.uploadPhoto(ctx, { imageUrl: uniqueUrl('noface') });

  assert.equal(uploaded.moderationStatus, 'rejected');
  assert.equal(uploaded.isPrimary, false);
  assert.equal(uploaded.faceDetected, false);
  // 'pending' would imply a human-review queue — zero human moderation (§18.1).
  assert.notEqual(uploaded.moderationStatus, 'pending');
});

test('uploadPhoto: nudity/weapons/illegal content is auto-rejected, never queued', async () => {
  const userId = await createUser();
  const ctx = buildCtx({ now: NOW, actor: userActor(userId) });

  const nsfw = await photo.uploadPhoto(ctx, { imageUrl: uniqueUrl('nsfw-photo') });
  assert.equal(nsfw.moderationStatus, 'rejected');

  const weapon = await photo.uploadPhoto(ctx, { imageUrl: uniqueUrl('weapon-photo') });
  assert.equal(weapon.moderationStatus, 'rejected');

  const illegal = await photo.uploadPhoto(ctx, { imageUrl: uniqueUrl('illegal-photo') });
  assert.equal(illegal.moderationStatus, 'rejected');
});

test('uploadPhoto: a second (non-primary-candidate) photo is never auto-primary even if approved', async () => {
  const userId = await createUser();
  const ctx = buildCtx({ now: NOW, actor: userActor(userId) });

  await photo.uploadPhoto(ctx, { imageUrl: uniqueUrl('first') });
  const second = await photo.uploadPhoto(ctx, { imageUrl: uniqueUrl('second') });

  assert.equal(second.moderationStatus, 'approved');
  assert.equal(second.isPrimary, false);
  assert.equal(second.position, 1);
});

test('uploadPhoto: a duplicate perceptual hash shared with another user’s approved photo is flagged', async () => {
  const userA = await createUser();
  const userB = await createUser();
  const ctxA = buildCtx({ now: NOW, actor: userActor(userA) });
  const ctxB = buildCtx({ now: NOW, actor: userActor(userB) });

  const sharedUrl = 'https://example.test/dup:shared-hash.jpg';
  const first = await photo.uploadPhoto(ctxA, { imageUrl: sharedUrl });
  assert.equal(first.moderationStatus, 'approved');

  const second = await photo.uploadPhoto(ctxB, { imageUrl: sharedUrl });
  assert.equal(second.moderationStatus, 'flagged');

  const duplicateOwners = await photo.findDuplicateOwners(ctxB, second.perceptualHash!, userB);
  assert.deepEqual(duplicateOwners, [userA]);
});

test('exactly one primary photo is enforced across upload/setPrimaryPhoto', async () => {
  const userId = await createUser();
  const ctx = buildCtx({ now: NOW, actor: userActor(userId) });

  const first = await photo.uploadPhoto(ctx, { imageUrl: uniqueUrl('one') });
  const second = await photo.uploadPhoto(ctx, { imageUrl: uniqueUrl('two') });
  await photo.uploadPhoto(ctx, { imageUrl: uniqueUrl('three') });

  assert.equal(first.isPrimary, true);
  assert.equal(second.isPrimary, false);

  const promoted = await photo.setPrimaryPhoto(ctx, second.id);
  assert.equal(promoted.isPrimary, true);

  const all = await photo.listMyPhotos(ctx);
  const primaries = all.filter((p) => p.isPrimary);
  assert.equal(primaries.length, 1);
  assert.equal(primaries[0]!.id, second.id);
});

test('setPrimaryPhoto: rejects a photo that has no detected face (re-analyzed as a primary-candidate)', async () => {
  const userId = await createUser();
  const ctx = buildCtx({ now: NOW, actor: userActor(userId) });

  await photo.uploadPhoto(ctx, { imageUrl: uniqueUrl('first') });
  // Uploaded as a *secondary* photo, so its own upload analysis never
  // required a face — but promoting it to primary must re-check that gate.
  const faceless = await photo.uploadPhoto(ctx, { imageUrl: uniqueUrl('noface-secondary') });
  // As a *secondary* upload, the face gate never applied — it's approved.
  assert.equal(faceless.moderationStatus, 'approved');
  assert.equal(faceless.faceDetected, false);

  await assert.rejects(() => photo.setPrimaryPhoto(ctx, faceless.id), ValidationError);
});

test('deletePhoto: deleting the primary promotes the next approved, face-detected photo', async () => {
  const userId = await createUser();
  const ctx = buildCtx({ now: NOW, actor: userActor(userId) });

  const first = await photo.uploadPhoto(ctx, { imageUrl: uniqueUrl('first') });
  const second = await photo.uploadPhoto(ctx, { imageUrl: uniqueUrl('second') });
  assert.equal(first.isPrimary, true);
  assert.equal(second.moderationStatus, 'approved');

  await photo.deletePhoto(ctx, first.id);

  const remaining = await photo.listMyPhotos(ctx);
  assert.equal(remaining.length, 1);
  assert.equal(remaining[0]!.id, second.id);
  assert.equal(remaining[0]!.isPrimary, true);
});

test('deletePhoto: deleting the primary leaves no primary when no remaining photo has a detected face', async () => {
  const userId = await createUser();
  const ctx = buildCtx({ now: NOW, actor: userActor(userId) });

  const first = await photo.uploadPhoto(ctx, { imageUrl: uniqueUrl('first') });
  const second = await photo.uploadPhoto(ctx, { imageUrl: uniqueUrl('noface-only') });
  assert.equal(second.faceDetected, false);

  await photo.deletePhoto(ctx, first.id);

  const remaining = await photo.listMyPhotos(ctx);
  assert.equal(remaining.length, 1);
  assert.equal(remaining[0]!.isPrimary, false, 'never auto-promote a photo with no detected face');
});

test('deletePhoto: throws NotFoundError for a photo owned by someone else', async () => {
  const userA = await createUser();
  const userB = await createUser();
  const ctxA = buildCtx({ now: NOW, actor: userActor(userA) });
  const ctxB = buildCtx({ now: NOW, actor: userActor(userB) });

  const photoA = await photo.uploadPhoto(ctxA, { imageUrl: uniqueUrl('a') });

  await assert.rejects(() => photo.deletePhoto(ctxB, photoA.id), NotFoundError);
});

test('reorderPhotos: persists a new position order without changing who is primary', async () => {
  const userId = await createUser();
  const ctx = buildCtx({ now: NOW, actor: userActor(userId) });

  const a = await photo.uploadPhoto(ctx, { imageUrl: uniqueUrl('a') });
  const b = await photo.uploadPhoto(ctx, { imageUrl: uniqueUrl('b') });
  const c = await photo.uploadPhoto(ctx, { imageUrl: uniqueUrl('c') });

  const reordered = await photo.reorderPhotos(ctx, [c.id, a.id, b.id]);

  assert.deepEqual(
    reordered.map((p) => p.id),
    [c.id, a.id, b.id],
  );
  assert.deepEqual(
    reordered.map((p) => p.position),
    [0, 1, 2],
  );
  // `a` is still the one marked primary — reordering never changes that.
  const primary = reordered.find((p) => p.isPrimary);
  assert.equal(primary?.id, a.id);
});

test('reorderPhotos: rejects a list that does not match the caller’s current photo ids', async () => {
  const userId = await createUser();
  const ctx = buildCtx({ now: NOW, actor: userActor(userId) });
  await photo.uploadPhoto(ctx, { imageUrl: uniqueUrl('a') });
  await photo.uploadPhoto(ctx, { imageUrl: uniqueUrl('b') });

  await assert.rejects(() => photo.reorderPhotos(ctx, ['00000000-0000-0000-0000-000000000000']), ValidationError);
});

test('listMyPhotos: only ever returns the caller’s own photos, ordered by position', async () => {
  const userA = await createUser();
  const userB = await createUser();
  const ctxA = buildCtx({ now: NOW, actor: userActor(userA) });
  const ctxB = buildCtx({ now: NOW, actor: userActor(userB) });

  await photo.uploadPhoto(ctxA, { imageUrl: uniqueUrl('a1') });
  await photo.uploadPhoto(ctxA, { imageUrl: uniqueUrl('a2') });
  await photo.uploadPhoto(ctxB, { imageUrl: uniqueUrl('b1') });

  const aPhotos = await photo.listMyPhotos(ctxA);
  assert.equal(aPhotos.length, 2);
  assert.ok(aPhotos.every((p) => p.userId === userA));
  assert.deepEqual(
    aPhotos.map((p) => p.position),
    [0, 1],
  );
});

test('findDuplicateOwners: excludes the caller and non-approved photos', async () => {
  const userA = await createUser();
  const userB = await createUser();
  const userC = await createUser();
  const ctxA = buildCtx({ now: NOW, actor: userActor(userA) });
  const ctxB = buildCtx({ now: NOW, actor: userActor(userB) });
  const ctxC = buildCtx({ now: NOW, actor: userActor(userC) });

  const a = await photo.uploadPhoto(ctxA, { imageUrl: 'https://example.test/dup:x2.jpg' });
  // userB's copy is rejected outright (nsfw) even though it shares the hash — not counted as an "approved" duplicate owner.
  await photo.uploadPhoto(ctxB, { imageUrl: 'https://example.test/dup:x2-nsfw.jpg' });
  const c = await photo.uploadPhoto(ctxC, { imageUrl: 'https://example.test/dup:x2.jpg' });

  const owners = await photo.findDuplicateOwners(ctxC, a.perceptualHash!, userC);
  assert.ok(owners.includes(userA));
  assert.ok(!owners.includes(userC));
  assert.equal(c.moderationStatus, 'flagged');
});
