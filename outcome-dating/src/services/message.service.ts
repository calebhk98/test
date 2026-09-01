import { z } from 'zod';
import type { Ctx } from '../lib/ctx.js';
import { requireUserActor } from '../lib/ctx.js';
import { ForbiddenError, RateLimitError } from '../lib/errors.js';
import { newId } from '../lib/ids.js';
import type { Message, MessageFlagType, Page } from '../domain/types.js';
import * as textscan from './textscan.service.js';
import * as trustService from './trust.service.js';
import * as conversationService from './conversation.service.js';
import * as notificationService from './notification.service.js';
import { enqueueNotification } from './notifications/index.js';
import { decodeTimestampIdCursor, encodeTimestampIdCursor } from '../lib/cursor.js';

/**
 * message.service, in-conversation messaging.
 * Spec: §12.2-§12.5, §24.7.
 *
 * Owning agent: C.
 *
 * Invariants:
 *  - Chat unlocks only after mutual match (spec §12.1): `sendMessage`
 *    throws `ForbiddenError` unless the conversation's status is one of
 *    `active`, `cooling`, `established` (never for a conversation the
 *    caller isn't a participant of, and never for `archived`).
 *  - Plain text + emoji only for MVP (spec §12.2), `MessageBodySchema` is
 *    a plain string with a length bound; there is no attachment/media
 *    field anywhere on this function's signature or on `Message` to
 *    validate, because none exists, adding one would be the actual
 *    violation, not a missing check here.
 *  - Every send calls `textscan.service#scanText`, persists any
 *    `message_flags` rows, and enforces `chat.max_messages_per_hour` and
 *    the trust-tiered `chat.max_links_per_hour_*` config (spec §12.3,
 *    §19.4), messages are never blocked for flagged *content* by default
 *    (spec §19.3), only rate-limited on raw throughput.
 *  - Off-app handles/links are never blocked outright (spec §12.5), a
 *    flagged message still sends, with `notification`'s static banner
 *    template attached via `analysisFlags` + a `safety_notice`
 *    notification whose `payload.reason` picks between the two static
 *    banner copies (never a new template per situation, see
 *    `notification.service.ts`'s "exactly one template per event"
 *    invariant).
 *  - Link *clickability* (spec §19.4) has nowhere to live on the frozen
 *    `Message`/`TextScanResult` domain types, so it is not persisted as a
 *    boolean. Instead it is folded into `message_flags.severity` for the
 *    `link` flag: severity 1 = clickable-eligible, severity 2 = present
 *    but must render as plain (non-clickable) text, see
 *    `LINK_NOT_CLICKABLE_SEVERITY` below for the single place this
 *    convention is defined.
 */

const OPEN_STATUSES: ReadonlySet<string> = new Set(['active', 'cooling', 'established']);
const MAX_MESSAGE_LENGTH = 4000;

// Plain text + emoji only (spec §12.2). A `string` schema with a length
// bound is the entire content contract, there is no way to smuggle an
// attachment through this validator because there is no field for one.
const MessageBodySchema = z
  .string()
  .trim()
  .min(1, 'Message cannot be empty.')
  .max(MAX_MESSAGE_LENGTH, `Message cannot exceed ${MAX_MESSAGE_LENGTH} characters.`);

/** See the file-header note on link-clickability encoding. */
const LINK_NOT_CLICKABLE_SEVERITY = 2;

interface MessageRow {
  id: string;
  conversation_id: string;
  sender_id: string;
  body: string;
  created_at: Date;
  read_at: Date | null;
  analysis_flags: MessageFlagType[];
}

function mapRow(row: MessageRow): Message {
  return {
    id: row.id,
    conversationId: row.conversation_id,
    senderId: row.sender_id,
    body: row.body,
    createdAt: row.created_at,
    readAt: row.read_at,
    analysisFlags: row.analysis_flags,
  };
}

/**
 * Trust-tiered hourly clickable-link quota (spec §12.3, §6.4 "Send links").
 *
 * Delegates to `trust.service#linksPerHourLimitFor`, which buckets against
 * the configurable `trust.link_min_level` (rather than a hardcoded
 * `=== 'limited'` comparison), so retuning that one key moves this send-time
 * cap and the render-time clickability gate (`trustService.canSendClickableLinks`,
 * called below) together, see trust.service.ts's "§6.4 vs §12.3 PRECEDENCE"
 * comment on `can()`, and docs/duplication.md finding 2, which this fixes:
 * this function used to re-derive its own hardcoded `'limited'` boundary,
 * so retuning `trust.link_min_level` moved link clickability but silently
 * left the per-hour send cap pinned to the old boundary.
 */
export async function linkLimitForCaller(ctx: Ctx): Promise<number> {
  const { trustLevel } = requireUserActor(ctx);
  return trustService.linksPerHourLimitFor(ctx, trustLevel);
}

/**
 * First word of the sender's own display name, for the `message_received`
 * notification's `senderFirstName` payload field (see
 * `notifications/delivery.ts#resolveTemplateAndData`). A direct,
 * read-only query against `profiles`, the same "narrow cross-domain
 * read" pattern `serializers/venue.ts#displayNamesFor` already uses for
 * an identical need, rather than a new `profile.service.ts` export for
 * one call site (this module has no "may call profile" edge, and adding
 * one is out of scope for this one field).
 */
async function senderFirstNameFor(ctx: Ctx, senderId: string): Promise<string> {
  const { rows } = await ctx.db.query<{ display_name: string }>('SELECT display_name FROM profiles WHERE user_id = $1', [senderId]);
  const displayName = rows[0]?.display_name ?? 'Someone';
  return displayName.trim().split(/\s+/)[0] ?? displayName;
}

export async function sendMessage(ctx: Ctx, conversationId: string, body: string): Promise<Message> {
  const { userId } = requireUserActor(ctx);
  const validBody = MessageBodySchema.parse(body);

  // Participant + existence check, and the source of truth for chat-unlock
  // (spec §12.1) below.
  const conversation = await conversationService.getConversation(ctx, conversationId);
  if (!OPEN_STATUSES.has(conversation.status)) {
    throw new ForbiddenError('You can’t send messages in this conversation right now.', { status: conversation.status });
  }

  const maxPerHour = await ctx.config.get('chat.max_messages_per_hour');
  const recentCount = await countMessagesInLastHour(ctx, userId);
  if (recentCount >= maxPerHour) {
    throw new RateLimitError('You are sending messages too fast. Please wait a bit before sending more.', {
      limit: maxPerHour,
    });
  }

  const scan = textscan.scanText(ctx, validBody);

  // §19.4 link-clickability. Resolved via `trust.service#canSendClickableLinks`
  // never re-derived from a raw trust-level comparison here (that would
  // be reimplementing trust scoring). Fails CLOSED (non-clickable) on any
  // error from that call, including `trust.service.ts` still being an
  // unimplemented stub in this parallel build, a safe default, not a
  // testing workaround: if the trust subsystem is unavailable, the correct
  // behavior is "don't render links clickable," not "assume the best."
  let linkNotClickable = false;
  if (scan.flags.some((f) => f.type === 'link')) {
    let canClick: boolean;
    try {
      canClick = await trustService.canSendClickableLinks(ctx, userId);
    } catch (err) {
      ctx.logger.warn('message.trust_check_failed_failing_closed', {
        userId,
        error: err instanceof Error ? err.message : String(err),
      });
      canClick = false;
    }
    const linkLimitPerHour = await linkLimitForCaller(ctx);
    const linksSentThisHour = await countLinksInLastHour(ctx, userId);
    const url = textscan.extractFirstLink(validBody) ?? validBody;
    const presentation = textscan.decideLinkPresentation({
      url,
      canSendClickableLinks: canClick,
      linksSentInLastHour: linksSentThisHour,
      linkLimitPerHour,
    });
    linkNotClickable = !presentation.clickable;
  }

  const now = ctx.clock.now();
  const id = newId();
  const flagTypes = [...new Set(scan.flags.map((f) => f.type))];

  const { rows } = await ctx.db.query<MessageRow>(
    `INSERT INTO messages (id, conversation_id, sender_id, body, created_at, analysis_flags)
     VALUES ($1, $2, $3, $4, $5, $6::jsonb)
     RETURNING *`,
    [id, conversationId, userId, validBody, now, JSON.stringify(flagTypes)],
  );
  const row = rows[0]!;

  for (const flag of scan.flags) {
    const severity = flag.type === 'link' && linkNotClickable ? Math.max(flag.severity, LINK_NOT_CLICKABLE_SEVERITY) : flag.severity;
    await ctx.db.query(`INSERT INTO message_flags (message_id, flag_type, severity) VALUES ($1, $2, $3)`, [
      id,
      flag.type,
      severity,
    ]);
  }

  await ctx.db.query(`UPDATE conversations SET last_message_at = $2 WHERE id = $1`, [conversationId, now]);

  // New-message notification (docs/ux-api-review.md §13: "there is no way
  // for a client to know a new message arrived without polling",
  // `message_received` had nowhere to fire from since this module wasn't
  // permitted to call the notification layer at all; see INTERFACES.md's
  // updated `message ─▶ notification` edge). Routed through
  // `notifications/index#enqueueNotification`, never `notification.service
  // #notify` directly, `message_received` isn't in that frozen event
  // enum (see notification.service.ts's own doc), and enqueueNotification
  // is the one place that applies the coalescing/preference/quiet-hours
  // pipeline this event needs (five messages while you're away should
  // become one push, not five).
  const recipientId = conversation.userAId === userId ? conversation.userBId : conversation.userAId;
  try {
    await enqueueNotification(ctx, {
      userId: recipientId,
      eventType: 'message_received',
      // Convention: `${eventType}:${entityId}`, this specific message,
      // so a retried send can never double-enqueue for the same row.
      dedupKey: `message_received:${id}`,
      // Convention (notifications/outbox.ts's own doc): groups every
      // undelivered message notification for this (recipient,
      // conversation) into one coalesced push, "5 messages -> 1 push",
      // instead of one push per message.
      coalescingKey: `message:${recipientId}:${conversationId}`,
      payload: {
        conversationId,
        senderFirstName: await senderFirstNameFor(ctx, userId),
        messagePreviewText: validBody,
      },
    });
  } catch (err) {
    // Best-effort, like every other notification call site in this
    // codebase, a notification-layer hiccup must never fail or roll
    // back an otherwise-successful send.
    ctx.logger.warn('message.enqueue_notification_failed', {
      messageId: id,
      conversationId,
      err: err instanceof Error ? err.message : String(err),
    });
  }

  // §19.3/§12.5: nothing above this point can block the send, flags are
  // recorded, and at most a static safety-notice banner is attached.
  // Raising the moderation score from repeated flags is
  // `moderation.service.ts`'s job (Agent E), fed by the `message_flags`
  // rows just written.
  if (scan.showSafetyBanner) {
    await notificationService.notify(ctx, {
      userId,
      eventType: 'safety_notice',
      channel: 'in_app',
      payload: { messageId: id, conversationId, reason: scan.safetyBannerTemplateKey },
    });
  }

  return mapRow(row);
}

const ListMessagesParamsSchema = z.object({
  cursor: z.string().optional(),
  limit: z.number().int().min(1).max(200).optional(),
});

export async function listMessages(
  ctx: Ctx,
  conversationId: string,
  params?: { cursor?: string; limit?: number },
): Promise<Page<Message>> {
  await conversationService.getConversation(ctx, conversationId); // authorizes participant, throws NotFound otherwise
  const parsed = ListMessagesParamsSchema.parse(params ?? {});
  const limit = parsed.limit ?? 50;

  const values: unknown[] = [conversationId];
  let cursorClause = '';
  if (parsed.cursor) {
    const c = decodeTimestampIdCursor(parsed.cursor);
    values.push(c.ts, c.id);
    cursorClause = `AND (created_at, id) < ($2, $3)`;
  }
  values.push(limit + 1);

  const { rows } = await ctx.db.query<MessageRow>(
    `SELECT * FROM messages WHERE conversation_id = $1 ${cursorClause} ORDER BY created_at DESC, id DESC LIMIT $${values.length}`,
    values,
  );

  const hasMore = rows.length > limit;
  const pageRows = hasMore ? rows.slice(0, limit) : rows;
  const items = pageRows.map(mapRow);
  const last = items[items.length - 1]!;
  const nextCursor = hasMore ? encodeTimestampIdCursor(last.createdAt, last.id) : null;
  return { items, nextCursor };
}

/** Marks every message in the conversation up to and including `uptoMessageId` as read for the caller. */
export async function markRead(ctx: Ctx, conversationId: string, uptoMessageId: string): Promise<void> {
  const { userId } = requireUserActor(ctx);
  await conversationService.getConversation(ctx, conversationId); // authorizes participant

  const now = ctx.clock.now();
  await ctx.db.query(
    `UPDATE messages
     SET read_at = $1
     WHERE conversation_id = $2
       AND sender_id <> $3
       AND read_at IS NULL
       AND created_at <= (SELECT created_at FROM messages WHERE id = $4 AND conversation_id = $2)`,
    [now, conversationId, userId, uptoMessageId],
  );
}

/** Messages the caller has sent in the last rolling hour, for the §12.3 rate limit check. Exposed separately so `message.sendMessage`'s guard is unit-testable without sending a real message. */
export async function countMessagesInLastHour(ctx: Ctx, userId: string): Promise<number> {
  const now = ctx.clock.now();
  const hourAgo = new Date(now.getTime() - 60 * 60 * 1000);
  const { rows } = await ctx.db.query<{ count: string }>(
    `SELECT count(*)::text AS count FROM messages WHERE sender_id = $1 AND created_at >= $2`,
    [userId, hourAgo],
  );
  return Number(rows[0]!.count);
}

/** Link-flagged messages sent by the caller in the last rolling hour, for the trust-tiered §12.3/§19.4 limit. Counts every link-flagged message in the window (clickable or not), so the quota actually sticks once exhausted rather than resetting every message. */
export async function countLinksInLastHour(ctx: Ctx, userId: string): Promise<number> {
  const now = ctx.clock.now();
  const hourAgo = new Date(now.getTime() - 60 * 60 * 1000);
  const { rows } = await ctx.db.query<{ count: string }>(
    `SELECT count(DISTINCT m.id)::text AS count
     FROM messages m
     JOIN message_flags mf ON mf.message_id = m.id AND mf.flag_type = 'link'
     WHERE m.sender_id = $1 AND m.created_at >= $2`,
    [userId, hourAgo],
  );
  return Number(rows[0]!.count);
}
