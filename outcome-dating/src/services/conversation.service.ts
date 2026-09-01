import { z } from 'zod';
import type { Ctx } from '../lib/ctx.js';
import { requireUserActor } from '../lib/ctx.js';
import { ForbiddenError, NotFoundError } from '../lib/errors.js';
import { hoursBetween } from '../lib/time.js';
import type { Conversation, ConversationStatus } from '../domain/types.js';
import * as notificationService from './notification.service.js';

/**
 * conversation.service — conversation lifecycle (not message content —
 * see `message.service.ts`).
 * Spec: §12.1, §12.6, §12.7, §23.13, §24.7, §25.3 (decay job).
 *
 * Owning agent: C.
 *
 * Invariants:
 *  - Exactly one conversation per unordered user pair, enforced by the DB
 *    (`uq_conversations_pair` + `conversations_ordered_pair` requiring
 *    `user_a_id < user_b_id`). `getOrCreateConversation` sorts the two ids
 *    before insert/lookup — callers never need to do that ordering
 *    themselves.
 *  - **§12.6-vs-§12.7 precedence, made explicit**: `established` always
 *    wins over decay. This is encoded in exactly one place —
 *    `runChatDecayJob`'s SQL `WHERE c.status IN ('active', 'cooling')` —
 *    so an `established` row is never even a candidate row the job
 *    inspects, rather than being filtered out after the fact in
 *    application code. `establishConversation` is one-directional:
 *    `established` is a terminal state reached only via a completed date
 *    (spec §15.3, §15.4) and never decays, never re-enters
 *    `active`/`cooling`/`archived`.
 */

// ---------------------------------------------------------------------
// Row mapping
// ---------------------------------------------------------------------

interface ConversationRow {
  id: string;
  user_a_id: string;
  user_b_id: string;
  status: ConversationStatus;
  created_at: Date;
  last_message_at: Date | null;
  first_date_completed_at: Date | null;
  archived_at: Date | null;
}

function mapRow(row: ConversationRow): Conversation {
  return {
    id: row.id,
    userAId: row.user_a_id,
    userBId: row.user_b_id,
    status: row.status,
    createdAt: row.created_at,
    lastMessageAt: row.last_message_at,
    firstDateCompletedAt: row.first_date_completed_at,
    archivedAt: row.archived_at,
  };
}

function orderPair(userAId: string, userBId: string): [string, string] {
  return userAId < userBId ? [userAId, userBId] : [userBId, userAId];
}

// ---------------------------------------------------------------------
// getOrCreateConversation
// ---------------------------------------------------------------------

/** Sorts (userAId, userBId) canonically and inserts if missing, else returns the existing row. Called by `interest.service#acceptInterest` inside its transaction. */
export async function getOrCreateConversation(ctx: Ctx, userAId: string, userBId: string): Promise<Conversation> {
  if (userAId === userBId) throw new ForbiddenError('A conversation requires two distinct users.');
  const [a, b] = orderPair(userAId, userBId);
  const now = ctx.clock.now();

  const inserted = await ctx.db.query<ConversationRow>(
    `INSERT INTO conversations (user_a_id, user_b_id, status, created_at)
     VALUES ($1, $2, 'active', $3)
     ON CONFLICT (user_a_id, user_b_id) DO NOTHING
     RETURNING *`,
    [a, b, now],
  );
  if (inserted.rows[0]) return mapRow(inserted.rows[0]);

  // A row already existed for this pair (unique per §23.13 — there is only
  // ever one conversation per user pair, for its whole lifetime). Two cases:
  //  - `established`: never touched, per the precedence rule above — the
  //    UPDATE below only matches 'archived'/'cooling', so it's a no-op for
  //    an established row and we just re-fetch it as-is.
  //  - `archived`/`cooling` from a prior decay cycle: a *new* mutual match
  //    reactivates the conversation to 'active', mirroring §11.4 "recipient
  //    accepts -> conversation = active". `active` rows also fall through
  //    to the no-op re-fetch below (nothing to change).
  const reactivated = await ctx.db.query<ConversationRow>(
    `UPDATE conversations
     SET status = 'active', archived_at = NULL
     WHERE user_a_id = $1 AND user_b_id = $2 AND status IN ('archived', 'cooling')
     RETURNING *`,
    [a, b],
  );
  if (reactivated.rows[0]) return mapRow(reactivated.rows[0]);

  const current = await ctx.db.query<ConversationRow>(`SELECT * FROM conversations WHERE user_a_id = $1 AND user_b_id = $2`, [
    a,
    b,
  ]);
  const row = current.rows[0];
  if (!row) {
    // Should be unreachable (insert-or-reactivate-or-select covers every
    // case) short of a concurrent delete, which nothing in this codebase
    // does — surfaced clearly rather than silently returning undefined.
    throw new NotFoundError(`Conversation between ${a} and ${b} could not be created or found.`);
  }
  return mapRow(row);
}

// ---------------------------------------------------------------------
// listMyConversations / getConversation
// ---------------------------------------------------------------------

const ListMyConversationsSchema = z.object({
  status: z.enum(['active', 'cooling', 'archived', 'established']).optional(),
});

export async function listMyConversations(ctx: Ctx, params?: { status?: Conversation['status'] }): Promise<Conversation[]> {
  const { userId } = requireUserActor(ctx);
  const parsed = ListMyConversationsSchema.parse(params ?? {});

  const values: unknown[] = [userId];
  let statusClause = '';
  if (parsed.status) {
    values.push(parsed.status);
    statusClause = `AND status = $2`;
  }

  const { rows } = await ctx.db.query<ConversationRow>(
    `SELECT * FROM conversations WHERE (user_a_id = $1 OR user_b_id = $1) ${statusClause}
     ORDER BY COALESCE(last_message_at, created_at) DESC`,
    values,
  );
  return rows.map(mapRow);
}

export async function getConversation(ctx: Ctx, conversationId: string): Promise<Conversation> {
  const { userId } = requireUserActor(ctx);
  const { rows } = await ctx.db.query<ConversationRow>('SELECT * FROM conversations WHERE id = $1', [conversationId]);
  const row = rows[0];
  if (!row || (row.user_a_id !== userId && row.user_b_id !== userId)) {
    // Same error for "doesn't exist" and "exists but you're not in it" —
    // don't leak existence of a conversation the caller isn't part of.
    throw new NotFoundError(`Conversation ${conversationId} not found.`);
  }
  return mapRow(row);
}

// ---------------------------------------------------------------------
// archiveConversation (user-initiated, distinct from the decay job)
// ---------------------------------------------------------------------

export async function archiveConversation(ctx: Ctx, conversationId: string): Promise<Conversation> {
  const now = ctx.clock.now();
  const existing = await getConversation(ctx, conversationId); // authorizes participant + existence
  if (existing.status === 'archived') return existing; // idempotent no-op

  const { rows } = await ctx.db.query<ConversationRow>(
    `UPDATE conversations SET status = 'archived', archived_at = $2 WHERE id = $1 RETURNING *`,
    [conversationId, now],
  );
  return mapRow(rows[0]!);
}

// ---------------------------------------------------------------------
// establishConversation (§15.3/§15.4 completion hook)
// ---------------------------------------------------------------------

/** Transitions to 'established' and stamps `first_date_completed_at`. Called by `voucher.service`/`redemption.service`/`dateProposal.service` on date completion (§15.3, §15.4) — never called directly from the HTTP layer. */
export async function establishConversation(ctx: Ctx, conversationId: string): Promise<Conversation> {
  const now = ctx.clock.now();

  // Not gated on `ctx.actor` being a participant: venue-redemption flows
  // run under a `venue_staff`/`system` actor (spec §4.2 — venue staff
  // still trigger this transition even though they can never read the
  // chat itself; `message.service.ts`/`conversation.service.ts` never
  // expose message content to a `venue_staff` actor anywhere).
  const { rows } = await ctx.db.query<ConversationRow>(
    `UPDATE conversations
     SET status = 'established', first_date_completed_at = COALESCE(first_date_completed_at, $2)
     WHERE id = $1 AND status <> 'established'
     RETURNING *`,
    [conversationId, now],
  );
  if (rows[0]) return mapRow(rows[0]);

  // Already established, or didn't exist. `established` is terminal and
  // this call is idempotent by design (redemption retries, or both users
  // confirming the §15.4 no-scan fallback back-to-back, may call this
  // twice for the same conversation) — re-fetch rather than error.
  const current = await ctx.db.query<ConversationRow>('SELECT * FROM conversations WHERE id = $1', [conversationId]);
  const row = current.rows[0];
  if (!row) throw new NotFoundError(`Conversation ${conversationId} not found.`);
  return mapRow(row);
}

// ---------------------------------------------------------------------
// countActiveConversationsForUser — additive export
// ---------------------------------------------------------------------

/**
 * Active (`active`/`cooling`, i.e. NOT `established`) conversation count
 * for `userId` — spec §21.4 `chat.active_limit`, §12.7 "established... do
 * not count against pre-date chat slots". Additive beyond the frozen
 * INTERFACES.md function list (safe: it doesn't change any existing
 * signature). `interest.service#sendInterest` calls this directly for the
 * §10.2 rule 6 capacity gate; `discovery.service.ts` (Agent B) should call
 * it too once its own capacity-check wiring lands — see this module's
 * "may call: discovery (capacity check)" note in INTERFACES.md.
 */
export async function countActiveConversationsForUser(ctx: Ctx, userId: string): Promise<number> {
  const { rows } = await ctx.db.query<{ count: string }>(
    `SELECT count(*)::text AS count FROM conversations WHERE (user_a_id = $1 OR user_b_id = $1) AND status IN ('active', 'cooling')`,
    [userId],
  );
  return Number(rows[0]!.count);
}

// ---------------------------------------------------------------------
// runChatDecayJob (§25.3)
// ---------------------------------------------------------------------

interface DecayCandidateRow {
  id: string;
  status: ConversationStatus;
  user_a_id: string;
  user_b_id: string;
  first_message_at: Date | null;
  has_date_proposal: boolean;
}

/** §25.3 job: prompt at `chat.date_prompt_hours` since first message with no date proposal, cool at `chat.cooling_days` (decision-layer addition — see `docs/conformance.md`; this used to be a local fallback constant because `chat.cooling_days` didn't exist as a config key), archive at `chat.pre_date_archive_days`. Config keys are 'live' (spec §21.4) — this job always reads current values. */
export async function runChatDecayJob(ctx: Ctx): Promise<{ prompted: number; cooled: number; archived: number }> {
  const promptHours = await ctx.config.get('chat.date_prompt_hours');
  const archiveDays = await ctx.config.get('chat.pre_date_archive_days');
  const coolingDays = await ctx.config.get('chat.cooling_days');
  const now = ctx.clock.now();

  // §12.7 precedence, encoded at the SQL level: only 'active'/'cooling'
  // rows are even candidates here. An 'established' conversation is never
  // fetched by this query, so there is no code path in this job that can
  // touch one — "established always wins" is true by construction, not by
  // a runtime check that could be forgotten.
  //
  // `messages`/`date_proposals` are queried directly (read-only) rather
  // than through `message.service.ts` (same agent, no boundary issue) or
  // `dateProposal.service.ts` (Agent D — conversation.service's sanctioned
  // "may call" list per INTERFACES.md does not include `dateProposal`, so
  // a raw existence check against the shared table is the correct way to
  // ask "has a date been proposed for this conversation" without adding an
  // unsanctioned cross-module call).
  const { rows } = await ctx.db.query<DecayCandidateRow>(
    `SELECT
       c.id, c.status, c.user_a_id, c.user_b_id,
       (SELECT min(m.created_at) FROM messages m WHERE m.conversation_id = c.id) AS first_message_at,
       EXISTS (SELECT 1 FROM date_proposals dp WHERE dp.conversation_id = c.id) AS has_date_proposal
     FROM conversations c
     WHERE c.status IN ('active', 'cooling')`,
  );

  let prompted = 0;
  let cooled = 0;
  let archived = 0;

  for (const row of rows) {
    // A date proposal exists (any status) -> this pair already engaged
    // with the structured-date flow; the decay job stops nagging them
    // (spec §12.6's trigger condition for every threshold is "no date
    // proposal").
    if (row.has_date_proposal) continue;
    // No first message yet -> the clock (anchored on "first message" per
    // §12.6) hasn't started.
    if (!row.first_message_at) continue;

    const hoursSinceFirstMessage = hoursBetween(row.first_message_at, now);
    const daysSinceFirstMessage = hoursSinceFirstMessage / 24;

    if (daysSinceFirstMessage >= archiveDays) {
      const { rowCount } = await ctx.db.query(
        `UPDATE conversations SET status = 'archived', archived_at = $2 WHERE id = $1 AND status IN ('active', 'cooling')`,
        [row.id, now],
      );
      if (rowCount) archived++;
      continue;
    }

    if (daysSinceFirstMessage >= coolingDays) {
      if (row.status === 'active') {
        const { rowCount } = await ctx.db.query(`UPDATE conversations SET status = 'cooling' WHERE id = $1 AND status = 'active'`, [
          row.id,
        ]);
        if (rowCount) {
          cooled++;
          await notificationService.notify(ctx, {
            userId: row.user_a_id,
            eventType: 'chat_cooling',
            channel: 'in_app',
            payload: { conversationId: row.id },
          });
          await notificationService.notify(ctx, {
            userId: row.user_b_id,
            eventType: 'chat_cooling',
            channel: 'in_app',
            payload: { conversationId: row.id },
          });
        }
      }
      continue;
    }

    if (hoursSinceFirstMessage >= promptHours) {
      // No persisted state change, and no notification event exists for
      // this in `NotificationEventType` (§20.1 has no "date prompt" entry)
      // — surfaced only via this count for a caller (job runner / API) to
      // act on, e.g. rendering a client-side banner.
      prompted++;
    }
  }

  return { prompted, cooled, archived };
}
