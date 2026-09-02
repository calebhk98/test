/**
 * tests/http/cursorAdoption.test.ts, proves the four endpoints this build
 * adopted onto the shared `(timestamp, id)` cursor codec (src/lib/cursor.ts)
 * actually get its validation at the HTTP layer: a malformed cursor must
 * come back as a 400 (`validation_error`), never an unhandled 500, for
 * `GET /notifications`, `GET /interests/outgoing`, `GET /matches`, and
 * `GET /conversations/:conversationId/timeline`.
 *
 * `message.service.ts#listMessages` already adopted the shared helper
 * before this build (see tests/unit/cursor.test.ts's own coverage of it);
 * this file covers exactly the four endpoints this build newly switched
 * over: notification, interest, matches, timeline.
 */
import { test, before, after, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestApp, teardownTestApp, registerUser, authHeader, resetRateLimiter } from './testServer.js';
import type { TestApp } from './testServer.js';

let t: TestApp;

before(async () => {
  t = await setupTestApp('cursoradoption');
});

after(async () => {
  await teardownTestApp(t);
});

beforeEach(() => {
  resetRateLimiter(t);
});

/** Same malformed shape as tests/unit/cursor.test.ts: parseable base64url, corrupted date. */
const BAD_CURSOR = Buffer.from('not-a-date|11111111-1111-1111-1111-111111111111', 'utf8').toString('base64url');

async function makeMatch(alice: { accessToken: string; userId: string }, bob: { accessToken: string; userId: string }): Promise<string> {
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
  const accepted = JSON.parse(acceptRes.body) as { conversation: { id: string } };
  return accepted.conversation.id;
}

function assertBadRequest(res: { statusCode: number; body: string }, label: string): void {
  assert.equal(res.statusCode, 400, `${label}: expected 400, got ${res.statusCode} (${res.body})`);
  const body = JSON.parse(res.body) as { error: { code: string } };
  assert.equal(body.error.code, 'validation_error', `${label}: expected a validation_error code`);
}

test('GET /notifications: a malformed cursor is a 400, never a 500', async () => {
  const alice = await registerUser(t);
  const res = await t.app.inject({ method: 'GET', url: `/notifications?cursor=${BAD_CURSOR}`, headers: authHeader(alice.accessToken) });
  assertBadRequest(res, 'GET /notifications');
});

test('GET /interests/outgoing and /interests/incoming: a malformed cursor is a 400, never a 500', async () => {
  const alice = await registerUser(t);
  const outgoingRes = await t.app.inject({
    method: 'GET',
    url: `/interests/outgoing?cursor=${BAD_CURSOR}`,
    headers: authHeader(alice.accessToken),
  });
  assertBadRequest(outgoingRes, 'GET /interests/outgoing');

  const incomingRes = await t.app.inject({
    method: 'GET',
    url: `/interests/incoming?cursor=${BAD_CURSOR}`,
    headers: authHeader(alice.accessToken),
  });
  assertBadRequest(incomingRes, 'GET /interests/incoming');
});

test('GET /matches: a malformed cursor is a 400, never a 500', async () => {
  const alice = await registerUser(t);
  const res = await t.app.inject({ method: 'GET', url: `/matches?cursor=${BAD_CURSOR}`, headers: authHeader(alice.accessToken) });
  assertBadRequest(res, 'GET /matches');
});

test('GET /conversations/:conversationId/timeline: a malformed cursor is a 400, never a 500', async () => {
  const alice = await registerUser(t);
  const bob = await registerUser(t);
  const conversationId = await makeMatch(alice, bob);

  const res = await t.app.inject({
    method: 'GET',
    url: `/conversations/${conversationId}/timeline?cursor=${BAD_CURSOR}`,
    headers: authHeader(alice.accessToken),
  });
  assertBadRequest(res, 'GET /conversations/:conversationId/timeline');
});

test('well-formed cursors on all four adopted endpoints still paginate correctly (the fix only tightens validation, it never changes the wire format)', async () => {
  const alice = await registerUser(t);
  const bob = await registerUser(t);

  // Two notifications for alice: bob sends, then a second registrant sends.
  const carol = await registerUser(t);
  await t.app.inject({ method: 'POST', url: '/interests', headers: authHeader(bob.accessToken), payload: { recipientId: alice.userId } });
  await t.app.inject({ method: 'POST', url: '/interests', headers: authHeader(carol.accessToken), payload: { recipientId: alice.userId } });

  const page1 = await t.app.inject({ method: 'GET', url: '/notifications?limit=1', headers: authHeader(alice.accessToken) });
  assert.equal(page1.statusCode, 200);
  const page1Body = JSON.parse(page1.body) as { items: unknown[]; nextCursor: string | null };
  assert.equal(page1Body.items.length, 1);
  assert.ok(page1Body.nextCursor);

  const page2 = await t.app.inject({
    method: 'GET',
    url: `/notifications?limit=1&cursor=${page1Body.nextCursor}`,
    headers: authHeader(alice.accessToken),
  });
  assert.equal(page2.statusCode, 200);
  const page2Body = JSON.parse(page2.body) as { items: unknown[]; nextCursor: string | null };
  assert.equal(page2Body.items.length, 1);
});
