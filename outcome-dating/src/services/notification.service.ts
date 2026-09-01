import { z } from 'zod';
import type { Ctx } from '../lib/ctx.js';
import { requireUserActor } from '../lib/ctx.js';
import { ForbiddenError, NotFoundError, ValidationError } from '../lib/errors.js';
import { newId } from '../lib/ids.js';
import type { Notification, NotificationChannel, NotificationEventType, NotificationStatus, Page } from '../domain/types.js';

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
 * `(eventType -> default templateKey)` pairs; `notify` rejects any
 * `templateKey` (default or caller-supplied) that isn't one of this
 * registry's *values*, and separately rejects a payload that tries to
 * carry free-text prose under a common footgun key (`body`/`text`/
 * `message`/`html`/`copy`/`content`) — payloads may only carry structured
 * data (ids, enums, numbers) for the static template to interpolate.
 *
 * This module is intentionally a leaf: it takes fully-formed event data
 * from every other service (interest, conversation/message, dateProposal,
 * voucher, trust, moderation) and has no outgoing dependency on any of
 * them, which is what makes it safe for all of them to import without
 * creating a cycle.
 */

/** Fixed event -> default template key mapping (spec §20.1 event list x static-copy constraint). Real copy strings live in the client/email-renderer, not here — this registry is the contract for which key goes with which event. `Record<NotificationEventType, string>` also guarantees, at the type level, exactly one entry per event. */
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

const EVENT_TYPES = Object.keys(NOTIFICATION_TEMPLATES) as [NotificationEventType, ...NotificationEventType[]];
const VALID_TEMPLATE_KEYS: ReadonlySet<string> = new Set(Object.values(NOTIFICATION_TEMPLATES));

/**
 * Payload keys that would smuggle free-text prose into what must stay a
 * structured-data-only object (spec §1 rule 9, §20). Rejected outright by
 * `notify` — content comes from the static template the client renders,
 * never from anything in `payload`.
 */
const FORBIDDEN_PAYLOAD_KEYS = ['body', 'text', 'message', 'html', 'copy', 'content'] as const;

export interface NotifyInput {
  userId: string;
  eventType: NotificationEventType;
  channel: NotificationChannel;
  /** Defaults to `NOTIFICATION_TEMPLATES[eventType]` if omitted. */
  templateKey?: string;
  payload?: Record<string, unknown>;
}

const NotifyInputSchema = z.object({
  userId: z.string().uuid(),
  eventType: z.enum(EVENT_TYPES),
  channel: z.enum(['push', 'email', 'in_app']),
  templateKey: z.string().optional(),
  payload: z.record(z.unknown()).optional(),
});

interface NotificationRow {
  id: string;
  user_id: string;
  event_type: NotificationEventType;
  channel: NotificationChannel;
  template_key: string;
  payload: Record<string, unknown>;
  status: NotificationStatus;
  created_at: Date;
  sent_at: Date | null;
  read_at: Date | null;
}

function mapRow(row: NotificationRow): Notification {
  return {
    id: row.id,
    userId: row.user_id,
    eventType: row.event_type,
    channel: row.channel,
    templateKey: row.template_key,
    payload: row.payload,
    status: row.status,
    createdAt: row.created_at,
    sentAt: row.sent_at,
    readAt: row.read_at,
  };
}

function encodeCursor(row: { createdAt: Date; id: string }): string {
  return Buffer.from(`${row.createdAt.toISOString()}|${row.id}`, 'utf8').toString('base64url');
}

function decodeCursor(cursor: string): { createdAt: Date; id: string } {
  const [iso, id] = Buffer.from(cursor, 'base64url').toString('utf8').split('|');
  if (!iso || !id) throw new ValidationError('Invalid pagination cursor.');
  return { createdAt: new Date(iso), id };
}

/** Creates and enqueues one notification. §20.2 "Do not use SMS by default" — `channel` is restricted to push/email/in_app at the type level, so SMS isn't representable here. */
export async function notify(ctx: Ctx, input: NotifyInput): Promise<Notification> {
  const parsed = NotifyInputSchema.parse(input);
  const templateKey = parsed.templateKey ?? NOTIFICATION_TEMPLATES[parsed.eventType];

  if (!VALID_TEMPLATE_KEYS.has(templateKey)) {
    throw new ValidationError(
      `"${templateKey}" is not a registered static template for event "${parsed.eventType}" — every notification must render from a key in NOTIFICATION_TEMPLATES (spec §1 rule 9, §20).`,
    );
  }

  const payload = parsed.payload ?? {};
  for (const key of FORBIDDEN_PAYLOAD_KEYS) {
    if (key in payload) {
      throw new ValidationError(
        `Notification payload must not contain a free-text "${key}" field — content comes from the static template, never from payload prose.`,
      );
    }
  }

  const id = newId();
  const now = ctx.clock.now();
  const { rows } = await ctx.db.query<NotificationRow>(
    `INSERT INTO notifications (id, user_id, event_type, channel, template_key, payload, status, created_at)
     VALUES ($1, $2, $3, $4, $5, $6::jsonb, 'pending', $7)
     RETURNING *`,
    [id, parsed.userId, parsed.eventType, parsed.channel, templateKey, JSON.stringify(payload), now],
  );
  return mapRow(rows[0]!);
}

const ListParamsSchema = z.object({
  cursor: z.string().optional(),
  limit: z.number().int().min(1).max(100).optional(),
  unreadOnly: z.boolean().optional(),
});

export async function listMyNotifications(
  ctx: Ctx,
  params?: { cursor?: string; limit?: number; unreadOnly?: boolean },
): Promise<Page<Notification>> {
  const { userId } = requireUserActor(ctx);
  const parsed = ListParamsSchema.parse(params ?? {});
  const limit = parsed.limit ?? 20;

  const values: unknown[] = [userId];
  let clause = '';
  if (parsed.unreadOnly) clause += ' AND read_at IS NULL';
  if (parsed.cursor) {
    const c = decodeCursor(parsed.cursor);
    values.push(c.createdAt, c.id);
    clause += ` AND (created_at, id) < ($${values.length - 1}, $${values.length})`;
  }
  values.push(limit + 1);

  const { rows } = await ctx.db.query<NotificationRow>(
    `SELECT * FROM notifications WHERE user_id = $1 ${clause} ORDER BY created_at DESC, id DESC LIMIT $${values.length}`,
    values,
  );

  const hasMore = rows.length > limit;
  const pageRows = hasMore ? rows.slice(0, limit) : rows;
  const items = pageRows.map(mapRow);
  const nextCursor = hasMore ? encodeCursor(items[items.length - 1]!) : null;
  return { items, nextCursor };
}

export async function markNotificationRead(ctx: Ctx, notificationId: string): Promise<void> {
  const { userId } = requireUserActor(ctx);
  const now = ctx.clock.now();

  const { rows } = await ctx.db.query<{ id: string }>(
    `UPDATE notifications SET status = 'read', read_at = $1 WHERE id = $2 AND user_id = $3 AND read_at IS NULL RETURNING id`,
    [now, notificationId, userId],
  );
  if (rows[0]) return;

  const { rows: existing } = await ctx.db.query<{ user_id: string }>('SELECT user_id FROM notifications WHERE id = $1', [
    notificationId,
  ]);
  const existingRow = existing[0];
  if (!existingRow) throw new NotFoundError(`Notification ${notificationId} not found.`);
  if (existingRow.user_id !== userId) throw new ForbiddenError('Not your notification.');
  // else: already read — idempotent no-op.
}

/** Delivers all 'pending' notifications for the given channel (push/email sender integration point — actual transport is out of scope for the foundation layer). */
export async function deliverPending(ctx: Ctx, channel: NotificationChannel): Promise<{ sent: number; failed: number }> {
  if (ctx.actor.type !== 'system' && ctx.actor.type !== 'admin') {
    throw new ForbiddenError('Only a system job or an admin may trigger notification delivery.');
  }

  const now = ctx.clock.now();
  const { rows } = await ctx.db.query<{ id: string }>(
    `SELECT id FROM notifications WHERE channel = $1 AND status = 'pending' ORDER BY created_at ASC LIMIT 500`,
    [channel],
  );
  if (rows.length === 0) return { sent: 0, failed: 0 };

  const ids = rows.map((r) => r.id);
  // Real push/email transport is out of scope for the foundation layer
  // (see INTERFACES.md "what's real vs. stubbed") — this simulates a
  // successful hand-off to whichever sender integration lands later.
  await ctx.db.query(`UPDATE notifications SET status = 'sent', sent_at = $2 WHERE id = ANY($1::uuid[])`, [ids, now]);
  return { sent: ids.length, failed: 0 };
}
