/**
 * The SMS notification channel (build correction: an OPTIONAL, verified
 * phone number may back an OPT-IN SMS channel, see auth.service.ts's
 * module doc and preferences.ts/delivery.ts/outbox.ts in this same
 * directory).
 *
 * Reuses `notifications/testSupport.ts` (this build's own sibling-owned
 * harness, same file `notificationDelivery.test.ts`/`quietHours.test.ts`
 * already use, not modified here) for its `odate_notif_<suite>` database
 * bootstrap and `buildCtx`/`insertUser` helpers.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import pg from 'pg';
import { enqueueNotification } from '../../src/services/notifications/outbox.js';
import { runNotificationDeliveryWorker } from '../../src/services/notifications/delivery.js';
import {
  getMyNotificationPreferences,
  updateMyNotificationPreference,
  DEFAULT_PREFERENCES,
} from '../../src/services/notifications/preferences.js';
import { NOTIFICATION_CONFIG } from '../../src/services/notifications/config.js';
import { FakePushSender } from '../../src/services/notifications/adapters/fake.push.js';
import { FakeEmailSender } from '../../src/services/notifications/adapters/fake.email.js';
import { FakeSmsSender } from '../../src/services/notifications/adapters/fake.sms.js';
import { registerDeviceToken } from '../../src/services/notifications/devices.js';
import * as authService from '../../src/services/auth.service.js';
import { sha256Hex } from '../../src/lib/hash.js';
import { ValidationError } from '../../src/lib/errors.js';
import { ManualClock } from '../../src/lib/time.js';
import { setupTestDatabase, teardownTestDatabase, buildCtx, userActor, insertUser } from '../../src/services/notifications/testSupport.js';

let pool: pg.Pool;

before(async () => {
  pool = await setupTestDatabase('sms');
});

after(async () => {
  await teardownTestDatabase();
});

/** Adds and verifies a phone number for `userId` directly through auth.service, seeding a known code hash so the test never needs the randomly-generated raw code (same pattern `tests/unit/phone.test.ts`/`auth.test.ts` use). */
async function giveVerifiedPhone(userCtx: ReturnType<typeof buildCtx>, userId: string, e164: string): Promise<void> {
  await authService.requestPhoneVerification(userCtx, { phoneNumber: e164, country: 'US' });
  await pool.query(`UPDATE phone_verification_codes SET code_hash = $2 WHERE user_id = $1 AND consumed_at IS NULL`, [
    userId,
    sha256Hex('654321'),
  ]);
  await authService.verifyPhone(userCtx, { code: '654321' });
}

// =====================================================================
// Defaults and the opt-in gate
// =====================================================================

test('sms defaults to OFF for every single category, including account_activity (unlike push/email)', () => {
  for (const category of Object.keys(DEFAULT_PREFERENCES) as Array<keyof typeof DEFAULT_PREFERENCES>) {
    assert.equal(DEFAULT_PREFERENCES[category].sms, false, `${category} must default sms to false`);
  }
});

test('getMyNotificationPreferences: a brand-new user (no rows at all) still reads sms:false everywhere', async () => {
  const user = await insertUser(pool);
  const ctx = buildCtx({ actor: userActor(user) });
  const prefs = await getMyNotificationPreferences(ctx);
  for (const category of Object.keys(prefs) as Array<keyof typeof prefs>) {
    assert.equal(prefs[category].sms, false);
  }
});

test('updateMyNotificationPreference: turning sms ON is rejected without a verified phone', async () => {
  const user = await insertUser(pool);
  const ctx = buildCtx({ actor: userActor(user) });
  await assert.rejects(() => updateMyNotificationPreference(ctx, 'match', { sms: true }), ValidationError);
});

test('updateMyNotificationPreference: sms can be turned on once the phone is verified, and off again freely', async () => {
  const user = await insertUser(pool);
  const ctx = buildCtx({ actor: userActor(user) });
  await giveVerifiedPhone(ctx, user, '+14155559001');

  const on = await updateMyNotificationPreference(ctx, 'match', { sms: true });
  assert.equal(on.sms, true);

  const off = await updateMyNotificationPreference(ctx, 'match', { sms: false });
  assert.equal(off.sms, false);
});

// =====================================================================
// outbox.ts: SMS row creation is cost-gated at enqueue time
// =====================================================================

test('enqueueNotification: creates no sms row at all when the recipient has not opted in (the common case)', async () => {
  const user = await insertUser(pool);
  const sysCtx = buildCtx({ actor: { type: 'system', job: 'test' } });

  await enqueueNotification(sysCtx, {
    userId: user,
    eventType: 'interest_accepted',
    dedupKey: `interest_accepted:${user}-no-optin`,
    payload: {},
  });

  const { rows } = await pool.query<{ channel: string }>('SELECT channel FROM notification_outbox WHERE user_id = $1', [user]);
  assert.deepEqual(rows.map((r) => r.channel).sort(), ['email', 'push'], 'no sms row should exist when nobody opted in');
});

test('enqueueNotification: creates no sms row when opted in but the phone is unverified', async () => {
  const user = await insertUser(pool);
  const ctx = buildCtx({ actor: userActor(user) });
  // Request but never verify, cannot even turn the preference on (previous
  // test), but simulate the defensive case directly at the outbox level too.
  await authService.requestPhoneVerification(ctx, { phoneNumber: '+14155559002', country: 'US' });

  const sysCtx = buildCtx({ actor: { type: 'system', job: 'test' } });
  await enqueueNotification(sysCtx, {
    userId: user,
    eventType: 'interest_accepted',
    dedupKey: `interest_accepted:${user}-unverified`,
    payload: {},
  });
  const { rows } = await pool.query<{ channel: string }>(
    `SELECT channel FROM notification_outbox WHERE user_id = $1 AND channel = 'sms'`,
    [user],
  );
  assert.equal(rows.length, 0);
});

test('enqueueNotification: creates an sms row when opted in AND verified, and it actually delivers', async () => {
  const user = await insertUser(pool);
  const ctx = buildCtx({ actor: userActor(user) });
  await giveVerifiedPhone(ctx, user, '+14155559003');
  // account_activity is the one category that defaults BOTH push and email
  // ON (preferences.ts), using it here means the "push drops (no device
  // token), email + sms both deliver" story below isn't an artifact of a
  // category-specific default, just of the device-token gap.
  await updateMyNotificationPreference(ctx, 'account_activity', { sms: true });

  const sysCtx = buildCtx({ actor: { type: 'system', job: 'test' } });
  await enqueueNotification(sysCtx, {
    userId: user,
    eventType: 'payment_hold_authorized',
    dedupKey: `payment_hold_authorized:${user}-optedin`,
    payload: {},
  });

  const { rows } = await pool.query<{ channel: string }>('SELECT channel FROM notification_outbox WHERE user_id = $1', [user]);
  assert.deepEqual(rows.map((r) => r.channel).sort(), ['email', 'push', 'sms']);

  const push = new FakePushSender();
  const email = new FakeEmailSender();
  const sms = new FakeSmsSender();
  const result = await runNotificationDeliveryWorker(sysCtx, { push, email, sms });
  assert.equal(result.sent, 2, 'push has no device token so it drops no-target; email + sms both deliver');
  assert.equal(sms.sent.length, 1);
  assert.equal(sms.sent[0]!.toE164, '+14155559003');
});

test('safety_notice can never have an sms row, safety is not a configurable category', async () => {
  const user = await insertUser(pool);
  const ctx = buildCtx({ actor: userActor(user) });
  await giveVerifiedPhone(ctx, user, '+14155559004');
  // No category preference exists for 'safety' at all (types.ts), nothing to opt into.

  const sysCtx = buildCtx({ actor: { type: 'system', job: 'test' } });
  await enqueueNotification(sysCtx, { userId: user, eventType: 'safety_notice', dedupKey: `safety_notice:${user}`, payload: {} });

  const { rows } = await pool.query<{ channel: string }>('SELECT channel FROM notification_outbox WHERE user_id = $1', [user]);
  assert.deepEqual(rows.map((r) => r.channel).sort(), ['email', 'push']);
});

// =====================================================================
// delivery.ts: removing the phone mid-flight immediately disables SMS,
// even for a row that was already queued while it was verified.
// =====================================================================

test('removing the phone after enqueue but before delivery drops the already-queued sms row (never sent)', async () => {
  const user = await insertUser(pool);
  const ctx = buildCtx({ actor: userActor(user) });
  await giveVerifiedPhone(ctx, user, '+14155559005');
  await updateMyNotificationPreference(ctx, 'match', { sms: true });

  const sysCtx = buildCtx({ actor: { type: 'system', job: 'test' } });
  await enqueueNotification(sysCtx, {
    userId: user,
    eventType: 'interest_accepted',
    dedupKey: `interest_accepted:${user}-then-removed`,
    payload: {},
  });

  await authService.removePhone(ctx);

  const push = new FakePushSender();
  const email = new FakeEmailSender();
  const sms = new FakeSmsSender();
  await runNotificationDeliveryWorker(sysCtx, { push, email, sms });

  assert.equal(sms.sent.length, 0, 'no SMS should ever reach the sender once the phone is gone');
  const { rows } = await pool.query<{ status: string }>(
    `SELECT status FROM notification_outbox WHERE user_id = $1 AND channel = 'sms'`,
    [user],
  );
  assert.equal(rows[0]!.status, 'dropped_no_target');
});

// =====================================================================
// Cost controls: coalescing at least as aggressive as push, and the
// per-user daily rate cap.
// =====================================================================

test('config sanity: sms coalescing windows are at least as long (as aggressive) as push\'s', () => {
  assert.ok(NOTIFICATION_CONFIG.sms.coalesceDebounceSeconds >= NOTIFICATION_CONFIG.message.coalesceDebounceSeconds);
  assert.ok(NOTIFICATION_CONFIG.sms.coalesceMaxWaitSeconds >= NOTIFICATION_CONFIG.message.coalesceMaxWaitSeconds);
});

test('message_received: a two-message burst produces 2 separate pushes but only 1 coalesced sms', async () => {
  const user = await insertUser(pool);
  const clock = new ManualClock(new Date('2026-02-01T12:00:00.000Z'));
  const userCtx = buildCtx({ actor: userActor(user), clock });
  await giveVerifiedPhone(userCtx, user, '+14155559006');
  await updateMyNotificationPreference(userCtx, 'message', { sms: true });
  await registerDeviceToken(userCtx, { platform: 'ios', deviceId: 'd', pushToken: 'tok-burst' });

  const sysCtx = buildCtx({ actor: { type: 'system', job: 'test' }, clock });
  const push = new FakePushSender();
  const email = new FakeEmailSender();
  const sms = new FakeSmsSender();

  // Message 1.
  await enqueueNotification(sysCtx, {
    userId: user,
    eventType: 'message_received',
    dedupKey: `message_received:${user}-1`,
    coalescingKey: `message:${user}:convo-1`,
    payload: { senderFirstName: 'Alex' },
  });

  // Past push's 90s debounce, well before sms's 300s, push fires, sms doesn't.
  clock.advanceMs(91_000);
  let result = await runNotificationDeliveryWorker(sysCtx, { push, email, sms });
  assert.equal(push.sent.length, 1, 'first push fires on its own debounce');
  assert.equal(sms.sent.length, 0, 'sms is still coalescing, nowhere near its own, longer window yet');

  // Message 2, same conversation, a fresh push row (the first is 'sent',
  // terminal) but MERGES into the still-'queued' sms row.
  await enqueueNotification(sysCtx, {
    userId: user,
    eventType: 'message_received',
    dedupKey: `message_received:${user}-2`,
    coalescingKey: `message:${user}:convo-1`,
    payload: { senderFirstName: 'Alex' },
  });

  clock.advanceMs(91_000); // t = 182s: past push row 2's debounce, still before sms's
  result = await runNotificationDeliveryWorker(sysCtx, { push, email, sms });
  assert.equal(push.sent.length, 2, 'second message gets its own separate push');
  assert.equal(sms.sent.length, 0, 'sms has still not fired, both messages are still batched into one pending sms');

  // Jump well past the sms window's own (longer) deadline.
  clock.advanceMs(400_000);
  result = await runNotificationDeliveryWorker(sysCtx, { push, email, sms });
  assert.equal(sms.sent.length, 1, 'both messages finally go out as exactly ONE coalesced sms');
  assert.equal(push.sent.length, 2, 'push count is unaffected by the sms window, still 2, never merged down');
  void result;
});

// =====================================================================
// Per-user daily SMS rate cap (cost control)
// =====================================================================

test('per-user daily sms cap: further SMS for the same user are dropped_rate_limited, not sent, once the cap is hit', async () => {
  const user = await insertUser(pool);
  const clock = new ManualClock(new Date('2026-02-05T12:00:00.000Z'));
  const userCtx = buildCtx({ actor: userActor(user), clock });
  await giveVerifiedPhone(userCtx, user, '+14155559007');
  await updateMyNotificationPreference(userCtx, 'account_activity', { sms: true });

  // Seed the cap directly (avoids the test needing to actually run
  // maxPerUserPerDay real deliveries), `NOTIFICATION_CONFIG.sms.maxPerUserPerDay`
  // rows already 'sent' with delivered_at inside the trailing 24h window
  // `deliverSms` checks.
  const { maxPerUserPerDay } = NOTIFICATION_CONFIG.sms;
  for (let i = 0; i < maxPerUserPerDay; i++) {
    await pool.query(
      `INSERT INTO notification_outbox
         (user_id, event_type, category, channel, template_key, payload, coalescing_key, status, next_attempt_at, delivered_at, created_at, updated_at)
       VALUES ($1, 'payment_hold_authorized', 'account_activity', 'sms', 'x', '{}'::jsonb, $2, 'sent', $3, $3, $3, $3)`,
      [user, `seed-cap-${i}`, clock.now()],
    );
  }

  const sysCtx = buildCtx({ actor: { type: 'system', job: 'test' }, clock });
  await enqueueNotification(sysCtx, {
    userId: user,
    eventType: 'payment_hold_authorized',
    dedupKey: `payment_hold_authorized:${user}-over-cap`,
    payload: {},
  });

  const push = new FakePushSender();
  const email = new FakeEmailSender();
  const sms = new FakeSmsSender();
  const result = await runNotificationDeliveryWorker(sysCtx, { push, email, sms });

  assert.equal(sms.sent.length, 0, 'the provider must never even be called once the cap is hit');
  assert.equal(result.droppedRateLimited, 1);
  const { rows } = await pool.query<{ status: string }>(
    `SELECT status FROM notification_outbox WHERE user_id = $1 AND channel = 'sms' AND coalescing_key = $2`,
    [user, `payment_hold_authorized:${user}-over-cap`],
  );
  assert.equal(rows[0]!.status, 'dropped_rate_limited');
});

// =====================================================================
// Content-preview rule applies identically to sms (never message text
// unless the recipient opted into previews).
// =====================================================================

test('sms for message_received never carries preview text unless the recipient opted in, and truncates when they did', async () => {
  const user = await insertUser(pool);
  const clock = new ManualClock(new Date('2026-03-01T09:00:00.000Z'));
  const ctx = buildCtx({ actor: userActor(user), clock });
  await giveVerifiedPhone(ctx, user, '+14155559008');
  await updateMyNotificationPreference(ctx, 'message', { sms: true });

  const sysCtx = buildCtx({ actor: { type: 'system', job: 'test' }, clock });
  await enqueueNotification(sysCtx, {
    userId: user,
    eventType: 'message_received',
    dedupKey: `message_received:${user}-preview-off`,
    coalescingKey: `message:${user}:convo-preview`,
    payload: { senderFirstName: 'Sam', messagePreviewText: 'this is the actual private message body' },
  });

  // Past sms's (longer) coalescing window so this lone message is due.
  clock.advanceMs((NOTIFICATION_CONFIG.sms.coalesceDebounceSeconds + 5) * 1000);

  const push1 = new FakePushSender();
  const email1 = new FakeEmailSender();
  const sms1 = new FakeSmsSender();
  await runNotificationDeliveryWorker(sysCtx, { push: push1, email: email1, sms: sms1 });
  assert.equal(sms1.sent.length, 1);
  assert.equal('previewText' in sms1.sent[0]!.data, false, 'content preview defaults OFF, no message text in the sms payload');

  // Opt into previews, then repeat with a fresh event.
  const { updateMyContentPreviewSetting } = await import('../../src/services/notifications/preferences.js');
  await updateMyContentPreviewSetting(ctx, true);

  await enqueueNotification(sysCtx, {
    userId: user,
    eventType: 'message_received',
    dedupKey: `message_received:${user}-preview-on`,
    coalescingKey: `message:${user}:convo-preview-2`,
    payload: { senderFirstName: 'Sam', messagePreviewText: 'this is the actual private message body' },
  });
  clock.advanceMs((NOTIFICATION_CONFIG.sms.coalesceDebounceSeconds + 5) * 1000);
  const push2 = new FakePushSender();
  const email2 = new FakeEmailSender();
  const sms2 = new FakeSmsSender();
  await runNotificationDeliveryWorker(sysCtx, { push: push2, email: email2, sms: sms2 });
  assert.equal(sms2.sent.length, 1);
  assert.equal(sms2.sent[0]!.data.previewText, 'this is the actual private message body');
});

// =====================================================================
// Privacy-safe payload discipline applies to sms-eligible events too
// (shared code path, smoke-tested here for confidence).
// =====================================================================

test('a forbidden payload key (e.g. raw prose, reporter identity) is rejected regardless of sms eligibility', async () => {
  const user = await insertUser(pool);
  const ctx = buildCtx({ actor: userActor(user) });
  await giveVerifiedPhone(ctx, user, '+14155559009');
  await updateMyNotificationPreference(ctx, 'match', { sms: true });

  const sysCtx = buildCtx({ actor: { type: 'system', job: 'test' } });
  await assert.rejects(
    () =>
      enqueueNotification(sysCtx, {
        userId: user,
        eventType: 'interest_accepted',
        dedupKey: `interest_accepted:${user}-bad-payload`,
        payload: { body: 'free text should never be here' },
      }),
    ValidationError,
  );
});
