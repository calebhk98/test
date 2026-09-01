/**
 * Optional phone number lifecycle (build correction, see
 * `auth.service.ts`'s module doc: a phone number must never be MANDATORY
 * for anything, but an OPTIONAL, verified-by-one-time-code phone number is
 * fully supported).
 *
 * Reuses `tests/http/testServer.ts` (read-only import, not owned by this
 * build, never modified here) as the harness for this whole file rather
 * than hand-rolling a second database bootstrap: it already gives a real
 * migrated database, a real Fastify app (needed for the "never leaks
 * through any user-facing route" and "the core loop never needs a phone"
 * scenarios below), AND a plain `Ctx` (`ctxWithActor`) for driving
 * `auth.service`'s phone functions directly where a test needs to inspect
 * server-side state (attempt counts, expiry, rate-limit windows) that no
 * HTTP response exposes. One database for the whole file
 * (`odate_http_phone`), created/dropped by `setupTestApp`/`teardownTestApp`
 * exactly like every other `tests/http/*.test.ts` suite.
 */
import { readdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { test, before, after, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import {
  setupTestApp,
  teardownTestApp,
  registerUser,
  authHeader,
  completeOnboarding,
  createVenue,
  resetRateLimiter,
} from '../http/testServer.js';
import type { TestApp } from '../http/testServer.js';
import { ctxWithActor } from '../../src/http/deps.js';
import * as authService from '../../src/services/auth.service.js';
import { sha256Hex } from '../../src/lib/hash.js';
import { ConflictError, ForbiddenError, RateLimitError, UnauthorizedError, ValidationError } from '../../src/lib/errors.js';

let t: TestApp;

before(async () => {
  t = await setupTestApp('phone');
});

after(async () => {
  await teardownTestApp(t);
});

beforeEach(() => {
  resetRateLimiter(t);
});

function userCtx(userId: string) {
  return ctxWithActor(t.deps, { type: 'user', userId, trustLevel: 'standard' }, t.pool);
}
function systemCtx() {
  return ctxWithActor(t.deps, { type: 'system', job: 'test' }, t.pool);
}

/** Overwrites the caller's current pending code's hash so the test can drive `verifyPhone` without knowing the randomly-generated raw code, same "seed a known hash directly" pattern `auth.test.ts` already uses for email verification/password reset tokens. */
async function seedKnownCode(userId: string, code: string): Promise<void> {
  await t.pool.query(
    `UPDATE phone_verification_codes SET code_hash = $2 WHERE user_id = $1 AND consumed_at IS NULL`,
    [userId, sha256Hex(code)],
  );
}

async function freshUser(): Promise<{ userId: string; accessToken: string }> {
  const u = await registerUser(t);
  return { userId: u.userId, accessToken: u.accessToken };
}

// =====================================================================
// Core lifecycle: request -> verify -> status -> remove
// =====================================================================

test('requestPhoneVerification + verifyPhone: happy path marks the number verified', async () => {
  const alice = await freshUser();
  const ctx = userCtx(alice.userId);

  let status = await authService.getMyPhoneStatus(ctx);
  assert.equal(status.hasPhone, false);
  assert.equal(status.verified, false);

  await authService.requestPhoneVerification(ctx, { phoneNumber: '+1 415-555-0100', country: 'us' });

  status = await authService.getMyPhoneStatus(ctx);
  assert.equal(status.hasPhone, true, 'a pending (unverified) phone already shows up in status');
  assert.equal(status.verified, false);
  assert.equal(status.countryCode, 'US', 'country is normalized to uppercase');
  assert.equal(status.last2, '00', 'last2 of +14155550100');

  await seedKnownCode(alice.userId, '123456');
  await authService.verifyPhone(ctx, { code: '123456' });

  status = await authService.getMyPhoneStatus(ctx);
  assert.equal(status.verified, true);
  assert.ok(status.verifiedAt);

  const verified = await authService.getVerifiedPhoneForUser(systemCtx(), alice.userId);
  assert.equal(verified?.e164, '+14155550100', 'stored normalized E.164 (punctuation stripped)');
  assert.equal(verified?.countryCode, 'US');
});

test('requestPhoneVerification: rejects a malformed number and a malformed country code', async () => {
  const alice = await freshUser();
  const ctx = userCtx(alice.userId);

  await assert.rejects(
    () => authService.requestPhoneVerification(ctx, { phoneNumber: 'not-a-phone-number', country: 'US' }),
    ValidationError,
  );
  await assert.rejects(
    () => authService.requestPhoneVerification(ctx, { phoneNumber: '+14155550100', country: 'USA' }),
    /* zod refine -> ValidationError is thrown as a generic ZodError wrapped by the schema itself */
  );
});

test('verifyPhone: wrong code increments attempts; correct code still works before the cap', async () => {
  const alice = await freshUser();
  const ctx = userCtx(alice.userId);
  await authService.requestPhoneVerification(ctx, { phoneNumber: '+14155550101', country: 'US' });
  await seedKnownCode(alice.userId, '111111');

  await assert.rejects(() => authService.verifyPhone(ctx, { code: '000000' }), UnauthorizedError);
  await assert.rejects(() => authService.verifyPhone(ctx, { code: '000001' }), UnauthorizedError);

  await authService.verifyPhone(ctx, { code: '111111' });
  const status = await authService.getMyPhoneStatus(ctx);
  assert.equal(status.verified, true, 'two prior wrong guesses do not block the eventual correct one');
});

test('verifyPhone: exhausting the attempt cap rejects even the correct code, until a fresh code is requested', async () => {
  const alice = await freshUser();
  const ctx = userCtx(alice.userId);
  await authService.requestPhoneVerification(ctx, { phoneNumber: '+14155550102', country: 'US' });
  await seedKnownCode(alice.userId, '222222');

  for (let i = 0; i < 5; i++) {
    await assert.rejects(() => authService.verifyPhone(ctx, { code: '999999' }), UnauthorizedError);
  }
  // The cap (5) is now exhausted, even the right code is refused, and the
  // refusal is a RateLimitError (not UnauthorizedError), so a client can
  // tell "you're locked out" apart from "that guess was wrong".
  await assert.rejects(() => authService.verifyPhone(ctx, { code: '222222' }), RateLimitError);

  // Requesting a new code resets the cap.
  await authService.requestPhoneVerification(ctx, { phoneNumber: '+14155550102', country: 'US' });
  await seedKnownCode(alice.userId, '333333');
  await authService.verifyPhone(ctx, { code: '333333' });
  const status = await authService.getMyPhoneStatus(ctx);
  assert.equal(status.verified, true);
});

test('verifyPhone: an expired code is rejected', async () => {
  const alice = await freshUser();
  const ctx = userCtx(alice.userId);
  await authService.requestPhoneVerification(ctx, { phoneNumber: '+14155550103', country: 'US' });
  await seedKnownCode(alice.userId, '444444');

  t.clock.advanceMs(11 * 60 * 1000); // TTL is 10 minutes
  await assert.rejects(() => authService.verifyPhone(userCtx(alice.userId), { code: '444444' }), UnauthorizedError);
  t.clock.set(new Date('2026-01-05T12:00:00.000Z')); // restore for later tests in this file
});

test('verifyPhone: no pending code at all is rejected', async () => {
  const alice = await freshUser();
  await assert.rejects(() => authService.verifyPhone(userCtx(alice.userId), { code: '123456' }), UnauthorizedError);
});

test('requestPhoneVerification: rate-limits repeated requests within the window', async () => {
  const alice = await freshUser();
  const ctx = userCtx(alice.userId);

  for (let i = 0; i < 5; i++) {
    await authService.requestPhoneVerification(ctx, { phoneNumber: `+141555501${10 + i}`, country: 'US' });
  }
  await assert.rejects(
    () => authService.requestPhoneVerification(ctx, { phoneNumber: '+14155550199', country: 'US' }),
    RateLimitError,
  );

  // Past the window, requests are allowed again.
  t.clock.advanceMs(61 * 60 * 1000);
  await authService.requestPhoneVerification(ctx, { phoneNumber: '+14155550199', country: 'US' });
  t.clock.set(new Date('2026-01-05T12:00:00.000Z'));
});

test('requestPhoneVerification: changing the number resets verification and supersedes the old pending code', async () => {
  const alice = await freshUser();
  const ctx = userCtx(alice.userId);

  await authService.requestPhoneVerification(ctx, { phoneNumber: '+14155550200', country: 'US' });
  await seedKnownCode(alice.userId, '555555');
  await authService.verifyPhone(ctx, { code: '555555' });
  assert.equal((await authService.getMyPhoneStatus(ctx)).verified, true);

  // Changing to a new number requires re-verification.
  await authService.requestPhoneVerification(ctx, { phoneNumber: '+14155550201', country: 'US' });
  const afterChange = await authService.getMyPhoneStatus(ctx);
  assert.equal(afterChange.verified, false, 'changing the number un-verifies it');
  assert.equal(afterChange.last2, '01');

  // The OLD code (for the old number) is now stale and can never verify anything.
  await assert.rejects(() => authService.verifyPhone(ctx, { code: '555555' }), UnauthorizedError);

  await seedKnownCode(alice.userId, '666666');
  await authService.verifyPhone(ctx, { code: '666666' });
  assert.equal((await authService.getMyPhoneStatus(ctx)).verified, true);
});

test('requestPhoneVerification: a number already VERIFIED on another account cannot be claimed', async () => {
  const alice = await freshUser();
  const bob = await freshUser();

  await authService.requestPhoneVerification(userCtx(alice.userId), { phoneNumber: '+14155550300', country: 'US' });
  await seedKnownCode(alice.userId, '777777');
  await authService.verifyPhone(userCtx(alice.userId), { code: '777777' });

  await assert.rejects(
    () => authService.requestPhoneVerification(userCtx(bob.userId), { phoneNumber: '+14155550300', country: 'US' }),
    ConflictError,
  );
});

test('removePhone: as easy as adding one, and immediately turns off SMS eligibility', async () => {
  const alice = await freshUser();
  const ctx = userCtx(alice.userId);

  await authService.requestPhoneVerification(ctx, { phoneNumber: '+14155550400', country: 'US' });
  await seedKnownCode(alice.userId, '888888');
  await authService.verifyPhone(ctx, { code: '888888' });
  assert.ok(await authService.getVerifiedPhoneForUser(systemCtx(), alice.userId));

  await authService.removePhone(ctx);

  const status = await authService.getMyPhoneStatus(ctx);
  assert.equal(status.hasPhone, false);
  assert.equal(await authService.getVerifiedPhoneForUser(systemCtx(), alice.userId), null);

  // A no-op, not an error, when called again with nothing to remove.
  await authService.removePhone(ctx);
});

// =====================================================================
// Privacy: `getVerifiedPhoneForUser` internal read's trust boundary, and
// `getMyPhoneStatus`'s masking.
// =====================================================================

test('getVerifiedPhoneForUser: readable by the user themselves or `system`, never by a different user', async () => {
  const alice = await freshUser();
  const bob = await freshUser();
  await authService.requestPhoneVerification(userCtx(alice.userId), { phoneNumber: '+14155550500', country: 'US' });
  await seedKnownCode(alice.userId, '121212');
  await authService.verifyPhone(userCtx(alice.userId), { code: '121212' });

  assert.ok(await authService.getVerifiedPhoneForUser(userCtx(alice.userId), alice.userId));
  assert.ok(await authService.getVerifiedPhoneForUser(systemCtx(), alice.userId));
  await assert.rejects(
    () => authService.getVerifiedPhoneForUser(userCtx(bob.userId), alice.userId),
    ForbiddenError,
    "one user must never be able to read another user's phone number",
  );
});

test('getMyPhoneStatus: never returns the full number, only the last 2 digits', async () => {
  const alice = await freshUser();
  const ctx = userCtx(alice.userId);
  await authService.requestPhoneVerification(ctx, { phoneNumber: '+14155559876', country: 'US' });
  await seedKnownCode(alice.userId, '343434');
  await authService.verifyPhone(ctx, { code: '343434' });

  const status = await authService.getMyPhoneStatus(ctx);
  const serialized = JSON.stringify(status);
  assert.equal(status.last2, '76');
  assert.ok(!serialized.includes('9876'), 'the status view must never carry the full number, even masked to a few extra digits');
  assert.ok(!serialized.includes('+1415'), 'no E.164 prefix leakage either');
});

// =====================================================================
// "Never mandatory": the entire core loop works with no phone at all, and
// a phone that IS added/verified can never reach another user through any
// user-facing serializer or route.
// =====================================================================

test('phone-less core loop: register -> answers -> filters -> discovery -> interest -> accept -> chat -> propose date, with no phone ever added', async () => {
  const alice = await registerUser(t);
  const bob = await registerUser(t);

  await completeOnboarding(t, alice.accessToken, { displayName: 'AliceCoreLoop', gender: 'woman', seeking: 'man' });
  await completeOnboarding(t, bob.accessToken, { displayName: 'BobCoreLoop', gender: 'man', seeking: 'woman' });

  const filtersRes = await t.app.inject({
    method: 'PATCH',
    url: '/me/filters',
    headers: authHeader(alice.accessToken),
    payload: [{ filterKey: 'age_min', operator: 'gte', value: 18, enabled: true }],
  });
  assert.equal(filtersRes.statusCode, 200);

  const discoveryRes = await t.app.inject({ method: 'GET', url: '/discovery', headers: authHeader(alice.accessToken) });
  assert.equal(discoveryRes.statusCode, 200);
  const discoveryBody = JSON.parse(discoveryRes.body) as { items: Array<{ userId: string }> };
  assert.ok(discoveryBody.items.some((c) => c.userId === bob.userId));

  const sendRes = await t.app.inject({
    method: 'POST',
    url: '/interests',
    headers: authHeader(alice.accessToken),
    payload: { recipientId: bob.userId },
  });
  assert.equal(sendRes.statusCode, 201);
  const interest = JSON.parse(sendRes.body) as { id: string };

  const acceptRes = await t.app.inject({
    method: 'POST',
    url: `/interests/${interest.id}/accept`,
    headers: authHeader(bob.accessToken),
  });
  assert.equal(acceptRes.statusCode, 200);
  const conversationId = (JSON.parse(acceptRes.body) as { conversation: { id: string } }).conversation.id;

  const messageRes = await t.app.inject({
    method: 'POST',
    url: `/conversations/${conversationId}/messages`,
    headers: authHeader(alice.accessToken),
    payload: { body: 'Hi Bob! No phone number required to get here.' },
  });
  assert.equal(messageRes.statusCode, 201);

  const venueId = await createVenue(t, { name: 'Core Loop Cafe' });
  const scheduledStart = new Date(t.clock.now().getTime() + 3 * 24 * 60 * 60 * 1000);
  const scheduledEnd = new Date(scheduledStart.getTime() + 60 * 60 * 1000);
  const proposeRes = await t.app.inject({
    method: 'POST',
    url: `/conversations/${conversationId}/date-proposals`,
    headers: authHeader(alice.accessToken),
    payload: { venueId, scheduledStart: scheduledStart.toISOString(), scheduledEnd: scheduledEnd.toISOString() },
  });
  assert.equal(proposeRes.statusCode, 201, 'a date can be proposed with no phone number on either account');
  assert.equal((JSON.parse(proposeRes.body) as { status: string }).status, 'pending_acceptance');

  for (const u of [alice, bob]) {
    const status = await authService.getMyPhoneStatus(userCtx(u.userId));
    assert.equal(status.hasPhone, false, 'neither account ever added a phone number during the loop above');
  }
});

test('a verified phone number never leaks through /me, /profiles/:id, /discovery, /matches, or the conversation timeline', async () => {
  const alice = await registerUser(t);
  const bob = await registerUser(t);
  await completeOnboarding(t, alice.accessToken, { displayName: 'AliceLeakCheck', gender: 'woman', seeking: 'man' });
  await completeOnboarding(t, bob.accessToken, { displayName: 'BobLeakCheck', gender: 'man', seeking: 'woman' });

  const PHONE = '+14155557788';
  await authService.requestPhoneVerification(userCtx(alice.userId), { phoneNumber: PHONE, country: 'US' });
  await seedKnownCode(alice.userId, '090909');
  await authService.verifyPhone(userCtx(alice.userId), { code: '090909' });

  function assertNoLeak(label: string, body: string): void {
    const lower = body.toLowerCase();
    assert.ok(!lower.includes('phone'), `${label}: response body must never mention "phone"`);
    assert.ok(!body.includes('5557788'), `${label}: response body must never contain the phone number's digits`);
    assert.ok(!body.includes(PHONE), `${label}: response body must never contain the full E.164 number`);
  }

  const meRes = await t.app.inject({ method: 'GET', url: '/me', headers: authHeader(alice.accessToken) });
  assert.equal(meRes.statusCode, 200);
  assertNoLeak('GET /me (the phone number owner\'s own account view)', meRes.body);

  const sendRes = await t.app.inject({
    method: 'POST',
    url: '/interests',
    headers: authHeader(bob.accessToken),
    payload: { recipientId: alice.userId },
  });
  const interest = JSON.parse(sendRes.body) as { id: string };
  const acceptRes = await t.app.inject({
    method: 'POST',
    url: `/interests/${interest.id}/accept`,
    headers: authHeader(alice.accessToken),
  });
  const conversationId = (JSON.parse(acceptRes.body) as { conversation: { id: string } }).conversation.id;

  const profileRes = await t.app.inject({
    method: 'GET',
    url: `/profiles/${alice.userId}`,
    headers: authHeader(bob.accessToken),
  });
  assert.equal(profileRes.statusCode, 200);
  assertNoLeak('GET /profiles/:userId (a match viewing the phone owner\'s public profile)', profileRes.body);

  const discoveryRes = await t.app.inject({ method: 'GET', url: '/discovery', headers: authHeader(bob.accessToken) });
  assert.equal(discoveryRes.statusCode, 200);
  assertNoLeak('GET /discovery (the phone owner\'s discovery card)', discoveryRes.body);

  await t.app.inject({
    method: 'POST',
    url: `/conversations/${conversationId}/messages`,
    headers: authHeader(alice.accessToken),
    payload: { body: 'Hello from the number owner, hope you are well.' },
  });

  const matchesRes = await t.app.inject({ method: 'GET', url: '/matches', headers: authHeader(bob.accessToken) });
  assert.equal(matchesRes.statusCode, 200);
  assertNoLeak('GET /matches (the match-list row for the phone owner)', matchesRes.body);

  const timelineRes = await t.app.inject({
    method: 'GET',
    url: `/conversations/${conversationId}/timeline`,
    headers: authHeader(bob.accessToken),
  });
  assert.equal(timelineRes.statusCode, 200);
  assertNoLeak('GET /conversations/:id/timeline', timelineRes.body);
});

test('HTTP routes: POST /auth/phone -> POST /auth/phone/verify -> GET /auth/phone -> DELETE /auth/phone round trip', async () => {
  const alice = await registerUser(t);

  const addRes = await t.app.inject({
    method: 'POST',
    url: '/auth/phone',
    headers: authHeader(alice.accessToken),
    payload: { phoneNumber: '+14155551313', country: 'US' },
  });
  assert.equal(addRes.statusCode, 202);

  let statusRes = await t.app.inject({ method: 'GET', url: '/auth/phone', headers: authHeader(alice.accessToken) });
  assert.equal(statusRes.statusCode, 200);
  let statusBody = JSON.parse(statusRes.body) as { hasPhone: boolean; verified: boolean; last2: string };
  assert.equal(statusBody.hasPhone, true);
  assert.equal(statusBody.verified, false);
  assert.equal(statusBody.last2, '13');
  assert.ok(!JSON.stringify(statusBody).includes('5551313'), 'GET /auth/phone must never return the full number');

  await seedKnownCode(alice.userId, '424242');
  const verifyRes = await t.app.inject({
    method: 'POST',
    url: '/auth/phone/verify',
    headers: authHeader(alice.accessToken),
    payload: { code: '424242' },
  });
  assert.equal(verifyRes.statusCode, 204);

  statusRes = await t.app.inject({ method: 'GET', url: '/auth/phone', headers: authHeader(alice.accessToken) });
  statusBody = JSON.parse(statusRes.body) as { hasPhone: boolean; verified: boolean; last2: string };
  assert.equal(statusBody.verified, true);

  const removeRes = await t.app.inject({ method: 'DELETE', url: '/auth/phone', headers: authHeader(alice.accessToken) });
  assert.equal(removeRes.statusCode, 204);

  statusRes = await t.app.inject({ method: 'GET', url: '/auth/phone', headers: authHeader(alice.accessToken) });
  statusBody = JSON.parse(statusRes.body) as { hasPhone: boolean; verified: boolean; last2: string };
  assert.equal(statusBody.hasPhone, false);
});

test('HTTP routes: /auth/phone requires authentication', async () => {
  const res = await t.app.inject({ method: 'POST', url: '/auth/phone', payload: { phoneNumber: '+14155551313', country: 'US' } });
  assert.equal(res.statusCode, 401);
});

test('static allowlist audit: no file under src/http/serializers/ mentions "phone" at all', () => {
  const here = dirname(fileURLToPath(import.meta.url));
  const serializersDir = join(here, '..', '..', 'src', 'http', 'serializers');
  const files = readdirSync(serializersDir).filter((f) => f.endsWith('.ts'));
  assert.ok(files.length > 0, 'sanity check: the serializers directory should not be empty');

  for (const file of files) {
    const source = readFileSync(join(serializersDir, file), 'utf8');
    assert.ok(
      !/phone/i.test(source),
      `${file} mentions "phone", every serializer is an explicit field allowlist (see each file's own doc comment); ` +
        'a phone number must never be named in any of them, since it must never reach another user or leave via any wire response',
    );
  }
});
