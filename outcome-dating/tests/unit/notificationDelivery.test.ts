import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import pg from 'pg';
import { enqueueNotification } from '../../src/services/notifications/outbox.js';
import { runNotificationDeliveryWorker } from '../../src/services/notifications/delivery.js';
import { registerDeviceToken } from '../../src/services/notifications/devices.js';
import { updateMyNotificationPreference } from '../../src/services/notifications/preferences.js';
import { updateMyContentPreviewSetting } from '../../src/services/notifications/preferences.js';
import { NOTIFICATION_CONFIG } from '../../src/services/notifications/config.js';
import { FakePushSender } from '../../src/services/notifications/adapters/fake.push.js';
import { FakeEmailSender } from '../../src/services/notifications/adapters/fake.email.js';
import type { PushSendParams, PushSendResult, PushSender } from '../../src/services/notifications/ports/push.port.js';
import { ForbiddenError, ValidationError } from '../../src/lib/errors.js';
import { ManualClock } from '../../src/lib/time.js';
import { withTransaction } from '../../src/db/tx.js';
import { withDb } from '../../src/lib/ctx.js';
import { setupTestDatabase, teardownTestDatabase, buildCtx, userActor, insertUser } from '../../src/services/notifications/testSupport.js';

let pool: pg.Pool;

before(async () => {
  pool = await setupTestDatabase('delivery');
});

after(async () => {
  await teardownTestDatabase();
});

// Every test gets its own 2-hour-wide clock "slot", strictly separated from
// every other test's slot. All tests share one Postgres database (and run
// sequentially in this file), so an outbox row a test deliberately leaves
// in a non-terminal state (e.g. `failed_retryable` mid-backoff) is a real
// row another test's `runNotificationDeliveryWorker` call could otherwise
// sweep up if their clocks' absolute due-timestamps happened to overlap.
// 2 hours comfortably exceeds this build's largest window (max retry
// backoff caps at 1h, coalescing caps at 10min), so no test can ever
// observe another test's row as "due".
let testSlot = 0;
function slotClock(): Date {
  testSlot += 1;
  return new Date(Date.UTC(2026, 1, 1, 0, 0, 0, 0) + testSlot * 2 * 60 * 60 * 1000);
}

async function registerToken(userId: string, token: string, clock?: ManualClock): Promise<void> {
  const ctx = buildCtx({ actor: userActor(userId), ...(clock ? { clock } : {}) });
  await registerDeviceToken(ctx, { platform: 'ios', deviceId: `d-${token}`, pushToken: token });
}

// =========================================================================
// The three product-owner-named events, end to end
// =========================================================================

test('a new match (interest accepted) produces exactly one delivered push', async () => {
  const user = await insertUser(pool);
  const clock = new ManualClock(slotClock());
  await registerToken(user, 'tok-match', clock);
  const sysCtx = buildCtx({ actor: { type: 'system', job: 'test' }, clock });

  await enqueueNotification(sysCtx, {
    userId: user,
    eventType: 'interest_accepted',
    dedupKey: `interest_accepted:match-1`,
    payload: { otherUserFirstName: 'Priya' },
  });

  const push = new FakePushSender();
  const email = new FakeEmailSender();
  const result = await runNotificationDeliveryWorker(sysCtx, { push, email });

  assert.equal(result.sent, 1, 'exactly one channel (push) should have delivered');
  assert.equal(push.sent.length, 1);
  assert.equal(email.sent.length, 0, 'email defaults OFF for the match category, push is the primary channel');
});

test('a new message received produces exactly one delivered push', async () => {
  const user = await insertUser(pool);
  const clock = new ManualClock(slotClock());
  await registerToken(user, 'tok-message', clock);
  const sysCtx = buildCtx({ actor: { type: 'system', job: 'test' }, clock });

  await enqueueNotification(sysCtx, {
    userId: user,
    eventType: 'message_received',
    dedupKey: `message_received:msg-1`,
    payload: { senderFirstName: 'Alex', conversationId: 'conv-1' },
  });

  const push = new FakePushSender();
  const email = new FakeEmailSender();

  const before1 = await runNotificationDeliveryWorker(sysCtx, { push, email });
  assert.equal(before1.processed, 0, 'a message notification always waits out the coalescing debounce first');

  clock.advanceMs((NOTIFICATION_CONFIG.message.coalesceDebounceSeconds + 1) * 1000);
  const result = await runNotificationDeliveryWorker(sysCtx, { push, email });

  assert.equal(result.sent, 1);
  assert.equal(push.sent.length, 1);
  assert.equal(push.sent[0]!.data.senderFirstName, 'Alex');
});

test('a date proposal received produces exactly one delivered push', async () => {
  const user = await insertUser(pool);
  const clock = new ManualClock(slotClock());
  await registerToken(user, 'tok-date', clock);
  const sysCtx = buildCtx({ actor: { type: 'system', job: 'test' }, clock });

  await enqueueNotification(sysCtx, {
    userId: user,
    eventType: 'date_proposal_received',
    dedupKey: `date_proposal_received:proposal-1`,
    payload: { venueName: 'Sunset Coffee' },
  });

  const push = new FakePushSender();
  const email = new FakeEmailSender();
  const result = await runNotificationDeliveryWorker(sysCtx, { push, email });

  assert.equal(result.sent, 1);
  assert.equal(push.sent.length, 1);
});

// =========================================================================
// Preferences suppress a channel, enforced in the delivery path only
// =========================================================================

test('preferences suppress a channel, and the gate lives in delivery, not at enqueue time', async () => {
  const user = await insertUser(pool);
  const clock = new ManualClock(slotClock());
  await registerToken(user, 'tok-pref', clock);
  const userCtx = buildCtx({ actor: userActor(user), clock });
  const sysCtx = buildCtx({ actor: { type: 'system', job: 'test' }, clock });

  await updateMyNotificationPreference(userCtx, 'match', { push: false });

  // enqueueNotification takes no "force"/"bypass preference" flag at all,
  // there is nothing for a careless call site to get wrong here.
  const enqueued = await enqueueNotification(sysCtx, {
    userId: user,
    eventType: 'interest_accepted',
    dedupKey: `interest_accepted:pref-test`,
    payload: {},
  });
  assert.equal(enqueued.deduplicated, false);

  const push = new FakePushSender();
  const email = new FakeEmailSender();
  const result = await runNotificationDeliveryWorker(sysCtx, { push, email });

  // Both the push row (explicitly turned off above) and the email row
  // (match's default is email:false regardless) are dropped here, the
  // point under test is that push specifically was never attempted.
  assert.equal(result.droppedPreference, 2);
  assert.equal(push.sent.length, 0, 'push must not be attempted once the user has turned it off for this category');

  const { rows } = await pool.query<{ status: string }>(
    `SELECT status FROM notification_outbox WHERE user_id = $1 AND channel = 'push'`,
    [user],
  );
  assert.equal(rows[0]!.status, 'dropped_preference');
});

// =========================================================================
// Coalescing: a burst collapses into one delivered notification
// =========================================================================

test('coalescing: five messages in a burst produce exactly one push, not five', async () => {
  const user = await insertUser(pool);
  const clock = new ManualClock(slotClock());
  await registerToken(user, 'tok-burst', clock);
  const sysCtx = buildCtx({ actor: { type: 'system', job: 'test' }, clock });

  for (let i = 0; i < 5; i++) {
    await enqueueNotification(sysCtx, {
      userId: user,
      eventType: 'message_received',
      dedupKey: `message_received:burst-${i}`,
      coalescingKey: `message:${user}:conv-burst`,
      payload: { senderFirstName: 'Alex', conversationId: 'conv-burst', messagePreviewText: `msg ${i}` },
    });
  }

  const { rows: outboxRows } = await pool.query<{ coalesced_count: number }>(
    `SELECT coalesced_count FROM notification_outbox WHERE user_id = $1 AND channel = 'push'`,
    [user],
  );
  assert.equal(outboxRows.length, 1, 'five enqueues into the same coalescing group must produce ONE outbox row, not five');
  assert.equal(outboxRows[0]!.coalesced_count, 5);

  const push = new FakePushSender();
  const email = new FakeEmailSender();

  clock.advanceMs((NOTIFICATION_CONFIG.message.coalesceDebounceSeconds + 1) * 1000);
  const result = await runNotificationDeliveryWorker(sysCtx, { push, email });

  assert.equal(result.sent, 1);
  assert.equal(push.sent.length, 1, 'exactly one PushSender.send call for the whole burst');
  assert.equal(push.sent[0]!.data.count, '5');
});

test('coalescing: a steady stream cannot postpone delivery past the hard cap', async () => {
  const user = await insertUser(pool);
  const clock = new ManualClock(slotClock());
  await registerToken(user, 'tok-cap', clock);
  const sysCtx = buildCtx({ actor: { type: 'system', job: 'test' }, clock });

  const stepMs = (NOTIFICATION_CONFIG.message.coalesceDebounceSeconds - 10) * 1000; // always re-debounce just before it would fire
  const steps = Math.ceil((NOTIFICATION_CONFIG.message.coalesceMaxWaitSeconds * 1000) / stepMs) + 2;

  for (let i = 0; i < steps; i++) {
    await enqueueNotification(sysCtx, {
      userId: user,
      eventType: 'message_received',
      dedupKey: `message_received:steady-${i}`,
      coalescingKey: `message:${user}:conv-steady`,
      payload: { senderFirstName: 'Jordan', conversationId: 'conv-steady' },
    });
    clock.advanceMs(stepMs);
  }

  const push = new FakePushSender();
  const email = new FakeEmailSender();
  const result = await runNotificationDeliveryWorker(sysCtx, { push, email });

  assert.equal(result.sent, 1, 'the batch must have fired on its own despite messages still arriving, once maxWait elapsed');
});

// =========================================================================
// Deduplication survives a retried domain operation
// =========================================================================

test('deduplication: enqueueing the same dedupKey twice (a retried domain operation) never double-notifies', async () => {
  const user = await insertUser(pool);
  const clock = new ManualClock(slotClock());
  await registerToken(user, 'tok-dedup', clock);
  const sysCtx = buildCtx({ actor: { type: 'system', job: 'test' }, clock });

  const dedupKey = `interest_accepted:retry-scenario`;
  const first = await enqueueNotification(sysCtx, { userId: user, eventType: 'interest_accepted', dedupKey, payload: {} });
  assert.equal(first.deduplicated, false);

  // Simulate the raising service's transaction being retried (e.g. after a
  // timeout the client never saw the first commit) and calling enqueueNotification again.
  const second = await enqueueNotification(sysCtx, { userId: user, eventType: 'interest_accepted', dedupKey, payload: {} });
  assert.equal(second.deduplicated, true);
  assert.deepEqual(second.outboxIds, []);

  const { rows } = await pool.query(`SELECT id FROM notification_outbox WHERE user_id = $1 AND channel = 'push'`, [user]);
  assert.equal(rows.length, 1, 'still exactly one outbox row after the "retried" call');

  const push = new FakePushSender();
  const email = new FakeEmailSender();
  const result = await runNotificationDeliveryWorker(sysCtx, { push, email });
  assert.equal(push.sent.length, 1, 'still exactly one push, not two');
  assert.equal(result.sent, 1);

  // And enqueueing the SAME key again after it has already been delivered
  // must still be a no-op forever, not just until the first delivery.
  const third = await enqueueNotification(sysCtx, { userId: user, eventType: 'interest_accepted', dedupKey, payload: {} });
  assert.equal(third.deduplicated, true);
});

// =========================================================================
// Content previews: OFF by default means no message body leaves the server
// =========================================================================

test('content preview OFF (default): no message body/preview text is ever sent to the push provider', async () => {
  const user = await insertUser(pool);
  const clock = new ManualClock(slotClock());
  await registerToken(user, 'tok-preview-off', clock);
  const sysCtx = buildCtx({ actor: { type: 'system', job: 'test' }, clock });

  await enqueueNotification(sysCtx, {
    userId: user,
    eventType: 'message_received',
    dedupKey: `message_received:preview-off`,
    payload: { senderFirstName: 'Sam', conversationId: 'conv-preview', messagePreviewText: 'Meet me at the place we talked about, bring cash' },
  });

  const push = new FakePushSender();
  const email = new FakeEmailSender();
  clock.advanceMs((NOTIFICATION_CONFIG.message.coalesceDebounceSeconds + 1) * 1000);
  await runNotificationDeliveryWorker(sysCtx, { push, email });

  assert.equal(push.sent.length, 1);
  assert.equal(push.sent[0]!.data.previewText, undefined, 'no previewText key at all when the user has not opted in');
  assert.equal(push.sent[0]!.templateKey, 'message_received_generic_v1');
  const serialized = JSON.stringify(push.sent[0]!.data);
  assert.ok(!serialized.includes('cash'), 'raw message content must never reach the push provider when previews are off');
});

test('content preview ON (explicit opt-in): a single coalesced message may include truncated preview text', async () => {
  const user = await insertUser(pool);
  const clock = new ManualClock(slotClock());
  await registerToken(user, 'tok-preview-on', clock);
  const userCtx = buildCtx({ actor: userActor(user), clock });
  const sysCtx = buildCtx({ actor: { type: 'system', job: 'test' }, clock });

  await updateMyContentPreviewSetting(userCtx, true);

  await enqueueNotification(sysCtx, {
    userId: user,
    eventType: 'message_received',
    dedupKey: `message_received:preview-on`,
    payload: { senderFirstName: 'Sam', conversationId: 'conv-preview-2', messagePreviewText: 'Hey, are you free Friday evening?' },
  });

  const push = new FakePushSender();
  const email = new FakeEmailSender();
  clock.advanceMs((NOTIFICATION_CONFIG.message.coalesceDebounceSeconds + 1) * 1000);
  await runNotificationDeliveryWorker(sysCtx, { push, email });

  assert.equal(push.sent[0]!.templateKey, 'message_received_preview_v1');
  assert.equal(push.sent[0]!.data.previewText, 'Hey, are you free Friday evening?');
});

test('content preview: a coalesced batch of more than one message never shows a preview, even when opted in', async () => {
  const user = await insertUser(pool);
  const clock = new ManualClock(slotClock());
  await registerToken(user, 'tok-preview-plural', clock);
  const userCtx = buildCtx({ actor: userActor(user), clock });
  const sysCtx = buildCtx({ actor: { type: 'system', job: 'test' }, clock });
  await updateMyContentPreviewSetting(userCtx, true);

  for (let i = 0; i < 2; i++) {
    await enqueueNotification(sysCtx, {
      userId: user,
      eventType: 'message_received',
      dedupKey: `message_received:plural-${i}`,
      coalescingKey: `message:${user}:conv-plural`,
      payload: { senderFirstName: 'Sam', conversationId: 'conv-plural', messagePreviewText: `text ${i}` },
    });
  }

  const push = new FakePushSender();
  const email = new FakeEmailSender();
  clock.advanceMs((NOTIFICATION_CONFIG.message.coalesceDebounceSeconds + 1) * 1000);
  await runNotificationDeliveryWorker(sysCtx, { push, email });

  assert.equal(push.sent[0]!.templateKey, 'message_received_plural_generic_v1');
  assert.equal(push.sent[0]!.data.previewText, undefined);
});

// =========================================================================
// A push-sender outage never fails or rolls back the domain transaction
// =========================================================================

test('a push-sender outage does not fail or roll back the domain transaction that raised the notification', async () => {
  const user = await insertUser(pool);
  const clock = new ManualClock(slotClock());
  await registerToken(user, 'tok-outage', clock);
  const sysCtx = buildCtx({ actor: { type: 'system', job: 'test' }, clock });

  const marker = new Date('2026-02-01T13:00:00.000Z');
  await withTransaction(async (db) => {
    const txCtx = withDb(sysCtx, db);
    // Stand-in for "the raising service's own domain write", sharing the
    // same transaction the way interest.acceptInterest etc. do per
    // INTERFACES.md's withTransaction/withDb pattern.
    const updated = await db.query('UPDATE users SET last_active_at = $2 WHERE id = $1 RETURNING id', [user, marker]);
    assert.equal(updated.rows.length, 1);
    await enqueueNotification(txCtx, {
      userId: user,
      eventType: 'interest_accepted',
      dedupKey: `interest_accepted:outage-test`,
      payload: {},
    });
  });

  const { rows } = await pool.query<{ last_active_at: Date }>('SELECT last_active_at FROM users WHERE id = $1', [user]);
  assert.equal(rows[0]!.last_active_at.toISOString(), marker.toISOString(), 'the domain write committed regardless of delivery outcome');

  // Now simulate a total provider outage: PushSender.send THROWS (the port's
  // documented "true infra failure" signal) rather than returning a result.
  class ThrowingPushSender implements PushSender {
    readonly name = 'throwing';
    calls = 0;
    async send(_params: PushSendParams): Promise<PushSendResult> {
      this.calls += 1;
      throw new Error('simulated total provider outage');
    }
  }
  const outage = new ThrowingPushSender();
  const email = new FakeEmailSender();

  const result = await runNotificationDeliveryWorker(sysCtx, { push: outage, email });
  // Two rows are due (push + email, both from the same enqueue call); the
  // point under test is that the THROWING push sender doesn't abort
  // processing of either row, the email row (dropped_preference, match's
  // default) still resolves normally in the same batch.
  assert.equal(result.processed, 2, 'the worker itself must not throw or abort when the sender throws');
  assert.equal(outage.calls, 1);

  const { rows: outboxRows } = await pool.query<{ status: string; attempt_count: number }>(
    `SELECT status, attempt_count FROM notification_outbox WHERE user_id = $1 AND channel = 'push'`,
    [user],
  );
  assert.equal(outboxRows[0]!.status, 'failed_retryable');
  assert.equal(outboxRows[0]!.attempt_count, 1);

  // Clean up: this row is deliberately left non-terminal (that's the point
  // of the assertion above) with a due time only ~30s out. Left alone, any
  // LATER test in this file, whose clock, by construction, always reads
  // later than this one's, would immediately see it as due and sweep it
  // into an unrelated assertion. Every other test in this file resolves
  // its own rows to a terminal status before finishing; this one can't
  // (that's what it's testing), so it deletes them explicitly instead.
  await pool.query('DELETE FROM notification_outbox WHERE user_id = $1', [user]);
});

test('a push-sender outage retries with backoff and reaches a terminal "dead" state, no infinite retry loop', async () => {
  const user = await insertUser(pool);
  const clock = new ManualClock(slotClock());
  await registerToken(user, 'tok-fail_send-loop', clock); // FakePushSender: "fail_send" substring -> always fails
  const sysCtx = buildCtx({ actor: { type: 'system', job: 'test' }, clock });

  await enqueueNotification(sysCtx, {
    userId: user,
    eventType: 'interest_accepted',
    dedupKey: `interest_accepted:backoff-test`,
    payload: {},
  });

  const push = new FakePushSender();
  const email = new FakeEmailSender();

  const expectedBackoffs = [30, 60, 120, 240]; // base 30s, x2 each time, until maxAttempts=5
  for (const backoff of expectedBackoffs) {
    const r = await runNotificationDeliveryWorker(sysCtx, { push, email });
    assert.equal(r.retried, 1);
    clock.advanceMs(backoff * 1000);
  }
  // 5th failure reaches maxAttempts and goes terminal.
  const final = await runNotificationDeliveryWorker(sysCtx, { push, email });
  assert.equal(final.dead, 1);
  assert.equal(final.retried, 0);

  const { rows } = await pool.query<{ status: string; attempt_count: number }>(
    `SELECT status, attempt_count FROM notification_outbox WHERE user_id = $1 AND channel = 'push'`,
    [user],
  );
  assert.equal(rows[0]!.status, 'dead');
  assert.equal(rows[0]!.attempt_count, 5);

  // And it stays dead, running the worker again must not pick it up or retry it further.
  clock.advanceMs(10 * 60 * 60 * 1000);
  const afterDead = await runNotificationDeliveryWorker(sysCtx, { push, email });
  assert.equal(afterDead.processed, 0, 'a dead row must never be retried again');
});

// =========================================================================
// Invalid tokens are pruned automatically during real delivery
// =========================================================================

test('an invalid/unregistered token reported by the sender during delivery is pruned automatically', async () => {
  const user = await insertUser(pool);
  const clock = new ManualClock(slotClock());
  await registerToken(user, 'tok-invalid_token-marker', clock); // FakePushSender: "invalid_token" substring
  const sysCtx = buildCtx({ actor: { type: 'system', job: 'test' }, clock });

  await enqueueNotification(sysCtx, {
    userId: user,
    eventType: 'interest_accepted',
    dedupKey: `interest_accepted:prune-test`,
    payload: {},
  });

  const push = new FakePushSender();
  const email = new FakeEmailSender();
  const result = await runNotificationDeliveryWorker(sysCtx, { push, email });

  assert.equal(result.prunedTokens, 1);
  assert.equal(result.droppedNoTarget, 1, 'no devices left after pruning the only (invalid) one');

  const { rows } = await pool.query('SELECT * FROM device_tokens WHERE push_token = $1', ['tok-invalid_token-marker']);
  assert.equal(rows.length, 0);
});

// =========================================================================
// Privacy-safe payloads
// =========================================================================

test('enqueueNotification rejects payloads that would leak a reporter identity, exact location, or payment details', async () => {
  const user = await insertUser(pool);
  const sysCtx = buildCtx({ actor: { type: 'system', job: 'test' } });

  await assert.rejects(
    () =>
      enqueueNotification(sysCtx, {
        userId: user,
        eventType: 'safety_notice',
        dedupKey: `safety_notice:${user}-1`,
        payload: { reporterUserId: 'someone' },
      }),
    ValidationError,
  );
  await assert.rejects(
    () =>
      enqueueNotification(sysCtx, {
        userId: user,
        eventType: 'date_proposal_received',
        dedupKey: `date_proposal_received:${user}-2`,
        payload: { latitude: 40.7128, longitude: -74.006 },
      }),
    ValidationError,
  );
  await assert.rejects(
    () =>
      enqueueNotification(sysCtx, {
        userId: user,
        eventType: 'payment_failed',
        dedupKey: `payment_failed:${user}-3`,
        payload: { cardLast4: '4242' },
      }),
    ValidationError,
  );
  await assert.rejects(
    () =>
      enqueueNotification(sysCtx, {
        userId: user,
        eventType: 'interest_accepted',
        dedupKey: `interest_accepted:${user}-4`,
        payload: { body: 'hand-written prose' },
      }),
    ValidationError,
  );
});

test('enqueueNotification rejects "messagePreviewText" on any event other than message_received', async () => {
  const user = await insertUser(pool);
  const sysCtx = buildCtx({ actor: { type: 'system', job: 'test' } });
  await assert.rejects(
    () =>
      enqueueNotification(sysCtx, {
        userId: user,
        eventType: 'chat_opened',
        dedupKey: `chat_opened:${user}-preview-misuse`,
        payload: { messagePreviewText: 'should not be allowed here' },
      }),
    ValidationError,
  );
});

// =========================================================================
// Misc guardrails
// =========================================================================

test('runNotificationDeliveryWorker: only a system or admin actor may run delivery', async () => {
  const user = await insertUser(pool);
  const userCtx = buildCtx({ actor: userActor(user) });
  await assert.rejects(
    () => runNotificationDeliveryWorker(userCtx, { push: new FakePushSender(), email: new FakeEmailSender() }),
    ForbiddenError,
  );
});

test('a user with no registered device receives no push and the row is dropped, not retried forever', async () => {
  const user = await insertUser(pool);
  const sysCtx = buildCtx({ actor: { type: 'system', job: 'test' } });
  await enqueueNotification(sysCtx, {
    userId: user,
    eventType: 'interest_accepted',
    dedupKey: `interest_accepted:no-device`,
    payload: {},
  });

  const result = await runNotificationDeliveryWorker(sysCtx, { push: new FakePushSender(), email: new FakeEmailSender() });
  assert.equal(result.droppedNoTarget, 1);
});
