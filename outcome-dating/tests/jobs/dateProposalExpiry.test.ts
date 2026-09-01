/**
 * §25.2 Date Proposal Expiry job — boundary behavior (mirrors C-14.6.1) and
 * idempotent re-run, run through the actual job function.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import {
  setupTestDb,
  teardownTestDb,
  makeCtx,
  userActor,
  createUser,
  createProfile,
  createConversation,
  createVenue,
  createPaymentMethod,
} from './testHarness.js';
import type { TestDb } from './testHarness.js';
import { runDateProposalExpiryJob } from '../../src/jobs/dateProposalExpiry.job.js';
import { proposeDate } from '../../src/services/dateProposal.service.js';
import type { Ctx } from '../../src/lib/ctx.js';

let db: TestDb;

before(async () => {
  db = await setupTestDb('date_proposal_expiry');
});

after(async () => {
  await teardownTestDb(db);
});

async function makePendingProposal(ctx: Ctx): Promise<{ dateProposalId: string; proposerId: string }> {
  const proposerId = await createUser(db);
  const recipientId = await createUser(db);
  await createProfile(db, proposerId);
  await createProfile(db, recipientId);
  await createPaymentMethod(db, proposerId);
  const conversationId = await createConversation(db, proposerId, recipientId);
  const venueId = await createVenue(db);

  const proposerCtx = { ...ctx, actor: userActor(proposerId) };
  const start = new Date(ctx.clock.now().getTime() + 7 * 24 * 60 * 60 * 1000);
  const end = new Date(start.getTime() + 60 * 60 * 1000);
  const proposal = await proposeDate(proposerCtx, { conversationId, venueId, scheduledStart: start, scheduledEnd: end });
  assert.equal(proposal.status, 'pending_acceptance', 'fixture setup: proposal must have authorized on creation');
  return { dateProposalId: proposal.id, proposerId };
}

async function backdateCreatedAt(dateProposalId: string, hoursAgo: number): Promise<void> {
  await db.pool.query(`UPDATE date_proposals SET created_at = created_at - ($2 || ' hours')::interval WHERE id = $1`, [
    dateProposalId,
    String(hoursAgo),
  ]);
}

test('boundary: just under 48h is untouched, at/past 48h expires and releases the proposer hold', async () => {
  const ctx = makeCtx(db);

  const notDue = await makePendingProposal(ctx);
  await backdateCreatedAt(notDue.dateProposalId, 47.999); // 47h59m56s ago

  const due = await makePendingProposal(ctx);
  await backdateCreatedAt(due.dateProposalId, 48); // exactly at the cutoff

  const result = await runDateProposalExpiryJob(ctx);
  assert.equal(result.expired, 1);

  const { rows } = await db.pool.query<{ id: string; status: string }>(
    `SELECT id, status FROM date_proposals WHERE id = ANY($1::uuid[])`,
    [[notDue.dateProposalId, due.dateProposalId]],
  );
  const byId = new Map(rows.map((r) => [r.id, r.status]));
  assert.equal(byId.get(notDue.dateProposalId), 'pending_acceptance');
  assert.equal(byId.get(due.dateProposalId), 'expired');

  const { rows: holdRows } = await db.pool.query<{ status: string }>(
    `SELECT status FROM payment_holds WHERE date_proposal_id = $1 AND user_id = $2`,
    [due.dateProposalId, due.proposerId],
  );
  assert.equal(holdRows[0]!.status, 'released');
});

test('idempotent re-run: running twice does not double-release or error', async () => {
  const ctx = makeCtx(db);
  const { dateProposalId, proposerId } = await makePendingProposal(ctx);
  await backdateCreatedAt(dateProposalId, 49);

  const first = await runDateProposalExpiryJob(ctx);
  assert.equal(first.expired, 1);
  const second = await runDateProposalExpiryJob(ctx);
  assert.equal(second.expired, 0);

  const { rows } = await db.pool.query<{ status: string }>(
    `SELECT status FROM payment_holds WHERE date_proposal_id = $1 AND user_id = $2`,
    [dateProposalId, proposerId],
  );
  assert.equal(rows[0]!.status, 'released');
});
