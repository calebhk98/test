/**
 * tests/http/trustExposure.test.ts — end-to-end proof for docs/duplication.md
 * finding 1 (the trust-score exposure gate).
 *
 * Before the fix: `GET /me/trust` gated the numeric `trustScore` field
 * through an ad-hoc, unseeded, per-user feature flag
 * (`expose_trust_score_to_user`) that nothing in this codebase ever set —
 * the documented `trust.expose_raw_score` config key
 * (`trust.service#shouldExposeRawTrustScore`, whose own doc comment calls
 * it "the single source of truth for the display gate") was never
 * consulted by the route at all. An admin flipping the documented key had
 * zero effect on the live response.
 *
 * This is deliberately an HTTP test that drives the REAL route via
 * `app.inject`, not a unit test of the gate function in isolation — a unit
 * test of `shouldExposeRawTrustScore` already existed
 * (`tests/unit/decisionsConfig.test.ts`) and passed the whole time the
 * route ignored it, which is exactly the blind spot this test closes.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestApp, teardownTestApp, registerUser, authHeader } from './testServer.js';
import type { TestApp } from './testServer.js';

let t: TestApp;

before(async () => {
  t = await setupTestApp('trust_exposure');
});

after(async () => {
  await teardownTestApp(t);
});

test('GET /me/trust: trustScore is hidden by default (trust.expose_raw_score defaults false)', async () => {
  const user = await registerUser(t);
  const res = await t.app.inject({ method: 'GET', url: '/me/trust', headers: authHeader(user.accessToken) });
  assert.equal(res.statusCode, 200);
  const body = JSON.parse(res.body) as { trustLevel: string; trustScore?: number };
  assert.equal(typeof body.trustLevel, 'string', 'trustLevel is always present');
  assert.equal('trustScore' in body, false, 'trustScore must be withheld by default');
});

test('GET /me/trust: setting trust.expose_raw_score=true makes trustScore appear, and =false hides it again — the documented config key actually controls the live response', async () => {
  const user = await registerUser(t);

  // 1. Default: hidden.
  const before1 = await t.app.inject({ method: 'GET', url: '/me/trust', headers: authHeader(user.accessToken) });
  assert.equal('trustScore' in JSON.parse(before1.body), false);

  // 2. Admin flips the DOCUMENTED key on. This is the exact control an
  //    operator has — no route/serializer code path other than this key
  //    should be able to move the field.
  await t.deps.config.set('trust.expose_raw_score', true, 'test-admin');

  const after1 = await t.app.inject({ method: 'GET', url: '/me/trust', headers: authHeader(user.accessToken) });
  assert.equal(after1.statusCode, 200);
  const bodyAfter1 = JSON.parse(after1.body) as { trustLevel: string; trustScore?: number };
  assert.equal('trustScore' in bodyAfter1, true, 'trustScore must appear once trust.expose_raw_score=true');
  assert.equal(typeof bodyAfter1.trustScore, 'number');
  assert.ok(bodyAfter1.trustScore! >= 0 && bodyAfter1.trustScore! <= 100);

  // 3. Flip it back off — must disappear again, proving the gate is live
  //    in both directions, not just "on by accident".
  await t.deps.config.set('trust.expose_raw_score', false, 'test-admin');

  const after2 = await t.app.inject({ method: 'GET', url: '/me/trust', headers: authHeader(user.accessToken) });
  const bodyAfter2 = JSON.parse(after2.body) as { trustLevel: string; trustScore?: number };
  assert.equal('trustScore' in bodyAfter2, false, 'trustScore must be withheld again once trust.expose_raw_score=false');
});

test('GET /me/trust: trustLevel and the rest of the summary are unaffected by the exposure gate', async () => {
  const user = await registerUser(t);
  await t.deps.config.set('trust.expose_raw_score', true, 'test-admin');

  const res = await t.app.inject({ method: 'GET', url: '/me/trust', headers: authHeader(user.accessToken) });
  const body = JSON.parse(res.body) as {
    trustLevel: string;
    trustScore?: number;
    actionableImprovements: string[];
    recentNegativeEvents: string[];
  };
  assert.deepEqual(Object.keys(body).sort(), ['actionableImprovements', 'recentNegativeEvents', 'trustLevel', 'trustScore'].sort());
  assert.ok(Array.isArray(body.actionableImprovements));
  assert.ok(Array.isArray(body.recentNegativeEvents));

  await t.deps.config.set('trust.expose_raw_score', false, 'test-admin'); // restore default for later tests
});
