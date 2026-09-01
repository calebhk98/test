/**
 * tests/http/admin.test.ts, HTTP coverage for `src/http/routes/admin.routes.ts`'s
 * §27 item 3 question manager (`GET/POST /admin/questions`,
 * `PATCH /admin/questions/:id`), repointed at the ONE typed question bank
 * (question_bank/user_question_answers, db/migrations/008_questions.sql)
 * per the question-system cutover, see question.service.ts's file-level
 * CUTOVER doc.
 *
 * Uses the shared `tests/http/testServer.ts` harness (same
 * `odate_http_<suite>_<runSuffix>` isolation every other
 * `tests/http/*.test.ts` file relies on).
 *
 * Coverage:
 *   - role gating (no token -> 401; a plain user -> 403).
 *   - an admin can create a question with the typed bank's full shape
 *     (type, options/typeDef, category/tags, sensitivity, baseWeight) and
 *     it is immediately visible via the ONE bank a user actually answers
 *     (`GET /questions`), the headline proof that this panel no longer
 *     grows a second, unscored bank.
 *   - editing a question inserts a NEW version rather than mutating in
 *     place (question_bank's versioning invariant), and the OLD version
 *     stops being listed as current.
 *   - every mutation writes an admin_audit_log row (task brief: "every
 *     admin mutation writes admin_audit_log").
 *   - a duplicate slug is rejected (ConflictError -> 409), matching
 *     `question.service#adminCreateQuestionBankEntry`'s own guard against
 *     the exact "recreate the same concept under a different definition"
 *     duplication the product owner flagged.
 */
import { test, before, after, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestApp, teardownTestApp, registerUser, authHeader, makeAdmin, resetRateLimiter } from './testServer.js';
import type { TestApp } from './testServer.js';

let t: TestApp;

before(async () => {
  t = await setupTestApp('admin');
});

after(async () => {
  await teardownTestApp(t);
});

beforeEach(() => {
  resetRateLimiter(t);
});

const SCALE_TYPE_DEF = { type: 'scale', min: 1, max: 5, minLabel: 'Not at all', maxLabel: 'Very much', midLabel: 'Somewhat' };

function baseQuestionBody(slug: string, overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    slug,
    category: 'lifestyle',
    subcategory: null,
    tags: ['test'],
    questionText: `How would you describe yourself on "${slug}"?`,
    typeDef: SCALE_TYPE_DEF,
    baseWeight: 1,
    sensitive: false,
    answerRateHint: 0.5,
    ...overrides,
  };
}

async function makeAdminUser(): Promise<{ userId: string; accessToken: string }> {
  const admin = await registerUser(t);
  await makeAdmin(t, admin.userId);
  return admin;
}

// =====================================================================
// Role gating
// =====================================================================

test('GET/POST /admin/questions, PATCH /admin/questions/:id: no bearer token -> 401', async () => {
  const getRes = await t.app.inject({ method: 'GET', url: '/admin/questions' });
  assert.equal(getRes.statusCode, 401);
  const postRes = await t.app.inject({ method: 'POST', url: '/admin/questions', payload: baseQuestionBody(`noauth-${Date.now()}`) });
  assert.equal(postRes.statusCode, 401);
  const patchRes = await t.app.inject({ method: 'PATCH', url: '/admin/questions/some-slug', payload: {} });
  assert.equal(patchRes.statusCode, 401);
});

test('GET/POST /admin/questions: a plain (non-admin) user is rejected with 403', async () => {
  const user = await registerUser(t);
  const getRes = await t.app.inject({ method: 'GET', url: '/admin/questions', headers: authHeader(user.accessToken) });
  assert.equal(getRes.statusCode, 403);
  const postRes = await t.app.inject({
    method: 'POST',
    url: '/admin/questions',
    headers: authHeader(user.accessToken),
    payload: baseQuestionBody(`plainuser-${Date.now()}`),
  });
  assert.equal(postRes.statusCode, 403);
});

// =====================================================================
// The headline fix: the admin panel manages the SAME bank users answer.
// =====================================================================

test('POST /admin/questions: creates a question in the ONE typed bank, and it is immediately visible via GET /questions (the bank users actually answer)', async () => {
  const admin = await makeAdminUser();
  const slug = `admin_created_${Date.now()}`;

  const createRes = await t.app.inject({
    method: 'POST',
    url: '/admin/questions',
    headers: authHeader(admin.accessToken),
    payload: baseQuestionBody(slug, { category: 'values', tags: ['family', 'lifestyle'], sensitive: true }),
  });
  assert.equal(createRes.statusCode, 201);
  const created = JSON.parse(createRes.body) as {
    id: string;
    slug: string;
    version: number;
    category: string;
    tags: string[];
    sensitive: boolean;
    baseWeight: number;
    typeDef: unknown;
  };
  assert.equal(created.slug, slug);
  assert.equal(created.version, 1);
  assert.equal(created.category, 'values');
  assert.deepEqual(created.tags, ['family', 'lifestyle']);
  assert.equal(created.sensitive, true);
  assert.equal(created.baseWeight, 1);
  // Internal scoring-tuning fields end users never see are absent from
  // the CLIENT-facing question card, but present in the admin view,
  // sanity-check the admin view actually carries them (see
  // serializers/questions.ts's AdminQuestionView vs QuestionCardView).
  assert.deepEqual(created.typeDef, SCALE_TYPE_DEF);

  // The user-facing route (`GET /questions`, driven by
  // `question.service#listActiveQuestionBank`) must see it too, same
  // bank, not a shadow copy.
  const user = await registerUser(t);
  const listRes = await t.app.inject({ method: 'GET', url: '/questions?limit=200', headers: authHeader(user.accessToken) });
  assert.equal(listRes.statusCode, 200);
  const listBody = JSON.parse(listRes.body) as { items: Array<{ slug: string }> };
  assert.ok(listBody.items.some((q) => q.slug === slug), 'a question created via the admin panel must appear in the bank users actually answer');
});

test('POST /admin/questions: every field the typed bank needs (type, options, importance-relevant sensitivity, versioning) round-trips through the admin panel', async () => {
  const admin = await makeAdminUser();
  const slug = `admin_choice_${Date.now()}`;

  const typeDef = {
    type: 'single_choice',
    options: [
      { key: 'no_kids', label: 'No children' },
      { key: 'has_kids', label: 'Has children' },
    ],
  };
  const createRes = await t.app.inject({
    method: 'POST',
    url: '/admin/questions',
    headers: authHeader(admin.accessToken),
    payload: baseQuestionBody(slug, { typeDef, category: 'family' }),
  });
  assert.equal(createRes.statusCode, 201);
  const created = JSON.parse(createRes.body) as { typeDef: unknown; presentation: string };
  assert.deepEqual(created.typeDef, typeDef);
  // A two-option single_choice question must be flagged `ladder`, the
  // client-rendering signal a client must never infer itself.
  assert.equal(created.presentation, 'ladder');
});

test('POST /admin/questions: a duplicate slug is rejected (409), an admin cannot recreate the same concept under a second definition', async () => {
  const admin = await makeAdminUser();
  const slug = `admin_dup_${Date.now()}`;

  const first = await t.app.inject({
    method: 'POST',
    url: '/admin/questions',
    headers: authHeader(admin.accessToken),
    payload: baseQuestionBody(slug),
  });
  assert.equal(first.statusCode, 201);

  const second = await t.app.inject({
    method: 'POST',
    url: '/admin/questions',
    headers: authHeader(admin.accessToken),
    payload: baseQuestionBody(slug),
  });
  assert.equal(second.statusCode, 409);
});

// =====================================================================
// Editing versions rather than mutating in place.
// =====================================================================

test('PATCH /admin/questions/:id: editing a question inserts a NEW version and retires the old one, not an in-place mutation', async () => {
  const admin = await makeAdminUser();
  const slug = `admin_edit_${Date.now()}`;

  const createRes = await t.app.inject({
    method: 'POST',
    url: '/admin/questions',
    headers: authHeader(admin.accessToken),
    payload: baseQuestionBody(slug, { questionText: 'Original wording' }),
  });
  const created = JSON.parse(createRes.body) as { id: string; version: number };
  assert.equal(created.version, 1);

  const patchRes = await t.app.inject({
    method: 'PATCH',
    url: `/admin/questions/${slug}`,
    headers: authHeader(admin.accessToken),
    payload: { questionText: 'Revised wording' },
  });
  assert.equal(patchRes.statusCode, 200);
  const updated = JSON.parse(patchRes.body) as { id: string; version: number; questionText: string };
  assert.equal(updated.version, 2, 'editing must bump the version, never reuse it');
  assert.notEqual(updated.id, created.id, 'a new version is a NEW row, not the same row mutated in place');
  assert.equal(updated.questionText, 'Revised wording');

  // Only the new version is "current", GET /admin/questions (default:
  // includeInactive so retired/older rows are still visible to an admin)
  // must show the revised text under this slug exactly once, not twice.
  const listRes = await t.app.inject({ method: 'GET', url: '/admin/questions', headers: authHeader(admin.accessToken) });
  const items = JSON.parse(listRes.body) as Array<{ slug: string; questionText: string; version: number }>;
  const matches = items.filter((q) => q.slug === slug);
  assert.equal(matches.length, 1, 'only the current version of a slug should be listed');
  assert.equal(matches[0]!.version, 2);
  assert.equal(matches[0]!.questionText, 'Revised wording');
});

test('PATCH /admin/questions/:id: an admin can deactivate a question (active:false) without deleting its history', async () => {
  const admin = await makeAdminUser();
  const slug = `admin_deactivate_${Date.now()}`;
  await t.app.inject({ method: 'POST', url: '/admin/questions', headers: authHeader(admin.accessToken), payload: baseQuestionBody(slug) });

  const patchRes = await t.app.inject({
    method: 'PATCH',
    url: `/admin/questions/${slug}`,
    headers: authHeader(admin.accessToken),
    payload: { active: false },
  });
  assert.equal(patchRes.statusCode, 200);
  const updated = JSON.parse(patchRes.body) as { active: boolean };
  assert.equal(updated.active, false);

  // Deactivated questions no longer show up in the user-facing bank...
  const user = await registerUser(t);
  const listRes = await t.app.inject({ method: 'GET', url: '/questions?limit=200', headers: authHeader(user.accessToken) });
  const listBody = JSON.parse(listRes.body) as { items: Array<{ slug: string }> };
  assert.ok(!listBody.items.some((q) => q.slug === slug), 'a deactivated question must not appear in GET /questions');

  // ...but an admin can still find it (includeInactive defaults to true).
  const adminListRes = await t.app.inject({ method: 'GET', url: '/admin/questions', headers: authHeader(admin.accessToken) });
  const adminItems = JSON.parse(adminListRes.body) as Array<{ slug: string; active: boolean }>;
  assert.ok(adminItems.some((q) => q.slug === slug && q.active === false), 'an admin must still be able to find a deactivated question to review/reactivate it');
});

// =====================================================================
// Audit logging (every admin mutation writes admin_audit_log).
// =====================================================================

test('every mutating admin question-manager route writes an admin_audit_log row', async () => {
  const admin = await makeAdminUser();
  const slug = `admin_audit_${Date.now()}`;

  const before = await t.pool.query<{ count: string }>('SELECT count(*)::text AS count FROM admin_audit_log');

  const createRes = await t.app.inject({
    method: 'POST',
    url: '/admin/questions',
    headers: authHeader(admin.accessToken),
    payload: baseQuestionBody(slug),
  });
  assert.equal(createRes.statusCode, 201);

  await t.app.inject({
    method: 'PATCH',
    url: `/admin/questions/${slug}`,
    headers: authHeader(admin.accessToken),
    payload: { active: false },
  });

  const after = await t.pool.query<{ count: string }>('SELECT count(*)::text AS count FROM admin_audit_log');
  assert.equal(Number(after.rows[0]!.count) - Number(before.rows[0]!.count), 2, 'one admin_audit_log row per mutation (create + update)');

  const { rows } = await t.pool.query<{ action: string; target_type: string }>(
    `SELECT action, target_type FROM admin_audit_log WHERE admin_user_id = $1 ORDER BY created_at`,
    [admin.userId],
  );
  assert.ok(rows.some((r) => r.action === 'question.create' && r.target_type === 'question_bank'));
  assert.ok(rows.some((r) => r.action === 'question.update' && r.target_type === 'question_bank'));
});
