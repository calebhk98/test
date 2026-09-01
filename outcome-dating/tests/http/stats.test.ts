/**
 * HTTP tests for the two stats pages (user: `/me/stats*`, admin:
 * `/admin/stats/*`). Uses the shared `tests/http/testServer.ts` harness
 * (same `odate_http_<suite>_<runSuffix>` isolation every other
 * `tests/http/*.test.ts` file already relies on) rather than a bespoke
 * harness, so these routes are exercised through the real, fully-wired
 * Fastify app exactly like every sibling HTTP suite.
 *
 * Coverage:
 *  - role gating (no token -> 401; wrong role -> 403)
 *  - every admin stats access writes an admin_audit_log row (task brief:
 *    "every access audited like other admin routes" — a deliberately
 *    stronger bar than admin.routes.ts's read-routes-are-not-audited
 *    convention, see adminStats.routes.ts's module doc)
 *  - privacy: a user's own stats page never contains another identifiable
 *    user's id/email, even after a real interaction between two accounts
 *  - shape/sanity of every route's response for a fresh account
 */
import { test, before, after, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestApp, teardownTestApp, registerUser, authHeader, makeAdmin, resetRateLimiter } from './testServer.js';
import type { TestApp } from './testServer.js';
import { systemCtx } from '../../src/http/deps.js';
import { runStatsAggregationJob } from '../../src/jobs/statsAggregation.job.js';

let t: TestApp;

before(async () => {
  t = await setupTestApp('stats');
});

after(async () => {
  await teardownTestApp(t);
});

beforeEach(() => {
  resetRateLimiter(t);
});

// =====================================================================
// Role gating
// =====================================================================

test('GET /me/stats: no bearer token -> 401', async () => {
  const res = await t.app.inject({ method: 'GET', url: '/me/stats' });
  assert.equal(res.statusCode, 401);
});

test('GET /admin/stats/overview: no bearer token -> 401', async () => {
  const res = await t.app.inject({ method: 'GET', url: '/admin/stats/overview' });
  assert.equal(res.statusCode, 401);
});

test('GET /admin/stats/overview and /admin/stats/retention: a regular user is rejected with 403', async () => {
  const user = await registerUser(t);
  const overviewRes = await t.app.inject({ method: 'GET', url: '/admin/stats/overview', headers: authHeader(user.accessToken) });
  assert.equal(overviewRes.statusCode, 403);
  const retentionRes = await t.app.inject({ method: 'GET', url: '/admin/stats/retention', headers: authHeader(user.accessToken) });
  assert.equal(retentionRes.statusCode, 403);
});

test('GET /me/stats*: an admin actor (not a plain user) is rejected with 403', async () => {
  const admin = await registerUser(t);
  await makeAdmin(t, admin.userId);
  const res = await t.app.inject({ method: 'GET', url: '/me/stats', headers: authHeader(admin.accessToken) });
  assert.equal(res.statusCode, 403);
});

// =====================================================================
// Admin stats: access, audit, and freshness.
// =====================================================================

test('GET /admin/stats/overview: admin gets 200 and every access writes an admin_audit_log row', async () => {
  const admin = await registerUser(t);
  await makeAdmin(t, admin.userId);

  const before = await t.pool.query<{ count: string }>('SELECT count(*)::text AS count FROM admin_audit_log');

  const res = await t.app.inject({ method: 'GET', url: '/admin/stats/overview', headers: authHeader(admin.accessToken) });
  assert.equal(res.statusCode, 200);
  const body = JSON.parse(res.body);
  assert.ok(body.window);
  assert.ok(body.core);
  assert.ok(body.money);
  assert.ok(body.quality);
  assert.ok('freshness' in body);

  const after = await t.pool.query<{ count: string }>('SELECT count(*)::text AS count FROM admin_audit_log');
  assert.equal(Number(after.rows[0]!.count), Number(before.rows[0]!.count) + 1);

  const { rows: auditRows } = await t.pool.query(
    `SELECT admin_user_id, action, target_type FROM admin_audit_log WHERE admin_user_id = $1 AND action = 'stats.view_overview'`,
    [admin.userId],
  );
  assert.equal(auditRows.length, 1);
  assert.equal(auditRows[0].admin_user_id, admin.userId);
  assert.equal(auditRows[0].action, 'stats.view_overview');
  assert.equal(auditRows[0].target_type, 'stats_platform_daily');
});

test('GET /admin/stats/retention: admin gets 200 and writes an audit row', async () => {
  const admin = await registerUser(t);
  await makeAdmin(t, admin.userId);

  const before = await t.pool.query<{ count: string }>('SELECT count(*)::text AS count FROM admin_audit_log');
  const res = await t.app.inject({ method: 'GET', url: '/admin/stats/retention', headers: authHeader(admin.accessToken) });
  assert.equal(res.statusCode, 200);
  const body = JSON.parse(res.body);
  assert.ok(Array.isArray(body.cohorts));

  const after = await t.pool.query<{ count: string }>('SELECT count(*)::text AS count FROM admin_audit_log');
  assert.equal(Number(after.rows[0]!.count), Number(before.rows[0]!.count) + 1);
  const { rows: auditRows } = await t.pool.query(
    `SELECT action, target_type FROM admin_audit_log WHERE admin_user_id = $1 AND action = 'stats.view_retention'`,
    [admin.userId],
  );
  assert.equal(auditRows.length, 1);
  assert.equal(auditRows[0].target_type, 'stats_cohort_retention');
});

test('GET /admin/stats/overview reflects real registrations once the rollup job has run', async () => {
  const admin = await registerUser(t);
  await makeAdmin(t, admin.userId);
  await registerUser(t);
  await registerUser(t);

  await runStatsAggregationJob(systemCtx(t.deps, 'test'));

  const res = await t.app.inject({
    method: 'GET',
    url: '/admin/stats/overview?window=all',
    headers: authHeader(admin.accessToken),
  });
  assert.equal(res.statusCode, 200);
  const body = JSON.parse(res.body);
  assert.ok(body.core.registrations >= 3, `expected at least 3 registrations, got ${body.core.registrations}`);
  assert.ok(body.freshness.lastRunAt, 'freshness.lastRunAt should be populated once the job has run');
});

// =====================================================================
// User stats: shape for a fresh account, and privacy between two real
// interacting accounts.
// =====================================================================

test('GET /me/stats: 200 with a sane all-zero shape for a brand-new account', async () => {
  const user = await registerUser(t);
  const res = await t.app.inject({ method: 'GET', url: '/me/stats', headers: authHeader(user.accessToken) });
  assert.equal(res.statusCode, 200);
  const body = JSON.parse(res.body);
  assert.equal(body.funnel.interestsSent.total, 0);
  assert.equal(body.funnel.interestsReceived.total, 0);
  assert.equal(body.dateOutcomes.totalCheckIns, 0);
  assert.equal(typeof body.completeness.profileCompleteness, 'number');
});

test('GET /me/stats/trends, /me/stats/photos, /me/stats/filters: all 200 for a fresh account', async () => {
  const user = await registerUser(t);
  const trendsRes = await t.app.inject({ method: 'GET', url: '/me/stats/trends', headers: authHeader(user.accessToken) });
  assert.equal(trendsRes.statusCode, 200);
  assert.ok(Array.isArray(JSON.parse(trendsRes.body).points));

  const photosRes = await t.app.inject({ method: 'GET', url: '/me/stats/photos', headers: authHeader(user.accessToken) });
  assert.equal(photosRes.statusCode, 200);
  assert.deepEqual(JSON.parse(photosRes.body).photos, []);

  const filtersRes = await t.app.inject({ method: 'GET', url: '/me/stats/filters', headers: authHeader(user.accessToken) });
  assert.equal(filtersRes.statusCode, 200);
  const filtersBody = JSON.parse(filtersRes.body);
  assert.ok('currentPool' in filtersBody);
  assert.deepEqual(filtersBody.perFilter, []);
});

test('GET /me/stats/trends: rejects an out-of-range weeks parameter', async () => {
  const user = await registerUser(t);
  const res = await t.app.inject({ method: 'GET', url: '/me/stats/trends?weeks=999', headers: authHeader(user.accessToken) });
  assert.equal(res.statusCode, 400);
});

test('privacy: after a real interaction between two users, /me/stats never contains the other account\'s id or email', async () => {
  const alice = await registerUser(t);
  const bob = await registerUser(t);

  await t.app.inject({
    method: 'PATCH',
    url: '/me/profile',
    headers: authHeader(alice.accessToken),
    payload: { displayName: 'Alice', city: 'Springfield', age: 28, gender: 'woman', seeking: 'men', relationshipIntention: 'long_term' },
  });
  await t.app.inject({
    method: 'PATCH',
    url: '/me/profile',
    headers: authHeader(bob.accessToken),
    payload: { displayName: 'Bob', city: 'Springfield', age: 30, gender: 'man', seeking: 'women', relationshipIntention: 'long_term' },
  });

  const interestRes = await t.app.inject({
    method: 'POST',
    url: '/interests',
    headers: authHeader(alice.accessToken),
    payload: { recipientId: bob.userId },
  });
  assert.equal(interestRes.statusCode, 201);
  const interestId = JSON.parse(interestRes.body).id as string;

  const acceptRes = await t.app.inject({
    method: 'POST',
    url: `/interests/${interestId}/accept`,
    headers: authHeader(bob.accessToken),
  });
  assert.equal(acceptRes.statusCode, 200);

  const statsRes = await t.app.inject({ method: 'GET', url: '/me/stats', headers: authHeader(alice.accessToken) });
  assert.equal(statsRes.statusCode, 200);
  assert.ok(!statsRes.body.includes(bob.userId), "alice's stats page must never include bob's user id");
  assert.ok(!statsRes.body.includes(bob.email), "alice's stats page must never include bob's email");
  assert.equal(JSON.parse(statsRes.body).funnel.interestsSent.accepted, 1);

  const filtersRes = await t.app.inject({ method: 'GET', url: '/me/stats/filters', headers: authHeader(alice.accessToken) });
  assert.ok(!filtersRes.body.includes(bob.userId));

  const trendsRes = await t.app.inject({ method: 'GET', url: '/me/stats/trends', headers: authHeader(alice.accessToken) });
  assert.ok(!trendsRes.body.includes(bob.userId));
});
