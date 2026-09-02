/**
 * HTTP tests for the post-date check-in routes
 * (`POST`/`GET /date-proposals/:dateProposalId/check-in`,
 * postDateFeedback.service.ts). Driven entirely via `app.inject`, real
 * routes, real services, no mocking. Uses the shared `tests/http/
 * testServer.ts` harness (owned by the API/HTTP agent, imported not
 * edited) for account registration, same as every other `tests/http/*`
 * suite.
 *
 * Date proposals are inserted directly via SQL (bypassing the
 * interest -> conversation -> propose -> accept -> capture flow, which
 * has its own dedicated coverage elsewhere), this file is about the
 * check-in routes themselves, not re-proving the payment/escrow state
 * machine.
 */
import { test, before, after, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestApp, teardownTestApp, registerUser, authHeader, resetRateLimiter } from './testServer.js';
import type { TestApp } from './testServer.js';

let t: TestApp;

before(async () => {
  t = await setupTestApp('feedback');
});

after(async () => {
  await teardownTestApp(t);
});

beforeEach(() => {
  resetRateLimiter(t);
});

let venueIdCache: string | undefined;
async function venueId(): Promise<string> {
  if (venueIdCache) return venueIdCache;
  const { rows } = await t.pool.query<{ id: string }>(
    `INSERT INTO venues (name, address, latitude, longitude, category, active, margin_percent, time_slot_config, redemption_method)
     VALUES ('Test Cafe', '1 Test St', 39.0, -89.0, 'coffee', true, 15, '{"slots":[]}'::jsonb, 'qr_scan')
     RETURNING id`,
  );
  venueIdCache = rows[0]!.id;
  return venueIdCache;
}

interface Proposal {
  id: string;
}

async function insertProposal(
  proposerId: string,
  recipientId: string,
  opts: { status?: string; scheduledStart?: Date; scheduledEnd?: Date } = {},
): Promise<Proposal> {
  const [a, b] = proposerId < recipientId ? [proposerId, recipientId] : [recipientId, proposerId];
  const { rows: convRows } = await t.pool.query<{ id: string }>(
    `INSERT INTO conversations (user_a_id, user_b_id, status) VALUES ($1, $2, 'active')
     ON CONFLICT (user_a_id, user_b_id) DO UPDATE SET status = conversations.status
     RETURNING id`,
    [a, b],
  );
  const venue = await venueId();
  const now = t.clock.now();
  const scheduledStart = opts.scheduledStart ?? new Date(now.getTime() - 6 * 60 * 60 * 1000);
  const scheduledEnd = opts.scheduledEnd ?? new Date(scheduledStart.getTime() + 60 * 60 * 1000);
  const { rows } = await t.pool.query<{ id: string }>(
    `INSERT INTO date_proposals (conversation_id, proposer_id, recipient_id, venue_id, scheduled_start, scheduled_end, status, policy_snapshot, escrow_amount_cents)
     VALUES ($1, $2, $3, $4, $5, $6, $7, '{}'::jsonb, 2000)
     RETURNING id`,
    [convRows[0]!.id, proposerId, recipientId, venue, scheduledStart, scheduledEnd, opts.status ?? 'completed'],
  );
  return { id: rows[0]!.id };
}

test('POST then GET /date-proposals/:id/check-in round-trips the submitter\'s own answer', async () => {
  const alice = await registerUser(t);
  const bob = await registerUser(t);
  const proposal = await insertProposal(alice.userId, bob.userId);

  const postRes = await t.app.inject({
    method: 'POST',
    url: `/date-proposals/${proposal.id}/check-in`,
    headers: authHeader(alice.accessToken),
    payload: { outcome: 'happened_good', wouldMeetAgain: 'yes', notes: 'Really enjoyed it' },
  });
  assert.equal(postRes.statusCode, 201);
  const posted = JSON.parse(postRes.body) as Record<string, unknown>;
  assert.equal(posted.outcome, 'happened_good');
  assert.equal(posted.wouldMeetAgain, 'yes');
  assert.equal(posted.notes, 'Really enjoyed it');
  assert.equal(posted.safetyFlag, 'none');
  assert.equal(posted.reportFiled, false);
  assert.equal(posted.dateProposalId, proposal.id);

  const getRes = await t.app.inject({
    method: 'GET',
    url: `/date-proposals/${proposal.id}/check-in`,
    headers: authHeader(alice.accessToken),
  });
  assert.equal(getRes.statusCode, 200);
  const fetched = JSON.parse(getRes.body) as Record<string, unknown>;
  assert.equal(fetched.id, posted.id);
});

test('GET /date-proposals/:id/check-in is 404 for a participant who never submitted, one-sided is the normal case, not an error', async () => {
  const alice = await registerUser(t);
  const bob = await registerUser(t);
  const proposal = await insertProposal(alice.userId, bob.userId);

  await t.app.inject({
    method: 'POST',
    url: `/date-proposals/${proposal.id}/check-in`,
    headers: authHeader(alice.accessToken),
    payload: { outcome: 'happened_good' },
  });

  const bobGet = await t.app.inject({
    method: 'GET',
    url: `/date-proposals/${proposal.id}/check-in`,
    headers: authHeader(bob.accessToken),
  });
  assert.equal(bobGet.statusCode, 404, 'bob has not checked in himself, and must never be handed alice\'s row instead');
});

test('a non-participant cannot submit or read a check-in for a date they were not part of', async () => {
  const alice = await registerUser(t);
  const bob = await registerUser(t);
  const stranger = await registerUser(t);
  const proposal = await insertProposal(alice.userId, bob.userId);

  const postRes = await t.app.inject({
    method: 'POST',
    url: `/date-proposals/${proposal.id}/check-in`,
    headers: authHeader(stranger.accessToken),
    payload: { outcome: 'happened_good' },
  });
  assert.equal(postRes.statusCode, 403);

  const getRes = await t.app.inject({
    method: 'GET',
    url: `/date-proposals/${proposal.id}/check-in`,
    headers: authHeader(stranger.accessToken),
  });
  assert.equal(getRes.statusCode, 404); // never checked in themselves either, same 404 as any other non-submitter, not a distinguishing 403
});

test('the four outcome categories all round-trip distinctly over HTTP (never collapsed into one score)', async () => {
  const alice = await registerUser(t);
  const outcomes = ['did_not_happen', 'happened_bad', 'happened_fine', 'happened_good'] as const;
  for (const outcome of outcomes) {
    const bob = await registerUser(t);
    const proposal = await insertProposal(alice.userId, bob.userId);
    const res = await t.app.inject({
      method: 'POST',
      url: `/date-proposals/${proposal.id}/check-in`,
      headers: authHeader(alice.accessToken),
      payload: { outcome },
    });
    assert.equal(res.statusCode, 201);
    const body = JSON.parse(res.body) as { outcome: string };
    assert.equal(body.outcome, outcome);
  }
});

test('a safety flag is never observable by the other party through ANY HTTP surface, not the check-in route, not the date-proposal view, not their own trust events', async () => {
  const alice = await registerUser(t);
  const bob = await registerUser(t);
  const proposal = await insertProposal(alice.userId, bob.userId);

  const postRes = await t.app.inject({
    method: 'POST',
    url: `/date-proposals/${proposal.id}/check-in`,
    headers: authHeader(alice.accessToken),
    payload: { outcome: 'happened_bad', safetyFlag: 'incident', safetyDetails: 'a very specific http-only safety detail' },
  });
  assert.equal(postRes.statusCode, 201);
  const posted = JSON.parse(postRes.body) as { safetyFlag: string; safetyDetails: string };
  assert.equal(posted.safetyFlag, 'incident'); // alice, the submitter, sees her own answer plainly
  assert.equal(posted.safetyDetails, 'a very specific http-only safety detail');

  // Bob (the reported party) cannot fetch a check-in, he has none of his own.
  const bobCheckIn = await t.app.inject({ method: 'GET', url: `/date-proposals/${proposal.id}/check-in`, headers: authHeader(bob.accessToken) });
  assert.equal(bobCheckIn.statusCode, 404);
  assert.ok(!bobCheckIn.body.includes('very specific http-only safety detail'));

  // Bob's own view of the date proposal itself carries nothing about it.
  const bobProposal = await t.app.inject({ method: 'GET', url: `/date-proposals/${proposal.id}`, headers: authHeader(bob.accessToken) });
  assert.equal(bobProposal.statusCode, 200);
  assert.ok(!bobProposal.body.toLowerCase().includes('safety'));
  assert.ok(!bobProposal.body.includes('very specific http-only safety detail'));

  // Bob's own trust-event history carries no safety text and no
  // dateProposalId correlating it back to this specific date/partner.
  const bobTrustEvents = await t.app.inject({ method: 'GET', url: '/me/trust/events', headers: authHeader(bob.accessToken) });
  assert.equal(bobTrustEvents.statusCode, 200);
  assert.ok(!bobTrustEvents.body.includes('very specific http-only safety detail'));
  assert.ok(!bobTrustEvents.body.includes(proposal.id), 'trust events must not correlate back to a specific date proposal');
});

test('submitting a check-in requires the date to have started, and only accepts an eligible date-proposal status', async () => {
  const alice = await registerUser(t);
  const bob = await registerUser(t);

  const future = await insertProposal(alice.userId, bob.userId, {
    status: 'ticketed',
    scheduledStart: new Date(t.clock.now().getTime() + 3600_000),
    scheduledEnd: new Date(t.clock.now().getTime() + 7200_000),
  });
  const tooSoon = await t.app.inject({
    method: 'POST',
    url: `/date-proposals/${future.id}/check-in`,
    headers: authHeader(alice.accessToken),
    payload: { outcome: 'happened_good' },
  });
  assert.equal(tooSoon.statusCode, 409);

  const neverTicketed = await insertProposal(alice.userId, bob.userId, { status: 'pending_acceptance' });
  const wrongStatus = await t.app.inject({
    method: 'POST',
    url: `/date-proposals/${neverTicketed.id}/check-in`,
    headers: authHeader(alice.accessToken),
    payload: { outcome: 'happened_good' },
  });
  assert.equal(wrongStatus.statusCode, 409);
});

test('submitCheckIn input is Zod-validated over HTTP, an invalid outcome/safetyFlag is rejected with a typed validation error', async () => {
  const alice = await registerUser(t);
  const bob = await registerUser(t);
  const proposal = await insertProposal(alice.userId, bob.userId);

  const res = await t.app.inject({
    method: 'POST',
    url: `/date-proposals/${proposal.id}/check-in`,
    headers: authHeader(alice.accessToken),
    payload: { outcome: 'it_was_complicated' },
  });
  assert.equal(res.statusCode, 400);
  const body = JSON.parse(res.body) as { error: { code: string } };
  assert.equal(body.error.code, 'validation_error');
});

// There is no legacy `POST /date-proposals/:id/feedback` route any more
// (see dates.routes.ts and postDateFeedback.service.ts's removal of
// submitLegacyFeedback: this is a prototype, no external consumers, no
// reason to keep translating an older request shape onto the check-in
// once the check-in was the only real writer). `submitCheckIn` is the
// single write path, so there is only one call order to prove, a second
// submission for the same date proposal simply overwrites the caller's
// own row.
test('submitting a second check-in for the same date proposal overwrites the caller\'s own row, not a second one', async () => {
  const alice = await registerUser(t);
  const bob = await registerUser(t);
  const proposal = await insertProposal(alice.userId, bob.userId);

  const firstRes = await t.app.inject({
    method: 'POST',
    url: `/date-proposals/${proposal.id}/check-in`,
    headers: authHeader(alice.accessToken),
    payload: { outcome: 'happened_bad', wouldMeetAgain: 'no' },
  });
  assert.equal(firstRes.statusCode, 201);

  const secondRes = await t.app.inject({
    method: 'POST',
    url: `/date-proposals/${proposal.id}/check-in`,
    headers: authHeader(alice.accessToken),
    payload: { outcome: 'happened_good', wouldMeetAgain: 'yes' },
  });
  assert.equal(secondRes.statusCode, 201);

  const getRes = await t.app.inject({ method: 'GET', url: `/date-proposals/${proposal.id}/check-in`, headers: authHeader(alice.accessToken) });
  const body = JSON.parse(getRes.body) as { outcome: string; wouldMeetAgain: string };
  assert.equal(body.outcome, 'happened_good', 'the later call wins, one row, one writer');
  assert.equal(body.wouldMeetAgain, 'yes');

  const { rows } = await t.pool.query<{ count: string }>(
    `SELECT count(*)::text AS count FROM post_date_feedback WHERE date_proposal_id = $1 AND user_id = $2`,
    [proposal.id, alice.userId],
  );
  assert.equal(rows[0]!.count, '1', 'still exactly one row for this (date_proposal_id, user_id) pair');
});

test('the legacy feedback route no longer exists', async () => {
  const alice = await registerUser(t);
  const bob = await registerUser(t);
  const proposal = await insertProposal(alice.userId, bob.userId);

  const res = await t.app.inject({
    method: 'POST',
    url: `/date-proposals/${proposal.id}/feedback`,
    headers: authHeader(alice.accessToken),
    payload: { positive: true, wouldMeetAgain: true },
  });
  assert.equal(res.statusCode, 404, 'POST /date-proposals/:id/feedback was removed, there is no backward-compatible translator left standing in for it');
});
