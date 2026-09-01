import type { NotificationEventType } from '../../domain/types.js';

/**
 * Local types for the notification DELIVERY layer (push/email/device
 * registration/preferences/quiet hours). Deliberately NOT added to
 * `src/domain/types.ts` — that file is frozen shared infrastructure this
 * build does not own, and `notification.service.ts`'s
 * `NotificationEventType` enum is likewise frozen (another agent owns that
 * file). See this build's report for the one-line addition
 * (`'message_received'`) a future cross-cutting change could make to that
 * shared enum; until then, this module's own `ExtendedNotificationEventType`
 * is the superset the delivery pipeline actually needs.
 */

export type DevicePlatform = 'ios' | 'android' | 'web';

/** Every event the shared notification service knows about (§20.1), plus the one product-named event that enum doesn't cover yet. */
export type ExtendedNotificationEventType = NotificationEventType | 'message_received';

/**
 * The delivery pipeline's own channel set. 'in_app' is NOT a member here —
 * the in-app notification center is `notification.service.ts`'s
 * `notifications` table, which `enqueueNotification` calls into directly
 * for canonical event types (see outbox.ts). This outbox only ever queues
 * transport channels that need real, possibly-failing, possibly-retried
 * delivery.
 *
 * 'sms' (build correction: an OPTIONAL, verified phone number may back an
 * opt-in SMS channel — never a required one, see auth.service.ts module
 * doc) is added the same way `message_received` was added to
 * `ExtendedNotificationEventType` above: this is this build's own local
 * superset, not a change to any frozen shared type.
 */
export type NotificationOutboxChannel = 'push' | 'email' | 'sms';

/**
 * Preference categories a user can configure. 'safety' is deliberately NOT
 * a member — safety_notice is never user-configurable (see outbox.ts
 * `EVENT_CATEGORY` and the quiet-hours bypass list).
 */
export type NotificationCategory = 'match' | 'message' | 'date_request' | 'account_activity' | 'marketing';

/** Internal: every event is bucketed into one of the user-configurable categories, or 'safety' (not configurable, always delivered, bypasses quiet hours). */
export type NotificationBucket = NotificationCategory | 'safety';

export type OutboxStatus =
  | 'queued'
  | 'held_quiet_hours'
  | 'sent'
  | 'failed_retryable'
  | 'dead'
  | 'dropped_preference'
  | 'dropped_no_target'
  /** SMS-only, terminal, never retried: this user already hit `NOTIFICATION_CONFIG.sms.maxPerUserPerDay` (delivery.ts) — a cost cap, not a transport failure. */
  | 'dropped_rate_limited';

export interface OutboxRow {
  id: string;
  userId: string;
  eventType: ExtendedNotificationEventType;
  category: NotificationBucket;
  channel: NotificationOutboxChannel;
  templateKey: string;
  payload: Record<string, unknown>;
  coalescingKey: string;
  coalescedCount: number;
  status: OutboxStatus;
  attemptCount: number;
  nextAttemptAt: Date;
  lastError: string | null;
  createdAt: Date;
  updatedAt: Date;
  deliveredAt: Date | null;
}

export interface DeviceTokenRow {
  id: string;
  userId: string;
  platform: DevicePlatform;
  deviceId: string;
  pushToken: string;
  enabled: boolean;
  createdAt: Date;
  lastSeenAt: Date;
}

export interface CategoryPrefs {
  push: boolean;
  email: boolean;
  inApp: boolean;
  /**
   * Defaults to `false` for every category (see `preferences.ts`
   * `DEFAULT_PREFERENCES`) — unlike push/email, no category ever defaults
   * SMS on, because every send costs real money and requires a verified
   * phone number the user chose to add. Turning this on for a category is
   * necessary but not sufficient for that category's SMS to actually send —
   * `delivery.ts` also requires a currently-verified phone at send time.
   */
  sms: boolean;
}

export interface QuietHours {
  enabled: boolean;
  startMinute: number;
  endMinute: number;
  timezone: string;
}
