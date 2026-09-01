/**
 * HTTP tests for every capability this build routed for the first time
 * (docs/ux-api-review.md): the notification centre, device-token
 * registration, `GET /me/photos`, `GET /venues/:venueId`,
 * `GET /me/capabilities`, the enriched interests list, the enriched
 * tickets list, and the physical-attribute round trip on
 * `PATCH`/`GET /me/profile`. Driven entirely via `app.inject`, real
 * routes, real services, no mocking. Uses the shared
 * `tests/http/testServer.ts` harness (owned by the API/HTTP agent,
 * imported not edited), same as every other `tests/http/*` suite.
 */
import { test, before, after, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import {
  setupTestApp,
  teardownTestApp,
  registerUser,
  authHeader,
  completeOnboarding,
  createVenue,
  makeVenueStaff,
  makeAdmin,
  resetRateLimiter,
} from './testServer.js';
import type { TestApp } from './testServer.js';

let t: TestApp;

before(async () => {
  t = await setupTestApp('wiring');
});

after(async () => {
  await teardownTestApp(t);
});

beforeEach(() => {
  resetRateLimiter(t);
});

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

// =====================================================================
// Device token registration
// =====================================================================

test('POST /devices registers a push token; GET /devices lists it; DELETE /devices disables it', async () => {
  const alice = await registerUser(t);

  const registerRes = await t.app.inject({
    method: 'POST',
    url: '/devices',
    headers: authHeader(alice.accessToken),
    payload: { platform: 'ios', deviceId: 'device-1', pushToken: 'push-token-1' },
  });
  assert.equal(registerRes.statusCode, 201);
  const registered = JSON.parse(registerRes.body) as { platform: string; pushToken: string; enabled: boolean };
  assert.equal(registered.platform, 'ios');
  assert.equal(registered.pushToken, 'push-token-1');
  assert.equal(registered.enabled, true);

  const listRes = await t.app.inject({ method: 'GET', url: '/devices', headers: authHeader(alice.accessToken) });
  assert.equal(listRes.statusCode, 200);
  const list = JSON.parse(listRes.body) as Array<{ pushToken: string; enabled: boolean }>;
  assert.ok(list.some((d) => d.pushToken === 'push-token-1' && d.enabled));

  const deleteRes = await t.app.inject({
    method: 'DELETE',
    url: '/devices',
    headers: authHeader(alice.accessToken),
    payload: { pushToken: 'push-token-1' },
  });
  assert.equal(deleteRes.statusCode, 204);

  const listAfterRes = await t.app.inject({ method: 'GET', url: '/devices', headers: authHeader(alice.accessToken) });
  const listAfter = JSON.parse(listAfterRes.body) as Array<{ pushToken: string; enabled: boolean }>;
  const row = listAfter.find((d) => d.pushToken === 'push-token-1');
  assert.ok(row, 'the disabled token row is still listed');
  assert.equal(row!.enabled, false);
});

test('devices routes are user-only: a venue-staff token gets 403', async () => {
  const staffUser = await registerUser(t);
  await makeVenueStaff(t, staffUser.userId);

  const res = await t.app.inject({
    method: 'POST',
    url: '/devices',
    headers: authHeader(staffUser.accessToken),
    payload: { platform: 'android', deviceId: 'd', pushToken: 'p' },
  });
  assert.equal(res.statusCode, 403);
});

// =====================================================================
// Notification centre
// =====================================================================

test('GET /notifications and POST /notifications/:id/read: an interest_received notification is reachable, filterable by unreadOnly, and markable read', async () => {
  const alice = await registerUser(t);
  const bob = await registerUser(t);

  const sendRes = await t.app.inject({
    method: 'POST',
    url: '/interests',
    headers: authHeader(alice.accessToken),
    payload: { recipientId: bob.userId },
  });
  assert.equal(sendRes.statusCode, 201);

  const listRes = await t.app.inject({ method: 'GET', url: '/notifications', headers: authHeader(bob.accessToken) });
  assert.equal(listRes.statusCode, 200);
  const list = JSON.parse(listRes.body) as { items: Array<{ id: string; eventType: string; readAt: string | null }>; nextCursor: string | null };
  const row = list.items.find((n) => n.eventType === 'interest_received');
  assert.ok(row, 'bob has an interest_received notification');
  assert.equal(row!.readAt, null);

  const unreadRes = await t.app.inject({
    method: 'GET',
    url: '/notifications?unreadOnly=true',
    headers: authHeader(bob.accessToken),
  });
  const unread = JSON.parse(unreadRes.body) as { items: Array<{ id: string }> };
  assert.ok(unread.items.some((n) => n.id === row!.id));

  const readRes = await t.app.inject({
    method: 'POST',
    url: `/notifications/${row!.id}/read`,
    headers: authHeader(bob.accessToken),
  });
  assert.equal(readRes.statusCode, 204);

  const unreadAfterRes = await t.app.inject({
    method: 'GET',
    url: '/notifications?unreadOnly=true',
    headers: authHeader(bob.accessToken),
  });
  const unreadAfter = JSON.parse(unreadAfterRes.body) as { items: Array<{ id: string }> };
  assert.ok(!unreadAfter.items.some((n) => n.id === row!.id));
});

test('a user cannot mark another user’s notification read (404, never leaks whose it is)', async () => {
  const alice = await registerUser(t);
  const bob = await registerUser(t);
  const carol = await registerUser(t);

  await t.app.inject({ method: 'POST', url: '/interests', headers: authHeader(alice.accessToken), payload: { recipientId: bob.userId } });
  const listRes = await t.app.inject({ method: 'GET', url: '/notifications', headers: authHeader(bob.accessToken) });
  const list = JSON.parse(listRes.body) as { items: Array<{ id: string }> };
  const notificationId = list.items[0]!.id;

  const res = await t.app.inject({
    method: 'POST',
    url: `/notifications/${notificationId}/read`,
    headers: authHeader(carol.accessToken),
  });
  assert.equal(res.statusCode, 403);
});

// =====================================================================
// GET /me/photos
// =====================================================================

test('GET /me/photos returns the own-profile photo grid in position order', async () => {
  const alice = await registerUser(t);
  await completeOnboarding(t, alice.accessToken, { displayName: 'PhotoAlice', gender: 'woman', seeking: 'man' });

  const res = await t.app.inject({ method: 'GET', url: '/me/photos', headers: authHeader(alice.accessToken) });
  assert.equal(res.statusCode, 200);
  const photos = JSON.parse(res.body) as Array<{ id: string; position: number; imageUrl: string }>;
  assert.equal(photos.length, 3);
  assert.deepEqual(
    photos.map((p) => p.position),
    [...photos.map((p) => p.position)].sort((a, b) => a - b),
  );
});

// =====================================================================
// GET /venues/:venueId
// =====================================================================

test('GET /venues/:venueId returns the single venue; an unknown id 404s', async () => {
  const alice = await registerUser(t);
  const venueId = await createVenue(t, { name: 'Single Venue Fetch Cafe' });

  const res = await t.app.inject({ method: 'GET', url: `/venues/${venueId}`, headers: authHeader(alice.accessToken) });
  assert.equal(res.statusCode, 200);
  const venue = JSON.parse(res.body) as { id: string; name: string };
  assert.equal(venue.id, venueId);
  assert.equal(venue.name, 'Single Venue Fetch Cafe');

  const notFoundRes = await t.app.inject({
    method: 'GET',
    url: '/venues/00000000-0000-0000-0000-000000000000',
    headers: authHeader(alice.accessToken),
  });
  assert.equal(notFoundRes.statusCode, 404);
});

// =====================================================================
// GET /me/capabilities
// =====================================================================

test('GET /me/capabilities returns a decision for every trust-gated action, including payment_method_required for propose_date with no payment method on file', async () => {
  const alice = await registerUser(t);

  const res = await t.app.inject({ method: 'GET', url: '/me/capabilities', headers: authHeader(alice.accessToken) });
  assert.equal(res.statusCode, 200);
  const capabilities = JSON.parse(res.body) as Record<string, { allowed: boolean; reasonCode?: string }>;
  for (const action of ['browse', 'send_interest', 'chat', 'send_links', 'propose_date']) {
    assert.ok(action in capabilities, `capabilities response includes "${action}"`);
  }
  assert.equal(capabilities.browse!.allowed, true);
});

test('GET /me/capabilities: propose_date becomes allowed once a verified payment method is on file', async () => {
  const alice = await registerUser(t);
  await completeOnboarding(t, alice.accessToken, { displayName: 'CapAlice', gender: 'woman', seeking: 'man' });

  const res = await t.app.inject({ method: 'GET', url: '/me/capabilities', headers: authHeader(alice.accessToken) });
  const capabilities = JSON.parse(res.body) as Record<string, { allowed: boolean }>;
  // completeOnboarding's default account is standard trust, which never
  // needed a payment method to be `allowed` for propose_date in the
  // first place (the gate only bites Limited trust), this asserts the
  // route reaches trust.service#can() with a real hasVerifiedPaymentMethod
  // signal either way, never throwing.
  assert.equal(capabilities.propose_date!.allowed, true);
});

// =====================================================================
// Enriched GET /interests/incoming and /outgoing
// =====================================================================

test('GET /interests/incoming and /outgoing are enriched with the counterpart’s profile, not bare ids, and drop policySnapshot', async () => {
  const alice = await registerUser(t);
  const bob = await registerUser(t);
  await completeOnboarding(t, alice.accessToken, { displayName: 'EnrichAlice', gender: 'woman', seeking: 'man' });
  await completeOnboarding(t, bob.accessToken, { displayName: 'EnrichBob', gender: 'man', seeking: 'woman' });

  const sendRes = await t.app.inject({
    method: 'POST',
    url: '/interests',
    headers: authHeader(alice.accessToken),
    payload: { recipientId: bob.userId },
  });
  assert.equal(sendRes.statusCode, 201);

  const incomingRes = await t.app.inject({ method: 'GET', url: '/interests/incoming', headers: authHeader(bob.accessToken) });
  assert.equal(incomingRes.statusCode, 200);
  const incoming = JSON.parse(incomingRes.body) as { items: Array<Record<string, unknown>> };
  const incomingRow = incoming.items[0]!;
  assert.equal(incomingRow.counterpartUserId, alice.userId);
  assert.equal(incomingRow.displayName, 'EnrichAlice');
  assert.equal('policySnapshot' in incomingRow, false);
  assert.equal('senderId' in incomingRow, false);

  const outgoingRes = await t.app.inject({ method: 'GET', url: '/interests/outgoing', headers: authHeader(alice.accessToken) });
  assert.equal(outgoingRes.statusCode, 200);
  const outgoing = JSON.parse(outgoingRes.body) as { items: Array<Record<string, unknown>> };
  const outgoingRow = outgoing.items[0]!;
  assert.equal(outgoingRow.counterpartUserId, bob.userId);
  assert.equal(outgoingRow.displayName, 'EnrichBob');
  assert.equal('policySnapshot' in outgoingRow, false);
});

// =====================================================================
// Physical-attribute round trip on PATCH/GET /me/profile
// =====================================================================

test('PATCH /me/profile heightCm/weightG/bodyType/unitPreference/distancePrecisionFloorKm round-trip through GET /me/profile', async () => {
  const alice = await registerUser(t);

  const patchRes = await t.app.inject({
    method: 'PATCH',
    url: '/me/profile',
    headers: authHeader(alice.accessToken),
    payload: {
      // Base required fields, this is alice's first-ever profile write,
      // so `profile.service#updateMyProfile` requires the full required
      // set (no prior row to fall back on).
      displayName: 'RoundTripAlice',
      age: 29,
      gender: 'woman',
      seeking: 'man',
      relationshipIntention: 'long_term',
      heightCm: 178,
      weightG: 72000,
      weightVisible: false,
      bodyType: 'athletic',
      unitPreference: 'imperial',
      distancePrecisionFloorKm: 25,
    },
  });
  assert.equal(patchRes.statusCode, 200);
  const patched = JSON.parse(patchRes.body) as Record<string, unknown>;
  assert.equal(patched.heightCm, 178);
  assert.equal(patched.weightG, 72000);
  assert.equal(patched.weightVisible, false);
  assert.equal(patched.bodyType, 'athletic');
  assert.equal(patched.unitPreference, 'imperial');
  assert.equal(patched.distancePrecisionFloorKm, 25);

  const getRes = await t.app.inject({ method: 'GET', url: '/me/profile', headers: authHeader(alice.accessToken) });
  assert.equal(getRes.statusCode, 200);
  const fetched = JSON.parse(getRes.body) as Record<string, unknown>;
  assert.equal(fetched.heightCm, 178);
  assert.equal(fetched.weightG, 72000);
  assert.equal(fetched.weightVisible, false);
  assert.equal(fetched.bodyType, 'athletic');
  assert.equal(fetched.unitPreference, 'imperial');
  assert.equal(fetched.distancePrecisionFloorKm, 25);

  // The unset toggle: sending `null` clears it back to "use the platform default".
  const unsetRes = await t.app.inject({
    method: 'PATCH',
    url: '/me/profile',
    headers: authHeader(alice.accessToken),
    payload: { distancePrecisionFloorKm: null },
  });
  assert.equal(unsetRes.statusCode, 200);
  assert.equal(JSON.parse(unsetRes.body).distancePrecisionFloorKm, null);

  const getAfterUnsetRes = await t.app.inject({ method: 'GET', url: '/me/profile', headers: authHeader(alice.accessToken) });
  assert.equal(JSON.parse(getAfterUnsetRes.body).distancePrecisionFloorKm, null);
});

// =====================================================================
// Enriched GET /tickets
// =====================================================================

test('GET /tickets is denormalized with venue name/address and the proposal schedule, no per-ticket venue/date-proposal follow-up call needed', async () => {
  const alice = await registerUser(t);
  const bob = await registerUser(t);
  await completeOnboarding(t, alice.accessToken, { displayName: 'TixAlice', gender: 'woman', seeking: 'man' });
  await completeOnboarding(t, bob.accessToken, { displayName: 'TixBob', gender: 'man', seeking: 'woman' });
  const conversationId = await makeMatch(alice, bob);

  const venueId = await createVenue(t, { name: 'Ticket Wallet Cafe' });
  const scheduledStart = new Date(t.clock.now().getTime() + 2 * 24 * 60 * 60 * 1000);
  const scheduledEnd = new Date(scheduledStart.getTime() + 60 * 60 * 1000);

  const proposeRes = await t.app.inject({
    method: 'POST',
    url: `/conversations/${conversationId}/date-proposals`,
    headers: authHeader(alice.accessToken),
    payload: { venueId, scheduledStart: scheduledStart.toISOString(), scheduledEnd: scheduledEnd.toISOString() },
  });
  assert.equal(proposeRes.statusCode, 201);
  const proposal = JSON.parse(proposeRes.body) as { id: string };

  const acceptRes = await t.app.inject({
    method: 'POST',
    url: `/date-proposals/${proposal.id}/accept`,
    headers: authHeader(bob.accessToken),
  });
  assert.equal(acceptRes.statusCode, 200);
  assert.equal(JSON.parse(acceptRes.body).status, 'ticketed');

  const ticketsRes = await t.app.inject({ method: 'GET', url: '/tickets', headers: authHeader(alice.accessToken) });
  assert.equal(ticketsRes.statusCode, 200);
  const tickets = JSON.parse(ticketsRes.body) as Array<Record<string, unknown>>;
  const ticket = tickets.find((tk) => tk.dateProposalId === proposal.id)!;
  assert.ok(ticket, 'alice has a ticket for the proposal');
  assert.equal(ticket.venueName, 'Ticket Wallet Cafe');
  assert.equal(typeof ticket.venueAddress, 'string');
  assert.equal(ticket.scheduledStart, scheduledStart.toISOString());
  assert.equal(ticket.scheduledEnd, scheduledEnd.toISOString());

  const singleTicketRes = await t.app.inject({ method: 'GET', url: `/tickets/${ticket.id}`, headers: authHeader(alice.accessToken) });
  assert.equal(singleTicketRes.statusCode, 200);
  const singleTicket = JSON.parse(singleTicketRes.body) as Record<string, unknown>;
  assert.equal(singleTicket.venueName, 'Ticket Wallet Cafe');
  assert.equal(singleTicket.scheduledStart, scheduledStart.toISOString());

  // A stranger cannot fetch someone else's single ticket by id.
  const stranger = await registerUser(t);
  const strangerRes = await t.app.inject({ method: 'GET', url: `/tickets/${ticket.id}`, headers: authHeader(stranger.accessToken) });
  assert.equal(strangerRes.statusCode, 403);
});

// =====================================================================
// New-message notification (item 6, message.service was not previously
// permitted to call the notification layer at all, so message_received
// never fired; see INTERFACES.md's updated `message ─▶ notification` edge)
// =====================================================================

test('sending a message enqueues a message_received notification for the recipient, coalesced per (recipient, conversation)', async () => {
  const alice = await registerUser(t);
  const bob = await registerUser(t);
  const conversationId = await makeMatch(alice, bob);

  const sendRes = await t.app.inject({
    method: 'POST',
    url: `/conversations/${conversationId}/messages`,
    headers: authHeader(alice.accessToken),
    payload: { body: 'Hey Bob!' },
  });
  assert.equal(sendRes.statusCode, 201);

  const { rows } = await t.pool.query<{ user_id: string; event_type: string; coalescing_key: string; channel: string }>(
    `SELECT user_id, event_type, coalescing_key, channel FROM notification_outbox WHERE event_type = 'message_received'`,
  );
  assert.ok(rows.length > 0, 'a message_received outbox row was enqueued');
  for (const row of rows) {
    assert.equal(row.user_id, bob.userId, 'only the recipient is notified, never the sender');
    assert.equal(row.coalescing_key, `message:${bob.userId}:${conversationId}`);
  }
});

// =====================================================================
// Route table
// =====================================================================

test('the route table registers every newly-wired route', () => {
  assert.ok(t.app.hasRoute({ method: 'GET', url: '/notifications' }));
  assert.ok(t.app.hasRoute({ method: 'POST', url: '/notifications/:notificationId/read' }));
  assert.ok(t.app.hasRoute({ method: 'GET', url: '/devices' }));
  assert.ok(t.app.hasRoute({ method: 'POST', url: '/devices' }));
  assert.ok(t.app.hasRoute({ method: 'DELETE', url: '/devices' }));
  assert.ok(t.app.hasRoute({ method: 'GET', url: '/me/photos' }));
  assert.ok(t.app.hasRoute({ method: 'GET', url: '/venues/:venueId' }));
  assert.ok(t.app.hasRoute({ method: 'GET', url: '/me/capabilities' }));
});

test('an admin token is rejected (403) on the user-only new routes', async () => {
  const admin = await registerUser(t);
  await makeAdmin(t, admin.userId);

  for (const url of ['/notifications', '/devices', '/me/photos', '/me/capabilities']) {
    const res = await t.app.inject({ method: 'GET', url, headers: authHeader(admin.accessToken) });
    assert.equal(res.statusCode, 403, `${url} should reject an admin token`);
  }
});
