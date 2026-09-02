/**
 * tests/http/altTextWiring.test.ts, wiring item 3: photo alt text must
 * reach a client. Alt text was already stored on the photo row
 * (`photoAltText.service.ts`), but every reader that built a photo shape
 * for the wire discarded even the photo id, so a description could never
 * travel with it. This suite proves it now does, everywhere a photo
 * appears: the owner's own profile (`GET /me/photos`), another user's
 * profile (`GET /profiles/:userId`), a discovery card (`GET /discovery`),
 * and a matches row (`GET /matches`). It also exercises the new
 * `PUT/DELETE /me/photos/:photoId/alt-text` routes this build added, since
 * without them a client could never set a description in the first place.
 */
import { test, before, after, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestApp, teardownTestApp, registerUser, authHeader, resetRateLimiter } from './testServer.js';
import type { TestApp } from './testServer.js';

let t: TestApp;

before(async () => {
  t = await setupTestApp('alttextwiring');
});

after(async () => {
  await teardownTestApp(t);
});

beforeEach(() => {
  resetRateLimiter(t);
});

const DESCRIPTION = 'A person smiling on a sunlit trail, wearing a red jacket.';

async function uploadPrimaryPhoto(token: string, url: string): Promise<{ id: string; imageUrl: string }> {
  const res = await t.app.inject({ method: 'POST', url: '/me/photos', headers: authHeader(token), payload: { imageUrl: url } });
  assert.equal(res.statusCode, 201);
  const photo = JSON.parse(res.body) as { id: string; imageUrl: string; isPrimary: boolean };
  assert.equal(photo.isPrimary, true, 'the first photo uploaded is the primary candidate');
  return photo;
}

async function setAltText(token: string, photoId: string, altText: string): Promise<void> {
  const res = await t.app.inject({
    method: 'PUT',
    url: `/me/photos/${photoId}/alt-text`,
    headers: authHeader(token),
    payload: { altText },
  });
  assert.equal(res.statusCode, 200, `set alt text failed: ${res.body}`);
  const body = JSON.parse(res.body) as { altText: string };
  assert.equal(body.altText, altText);
}

async function completeBaseProfile(token: string, opts: { displayName: string; gender: string; seeking: string }): Promise<void> {
  const res = await t.app.inject({
    method: 'PATCH',
    url: '/me/profile',
    headers: authHeader(token),
    payload: {
      displayName: opts.displayName,
      bio: 'Alt text wiring test bio, long enough to be a real bio for completeness scoring.',
      city: 'Springfield',
      latitude: 39.78,
      longitude: -89.65,
      age: 28,
      gender: opts.gender,
      seeking: opts.seeking,
      relationshipIntention: 'long_term',
    },
  });
  assert.equal(res.statusCode, 200, `profile setup failed: ${res.body}`);
}

test('PUT /me/photos/:photoId/alt-text sets a description; DELETE clears it back to null', async () => {
  const alice = await registerUser(t);
  const photo = await uploadPrimaryPhoto(alice.accessToken, 'https://example.test/alt-alice-1.jpg');

  await setAltText(alice.accessToken, photo.id, DESCRIPTION);

  const clearRes = await t.app.inject({ method: 'DELETE', url: `/me/photos/${photo.id}/alt-text`, headers: authHeader(alice.accessToken) });
  assert.equal(clearRes.statusCode, 204);

  const listRes = await t.app.inject({ method: 'GET', url: '/me/photos', headers: authHeader(alice.accessToken) });
  const list = JSON.parse(listRes.body) as Array<{ id: string; altText: string | null }>;
  const row = list.find((p) => p.id === photo.id)!;
  assert.equal(row.altText, null);
});

test('a stranger cannot set alt text on someone else’s photo (404, never leaks whose it is)', async () => {
  const alice = await registerUser(t);
  const mallory = await registerUser(t);
  const photo = await uploadPrimaryPhoto(alice.accessToken, 'https://example.test/alt-alice-2.jpg');

  const res = await t.app.inject({
    method: 'PUT',
    url: `/me/photos/${photo.id}/alt-text`,
    headers: authHeader(mallory.accessToken),
    payload: { altText: 'Attempted description.' },
  });
  assert.equal(res.statusCode, 404);
});

test('alt text reaches the owner’s own profile (GET /me/photos)', async () => {
  const alice = await registerUser(t);
  const photo = await uploadPrimaryPhoto(alice.accessToken, 'https://example.test/alt-own-1.jpg');
  await setAltText(alice.accessToken, photo.id, DESCRIPTION);

  const res = await t.app.inject({ method: 'GET', url: '/me/photos', headers: authHeader(alice.accessToken) });
  assert.equal(res.statusCode, 200);
  const photos = JSON.parse(res.body) as Array<{ id: string; imageUrl: string; altText: string | null }>;
  const row = photos.find((p) => p.id === photo.id)!;
  assert.ok(row, 'the uploaded photo is present');
  assert.equal(row.imageUrl, 'https://example.test/alt-own-1.jpg');
  assert.equal(row.altText, DESCRIPTION);
});

test('alt text reaches another user’s profile (GET /profiles/:userId)', async () => {
  const viewer = await registerUser(t);
  const target = await registerUser(t);
  await completeBaseProfile(viewer.accessToken, { displayName: 'AltViewer', gender: 'woman', seeking: 'man' });
  await completeBaseProfile(target.accessToken, { displayName: 'AltTarget', gender: 'man', seeking: 'woman' });
  const photo = await uploadPrimaryPhoto(target.accessToken, 'https://example.test/alt-public-1.jpg');
  await setAltText(target.accessToken, photo.id, DESCRIPTION);

  const res = await t.app.inject({ method: 'GET', url: `/profiles/${target.userId}`, headers: authHeader(viewer.accessToken) });
  assert.equal(res.statusCode, 200);
  const body = JSON.parse(res.body) as { photos: Array<{ id: string; imageUrl: string; altText: string | null }> };
  assert.equal('photoUrls' in body, false, 'the old bare-string field must be gone');
  const row = body.photos.find((p) => p.id === photo.id)!;
  assert.ok(row, 'the photo is present on the public profile view');
  assert.equal(row.altText, DESCRIPTION);
});

test('alt text reaches a discovery card (GET /discovery)', async () => {
  const viewer = await registerUser(t);
  const target = await registerUser(t);
  await completeBaseProfile(viewer.accessToken, { displayName: 'AltDiscViewer', gender: 'woman', seeking: 'man' });
  await completeBaseProfile(target.accessToken, { displayName: 'AltDiscTarget', gender: 'man', seeking: 'woman' });
  const photo = await uploadPrimaryPhoto(target.accessToken, 'https://example.test/alt-discovery-1.jpg');
  await setAltText(target.accessToken, photo.id, DESCRIPTION);

  const res = await t.app.inject({ method: 'GET', url: '/discovery', headers: authHeader(viewer.accessToken) });
  assert.equal(res.statusCode, 200);
  const body = JSON.parse(res.body) as { items: Array<{ userId: string; primaryPhoto: { id: string; imageUrl: string; altText: string | null } | null }> };
  const card = body.items.find((c) => c.userId === target.userId);
  assert.ok(card, 'target should be discoverable');
  assert.ok(card!.primaryPhoto, 'the card carries a primaryPhoto object, not a bare url');
  assert.equal(card!.primaryPhoto!.id, photo.id);
  assert.equal(card!.primaryPhoto!.imageUrl, 'https://example.test/alt-discovery-1.jpg');
  assert.equal(card!.primaryPhoto!.altText, DESCRIPTION);
});

test('alt text reaches a matches row (GET /matches)', async () => {
  const alice = await registerUser(t);
  const bob = await registerUser(t);
  await completeBaseProfile(alice.accessToken, { displayName: 'AltMatchAlice', gender: 'woman', seeking: 'man' });
  await completeBaseProfile(bob.accessToken, { displayName: 'AltMatchBob', gender: 'man', seeking: 'woman' });
  const photo = await uploadPrimaryPhoto(bob.accessToken, 'https://example.test/alt-match-1.jpg');
  await setAltText(bob.accessToken, photo.id, DESCRIPTION);

  const sendRes = await t.app.inject({ method: 'POST', url: '/interests', headers: authHeader(alice.accessToken), payload: { recipientId: bob.userId } });
  assert.equal(sendRes.statusCode, 201);
  const interest = JSON.parse(sendRes.body) as { id: string };
  const acceptRes = await t.app.inject({ method: 'POST', url: `/interests/${interest.id}/accept`, headers: authHeader(bob.accessToken) });
  assert.equal(acceptRes.statusCode, 200);

  const res = await t.app.inject({ method: 'GET', url: '/matches', headers: authHeader(alice.accessToken) });
  assert.equal(res.statusCode, 200);
  const body = JSON.parse(res.body) as { items: Array<{ matchedUserId: string; primaryPhoto: { id: string; imageUrl: string; altText: string | null } | null }> };
  assert.equal('primaryPhotoUrl' in (body.items[0] ?? {}), false, 'the old bare-string field must be gone');
  const row = body.items.find((m) => m.matchedUserId === bob.userId)!;
  assert.ok(row, 'bob appears in alice’s matches');
  assert.ok(row.primaryPhoto, 'the match row carries a primaryPhoto object, not a bare url');
  assert.equal(row.primaryPhoto!.id, photo.id);
  assert.equal(row.primaryPhoto!.altText, DESCRIPTION);
});

test('a photo with no description degrades to null altText everywhere, never the literal word "null" or a thrown error', async () => {
  const viewer = await registerUser(t);
  const target = await registerUser(t);
  await completeBaseProfile(viewer.accessToken, { displayName: 'AltNoneViewer', gender: 'woman', seeking: 'man' });
  await completeBaseProfile(target.accessToken, { displayName: 'AltNoneTarget', gender: 'man', seeking: 'woman' });
  await uploadPrimaryPhoto(target.accessToken, 'https://example.test/alt-none-1.jpg');

  const profileRes = await t.app.inject({ method: 'GET', url: `/profiles/${target.userId}`, headers: authHeader(viewer.accessToken) });
  const profileBody = JSON.parse(profileRes.body) as { photos: Array<{ altText: string | null }> };
  assert.equal(profileBody.photos[0]!.altText, null);

  const discoveryRes = await t.app.inject({ method: 'GET', url: '/discovery', headers: authHeader(viewer.accessToken) });
  const discoveryBody = JSON.parse(discoveryRes.body) as { items: Array<{ userId: string; primaryPhoto: { altText: string | null } | null }> };
  const card = discoveryBody.items.find((c) => c.userId === target.userId);
  assert.equal(card!.primaryPhoto!.altText, null);
});
