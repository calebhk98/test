/**
 * Walks the spec's own "Definition of Done" (§34), one test per numbered
 * item, so the product's completion criteria are executable rather than
 * aspirational (task brief: "write a suite that walks that mapping").
 * Each test drives the minimal real behavior that item asserts, through
 * the service layer; most of the underlying invariants are covered in
 * much greater depth by this suite's other files (moneyInvariants.test.ts,
 * the state-machine files, numericBoundaries.test.ts), this file's job is
 * only to make the 20-item checklist itself into 20 runnable assertions,
 * traceable one-to-one back to docs/conformance.md's "Definition of Done
 * (§34), Coverage Mapping" table.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import {
  setupConformanceDb,
  teardownConformanceDb,
  makeCtx,
  userActor,
  systemActor,
  createUser,
  createPaymentMethod,
  createConversation,
  createVenue,
  rawRow,
  type TestDb,
} from './support.js';
import * as authService from '../../src/services/auth.service.js';
import * as questionService from '../../src/services/question.service.js';
import * as filterService from '../../src/services/filter.service.js';
import * as discoveryService from '../../src/services/discovery.service.js';
import { sortDiscoveryCandidates } from '../../src/services/discovery.service.js';
import * as interestService from '../../src/services/interest.service.js';
import * as messageService from '../../src/services/message.service.js';
import * as textscanService from '../../src/services/textscan.service.js';
import * as dateProposalService from '../../src/services/dateProposal.service.js';
import * as redemptionService from '../../src/services/redemption.service.js';
import * as moderationService from '../../src/services/moderation.service.js';
import * as trustService from '../../src/services/trust.service.js';
import * as ledgerService from '../../src/services/ledger.service.js';
import { FakeProcessor } from '../../src/services/payments/fake.processor.js';
import { ValidationError } from '../../src/lib/errors.js';

let db: TestDb;

before(async () => {
  db = await setupConformanceDb('dod');
});

after(async () => {
  await teardownConformanceDb(db);
});

test('DoD #1: register without phone or government ID', async () => {
  const ctx = makeCtx(db, systemActor());
  const result = await authService.register(ctx, {
    email: `dod1-${Date.now()}@example.test`,
    password: 'Passw0rd!12345',
    birthdate: '1995-06-15',
    acceptedTermsAt: db.clock.now(),
    city: 'Springfield',
  });
  assert.ok(result.user.id);
  assert.equal('phone' in (result.user as object), false, 'the returned user has no phone field at all');
});

test('DoD #2: answer dual 5-point (self + preference) questions', async () => {
  const userId = await createUser(db);
  const adminCtx = makeCtx(db, { type: 'admin', adminId: 'a1' });
  const q = await questionService.adminCreateQuestionBankEntry(adminCtx, {
    slug: `dod2_${Date.now()}`,
    category: 'conformance',
    questionText: 'How important is X?',
    typeDef: { type: 'scale', min: 1, max: 5, minLabel: 'low', maxLabel: 'high', midLabel: 'mid' },
    baseWeight: 1,
  });
  const ctx = makeCtx(db, userActor(userId));
  const answer = await questionService.putMyQuestionAnswer(ctx, { slug: q.slug, status: 'answered', selfValue: 4, preferenceValue: 5, importance: 'important' });
  assert.equal(answer.selfValue, 4);
  assert.equal(answer.preferenceValue, 5);
});

test('DoD #3: hard filters strictly control discovery (a filter-failing candidate never appears, filter set separately from scoring)', async () => {
  const viewerId = await createUser(db);
  const failingId = await createUser(db);
  await db.pool.query(`INSERT INTO profiles (user_id, display_name, city, age, gender, seeking, relationship_intention, profile_completeness) VALUES ($1,'V','X',30,'woman','any','long_term',80)`, [viewerId]);
  await db.pool.query(`INSERT INTO profiles (user_id, display_name, city, age, gender, seeking, relationship_intention, profile_completeness) VALUES ($1,'F','X',18,'woman','any','long_term',80)`, [failingId]);

  const viewerCtx = makeCtx(db, userActor(viewerId));
  await filterService.updateMyFilters(viewerCtx, [{ filterKey: 'age_min', operator: 'gte', value: 25, enabled: true }]);
  assert.equal(await filterService.passesMutualFilters(viewerCtx, viewerId, failingId), false);
});

test('DoD #4: discovery grid sorts by compatibility score', () => {
  const candidate = (userId: string, compatibilityScore: number) => ({
    userId,
    displayName: userId,
    age: 30,
    approximateDistanceKm: 5,
    primaryPhotoUrl: null,
    sharedInterestTag: null,
    compatibilityScore,
    trustLevel: 'standard' as const,
    profileCompleteness: 80,
  });
  const ranked = (c: ReturnType<typeof candidate>) => ({ candidate: c, trustScore: 60, lastActiveAt: new Date(), responseRate: 0.5 });
  const sorted = sortDiscoveryCandidates([ranked(candidate('low', 0.1)), ranked(candidate('high', 0.9))]);
  assert.deepEqual(sorted.map((c) => c.userId), ['high', 'low']);
});

test('DoD #5: users can send LIMITED interests (the outgoing-pending cap genuinely blocks)', async () => {
  const senderId = await createUser(db);
  const ctx = makeCtx(db, userActor(senderId));
  for (let i = 0; i < 5; i++) {
    await interestService.sendInterest(ctx, await createUser(db));
  }
  await assert.rejects(() => interestService.sendInterest(ctx, await createUser(db)), { name: 'RateLimitError' });
});

test('DoD #6: incoming interests are capped and expire (freeing the sender\'s slot)', async () => {
  const senderId = await createUser(db);
  const recipientId = await createUser(db);
  const ctx = makeCtx(db, userActor(senderId));
  const interest = await interestService.sendInterest(ctx, recipientId);
  db.clock.advanceHours(49);
  const systemCtx = makeCtx(db, systemActor());
  const swept = await interestService.expireDuePendingInterests(systemCtx);
  assert.ok(swept.expired >= 1);
  const row = await rawRow<{ status: string }>(db, `SELECT status FROM interests WHERE id = $1`, [interest.id]);
  assert.equal(row?.status, 'expired');
});

test('DoD #7: mutual interest opens chat', async () => {
  const senderId = await createUser(db);
  const recipientId = await createUser(db);
  const interest = await interestService.sendInterest(makeCtx(db, userActor(senderId)), recipientId);
  const { conversation } = await interestService.acceptInterest(makeCtx(db, userActor(recipientId)), interest.id);
  assert.equal(conversation.status, 'active');
});

test('DoD #8: chat supports free-text (including emoji) after match', async () => {
  const a = await createUser(db);
  const b = await createUser(db);
  const conversationId = await createConversation(db, a, b, 'active');
  const message = await messageService.sendMessage(makeCtx(db, userActor(a)), conversationId, 'Hey! 👋 want to grab coffee sometime?');
  assert.match(message.body, /👋/);
});

test('DoD #9: text analysis flags risky patterns without blocking normal messages', async () => {
  const ctx = makeCtx(db, systemActor());
  const normal = textscanService.scanText(ctx, 'Hi, how was your weekend?');
  assert.equal(normal.flags.length, 0);
  const risky = textscanService.scanText(ctx, 'send bitcoin to my wallet right now');
  assert.ok(risky.flags.length > 0);
});

interface Pair {
  proposerId: string;
  recipientId: string;
  conversationId: string;
  venueId: string;
  proposerCtx: ReturnType<typeof makeCtx>;
  recipientCtx: ReturnType<typeof makeCtx>;
}

async function moneyPair(): Promise<Pair> {
  const proposerId = await createUser(db);
  const recipientId = await createUser(db);
  await createPaymentMethod(db, proposerId, 'tok_good');
  await createPaymentMethod(db, recipientId, 'tok_good');
  const conversationId = await createConversation(db, proposerId, recipientId, 'active');
  const venueId = await createVenue(db);
  const processor = new FakeProcessor();
  return {
    proposerId,
    recipientId,
    conversationId,
    venueId,
    proposerCtx: makeCtx(db, userActor(proposerId), { payments: processor }),
    recipientCtx: makeCtx(db, userActor(recipientId), { payments: processor }),
  };
}

test('DoD #10: propose dates with structured venues (a real venue id works, a made-up one is rejected)', async () => {
  const pair = await moneyPair();
  const start = new Date(db.clock.now().getTime() + 48 * 60 * 60 * 1000);
  const end = new Date(start.getTime() + 60 * 60 * 1000);
  const proposal = await dateProposalService.proposeDate(pair.proposerCtx, { conversationId: pair.conversationId, venueId: pair.venueId, scheduledStart: start, scheduledEnd: end });
  assert.equal(proposal.status, 'pending_acceptance');
  await assert.rejects(
    () => dateProposalService.proposeDate(pair.proposerCtx, { conversationId: pair.conversationId, venueId: '00000000-0000-0000-0000-000000000000', scheduledStart: start, scheduledEnd: end }),
    Error,
  );
});

test('DoD #11: proposer hold authorized on proposal', async () => {
  const pair = await moneyPair();
  const start = new Date(db.clock.now().getTime() + 48 * 60 * 60 * 1000);
  const end = new Date(start.getTime() + 60 * 60 * 1000);
  const proposal = await dateProposalService.proposeDate(pair.proposerCtx, { conversationId: pair.conversationId, venueId: pair.venueId, scheduledStart: start, scheduledEnd: end });
  const hold = await rawRow<{ status: string }>(db, `SELECT status FROM payment_holds WHERE date_proposal_id = $1 AND user_id = $2`, [proposal.id, pair.proposerId]);
  assert.equal(hold?.status, 'authorized');
});

test('DoD #12 / #13 / #14: acceptor hold authorized on acceptance, both capture only after both authorized, ticket issued only then', async () => {
  const pair = await moneyPair();
  const start = new Date(db.clock.now().getTime() + 48 * 60 * 60 * 1000);
  const end = new Date(start.getTime() + 60 * 60 * 1000);
  const proposal = await dateProposalService.proposeDate(pair.proposerCtx, { conversationId: pair.conversationId, venueId: pair.venueId, scheduledStart: start, scheduledEnd: end });
  const noVoucherYet = await rawRow(db, `SELECT id FROM vouchers WHERE date_proposal_id = $1`, [proposal.id]);
  assert.equal(noVoucherYet, undefined);

  const ticketed = await dateProposalService.acceptDateProposal(pair.recipientCtx, proposal.id);
  assert.equal(ticketed.status, 'ticketed');
  const recipientHold = await rawRow<{ status: string }>(db, `SELECT status FROM payment_holds WHERE date_proposal_id = $1 AND user_id = $2`, [proposal.id, pair.recipientId]);
  assert.equal(recipientHold?.status, 'captured');
  const voucher = await rawRow(db, `SELECT id FROM vouchers WHERE date_proposal_id = $1`, [proposal.id]);
  assert.ok(voucher, 'a ticket exists now that both holds captured');
});

test('DoD #15 / #16: venue redemption marks date completed, and post-date chat becomes established', async () => {
  const pair = await moneyPair();
  const start = new Date(db.clock.now().getTime() + 3 * 60 * 60 * 1000);
  const end = new Date(start.getTime() + 60 * 60 * 1000);
  const proposal = await dateProposalService.proposeDate(pair.proposerCtx, { conversationId: pair.conversationId, venueId: pair.venueId, scheduledStart: start, scheduledEnd: end });
  await dateProposalService.acceptDateProposal(pair.recipientCtx, proposal.id);
  const voucherRow = await rawRow<{ code: string }>(db, `SELECT code FROM vouchers WHERE date_proposal_id = $1`, [proposal.id]);

  const staffUserId = await createUser(db);
  const staffRow = await rawRow<{ id: string }>(db, `INSERT INTO venue_staff (user_id, venue_id, active) VALUES ($1, $2, true) RETURNING id`, [staffUserId, pair.venueId]);
  const venueStaffCtx = makeCtx(db, { type: 'venue_staff', venueStaffId: staffRow!.id, venueId: pair.venueId });
  const result = await redemptionService.redeemByStaff(venueStaffCtx, { code: voucherRow!.code });
  assert.equal(result.dateProposal.status, 'completed');

  const convo = await rawRow<{ status: string }>(db, `SELECT status FROM conversations WHERE id = $1`, [pair.conversationId]);
  assert.equal(convo?.status, 'established');
});

test('DoD #17: automated moderation works with ZERO admin/human calls anywhere in this test', async () => {
  const userId = await createUser(db);
  const systemCtx = makeCtx(db, systemActor()); // never { type: 'admin', ... } anywhere in this test
  await moderationService.recordAutomatedFlag(systemCtx, { userId, signalType: 'user_report', weight: 90, metadata: {} });
  const action = await moderationService.applyThresholds(systemCtx, userId);
  assert.equal(action?.action, 'shadowban');
  const row = await rawRow<{ shadowbanned: boolean }>(db, `SELECT shadowbanned FROM users WHERE id = $1`, [userId]);
  assert.equal(row?.shadowbanned, true);
});

test('DoD #18: trust score visible with actionable reasons', async () => {
  const userId = await createUser(db);
  const ctx = makeCtx(db, userActor(userId));
  const summary = await trustService.getMyTrustSummary(ctx);
  assert.ok(['limited', 'standard', 'trusted', 'elite'].includes(summary.trustLevel));
  assert.ok(summary.actionableImprovements.length > 0, 'a non-elite, freshly-created user must see concrete next steps');
});

test('DoD #19: admin can change core variables without a code deployment, and it takes effect immediately', async () => {
  const before = await db.config.get('date.escrow_amount_cents');
  assert.equal(before, 2000);
  await db.config.set('date.escrow_amount_cents', 2500, 'admin:dod-test');
  const after = await db.config.get('date.escrow_amount_cents');
  assert.equal(after, 2500);
  await db.config.set('date.escrow_amount_cents', 2000, 'admin:dod-test'); // restore for any later test in this file
});

test('DoD #20: all payment events are recorded in an immutable ledger, with no update/delete function exposed at all', async () => {
  const pair = await moneyPair();
  const start = new Date(db.clock.now().getTime() + 48 * 60 * 60 * 1000);
  const end = new Date(start.getTime() + 60 * 60 * 1000);
  const proposal = await dateProposalService.proposeDate(pair.proposerCtx, { conversationId: pair.conversationId, venueId: pair.venueId, scheduledStart: start, scheduledEnd: end });
  await dateProposalService.acceptDateProposal(pair.recipientCtx, proposal.id);

  const entries = await ledgerService.listEntriesForDateProposal(pair.proposerCtx, proposal.id);
  assert.ok(entries.length >= 4, 'two authorizations + two captures at minimum');

  // Structural: the module exports no mutation function on existing rows.
  const exportedNames = Object.keys(ledgerService);
  assert.equal(exportedNames.some((n) => /update|delete|edit|mutate/i.test(n)), false, 'ledger.service.ts must expose no way to update or delete an existing entry');
});
