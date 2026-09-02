import { z } from 'zod';
import type { Ctx } from '../lib/ctx.js';
import { requireUserActor } from '../lib/ctx.js';
import type { ConversationStatus, Page } from '../domain/types.js';
import { decodeTimestampIdCursor, encodeTimestampIdCursor } from '../lib/cursor.js';
import * as conversationService from './conversation.service.js';
import * as profileService from './profile.service.js';
import type { ProfilePhotoView } from './profile.service.js';

/**
 * matches.service, "your matches" list (product-owner finding #1: "You
 * cannot see your matches.").
 *
 * Not part of INTERFACES.md's frozen module table (this whole feature is a
 * post-foundation addition), this file's own header documents its "may
 * call" boundary the same way a frozen module's INTERFACES.md row would:
 *
 *   matches -> conversation (read only: `getConversation` for the
 *              single-match lookup's participant/existence check),
 *              profile (read only: `getPublicProfile`, reused verbatim,
 *              never a parallel profile shape, see below)
 *
 * WHAT COUNTS AS A "MATCH": every row in `conversations` the caller is a
 * participant of. A `conversations` row is created in exactly one place in
 * this codebase, `conversation.service#getOrCreateConversation`, called
 * only from `interest.service#acceptInterest` inside its own transaction
 * (see INTERFACES.md's call graph and that module's own header), so its
 * mere existence already encodes "a mutually accepted interest happened
 * between these two users." There is no second, weaker notion of "match"
 * to reconcile here; this file adds no new table and stores no new state.
 *
 * PROFILE REUSE (product-owner finding #1's "click-through to full
 * profile"): each row's `displayName`/`primaryPhotoUrl`/
 * `approximateDistanceKm` are read directly off
 * `profile.service#getPublicProfile`, the exact same value the client
 * would get back from `GET /profiles/:userId`, never a hand-rolled
 * second view. That function already (a) throws if either side has
 * blocked the other (b) never returns raw coordinates, only the
 * server-bucketed `approximateDistanceKm` (c) 404s a deleted account. This
 * file inherits all three for free by calling through it rather than
 * querying `profiles`/`user_photos` directly, which is what makes "do not
 * leak anything the existing view withholds" a structural guarantee, not a
 * convention this file has to remember to uphold. A row whose target user
 * became unreachable that way (blocked either direction, or deleted) is
 * silently OMITTED from the page rather than erroring the whole list,
 * see `listMyMatches` below.
 *
 * ORDERING RULE (documented once, here, since the task asked for it):
 *   sort key = COALESCE(last_message_at, created_at), DESC.
 * "Most recent activity first" for a conversation that has messages means
 * exactly what it says, the last message's time. For a conversation with
 * NO messages yet (a brand-new match nobody has said anything in), there
 * is no message activity to sort by, so it sorts by ITS OWN match time
 * instead. Concretely: a match made ten minutes ago with zero messages
 * sorts ABOVE a conversation whose last message was yesterday, because ten
 * minutes ago is more recent than yesterday, a new match is never buried
 * under older, quieter conversations just because nobody has typed
 * anything yet. This is the identical rule
 * `conversation.service#listMyConversations` already uses for its own
 * ordering (`ORDER BY COALESCE(last_message_at, created_at) DESC`); this
 * file doesn't call that function (it has no cursor support and doesn't
 * return the per-row extras this list needs) but deliberately mirrors its
 * sort key so `/matches` and `/conversations` never disagree about what
 * "most recent" means.
 */

export interface MatchListItem {
  conversationId: string;
  matchedUserId: string;
  displayName: string;
  /** Wiring fix: was `primaryPhotoUrl: string | null`, a bare url discards the photo id a description needs to travel with (see `profile.service.ts#ProfilePhotoView`). `null` when the matched user has no approved photo. */
  primaryPhoto: ProfilePhotoView | null;
  approximateDistanceKm: number | null;
  /** When the mutual match happened, `conversations.created_at` (ISO-8601 UTC). */
  matchedAt: string;
  conversationStatus: ConversationStatus;
  /** Truncated to `MESSAGE_PREVIEW_MAX_CHARS`; `null` if nobody has sent a message yet. */
  lastMessagePreview: string | null;
  /** ISO-8601 UTC; `null` if nobody has sent a message yet. */
  lastMessageAt: string | null;
  /** Messages sent to the caller in this conversation that the caller has not yet read. */
  unreadCount: number;
  /** `COALESCE(lastMessageAt, matchedAt)`, the sort key, exposed so a client never has to re-derive it. ISO-8601 UTC. */
  lastActivityAt: string;
}

const MESSAGE_PREVIEW_MAX_CHARS = 140;

function truncatePreview(body: string): string {
  const trimmed = body.trim();
  if (trimmed.length <= MESSAGE_PREVIEW_MAX_CHARS) return trimmed;
  return `${trimmed.slice(0, MESSAGE_PREVIEW_MAX_CHARS)}…`;
}

interface ConversationRow {
  id: string;
  user_a_id: string;
  user_b_id: string;
  status: ConversationStatus;
  created_at: Date;
  last_message_at: Date | null;
  activity_at: Date;
}

interface LastMessageRow {
  body: string;
  created_at: Date;
}

const ListMyMatchesParamsSchema = z.object({
  cursor: z.string().optional(),
  limit: z.number().int().min(1).max(100).optional(),
});

export interface ListMyMatchesParams {
  cursor?: string;
  limit?: number;
}

/**
 * Every conversation the caller is a participant of (i.e. every match),
 * most-recent-activity-first (see module doc), cursor-paginated. A row is
 * silently dropped from the page (never surfaced as a partial-list error)
 * when `profile.service#getPublicProfile` refuses it, either side has
 * blocked the other, or the matched account was deleted, which can make
 * a page shorter than `limit` even while `nextCursor` is non-null; a
 * client should keep paging on a non-null cursor rather than assume a
 * short page means "no more data."
 */
export async function listMyMatches(ctx: Ctx, params?: ListMyMatchesParams): Promise<Page<MatchListItem>> {
  const { userId } = requireUserActor(ctx);
  const parsed = ListMyMatchesParamsSchema.parse(params ?? {});
  const limit = parsed.limit ?? 20;

  const values: unknown[] = [userId];
  let cursorClause = '';
  if (parsed.cursor) {
    const c = decodeTimestampIdCursor(parsed.cursor);
    values.push(c.ts, c.id);
    cursorClause = `AND (COALESCE(last_message_at, created_at), id) < ($2, $3)`;
  }
  values.push(limit + 1);

  const { rows } = await ctx.db.query<ConversationRow>(
    `SELECT id, user_a_id, user_b_id, status, created_at, last_message_at,
            COALESCE(last_message_at, created_at) AS activity_at
     FROM conversations
     WHERE (user_a_id = $1 OR user_b_id = $1) ${cursorClause}
     ORDER BY COALESCE(last_message_at, created_at) DESC, id DESC
     LIMIT $${values.length}`,
    values,
  );

  const hasMore = rows.length > limit;
  const pageRows = hasMore ? rows.slice(0, limit) : rows;
  const nextCursor = hasMore ? encodeTimestampIdCursor(pageRows[pageRows.length - 1]!.activity_at, pageRows[pageRows.length - 1]!.id) : null;

  const items: MatchListItem[] = [];
  for (const row of pageRows) {
    const matchedUserId = row.user_a_id === userId ? row.user_b_id : row.user_a_id;

    // See module doc "PROFILE REUSE": a block (either direction) or a
    // deleted target account makes this row unreachable, drop it rather
    // than fail the whole page.
    let profile: Awaited<ReturnType<typeof profileService.getPublicProfile>>;
    try {
      profile = await profileService.getPublicProfile(ctx, matchedUserId);
    } catch {
      continue;
    }

    const { rows: lastMessageRows } = await ctx.db.query<LastMessageRow>(
      `SELECT body, created_at FROM messages WHERE conversation_id = $1 ORDER BY created_at DESC, id DESC LIMIT 1`,
      [row.id],
    );
    const lastMessage = lastMessageRows[0];

    const { rows: unreadRows } = await ctx.db.query<{ count: string }>(
      `SELECT count(*)::text AS count FROM messages WHERE conversation_id = $1 AND sender_id <> $2 AND read_at IS NULL`,
      [row.id, userId],
    );

    items.push({
      conversationId: row.id,
      matchedUserId,
      displayName: profile.displayName,
      primaryPhoto: profile.photos[0] ?? null,
      approximateDistanceKm: profile.approximateDistanceKm,
      matchedAt: row.created_at.toISOString(),
      conversationStatus: row.status,
      lastMessagePreview: lastMessage ? truncatePreview(lastMessage.body) : null,
      lastMessageAt: lastMessage ? lastMessage.created_at.toISOString() : null,
      unreadCount: Number(unreadRows[0]!.count),
      lastActivityAt: row.activity_at.toISOString(),
    });
  }

  return { items, nextCursor };
}

/**
 * Single-match detail, authorizes participancy via
 * `conversation.service#getConversation` (throws `NotFoundError` for a
 * conversation the caller isn't in, same "don't leak existence" behavior
 * every other lookup in this codebase uses) and otherwise builds the exact
 * same row shape `listMyMatches` returns, for a client that navigated
 * straight to a conversation and wants the match-card header without
 * re-fetching the whole list.
 */
export async function getMyMatch(ctx: Ctx, conversationId: string): Promise<MatchListItem> {
  const { userId } = requireUserActor(ctx);
  const conversation = await conversationService.getConversation(ctx, conversationId); // authorizes participant + existence

  const matchedUserId = conversation.userAId === userId ? conversation.userBId : conversation.userAId;
  const profile = await profileService.getPublicProfile(ctx, matchedUserId);

  const { rows: lastMessageRows } = await ctx.db.query<LastMessageRow>(
    `SELECT body, created_at FROM messages WHERE conversation_id = $1 ORDER BY created_at DESC, id DESC LIMIT 1`,
    [conversationId],
  );
  const lastMessage = lastMessageRows[0];

  const { rows: unreadRows } = await ctx.db.query<{ count: string }>(
    `SELECT count(*)::text AS count FROM messages WHERE conversation_id = $1 AND sender_id <> $2 AND read_at IS NULL`,
    [conversationId, userId],
  );

  const activityAt = conversation.lastMessageAt ?? conversation.createdAt;

  return {
    conversationId: conversation.id,
    matchedUserId,
    displayName: profile.displayName,
    primaryPhoto: profile.photos[0] ?? null,
    approximateDistanceKm: profile.approximateDistanceKm,
    matchedAt: conversation.createdAt.toISOString(),
    conversationStatus: conversation.status,
    lastMessagePreview: lastMessage ? truncatePreview(lastMessage.body) : null,
    lastMessageAt: lastMessage ? lastMessage.created_at.toISOString() : null,
    unreadCount: Number(unreadRows[0]!.count),
    lastActivityAt: activityAt.toISOString(),
  };
}
