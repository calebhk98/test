import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import pg from 'pg';
import { isWithinQuietHours, nextQuietHoursEnd, updateMyQuietHours } from '../../src/services/notifications/quietHours.js';
import { enqueueNotification } from '../../src/services/notifications/outbox.js';
import { runNotificationDeliveryWorker } from '../../src/services/notifications/delivery.js';
import { registerDeviceToken } from '../../src/services/notifications/devices.js';
import { FakePushSender } from '../../src/services/notifications/adapters/fake.push.js';
import { FakeEmailSender } from '../../src/services/notifications/adapters/fake.email.js';
import { ValidationError } from '../../src/lib/errors.js';
import { ManualClock } from '../../src/lib/time.js';
import { setupTestDatabase, teardownTestDatabase, buildCtx, userActor, insertUser } from '../../src/services/notifications/testSupport.js';

let pool: pg.Pool;

before(async () => {
  pool = await setupTestDatabase('quiethours');
});

after(async () => {
  await teardownTestDatabase();
});

// ---- pure isWithinQuietHours / nextQuietHoursEnd -------------------------

test('isWithinQuietHours: a normal (non-wrapping) window', () => {
  const qh = { enabled: true, startMinute: 9 * 60, endMinute: 17 * 60, timezone: 'UTC' };
  assert.equal(isWithinQuietHours(qh, new Date('2026-03-10T10:00:00.000Z')), true);
  assert.equal(isWithinQuietHours(qh, new Date('2026-03-10T08:59:00.000Z')), false);
  assert.equal(isWithinQuietHours(qh, new Date('2026-03-10T17:00:00.000Z')), false, 'end is exclusive');
});

test('isWithinQuietHours: an overnight window wraps across midnight', () => {
  const qh = { enabled: true, startMinute: 22 * 60, endMinute: 8 * 60, timezone: 'UTC' }; // 22:00 -> 08:00
  assert.equal(isWithinQuietHours(qh, new Date('2026-03-10T23:30:00.000Z')), true);
  assert.equal(isWithinQuietHours(qh, new Date('2026-03-11T02:00:00.000Z')), true);
  assert.equal(isWithinQuietHours(qh, new Date('2026-03-10T12:00:00.000Z')), false);
});

test('isWithinQuietHours: disabled, or no configuration at all, is never "quiet"', () => {
  const disabled = { enabled: false, startMinute: 0, endMinute: 60, timezone: 'UTC' };
  assert.equal(isWithinQuietHours(disabled, new Date('2026-03-10T00:30:00.000Z')), false);

  const zeroLength = { enabled: true, startMinute: 500, endMinute: 500, timezone: 'UTC' };
  assert.equal(isWithinQuietHours(zeroLength, new Date('2026-03-10T08:20:00.000Z')), false);
});

test('isWithinQuietHours: evaluated in the user\'s own local time zone, not UTC', () => {
  // 22:00-08:00 local in America/New_York (UTC-5 in March, before DST). 03:00 UTC == 22:00 local.
  const qh = { enabled: true, startMinute: 22 * 60, endMinute: 8 * 60, timezone: 'America/New_York' };
  assert.equal(isWithinQuietHours(qh, new Date('2026-03-10T03:00:00.000Z')), true);
  assert.equal(isWithinQuietHours(qh, new Date('2026-03-10T15:00:00.000Z')), false); // 10:00 local
});

test('nextQuietHoursEnd: minutes remaining until local end-of-window', () => {
  const qh = { enabled: true, startMinute: 22 * 60, endMinute: 8 * 60, timezone: 'UTC' };
  const now = new Date('2026-03-10T23:00:00.000Z'); // 23:00, window ends 08:00 -> 9h away
  const end = nextQuietHoursEnd(qh, now);
  assert.equal(end.toISOString(), '2026-03-11T08:00:00.000Z');
});

test('updateMyQuietHours: rejects an unrecognized time zone', async () => {
  const user = await insertUser(pool);
  const ctx = buildCtx({ actor: userActor(user) });
  await assert.rejects(
    () => updateMyQuietHours(ctx, { enabled: true, startMinute: 0, endMinute: 60, timezone: 'Not/A_Zone' }),
    ValidationError,
  );
});

test('updateMyQuietHours: persists and round-trips', async () => {
  const user = await insertUser(pool);
  const ctx = buildCtx({ actor: userActor(user) });
  const saved = await updateMyQuietHours(ctx, { enabled: true, startMinute: 1320, endMinute: 480, timezone: 'America/Los_Angeles' });
  assert.deepEqual(saved, { enabled: true, startMinute: 1320, endMinute: 480, timezone: 'America/Los_Angeles' });
});

// ---- integration: quiet hours through the real delivery pipeline --------

test('a notification raised during quiet hours is HELD, then delivered right after quiet hours end (documented hold-not-drop policy)', async () => {
  const user = await insertUser(pool);
  const clock = new ManualClock(new Date('2026-04-01T23:00:00.000Z')); // inside a 22:00-08:00 UTC quiet window
  const userCtx = buildCtx({ actor: userActor(user), clock });
  const sysCtx = buildCtx({ actor: { type: 'system', job: 'test' }, clock });

  await registerDeviceToken(userCtx, { platform: 'ios', deviceId: 'd', pushToken: 'tok-quiet' });
  await updateMyQuietHours(userCtx, { enabled: true, startMinute: 22 * 60, endMinute: 8 * 60, timezone: 'UTC' });

  await enqueueNotification(sysCtx, {
    userId: user,
    eventType: 'interest_accepted',
    dedupKey: `interest_accepted:${user}-quiet-test`,
    payload: {},
  });

  const push = new FakePushSender();
  const email = new FakeEmailSender();

  const first = await runNotificationDeliveryWorker(sysCtx, { push, email });
  assert.equal(first.held, 1, 'push row must be held, not sent or dropped, while inside quiet hours');
  assert.equal(push.sent.length, 0, 'no push should reach the sender while quiet hours are active');

  const { rows } = await pool.query<{ status: string; next_attempt_at: Date }>(
    `SELECT status, next_attempt_at FROM notification_outbox WHERE user_id = $1 AND channel = 'push'`,
    [user],
  );
  assert.equal(rows[0]!.status, 'held_quiet_hours');
  assert.equal(rows[0]!.next_attempt_at.toISOString(), '2026-04-02T08:00:00.000Z');

  // Still inside the window an hour later: still held.
  clock.advanceHours(1);
  const stillHeld = await runNotificationDeliveryWorker(sysCtx, { push, email });
  assert.equal(stillHeld.processed, 0, 'not due yet, the held row\'s next_attempt_at is still in the future');

  // Jump past quiet hours end.
  clock.set(new Date('2026-04-02T08:00:01.000Z'));
  const after = await runNotificationDeliveryWorker(sysCtx, { push, email });
  assert.equal(after.sent, 1, 'held notification must be delivered once quiet hours end');
  assert.equal(push.sent.length, 1);
});

test('safety_notice bypasses quiet hours entirely and is delivered immediately', async () => {
  const user = await insertUser(pool);
  const clock = new ManualClock(new Date('2026-04-01T23:00:00.000Z')); // deep inside quiet hours
  const userCtx = buildCtx({ actor: userActor(user), clock });
  const sysCtx = buildCtx({ actor: { type: 'system', job: 'test' }, clock });

  await registerDeviceToken(userCtx, { platform: 'ios', deviceId: 'd', pushToken: 'tok-safety' });
  await updateMyQuietHours(userCtx, { enabled: true, startMinute: 22 * 60, endMinute: 8 * 60, timezone: 'UTC' });

  await enqueueNotification(sysCtx, {
    userId: user,
    eventType: 'safety_notice',
    dedupKey: `safety_notice:${user}-bypass-test`,
    payload: {},
  });

  const push = new FakePushSender();
  const email = new FakeEmailSender();
  const result = await runNotificationDeliveryWorker(sysCtx, { push, email });

  assert.equal(result.held, 0, 'a safety notice must never be held for quiet hours');
  // Safety notices are also never gated by channel preference (file doc),
  // so both the push and email outbox rows deliver immediately here.
  assert.equal(result.sent, 2);
  assert.equal(push.sent.length, 1);
  assert.equal(email.sent.length, 1);
});

test('a non-safety event for a user with quiet hours disabled (the default) delivers immediately at any local hour', async () => {
  const user = await insertUser(pool);
  const clock = new ManualClock(new Date('2026-04-01T03:00:00.000Z')); // 3am, would be "quiet" under a typical window, but none is configured
  const userCtx = buildCtx({ actor: userActor(user), clock });
  const sysCtx = buildCtx({ actor: { type: 'system', job: 'test' }, clock });
  await registerDeviceToken(userCtx, { platform: 'android', deviceId: 'd', pushToken: 'tok-nodefault' });

  await enqueueNotification(sysCtx, {
    userId: user,
    eventType: 'date_proposal_received',
    dedupKey: `date_proposal_received:${user}-nodefault`,
    payload: {},
  });

  const push = new FakePushSender();
  const email = new FakeEmailSender();
  const result = await runNotificationDeliveryWorker(sysCtx, { push, email });
  assert.equal(result.sent, 1, 'no quiet-hours row means "24/7 delivery allowed" (build brief default)');
});
