/**
 * `POST /webhooks/payments`, signature verification (C-24.5) and
 * idempotency (§25.9) at the HTTP boundary. `payment.handleProcessorWebhook`
 * itself is already idempotent (dup-ledger-row check); this file proves the
 * ROUTE also rejects an unsigned/bad-signature request before that function
 * ever runs.
 */
import { test, before, beforeEach, after } from 'node:test';
import assert from 'node:assert/strict';
import { createHmac } from 'node:crypto';
import { setupTestApp, teardownTestApp, registerUser, authHeader, resetRateLimiter } from './testServer.js';
import type { TestApp } from './testServer.js';

let t: TestApp;

before(async () => {
  t = await setupTestApp('webhook');
});

after(async () => {
  await teardownTestApp(t);
});

beforeEach(() => {
  resetRateLimiter(t);
});

function sign(body: unknown): string {
  // Mirrors src/http/routes/payments.routes.ts#webhookSecret's fallback for
  // PAYMENT_PROCESSOR=fake (the default in tests): AUTH_TOKEN_SECRET.
  const secret = process.env.AUTH_TOKEN_SECRET ?? 'dev-insecure-secret-change-me';
  return createHmac('sha256', secret).update(JSON.stringify(body)).digest('hex');
}

async function setUpAuthorizedHold(): Promise<{ dateProposalId: string; processorIntentId: string; proposerId: string }> {
  const alice = await registerUser(t);
  const bob = await registerUser(t);

  for (const [tokenHolder, brand] of [[alice, 'a'], [bob, 'b']] as const) {
    const res = await t.app.inject({
      method: 'POST',
      url: '/payment-methods',
      headers: authHeader(tokenHolder.accessToken),
      payload: { processorToken: `tok_webhook_${brand}`, makeDefault: true },
    });
    assert.equal(res.statusCode, 201);
  }

  const sendRes = await t.app.inject({ method: 'POST', url: '/interests', headers: authHeader(alice.accessToken), payload: { recipientId: bob.userId } });
  const interest = JSON.parse(sendRes.body) as { id: string };
  const acceptRes = await t.app.inject({ method: 'POST', url: `/interests/${interest.id}/accept`, headers: authHeader(bob.accessToken) });
  const { conversation } = JSON.parse(acceptRes.body) as { conversation: { id: string } };

  const { rows: venueRows } = await t.pool.query<{ id: string }>(
    `INSERT INTO venues (name, address, latitude, longitude, category, active, margin_percent, time_slot_config, redemption_method)
     VALUES ('Webhook Venue', '1 St', 0, 0, 'coffee', true, 10, '{"slots":[]}'::jsonb, 'qr_scan') RETURNING id`,
  );
  const venueId = venueRows[0]!.id;
  const start = new Date(t.clock.now().getTime() + 2 * 24 * 60 * 60 * 1000);
  const end = new Date(start.getTime() + 60 * 60 * 1000);
  const proposeRes = await t.app.inject({
    method: 'POST',
    url: `/conversations/${conversation.id}/date-proposals`,
    headers: authHeader(alice.accessToken),
    payload: { venueId, scheduledStart: start.toISOString(), scheduledEnd: end.toISOString() },
  });
  const proposal = JSON.parse(proposeRes.body) as { id: string };

  const { rows: holdRows } = await t.pool.query<{ processor_intent_id: string }>(
    `SELECT processor_intent_id FROM payment_holds WHERE date_proposal_id = $1 AND user_id = $2`,
    [proposal.id, alice.userId],
  );
  return { dateProposalId: proposal.id, processorIntentId: holdRows[0]!.processor_intent_id, proposerId: alice.userId };
}

test('C-24.5: a webhook with no signature header is rejected before the payload is trusted', async () => {
  const { processorIntentId } = await setUpAuthorizedHold();
  const payload = { type: 'payment_intent.succeeded', processorIntentId };
  const res = await t.app.inject({ method: 'POST', url: '/webhooks/payments', payload });
  assert.equal(res.statusCode, 401);
  assert.equal(JSON.parse(res.body).error.code, 'unauthorized');

  const { rows } = await t.pool.query(`SELECT status FROM payment_holds WHERE processor_intent_id = $1`, [processorIntentId]);
  assert.equal(rows[0]?.status, 'authorized', 'an unsigned webhook must never move the hold to captured');
});

test('C-24.5: a webhook with a WRONG signature is rejected', async () => {
  const { processorIntentId } = await setUpAuthorizedHold();
  const payload = { type: 'payment_intent.succeeded', processorIntentId };
  const res = await t.app.inject({
    method: 'POST',
    url: '/webhooks/payments',
    payload,
    headers: { 'x-webhook-signature': 'deadbeef'.repeat(8) },
  });
  assert.equal(res.statusCode, 401);
});

test('a correctly-signed webhook is accepted and updates local state', async () => {
  const { processorIntentId } = await setUpAuthorizedHold();
  const payload = { type: 'payment_intent.succeeded', processorIntentId };
  const res = await t.app.inject({
    method: 'POST',
    url: '/webhooks/payments',
    payload,
    headers: { 'x-webhook-signature': sign(payload) },
  });
  assert.equal(res.statusCode, 204);

  const { rows } = await t.pool.query(`SELECT status FROM payment_holds WHERE processor_intent_id = $1`, [processorIntentId]);
  assert.equal(rows[0]?.status, 'captured');
});

test('§25.9: replaying the same signed webhook event is idempotent (no duplicate ledger row)', async () => {
  const { processorIntentId, dateProposalId } = await setUpAuthorizedHold();
  const payload = { type: 'payment_intent.succeeded', processorIntentId };
  const signature = sign(payload);

  const first = await t.app.inject({ method: 'POST', url: '/webhooks/payments', payload, headers: { 'x-webhook-signature': signature } });
  assert.equal(first.statusCode, 204);
  const second = await t.app.inject({ method: 'POST', url: '/webhooks/payments', payload, headers: { 'x-webhook-signature': signature } });
  assert.equal(second.statusCode, 204);

  const { rows } = await t.pool.query(
    `SELECT count(*)::int AS count FROM payment_ledger WHERE date_proposal_id = $1 AND processor_reference = $2 AND type = 'capture'`,
    [dateProposalId, processorIntentId],
  );
  assert.equal(rows[0].count, 1, 'a replayed webhook must not double-record the ledger entry');
});
