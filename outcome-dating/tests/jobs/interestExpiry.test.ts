/**
 * §25.1 Interest Expiry job, boundary behavior and idempotent re-run.
 * Mirrors conformance C-25.1.1 / C-11.4.5-6, run through the actual job
 * function (not the inline service call).
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestDb, teardownTestDb, makeCtx, createUser } from './testHarness.js';
import type { TestDb } from './testHarness.js';
import { runInterestExpiryJob } from '../../src/jobs/interestExpiry.job.js';

let db: TestDb;

before(async () => {
  db = await setupTestDb('interest_expiry');
});

after(async () => {
  await teardownTestDb(db);
});

async function insertInterest(senderId: string, recipientId: string, expiresAt: Date): Promise<string> {
  const { rows } = await db.pool.query<{ id: string }>(
    `INSERT INTO interests (sender_id, recipient_id, status, policy_snapshot, expires_at)
     VALUES ($1, $2, 'pending', '{"interest.expiry_hours":48,"interest.outgoing_pending_limit":5,"interest.incoming_pending_limit":10}'::jsonb, $3)
     RETURNING id`,
    [senderId, recipientId, expiresAt],
  );
  return rows[0]!.id;
}

test('boundary: not yet expired is untouched, past-expiry is expired, and the sender outgoing slot frees', async () => {
  const sender = await createUser(db);
  const recipientDue = await createUser(db);
  const recipientNotDue = await createUser(db);
  const ctx = makeCtx(db);
  const now = ctx.clock.now();

  const dueId = await insertInterest(sender, recipientDue, now); // exactly at now -> due
  const notDueId = await insertInterest(sender, recipientNotDue, new Date(now.getTime() + 1000)); // 1s in the future -> not due

  const result = await runInterestExpiryJob(ctx);
  assert.equal(result.expired, 1);

  const { rows } = await db.pool.query<{ id: string; status: string }>(`SELECT id, status FROM interests ORDER BY id`);
  const byId = new Map(rows.map((r) => [r.id, r.status]));
  assert.equal(byId.get(dueId), 'expired');
  assert.equal(byId.get(notDueId), 'pending');

  // Outgoing-slot-freed is structural: only pending interests count toward
  // the sender's cap, and the expired row no longer does.
  const { rows: pendingCount } = await db.pool.query<{ count: string }>(
    `SELECT count(*)::text AS count FROM interests WHERE sender_id = $1 AND status = 'pending'`,
    [sender],
  );
  assert.equal(pendingCount[0]!.count, '1');
});

test('idempotent re-run: running twice produces no duplicate effects', async () => {
  const sender = await createUser(db);
  const recipient = await createUser(db);
  const ctx = makeCtx(db);
  const interestId = await insertInterest(sender, recipient, ctx.clock.now());

  const first = await runInterestExpiryJob(ctx);
  assert.equal(first.expired, 1);
  const second = await runInterestExpiryJob(ctx);
  assert.equal(second.expired, 0, 'a second run must not re-expire the same row');

  const { rows } = await db.pool.query<{ status: string; expired_at: Date }>(`SELECT status, expired_at FROM interests WHERE id = $1`, [interestId]);
  assert.equal(rows[0]!.status, 'expired');
  assert.ok(rows[0]!.expired_at, 'expired_at is stamped exactly once');
});
