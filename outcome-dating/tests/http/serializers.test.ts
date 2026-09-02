/**
 * Serializer-level privacy-invariant tests, one per invariant named in the
 * task brief: no exact coordinates (§7.1/§28.5), no card numbers (§28.4),
 * no reporter identity ever (§30.9), no raw trust weights (§6.3), no like
 * counts/popularity/boost fields (§10.1). Each test asserts on the actual
 * HTTP response body (not the internal domain object), since a serializer
 * bug that leaked a field would show up exactly there.
 */
import { test, before, beforeEach, after } from 'node:test';
import assert from 'node:assert/strict';
import {
  setupTestApp,
  teardownTestApp,
  registerUser,
  authHeader,
  completeOnboarding,
  makeAdmin,
  makeVenueStaff,
  createVenue,
  resetRateLimiter,
} from './testServer.js';
import type { TestApp } from './testServer.js';

let t: TestApp;

before(async () => {
  t = await setupTestApp('serializers');
});

after(async () => {
  await teardownTestApp(t);
});

beforeEach(() => {
  resetRateLimiter(t);
});

test('discovery cards never carry coordinates, like counts, popularity, or boost fields (§10.1, §28.5)', async () => {
  const viewer = await registerUser(t);
  const target = await registerUser(t);
  await completeOnboarding(t, viewer.accessToken, { displayName: 'Viewer', gender: 'woman', seeking: 'man' });
  await completeOnboarding(t, target.accessToken, { displayName: 'Target', gender: 'man', seeking: 'woman' });

  const res = await t.app.inject({ method: 'GET', url: '/discovery', headers: authHeader(viewer.accessToken) });
  assert.equal(res.statusCode, 200);
  const body = JSON.parse(res.body) as { items: Array<Record<string, unknown>> };
  const card = body.items.find((c) => c.userId === target.userId);
  assert.ok(card, 'target should be discoverable');

  // Wiring fix: `trustLevel` moved from allowed to forbidden here. It was
  // never part of the card's own design (product-owner rule: no
  // popularity/status signal on a card), and this test previously asserted
  // the old, over-broad shape; a candidate's trust level stays visible only
  // on their OWN trust page (`GET /me/trust`), never on someone else's card.
  const forbiddenKeys = [
    'latitude',
    'longitude',
    'likeCount',
    'popularityScore',
    'boosted',
    'badge',
    'compatibilityScore',
    'profileCompleteness',
    'trustLevel',
    'trustScore',
    'rank',
    'ranking',
    'rankingScore',
    'status',
    'statusBadge',
  ];
  for (const key of forbiddenKeys) {
    assert.equal(key in card!, false, `discovery card must not carry "${key}"`);
  }
  // Wiring fix (item 3): `primaryPhotoUrl` (a bare string) became
  // `primaryPhoto` (`{id, imageUrl, altText}`), see
  // src/http/serializers/discovery.ts's own doc.
  const allowedKeys = ['userId', 'displayName', 'age', 'approximateDistanceKm', 'primaryPhoto', 'sharedInterestTag'];
  for (const key of Object.keys(card!)) {
    assert.ok(allowedKeys.includes(key), `unexpected field "${key}" on discovery card`);
  }
  assert.equal('primaryPhotoUrl' in card!, false, 'the old bare-string field must be gone, not just renamed-and-kept');
});

/**
 * Wiring item 2: a pattern-based guard, not just an exact-name check, so
 * this fails the moment ANY status- or ranking-shaped field reappears on a
 * discovery card under a name this test hasn't been told about yet
 * (a renamed `trustLevel`, a new `rankScore`, a `verifiedBadge`, ...), the
 * same "actually catches something" discipline dashGuard.test.ts/
 * copyGuard.test.ts use: proven against a deliberately-violating fixture,
 * not just asserted quiet against the real response.
 */
const STATUS_OR_RANKING_KEY_PATTERN = /trust|status|rank|badge|boost|popular|like|score|tier|level/i;
/** The only allowed key that happens to match the pattern above (a distance measurement, not a status/ranking signal, see `approximateDistanceKm`'s own description elsewhere in this file). */
const STATUS_OR_RANKING_KEY_ALLOWLIST = new Set<string>([]);

function findStatusOrRankingKeys(card: Record<string, unknown>): string[] {
  return Object.keys(card).filter((k) => STATUS_OR_RANKING_KEY_PATTERN.test(k) && !STATUS_OR_RANKING_KEY_ALLOWLIST.has(k));
}

test('discovery card guard: no status- or ranking-shaped field under any name (pattern scan, not just an exact-name check)', async () => {
  const viewer = await registerUser(t);
  const target = await registerUser(t);
  await completeOnboarding(t, viewer.accessToken, { displayName: 'ViewerRank', gender: 'woman', seeking: 'man' });
  await completeOnboarding(t, target.accessToken, { displayName: 'TargetRank', gender: 'man', seeking: 'woman' });

  const res = await t.app.inject({ method: 'GET', url: '/discovery', headers: authHeader(viewer.accessToken) });
  assert.equal(res.statusCode, 200);
  const body = JSON.parse(res.body) as { items: Array<Record<string, unknown>> };
  const card = body.items.find((c) => c.userId === target.userId);
  assert.ok(card, 'target should be discoverable');

  const found = findStatusOrRankingKeys(card!);
  assert.deepEqual(found, [], `discovery card carries status/ranking-shaped field(s): ${found.join(', ')}`);

  // Prove the scanner itself actually catches something, not a silent no-op.
  const violatingFixture = { ...card, trustLevel: 'trusted' };
  assert.deepEqual(findStatusOrRankingKeys(violatingFixture), ['trustLevel']);
  const violatingFixture2 = { ...card, rankScore: 0.9 };
  assert.deepEqual(findStatusOrRankingKeys(violatingFixture2), ['rankScore']);
});

test('public profile view never carries exact coordinates (§7.1, §28.5, C-28.5.1)', async () => {
  const viewer = await registerUser(t);
  const target = await registerUser(t);
  await completeOnboarding(t, viewer.accessToken, { displayName: 'Viewer2', gender: 'woman', seeking: 'man' });
  await completeOnboarding(t, target.accessToken, { displayName: 'Target2', gender: 'man', seeking: 'woman' });

  const res = await t.app.inject({ method: 'GET', url: `/profiles/${target.userId}`, headers: authHeader(viewer.accessToken) });
  assert.equal(res.statusCode, 200);
  const body = JSON.parse(res.body) as Record<string, unknown>;
  assert.equal('latitude' in body, false);
  assert.equal('longitude' in body, false);
  assert.ok('approximateDistanceKm' in body);
});

test('payment methods never carry the raw processor token or a card-number-shaped field (§28.4)', async () => {
  const user = await registerUser(t);
  const res = await t.app.inject({
    method: 'POST',
    url: '/payment-methods',
    headers: authHeader(user.accessToken),
    payload: { processorToken: 'tok_visa_4242424242424242', brand: 'visa', last4: '4242' },
  });
  assert.equal(res.statusCode, 201);
  const body = JSON.parse(res.body) as Record<string, unknown>;
  assert.equal('processorToken' in body, false);
  assert.equal('cardNumber' in body, false);
  assert.equal('pan' in body, false);
  assert.equal(body.last4, '4242');

  const listRes = await t.app.inject({ method: 'GET', url: '/payment-methods', headers: authHeader(user.accessToken) });
  const list = JSON.parse(listRes.body) as Array<Record<string, unknown>>;
  for (const pm of list) {
    assert.equal('processorToken' in pm, false);
    const serialized = JSON.stringify(pm);
    assert.equal(/\b\d{13,19}\b/.test(serialized), false, 'no card-number-shaped digit run anywhere in the payment method response');
  }
});

test('venue-staff redemption response never carries emails, chat content, or payment/card data (§4.2)', async () => {
  const alice = await registerUser(t);
  const bob = await registerUser(t);
  await completeOnboarding(t, alice.accessToken, { displayName: 'AliceV', gender: 'woman', seeking: 'man' });
  await completeOnboarding(t, bob.accessToken, { displayName: 'BobV', gender: 'man', seeking: 'woman' });

  const sendRes = await t.app.inject({
    method: 'POST',
    url: '/interests',
    headers: authHeader(alice.accessToken),
    payload: { recipientId: bob.userId },
  });
  const interest = JSON.parse(sendRes.body) as { id: string };
  const acceptRes = await t.app.inject({
    method: 'POST',
    url: `/interests/${interest.id}/accept`,
    headers: authHeader(bob.accessToken),
  });
  const { conversation } = JSON.parse(acceptRes.body) as { conversation: { id: string } };

  const venueId = await createVenue(t, { name: 'Privacy Test Venue' });
  const start = new Date(t.clock.now().getTime() + 2 * 24 * 60 * 60 * 1000);
  const end = new Date(start.getTime() + 60 * 60 * 1000);
  const proposeRes = await t.app.inject({
    method: 'POST',
    url: `/conversations/${conversation.id}/date-proposals`,
    headers: authHeader(alice.accessToken),
    payload: { venueId, scheduledStart: start.toISOString(), scheduledEnd: end.toISOString() },
  });
  const proposal = JSON.parse(proposeRes.body) as { id: string };
  await t.app.inject({ method: 'POST', url: `/date-proposals/${proposal.id}/accept`, headers: authHeader(bob.accessToken) });

  const ticketsRes = await t.app.inject({ method: 'GET', url: '/tickets', headers: authHeader(alice.accessToken) });
  const tickets = (JSON.parse(ticketsRes.body) as { items: Array<{ code: string; dateProposalId: string }> }).items;
  const ticket = tickets.find((tk) => tk.dateProposalId === proposal.id)!;

  const staffUser = await registerUser(t);
  await makeVenueStaff(t, staffUser.userId, venueId);

  const redeemRes = await t.app.inject({
    method: 'POST',
    url: '/venue/redeem',
    headers: authHeader(staffUser.accessToken),
    payload: { code: ticket.code },
  });
  assert.equal(redeemRes.statusCode, 200);
  const raw = redeemRes.body;

  // Structural allowlist check (serializer-level enforcement).
  const body = JSON.parse(raw) as { voucher: object; dateProposal: object; redemption: object };
  const dpKeys = Object.keys(body.dateProposal);
  for (const key of dpKeys) {
    assert.ok(
      ['id', 'venueId', 'scheduledStart', 'scheduledEnd', 'status', 'participantNames'].includes(key),
      `venue-staff dateProposal view leaked unexpected field "${key}"`,
    );
  }
  // Property-style scan: no email-looking string, no "message"/"body" chat
  // content, no card/processor token fields anywhere in the payload.
  assert.equal(/[a-z0-9.+_-]+@[a-z0-9.-]+\.[a-z]{2,}/i.test(raw), false, 'no email address anywhere in a venue-staff response');
  assert.equal(raw.includes('processorToken'), false);
  assert.equal(raw.includes('processor_token'), false);
  assert.equal(raw.toLowerCase().includes('👋'), false, "the chat message body must never reach a venue-staff response");
});

test('reporter identity never reaches any response the reported user (or venue staff) can see (§30.9, C-30.9.2)', async () => {
  const reporter = await registerUser(t);
  const reported = await registerUser(t);

  const reportRes = await t.app.inject({
    method: 'POST',
    url: '/reports',
    headers: authHeader(reporter.accessToken),
    payload: { reportedId: reported.userId, category: 'spam', details: 'unwanted messages' },
  });
  assert.equal(reportRes.statusCode, 201);

  // The reported user has no route that surfaces reports filed against
  // them at all -- confirm no such data leaks via their own profile/trust
  // views, which is the only thing they can fetch about themselves.
  const meTrustRes = await t.app.inject({ method: 'GET', url: '/me/trust', headers: authHeader(reported.accessToken) });
  assert.equal(meTrustRes.statusCode, 200);
  assert.equal(meTrustRes.body.includes(reporter.userId), false);
  assert.equal(meTrustRes.body.toLowerCase().includes('reporter'), false);

  // Even the admin-facing moderation-action viewer never carries a
  // reporter id on the action itself (report.service.ts's own invariant:
  // reporter id is retained on automated_moderation_flags for admin
  // traceability elsewhere, never surfaced on `ModerationAction`).
  const admin = await registerUser(t);
  await makeAdmin(t, admin.userId);
  const actionsRes = await t.app.inject({
    method: 'GET',
    url: `/admin/moderation/actions?userId=${reported.userId}`,
    headers: authHeader(admin.accessToken),
  });
  assert.equal(actionsRes.statusCode, 200);
  const actions = JSON.parse(actionsRes.body) as { items: Array<Record<string, unknown>> };
  for (const action of actions.items) {
    assert.equal('reporterId' in action, false);
    assert.equal('reporter_id' in action, false);
  }
});

test('§6.3: trust summary defaults to exposing trustLevel only, never the raw weighting formula', async () => {
  const user = await registerUser(t);
  const res = await t.app.inject({ method: 'GET', url: '/me/trust', headers: authHeader(user.accessToken) });
  assert.equal(res.statusCode, 200);
  const body = JSON.parse(res.body) as Record<string, unknown>;
  assert.ok('trustLevel' in body);
  // Default (no flag enabled): the raw numeric score is withheld.
  assert.equal('trustScore' in body, false);
  // Never any per-factor weight/breakdown field, regardless of flag state.
  for (const key of Object.keys(body)) {
    assert.ok(
      ['trustLevel', 'trustScore', 'actionableImprovements', 'recentNegativeEvents'].includes(key),
      `unexpected field "${key}" on trust summary`,
    );
  }
});
