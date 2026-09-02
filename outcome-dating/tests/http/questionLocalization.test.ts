/**
 * tests/http/questionLocalization.test.ts, wiring item 4: question
 * translations must reach a client. `src/domain/i18n/questionLocalization.ts`
 * (`getQuestionTranslation(s)`/`localizeQuestionDefinition`) and the
 * `question_bank_translations` table were built and tested in isolation,
 * but nothing called them from the point a question definition is built
 * for a response, so a question shipped in English only regardless of the
 * caller's negotiated locale. This suite proves `GET /questions` and
 * `GET /questions/next` now honour the caller's negotiated locale (a
 * stored `PUT /me/locale` preference, per `src/domain/i18n/locales.ts`'s
 * negotiation rule), and degrade cleanly to English when a translation
 * doesn't exist for that locale/question pair.
 */
import { test, before, after, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestApp, teardownTestApp, registerUser, authHeader, insertQuestion, resetRateLimiter } from './testServer.js';
import type { TestApp } from './testServer.js';
import type { Ctx } from '../../src/lib/ctx.js';
import { upsertQuestionTranslation } from '../../src/domain/i18n/questionLocalization.js';

let t: TestApp;

before(async () => {
  t = await setupTestApp('questionlocalization');
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

test('GET /questions: a question comes back in a second locale when a translation exists', async () => {
  const alice = await registerUser(t);
  const questionId = await insertQuestion(t, { slug: 'localization_scale_es' });

  await upsertQuestionTranslation(systemCtx(), questionId, 'es', {
    questionText: 'Traduccion en espanol de la pregunta.',
    labels: { minLabel: 'bajo', maxLabel: 'alto', midLabel: 'medio' },
  });

  const setLocaleRes = await t.app.inject({ method: 'PUT', url: '/me/locale', headers: authHeader(alice.accessToken), payload: { locale: 'es' } });
  assert.equal(setLocaleRes.statusCode, 200);

  const res = await t.app.inject({ method: 'GET', url: '/questions?limit=200', headers: authHeader(alice.accessToken) });
  assert.equal(res.statusCode, 200);
  const body = JSON.parse(res.body) as { items: Array<{ id: string; questionText: string; typeDef: { minLabel?: string } }> };
  const item = body.items.find((q) => q.id === questionId)!;
  assert.ok(item, 'the seeded question is present in the page');
  assert.equal(item.questionText, 'Traduccion en espanol de la pregunta.');
  assert.equal(item.typeDef.minLabel, 'bajo');
});

test('GET /questions: falls back to the English question text when no translation exists for the caller’s locale', async () => {
  const bob = await registerUser(t);
  const questionId = await insertQuestion(t, { slug: 'localization_scale_no_translation' });

  const setLocaleRes = await t.app.inject({ method: 'PUT', url: '/me/locale', headers: authHeader(bob.accessToken), payload: { locale: 'de' } });
  assert.equal(setLocaleRes.statusCode, 200);

  const res = await t.app.inject({ method: 'GET', url: '/questions?limit=200', headers: authHeader(bob.accessToken) });
  assert.equal(res.statusCode, 200);
  const body = JSON.parse(res.body) as { items: Array<{ id: string; questionText: string }> };
  const item = body.items.find((q) => q.id === questionId)!;
  assert.ok(item);
  assert.equal(item.questionText, 'localization_scale_no_translation', 'insertQuestion seeds English questionText equal to the slug');
});

test('GET /questions/next: the selector-picked questions also honour the caller’s stored locale', async () => {
  const carol = await registerUser(t);
  const questionId = await insertQuestion(t, { slug: 'localization_next_es' });
  await upsertQuestionTranslation(systemCtx(), questionId, 'es', { questionText: 'Pregunta siguiente en espanol.' });

  await t.app.inject({ method: 'PUT', url: '/me/locale', headers: authHeader(carol.accessToken), payload: { locale: 'es' } });

  const res = await t.app.inject({ method: 'GET', url: '/questions/next?count=50', headers: authHeader(carol.accessToken) });
  assert.equal(res.statusCode, 200);
  const body = JSON.parse(res.body) as { items: Array<{ id: string; questionText: string }> };
  const item = body.items.find((q) => q.id === questionId);
  assert.ok(item, 'the seeded question is present among the next-question selection');
  assert.equal(item!.questionText, 'Pregunta siguiente en espanol.');
});

test('GET /questions: an Accept-Language header is honoured when no stored preference exists', async () => {
  const dave = await registerUser(t);
  const questionId = await insertQuestion(t, { slug: 'localization_header_es' });
  await upsertQuestionTranslation(systemCtx(), questionId, 'es', { questionText: 'Texto via encabezado Accept-Language.' });

  const res = await t.app.inject({
    method: 'GET',
    url: '/questions?limit=200',
    headers: { ...authHeader(dave.accessToken), 'accept-language': 'es-MX,es;q=0.9,en;q=0.1' },
  });
  assert.equal(res.statusCode, 200);
  const body = JSON.parse(res.body) as { items: Array<{ id: string; questionText: string }> };
  const item = body.items.find((q) => q.id === questionId)!;
  assert.ok(item);
  assert.equal(item.questionText, 'Texto via encabezado Accept-Language.');
});

test('GET /questions: a stored preference wins over an Accept-Language header', async () => {
  const erin = await registerUser(t);
  const questionId = await insertQuestion(t, { slug: 'localization_precedence' });
  await upsertQuestionTranslation(systemCtx(), questionId, 'es', { questionText: 'Preferencia guardada gana.' });

  await t.app.inject({ method: 'PUT', url: '/me/locale', headers: authHeader(erin.accessToken), payload: { locale: 'es' } });

  const res = await t.app.inject({
    method: 'GET',
    url: '/questions?limit=200',
    headers: { ...authHeader(erin.accessToken), 'accept-language': 'en-US,en;q=0.9' },
  });
  assert.equal(res.statusCode, 200);
  const body = JSON.parse(res.body) as { items: Array<{ id: string; questionText: string }> };
  const item = body.items.find((q) => q.id === questionId)!;
  assert.ok(item);
  assert.equal(item.questionText, 'Preferencia guardada gana.', 'the stored es preference must win over the en Accept-Language header');
});
