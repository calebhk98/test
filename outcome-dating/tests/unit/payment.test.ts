/**
 * payment.service.ts unit tests. Spec §14, §14.5, §14.8.
 *
 * Exercises the hold lifecycle (authorize/capture/release/refund) against
 * a real Postgres database (own `odate_agent_d_payment` db) and the
 * deterministic `FakeProcessor`, with a focus on:
 *  - every hold-status transition writing exactly one matching ledger row,
 *  - idempotency: a replayed `captureHold` never double-charges,
 *  - the ledger being genuinely append-only (no update/delete API surface)
 *    and reconciling to the expected net position.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import * as paymentService from '../../src/services/payment.service.js';
import * as ledgerService from '../../src/services/ledger.service.js';
import { FakeProcessor } from '../../src/services/payments/fake.processor.js';
import { ConflictError, NotFoundError, ValidationError } from '../../src/lib/errors.js';
import {
  setupTestDb,
  teardownTestDb,
  makeCtx,
  userActor,
  createUser,
  createPaymentMethod,
  type TestDb,
} from './testHarness.js';

let db: TestDb;

before(async () => {
  db = await setupTestDb('payment');
});

after(async () => {
  await teardownTestDb(db);
});

async function proposalId(): Promise<string> {
  // date_proposals rows are owned by dateProposal.service in production,
  // but payment_holds only foreign-keys to date_proposals.id — insert a
  // minimal row directly so these tests can stay focused on the payment
  // lifecycle without depending on dateProposal.service's own logic.
  const proposerId = await createUser(db);
  const recipientId = await createUser(db);
  const venue = await db.pool.query<{ id: string }>(
    `INSERT INTO venues (name, address, latitude, longitude, category, active, margin_percent, time_slot_config, redemption_method)
     VALUES ('V', 'A', 0, 0, 'coffee', true, 10, '{}'::jsonb, 'qr_scan') RETURNING id`,
  );
  const conv = await db.pool.query<{ id: string }>(
    `INSERT INTO conversations (user_a_id, user_b_id, status) VALUES ($1, $2, 'active') RETURNING id`,
    [proposerId < recipientId ? proposerId : recipientId, proposerId < recipientId ? recipientId : proposerId],
  );
  const { rows } = await db.pool.query<{ id: string }>(
    `INSERT INTO date_proposals (conversation_id, proposer_id, recipient_id, venue_id, scheduled_start, scheduled_end, status, policy_snapshot, escrow_amount_cents)
     VALUES ($1, $2, $3, $4, now() + interval '3 days', now() + interval '3 days 2 hours', 'pending_acceptance', '{}'::jsonb, 2000)
     RETURNING id`,
    [conv.rows[0]!.id, proposerId, recipientId, venue.rows[0]!.id],
  );
  return rows[0]!.id;
}

test('authorizeHold: happy path authorizes and records one ledger entry', async () => {
  const dpId = await proposalId();
  const userId = await createUser(db);
  await createPaymentMethod(db, userId, 'tok_good');
  const ctx = makeCtx(db, userActor(userId));

  const hold = await paymentService.authorizeHold(ctx, { dateProposalId: dpId, userId, amountCents: 2000, currency: 'usd' });
  assert.equal(hold.status, 'authorized');
  assert.ok(hold.processorIntentId);
  assert.ok(hold.authorizedAt);

  const entries = await ledgerService.listEntriesForDateProposal(ctx, dpId);
  assert.equal(entries.length, 1);
  assert.equal(entries[0]!.type, 'authorization');
  assert.equal(entries[0]!.amountCents, 2000);
  assert.equal(entries[0]!.userId, userId);
});

test('authorizeHold: processor decline persists failed status with an audit-trail ledger entry', async () => {
  const dpId = await proposalId();
  const userId = await createUser(db);
  await createPaymentMethod(db, userId, 'tok_fail_authorize');
  const ctx = makeCtx(db, userActor(userId));

  const hold = await paymentService.authorizeHold(ctx, { dateProposalId: dpId, userId, amountCents: 2000, currency: 'usd' });
  assert.equal(hold.status, 'failed');
  assert.equal(hold.failureReason, 'card_declined');
  assert.equal(hold.processorIntentId, null);

  const entries = await ledgerService.listEntriesForDateProposal(ctx, dpId);
  assert.equal(entries.length, 1, 'a declined authorization is still recorded (spec §14.8)');
  assert.equal(entries[0]!.type, 'authorization');
  assert.equal((entries[0]!.metadata as { status: string }).status, 'failed');
});

test('authorizeHold: no payment method on file fails without calling the processor', async () => {
  const dpId = await proposalId();
  const userId = await createUser(db);
  const ctx = makeCtx(db, userActor(userId));

  const hold = await paymentService.authorizeHold(ctx, { dateProposalId: dpId, userId, amountCents: 2000, currency: 'usd' });
  assert.equal(hold.status, 'failed');
  assert.equal(hold.failureReason, 'no_payment_method');
});

test('authorizeHold: idempotent on retry — does not re-call the processor or duplicate the ledger entry', async () => {
  const dpId = await proposalId();
  const userId = await createUser(db);
  await createPaymentMethod(db, userId, 'tok_good');
  const ctx = makeCtx(db, userActor(userId));

  const first = await paymentService.authorizeHold(ctx, { dateProposalId: dpId, userId, amountCents: 2000, currency: 'usd' });
  const second = await paymentService.authorizeHold(ctx, { dateProposalId: dpId, userId, amountCents: 2000, currency: 'usd' });
  assert.equal(second.id, first.id);
  assert.equal(second.processorIntentId, first.processorIntentId);

  const entries = await ledgerService.listEntriesForDateProposal(ctx, dpId);
  assert.equal(entries.length, 1, 'retrying an already-authorized hold must not write a second ledger row');
});

test('captureHold: happy path captures and records the capture ledger entry', async () => {
  const dpId = await proposalId();
  const userId = await createUser(db);
  await createPaymentMethod(db, userId, 'tok_good');
  const ctx = makeCtx(db, userActor(userId));

  const authorized = await paymentService.authorizeHold(ctx, { dateProposalId: dpId, userId, amountCents: 2000, currency: 'usd' });
  const captured = await paymentService.captureHold(ctx, authorized.id);
  assert.equal(captured.status, 'captured');
  assert.ok(captured.capturedAt);

  const entries = await ledgerService.listEntriesForDateProposal(ctx, dpId);
  const captureEntries = entries.filter((e) => e.type === 'capture');
  assert.equal(captureEntries.length, 1);
  assert.equal(captureEntries[0]!.amountCents, 2000);
});

test('captureHold: cannot capture a hold that was never authorized', async () => {
  const dpId = await proposalId();
  const userId = await createUser(db);
  const ctx = makeCtx(db, userActor(userId));
  // No payment method -> authorizeHold leaves the hold 'failed'.
  const failed = await paymentService.authorizeHold(ctx, { dateProposalId: dpId, userId, amountCents: 2000, currency: 'usd' });
  await assert.rejects(() => paymentService.captureHold(ctx, failed.id), ConflictError);
});

test('captureHold: unknown hold id is a NotFoundError', async () => {
  const userId = await createUser(db);
  const ctx = makeCtx(db, userActor(userId));
  await assert.rejects(() => paymentService.captureHold(ctx, '00000000-0000-0000-0000-000000000000'), NotFoundError);
});

test('captureHold: processor decline leaves the hold failed with an audit-trail ledger entry, amount 0', async () => {
  const dpId = await proposalId();
  const userId = await createUser(db);
  await createPaymentMethod(db, userId, 'tok_fail_capture');
  const ctx = makeCtx(db, userActor(userId));

  const authorized = await paymentService.authorizeHold(ctx, { dateProposalId: dpId, userId, amountCents: 2000, currency: 'usd' });
  assert.equal(authorized.status, 'authorized');
  const captured = await paymentService.captureHold(ctx, authorized.id);
  assert.equal(captured.status, 'failed');

  const entries = await ledgerService.listEntriesForDateProposal(ctx, dpId);
  const captureEntries = entries.filter((e) => e.type === 'capture');
  assert.equal(captureEntries.length, 1);
  assert.equal(captureEntries[0]!.amountCents, 0, 'a failed capture moved no money, so the audit entry records 0 cents');
});

test('captureHold: REPLAYED capture is idempotent — no double charge, exactly one ledger row', async () => {
  const dpId = await proposalId();
  const userId = await createUser(db);
  await createPaymentMethod(db, userId, 'tok_good');
  const processor = new FakeProcessor();
  const ctx = makeCtx(db, userActor(userId), { payments: processor });

  const authorized = await paymentService.authorizeHold(ctx, { dateProposalId: dpId, userId, amountCents: 2000, currency: 'usd' });
  const first = await paymentService.captureHold(ctx, authorized.id);
  assert.equal(first.status, 'captured');

  // Simulate a replayed capture — e.g. a retried request or a duplicated
  // webhook-triggered call — hitting the exact same hold id again.
  const second = await paymentService.captureHold(ctx, authorized.id);
  assert.equal(second.status, 'captured');
  assert.equal(second.capturedAt?.getTime(), first.capturedAt?.getTime());

  const entries = await ledgerService.listEntriesForDateProposal(ctx, dpId);
  const captureEntries = entries.filter((e) => e.type === 'capture');
  assert.equal(captureEntries.length, 1, 'a replayed capture must not create a second ledger row');

  const intent = processor._debugGetIntent(authorized.processorIntentId!);
  assert.equal(intent?.capturedAmountCents, 2000, 'the processor itself must not have captured twice');
});

test('releaseHold: happy path releases an authorized hold', async () => {
  const dpId = await proposalId();
  const userId = await createUser(db);
  await createPaymentMethod(db, userId, 'tok_good');
  const ctx = makeCtx(db, userActor(userId));

  const authorized = await paymentService.authorizeHold(ctx, { dateProposalId: dpId, userId, amountCents: 2000, currency: 'usd' });
  const released = await paymentService.releaseHold(ctx, authorized.id);
  assert.equal(released.status, 'released');
  assert.ok(released.releasedAt);

  const entries = await ledgerService.listEntriesForDateProposal(ctx, dpId);
  assert.equal(entries.filter((e) => e.type === 'release').length, 1);
});

test('releaseHold: idempotent when already released; ConflictError from a captured hold', async () => {
  const dpId = await proposalId();
  const userId = await createUser(db);
  await createPaymentMethod(db, userId, 'tok_good');
  const ctx = makeCtx(db, userActor(userId));

  const authorized = await paymentService.authorizeHold(ctx, { dateProposalId: dpId, userId, amountCents: 2000, currency: 'usd' });
  const released1 = await paymentService.releaseHold(ctx, authorized.id);
  const released2 = await paymentService.releaseHold(ctx, authorized.id);
  assert.equal(released2.releasedAt?.getTime(), released1.releasedAt?.getTime());

  const dpId2 = await proposalId();
  const userId2 = await createUser(db);
  await createPaymentMethod(db, userId2, 'tok_good');
  const ctx2 = makeCtx(db, userActor(userId2));
  const authorized2 = await paymentService.authorizeHold(ctx2, { dateProposalId: dpId2, userId: userId2, amountCents: 2000, currency: 'usd' });
  await paymentService.captureHold(ctx2, authorized2.id);
  await assert.rejects(() => paymentService.releaseHold(ctx2, authorized2.id), ConflictError);
});

test('refundHold: full refund transitions the hold to refunded', async () => {
  const dpId = await proposalId();
  const userId = await createUser(db);
  await createPaymentMethod(db, userId, 'tok_good');
  const ctx = makeCtx(db, userActor(userId));

  const authorized = await paymentService.authorizeHold(ctx, { dateProposalId: dpId, userId, amountCents: 2000, currency: 'usd' });
  await paymentService.captureHold(ctx, authorized.id);
  const refunded = await paymentService.refundHold(ctx, authorized.id);
  assert.equal(refunded.status, 'refunded');

  const entries = await ledgerService.listEntriesForDateProposal(ctx, dpId);
  const refundEntries = entries.filter((e) => e.type === 'refund');
  assert.equal(refundEntries.length, 1);
  assert.equal(refundEntries[0]!.amountCents, 2000);
});

test('refundHold: cumulative partial refunds — repeating the same partial amount is idempotent, a larger target refunds only the delta', async () => {
  const dpId = await proposalId();
  const userId = await createUser(db);
  await createPaymentMethod(db, userId, 'tok_good');
  const ctx = makeCtx(db, userActor(userId));

  const authorized = await paymentService.authorizeHold(ctx, { dateProposalId: dpId, userId, amountCents: 2000, currency: 'usd' });
  await paymentService.captureHold(ctx, authorized.id);

  const partial1 = await paymentService.refundHold(ctx, authorized.id, 500);
  assert.equal(partial1.status, 'captured', 'not yet fully refunded, status stays captured');

  const partial1Again = await paymentService.refundHold(ctx, authorized.id, 500);
  assert.equal(partial1Again.status, 'captured');

  let entries = await ledgerService.listEntriesForDateProposal(ctx, dpId);
  let refundEntries = entries.filter((e) => e.type === 'refund');
  assert.equal(refundEntries.length, 1, 'repeating the same partial target must not double-refund');
  assert.equal(refundEntries[0]!.amountCents, 500);

  const partial2 = await paymentService.refundHold(ctx, authorized.id, 1200);
  assert.equal(partial2.status, 'captured');
  entries = await ledgerService.listEntriesForDateProposal(ctx, dpId);
  refundEntries = entries.filter((e) => e.type === 'refund');
  assert.equal(refundEntries.length, 2, 'raising the target refunds only the additional delta as a second entry');
  assert.equal(refundEntries[1]!.amountCents, 700);

  const totalRefunded = refundEntries.reduce((sum, e) => sum + e.amountCents, 0);
  assert.equal(totalRefunded, 1200);
});

test('refundHold: cannot refund more than was captured', async () => {
  const dpId = await proposalId();
  const userId = await createUser(db);
  await createPaymentMethod(db, userId, 'tok_good');
  const ctx = makeCtx(db, userActor(userId));

  const authorized = await paymentService.authorizeHold(ctx, { dateProposalId: dpId, userId, amountCents: 2000, currency: 'usd' });
  await paymentService.captureHold(ctx, authorized.id);
  await assert.rejects(() => paymentService.refundHold(ctx, authorized.id, 5000), ValidationError);
});

test('handleProcessorWebhook: a replayed webhook event does not double-record', async () => {
  const dpId = await proposalId();
  const userId = await createUser(db);
  await createPaymentMethod(db, userId, 'tok_good');
  const ctx = makeCtx(db, userActor(userId));

  const authorized = await paymentService.authorizeHold(ctx, { dateProposalId: dpId, userId, amountCents: 2000, currency: 'usd' });

  const event = { type: 'payment_intent.succeeded', processorIntentId: authorized.processorIntentId!, amountCents: 2000 };
  await paymentService.handleProcessorWebhook(ctx, event);
  await paymentService.handleProcessorWebhook(ctx, event); // replay

  const entries = await ledgerService.listEntriesForDateProposal(ctx, dpId);
  const captureEntries = entries.filter((e) => e.type === 'capture');
  assert.equal(captureEntries.length, 1, 'a replayed webhook must not write a second ledger row');
});

test('ledger: insert-only API surface — no update/delete function is exported', () => {
  const exported = ledgerService as unknown as Record<string, unknown>;
  assert.equal(typeof exported['updateEntry'], 'undefined');
  assert.equal(typeof exported['deleteEntry'], 'undefined');
  assert.equal(typeof exported['recordEntry'], 'function');
});

test('ledger: a full authorize->capture->refund flow reconciles to the expected net position', async () => {
  const dpId = await proposalId();
  const userId = await createUser(db);
  await createPaymentMethod(db, userId, 'tok_good');
  const ctx = makeCtx(db, userActor(userId));

  const authorized = await paymentService.authorizeHold(ctx, { dateProposalId: dpId, userId, amountCents: 2000, currency: 'usd' });
  await paymentService.captureHold(ctx, authorized.id);
  await paymentService.refundHold(ctx, authorized.id, 800);

  const entries = await ledgerService.listEntriesForDateProposal(ctx, dpId);
  // Append-only, chronological.
  assert.deepEqual(entries.map((e) => e.type), ['authorization', 'capture', 'refund']);

  const net = entries.reduce((sum, e) => {
    if (e.type === 'capture') return sum + e.amountCents;
    if (e.type === 'refund') return sum - e.amountCents;
    return sum; // authorization moves no money
  }, 0);
  assert.equal(net, 1200, 'net platform-held position = captured - refunded');

  const { checked, mismatches } = await ledgerService.reconcileWithProcessor(ctx);
  assert.ok(checked >= 1);
  assert.deepEqual(mismatches, [], 'a correctly-recorded flow must reconcile with no mismatches');
});
