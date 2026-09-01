import { NOTIFICATION_TEMPLATES } from '../notification.service.js';
import type { NotificationEventType } from '../../domain/types.js';
import type { ExtendedNotificationEventType, NotificationBucket } from './types.js';

/**
 * Static template registry for events the delivery pipeline needs that
 * `notification.service.ts`'s frozen `NOTIFICATION_TEMPLATES` doesn't
 * cover, today, just `message_received` (see this build's report: that
 * event isn't in the shared `NotificationEventType` enum). Same discipline
 * as the shared registry: every value is a static, versioned template key,
 * never free text (spec §1 rule 9, §20).
 *
 * Four variants because two independent axes matter for a message push:
 * how many messages coalesced into this one notification (single vs
 * plural, "New message from Alex" vs "3 new messages from Alex"), and
 * whether the recipient opted into lock-screen content previews (generic
 * vs preview, see preferences.ts `getContentPreviewForUser`, default
 * OFF). `pickMessageTemplate` below is the only place that should choose
 * among these.
 */
export const MESSAGE_TEMPLATES = {
  singleGeneric: 'message_received_generic_v1',
  singlePreview: 'message_received_preview_v1',
  /** Used for every coalesced batch of 2+ messages, regardless of the preview preference, see `pickMessageTemplate`. */
  plural: 'message_received_plural_generic_v1',
} as const;

/** Chooses the message template key for a given (coalesced count, preview-allowed) pair. Preview is only ever shown for a single coalesced message, a preview of a *batch* would need to pick one message's text to show, which is its own small privacy/product decision this build declines to make; plural notifications always stay generic ("3 new messages from Alex"). */
export function pickMessageTemplate(coalescedCount: number, previewAllowed: boolean): string {
  if (coalescedCount <= 1) {
    return previewAllowed ? MESSAGE_TEMPLATES.singlePreview : MESSAGE_TEMPLATES.singleGeneric;
  }
  return MESSAGE_TEMPLATES.plural;
}

/** Every extended event type this build enqueues through, in one place, doubles as the zod enum tuple for input validation (see outbox.ts). */
export const EXTENDED_EVENT_TYPES = [
  ...(Object.keys(NOTIFICATION_TEMPLATES) as NotificationEventType[]),
  'message_received' as const,
] as unknown as [ExtendedNotificationEventType, ...ExtendedNotificationEventType[]];

const EXTENDED_EVENT_TYPE_SET: ReadonlySet<string> = new Set(EXTENDED_EVENT_TYPES);

export function isKnownEventType(eventType: string): eventType is ExtendedNotificationEventType {
  return EXTENDED_EVENT_TYPE_SET.has(eventType);
}

/**
 * The "logical" template key stored on an outbox row at enqueue time. For
 * every canonical event this is literally `NOTIFICATION_TEMPLATES[eventType]`
 * the same static template id notification.service.ts uses for the
 * in-app copy is reused for push/email too; only the renderer differs per
 * channel, not the identifier. `message_received` gets a placeholder
 * (`'message_received'` itself is not a real template key) because its
 * real template depends on the FINAL coalesced count and the recipient's
 * preview preference, both of which can still change between enqueue and
 * send, `pickMessageTemplate` resolves the real key at delivery time
 * (see delivery.ts).
 */
export function logicalTemplateKey(eventType: ExtendedNotificationEventType): string {
  if (eventType === 'message_received') return 'message_received';
  return NOTIFICATION_TEMPLATES[eventType];
}

/**
 * Fixed event -> user-configurable-category mapping (build brief: "A
 * preference per event category"). A product decision this build makes
 * explicitly so every event has exactly one home:
 *
 *  - match: the matching funnel itself, receiving/accepting/declining an
 *    interest, an interest about to expire, and the resulting chat
 *    unlocking (§11, §12.1).
 *  - message: new chat messages (product owner's second named event).
 *  - date_request: the date-proposal lifecycle end to end, from receipt
 *    through every terminal state (§13-§15), grouped together because a
 *    user who wants to hear about date requests wants to hear how they
 *    resolved, not just that one arrived.
 *  - account_activity: everything else that isn't user-initiated social
 *    activity, payments, tickets, reminders, chat decay, trust level
 *    changes.
 *  - safety: safety_notice only. Not in `NotificationCategory` at all
 *    (see types.ts), it is never user-configurable and always bypasses
 *    quiet hours (config.ts `quietHoursBypassEvents`).
 */
export const EVENT_BUCKET: Record<ExtendedNotificationEventType, NotificationBucket> = {
  interest_received: 'match',
  interest_accepted: 'match',
  interest_declined: 'match',
  interest_expiring_soon: 'match',
  chat_opened: 'match',
  message_received: 'message',
  date_proposal_received: 'date_request',
  date_accepted: 'date_request',
  date_canceled: 'date_request',
  date_refunded: 'date_request',
  date_disputed: 'date_request',
  date_no_show: 'date_request',
  date_completed: 'date_request',
  payment_hold_authorized: 'account_activity',
  payment_failed: 'account_activity',
  ticket_issued: 'account_activity',
  date_reminder: 'account_activity',
  venue_redeemed: 'account_activity',
  post_date_feedback_request: 'account_activity',
  chat_cooling: 'account_activity',
  trust_level_changed: 'account_activity',
  safety_notice: 'safety',
};
