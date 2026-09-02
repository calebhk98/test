/**
 * Role-boundary tests (spec §4, C-4.RBAC.1/2, C-4.2.4/5/6, C-24.2-4,
 * C-28.6.1): a regular user is rejected from `/admin/*` and `/venue/*`; a
 * venue-staff token is rejected from user routes (especially
 * `/conversations/*`, the "no chats" invariant) and from `/admin/*`; every
 * admin mutation writes an `admin_audit_log` row.
 */
import { test, before, beforeEach, after } from 'node:test';
import assert from 'node:assert/strict';
import {
  setupTestApp,
  teardownTestApp,
  registerUser,
  authHeader,
  makeAdmin,
  makeVenueStaff,
  createVenue,
  resetRateLimiter,
} from './testServer.js';
import type { TestApp } from './testServer.js';

let t: TestApp;

before(async () => {
  t = await setupTestApp('roles');
});

after(async () => {
  await teardownTestApp(t);
});

// This suite registers many accounts across scenarios against one shared
// in-process rate limiter (§19.2), reset it between tests so an earlier
// scenario's registrations never spuriously 429 a later, unrelated one.
// `tests/http/rateLimit.test.ts` is where the limiter's own behavior is
// actually exercised.
beforeEach(() => {
  resetRateLimiter(t);
});

test('no bearer token -> 401 on a protected route', async () => {
  const res = await t.app.inject({ method: 'GET', url: '/me' });
  assert.equal(res.statusCode, 401);
  assert.equal(JSON.parse(res.body).error.code, 'unauthorized');
});

test('garbage bearer token -> 401', async () => {
  const res = await t.app.inject({ method: 'GET', url: '/me', headers: { authorization: 'Bearer garbage.token' } });
  assert.equal(res.statusCode, 401);
});

test('C-4.RBAC.1: a regular user calling any /admin/* route is rejected with 403', async () => {
  const user = await registerUser(t);
  const res = await t.app.inject({ method: 'GET', url: '/admin/config', headers: authHeader(user.accessToken) });
  assert.equal(res.statusCode, 403);
  assert.equal(JSON.parse(res.body).error.code, 'forbidden');
});

test('C-4.RBAC.2 / C-24.3: a regular user calling /venue/redeem is rejected with 403', async () => {
  const user = await registerUser(t);
  const res = await t.app.inject({
    method: 'POST',
    url: '/venue/redeem',
    headers: authHeader(user.accessToken),
    payload: { code: 'ABCDEFGH' },
  });
  assert.equal(res.statusCode, 403);
});

test('C-4.2.4: venue staff calling /conversations/* is rejected with 403 (never sees chats)', async () => {
  const staffUser = await registerUser(t);
  await makeVenueStaff(t, staffUser.userId);

  const listRes = await t.app.inject({ method: 'GET', url: '/conversations', headers: authHeader(staffUser.accessToken) });
  assert.equal(listRes.statusCode, 403);

  const messagesRes = await t.app.inject({
    method: 'GET',
    url: '/conversations/00000000-0000-0000-0000-000000000000/messages',
    headers: authHeader(staffUser.accessToken),
  });
  assert.equal(messagesRes.statusCode, 403);
});

test('venue staff calling /admin/* is rejected with 403', async () => {
  const staffUser = await registerUser(t);
  await makeVenueStaff(t, staffUser.userId);
  const res = await t.app.inject({ method: 'GET', url: '/admin/users', headers: authHeader(staffUser.accessToken) });
  assert.equal(res.statusCode, 403);
});

test('venue staff calling other user-only routes (discovery, payment-methods) is rejected with 403', async () => {
  const staffUser = await registerUser(t);
  await makeVenueStaff(t, staffUser.userId);

  const discoveryRes = await t.app.inject({ method: 'GET', url: '/discovery', headers: authHeader(staffUser.accessToken) });
  assert.equal(discoveryRes.statusCode, 403);

  const paymentMethodsRes = await t.app.inject({ method: 'GET', url: '/payment-methods', headers: authHeader(staffUser.accessToken) });
  assert.equal(paymentMethodsRes.statusCode, 403);
});

test('C-4.2.1/2: venue staff CAN list upcoming vouchers and redeem for their own venue', async () => {
  const staffUser = await registerUser(t);
  const venueId = await makeVenueStaff(t, staffUser.userId);

  const listRes = await t.app.inject({ method: 'GET', url: '/venue/vouchers', headers: authHeader(staffUser.accessToken) });
  assert.equal(listRes.statusCode, 200);
  assert.deepEqual(JSON.parse(listRes.body), []);

  const redeemRes = await t.app.inject({
    method: 'POST',
    url: '/venue/redeem',
    headers: authHeader(staffUser.accessToken),
    payload: { code: 'DOESNOTEXIST' },
  });
  // Not found rather than forbidden -- proves the role gate itself passed.
  assert.equal(redeemRes.statusCode, 404);
  void venueId;
});

test('admin CAN reach /admin/* and a mutation writes an admin_audit_log row', async () => {
  const admin = await registerUser(t);
  await makeAdmin(t, admin.userId);

  const before = await t.pool.query('SELECT count(*)::int AS count FROM admin_audit_log');

  const res = await t.app.inject({
    method: 'PATCH',
    url: '/admin/config',
    headers: authHeader(admin.accessToken),
    payload: { key: 'interest.outgoing_pending_limit', value: 7 },
  });
  assert.equal(res.statusCode, 200);
  assert.equal(JSON.parse(res.body).value, 7);

  const after = await t.pool.query('SELECT count(*)::int AS count FROM admin_audit_log');
  assert.equal(after.rows[0].count, before.rows[0].count + 1);

  const { rows: auditRows } = await t.pool.query(
    `SELECT admin_user_id, action, target_type, target_id FROM admin_audit_log ORDER BY created_at DESC LIMIT 1`,
  );
  assert.equal(auditRows[0].admin_user_id, admin.userId);
  assert.equal(auditRows[0].action, 'config.set');
  assert.equal(auditRows[0].target_type, 'config_entries');
  assert.equal(auditRows[0].target_id, 'interest.outgoing_pending_limit');
});

test('admin mutations across venues/questions/feature-flags all write audit rows', async () => {
  const admin = await registerUser(t);
  await makeAdmin(t, admin.userId);

  const before = await t.pool.query('SELECT count(*)::int AS count FROM admin_audit_log');

  const venueRes = await t.app.inject({
    method: 'POST',
    url: '/admin/venues',
    headers: authHeader(admin.accessToken),
    payload: {
      name: 'Audit Test Venue',
      address: '1 Audit Way',
      latitude: 1,
      longitude: 1,
      category: 'coffee',
      marginPercent: 10,
      timeSlots: [],
      redemptionMethod: 'qr_scan',
    },
  });
  assert.equal(venueRes.statusCode, 201);

  const flagRes = await t.app.inject({
    method: 'POST',
    url: '/admin/feature-flags',
    headers: authHeader(admin.accessToken),
    payload: { key: 'photo_ab_testing', enabled: true, rolloutPercent: 50 },
  });
  assert.equal(flagRes.statusCode, 200);

  const after = await t.pool.query('SELECT count(*)::int AS count FROM admin_audit_log');
  assert.equal(after.rows[0].count, before.rows[0].count + 2);
});

test('§18.1: moderation pipeline runs to completion with zero admin endpoints called', async () => {
  const reported = await registerUser(t);

  // SAF-1 fix (docs/risk-review.md): a single, uncorroborated
  // minor_suspected report used to force an immediate suspension on its
  // own -- a one-click weapon letting any account suspend any other with
  // one unverified report. That has been deliberately fixed: one credible
  // report now applies only a fast, reversible interim restriction, and
  // it takes >= moderation.minor_suspected_min_corroborating_reporters
  // (default 2) DISTINCT, non-clustered credible reports before automated
  // suspension applies. This test used to assert the OLD ("one report ->
  // suspension") behavior; it is updated here to assert the fixed
  // behavior instead, per test-audit.md's item 6 -- not reverted back to
  // the vulnerable version.
  //
  // A report only counts as "credible" from an account at least
  // moderation.minor_suspected_reporter_min_account_age_hours old (default
  // 24h) -- backdate `users.created_at` directly (same technique
  // `tests/unit/safetyFixes.test.ts` uses) rather than advancing this
  // suite's shared clock, which every other test in this file also reads.
  async function backdatedCredibleReporter(daysOld: number) {
    const reporter = await registerUser(t);
    await t.pool.query(`UPDATE users SET created_at = $1 WHERE id = $2`, [
      new Date(t.clock.now().getTime() - daysOld * 24 * 60 * 60 * 1000),
      reporter.userId,
    ]);
    return reporter;
  }

  // `t.clock` is a `ManualClock` this whole file shares and never advances
  // (see testServer.ts), so the two `moderation_actions` rows this test
  // triggers below can legitimately land on the EXACT same `created_at`
  // (moderation.service.ts writes it from `ctx.clock.now()`, see that
  // file's own CC-12 fix doc comment). `created_at DESC` alone leaves
  // that tie's order unspecified; break it the same way
  // `moderation.service.ts` itself now does internally
  // (`ACTION_SEVERITY_SQL_CASE`): a later row from `applyThresholds` is
  // never a lower severity than an earlier one for the same user (see
  // that function's own "never LESS protective" guard), so highest
  // severity among tied timestamps is always the genuinely most recent.
  const ACTION_SEVERITY_SQL_CASE = `CASE action
    WHEN 'suspension' THEN 4
    WHEN 'shadowban' THEN 3
    WHEN 'restriction' THEN 2
    WHEN 'warning' THEN 1
    ELSE 0
  END`;
  async function latestModerationAction(userId: string): Promise<{ action: string; reason: string } | undefined> {
    const { rows } = await t.pool.query<{ action: string; reason: string }>(
      `SELECT action, reason FROM moderation_actions WHERE user_id = $1
       ORDER BY created_at DESC, ${ACTION_SEVERITY_SQL_CASE} DESC LIMIT 1`,
      [userId],
    );
    return rows[0];
  }

  const reporter1 = await backdatedCredibleReporter(90);
  const res1 = await t.app.inject({
    method: 'POST',
    url: '/reports',
    headers: authHeader(reporter1.accessToken),
    payload: { reportedId: reported.userId, category: 'minor_suspected', details: 'concern' },
  });
  assert.equal(res1.statusCode, 201);

  const afterFirst = await latestModerationAction(reported.userId);
  assert.equal(afterFirst?.action, 'restriction', 'one credible report: a fast, reversible interim restriction, never suspension');
  assert.equal(afterFirst?.reason, 'minor_suspected_report_interim_protective_action');

  // A second, DISTINCT, non-clustered credible reporter (a different
  // account-age bucket so no account-creation-proximity clustering
  // signal fires either) corroborates the signal -- this is the "still
  // suspends quickly" half of the fix.
  const reporter2 = await backdatedCredibleReporter(45);
  const res2 = await t.app.inject({
    method: 'POST',
    url: '/reports',
    headers: authHeader(reporter2.accessToken),
    payload: { reportedId: reported.userId, category: 'minor_suspected', details: 'also concerning' },
  });
  assert.equal(res2.statusCode, 201);

  const afterSecond = await latestModerationAction(reported.userId);
  assert.equal(afterSecond?.action, 'suspension', 'two corroborating credible reports must still suspend fast');
  assert.equal(afterSecond?.reason, 'minor_suspected_report_immediate_protective_action');
});

test('§30.6.1: admin can mark a venue inactive', async () => {
  const admin = await registerUser(t);
  await makeAdmin(t, admin.userId);
  const venueId = await createVenue(t, { active: true });

  const res = await t.app.inject({
    method: 'PATCH',
    url: `/admin/venues/${venueId}`,
    headers: authHeader(admin.accessToken),
    payload: { active: false },
  });
  assert.equal(res.statusCode, 200);
  assert.equal(JSON.parse(res.body).active, false);
});
