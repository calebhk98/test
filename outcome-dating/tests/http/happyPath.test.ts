/**
 * The full §2 happy-path loop, driven entirely over HTTP via `app.inject`:
 * register -> answer questions -> set filters -> browse (discovery) ->
 * send interest -> mutual accept -> chat -> propose date -> both holds
 * authorized -> capture -> ticket -> venue redemption -> post-date
 * feedback -> established chat. Mirrors conformance C-2.1.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import {
  setupTestApp,
  teardownTestApp,
  registerUser,
  authHeader,
  completeOnboarding,
  createVenue,
} from './testServer.js';
import type { TestApp } from './testServer.js';

let t: TestApp;

before(async () => {
  t = await setupTestApp('happy_path');
});

after(async () => {
  await teardownTestApp(t);
});

test('happy path: register -> answers -> filters -> discovery -> interest -> chat -> date -> payment -> ticket -> redemption -> feedback -> established', async () => {
  const alice = await registerUser(t);
  const bob = await registerUser(t);

  await completeOnboarding(t, alice.accessToken, { displayName: 'Alice', gender: 'woman', seeking: 'man' });
  await completeOnboarding(t, bob.accessToken, { displayName: 'Bob', gender: 'man', seeking: 'woman' });

  // ---- filters (§9) ----
  const filtersRes = await t.app.inject({
    method: 'PATCH',
    url: '/me/filters',
    headers: authHeader(alice.accessToken),
    payload: [{ filterKey: 'age_min', operator: 'gte', value: 18, enabled: true }],
  });
  assert.equal(filtersRes.statusCode, 200);

  // ---- discovery (§10) ----
  const discoveryRes = await t.app.inject({ method: 'GET', url: '/discovery', headers: authHeader(alice.accessToken) });
  assert.equal(discoveryRes.statusCode, 200);
  const discoveryBody = JSON.parse(discoveryRes.body) as { items: Array<{ userId: string; approximateDistanceKm: number | null }> };
  const bobCard = discoveryBody.items.find((c) => c.userId === bob.userId);
  assert.ok(bobCard, 'bob should appear in alice discovery grid');
  // §7.1/§28.5: never exact coordinates on the wire.
  assert.equal('latitude' in (bobCard as object), false);
  assert.equal('longitude' in (bobCard as object), false);

  // ---- interests (§11) ----
  const sendRes = await t.app.inject({
    method: 'POST',
    url: '/interests',
    headers: authHeader(alice.accessToken),
    payload: { recipientId: bob.userId },
  });
  assert.equal(sendRes.statusCode, 201);
  const interest = JSON.parse(sendRes.body) as { id: string; status: string };
  assert.equal(interest.status, 'pending');

  const incomingRes = await t.app.inject({ method: 'GET', url: '/interests/incoming', headers: authHeader(bob.accessToken) });
  const incoming = JSON.parse(incomingRes.body) as { items: Array<{ id: string }> };
  assert.ok(incoming.items.some((i) => i.id === interest.id));

  const acceptRes = await t.app.inject({
    method: 'POST',
    url: `/interests/${interest.id}/accept`,
    headers: authHeader(bob.accessToken),
  });
  assert.equal(acceptRes.statusCode, 200);
  const accepted = JSON.parse(acceptRes.body) as { conversation: { id: string; status: string } };
  assert.equal(accepted.conversation.status, 'active');
  const conversationId = accepted.conversation.id;

  // ---- chat (§12) ----
  const messageRes = await t.app.inject({
    method: 'POST',
    url: `/conversations/${conversationId}/messages`,
    headers: authHeader(alice.accessToken),
    payload: { body: 'Hey Bob! 👋 Would love to grab coffee sometime.' },
  });
  assert.equal(messageRes.statusCode, 201);

  // ---- date proposal + payment escrow (§13, §14) ----
  const venueId = await createVenue(t, { name: 'Happy Path Cafe' });
  const scheduledStart = new Date(t.clock.now().getTime() + 3 * 24 * 60 * 60 * 1000);
  const scheduledEnd = new Date(scheduledStart.getTime() + 60 * 60 * 1000);

  const proposeRes = await t.app.inject({
    method: 'POST',
    url: `/conversations/${conversationId}/date-proposals`,
    headers: authHeader(alice.accessToken),
    payload: {
      venueId,
      scheduledStart: scheduledStart.toISOString(),
      scheduledEnd: scheduledEnd.toISOString(),
      optionalNote: 'Looking forward to it!',
    },
  });
  assert.equal(proposeRes.statusCode, 201);
  const proposal = JSON.parse(proposeRes.body) as { id: string; status: string; escrowAmountCents: number };
  assert.equal(proposal.status, 'pending_acceptance');

  const acceptDateRes = await t.app.inject({
    method: 'POST',
    url: `/date-proposals/${proposal.id}/accept`,
    headers: authHeader(bob.accessToken),
  });
  assert.equal(acceptDateRes.statusCode, 200);
  const chargedProposal = JSON.parse(acceptDateRes.body) as { status: string };
  // Both holds authorized -> both captured -> voucher issued -> ticketed, all in one call.
  assert.equal(chargedProposal.status, 'ticketed');

  // ---- tickets (§15) ----
  const ticketsRes = await t.app.inject({ method: 'GET', url: '/tickets', headers: authHeader(alice.accessToken) });
  const tickets = JSON.parse(ticketsRes.body) as Array<{ id: string; code: string; dateProposalId: string; status: string }>;
  const ticket = tickets.find((tk) => tk.dateProposalId === proposal.id);
  assert.ok(ticket, 'alice should have a ticket for the proposal');
  assert.equal(ticket!.status, 'issued');

  const redeemRes = await t.app.inject({
    method: 'POST',
    url: `/tickets/${ticket!.id}/redeem`,
    headers: authHeader(alice.accessToken),
    payload: { code: ticket!.code },
  });
  assert.equal(redeemRes.statusCode, 200);
  const redeemBody = JSON.parse(redeemRes.body) as { dateProposal: { status: string }; voucher: { status: string } };
  assert.equal(redeemBody.voucher.status, 'redeemed');
  assert.equal(redeemBody.dateProposal.status, 'completed');

  // A check-in cannot be submitted before the date has started
  // (postDateFeedback.service#submitCheckIn), the proposal above was
  // scheduled 3 days out, so the manual test clock has to actually cross
  // that boundary first. Access tokens are also signed off `ctx.clock`
  // (auth.service.ts), so crossing 4 days expires the ones issued at
  // registration, refresh both before using them again below.
  t.clock.advanceDays(4);

  const aliceRefreshRes = await t.app.inject({ method: 'POST', url: '/auth/refresh', payload: { refreshToken: alice.refreshToken } });
  assert.equal(aliceRefreshRes.statusCode, 200);
  const aliceAccessToken = (JSON.parse(aliceRefreshRes.body) as { tokens: { accessToken: string } }).tokens.accessToken;

  const bobRefreshRes = await t.app.inject({ method: 'POST', url: '/auth/refresh', payload: { refreshToken: bob.refreshToken } });
  assert.equal(bobRefreshRes.statusCode, 200);
  const bobAccessToken = (JSON.parse(bobRefreshRes.body) as { tokens: { accessToken: string } }).tokens.accessToken;

  // ---- post-date check-in ----
  // The old `POST /date-proposals/:id/feedback` route (and the
  // `post_date_feedback.positive`/`safety_concern` columns it wrote) is
  // gone outright, no backward-compatibility shim, per the project
  // owner's "nothing has shipped, no compatibility path" instruction.
  // `POST /date-proposals/:id/check-in` is now the only way to submit
  // post-date feedback (postDateFeedback.service.ts).
  const checkInAliceRes = await t.app.inject({
    method: 'POST',
    url: `/date-proposals/${proposal.id}/check-in`,
    headers: authHeader(aliceAccessToken),
    payload: { outcome: 'happened_good', wouldMeetAgain: 'yes' },
  });
  assert.equal(checkInAliceRes.statusCode, 201);
  const checkInAlice = JSON.parse(checkInAliceRes.body) as { outcome: string; wouldMeetAgain: string; reportFiled: boolean };
  assert.equal(checkInAlice.outcome, 'happened_good');
  assert.equal(checkInAlice.wouldMeetAgain, 'yes');
  assert.equal(checkInAlice.reportFiled, false);

  const checkInBobRes = await t.app.inject({
    method: 'POST',
    url: `/date-proposals/${proposal.id}/check-in`,
    headers: authHeader(bobAccessToken),
    payload: { outcome: 'happened_good', wouldMeetAgain: 'yes' },
  });
  assert.equal(checkInBobRes.statusCode, 201);

  // Each participant can read back their own check-in.
  const getCheckInRes = await t.app.inject({
    method: 'GET',
    url: `/date-proposals/${proposal.id}/check-in`,
    headers: authHeader(aliceAccessToken),
  });
  assert.equal(getCheckInRes.statusCode, 200);

  // ---- established chat, no longer decays ----
  const conversationRes = await t.app.inject({
    method: 'GET',
    url: `/conversations/${conversationId}`,
    headers: authHeader(aliceAccessToken),
  });
  const conversation = JSON.parse(conversationRes.body) as { status: string };
  assert.equal(conversation.status, 'established');

  // ---- ledger sanity (admin view): both sides captured the full escrow ----
  const admin = await registerUser(t);
  const { rows: adminRow } = await t.pool.query<{ id: string }>('SELECT id FROM users WHERE id = $1', [admin.userId]);
  assert.ok(adminRow[0]);
  await t.pool.query('INSERT INTO admin_users (user_id) VALUES ($1)', [admin.userId]);

  const ledgerRes = await t.app.inject({
    method: 'GET',
    url: `/admin/users/${alice.userId}/ledger`,
    headers: authHeader(admin.accessToken),
  });
  assert.equal(ledgerRes.statusCode, 200);
  const ledger = JSON.parse(ledgerRes.body) as { items: Array<{ type: string; amountCents: number; dateProposalId: string }> };
  const captureEntry = ledger.items.find((e) => e.dateProposalId === proposal.id && e.type === 'capture');
  assert.ok(captureEntry, 'a capture ledger entry exists for alice on this proposal');
  assert.equal(captureEntry!.amountCents, proposal.escrowAmountCents);
});
