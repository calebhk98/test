import { z } from 'zod';
import type { Ctx } from '../lib/ctx.js';
import { ValidationError } from '../lib/errors.js';
import type { DateProposalStatus, Page } from '../domain/types.js';
import * as conversationService from './conversation.service.js';

/**
 * timeline.service, the merged conversation timeline (product-owner
 * finding #2/#3: "a date proposal is invisible in the chat" / "declining
 * is ambiguous").
 *
 * Not part of INTERFACES.md's frozen module table, a post-foundation
 * addition. Its own "may call" boundary:
 *
 *   timeline -> conversation (read only: `getConversation`, for the
 *               participant/existence authorization check, identical
 *               guard every other conversation-scoped read in this
 *               codebase uses)
 *
 * Everything else this file needs (`messages`, `date_proposals`,
 * `payment_ledger`, `venues`) is read directly with plain SQL, in ONE
 * query per page, see "WHY ONE SQL QUERY, NOT N SERVICE CALLS" below.
 *
 * =====================================================================
 * EVENT MODEL, DERIVED, NOT DUPLICATED
 * =====================================================================
 * Every date-proposal lifecycle event is read straight off the SAME
 * `date_proposals` row `dateProposal.service.ts` (read-only to this
 * build) already maintains, `created_at`/`accepted_at`/`declined_at`/
 * `expired_at`/`canceled_at`/`ticketed_at`/`completed_at`. There is no
 * second table storing "a date was proposed/accepted/..." as its own
 * fact; a timeline row is a VIEW over columns that already exist, so it
 * cannot drift from the proposal's real state the way a duplicated copy
 * could.
 *
 * The one exception, and why it needed one: `payment_failed` (spec §13.3)
 * is the only proposal status with NO timestamp column at all on
 * `date_proposals`, `dateProposal.service.ts#setStatus` is called for it
 * with no `timestampColumn` argument (see that file). Since that file is
 * read-only to this build, there was no way to add
 * `payment_failed_at` and have it ever get stamped. Rather than invent a
 * new stored "timeline events" table (which the task brief explicitly
 * steers away from unless nothing else works), this file reuses a
 * timestamp that ALREADY exists for exactly this transition:
 * `payment.service.ts#authorizeHold`/`captureHold` unconditionally record
 * a `payment_ledger` row for both success AND failure (see that module's
 * doc, "the attempt is part of the audit trail even when declined").
 * The failing `authorization`/`capture` ledger row's `created_at` is
 * written in the SAME synchronous call, immediately before
 * `dateProposal.service.ts` persists `status = 'payment_failed'`, so it
 * is, in practice, the payment-failure moment. See the caveat below.
 *
 * CAVEAT (documented, not hidden): `payment_ledger.created_at` is
 * deliberately the column's own SQL `now()` default, NOT `ctx.clock.now()`
 * `ledger.service.ts`'s own header explains why (the ledger is a
 * forensic audit trail that must reflect real physical write order, not a
 * test's simulated clock). Every OTHER timestamp this file reads
 * (`date_proposals.*_at`, `messages.created_at`) IS `ctx.clock`-stamped.
 * In production (`SystemClock`) this is a no-op distinction. In a test
 * using `ManualClock` set away from real wall-clock time, a
 * `payment_failed` event's `occurredAt` will not necessarily interleave
 * correctly against `ManualClock`-driven neighbors, a pre-existing
 * constraint of `ledger.service.ts`'s design (see its header) that this
 * file inherits rather than introduces, since neither
 * `dateProposal.service.ts` nor `ledger.service.ts` is this build's to
 * change. This build's own tests assert `payment_failed` events on their
 * own terms (present, correctly typed, correct `dateProposalId`) rather
 * than asserting strict interleaving against `ManualClock`-timestamped
 * siblings.
 *
 * SCOPE (deliberate, documented): `no_show` and `disputed` (spec §13.3)
 * are likewise stamped nowhere on `date_proposals`, and, unlike
 * `payment_failed`, correspond to no reliable, uniquely-matchable
 * `payment_ledger` row either (a no-show may refund $0 on the no-show
 * side, and a dispute involves no payment operation at all). The task's
 * required lifecycle-event list (proposed / accepted / declined /
 * cancelled / expired / payment failed / ticket issued / completed) does
 * not include them, so this file does not emit them rather than guess at
 * a timestamp. Flagged here for whoever next owns `dateProposal.service.ts`:
 * the durable fix is a `no_show_at`/`disputed_at` column stamped via
 * `ctx.clock` at the point of transition.
 *
 * `refunded` gets its own event type (`date_refunded`, distinct from
 * `date_canceled`) even though both share the same `canceled_at` column
 * (`dateProposal.service.ts#cancelDateProposal` reuses one column for
 * both terminal outcomes, see that file), this file branches on the
 * row's current `status` to label the shared timestamp correctly rather
 * than collapsing a full refund and a bare cancellation into one copy.
 *
 * =====================================================================
 * WHY ONE SQL QUERY, NOT N SERVICE CALLS
 * =====================================================================
 * A conversation's timeline interleaves two very differently-shaped,
 * differently-sized streams: potentially thousands of messages, and a
 * handful of date-proposal lifecycle events per proposal. Cursor
 * pagination over their MERGE has to be a single ordered sequence, computed
 * where the data lives, fetching "all messages" into memory to merge in
 * JS would defeat the entire point of pagination. So this file builds one
 * `UNION ALL` of every (kind, occurred_at) pair for the conversation, then
 * applies the identical keyset-pagination pattern every other cursor in
 * this codebase uses (see `message.service.ts#listMessages`): a compound
 * `(occurred_at, event_key) < (cursorTs, cursorKey)` predicate plus a
 * matching `ORDER BY ... DESC LIMIT n+1` to detect a next page.
 * `event_key` (`kind || ':' || id`) exists because the same
 * `dateProposalId` legitimately appears as the anchor for several
 * DIFFERENT rows (its `proposed` row and its `accepted` row share an id
 * but are different events), `kind` disambiguates them for the tie-break.
 *
 * Only the PAGE actually being returned (≤ `limit` rows) triggers a
 * second, small batch-hydration query per referenced proposal/venue/
 * message id, never a full-table scan.
 *
 * =====================================================================
 * CONSISTENCY ACROSS PARTICIPANTS
 * =====================================================================
 * The underlying query is keyed only by `conversationId`, it does not
 * branch on `ctx.actor`/viewer identity at all (viewer-relative rendering,
 * e.g. "you proposed this" vs "they proposed this", is left to the client
 * comparing `proposerId`/`senderId` against its own userId, exactly how
 * `message.service.ts#Message.senderId` already works). So the proposer
 * and the recipient necessarily see the identical set of events in the
 * identical order, there is no code path that could show one side an
 * event the other doesn't get. `tests/unit/timeline.test.ts` asserts this
 * directly (fetch as both participants, compare).
 *
 * =====================================================================
 * WHAT THIS FILE DELIBERATELY OMITS FROM EVERY EVENT PAYLOAD
 * =====================================================================
 * No payment card data (no `payment_holds`/`payment_methods` columns are
 * ever read here), no exact venue coordinates (`venues.latitude`/
 * `longitude` are never selected, only `name`; the task's own field list
 * for a proposal card is "venue name, the date and time, and the current
 * status"), and no raw voucher payload/QR/signature (no `vouchers` row is
 * ever read, "a ticket exists" is derived purely from
 * `date_proposals.ticketed_at` being non-null as of a given event's
 * timestamp, via `hasTicket` below, never from the voucher table itself).
 *
 * Every system event card is STATIC, typed data (`kind` + structured
 * fields like `venueName`/`scheduledStart`/`status`), this file emits no
 * prose string anywhere. Rendering "Date proposed at The Daily Grind,
 * Sat 6:00 PM" (or any other copy) from those typed fields is the
 * client's job, exactly like `notification.service.ts`'s
 * `templateKey` + `payload` split.
 */

export type DateProposalEventKind =
  | 'date_proposed'
  | 'date_accepted'
  | 'date_declined'
  | 'date_expired'
  | 'date_canceled'
  | 'date_refunded'
  | 'date_payment_failed'
  | 'date_ticketed'
  | 'date_completed';

export interface TimelineMessageEvent {
  kind: 'message';
  /** `messages.id`. */
  id: string;
  occurredAt: string; // ISO-8601 UTC
  conversationId: string;
  senderId: string;
  body: string;
  readAt: string | null; // ISO-8601 UTC, or null if unread
}

export interface TimelineDateProposalEvent {
  kind: DateProposalEventKind;
  /** `date_proposals.id`, stable across every event this one proposal produces. */
  id: string;
  occurredAt: string; // ISO-8601 UTC
  conversationId: string;
  dateProposalId: string;
  proposerId: string;
  recipientId: string;
  venueName: string;
  scheduledStart: string; // ISO-8601 UTC
  scheduledEnd: string; // ISO-8601 UTC
  /** The proposal's status AS OF this specific event (see module doc), not necessarily its current status. */
  status: DateProposalStatus;
  /** Whether a ticket existed as of this event's moment, `ticketed_at IS NOT NULL AND ticketed_at <= occurredAt`. Never the voucher's own payload/QR, see module doc. */
  hasTicket: boolean;
}

export type TimelineEvent = TimelineMessageEvent | TimelineDateProposalEvent;

// =====================================================================
// Row shapes
// =====================================================================

interface MergedEventRow {
  proposal_id: string | null;
  message_id: string | null;
  kind: 'message' | DateProposalEventKind;
  occurred_at: Date;
}

interface DateProposalHydrationRow {
  id: string;
  proposer_id: string;
  recipient_id: string;
  venue_id: string;
  scheduled_start: Date;
  scheduled_end: Date;
  status: DateProposalStatus;
  ticketed_at: Date | null;
}

interface MessageHydrationRow {
  id: string;
  conversation_id: string;
  sender_id: string;
  body: string;
  created_at: Date;
  read_at: Date | null;
}

// =====================================================================
// Cursor pagination (private to this module, same pattern as every
// other cursor in this codebase; see module doc "WHY ONE SQL QUERY").
// =====================================================================

function encodeCursor(occurredAt: Date, eventKey: string): string {
  return Buffer.from(`${occurredAt.toISOString()}|${eventKey}`, 'utf8').toString('base64url');
}

function decodeCursor(cursor: string): { occurredAt: Date; eventKey: string } {
  const [iso, ...rest] = Buffer.from(cursor, 'base64url').toString('utf8').split('|');
  const eventKey = rest.join('|');
  if (!iso || !eventKey) throw new ValidationError('Invalid pagination cursor.');
  const occurredAt = new Date(iso);
  if (Number.isNaN(occurredAt.getTime())) throw new ValidationError('Invalid pagination cursor.');
  return { occurredAt, eventKey };
}

function eventKeyFor(row: MergedEventRow): string {
  return `${row.kind}:${row.proposal_id ?? row.message_id}`;
}

const GetTimelineParamsSchema = z.object({
  cursor: z.string().optional(),
  limit: z.number().int().min(1).max(200).optional(),
});

export interface GetConversationTimelineParams {
  cursor?: string;
  limit?: number;
}

// Every UNION branch below shares this shape: (proposal_id, message_id, kind, occurred_at).
// `date_payment_failed` is derived from `payment_ledger`, see module doc
// "EVENT MODEL, DERIVED, NOT DUPLICATED" for exactly why and its caveat.
const MERGED_EVENTS_CTE = `
  WITH events AS (
    SELECT dp.id AS proposal_id, NULL::uuid AS message_id, 'date_proposed'::text AS kind, dp.created_at AS occurred_at
      FROM date_proposals dp WHERE dp.conversation_id = $1

    UNION ALL
    SELECT dp.id, NULL, 'date_accepted', dp.accepted_at
      FROM date_proposals dp WHERE dp.conversation_id = $1 AND dp.accepted_at IS NOT NULL

    UNION ALL
    SELECT dp.id, NULL, 'date_declined', dp.declined_at
      FROM date_proposals dp WHERE dp.conversation_id = $1 AND dp.declined_at IS NOT NULL

    UNION ALL
    SELECT dp.id, NULL, 'date_expired', dp.expired_at
      FROM date_proposals dp WHERE dp.conversation_id = $1 AND dp.expired_at IS NOT NULL

    UNION ALL
    SELECT dp.id, NULL, CASE WHEN dp.status = 'refunded' THEN 'date_refunded' ELSE 'date_canceled' END, dp.canceled_at
      FROM date_proposals dp WHERE dp.conversation_id = $1 AND dp.canceled_at IS NOT NULL

    UNION ALL
    SELECT dp.id, NULL, 'date_ticketed', dp.ticketed_at
      FROM date_proposals dp WHERE dp.conversation_id = $1 AND dp.ticketed_at IS NOT NULL

    UNION ALL
    SELECT dp.id, NULL, 'date_completed', dp.completed_at
      FROM date_proposals dp WHERE dp.conversation_id = $1 AND dp.completed_at IS NOT NULL

    UNION ALL
    SELECT dp.id, NULL, 'date_payment_failed', pf.created_at
      FROM date_proposals dp
      JOIN LATERAL (
        SELECT pl.created_at
        FROM payment_ledger pl
        WHERE pl.date_proposal_id = dp.id
          AND (
            (pl.type = 'authorization' AND pl.metadata->>'status' = 'failed')
            OR (pl.type = 'capture' AND pl.metadata->>'status' IS DISTINCT FROM 'captured')
          )
        ORDER BY pl.created_at ASC
        LIMIT 1
      ) pf ON true
      WHERE dp.conversation_id = $1 AND dp.status = 'payment_failed'

    UNION ALL
    SELECT NULL, m.id, 'message', m.created_at
      FROM messages m WHERE m.conversation_id = $1
  ),
  keyed AS (
    SELECT *, (kind || ':' || COALESCE(proposal_id, message_id)::text) AS event_key
    FROM events
  )
`;

/**
 * One merged, chronologically-ordered (newest-first, same DESC
 * convention `message.service.ts#listMessages` already uses, so this
 * endpoint and `GET /conversations/:id/messages` never disagree about
 * pagination direction), cursor-paginated stream of every message and
 * date-proposal lifecycle event in `conversationId`. Authorization: only
 * a participant may read it, `conversation.service#getConversation`
 * throws `NotFoundError` for a non-participant/non-existent conversation
 * and `ForbiddenError` for a non-`user` actor (venue staff/admin), which
 * is exactly the "can't tell a chat exists from the outside" + "venue
 * staff never sees chats" behavior every other conversation-scoped read
 * in this codebase already has.
 */
export async function getConversationTimeline(ctx: Ctx, conversationId: string, params?: GetConversationTimelineParams): Promise<Page<TimelineEvent>> {
  await conversationService.getConversation(ctx, conversationId); // authorizes participant + existence
  const parsed = GetTimelineParamsSchema.parse(params ?? {});
  const limit = parsed.limit ?? 50;

  const values: unknown[] = [conversationId];
  let cursorClause = '';
  if (parsed.cursor) {
    const c = decodeCursor(parsed.cursor);
    values.push(c.occurredAt, c.eventKey);
    cursorClause = `AND (occurred_at, event_key) < ($2, $3)`;
  }
  values.push(limit + 1);

  const { rows } = await ctx.db.query<MergedEventRow & { event_key: string }>(
    `${MERGED_EVENTS_CTE}
     SELECT proposal_id, message_id, kind, occurred_at, event_key
     FROM keyed
     WHERE occurred_at IS NOT NULL ${cursorClause}
     ORDER BY occurred_at DESC, event_key DESC
     LIMIT $${values.length}`,
    values,
  );

  const hasMore = rows.length > limit;
  const pageRows = hasMore ? rows.slice(0, limit) : rows;
  const last = pageRows[pageRows.length - 1];
  const nextCursor = hasMore && last ? encodeCursor(last.occurred_at, eventKeyFor(last)) : null;

  const proposalIds = [...new Set(pageRows.map((r) => r.proposal_id).filter((id): id is string => id != null))];
  const messageIds = [...new Set(pageRows.map((r) => r.message_id).filter((id): id is string => id != null))];

  const proposalsById = new Map<string, DateProposalHydrationRow>();
  if (proposalIds.length > 0) {
    const { rows: proposalRows } = await ctx.db.query<DateProposalHydrationRow>(
      `SELECT id, proposer_id, recipient_id, venue_id, scheduled_start, scheduled_end, status, ticketed_at
       FROM date_proposals WHERE id = ANY($1::uuid[])`,
      [proposalIds],
    );
    for (const row of proposalRows) proposalsById.set(row.id, row);
  }

  const venueNamesById = new Map<string, string>();
  const venueIds = [...new Set([...proposalsById.values()].map((p) => p.venue_id))];
  if (venueIds.length > 0) {
    const { rows: venueRows } = await ctx.db.query<{ id: string; name: string }>(`SELECT id, name FROM venues WHERE id = ANY($1::uuid[])`, [venueIds]);
    for (const row of venueRows) venueNamesById.set(row.id, row.name);
  }

  const messagesById = new Map<string, MessageHydrationRow>();
  if (messageIds.length > 0) {
    const { rows: messageRows } = await ctx.db.query<MessageHydrationRow>(
      `SELECT id, conversation_id, sender_id, body, created_at, read_at FROM messages WHERE id = ANY($1::uuid[])`,
      [messageIds],
    );
    for (const row of messageRows) messagesById.set(row.id, row);
  }

  const items: TimelineEvent[] = pageRows.map((row) => {
    if (row.kind === 'message') {
      const m = messagesById.get(row.message_id!)!;
      return {
        kind: 'message',
        id: m.id,
        occurredAt: m.created_at.toISOString(),
        conversationId: m.conversation_id,
        senderId: m.sender_id,
        body: m.body,
        readAt: m.read_at ? m.read_at.toISOString() : null,
      } satisfies TimelineMessageEvent;
    }

    const dp = proposalsById.get(row.proposal_id!)!;
    return {
      kind: row.kind,
      id: dp.id,
      occurredAt: row.occurred_at.toISOString(),
      conversationId,
      dateProposalId: dp.id,
      proposerId: dp.proposer_id,
      recipientId: dp.recipient_id,
      venueName: venueNamesById.get(dp.venue_id) ?? 'Unknown venue',
      scheduledStart: dp.scheduled_start.toISOString(),
      scheduledEnd: dp.scheduled_end.toISOString(),
      status: statusForEvent(row.kind, dp),
      hasTicket: dp.ticketed_at != null && dp.ticketed_at.getTime() <= row.occurred_at.getTime(),
    } satisfies TimelineDateProposalEvent;
  });

  return { items, nextCursor };
}

/**
 * The status label for one event, as of THAT event, not necessarily the
 * proposal's current status (a `date_proposed` card for a since-completed
 * date still says "pending_acceptance", the status it actually had at
 * that moment). See module doc's `date_proposed` caveat for the one rare
 * edge (an immediate draft-stage payment failure) this slightly
 * simplifies rather than fully disambiguates.
 */
function statusForEvent(kind: DateProposalEventKind, dp: DateProposalHydrationRow): DateProposalStatus {
  switch (kind) {
    case 'date_proposed':
      return 'pending_acceptance';
    case 'date_accepted':
      return 'accepted';
    case 'date_declined':
      return 'declined';
    case 'date_expired':
      return 'expired';
    case 'date_canceled':
      return 'canceled';
    case 'date_refunded':
      return 'refunded';
    case 'date_ticketed':
      return 'ticketed';
    case 'date_payment_failed':
      return 'payment_failed';
    case 'date_completed':
      // `completed_at` is shared by both terminal outcomes (§15.3 scan vs
      // §15.4 no-scan fallback), the row's own current status is exactly
      // 'completed' or 'completed_unverified' by the time this fires, so
      // reading it directly (rather than guessing) is correct, not a
      // "current status leaking backward" case like the others above.
      return dp.status;
  }
}
