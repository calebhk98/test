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
// in-process rate limiter (§19.2) — reset it between tests so an earlier
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
  const reporter = await registerUser(t);
  const reported = await registerUser(t);

  // Threshold defaults: restriction at score 50; minor_suspected forces an
  // immediate suspension regardless of score (§18.3/§18.5) -- exercised
  // here with zero admin involvement, per C-18.1.1/C-4.3.7.
  const res = await t.app.inject({
    method: 'POST',
    url: '/reports',
    headers: authHeader(reporter.accessToken),
    payload: { reportedId: reported.userId, category: 'minor_suspected', details: 'concern' },
  });
  assert.equal(res.statusCode, 201);

  const { rows } = await t.pool.query(`SELECT action FROM moderation_actions WHERE user_id = $1 ORDER BY created_at DESC LIMIT 1`, [
    reported.userId,
  ]);
  assert.equal(rows[0]?.action, 'suspension');
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
