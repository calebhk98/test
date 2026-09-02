/**
 * tests/http/behavioralPromptWiring.test.ts, wiring item 5: the
 * behavioural prompt endpoint could not carry importance.
 * `behavioralPrompt.service#respondToSuggestion` requires an importance
 * level or a ladder position to record a real answer (the typed question
 * bank's "value + importance, never a bare number" invariant), but
 * `POST /me/behavioral-prompts/:suggestionId/respond`'s own request
 * schema only ever accepted `{skipped, selfValue, partnerValue}`, so
 * answering (not skipping) a prompt through the real HTTP route could
 * never succeed. This suite drives the real route (not the service
 * directly, `tests/unit/behavioralPrompt.test.ts` already covers that)
 * with each presentation form the question endpoints use
 * (`preferenceValue` + `importance`, and `ladderPosition` on a
 * ladder-presentation question), plus skipping.
 */
import { test, before, after, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestApp, teardownTestApp, registerUser, authHeader, resetRateLimiter } from './testServer.js';
import type { TestApp } from './testServer.js';
import type { Ctx } from '../../src/lib/ctx.js';
import { KNOWN_FLAGS } from '../../src/config/flags.service.js';

let t: TestApp;

before(async () => {
  t = await setupTestApp('behavioralpromptwiring');
});

after(async () => {
  await teardownTestApp(t);
});

beforeEach(() => {
  resetRateLimiter(t);
});

function systemCtx(): Ctx {
  return {
    db: t.pool,
    clock: t.clock,
    config: t.deps.config,
    flags: t.deps.flags,
    logger: t.deps.logger,
    actor: { type: 'system', job: 'test-seed' },
    payments: t.deps.payments,
    media: t.deps.media,
  };
}

const SCALE_TYPE_DEF = { type: 'scale', min: 1, max: 5, minLabel: 'low', maxLabel: 'high', midLabel: 'mid' };
const LADDER_TYPE_DEF = {
  type: 'single_choice',
  options: [
    { key: 'no', label: 'No' },
    { key: 'yes', label: 'Yes' },
  ],
};

/** Inserts a `question_bank` row directly (bypassing the admin routes, `tests/http/admin.test.ts` covers those) and a `pending` suggestion pointing at it, bypassing pattern DETECTION itself (`tests/unit/behavioralPrompt.test.ts` covers that), since this suite is only about the HTTP response route. */
async function makePendingSuggestion(userId: string, typeDef: unknown = SCALE_TYPE_DEF): Promise<{ suggestionId: string; questionId: string }> {
  const { rows: qRows } = await t.pool.query<{ id: string }>(
    `INSERT INTO question_bank (slug, version, is_current, category, question_type, question_text, type_definition, active)
     VALUES ($1, 1, true, 'test', $2, $1, $3::jsonb, true)
     RETURNING id`,
    [`bp_wiring_${Date.now()}_${Math.random().toString(36).slice(2)}`, (typeDef as { type: string }).type, JSON.stringify(typeDef)],
  );
  const questionId = qRows[0]!.id;

  const { rows: sRows } = await t.pool.query<{ id: string }>(
    `INSERT INTO behavioral_prompt_suggestions (user_id, question_id, trigger_kind, trigger_label, status)
     VALUES ($1, $2, 'tag', 'wiring-test-tag', 'pending')
     RETURNING id`,
    [userId, questionId],
  );
  return { suggestionId: sRows[0]!.id, questionId };
}

test('POST /me/behavioral-prompts/:suggestionId/respond: skipping still works', async () => {
  const alice = await registerUser(t);
  const { suggestionId } = await makePendingSuggestion(alice.userId);

  const res = await t.app.inject({
    method: 'POST',
    url: `/me/behavioral-prompts/${suggestionId}/respond`,
    headers: authHeader(alice.accessToken),
    payload: { skipped: true },
  });
  assert.equal(res.statusCode, 204);

  const { rows } = await t.pool.query<{ status: string }>(`SELECT status FROM behavioral_prompt_suggestions WHERE id = $1`, [suggestionId]);
  assert.equal(rows[0]!.status, 'skipped');
});

test('POST /me/behavioral-prompts/:suggestionId/respond: answering with preferenceValue + importance succeeds', async () => {
  const bob = await registerUser(t);
  const { suggestionId, questionId } = await makePendingSuggestion(bob.userId, SCALE_TYPE_DEF);

  const res = await t.app.inject({
    method: 'POST',
    url: `/me/behavioral-prompts/${suggestionId}/respond`,
    headers: authHeader(bob.accessToken),
    payload: { selfValue: 4, partnerValue: 3, importance: 'important' },
  });
  assert.equal(res.statusCode, 204, `expected 204, got ${res.statusCode}: ${res.body}`);

  const { rows: suggestionRows } = await t.pool.query<{ status: string }>(`SELECT status FROM behavioral_prompt_suggestions WHERE id = $1`, [suggestionId]);
  assert.equal(suggestionRows[0]!.status, 'answered');

  const { rows: answerRows } = await t.pool.query<{ importance: string; self_value: unknown; preference_value: unknown }>(
    `SELECT importance, self_value, preference_value FROM user_question_answers WHERE user_id = $1 AND question_bank_id = $2`,
    [bob.userId, questionId],
  );
  assert.equal(answerRows.length, 1, 'a real typed-bank answer was written');
  assert.equal(answerRows[0]!.importance, 'important');
});

test('POST /me/behavioral-prompts/:suggestionId/respond: answering with ladderPosition (in place of preferenceValue + importance) succeeds on a ladder-presentation question', async () => {
  const carol = await registerUser(t);
  const { suggestionId, questionId } = await makePendingSuggestion(carol.userId, LADDER_TYPE_DEF);

  const res = await t.app.inject({
    method: 'POST',
    url: `/me/behavioral-prompts/${suggestionId}/respond`,
    headers: authHeader(carol.accessToken),
    payload: { selfValue: 'yes', ladderPosition: 2 },
  });
  assert.equal(res.statusCode, 204, `expected 204, got ${res.statusCode}: ${res.body}`);

  const { rows: answerRows } = await t.pool.query<{ importance: string | null }>(
    `SELECT importance FROM user_question_answers WHERE user_id = $1 AND question_bank_id = $2`,
    [carol.userId, questionId],
  );
  assert.equal(answerRows.length, 1);
  assert.ok(answerRows[0]!.importance, 'a ladder position derives a real importance level, never null');
});

test('POST /me/behavioral-prompts/:suggestionId/respond: answering with neither importance nor ladderPosition is rejected, never silently defaulted', async () => {
  const dave = await registerUser(t);
  const { suggestionId } = await makePendingSuggestion(dave.userId);

  const res = await t.app.inject({
    method: 'POST',
    url: `/me/behavioral-prompts/${suggestionId}/respond`,
    headers: authHeader(dave.accessToken),
    payload: { selfValue: 3, partnerValue: 3 },
  });
  assert.equal(res.statusCode, 400, 'a stated preference must never be fabricated on the caller’s behalf');

  const { rows } = await t.pool.query<{ status: string }>(`SELECT status FROM behavioral_prompt_suggestions WHERE id = $1`, [suggestionId]);
  assert.equal(rows[0]!.status, 'pending', 'a rejected response must not silently resolve the suggestion');
});

test('end to end: a real pattern-detected suggestion is answerable through the route with importance', async () => {
  const erin = await registerUser(t);
  const other = await registerUser(t);

  await t.deps.flags.setFlag(KNOWN_FLAGS.BEHAVIORAL_QUESTION_PROMPTS, { enabled: true, rolloutPercent: 100 });

  const { rows: tagRows } = await t.pool.query<{ id: string }>(
    `INSERT INTO interest_tags (name, category, public_description) VALUES ('wiring_hiking', 'activity', 'Hiking') RETURNING id`,
  );
  const tagId = tagRows[0]!.id;
  await t.pool.query(`INSERT INTO user_tags (user_id, tag_id, visibility) VALUES ($1, $2, 'public')`, [other.userId, tagId]);

  await t.pool.query(
    `INSERT INTO question_bank (slug, version, is_current, category, question_type, question_text, type_definition, active)
     VALUES ('wiring_hiking', 1, true, 'test', 'scale', 'wiring_hiking', $1::jsonb, true)`,
    [JSON.stringify(SCALE_TYPE_DEF)],
  );

  for (let i = 0; i < 3; i++) {
    await t.pool.query(
      `INSERT INTO interests (sender_id, recipient_id, status, policy_snapshot, expires_at, accepted_at)
       VALUES ($1, $2, 'accepted', '{}'::jsonb, now() + interval '7 days', now())`,
      [erin.userId, other.userId],
    );
  }

  const behavioralPromptModule = await import('../../src/services/behavioralPrompt.service.js');
  const created = await behavioralPromptModule.detectPatternsForUser(systemCtx(), erin.userId);
  assert.ok(created.length > 0, 'a pattern was detected and a suggestion recorded');

  const listRes = await t.app.inject({ method: 'GET', url: '/me/behavioral-prompts', headers: authHeader(erin.accessToken) });
  const pending = JSON.parse(listRes.body) as Array<{ id: string; triggerLabel: string }>;
  const suggestion = pending.find((s) => s.triggerLabel === 'wiring_hiking')!;
  assert.ok(suggestion, 'the detected suggestion is reachable via GET /me/behavioral-prompts');

  const respondRes = await t.app.inject({
    method: 'POST',
    url: `/me/behavioral-prompts/${suggestion.id}/respond`,
    headers: authHeader(erin.accessToken),
    payload: { selfValue: 5, partnerValue: 5, importance: 'critical' },
  });
  assert.equal(respondRes.statusCode, 204, `expected 204, got ${respondRes.statusCode}: ${respondRes.body}`);
});
