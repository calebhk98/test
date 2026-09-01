/**
 * HTTP tests for the `/matches` and `/conversations/:id/timeline` routes
 * (product-owner findings #1-#4). Driven entirely via `app.inject`, real
 * routes, real services — no mocking.
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
  t = await setupTestApp('matches');
});

after(async () => {
  await teardownTestApp(t);
});

// Many scenarios register several accounts against one shared in-process
// rate limiter (§19.2) — reset it between tests, same pattern
// `tests/http/roles.test.ts` uses.
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

test('GET /matches lists a match with click-through data and no coordinate leak', async () => {
  const alice = await registerUser(t);
  const bob = await registerUser(t);
  await completeOnboarding(t, alice.accessToken, { displayName: 'Alice', gender: 'woman', seeking: 'man' });
  await completeOnboarding(t, bob.accessToken, { displayName: 'Bob', gender: 'man', seeking: 'woman' });

  const conversationId = await makeMatch(alice, bob);

  const listRes = await t.app.inject({ method: 'GET', url: '/matches', headers: authHeader(alice.accessToken) });
  assert.equal(listRes.statusCode, 200);
  const list = JSON.parse(listRes.body) as { items: Array<Record<string, unknown>>; nextCursor: string | null };
  const row = list.items.find((m) => m.conversationId === conversationId);
  assert.ok(row, 'the new match appears in the list');
  assert.equal(row!.matchedUserId, bob.userId);
  assert.equal(row!.displayName, 'Bob');
  assert.equal('latitude' in row!, false);
  assert.equal('longitude' in row!, false);
  assert.equal(row!.conversationStatus, 'active');

  // Click-through: full profile via the existing, unmodified §24.5 route.
  const profileRes = await t.app.inject({
    method: 'GET',
    url: `/profiles/${row!.matchedUserId}`,
    headers: authHeader(alice.accessToken),
  });
  assert.equal(profileRes.statusCode, 200);
  const profile = JSON.parse(profileRes.body) as { displayName: string };
  assert.equal(profile.displayName, 'Bob');

  // Single-match detail matches the list row.
  const detailRes = await t.app.inject({ method: 'GET', url: `/matches/${conversationId}`, headers: authHeader(alice.accessToken) });
  assert.equal(detailRes.statusCode, 200);
  assert.deepEqual(JSON.parse(detailRes.body), row);
});

test('GET /matches is absent from a never-matched user, and a stranger conversationId 404s on /matches/:id', async () => {
  const alice = await registerUser(t);
  const stranger = await registerUser(t);
  await completeOnboarding(t, alice.accessToken, { displayName: 'Alice2', gender: 'woman', seeking: 'man' });
  await completeOnboarding(t, stranger.accessToken, { displayName: 'Stranger', gender: 'man', seeking: 'woman' });

  const listRes = await t.app.inject({ method: 'GET', url: '/matches', headers: authHeader(alice.accessToken) });
  const list = JSON.parse(listRes.body) as { items: Array<{ matchedUserId: string }> };
  assert.ok(!list.items.some((m) => m.matchedUserId === stranger.userId));

  const res = await t.app.inject({
    method: 'GET',
    url: '/matches/00000000-0000-0000-0000-000000000000',
    headers: authHeader(alice.accessToken),
  });
  assert.equal(res.statusCode, 404);
});

test('a venue-staff token cannot read /matches or /matches/:id (403)', async () => {
  const alice = await registerUser(t);
  const bob = await registerUser(t);
  await completeOnboarding(t, alice.accessToken, { displayName: 'Alice3', gender: 'woman', seeking: 'man' });
  await completeOnboarding(t, bob.accessToken, { displayName: 'Bob3', gender: 'man', seeking: 'woman' });
  const conversationId = await makeMatch(alice, bob);

  const staffUser = await registerUser(t);
  await makeVenueStaff(t, staffUser.userId);

  const listRes = await t.app.inject({ method: 'GET', url: '/matches', headers: authHeader(staffUser.accessToken) });
  assert.equal(listRes.statusCode, 403);

  const detailRes = await t.app.inject({ method: 'GET', url: `/matches/${conversationId}`, headers: authHeader(staffUser.accessToken) });
  assert.equal(detailRes.statusCode, 403);
});

// =====================================================================
// Timeline
// =====================================================================

test('a proposed date shows up in the conversation timeline over HTTP, with timestamps and conversation age derivable', async () => {
  resetRateLimiter(t);
  const alice = await registerUser(t);
  const bob = await registerUser(t);
  await completeOnboarding(t, alice.accessToken, { displayName: 'AliceT', gender: 'woman', seeking: 'man' });
  await completeOnboarding(t, bob.accessToken, { displayName: 'BobT', gender: 'man', seeking: 'woman' });
  const conversationId = await makeMatch(alice, bob);

  const msgRes = await t.app.inject({
    method: 'POST',
    url: `/conversations/${conversationId}/messages`,
    headers: authHeader(alice.accessToken),
    payload: { body: 'hi there!' },
  });
  assert.equal(msgRes.statusCode, 201);

  const venueId = await createVenue(t, { name: 'HTTP Timeline Cafe' });
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

  // Conversation-level timestamps: creation time + last activity, both ISO-8601.
  const conversationRes = await t.app.inject({ method: 'GET', url: `/conversations/${conversationId}`, headers: authHeader(alice.accessToken) });
  const conversation = JSON.parse(conversationRes.body) as { createdAt: string; lastMessageAt: string | null };
  const iso8601 = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/;
  assert.match(conversation.createdAt, iso8601);
  assert.match(conversation.lastMessageAt!, iso8601);
  // Conversation age is trivially client-derivable from an ISO timestamp —
  // the server sends the raw instant, never a pre-formatted "x hours ago"
  // relative string (spec: let the client localize).
  const ageMs = t.clock.now().getTime() - new Date(conversation.createdAt).getTime();
  assert.ok(ageMs >= 0);

  const timelineRes = await t.app.inject({
    method: 'GET',
    url: `/conversations/${conversationId}/timeline`,
    headers: authHeader(alice.accessToken),
  });
  assert.equal(timelineRes.statusCode, 200);
  const timeline = JSON.parse(timelineRes.body) as { items: Array<Record<string, unknown>>; nextCursor: string | null };

  const proposedEvent = timeline.items.find((e) => e.kind === 'date_proposed');
  assert.ok(proposedEvent, 'the date_proposed event appears in the timeline');
  assert.equal(proposedEvent!.dateProposalId, proposal.id);
  assert.equal(proposedEvent!.venueName, 'HTTP Timeline Cafe');
  assert.equal(proposedEvent!.status, 'pending_acceptance');
  assert.match(proposedEvent!.occurredAt as string, iso8601);
  // No relative-string formatting, no raw voucher/card data.
  for (const key of ['ago', 'qrPayload', 'processorIntentId', 'cardNumber', 'latitude', 'longitude']) {
    assert.ok(!(key in proposedEvent!));
  }

  const messageEvent = timeline.items.find((e) => e.kind === 'message');
  assert.ok(messageEvent);
  assert.match(messageEvent!.occurredAt as string, iso8601);

  // Both participants see the identical timeline.
  const bobTimelineRes = await t.app.inject({
    method: 'GET',
    url: `/conversations/${conversationId}/timeline`,
    headers: authHeader(bob.accessToken),
  });
  assert.deepEqual(JSON.parse(bobTimelineRes.body), timeline);
});

test('declining a date proposal over HTTP leaves the conversation active and messageable, and the timeline shows the decline', async () => {
  resetRateLimiter(t);
  const alice = await registerUser(t);
  const bob = await registerUser(t);
  await completeOnboarding(t, alice.accessToken, { displayName: 'AliceD', gender: 'woman', seeking: 'man' });
  await completeOnboarding(t, bob.accessToken, { displayName: 'BobD', gender: 'man', seeking: 'woman' });
  const conversationId = await makeMatch(alice, bob);

  const venueId = await createVenue(t, { name: 'Decline Test Venue' });
  const scheduledStart = new Date(t.clock.now().getTime() + 2 * 24 * 60 * 60 * 1000);
  const scheduledEnd = new Date(scheduledStart.getTime() + 60 * 60 * 1000);

  const proposeRes = await t.app.inject({
    method: 'POST',
    url: `/conversations/${conversationId}/date-proposals`,
    headers: authHeader(alice.accessToken),
    payload: { venueId, scheduledStart: scheduledStart.toISOString(), scheduledEnd: scheduledEnd.toISOString() },
  });
  const proposal = JSON.parse(proposeRes.body) as { id: string };

  const declineRes = await t.app.inject({
    method: 'POST',
    url: `/date-proposals/${proposal.id}/decline`,
    headers: authHeader(bob.accessToken),
  });
  assert.equal(declineRes.statusCode, 200);
  assert.equal(JSON.parse(declineRes.body).status, 'declined');

  const conversationRes = await t.app.inject({ method: 'GET', url: `/conversations/${conversationId}`, headers: authHeader(alice.accessToken) });
  assert.equal(JSON.parse(conversationRes.body).status, 'active');

  const followUpMsgRes = await t.app.inject({
    method: 'POST',
    url: `/conversations/${conversationId}/messages`,
    headers: authHeader(alice.accessToken),
    payload: { body: 'all good, another time maybe?' },
  });
  assert.equal(followUpMsgRes.statusCode, 201);

  const secondProposeRes = await t.app.inject({
    method: 'POST',
    url: `/conversations/${conversationId}/date-proposals`,
    headers: authHeader(alice.accessToken),
    payload: {
      venueId,
      scheduledStart: new Date(scheduledStart.getTime() + 24 * 60 * 60 * 1000).toISOString(),
      scheduledEnd: new Date(scheduledEnd.getTime() + 24 * 60 * 60 * 1000).toISOString(),
    },
  });
  assert.equal(secondProposeRes.statusCode, 201);
  assert.equal(JSON.parse(secondProposeRes.body).status, 'pending_acceptance');

  const timelineRes = await t.app.inject({
    method: 'GET',
    url: `/conversations/${conversationId}/timeline`,
    headers: authHeader(alice.accessToken),
  });
  const timeline = JSON.parse(timelineRes.body) as { items: Array<Record<string, unknown>> };
  assert.ok(timeline.items.some((e) => e.kind === 'date_declined' && e.dateProposalId === proposal.id));
});

test('a non-participant gets 404 and a venue-staff/admin token gets 403 on the timeline route', async () => {
  const alice = await registerUser(t);
  const bob = await registerUser(t);
  await completeOnboarding(t, alice.accessToken, { displayName: 'AliceR', gender: 'woman', seeking: 'man' });
  await completeOnboarding(t, bob.accessToken, { displayName: 'BobR', gender: 'man', seeking: 'woman' });
  const conversationId = await makeMatch(alice, bob);

  const outsider = await registerUser(t);
  const outsiderRes = await t.app.inject({
    method: 'GET',
    url: `/conversations/${conversationId}/timeline`,
    headers: authHeader(outsider.accessToken),
  });
  assert.equal(outsiderRes.statusCode, 404);

  const staffUser = await registerUser(t);
  await makeVenueStaff(t, staffUser.userId);
  const staffRes = await t.app.inject({
    method: 'GET',
    url: `/conversations/${conversationId}/timeline`,
    headers: authHeader(staffUser.accessToken),
  });
  assert.equal(staffRes.statusCode, 403);

  const admin = await registerUser(t);
  await makeAdmin(t, admin.userId);
  const adminRes = await t.app.inject({
    method: 'GET',
    url: `/conversations/${conversationId}/timeline`,
    headers: authHeader(admin.accessToken),
  });
  assert.equal(adminRes.statusCode, 403);
});

test('the route table registers /matches, /matches/:conversationId, and the timeline route', () => {
  assert.ok(t.app.hasRoute({ method: 'GET', url: '/matches' }));
  assert.ok(t.app.hasRoute({ method: 'GET', url: '/matches/:conversationId' }));
  assert.ok(t.app.hasRoute({ method: 'GET', url: '/conversations/:conversationId/timeline' }));
});
