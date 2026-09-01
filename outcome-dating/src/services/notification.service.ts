import type { Ctx } from '../lib/ctx.js';
import { NotImplementedError } from '../lib/errors.js';
import type { Notification, NotificationChannel, NotificationEventType, Page } from '../domain/types.js';

/**
 * notification.service — §20 notifications.
 * Spec: §20.
 *
 * Owning agent: C.
 *
 * HARD INVARIANT (spec §1 rule 9, §20 "All notification text must be
 * static or template-based. No generated natural language."): every
 * notification is rendered client-side (or by a push/email sender) from
 * `templateKey` + `payload` — this service NEVER constructs free-text
 * copy. `NOTIFICATION_TEMPLATES` is the fixed registry of allowed
 * `(eventType -> default templateKey)` pairs; `notify` should reject an
 * eventType/templateKey combination that isn't in this table rather than
 * accept arbitrary strings from callers.
 *
 * This module is intentionally a leaf: it takes fully-formed event data
 * from every other service (interest, conversation/message, dateProposal,
 * voucher, trust, moderation) and has no outgoing dependency on any of
 * them, which is what makes it safe for all of them to import without
 * creating a cycle.
 */

/** Fixed event -> default template key mapping (spec §20.1 event list x static-copy constraint). Real copy strings live in the client/email-renderer, not here — this registry is the contract for which key goes with which event. */
export const NOTIFICATION_TEMPLATES: Record<NotificationEventType, string> = {
  interest_received: 'interest_received_v1',
  interest_accepted: 'interest_accepted_v1',
  interest_declined: 'interest_declined_generic_v1', // spec §11.4 "They passed on this match." — deliberately generic
  interest_expiring_soon: 'interest_expiring_soon_v1',
  chat_opened: 'chat_opened_v1',
  date_proposal_received: 'date_proposal_received_v1',
  date_accepted: 'date_accepted_v1',
  payment_hold_authorized: 'payment_hold_authorized_v1',
  payment_failed: 'payment_failed_v1',
  ticket_issued: 'ticket_issued_v1',
  date_reminder: 'date_reminder_v1',
  venue_redeemed: 'venue_redeemed_v1',
  post_date_feedback_request: 'post_date_feedback_request_v1',
  chat_cooling: 'chat_cooling_v1',
  trust_level_changed: 'trust_level_changed_v1',
  safety_notice: 'safety_notice_v1',
};

export interface NotifyInput {
  userId: string;
  eventType: NotificationEventType;
  channel: NotificationChannel;
  /** Defaults to `NOTIFICATION_TEMPLATES[eventType]` if omitted. */
  templateKey?: string;
  payload?: Record<string, unknown>;
}

/** Creates and enqueues one notification. §20.2 "Do not use SMS by default" — `channel` is restricted to push/email/in_app at the type level, so SMS isn't representable here. */
export async function notify(ctx: Ctx, input: NotifyInput): Promise<Notification> {
  throw new NotImplementedError('notification.notify');
}

export async function listMyNotifications(ctx: Ctx, params?: { cursor?: string; limit?: number; unreadOnly?: boolean }): Promise<Page<Notification>> {
  throw new NotImplementedError('notification.listMyNotifications');
}

export async function markNotificationRead(ctx: Ctx, notificationId: string): Promise<void> {
  throw new NotImplementedError('notification.markNotificationRead');
}

/** Delivers all 'pending' notifications for the given channel (push/email sender integration point — actual transport is out of scope for the foundation layer). */
export async function deliverPending(ctx: Ctx, channel: NotificationChannel): Promise<{ sent: number; failed: number }> {
  throw new NotImplementedError('notification.deliverPending');
}
