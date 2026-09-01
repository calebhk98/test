/**
 * timeline.service.ts unit tests. Product-owner findings #2/#3: a date
 * proposal must show up IN the conversation, and declining one must not
 * end the conversation.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import * as interestService from '../../src/services/interest.service.js';
import * as messageService from '../../src/services/message.service.js';
import * as conversationService from '../../src/services/conversation.service.js';
import * as dateProposalService from '../../src/services/dateProposal.service.js';
import * as timelineService from '../../src/services/timeline.service.js';
import { ForbiddenError, NotFoundError } from '../../src/lib/errors.js';
import { FakeProcessor } from '../../src/services/payments/fake.processor.js';
import {
  setupTestDb,
  teardownTestDb,
  makeCtx,
  userActor,
  systemActor,
  venueStaffActor,
  adminActor,
  createUserWithProfile,
  addPaymentMethod,
  createVenue,
  type TestDb,
} from './testHarnessMatch.js';

let db: TestDb;

before(async () => {
  db = await setupTestDb('timeline');
});

after(async () => {
  await teardownTestDb(db);
});

async function makeMatch(userAId: string, userBId: string): Promise<string> {
  const interest = await interestService.sendInterest(makeCtx(db, userActor(userAId)), userBId);
  const { conversation } = await interestService.acceptInterest(makeCtx(db, userActor(userBId)), interest.id);
  return conversation.id;
}

function kinds(events: timelineService.TimelineEvent[]): string[] {
  return events.map((e) => e.kind);
}

// =====================================================================
// A proposed date shows up IN the conversation for both participants,
// identically ordered.
// =====================================================================

test('a proposed date appears in both participants\' timelines, identically ordered', async () => {
  const proposer = await createUserWithProfile(db, { displayName: 'Iris' });
  const recipient = await createUserWithProfile(db, { displayName: 'Jack' });
  const processor = new FakeProcessor();
  await addPaymentMethod(db, proposer, 'tok_ok_proposer', processor);
  const venueId = await createVenue(db, { name: 'The Daily Grind' });
  const conversationId = await makeMatch(proposer, recipient);

  await messageService.sendMessage(makeCtx(db, userActor(proposer)), conversationId, 'hey! coffee sometime?');
  db.clock.advanceMs(1000);
  await messageService.sendMessage(makeCtx(db, userActor(recipient)), conversationId, 'sure, would love to');
  db.clock.advanceMs(1000);

  const scheduledStart = new Date(db.clock.now().getTime() + 7 * 24 * 60 * 60 * 1000);
  const scheduledEnd = new Date(scheduledStart.getTime() + 60 * 60 * 1000);
  const proposal = await dateProposalService.proposeDate(makeCtx(db, userActor(proposer), { payments: processor }), {
    conversationId,
    venueId,
    scheduledStart,
    scheduledEnd,
  });
  assert.equal(proposal.status, 'pending_acceptance');

  const proposerTimeline = await timelineService.getConversationTimeline(makeCtx(db, userActor(proposer)), conversationId);
  const recipientTimeline = await timelineService.getConversationTimeline(makeCtx(db, userActor(recipient)), conversationId);

  // Identical events, identical order, for both sides.
  assert.deepEqual(proposerTimeline, recipientTimeline);

  assert.deepEqual(kinds(proposerTimeline.items), ['date_proposed', 'message', 'message']);
  const proposedEvent = proposerTimeline.items.find((e) => e.kind === 'date_proposed')!;
  assert.equal(proposedEvent.kind, 'date_proposed');
  if (proposedEvent.kind !== 'message') {
    assert.equal(proposedEvent.dateProposalId, proposal.id);
    assert.equal(proposedEvent.venueName, 'The Daily Grind');
    assert.equal(proposedEvent.status, 'pending_acceptance');
    assert.equal(proposedEvent.scheduledStart, scheduledStart.toISOString());
    assert.equal(proposedEvent.hasTicket, false);
    assert.equal(proposedEvent.proposerId, proposer);
    assert.equal(proposedEvent.recipientId, recipient);
  }

  // No payment card data, no exact venue coordinates, no voucher payload
  // on any event — structural allowlist check.
  for (const e of proposerTimeline.items) {
    const keys = Object.keys(e);
    for (const forbidden of ['latitude', 'longitude', 'qrPayload', 'processorIntentId', 'last4', 'cardNumber']) {
      assert.ok(!keys.includes(forbidden), `event leaked forbidden field "${forbidden}"`);
    }
  }
});

// =====================================================================
// Every lifecycle event required by the task shows up.
// =====================================================================

test('the full accept -> ticket -> complete lifecycle appears as distinct events, in order', async () => {
  const proposer = await createUserWithProfile(db, { displayName: 'Kim' });
  const recipient = await createUserWithProfile(db, { displayName: 'Liam' });
  const processor = new FakeProcessor();
  await addPaymentMethod(db, proposer, 'tok_ok_proposer_2', processor);
  await addPaymentMethod(db, recipient, 'tok_ok_recipient_2', processor);
  const venueId = await createVenue(db, { name: 'Arcade Alley' });
  const conversationId = await makeMatch(proposer, recipient);

  const scheduledStart = new Date(db.clock.now().getTime() + 24 * 60 * 60 * 1000);
  const scheduledEnd = new Date(scheduledStart.getTime() + 60 * 60 * 1000);
  const proposal = await dateProposalService.proposeDate(makeCtx(db, userActor(proposer), { payments: processor }), {
    conversationId,
    venueId,
    scheduledStart,
    scheduledEnd,
  });

  db.clock.advanceMs(1000);
  const accepted = await dateProposalService.acceptDateProposal(makeCtx(db, userActor(recipient), { payments: processor }), proposal.id);
  assert.equal(accepted.status, 'ticketed'); // FakeProcessor succeeds end-to-end in one call

  db.clock.advanceMs(1000);
  await dateProposalService.markCompletedByRedemption(makeCtx(db, systemActor('redemption-test')), proposal.id);

  const timeline = await timelineService.getConversationTimeline(makeCtx(db, userActor(proposer)), conversationId);
  const proposalKinds = timeline.items.filter((e) => e.kind !== 'message').map((e) => e.kind);
  // Chronological (this timeline is newest-first) -> reverse to read as a story.
  assert.deepEqual([...proposalKinds].reverse(), ['date_proposed', 'date_accepted', 'date_ticketed', 'date_completed']);

  const ticketed = timeline.items.find((e) => e.kind === 'date_ticketed');
  const completed = timeline.items.find((e) => e.kind === 'date_completed');
  assert.ok(ticketed && ticketed.kind !== 'message' && ticketed.hasTicket === true);
  assert.ok(completed && completed.kind !== 'message' && completed.hasTicket === true);
  assert.ok(completed && completed.kind !== 'message' && completed.status === 'completed');

  const proposedAfterCompletion = timeline.items.find((e) => e.kind === 'date_proposed');
  assert.ok(proposedAfterCompletion && proposedAfterCompletion.kind !== 'message' && proposedAfterCompletion.hasTicket === false);
  // Even though the proposal has since completed, the "proposed" card
  // still reflects the status AS OF that moment, not the current one.
  assert.ok(proposedAfterCompletion && proposedAfterCompletion.kind !== 'message' && proposedAfterCompletion.status === 'pending_acceptance');
});

test('an expired proposal produces a date_expired event', async () => {
  const proposer = await createUserWithProfile(db, { displayName: 'Mona' });
  const recipient = await createUserWithProfile(db, { displayName: 'Noah' });
  const processor = new FakeProcessor();
  await addPaymentMethod(db, proposer, 'tok_ok_expiry', processor);
  const venueId = await createVenue(db, { name: 'Museum of Test' });
  const conversationId = await makeMatch(proposer, recipient);

  const scheduledStart = new Date(db.clock.now().getTime() + 30 * 24 * 60 * 60 * 1000);
  const scheduledEnd = new Date(scheduledStart.getTime() + 60 * 60 * 1000);
  const proposal = await dateProposalService.proposeDate(makeCtx(db, userActor(proposer), { payments: processor }), {
    conversationId,
    venueId,
    scheduledStart,
    scheduledEnd,
  });

  db.clock.advanceHours(200); // past date.accept_expiry_hours default
  await dateProposalService.expireDuePendingProposals(makeCtx(db, systemActor('expiry-test')));

  const timeline = await timelineService.getConversationTimeline(makeCtx(db, userActor(proposer)), conversationId);
  const expired = timeline.items.find((e) => e.kind === 'date_expired');
  assert.ok(expired && expired.kind !== 'message' && expired.dateProposalId === proposal.id);
  assert.ok(expired && expired.kind !== 'message' && expired.status === 'expired');
});

test('a canceled-before-acceptance proposal produces a date_canceled event', async () => {
  const proposer = await createUserWithProfile(db, { displayName: 'Omar' });
  const recipient = await createUserWithProfile(db, { displayName: 'Priya' });
  const processor = new FakeProcessor();
  await addPaymentMethod(db, proposer, 'tok_ok_cancel', processor);
  const venueId = await createVenue(db, { name: 'Comedy Cellar Test' });
  const conversationId = await makeMatch(proposer, recipient);

  const scheduledStart = new Date(db.clock.now().getTime() + 24 * 60 * 60 * 1000);
  const scheduledEnd = new Date(scheduledStart.getTime() + 60 * 60 * 1000);
  const proposal = await dateProposalService.proposeDate(makeCtx(db, userActor(proposer), { payments: processor }), {
    conversationId,
    venueId,
    scheduledStart,
    scheduledEnd,
  });

  await dateProposalService.cancelDateProposal(makeCtx(db, userActor(proposer), { payments: processor }), proposal.id);

  const timeline = await timelineService.getConversationTimeline(makeCtx(db, userActor(recipient)), conversationId);
  const canceled = timeline.items.find((e) => e.kind === 'date_canceled');
  assert.ok(canceled && canceled.kind !== 'message' && canceled.dateProposalId === proposal.id);
});

test('a recipient auth failure produces a date_payment_failed event, derived from the ledger', async () => {
  const proposer = await createUserWithProfile(db, { displayName: 'Quinn' });
  const recipient = await createUserWithProfile(db, { displayName: 'Ryan' });
  const processor = new FakeProcessor();
  await addPaymentMethod(db, proposer, 'tok_ok_pf_proposer', processor);
  await addPaymentMethod(db, recipient, 'tok_fail_authorize_pf_recipient', processor);
  const venueId = await createVenue(db, { name: 'Live Music Hall Test' });
  const conversationId = await makeMatch(proposer, recipient);

  const scheduledStart = new Date(db.clock.now().getTime() + 24 * 60 * 60 * 1000);
  const scheduledEnd = new Date(scheduledStart.getTime() + 60 * 60 * 1000);
  const proposal = await dateProposalService.proposeDate(makeCtx(db, userActor(proposer), { payments: processor }), {
    conversationId,
    venueId,
    scheduledStart,
    scheduledEnd,
  });
  assert.equal(proposal.status, 'pending_acceptance');

  const failed = await dateProposalService.acceptDateProposal(makeCtx(db, userActor(recipient), { payments: processor }), proposal.id);
  assert.equal(failed.status, 'payment_failed');

  const timeline = await timelineService.getConversationTimeline(makeCtx(db, userActor(proposer)), conversationId);
  const paymentFailed = timeline.items.find((e) => e.kind === 'date_payment_failed');
  assert.ok(paymentFailed, 'expected a date_payment_failed event derived from the payment_ledger');
  assert.ok(paymentFailed && paymentFailed.kind !== 'message' && paymentFailed.dateProposalId === proposal.id);
  assert.ok(paymentFailed && paymentFailed.kind !== 'message' && paymentFailed.status === 'payment_failed');
  // Both sides see it (consistency requirement).
  const recipientTimeline = await timelineService.getConversationTimeline(makeCtx(db, userActor(recipient)), conversationId);
  assert.ok(recipientTimeline.items.some((e) => e.kind === 'date_payment_failed'));
});

// =====================================================================
// Declining leaves the chat intact — verify and lock it down.
// =====================================================================

test('declining a date proposal leaves the conversation active, messageable, and produces a date_declined event', async () => {
  const proposer = await createUserWithProfile(db, { displayName: 'Sara' });
  const recipient = await createUserWithProfile(db, { displayName: 'Theo' });
  const processor = new FakeProcessor();
  await addPaymentMethod(db, proposer, 'tok_ok_decline', processor);
  const venueId = await createVenue(db, { name: 'Food Market Test' });
  const conversationId = await makeMatch(proposer, recipient);

  const scheduledStart = new Date(db.clock.now().getTime() + 24 * 60 * 60 * 1000);
  const scheduledEnd = new Date(scheduledStart.getTime() + 60 * 60 * 1000);
  const proposal = await dateProposalService.proposeDate(makeCtx(db, userActor(proposer), { payments: processor }), {
    conversationId,
    venueId,
    scheduledStart,
    scheduledEnd,
  });

  const declined = await dateProposalService.declineDateProposal(makeCtx(db, userActor(recipient)), proposal.id);
  assert.equal(declined.status, 'declined');

  // The conversation itself: still active, not archived/degraded.
  const conversation = await conversationService.getConversation(makeCtx(db, userActor(proposer)), conversationId);
  assert.equal(conversation.status, 'active');

  // Messages are still readable and sendable by both parties.
  await messageService.sendMessage(makeCtx(db, userActor(proposer)), conversationId, 'no worries, maybe another time?');
  const afterDeclineMessages = await messageService.listMessages(makeCtx(db, userActor(recipient)), conversationId, {});
  assert.ok(afterDeclineMessages.items.some((m) => m.body === 'no worries, maybe another time?'));

  // A different date can be proposed afterward.
  const secondStart = new Date(scheduledStart.getTime() + 48 * 60 * 60 * 1000);
  const secondEnd = new Date(secondStart.getTime() + 60 * 60 * 1000);
  const secondProposal = await dateProposalService.proposeDate(makeCtx(db, userActor(proposer), { payments: processor }), {
    conversationId,
    venueId,
    scheduledStart: secondStart,
    scheduledEnd: secondEnd,
  });
  assert.equal(secondProposal.status, 'pending_acceptance');

  // Timeline shows the decline event, and the conversation is still whole.
  const timeline = await timelineService.getConversationTimeline(makeCtx(db, userActor(recipient)), conversationId);
  const declinedEvent = timeline.items.find((e) => e.kind === 'date_declined' && e.id === proposal.id);
  assert.ok(declinedEvent);
  const secondProposedEvent = timeline.items.find((e) => e.kind === 'date_proposed' && e.id === secondProposal.id);
  assert.ok(secondProposedEvent);
});

test('an expired proposal also leaves the conversation active and re-proposable', async () => {
  const proposer = await createUserWithProfile(db, { displayName: 'Uma' });
  const recipient = await createUserWithProfile(db, { displayName: 'Victor' });
  const processor = new FakeProcessor();
  await addPaymentMethod(db, proposer, 'tok_ok_expiry_convo', processor);
  const venueId = await createVenue(db, { name: 'Class Activity Test' });
  const conversationId = await makeMatch(proposer, recipient);

  const scheduledStart = new Date(db.clock.now().getTime() + 60 * 24 * 60 * 60 * 1000);
  const scheduledEnd = new Date(scheduledStart.getTime() + 60 * 60 * 1000);
  await dateProposalService.proposeDate(makeCtx(db, userActor(proposer), { payments: processor }), {
    conversationId,
    venueId,
    scheduledStart,
    scheduledEnd,
  });

  db.clock.advanceHours(200);
  await dateProposalService.expireDuePendingProposals(makeCtx(db, systemActor('expiry-test-2')));

  const conversation = await conversationService.getConversation(makeCtx(db, userActor(recipient)), conversationId);
  assert.equal(conversation.status, 'active');

  const again = await dateProposalService.proposeDate(makeCtx(db, userActor(proposer), { payments: processor }), {
    conversationId,
    venueId,
    scheduledStart: new Date(scheduledStart.getTime() + 24 * 60 * 60 * 1000),
    scheduledEnd: new Date(scheduledEnd.getTime() + 24 * 60 * 60 * 1000),
  });
  assert.equal(again.status, 'pending_acceptance');
});

test('a canceled-before-acceptance proposal also leaves the conversation active and re-proposable', async () => {
  const proposer = await createUserWithProfile(db, { displayName: 'Wendy' });
  const recipient = await createUserWithProfile(db, { displayName: 'Xavier' });
  const processor = new FakeProcessor();
  await addPaymentMethod(db, proposer, 'tok_ok_cancel_convo', processor);
  const venueId = await createVenue(db, { name: 'Walk Test Park' });
  const conversationId = await makeMatch(proposer, recipient);

  const scheduledStart = new Date(db.clock.now().getTime() + 24 * 60 * 60 * 1000);
  const scheduledEnd = new Date(scheduledStart.getTime() + 60 * 60 * 1000);
  const proposal = await dateProposalService.proposeDate(makeCtx(db, userActor(proposer), { payments: processor }), {
    conversationId,
    venueId,
    scheduledStart,
    scheduledEnd,
  });
  await dateProposalService.cancelDateProposal(makeCtx(db, userActor(proposer), { payments: processor }), proposal.id);

  const conversation = await conversationService.getConversation(makeCtx(db, userActor(proposer)), conversationId);
  assert.equal(conversation.status, 'active');

  const again = await dateProposalService.proposeDate(makeCtx(db, userActor(proposer), { payments: processor }), {
    conversationId,
    venueId,
    scheduledStart: new Date(scheduledStart.getTime() + 24 * 60 * 60 * 1000),
    scheduledEnd: new Date(scheduledEnd.getTime() + 24 * 60 * 60 * 1000),
  });
  assert.equal(again.status, 'pending_acceptance');
});

// =====================================================================
// Timestamps: ISO-8601 UTC, and pagination.
// =====================================================================

test('every event timestamp is ISO-8601 UTC, and pagination covers every event exactly once', async () => {
  const a = await createUserWithProfile(db, { displayName: 'Yara' });
  const b = await createUserWithProfile(db, { displayName: 'Zack' });
  const conversationId = await makeMatch(a, b);

  for (let i = 0; i < 7; i++) {
    await messageService.sendMessage(makeCtx(db, userActor(i % 2 === 0 ? a : b)), conversationId, `message ${i}`);
    db.clock.advanceMs(500);
  }

  const iso8601Utc = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/;

  const seen: string[] = [];
  let cursor: string | null | undefined;
  do {
    const page = await timelineService.getConversationTimeline(makeCtx(db, userActor(a)), conversationId, { cursor: cursor ?? undefined, limit: 3 });
    for (const e of page.items) {
      assert.match(e.occurredAt, iso8601Utc, `occurredAt "${e.occurredAt}" is not ISO-8601 UTC`);
      seen.push(e.id + ':' + e.kind);
    }
    cursor = page.nextCursor;
  } while (cursor);

  assert.equal(seen.length, 7);
  assert.equal(new Set(seen).size, 7);
});

// =====================================================================
// Authorization: only a participant may read a timeline.
// =====================================================================

test('a non-participant gets 404, and a venue-staff/admin token gets 403', async () => {
  const a = await createUserWithProfile(db, { displayName: 'Aaron' });
  const b = await createUserWithProfile(db, { displayName: 'Bella' });
  const outsider = await createUserWithProfile(db, { displayName: 'Outsider Two' });
  const conversationId = await makeMatch(a, b);

  await assert.rejects(() => timelineService.getConversationTimeline(makeCtx(db, userActor(outsider)), conversationId), NotFoundError);

  await assert.rejects(
    () => timelineService.getConversationTimeline(makeCtx(db, venueStaffActor('staff-1', 'venue-1')), conversationId),
    ForbiddenError,
  );
  await assert.rejects(() => timelineService.getConversationTimeline(makeCtx(db, adminActor()), conversationId), ForbiddenError);
});
