/**
 * Unit tests for `eligibility.service.ts` and the two enforcement layers
 * built on it in `interest.service.ts` (Layer 2, send-time refusal), plus
 * a verification test for Layer 1 (discovery's existing mutual filter
 * gate, `discovery.service.ts` / `filter.service.ts`, neither modified
 * by this build).
 *
 * Layer 3 (the retroactive auto-decline sweep) has its own file,
 * `autoDecline.test.ts`, sharing this file's `odate_elig_eligibility`... no
 * see `testCtxEligibility.ts`: each test FILE gets its own database
 * (`odate_elig_eligibility` here, `odate_elig_autodecline` there).
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { RateLimitError } from '../../src/lib/errors.js';
import { ManualClock } from '../../src/lib/time.js';
import * as interestService from '../../src/services/interest.service.js';
import { evaluateMutualEligibility } from '../../src/services/eligibility.service.js';
import { getDiscoveryGrid } from '../../src/services/discovery.service.js';
import type { Ctx } from '../../src/lib/ctx.js';
import {
  setupTestDatabase,
  teardownTestDatabase,
  buildCtx,
  userActor,
  makeUser,
  setHardFilter,
  setSelfAnswer,
  getTestPool,
} from './testCtxEligibility.js';

let clock: ManualClock;

before(async () => {
  await setupTestDatabase('eligibility');
  clock = new ManualClock(new Date('2026-01-01T00:00:00.000Z'));
});

after(async () => {
  await teardownTestDatabase();
});

function ctxFor(userId: string): Ctx {
  return buildCtx({ actor: userActor(userId), clock });
}

async function countInterestsFor(userId: string): Promise<number> {
  const { rows } = await getTestPool().query<{ count: string }>(
    `SELECT count(*)::text AS count FROM interests WHERE sender_id = $1`,
    [userId],
  );
  return Number(rows[0]!.count);
}

// =====================================================================
// LAYER 1, verify, don't rebuild: discovery's existing mutual filter
// gate really does exclude both directions (spec §9.4, §10.2 rules 7-8).
// =====================================================================

test('Layer 1 (discovery): A (deal breaker: no kids) never sees B (has kids), and B never sees A either', async () => {
  const pool = getTestPool();
  const a = await makeUser(pool, { age: 30 });
  const b = await makeUser(pool, { age: 30 });

  // A's deal breaker: only match people scoring <= 2 on has_children (i.e. "no kids").
  await setHardFilter(pool, a, 'qb:has_children', 'lte', 2);
  // B scores 5 on has_children ("has kids").
  await setSelfAnswer(pool, b, 'has_children', 5);

  const aGrid = await getDiscoveryGrid(ctxFor(a), {});
  assert.ok(
    !aGrid.items.some((c) => c.userId === b),
    'B (has kids) must never appear in A (no-kids deal breaker)\'s discovery grid',
  );

  const bGrid = await getDiscoveryGrid(ctxFor(b), {});
  assert.ok(
    !bGrid.items.some((c) => c.userId === a),
    'A must never appear in B\'s discovery grid either, mutual filter passing runs both directions (spec §9.4)',
  );
});

test('Layer 1 (discovery): an eligible pair (no deal breaker in play) DOES see each other, the gate is precise, not just "hide everyone"', async () => {
  const pool = getTestPool();
  const c = await makeUser(pool, { age: 30 });
  const d = await makeUser(pool, { age: 30 });
  await setHardFilter(pool, c, 'qb:has_children', 'lte', 2);
  await setSelfAnswer(pool, d, 'has_children', 1); // "no kids", passes C's filter

  const cGrid = await getDiscoveryGrid(ctxFor(c), {});
  assert.ok(cGrid.items.some((cand) => cand.userId === d), 'D should be visible to C once D passes C\'s filter');
});

// =====================================================================
// LAYER 2, refuse the doomed interest at send time.
// =====================================================================

test('Layer 2: sendInterest refuses a doomed send (direct link / stale-grid bypass) and creates no interest row', async () => {
  const pool = getTestPool();
  const a = await makeUser(pool, { age: 30 });
  const b = await makeUser(pool, { age: 30 });
  await setHardFilter(pool, a, 'qb:has_children', 'lte', 2);
  await setSelfAnswer(pool, b, 'has_children', 5); // has kids, fails A's filter

  // B tries to send an interest straight to A (e.g. via a direct profile
  // link, or a discovery card fetched before A tightened their filter),
  // this must be refused even though B never saw A in their own grid.
  await assert.rejects(() => interestService.sendInterest(ctxFor(b), a), RateLimitError);

  assert.equal(await countInterestsFor(b), 0, 'no interest row should have been created');
});

test('Layer 2: refusal does NOT consume the sender\'s outgoing slot or daily quota', async () => {
  const pool = getTestPool();
  const sender = await makeUser(pool, { age: 30 });
  const ineligibleRecipient = await makeUser(pool, { age: 30 });
  await setHardFilter(pool, ineligibleRecipient, 'qb:has_children', 'lte', 2);
  await setSelfAnswer(pool, sender, 'has_children', 5);

  // Two refused sends in a row.
  await assert.rejects(() => interestService.sendInterest(ctxFor(sender), ineligibleRecipient), RateLimitError);
  await assert.rejects(() => interestService.sendInterest(ctxFor(sender), ineligibleRecipient), RateLimitError);
  assert.equal(await countInterestsFor(sender), 0);

  // The sender's outgoing-pending limit (default 5) and daily quota
  // (default 20) must be completely untouched by those refusals: sending
  // 5 legitimate interests to 5 OTHER, eligible recipients must still all
  // succeed.
  const eligibleRecipients = await Promise.all(Array.from({ length: 5 }, () => makeUser(pool, { age: 30 })));
  for (const r of eligibleRecipients) {
    const interest = await interestService.sendInterest(ctxFor(sender), r);
    assert.equal(interest.status, 'pending');
  }
  assert.equal(await countInterestsFor(sender), 5, 'exactly the 5 legitimate sends should have created rows');
});

test('Layer 2: privacy, the refusal is byte-identical (message AND details) no matter which filter/attribute failed, and never names one', async () => {
  const pool = getTestPool();

  // Three independent recipients, each excluding the sender via a DIFFERENT filter key.
  const byAge = await makeUser(pool, { age: 30 });
  await setHardFilter(pool, byAge, 'age_min', 'gte', 99); // sender's age will never satisfy this

  const byChildren = await makeUser(pool, { age: 30 });
  await setHardFilter(pool, byChildren, 'qb:has_children', 'lte', 1);

  const byGender = await makeUser(pool, { age: 30 });
  await setHardFilter(pool, byGender, 'gender_preference', 'eq', 'nonbinary');

  const senderReal = await makeUser(pool, { age: 30, gender: 'woman' });
  await setSelfAnswer(pool, senderReal, 'has_children', 5); // fails byChildren's filter

  const caught: Array<{ message: string; details: unknown }> = [];
  for (const recipient of [byAge, byChildren, byGender]) {
    try {
      await interestService.sendInterest(ctxFor(senderReal), recipient);
      assert.fail(`expected sendInterest to be refused for recipient excluding via a different filter (${recipient})`);
    } catch (err) {
      assert.ok(err instanceof RateLimitError);
      caught.push({ message: (err as RateLimitError).message, details: (err as RateLimitError).details });
    }
  }

  assert.equal(caught.length, 3);
  // All three refusals must be byte-identical to each other...
  for (const c of caught) {
    assert.deepEqual(c, caught[0]);
  }
  // ...and must be the neutral static copy, never a section reference,
  // never an attribute/filter-key name, never the word "filter" itself.
  // (Checked against the message text and the `details` VALUE only, not
  // a JSON dump of the whole envelope, the structural key "message"
  // itself contains the substring "age", which would be a false
  // positive against the *shape* of the response, not its content.)
  assert.equal(caught[0]!.message, interestService.RECIPIENT_UNAVAILABLE_MESSAGE);
  const contentOnly = `${caught[0]!.message} ${JSON.stringify(caught[0]!.details)}`.toLowerCase();
  for (const forbidden of ['age_min', 'age_max', 'qb:has_children', 'gender_preference', 'filter', '§', 'section']) {
    assert.ok(!contentOnly.includes(forbidden.toLowerCase()), `refusal payload must not mention "${forbidden}": ${contentOnly}`);
  }
});

test('Layer 2: an eligible send still succeeds (the gate only blocks doomed sends, not everything)', async () => {
  const pool = getTestPool();
  const sender = await makeUser(pool, { age: 30 });
  const recipient = await makeUser(pool, { age: 30 });
  const interest = await interestService.sendInterest(ctxFor(sender), recipient);
  assert.equal(interest.status, 'pending');
});

// =====================================================================
// eligibility.service.ts, direct unit tests (fail-open behavior).
// =====================================================================

test('evaluateMutualEligibility: eligible pair returns eligible:true, evaluatedOk:true', async () => {
  const pool = getTestPool();
  const a = await makeUser(pool, { age: 30 });
  const b = await makeUser(pool, { age: 30 });
  const result = await evaluateMutualEligibility(ctxFor(a), a, b);
  assert.deepEqual(result, { eligible: true, evaluatedOk: true });
});

test('evaluateMutualEligibility: ineligible pair returns eligible:false, evaluatedOk:true', async () => {
  const pool = getTestPool();
  const a = await makeUser(pool, { age: 30 });
  const b = await makeUser(pool, { age: 30 });
  await setHardFilter(pool, a, 'qb:has_children', 'lte', 1);
  await setSelfAnswer(pool, b, 'has_children', 5);
  const result = await evaluateMutualEligibility(ctxFor(a), a, b);
  assert.deepEqual(result, { eligible: false, evaluatedOk: true });
});

test('evaluateMutualEligibility: fails OPEN (eligible:true, evaluatedOk:false) when the underlying evaluation throws', async () => {
  const pool = getTestPool();
  const a = await makeUser(pool, { age: 30 });
  const b = await makeUser(pool, { age: 30 });
  const ctx = ctxFor(a);
  const throwingCtx: Ctx = {
    ...ctx,
    db: {
      query: async () => {
        throw new Error('simulated transient DB error');
      },
    },
  };
  const result = await evaluateMutualEligibility(throwingCtx, a, b);
  assert.deepEqual(result, { eligible: true, evaluatedOk: false });
});
