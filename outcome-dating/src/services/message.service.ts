import type { Ctx } from '../lib/ctx.js';
import { NotImplementedError } from '../lib/errors.js';
import type { Message, Page } from '../domain/types.js';

/**
 * message.service — in-conversation messaging.
 * Spec: §12.2-§12.5, §24.7.
 *
 * Owning agent: C.
 *
 * Invariants:
 *  - Chat unlocks only after mutual match (spec §12.1): `sendMessage`
 *    throws `ForbiddenError` unless the conversation's status is one of
 *    `active`, `cooling`, `established` (never for a conversation the
 *    caller isn't a participant of, and never for `archived`).
 *  - Plain text + emoji only for MVP (spec §12.2) — no attachment/media
 *    fields exist on `messages` and none should be added here.
 *  - Every send calls `textscan.service#scanText`, persists any
 *    `message_flags` rows, and enforces `chat.max_messages_per_hour` and
 *    the trust-tiered `chat.max_links_per_hour_*` config (spec §12.3,
 *    §19.4) — messages are never blocked for flagged *content* by default
 *    (spec §19.3), only rate-limited.
 *  - Off-app handles/links are never blocked outright (spec §12.5) — a
 *    flagged message still sends, with `notification`'s static banner
 *    template attached client-side via `analysisFlags`.
 */

export async function sendMessage(ctx: Ctx, conversationId: string, body: string): Promise<Message> {
  throw new NotImplementedError('message.sendMessage');
}

export async function listMessages(ctx: Ctx, conversationId: string, params?: { cursor?: string; limit?: number }): Promise<Page<Message>> {
  throw new NotImplementedError('message.listMessages');
}

/** Marks every message in the conversation up to and including `uptoMessageId` as read for the caller. */
export async function markRead(ctx: Ctx, conversationId: string, uptoMessageId: string): Promise<void> {
  throw new NotImplementedError('message.markRead');
}

/** Messages the caller has sent in the last rolling hour, for the §12.3 rate limit check. Exposed separately so `message.sendMessage`'s guard is unit-testable without sending a real message. */
export async function countMessagesInLastHour(ctx: Ctx, userId: string): Promise<number> {
  throw new NotImplementedError('message.countMessagesInLastHour');
}

/** Clickable-links sent by the caller in the last rolling hour, for the trust-tiered §12.3/§19.4 limit. */
export async function countLinksInLastHour(ctx: Ctx, userId: string): Promise<number> {
  throw new NotImplementedError('message.countLinksInLastHour');
}
