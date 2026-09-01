import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import * as interestService from '../../src/services/interest.service.js';
import { InterestTransitionError } from '../../src/services/interest.service.js';
import * as conversationService from '../../src/services/conversation.service.js';
import { ConflictError, ForbiddenError, NotFoundError, RateLimitError, ValidationError } from '../../src/lib/errors.js';
import { ManualClock } from '../../src/lib/time.js';
import { setupTestDatabase, teardownTestDatabase, buildCtx, userActor, insertUser } from './testCtxAgentC.js';
import type { Ctx } from '../../src/lib/ctx.js';

let pool: Awaited<ReturnType<typeof setupTestDatabase>>;
let clock: ManualClock;

before(async () => {
  pool = await setupTestDatabase('interest');
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

// =====================================================================
// §11.3, structurally impossible to attach free text before match.
// =====================================================================

function _typeOnly_cannotAttachMessageToSendInterest(ctx: Ctx, recipientId: string) {
  // @ts-expect-error sendInterest's signature is (ctx, recipientId: string)
  // there is no options object, so a caller cannot pass a `message`
  // field even by mistake. This is a compile-time guarantee (spec §11.3),
  // not a runtime-validated one; the surrounding function is never called.
  return interestService.sendInterest(ctx, recipientId, { message: 'hi there' });
}
void _typeOnly_cannotAttachMessageToSendInterest;

// =====================================================================
// Full legal transition matrix (spec §11.4).
// =====================================================================

test('legal transition: pending -> accepted creates a conversation', async () => {
  const sender = await makeUser();
  const recipient = await makeUser();
  const interest = await interestService.sendInterest(ctxFor(sender), recipient);
  assert.equal(interest.status, 'pending');

  const { interest: accepted, conversation } = await interestService.acceptInterest(ctxFor(recipient), interest.id);
  assert.equal(accepted.status, 'accepted');
  assert.ok(accepted.acceptedAt);
  assert.equal(conversation.status, 'active');
  assert.ok([conversation.userAId, conversation.userBId].includes(sender));
  assert.ok([conversation.userAId, conversation.userBId].includes(recipient));
});

test('legal transition: pending -> declined, sender sees only the generic copy (no reasoning field exists to leak)', async () => {
  const sender = await makeUser();
  const recipient = await makeUser();
  const interest = await interestService.sendInterest(ctxFor(sender), recipient);

  const declined = await interestService.declineInterest(ctxFor(recipient), interest.id);
  assert.equal(declined.status, 'declined');
  assert.ok(declined.declinedAt);
});

test('legal transition: pending -> canceled (by sender)', async () => {
  const sender = await makeUser();
  const recipient = await makeUser();
  const interest = await interestService.sendInterest(ctxFor(sender), recipient);

  const canceled = await interestService.cancelInterest(ctxFor(sender), interest.id);
  assert.equal(canceled.status, 'canceled');
  assert.ok(canceled.canceledAt);
});

test('legal transition: pending -> expired via the §25.1 job, and it frees the sender\'s outgoing slot', async () => {
  const sender = await makeUser();
  const recipient = await makeUser();
  const localClock = new ManualClock(new Date('2026-02-01T00:00:00.000Z'));
  const sysCtx = buildCtx({ actor: { type: 'system', job: 'interest_expiry' }, clock: localClock });

  const interest = await interestService.sendInterest({ ...sysCtx, actor: userActor(sender) }, recipient);
  assert.equal(interest.status, 'pending');

  localClock.advanceHours(49); // past the 48h default expiry
  const result = await interestService.expireDuePendingInterests(sysCtx);
  assert.equal(result.expired, 1);

  const [outgoing] = (await interestService.listOutgoing({ ...sysCtx, actor: userActor(sender) })).items;
  assert.equal(outgoing!.status, 'expired');
  assert.ok(outgoing!.expiredAt);
});

// =====================================================================
// Illegal transitions, every one must throw InterestTransitionError
// (except ownership/not-found, which get their own typed errors).
// =====================================================================

test('illegal: accepting an already-declined interest is rejected', async () => {
  const sender = await makeUser();
  const recipient = await makeUser();
  const interest = await interestService.sendInterest(ctxFor(sender), recipient);
  await interestService.declineInterest(ctxFor(recipient), interest.id);

  await assert.rejects(
    () => interestService.acceptInterest(ctxFor(recipient), interest.id),
    (err: unknown) => {
      assert.ok(err instanceof InterestTransitionError);
      assert.equal((err as InterestTransitionError).fromStatus, 'declined');
      return true;
    },
  );
});

test('illegal: declining twice is rejected', async () => {
  const sender = await makeUser();
  const recipient = await makeUser();
  const interest = await interestService.sendInterest(ctxFor(sender), recipient);
  await interestService.declineInterest(ctxFor(recipient), interest.id);

  await assert.rejects(() => interestService.declineInterest(ctxFor(recipient), interest.id), InterestTransitionError);
});

test('illegal: cancelling an already-accepted interest is rejected', async () => {
  const sender = await makeUser();
  const recipient = await makeUser();
  const interest = await interestService.sendInterest(ctxFor(sender), recipient);
  await interestService.acceptInterest(ctxFor(recipient), interest.id);

  await assert.rejects(
    () => interestService.cancelInterest(ctxFor(sender), interest.id),
    (err: unknown) => {
      assert.ok(err instanceof InterestTransitionError);
      assert.equal((err as InterestTransitionError).fromStatus, 'accepted');
      return true;
    },
  );
});

test('illegal: accepting an expired (but not-yet-swept) interest is rejected', async () => {
  const sender = await makeUser();
  const recipient = await makeUser();
  const localClock = new ManualClock(new Date('2026-03-01T00:00:00.000Z'));
  const senderCtx = buildCtx({ actor: userActor(sender), clock: localClock });
  const recipientCtx = buildCtx({ actor: userActor(recipient), clock: localClock });

  const interest = await interestService.sendInterest(senderCtx, recipient);
  localClock.advanceHours(49); // past expiry, but expireDuePendingInterests hasn't run

  await assert.rejects(
    () => interestService.acceptInterest(recipientCtx, interest.id),
    (err: unknown) => {
      assert.ok(err instanceof InterestTransitionError);
      assert.equal((err as InterestTransitionError).fromStatus, 'expired');
      return true;
    },
  );
});

test('illegal: only the recipient may accept/decline, only the sender may cancel', async () => {
  const sender = await makeUser();
  const recipient = await makeUser();
  const stranger = await makeUser();
  const interest = await interestService.sendInterest(ctxFor(sender), recipient);

  await assert.rejects(() => interestService.acceptInterest(ctxFor(stranger), interest.id), ForbiddenError);
  await assert.rejects(() => interestService.declineInterest(ctxFor(sender), interest.id), ForbiddenError);
  await assert.rejects(() => interestService.cancelInterest(ctxFor(recipient), interest.id), ForbiddenError);
});

test('illegal: acting on a nonexistent interest is NotFoundError, not a transition error', async () => {
  const someone = await makeUser();
  await assert.rejects(
    () => interestService.acceptInterest(ctxFor(someone), '00000000-0000-0000-0000-000000000000'),
    NotFoundError,
  );
});

test('sending an interest to yourself is rejected', async () => {
  const user = await makeUser();
  await assert.rejects(() => interestService.sendInterest(ctxFor(user), user), ValidationError);
});

test('a second pending interest to the same recipient while one is already pending is rejected', async () => {
  const sender = await makeUser();
  const recipient = await makeUser();
  await interestService.sendInterest(ctxFor(sender), recipient);
  await assert.rejects(() => interestService.sendInterest(ctxFor(sender), recipient), ConflictError);
});

// =====================================================================
// Cap enforcement at the exact boundary (spec §11.2, §30.2).
// =====================================================================

test('outgoing pending cap: 5th send succeeds, 6th is refused with the §30.2 static copy', async () => {
  const sender = await makeUser();
  const recipients = await Promise.all(Array.from({ length: 6 }, () => makeUser()));

  for (let i = 0; i < 5; i++) {
    const interest = await interestService.sendInterest(ctxFor(sender), recipients[i]!);
    assert.equal(interest.status, 'pending');
  }

  await assert.rejects(
    () => interestService.sendInterest(ctxFor(sender), recipients[5]!),
    (err: unknown) => {
      assert.ok(err instanceof RateLimitError);
      assert.equal((err as RateLimitError).message, interestService.OUTGOING_LIMIT_REACHED_MESSAGE);
      return true;
    },
  );
});

test('incoming pending cap: refuses a send once the recipient inbox is full', async () => {
  const recipient = await makeUser();
  const senders = await Promise.all(Array.from({ length: 11 }, () => makeUser()));

  for (let i = 0; i < 10; i++) {
    await interestService.sendInterest(ctxFor(senders[i]!), recipient);
  }

  await assert.rejects(() => interestService.sendInterest(ctxFor(senders[10]!), recipient), RateLimitError);
});

test('daily outgoing cap is enforced against a lowered live config value', async () => {
  const admin = 'test-admin';
  const localClock = new ManualClock(new Date('2026-04-01T00:00:00.000Z'));
  const ctx = buildCtx({ actor: { type: 'admin', adminId: admin }, clock: localClock });
  await ctx.config.set('interest.daily_outgoing_limit', 2, admin);

  const sender = await makeUser();
  const recipients = await Promise.all(Array.from({ length: 3 }, () => makeUser()));
  const senderCtx = buildCtx({ actor: userActor(sender), clock: localClock });

  await interestService.sendInterest(senderCtx, recipients[0]!);
  await interestService.sendInterest(senderCtx, recipients[1]!);
  await assert.rejects(() => interestService.sendInterest(senderCtx, recipients[2]!), RateLimitError);

  // Restore the default for later tests sharing this DB/process.
  await ctx.config.set('interest.daily_outgoing_limit', 20, admin);
});

// =====================================================================
// Policy-snapshot immutability across a config change (spec §21.3, MUST).
// =====================================================================

test('policy snapshot immutability: an interest keeps the expiry it was created under even after config changes', async () => {
  const admin = 'test-admin';
  const localClock = new ManualClock(new Date('2026-05-01T00:00:00.000Z'));
  const adminCtx = buildCtx({ actor: { type: 'admin', adminId: admin }, clock: localClock });

  const sender = await makeUser();
  const recipient1 = await makeUser();
  const recipient2 = await makeUser();
  // Deliberately share `adminCtx.config`'s ConfigService instance (rather
  // than calling `buildCtx` again, which would build a second instance
  // with its own independent in-memory cache), this test is about
  // whether an *already-created interest* observes a config change, not
  // about cross-instance cache coherency (out of scope per
  // config.service.ts's own docs).
  const senderCtx = { ...adminCtx, actor: userActor(sender) };

  const before = await interestService.sendInterest(senderCtx, recipient1);
  assert.equal(before.policySnapshot['interest.expiry_hours'], 48);
  const expectedExpiry = new Date(localClock.now().getTime() + 48 * 60 * 60 * 1000);
  assert.equal(before.expiresAt.getTime(), expectedExpiry.getTime());

  await adminCtx.config.set('interest.expiry_hours', 10, admin);

  // The already-created interest must not observe the change at all.
  assert.equal(before.policySnapshot['interest.expiry_hours'], 48);
  assert.equal(before.expiresAt.getTime(), expectedExpiry.getTime());

  // A brand-new interest picks up the new live value.
  const after = await interestService.sendInterest(senderCtx, recipient2);
  assert.equal(after.policySnapshot['interest.expiry_hours'], 10);
  assert.equal(after.expiresAt.getTime(), localClock.now().getTime() + 10 * 60 * 60 * 1000);

  // Restore the default for later tests sharing this DB/process.
  await adminCtx.config.set('interest.expiry_hours', 48, admin);
});

// =====================================================================
// Cross-module wiring: acceptInterest really does hand off to conversation.service.
// =====================================================================

test('acceptInterest and conversation.getOrCreateConversation agree on the same row (idempotent reuse)', async () => {
  const sender = await makeUser();
  const recipient = await makeUser();
  const interest = await interestService.sendInterest(ctxFor(sender), recipient);
  const { conversation } = await interestService.acceptInterest(ctxFor(recipient), interest.id);

  const again = await conversationService.getOrCreateConversation(ctxFor(sender), sender, recipient);
  assert.equal(again.id, conversation.id);
});
