import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import pg from 'pg';
import * as notificationService from '../../src/services/notification.service.js';
import { NOTIFICATION_TEMPLATES } from '../../src/services/notification.service.js';
import { ForbiddenError, ValidationError } from '../../src/lib/errors.js';
import { ManualClock } from '../../src/lib/time.js';
import { setupTestDatabase, teardownTestDatabase, buildCtx, userActor, insertUser } from './testCtxAgentC.js';
import type { NotificationEventType } from '../../src/domain/types.js';

let pool: pg.Pool;

before(async () => {
  pool = await setupTestDatabase('notification');
});

after(async () => {
  await teardownTestDatabase();
});

const ALL_EVENT_TYPES: NotificationEventType[] = [
  'interest_received',
  'interest_accepted',
  'interest_declined',
  'interest_expiring_soon',
  'chat_opened',
  'date_proposal_received',
  'date_accepted',
  'payment_hold_authorized',
  'payment_failed',
  'ticket_issued',
  'date_reminder',
  'venue_redeemed',
  'post_date_feedback_request',
  'chat_cooling',
  'trust_level_changed',
  'safety_notice',
];

test('NOTIFICATION_TEMPLATES has exactly one static template per §20.1 event, and every value looks like a static versioned key (never free text)', () => {
  const keys = Object.keys(NOTIFICATION_TEMPLATES);
  assert.equal(keys.length, ALL_EVENT_TYPES.length);
  for (const eventType of ALL_EVENT_TYPES) {
    assert.ok(eventType in NOTIFICATION_TEMPLATES, `missing template for event "${eventType}"`);
    const templateKey = NOTIFICATION_TEMPLATES[eventType];
    assert.equal(typeof templateKey, 'string');
    assert.match(templateKey, /^[a-z0-9_]+_v\d+$/, `"${templateKey}" doesn't look like a static versioned template key`);
  }
  // No duplicate values masquerading as distinct templates would be caught
  // by nothing structurally, but distinctness is nice hygiene too:
  const values = Object.values(NOTIFICATION_TEMPLATES);
  assert.equal(new Set(values).size, values.length, 'every event should have its own template key');
});

test('notify: persists using the default template when none is given', async () => {
  const user = await insertUser(pool);
  const ctx = buildCtx({ actor: { type: 'system', job: 'test' }, clock: new ManualClock(new Date('2026-01-01T00:00:00.000Z')) });
  const n = await notificationService.notify(ctx, {
    userId: user,
    eventType: 'interest_received',
    channel: 'in_app',
    payload: { interestId: 'x' },
  });
  assert.equal(n.templateKey, NOTIFICATION_TEMPLATES.interest_received);
  assert.equal(n.status, 'pending');
});

test('notify: rejects a templateKey that is not in the static registry', async () => {
  const user = await insertUser(pool);
  const ctx = buildCtx({ actor: { type: 'system', job: 'test' } });
  await assert.rejects(
    () =>
      notificationService.notify(ctx, {
        userId: user,
        eventType: 'interest_received',
        channel: 'in_app',
        templateKey: 'some_made_up_key_v1',
      }),
    ValidationError,
  );
});

test('notify: rejects a payload that tries to smuggle free-text prose', async () => {
  const user = await insertUser(pool);
  const ctx = buildCtx({ actor: { type: 'system', job: 'test' } });
  for (const key of ['body', 'text', 'message', 'html']) {
    await assert.rejects(
      () =>
        notificationService.notify(ctx, {
          userId: user,
          eventType: 'safety_notice',
          channel: 'in_app',
          payload: { [key]: 'hand-written prose should never live here' },
        }),
      ValidationError,
      `expected payload key "${key}" to be rejected`,
    );
  }
});

test('notify: SMS is not representable at the type level (§20.2 "Do not use SMS by default")', () => {
  // @ts-expect-error 'sms' is not a member of NotificationChannel.
  const _channel: import('../../src/domain/types.js').NotificationChannel = 'sms';
  void _channel;
});

test('listMyNotifications: unreadOnly filters and pagination cursor both work', async () => {
  const user = await insertUser(pool);
  const clock = new ManualClock(new Date('2026-01-02T00:00:00.000Z'));
  const ctx = buildCtx({ actor: userActor(user), clock });

  for (let i = 0; i < 3; i++) {
    await notificationService.notify(ctx, { userId: user, eventType: 'chat_opened', channel: 'in_app' });
    clock.advanceMs(1000);
  }
  const [, second] = (await notificationService.listMyNotifications(ctx, { limit: 100 })).items.slice().reverse();
  await notificationService.markNotificationRead(ctx, second!.id);

  const unread = await notificationService.listMyNotifications(ctx, { unreadOnly: true, limit: 100 });
  assert.equal(unread.items.length, 2);
  assert.ok(unread.items.every((n) => n.readAt === null));

  const firstPage = await notificationService.listMyNotifications(ctx, { limit: 2 });
  assert.equal(firstPage.items.length, 2);
  assert.ok(firstPage.nextCursor);
  const secondPage = await notificationService.listMyNotifications(ctx, { limit: 2, cursor: firstPage.nextCursor! });
  assert.equal(secondPage.items.length, 1);
});

test('markNotificationRead: idempotent, and forbidden for someone else\'s notification', async () => {
  const owner = await insertUser(pool);
  const stranger = await insertUser(pool);
  const ctx = buildCtx({ actor: { type: 'system', job: 'test' } });
  const n = await notificationService.notify(ctx, { userId: owner, eventType: 'chat_opened', channel: 'in_app' });

  const ownerCtx = buildCtx({ actor: userActor(owner) });
  await notificationService.markNotificationRead(ownerCtx, n.id);
  await notificationService.markNotificationRead(ownerCtx, n.id); // idempotent, must not throw

  const strangerCtx = buildCtx({ actor: userActor(stranger) });
  await assert.rejects(() => notificationService.markNotificationRead(strangerCtx, n.id), ForbiddenError);
});

test('deliverPending: only a system or admin actor may trigger delivery', async () => {
  const user = await insertUser(pool);
  const userCtx = buildCtx({ actor: userActor(user) });
  await assert.rejects(() => notificationService.deliverPending(userCtx, 'in_app'), ForbiddenError);

  const sysCtx = buildCtx({ actor: { type: 'system', job: 'notify_delivery' } });
  await notificationService.notify(sysCtx, { userId: user, eventType: 'chat_opened', channel: 'push' });
  const result = await notificationService.deliverPending(sysCtx, 'push');
  assert.equal(result.sent, 1);
  assert.equal(result.failed, 0);

  const again = await notificationService.deliverPending(sysCtx, 'push');
  assert.equal(again.sent, 0, 'already-sent notifications must not be redelivered');
});
