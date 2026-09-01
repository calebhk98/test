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
 */
export type NotificationOutboxChannel = 'push' | 'email';

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
  | 'dropped_no_target';

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
}

export interface QuietHours {
  enabled: boolean;
  startMinute: number;
  endMinute: number;
  timezone: string;
}
