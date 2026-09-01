/**
 * `notification_delivery` job — thin wrapper around
 * `notifications/delivery.ts#runNotificationDeliveryWorker`, resolving its
 * push/email/SMS senders the same environment-driven way every other
 * external-integration port is selected (`src/config/adapters.ts`). This
 * was the single most damaging orphaned job in the review: without it,
 * nothing in `notification_outbox` was ever actually delivered, no matter
 * how correctly the rest of the pipeline enqueued it. Full gating
 * behavior (preferences, quiet hours, retry/backoff) is covered by
 * `tests/unit/notificationDelivery.test.ts`; this file proves the job
 * itself is reachable, runs, and is idempotent (a delivered row is never
 * redelivered on the next run).
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestDb, teardownTestDb, makeCtx, createUser } from './testHarness.js';
import type { TestDb } from './testHarness.js';
import { runNotificationDeliveryJob } from '../../src/jobs/notificationDelivery.job.js';

let db: TestDb;

before(async () => {
  db = await setupTestDb('notification_delivery');
});

after(async () => {
  await teardownTestDb(db);
});

async function insertQueuedEmailRow(userId: string): Promise<string> {
  const now = db.clock.now();
  const { rows } = await db.pool.query<{ id: string }>(
    `INSERT INTO notification_outbox
       (user_id, event_type, category, channel, template_key, payload, coalescing_key, coalesced_count, status, attempt_count, next_attempt_at, created_at, updated_at)
     VALUES ($1, 'trust_level_changed', 'account_activity', 'email', 'trust_level_changed_v1', '{}'::jsonb, $2, 1, 'queued', 0, $3, $3, $3)
     RETURNING id`,
    [userId, `test:${userId}`, now],
  );
  return rows[0]!.id;
}

test('runNotificationDeliveryJob delivers a due, queued email row via the environment-selected (fake, in test) sender', async () => {
  const ctx = makeCtx(db);
  const userId = await createUser(db);
  const outboxId = await insertQueuedEmailRow(userId);

  const result = await runNotificationDeliveryJob(ctx);
  assert.equal(result.processed, 1);
  assert.equal(result.sent, 1);

  const { rows } = await db.pool.query<{ status: string; delivered_at: Date | null }>(
    `SELECT status, delivered_at FROM notification_outbox WHERE id = $1`,
    [outboxId],
  );
  assert.equal(rows[0]!.status, 'sent');
  assert.ok(rows[0]!.delivered_at !== null);
});

test('runNotificationDeliveryJob is idempotent: an already-sent row is never redelivered on the next run', async () => {
  const ctx = makeCtx(db);
  const userId = await createUser(db);
  await insertQueuedEmailRow(userId);

  const first = await runNotificationDeliveryJob(ctx);
  assert.equal(first.sent, 1);

  const second = await runNotificationDeliveryJob(ctx);
  assert.equal(second.processed, 0);
  assert.equal(second.sent, 0);
});
