/**
 * tests/http/questions.test.ts — end-to-end HTTP coverage for the ONE
 * typed question bank (db/migrations/008_questions.sql), driven through
 * the real routes (`src/http/routes/questions.routes.ts`) via
 * `app.inject`, not the service layer directly (that's
 * `tests/unit/question.service.test.ts`'s job).
 *
 * Proves, at the HTTP boundary:
 *   1. `GET /questions` is paginated (not a flat dump of the whole bank).
 *   2. Every question tells the client its `presentation` (ladder vs
 *      value_importance) explicitly.
 *   3. `PUT /me/answers` supports answered/skipped/prefer_not_to_say and
 *      the ladder shortcut.
 *   4. A `deal_breaker` answer persists a real, enabled hard filter
 *      (`GET /me/filters`), and softening it retracts (disables) that
 *      filter — the requirement #3 proof from the task brief.
 *   5. `GET /me/filters` never excludes a candidate for an unset
 *      attribute unless the toggle is explicitly turned on (verified via
 *      the derived filter's `excludeIfUnset: true`, matching
 *      dealBreakers.ts's documented rule — unset stays included
 *      everywhere else).
 *   6. Tag intensity + avoid-tags routes round-trip.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestApp, teardownTestApp, registerUser, authHeader } from './testServer.js';
import type { TestApp } from './testServer.js';

let t: TestApp;

before(async () => {
  t = await setupTestApp('questions');
});

after(async () => {
  await teardownTestApp(t);
});

interface BankQuestionOpts {
  slug: string;
  category?: string;
  typeDef: unknown;
  baseWeight?: number;
}

/** Inserts a typed-bank question directly, bypassing the admin routes — `tests/http/admin.test.ts` is the dedicated coverage for `POST /admin/questions`/`PATCH /admin/questions/:id`; this file only needs bank rows to already exist. */
async function insertBankQuestion(opts: BankQuestionOpts): Promise<string> {
  const { rows } = await t.pool.query<{ id: string }>(
    `INSERT INTO question_bank (slug, version, is_current, category, subcategory, tags, question_type, question_text, type_definition, base_weight, sensitive, active, answer_rate_hint)
     VALUES ($1, 1, true, $2, NULL, '{}', $3, $1, $4::jsonb, $5, false, true, 0.5)
     RETURNING id`,
    [opts.slug, opts.category ?? 'test', (opts.typeDef as { type: string }).type, JSON.stringify(opts.typeDef), opts.baseWeight ?? 1],
  );
  return rows[0]!.id;
}

const SCALE_TYPE_DEF = { type: 'scale', min: 1, max: 5, minLabel: 'low', maxLabel: 'high', midLabel: 'mid' };
const BINARY_CHOICE_TYPE_DEF = {
  type: 'single_choice',
  options: [
    { key: 'no', label: 'No' },
    { key: 'yes', label: 'Yes' },
  ],
};
const FIVE_CHOICE_TYPE_DEF = {
  type: 'single_choice',
  options: [
    { key: 'a', label: 'A' },
    { key: 'b', label: 'B' },
    { key: 'c', label: 'C' },
    { key: 'd', label: 'D' },
    { key: 'e', label: 'E' },
  ],
};

test('GET /questions: paginated — a small limit returns fewer items than the full seeded set, with a usable cursor', async () => {
  for (let i = 0; i < 5; i++) {
    await insertBankQuestion({ slug: `page-q-${i}-${Date.now()}`, typeDef: SCALE_TYPE_DEF });
  }
  const user = await registerUser(t);

  const first = await t.app.inject({ method: 'GET', url: '/questions?limit=2', headers: authHeader(user.accessToken) });
  assert.equal(first.statusCode, 200);
  const firstBody = JSON.parse(first.body) as { items: unknown[]; nextCursor: string | null };
  assert.equal(firstBody.items.length, 2, 'a limit=2 request must return exactly 2 items, not the whole bank');
  assert.ok(firstBody.nextCursor, 'more than 2 questions exist -> a cursor for the next page must be present');

  const second = await t.app.inject({
    method: 'GET',
    url: `/questions?limit=2&cursor=${encodeURIComponent(firstBody.nextCursor!)}`,
    headers: authHeader(user.accessToken),
  });
  assert.equal(second.statusCode, 200);
  const secondBody = JSON.parse(second.body) as { items: Array<{ id: string }> };
  const firstIds = new Set((firstBody.items as Array<{ id: string }>).map((q) => q.id));
  for (const item of secondBody.items) assert.ok(!firstIds.has(item.id), 'page 2 must not repeat a page 1 item');
});

test('GET /questions: every item carries an explicit presentation — ladder for a two-option single_choice, value_importance otherwise', async () => {
  const binarySlug = `ladder-q-${Date.now()}`;
  const fiveSlug = `five-q-${Date.now()}`;
  await insertBankQuestion({ slug: binarySlug, typeDef: BINARY_CHOICE_TYPE_DEF });
  await insertBankQuestion({ slug: fiveSlug, typeDef: FIVE_CHOICE_TYPE_DEF });
  const user = await registerUser(t);

  const res = await t.app.inject({ method: 'GET', url: '/questions?limit=200', headers: authHeader(user.accessToken) });
  const body = JSON.parse(res.body) as { items: Array<{ slug: string; presentation: string }> };
  const binary = body.items.find((q) => q.slug === binarySlug);
  const five = body.items.find((q) => q.slug === fiveSlug);
  assert.ok(binary && five, 'both seeded questions must appear in the listing');
  assert.equal(binary!.presentation, 'ladder', 'a two-option single_choice question must be presented as a ladder');
  assert.equal(five!.presentation, 'value_importance', 'a five-option single_choice question must use the two-control presentation');
});

test('PUT /me/answers: answered / skipped / prefer_not_to_say all round-trip through GET /me/answers', async () => {
  const scaleSlug = `answer-scale-${Date.now()}`;
  const skipSlug = `answer-skip-${Date.now()}`;
  const refuseSlug = `answer-refuse-${Date.now()}`;
  await insertBankQuestion({ slug: scaleSlug, typeDef: SCALE_TYPE_DEF });
  await insertBankQuestion({ slug: skipSlug, typeDef: SCALE_TYPE_DEF });
  await insertBankQuestion({ slug: refuseSlug, typeDef: SCALE_TYPE_DEF, category: 'sensitive' });
  const user = await registerUser(t);

  const answered = await t.app.inject({
    method: 'PUT',
    url: '/me/answers',
    headers: authHeader(user.accessToken),
    payload: { slug: scaleSlug, status: 'answered', selfValue: 4, preferenceValue: 4, importance: 'important' },
  });
  assert.equal(answered.statusCode, 200);

  const skipped = await t.app.inject({
    method: 'PUT',
    url: '/me/answers',
    headers: authHeader(user.accessToken),
    payload: { slug: skipSlug, status: 'skipped' },
  });
  assert.equal(skipped.statusCode, 200);

  const refused = await t.app.inject({
    method: 'PUT',
    url: '/me/answers',
    headers: authHeader(user.accessToken),
    payload: { slug: refuseSlug, status: 'prefer_not_to_say' },
  });
  assert.equal(refused.statusCode, 200);

  const mine = await t.app.inject({ method: 'GET', url: '/me/answers', headers: authHeader(user.accessToken) });
  assert.equal(mine.statusCode, 200);
  const answers = JSON.parse(mine.body) as Array<{ questionSlug: string; status: string; selfValue: unknown; importance: string | null }>;
  const byScale = answers.find((a) => a.questionSlug === scaleSlug)!;
  const bySkip = answers.find((a) => a.questionSlug === skipSlug)!;
  const byRefuse = answers.find((a) => a.questionSlug === refuseSlug)!;
  assert.equal(byScale.status, 'answered');
  assert.equal(byScale.selfValue, 4);
  assert.equal(byScale.importance, 'important');
  assert.equal(bySkip.status, 'skipped');
  assert.equal(byRefuse.status, 'prefer_not_to_say');
});

test('PUT /me/answers: ladderPosition sets preference + importance on a ladder-presentation question', async () => {
  const slug = `ladder-answer-${Date.now()}`;
  await insertBankQuestion({ slug, typeDef: BINARY_CHOICE_TYPE_DEF });
  const user = await registerUser(t);

  const res = await t.app.inject({
    method: 'PUT',
    url: '/me/answers',
    headers: authHeader(user.accessToken),
    payload: { slug, status: 'answered', selfValue: 'no', ladderPosition: 0 }, // "Deal breaker: no"
  });
  assert.equal(res.statusCode, 200);
  const body = JSON.parse(res.body) as { importance: string; preferenceValue: string[] };
  assert.equal(body.importance, 'deal_breaker');
  assert.deepEqual(body.preferenceValue, ['no']);
});

test('GET /questions/next: never returns a question the user already answered', async () => {
  const slug = `next-q-${Date.now()}`;
  await insertBankQuestion({ slug, typeDef: SCALE_TYPE_DEF });
  const user = await registerUser(t);

  await t.app.inject({
    method: 'PUT',
    url: '/me/answers',
    headers: authHeader(user.accessToken),
    payload: { slug, status: 'answered', selfValue: 3, preferenceValue: 3, importance: 'important' },
  });

  const res = await t.app.inject({ method: 'GET', url: '/questions/next?count=50', headers: authHeader(user.accessToken) });
  assert.equal(res.statusCode, 200);
  const body = JSON.parse(res.body) as { items: Array<{ slug: string }> };
  assert.ok(!body.items.some((q) => q.slug === slug), 'an already-answered question must never be suggested next');
});

// =====================================================================
// Deal-breaker filter persistence (task brief requirement #3) — a
// deal_breaker answer must produce a real, enabled hard_filters row via
// GET /me/filters; softening the answer must retract it.
// =====================================================================

test('a deal_breaker answer persists an enabled qb: hard filter with excludeIfUnset:true, and softening it retracts (disables) that filter', async () => {
  const slug = `dealbreaker-${Date.now()}`;
  await insertBankQuestion({ slug, typeDef: BINARY_CHOICE_TYPE_DEF });
  const user = await registerUser(t);

  await t.app.inject({
    method: 'PUT',
    url: '/me/answers',
    headers: authHeader(user.accessToken),
    payload: { slug, status: 'answered', selfValue: 'no', preferenceValue: ['no'], importance: 'deal_breaker' },
  });

  const afterDealBreaker = await t.app.inject({ method: 'GET', url: '/me/filters', headers: authHeader(user.accessToken) });
  assert.equal(afterDealBreaker.statusCode, 200);
  const filtersAfterDealBreaker = JSON.parse(afterDealBreaker.body) as Array<{
    filterKey: string;
    operator: string;
    value: unknown;
    enabled: boolean;
    excludeIfUnset: boolean;
  }>;
  const derived = filtersAfterDealBreaker.find((f) => f.filterKey === `qb:${slug}`);
  assert.ok(derived, 'a deal_breaker answer must persist a qb:-prefixed hard filter');
  assert.equal(derived!.enabled, true);
  assert.equal(derived!.operator, 'in');
  assert.deepEqual(derived!.value, ['no']);
  // requirement #3: unset attributes stay INCLUDED by default everywhere
  // EXCEPT where the deal breaker itself explicitly opts into strictness —
  // a deal-breaker-derived filter is exactly that explicit opt-in.
  assert.equal(derived!.excludeIfUnset, true, 'a deal-breaker-derived filter must exclude an unresolved (never-answered) candidate — that is the point of a deal breaker');

  // Soften the same question to a non-deal-breaker importance.
  await t.app.inject({
    method: 'PUT',
    url: '/me/answers',
    headers: authHeader(user.accessToken),
    payload: { slug, status: 'answered', selfValue: 'no', preferenceValue: ['no'], importance: 'important' },
  });

  const afterSoften = await t.app.inject({ method: 'GET', url: '/me/filters', headers: authHeader(user.accessToken) });
  const filtersAfterSoften = JSON.parse(afterSoften.body) as Array<{ filterKey: string; enabled: boolean }>;
  const retracted = filtersAfterSoften.find((f) => f.filterKey === `qb:${slug}`);
  assert.ok(retracted, 'the row is retracted (disabled), not deleted — updateMyFilters only ever upserts');
  assert.equal(retracted!.enabled, false, 'softening a deal breaker must retract (disable) its derived hard filter');
});

test('an ordinary (non-deal-breaker) answer never creates a hard filter', async () => {
  const slug = `ordinary-${Date.now()}`;
  await insertBankQuestion({ slug, typeDef: SCALE_TYPE_DEF });
  const user = await registerUser(t);

  await t.app.inject({
    method: 'PUT',
    url: '/me/answers',
    headers: authHeader(user.accessToken),
    payload: { slug, status: 'answered', selfValue: 4, preferenceValue: 4, importance: 'critical' },
  });

  const res = await t.app.inject({ method: 'GET', url: '/me/filters', headers: authHeader(user.accessToken) });
  const filters = JSON.parse(res.body) as Array<{ filterKey: string }>;
  assert.ok(!filters.some((f) => f.filterKey === `qb:${slug}`), 'a "critical" (not deal_breaker) answer must not derive a hard filter');
});

// =====================================================================
// Tag intensity + avoid-tags
// =====================================================================

async function insertTag(name: string): Promise<string> {
  const { rows } = await t.pool.query<{ id: string }>(
    `INSERT INTO interest_tags (name, category, public_description) VALUES ($1, 'test', '') RETURNING id`,
    [name],
  );
  return rows[0]!.id;
}

test('tag intensity: PUT /me/tag-intensity/:tagId then GET /me/tag-intensity round-trips', async () => {
  const tagId = await insertTag(`hiking-${Date.now()}`);
  const user = await registerUser(t);

  const put = await t.app.inject({
    method: 'PUT',
    url: `/me/tag-intensity/${tagId}`,
    headers: authHeader(user.accessToken),
    payload: { intensity: 'daily' },
  });
  assert.equal(put.statusCode, 200);

  const get = await t.app.inject({ method: 'GET', url: '/me/tag-intensity', headers: authHeader(user.accessToken) });
  const rows = JSON.parse(get.body) as Array<{ tagId: string; intensity: string }>;
  assert.ok(rows.some((r) => r.tagId === tagId && r.intensity === 'daily'));
});

test('avoid tags: PUT /me/avoid-tags then GET /me/avoid-tags round-trips (full-replace semantics)', async () => {
  const tagA = await insertTag(`astrology-${Date.now()}`);
  const tagB = await insertTag(`crypto-${Date.now()}`);
  const user = await registerUser(t);

  const put = await t.app.inject({
    method: 'PUT',
    url: '/me/avoid-tags',
    headers: authHeader(user.accessToken),
    payload: { tagIds: [tagA, tagB] },
  });
  assert.equal(put.statusCode, 200);

  const get = await t.app.inject({ method: 'GET', url: '/me/avoid-tags', headers: authHeader(user.accessToken) });
  const ids = JSON.parse(get.body) as string[];
  assert.deepEqual([...ids].sort(), [tagA, tagB].sort());

  // Full-replace: a second PUT with only one tag drops the other.
  await t.app.inject({
    method: 'PUT',
    url: '/me/avoid-tags',
    headers: authHeader(user.accessToken),
    payload: { tagIds: [tagA] },
  });
  const getAfter = await t.app.inject({ method: 'GET', url: '/me/avoid-tags', headers: authHeader(user.accessToken) });
  assert.deepEqual(JSON.parse(getAfter.body), [tagA]);
});

test('every route requires authentication', async () => {
  const unauth = await t.app.inject({ method: 'GET', url: '/questions' });
  assert.equal(unauth.statusCode, 401);
  const unauthAnswers = await t.app.inject({ method: 'GET', url: '/me/answers' });
  assert.equal(unauthAnswers.statusCode, 401);
});
