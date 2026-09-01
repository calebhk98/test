import { z } from 'zod';
import type { Ctx } from '../lib/ctx.js';
import { requireUserActor, withDb } from '../lib/ctx.js';
import { withTransaction } from '../db/tx.js';
import { newId } from '../lib/ids.js';
import { addHours } from '../lib/time.js';
import { ConflictError, ForbiddenError, NotFoundError, RateLimitError, ValidationError } from '../lib/errors.js';
import { INTEREST_POLICY_KEYS } from '../config/config.service.js';
import type { Conversation, Interest, InterestPolicySnapshot, InterestStatus, Page } from '../domain/types.js';
import * as conversationService from './conversation.service.js';
import * as notificationService from './notification.service.js';

/**
 * interest.service — match interests.
 * Spec: §11, §24.6, §25.1 (expiry job).
 *
 * Owning agent: C.
 *
 * Invariants:
 *  - `sendInterest` snapshots policy via
 *    `ctx.config.snapshotPolicy(INTEREST_POLICY_KEYS)` (spec §21.3) into
 *    `interests.policy_snapshot` at creation time — the interest's own
 *    expiry MUST use the snapshotted `interest.expiry_hours`, never a
 *    later-updated config value (spec §21.4 "existing keep original").
 *    The outgoing/incoming pending caps are 'live'-scoped in the config
 *    registry (see config.service.ts's per-key `scope`), so — unlike
 *    expiry — cap *enforcement* always re-reads the current value; only
 *    the stored `policy_snapshot` object is a point-in-time record.
 *  - Enforces, at send time: outgoing pending limit, daily outgoing limit,
 *    and (on the recipient's side) that the recipient's incoming pending
 *    count and active-conversation count are below their limits — mirrors
 *    the discovery visibility rule (§10.2 rules 5-6) so an interest can
 *    never be sent to someone whose inbox/chat load is already full. This
 *    is enforced here via `conversation.countActiveConversationsForUser`
 *    (same agent) rather than `discovery.service#isProfileVisibleTo`
 *    (Agent B, still a stub at the time of writing) — see this module's
 *    section of the final report for the cross-agent wiring note.
 *  - INVARIANT: `acceptInterest` MUST create (or reuse) exactly one
 *    `conversations` row in the same transaction as the status flip to
 *    'accepted' — see `conversation.service#getOrCreateConversation`. A
 *    caller must never observe `interest.status === 'accepted'` without a
 *    conversation existing.
 *  - `declineInterest` never surfaces the decliner's reasoning to the
 *    sender beyond the generic "They passed on this match." template
 *    (spec §11.4) — that copy lives in `notification.service.ts`'s
 *    template registry, not here.
 *  - §11.3 "no free text before match": `sendInterest`'s signature is
 *    `(ctx, recipientId: string)` — there is no options object and no
 *    field anywhere on this call for a message. That is a structural
 *    guarantee (a caller cannot pass free text even by mistake), not a
 *    validated-away one.
 */

// ---------------------------------------------------------------------
// State machine
// ---------------------------------------------------------------------

/**
 * The full legal-transition table (spec §11.4). `pending` is the only
 * non-terminal state; every other state is terminal. Every function below
 * that mutates status goes through `atomicTransition`/the accept-specific
 * transaction, both of which check against this table (via the identical
 * `WHERE status = 'pending'` guard + the error paths in
 * `explainIllegalTransition`) rather than trusting the caller.
 */
export const INTEREST_TRANSITIONS: Readonly<Record<InterestStatus, ReadonlySet<InterestStatus>>> = {
  pending: new Set<InterestStatus>(['accepted', 'declined', 'expired', 'canceled']),
  accepted: new Set<InterestStatus>(),
  declined: new Set<InterestStatus>(),
  expired: new Set<InterestStatus>(),
  canceled: new Set<InterestStatus>(),
};

/** Typed error for every rejected transition (accepting an expired/declined interest, declining twice, cancelling an accepted one, etc). */
export class InterestTransitionError extends ConflictError {
  readonly interestId: string;
  readonly fromStatus: InterestStatus;
  readonly attempted: InterestStatus;

  constructor(interestId: string, fromStatus: InterestStatus, attempted: InterestStatus) {
    const legal = INTEREST_TRANSITIONS[fromStatus];
    const reason =
      legal.size === 0
        ? `"${fromStatus}" is a terminal state`
        : `only {${[...legal].join(', ')}} are reachable from "${fromStatus}"`;
    super(`Interest ${interestId} cannot move from "${fromStatus}" to "${attempted}" — ${reason}.`, {
      interestId,
      fromStatus,
      attempted,
    });
    this.interestId = interestId;
    this.fromStatus = fromStatus;
    this.attempted = attempted;
  }
}

// ---------------------------------------------------------------------
// Static copy (spec §11.4, §30.2) — never generated, always these exact strings.
// ---------------------------------------------------------------------

/** §30.2 exact copy for "user reaches outgoing interest limit". */
export const OUTGOING_LIMIT_REACHED_MESSAGE =
  'You have reached your pending interest limit.\nWait for responses or expiration.';

/** Sender-facing copy when the recipient cannot receive more interests right now (mirrors §30.3's discovery-hiding rule, applied defensively at send time too). */
export const RECIPIENT_UNAVAILABLE_MESSAGE = 'This person cannot receive new interests right now.';

// ---------------------------------------------------------------------
// Row mapping
// ---------------------------------------------------------------------

interface InterestRow {
  id: string;
  sender_id: string;
  recipient_id: string;
  status: InterestStatus;
  policy_snapshot: InterestPolicySnapshot;
  created_at: Date;
  expires_at: Date;
  accepted_at: Date | null;
  declined_at: Date | null;
  canceled_at: Date | null;
  expired_at: Date | null;
}

function mapRow(row: InterestRow): Interest {
  return {
    id: row.id,
    senderId: row.sender_id,
    recipientId: row.recipient_id,
    status: row.status,
    policySnapshot: row.policy_snapshot,
    createdAt: row.created_at,
    expiresAt: row.expires_at,
    acceptedAt: row.accepted_at,
    declinedAt: row.declined_at,
    canceledAt: row.canceled_at,
    expiredAt: row.expired_at,
  };
}

function isUniqueViolation(err: unknown, constraint: string): boolean {
  const pgErr = err as { code?: string; constraint?: string } | null;
  return !!pgErr && pgErr.code === '23505' && pgErr.constraint === constraint;
}

async function fetchInterestRow(ctx: Ctx, interestId: string): Promise<InterestRow | undefined> {
  const { rows } = await ctx.db.query<InterestRow>('SELECT * FROM interests WHERE id = $1', [interestId]);
  return rows[0];
}

interface CountInterestsParams {
  senderId?: string;
  recipientId?: string;
  status?: InterestStatus;
  createdSince?: Date;
}

async function countInterests(ctx: Ctx, params: CountInterestsParams): Promise<number> {
  const clauses: string[] = [];
  const values: unknown[] = [];
  if (params.senderId) {
    values.push(params.senderId);
    clauses.push(`sender_id = $${values.length}`);
  }
  if (params.recipientId) {
    values.push(params.recipientId);
    clauses.push(`recipient_id = $${values.length}`);
  }
  if (params.status) {
    values.push(params.status);
    clauses.push(`status = $${values.length}`);
  }
  if (params.createdSince) {
    values.push(params.createdSince);
    clauses.push(`created_at >= $${values.length}`);
  }
  const where = clauses.length ? `WHERE ${clauses.join(' AND ')}` : '';
  const { rows } = await ctx.db.query<{ count: string }>(`SELECT count(*)::text AS count FROM interests ${where}`, values);
  return Number(rows[0]!.count);
}

// ---------------------------------------------------------------------
// Cursor pagination (private to this module)
// ---------------------------------------------------------------------

function encodeCursor(row: { createdAt: Date; id: string }): string {
  return Buffer.from(`${row.createdAt.toISOString()}|${row.id}`, 'utf8').toString('base64url');
}

function decodeCursor(cursor: string): { createdAt: Date; id: string } {
  const [iso, id] = Buffer.from(cursor, 'base64url').toString('utf8').split('|');
  if (!iso || !id) throw new ValidationError('Invalid pagination cursor.');
  return { createdAt: new Date(iso), id };
}

// ---------------------------------------------------------------------
// sendInterest
// ---------------------------------------------------------------------

const RecipientIdSchema = z.string().uuid({ message: 'recipientId must be a UUID.' });

export async function sendInterest(ctx: Ctx, recipientId: string): Promise<Interest> {
  const { userId } = requireUserActor(ctx);
  const parsedRecipientId = RecipientIdSchema.parse(recipientId);

  if (parsedRecipientId === userId) {
    throw new ValidationError('Cannot send an interest to yourself.');
  }

  const now = ctx.clock.now();

  const [outgoingLimit, dailyLimit, incomingLimitForRecipient, activeConvoLimit] = await Promise.all([
    ctx.config.get('interest.outgoing_pending_limit'),
    ctx.config.get('interest.daily_outgoing_limit'),
    ctx.config.get('interest.incoming_pending_limit'),
    ctx.config.get('chat.active_limit'),
  ]);

  const outgoingPendingCount = await countInterests(ctx, { senderId: userId, status: 'pending' });
  if (outgoingPendingCount >= outgoingLimit) {
    throw new RateLimitError(OUTGOING_LIMIT_REACHED_MESSAGE, { limit: outgoingLimit, kind: 'outgoing_pending' });
  }

  const dayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
  const dailyOutgoingCount = await countInterests(ctx, { senderId: userId, createdSince: dayAgo });
  if (dailyOutgoingCount >= dailyLimit) {
    throw new RateLimitError(OUTGOING_LIMIT_REACHED_MESSAGE, { limit: dailyLimit, kind: 'daily_outgoing' });
  }

  const incomingPendingCount = await countInterests(ctx, { recipientId: parsedRecipientId, status: 'pending' });
  if (incomingPendingCount >= incomingLimitForRecipient) {
    throw new RateLimitError(RECIPIENT_UNAVAILABLE_MESSAGE, { limit: incomingLimitForRecipient, kind: 'incoming_pending' });
  }

  const recipientActiveConvos = await conversationService.countActiveConversationsForUser(ctx, parsedRecipientId);
  if (recipientActiveConvos >= activeConvoLimit) {
    throw new RateLimitError(RECIPIENT_UNAVAILABLE_MESSAGE, { limit: activeConvoLimit, kind: 'active_conversation_cap' });
  }

  const policySnapshot = await ctx.config.snapshotPolicy(INTEREST_POLICY_KEYS);
  const expiresAt = addHours(now, policySnapshot['interest.expiry_hours']);
  const id = newId();

  try {
    const { rows } = await ctx.db.query<InterestRow>(
      `INSERT INTO interests (id, sender_id, recipient_id, status, policy_snapshot, created_at, expires_at)
       VALUES ($1, $2, $3, 'pending', $4::jsonb, $5, $6)
       RETURNING *`,
      [id, userId, parsedRecipientId, JSON.stringify(policySnapshot), now, expiresAt],
    );
    const interest = mapRow(rows[0]!);

    await notificationService.notify(ctx, {
      userId: parsedRecipientId,
      eventType: 'interest_received',
      channel: 'in_app',
      payload: { interestId: interest.id, senderId: userId },
    });

    return interest;
  } catch (err) {
    if (isUniqueViolation(err, 'uq_interests_pending_pair')) {
      throw new ConflictError('You already have a pending interest with this person.');
    }
    throw err;
  }
}

// ---------------------------------------------------------------------
// listOutgoing / listIncoming
// ---------------------------------------------------------------------

const ListParamsSchema = z.object({
  cursor: z.string().optional(),
  limit: z.number().int().min(1).max(100).optional(),
});

async function listInterests(
  ctx: Ctx,
  role: 'sender' | 'recipient',
  params?: { cursor?: string; limit?: number },
): Promise<Page<Interest>> {
  const { userId } = requireUserActor(ctx);
  const parsed = ListParamsSchema.parse(params ?? {});
  const limit = parsed.limit ?? 20;
  const column = role === 'sender' ? 'sender_id' : 'recipient_id';

  const values: unknown[] = [userId];
  let cursorClause = '';
  if (parsed.cursor) {
    const c = decodeCursor(parsed.cursor);
    values.push(c.createdAt, c.id);
    cursorClause = `AND (created_at, id) < ($2, $3)`;
  }
  values.push(limit + 1);

  const { rows } = await ctx.db.query<InterestRow>(
    `SELECT * FROM interests WHERE ${column} = $1 ${cursorClause} ORDER BY created_at DESC, id DESC LIMIT $${values.length}`,
    values,
  );

  const hasMore = rows.length > limit;
  const pageRows = hasMore ? rows.slice(0, limit) : rows;
  const items = pageRows.map(mapRow);
  const nextCursor = hasMore ? encodeCursor(items[items.length - 1]!) : null;
  return { items, nextCursor };
}

export async function listOutgoing(ctx: Ctx, params?: { cursor?: string; limit?: number }): Promise<Page<Interest>> {
  return listInterests(ctx, 'sender', params);
}

export async function listIncoming(ctx: Ctx, params?: { cursor?: string; limit?: number }): Promise<Page<Interest>> {
  return listInterests(ctx, 'recipient', params);
}

// ---------------------------------------------------------------------
// acceptInterest
// ---------------------------------------------------------------------

const InterestIdSchema = z.string().uuid({ message: 'interestId must be a UUID.' });

export async function acceptInterest(
  ctx: Ctx,
  interestId: string,
): Promise<{ interest: Interest; conversation: Conversation }> {
  const { userId } = requireUserActor(ctx);
  InterestIdSchema.parse(interestId);

  return withTransaction(async (db) => {
    const txCtx = withDb(ctx, db);
    const now = txCtx.clock.now();

    // Single atomic UPDATE encodes the entire legal-transition guard for
    // this path: only a 'pending', not-yet-expired interest addressed to
    // this recipient can become 'accepted'.
    const { rows } = await txCtx.db.query<InterestRow>(
      `UPDATE interests SET status = 'accepted', accepted_at = $1
       WHERE id = $2 AND status = 'pending' AND recipient_id = $3 AND expires_at > $1
       RETURNING *`,
      [now, interestId, userId],
    );

    const row = rows[0];
    if (!row) {
      const existing = await fetchInterestRow(txCtx, interestId);
      if (!existing) throw new NotFoundError(`Interest ${interestId} not found.`);
      if (existing.recipient_id !== userId) throw new ForbiddenError('Only the recipient can accept this interest.');
      if (existing.status !== 'pending') throw new InterestTransitionError(interestId, existing.status, 'accepted');
      // status is still 'pending' in the row but expires_at has passed —
      // the expiry job (§25.1) just hasn't swept it yet. Treat exactly
      // like an already-expired interest (spec §11.4): reject.
      throw new InterestTransitionError(interestId, 'expired', 'accepted');
    }

    const interest = mapRow(row);
    const conversation = await conversationService.getOrCreateConversation(txCtx, interest.senderId, interest.recipientId);

    await notificationService.notify(txCtx, {
      userId: interest.senderId,
      eventType: 'interest_accepted',
      channel: 'in_app',
      payload: { interestId: interest.id, conversationId: conversation.id },
    });
    await notificationService.notify(txCtx, {
      userId: interest.senderId,
      eventType: 'chat_opened',
      channel: 'in_app',
      payload: { conversationId: conversation.id },
    });
    await notificationService.notify(txCtx, {
      userId: interest.recipientId,
      eventType: 'chat_opened',
      channel: 'in_app',
      payload: { conversationId: conversation.id },
    });

    return { interest, conversation };
  });
}

// ---------------------------------------------------------------------
// declineInterest / cancelInterest (share one atomic-transition helper)
// ---------------------------------------------------------------------

async function atomicTransition(
  ctx: Ctx,
  interestId: string,
  actorUserId: string,
  role: 'sender' | 'recipient',
  to: 'declined' | 'canceled',
  stampColumn: 'declined_at' | 'canceled_at',
): Promise<InterestRow> {
  const now = ctx.clock.now();
  const roleColumn = role === 'sender' ? 'sender_id' : 'recipient_id';

  const { rows } = await ctx.db.query<InterestRow>(
    `UPDATE interests SET status = $1, ${stampColumn} = $2
     WHERE id = $3 AND status = 'pending' AND ${roleColumn} = $4 AND expires_at > $2
     RETURNING *`,
    [to, now, interestId, actorUserId],
  );
  const row = rows[0];
  if (row) return row;

  const existing = await fetchInterestRow(ctx, interestId);
  if (!existing) throw new NotFoundError(`Interest ${interestId} not found.`);

  const actualOwner = role === 'sender' ? existing.sender_id : existing.recipient_id;
  if (actualOwner !== actorUserId) {
    throw new ForbiddenError(`Only the ${role} may ${to === 'declined' ? 'decline' : 'cancel'} this interest.`);
  }
  if (existing.status !== 'pending') {
    throw new InterestTransitionError(interestId, existing.status, to);
  }
  // Still 'pending' but past expires_at — see the identical note in acceptInterest.
  throw new InterestTransitionError(interestId, 'expired', to);
}

export async function declineInterest(ctx: Ctx, interestId: string): Promise<Interest> {
  const { userId } = requireUserActor(ctx);
  InterestIdSchema.parse(interestId);

  const row = await atomicTransition(ctx, interestId, userId, 'recipient', 'declined', 'declined_at');
  const interest = mapRow(row);

  // §11.4: the sender only ever sees the generic "They passed on this
  // match." template — no decliner reasoning or identity-beyond-what-they
  // already know goes into this payload.
  await notificationService.notify(ctx, {
    userId: interest.senderId,
    eventType: 'interest_declined',
    channel: 'in_app',
    payload: { interestId: interest.id },
  });

  return interest;
}

/** Sender cancels their own pending outgoing interest, freeing their outgoing slot immediately (spec §11.4). */
export async function cancelInterest(ctx: Ctx, interestId: string): Promise<Interest> {
  const { userId } = requireUserActor(ctx);
  InterestIdSchema.parse(interestId);

  const row = await atomicTransition(ctx, interestId, userId, 'sender', 'canceled', 'canceled_at');
  return mapRow(row);
}

// ---------------------------------------------------------------------
// expireDuePendingInterests (§25.1 job)
// ---------------------------------------------------------------------

/** §25.1 job: find pending interests past `expires_at`, mark expired, free the sender's outgoing slot. Runs as `ctx.actor = { type: 'system', job: 'interest_expiry' }`. */
export async function expireDuePendingInterests(ctx: Ctx): Promise<{ expired: number }> {
  const now = ctx.clock.now();
  const { rows } = await ctx.db.query<{ id: string }>(
    `UPDATE interests SET status = 'expired', expired_at = $1
     WHERE status = 'pending' AND expires_at <= $1
     RETURNING id`,
    [now],
  );
  // The sender's outgoing slot is freed automatically: `sendInterest`'s cap
  // check counts `status = 'pending'` rows only, so a row that just flipped
  // to 'expired' stops counting against the cap the instant this commits —
  // no separate bookkeeping needed (spec §11.4, §25.1).
  return { expired: rows.length };
}
