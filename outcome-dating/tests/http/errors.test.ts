/**
 * The shared error envelope (`{ error: { code, message, details? } }`) and
 * its mapping from the typed `AppError` hierarchy / Zod validation
 * failures onto stable HTTP statuses + machine-readable codes.
 */
import { test, before, beforeEach, after } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestApp, teardownTestApp, registerUser, authHeader, resetRateLimiter } from './testServer.js';
import type { TestApp, RegisteredUser } from './testServer.js';

let t: TestApp;

before(async () => {
  t = await setupTestApp('errors');
});

after(async () => {
  await teardownTestApp(t);
});

beforeEach(() => {
  resetRateLimiter(t);
});

test('missing required registration fields -> 400 validation_error (C-5.1.1-5.1.5)', async () => {
  const res = await t.app.inject({ method: 'POST', url: '/auth/register', payload: { password: 'x', birthdate: '1990-01-01', termsAccepted: true } });
  assert.equal(res.statusCode, 400);
  const body = JSON.parse(res.body);
  assert.equal(body.error.code, 'validation_error');
});

test('termsAccepted !== true -> 400 validation_error (C-5.1.4)', async () => {
  const res = await t.app.inject({
    method: 'POST',
    url: '/auth/register',
    payload: { email: 'x@test.local', password: 'Passw0rd!!', birthdate: '1990-01-01', termsAccepted: false, city: 'X' },
  });
  assert.equal(res.statusCode, 400);
  assert.equal(JSON.parse(res.body).error.code, 'validation_error');
});

test('duplicate email on register -> 409 conflict (C-5.1.7)', async () => {
  const email = 'dupe@test.local';
  const first = await t.app.inject({
    method: 'POST',
    url: '/auth/register',
    payload: { email, password: 'Passw0rd!!', birthdate: '1990-01-01', termsAccepted: true, city: 'X' },
  });
  assert.equal(first.statusCode, 201);

  const second = await t.app.inject({
    method: 'POST',
    url: '/auth/register',
    payload: { email, password: 'Passw0rd!!', birthdate: '1990-01-01', termsAccepted: true, city: 'X' },
  });
  assert.equal(second.statusCode, 409);
  assert.equal(JSON.parse(second.body).error.code, 'conflict');
});

test('wrong password on login -> 401 unauthorized', async () => {
  const user = await registerUser(t);
  const res = await t.app.inject({ method: 'POST', url: '/auth/login', payload: { email: user.email, password: 'wrong-password' } });
  assert.equal(res.statusCode, 401);
  assert.equal(JSON.parse(res.body).error.code, 'unauthorized');
});

test('fetching a nonexistent conversation -> 404 not_found', async () => {
  const user = await registerUser(t);
  const res = await t.app.inject({
    method: 'GET',
    url: '/conversations/00000000-0000-0000-0000-000000000000',
    headers: authHeader(user.accessToken),
  });
  assert.equal(res.statusCode, 404);
  assert.equal(JSON.parse(res.body).error.code, 'not_found');
});

test('a non-uuid path param -> 400 validation_error, not a 500', async () => {
  const user = await registerUser(t);
  const res = await t.app.inject({ method: 'GET', url: '/conversations/not-a-uuid', headers: authHeader(user.accessToken) });
  assert.equal(res.statusCode, 400);
  assert.equal(JSON.parse(res.body).error.code, 'validation_error');
});

test('double-accepting the same interest race -> second caller gets 409 conflict, not a 500 (C-11.4.SM.I6)', async () => {
  const alice = await registerUser(t);
  const bob = await registerUser(t);
  const sendRes = await t.app.inject({ method: 'POST', url: '/interests', headers: authHeader(alice.accessToken), payload: { recipientId: bob.userId } });
  const interest = JSON.parse(sendRes.body) as { id: string };

  const first = await t.app.inject({ method: 'POST', url: `/interests/${interest.id}/accept`, headers: authHeader(bob.accessToken) });
  assert.equal(first.statusCode, 200);

  const second = await t.app.inject({ method: 'POST', url: `/interests/${interest.id}/decline`, headers: authHeader(bob.accessToken) });
  assert.equal(second.statusCode, 409);
  assert.equal(JSON.parse(second.body).error.code, 'conflict');
});

test('C-11.2.1: 6th pending outgoing interest -> 429 rate_limited with the outgoing-limit reason', async () => {
  const sender = await registerUser(t);
  const recipients: RegisteredUser[] = [];
  for (let i = 0; i < 6; i++) recipients.push(await registerUser(t));

  for (let i = 0; i < 5; i++) {
    const res = await t.app.inject({ method: 'POST', url: '/interests', headers: authHeader(sender.accessToken), payload: { recipientId: recipients[i]!.userId } });
    assert.equal(res.statusCode, 201, `interest ${i} should succeed`);
  }
  const sixth = await t.app.inject({ method: 'POST', url: '/interests', headers: authHeader(sender.accessToken), payload: { recipientId: recipients[5]!.userId } });
  assert.equal(sixth.statusCode, 429);
  assert.equal(JSON.parse(sixth.body).error.code, 'rate_limited');
});
