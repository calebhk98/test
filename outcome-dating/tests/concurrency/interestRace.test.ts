/**
 * True concurrency tests for the interest state machine (spec
 * C-11.4.SM.I6: "concurrent accept+decline (or accept+accept) must
 * resolve to exactly one terminal state, second writer gets `conflict`").
 *
 * test-audit.md Finding 3: every test that claimed to cover this raced
 * the two calls SEQUENTIALLY (`await a(); await b();`), which only proves
 * the ordinary post-hoc illegal-transition guard, not a race. The one
 * genuinely concurrent pattern already in the suite is
 * `tests/jobs/scheduler.test.ts`'s `Promise.all`-based advisory-lock
 * test, this file applies that same pattern (via `Promise.allSettled`,
 * since here we expect exactly one side to reject) to the interest
 * machine `interest.service.ts` already protects with a single atomic
 * `UPDATE ... WHERE status = 'pending'` (a compare-and-swap, not a
 * read-then-write), so this is expected to genuinely pass, it is the
 * proof that CAS pattern actually holds under real concurrency, not just
 * in the sequential tests that were already there.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import * as interestService from '../../src/services/interest.service.js';
import { InterestTransitionError } from '../../src/services/interest.service.js';
import { ManualClock } from '../../src/lib/time.js';
import type { Ctx } from '../../src/lib/ctx.js';
import { setupTestDatabase, teardownTestDatabase, buildCtx, userActor, insertUser } from '../unit/testCtxAgentC.js';

let pool: Awaited<ReturnType<typeof setupTestDatabase>>;
let clock: ManualClock;

before(async () => {
  pool = await setupTestDatabase('concurrency_interest');
  clock = new ManualClock(new Date('2026-01-01T00:00:00.000Z'));
});

after(async () => {
  await teardownTestDatabase();
});

function ctxFor(userId: string): Ctx {
  return buildCtx({ actor: userActor(userId), clock });
}

async function makeUser(): Promise<string> {
  return insertUser(pool);
}

test('C-11.4.SM.I6: concurrent accept + decline of the SAME interest resolves to exactly one terminal state', async () => {
  const sender = await makeUser();
  const recipient = await makeUser();
  const interest = await interestService.sendInterest(ctxFor(sender), recipient);

  const [a, b] = await Promise.allSettled([
    interestService.acceptInterest(ctxFor(recipient), interest.id),
    interestService.declineInterest(ctxFor(recipient), interest.id),
  ]);

  const fulfilled = [a, b].filter((r) => r.status === 'fulfilled');
  const rejected = [a, b].filter((r) => r.status === 'rejected');
  assert.equal(fulfilled.length, 1, 'exactly one of the two concurrent calls must win');
  assert.equal(rejected.length, 1, 'the loser must get a typed conflict, not a silent no-op or a crash');
  assert.ok(
    (rejected[0] as PromiseRejectedResult).reason instanceof InterestTransitionError,
    'the loser must fail with the typed transition-conflict error, not a generic exception',
  );

  const [outgoing] = (await interestService.listOutgoing(ctxFor(sender))).items;
  assert.ok(
    outgoing!.status === 'accepted' || outgoing!.status === 'declined',
    'must land on exactly one terminal state, never neither and never both',
  );
  // Whichever call actually won must match the row's final status,
  // proves the "winner" promise and the persisted state agree, not just
  // that some promise resolved.
  if (a.status === 'fulfilled') assert.equal(outgoing!.status, 'accepted');
  else assert.equal(outgoing!.status, 'declined');
});

test('C-11.4.SM.I6 variant: concurrent accept + accept of the SAME interest only ever creates one conversation', async () => {
  const sender = await makeUser();
  const recipient = await makeUser();
  const interest = await interestService.sendInterest(ctxFor(sender), recipient);

  const [a, b] = await Promise.allSettled([
    interestService.acceptInterest(ctxFor(recipient), interest.id),
    interestService.acceptInterest(ctxFor(recipient), interest.id),
  ]);

  const fulfilled = [a, b].filter((r) => r.status === 'fulfilled') as PromiseFulfilledResult<
    Awaited<ReturnType<typeof interestService.acceptInterest>>
  >[];
  const rejected = [a, b].filter((r) => r.status === 'rejected');
  assert.equal(fulfilled.length, 1, 'exactly one concurrent accept must actually perform the transition');
  assert.equal(rejected.length, 1, 'the second concurrent accept must be rejected, not silently succeed again');
  assert.ok((rejected[0] as PromiseRejectedResult).reason instanceof InterestTransitionError);

  const { rows } = await pool.query<{ id: string }>(
    `SELECT id FROM conversations WHERE (user_a_id = $1 OR user_b_id = $1) AND (user_a_id = $2 OR user_b_id = $2)`,
    [sender, recipient],
  );
  assert.equal(rows.length, 1, 'exactly one conversation must exist between this pair, never two from a duplicated accept');
  assert.equal(fulfilled[0]!.value.conversation.id, rows[0]!.id, 'the winning call\'s own returned conversation must be that one row');
});
