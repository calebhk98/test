/**
 * The §11.4 interest state machine, driven exhaustively: every legal
 * transition (C-11.4.SM.L1-L4) and every illegal one the checklist names
 * (C-11.4.SM.I1-I7), against `interest.service.ts` and a real database,
 * rather than a sample of the table. See docs/conformance.md's "Interest
 * state machine (§11.4)" table for the ground truth this file walks.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { setupConformanceDb, teardownConformanceDb, makeCtx, userActor, createUser, type TestDb } from './support.js';
import * as interestService from '../../src/services/interest.service.js';
import { ConflictError, ForbiddenError } from '../../src/lib/errors.js';

let db: TestDb;

before(async () => {
  db = await setupConformanceDb('interestsm');
});

after(async () => {
  await teardownConformanceDb(db);
});

async function pair(): Promise<{ senderId: string; recipientId: string }> {
  const senderId = await createUser(db);
  const recipientId = await createUser(db);
  return { senderId, recipientId };
}

async function sendPending(senderId: string, recipientId: string) {
  const senderCtx = makeCtx(db, userActor(senderId));
  return interestService.sendInterest(senderCtx, recipientId);
}

// =====================================================================
// Legal transitions
// =====================================================================

test('C-11.4.SM.L1: pending -> accepted (recipient accepts), creates/reuses a conversation in the same operation', async () => {
  const { senderId, recipientId } = await pair();
  const interest = await sendPending(senderId, recipientId);
  assert.equal(interest.status, 'pending');

  const recipientCtx = makeCtx(db, userActor(recipientId));
  const { interest: accepted, conversation } = await interestService.acceptInterest(recipientCtx, interest.id);
  assert.equal(accepted.status, 'accepted');
  assert.equal(conversation.status, 'active');
});

test('C-11.4.SM.L2: pending -> declined (recipient declines)', async () => {
  const { senderId, recipientId } = await pair();
  const interest = await sendPending(senderId, recipientId);
  const recipientCtx = makeCtx(db, userActor(recipientId));
  const declined = await interestService.declineInterest(recipientCtx, interest.id);
  assert.equal(declined.status, 'declined');
});

test('C-11.4.SM.L3 / C-11.4.5 / C-11.4.6: pending -> expired at the 48h boundary (background job), sender outgoing slot freed', async () => {
  const { senderId, recipientId } = await pair();
  const interest = await sendPending(senderId, recipientId);
  assert.equal(interest.status, 'pending');

  // Boundary, just short: still pending, the job must not touch it.
  db.clock.advanceHours(47);
  db.clock.advanceMs(59 * 60 * 1000 + 59 * 1000); // + 59m59s = 47h59m59s total
  const systemCtx = makeCtx(db, { type: 'system', job: 'interest_expiry' });
  const early = await interestService.expireDuePendingInterests(systemCtx);
  assert.equal(early.expired, 0, 'must not expire a single second before the 48h boundary');

  // Exactly at the boundary: eligible.
  db.clock.advanceMs(1000);
  const swept = await interestService.expireDuePendingInterests(systemCtx);
  assert.equal(swept.expired, 1);

  const senderCtx = makeCtx(db, userActor(senderId));
  const outgoing = await interestService.listOutgoing(senderCtx);
  const found = outgoing.items.find((i) => i.id === interest.id);
  assert.equal(found?.status, 'expired');

  // C-11.4.6: the freed slot lets a brand-new interest through even at
  // the outgoing-pending cap (default 5). Reach the cap with 5 pending
  // interests (the just-expired one no longer counts toward it), confirm
  // the cap genuinely blocks a 6th, then expire ALL of them and confirm
  // sending becomes possible again purely because the slots were freed.
  for (let i = 0; i < 5; i++) {
    const freshRecipient = await createUser(db);
    await sendPending(senderId, freshRecipient);
  }
  const blockedRecipient = await createUser(db);
  await assert.rejects(() => sendPending(senderId, blockedRecipient), { name: 'RateLimitError' }, 'the outgoing-pending cap must genuinely be full here');

  db.clock.advanceHours(49); // past expiry for these 5 too
  await interestService.expireDuePendingInterests(systemCtx);

  const sixthRecipient = await createUser(db);
  const sixth = await sendPending(senderId, sixthRecipient); // must not throw now that slots are freed
  assert.equal(sixth.status, 'pending');
});

test('C-11.4.SM.L4: pending -> canceled (sender cancels)', async () => {
  const { senderId, recipientId } = await pair();
  const interest = await sendPending(senderId, recipientId);
  const senderCtx = makeCtx(db, userActor(senderId));
  const canceled = await interestService.cancelInterest(senderCtx, interest.id);
  assert.equal(canceled.status, 'canceled');
});

// =====================================================================
// Illegal transitions
// =====================================================================

test('C-11.4.SM.I1: accepted -> declined is rejected (terminal state)', async () => {
  const { senderId, recipientId } = await pair();
  const interest = await sendPending(senderId, recipientId);
  const recipientCtx = makeCtx(db, userActor(recipientId));
  await interestService.acceptInterest(recipientCtx, interest.id);
  await assert.rejects(() => interestService.declineInterest(recipientCtx, interest.id), ConflictError);
});

test('C-11.4.SM.I2: accepted -> canceled is rejected (cancel endpoint only valid while pending)', async () => {
  const { senderId, recipientId } = await pair();
  const interest = await sendPending(senderId, recipientId);
  const recipientCtx = makeCtx(db, userActor(recipientId));
  await interestService.acceptInterest(recipientCtx, interest.id);
  const senderCtx = makeCtx(db, userActor(senderId));
  await assert.rejects(() => interestService.cancelInterest(senderCtx, interest.id), ConflictError);
});

test('C-11.4.SM.I3: declined -> accepted is rejected (terminal state)', async () => {
  const { senderId, recipientId } = await pair();
  const interest = await sendPending(senderId, recipientId);
  const recipientCtx = makeCtx(db, userActor(recipientId));
  await interestService.declineInterest(recipientCtx, interest.id);
  await assert.rejects(() => interestService.acceptInterest(recipientCtx, interest.id), ConflictError);
});

test('C-11.4.SM.I4: expired -> accepted is rejected, even a same-moment accept after the expiry sweep', async () => {
  const { senderId, recipientId } = await pair();
  const interest = await sendPending(senderId, recipientId);
  db.clock.advanceHours(48);
  const systemCtx = makeCtx(db, { type: 'system', job: 'interest_expiry' });
  await interestService.expireDuePendingInterests(systemCtx);

  const recipientCtx = makeCtx(db, userActor(recipientId));
  await assert.rejects(() => interestService.acceptInterest(recipientCtx, interest.id), ConflictError);
});

test('C-11.4.SM.I4b: recipient cannot accept past expiry even if the sweep job never ran (row still says pending)', async () => {
  const { senderId, recipientId } = await pair();
  const interest = await sendPending(senderId, recipientId);
  db.clock.advanceHours(49); // past expiry, but no sweep job invoked
  const recipientCtx = makeCtx(db, userActor(recipientId));
  await assert.rejects(() => interestService.acceptInterest(recipientCtx, interest.id), ConflictError);
});

test('C-11.4.SM.I5: canceled -> accepted is rejected (terminal state)', async () => {
  const { senderId, recipientId } = await pair();
  const interest = await sendPending(senderId, recipientId);
  const senderCtx = makeCtx(db, userActor(senderId));
  await interestService.cancelInterest(senderCtx, interest.id);
  const recipientCtx = makeCtx(db, userActor(recipientId));
  await assert.rejects(() => interestService.acceptInterest(recipientCtx, interest.id), ConflictError);
});

test('C-11.4.SM.I6: double-accept race (sequential) resolves to exactly one terminal state, the second writer gets a conflict', async () => {
  const { senderId, recipientId } = await pair();
  const interest = await sendPending(senderId, recipientId);
  const recipientCtx = makeCtx(db, userActor(recipientId));
  const first = await interestService.acceptInterest(recipientCtx, interest.id);
  assert.equal(first.interest.status, 'accepted');
  await assert.rejects(() => interestService.acceptInterest(recipientCtx, interest.id), ConflictError, 'a second accept on an already-accepted interest must not silently succeed again');
});

test('C-11.4.SM.I6b: accept-then-decline race resolves to exactly one terminal state', async () => {
  const { senderId, recipientId } = await pair();
  const interest = await sendPending(senderId, recipientId);
  const recipientCtx = makeCtx(db, userActor(recipientId));
  await interestService.acceptInterest(recipientCtx, interest.id);
  await assert.rejects(() => interestService.declineInterest(recipientCtx, interest.id), ConflictError);
});

test('C-11.4.SM.I7: only the recipient may accept/decline; only the sender may cancel', async () => {
  const { senderId, recipientId } = await pair();

  const interestForAccept = await sendPending(senderId, recipientId);
  const senderCtx = makeCtx(db, userActor(senderId));
  await assert.rejects(() => interestService.acceptInterest(senderCtx, interestForAccept.id), ForbiddenError, 'the sender must not be able to accept their own sent interest');

  const freshRecipient = await createUser(db);
  const interestForDecline = await sendPending(senderId, freshRecipient);
  await assert.rejects(() => interestService.declineInterest(senderCtx, interestForDecline.id), ForbiddenError, 'the sender must not be able to decline their own sent interest');

  const interestForCancel = await sendPending(senderId, await createUser(db));
  const recipientCtx = makeCtx(db, userActor(recipientId));
  await assert.rejects(() => interestService.cancelInterest(recipientCtx, interestForCancel.id), ForbiddenError, 'the recipient must not be able to cancel an interest they did not send');
});
