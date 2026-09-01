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
import { outgoingInterestPendingLimitFor } from './trust.service.js';
import { evaluateMutualEligibility } from './eligibility.service.js';

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
 *
 * ---------------------------------------------------------------------
 * MUTUAL-ELIGIBILITY ENFORCEMENT (this build; product-owner requirement
 * from user testing — see this build's report):
 * ---------------------------------------------------------------------
 * §9.1/§9.4's hard-filter guarantee ("filters MUST be enforced strictly",
 * "mutual filter passing") is discovery's job at browse time (Layer 1,
 * `discovery.service.ts`, unmodified by this build — verified, not
 * rebuilt, by `tests/unit/eligibility.test.ts`). But a stale grid, or a
 * direct profile link, bypasses Layer 1 entirely. One more layer closes
 * that gap, built on the shared check in
 * `eligibility.service.ts#evaluateMutualEligibility` (which itself just
 * wraps `filter.service#passesMutualFilters` — never a second, divergent
 * implementation):
 *
 *  - LAYER 2 (`sendInterest`, below): re-evaluates mutual eligibility
 *    FRESH, immediately before the interest row is inserted. If the
 *    recipient's current hard filters would exclude the sender (or vice
 *    versa), NO ROW IS CREATED — so the sender's outgoing-pending slot
 *    and daily quota are never consumed by a refused send (both are
 *    counted by querying existing rows; nothing to free if nothing was
 *    written). The refusal is `RECIPIENT_UNAVAILABLE_MESSAGE` — the
 *    EXACT SAME static copy and error shape already used for "recipient
 *    inbox full"/"recipient at conversation cap" a few lines below, on
 *    purpose: an attacker probing someone's filters by sending interests
 *    and reading error text cannot distinguish "your filters exclude
 *    them", "their inbox is full", or "they're at their chat cap" from
 *    each other, let alone learn *which* filter/attribute was involved —
 *    `evaluateMutualEligibility` never returns that detail even
 *    internally. This only ever affects an interest that does not exist
 *    yet — it never touches a row already sitting in the table.
 *
 * ---------------------------------------------------------------------
 * CORRECTION (product owner, after the original build shipped) — read
 * this before touching anything below labeled "cleanup":
 * ---------------------------------------------------------------------
 * The original build also had a "Layer 3": any time a recipient's
 * filters changed, every PENDING incoming interest their new filters now
 * excluded was retroactively auto-declined, intended to run inline right
 * after every filter save. That was a mistake, and it has been removed
 * along with any wiring that would run it as a consequence of a filter
 * update.
 *
 * The reasoning, preserved here so it isn't rediscovered the hard way:
 * people change their filters constantly, for completely ordinary
 * reasons — someone overwhelmed by too many options narrows things down
 * for a while, then widens the filter back out later. A filter is a
 * statement about what a person wants to see going FORWARD; it is not,
 * and must never become, a retroactive judgment on interests that
 * already exist. Auto-declining on a filter change destroys pending
 * likes and (had it ever run against something already accepted, which
 * it never did — see the test coverage) would have put conversations at
 * risk too, for a reason the other person never did anything wrong to
 * cause. That is a materially worse outcome than a slightly-stale inbox.
 *
 * What auto-decline was ever actually FOR — keeping a new batch of
 * incoming likes close to a "yes" so ten likes reads as ten real
 * prospects, not a chore — is fully delivered by LAYER 2 above, which
 * only ever refuses a send that hasn't happened yet. Nothing already
 * sitting in a recipient's inbox needs to be touched for that guarantee
 * to hold.
 *
 * What's left of the old Layer 3 is `previewFilterCleanup` /
 * `runFilterCleanup` at the bottom of this file: a real capability (a
 * user narrowed their filters and genuinely wants to tidy a now-stale
 * inbox), but now strictly OPT-IN — a user deliberately invokes it on
 * their own inbox (see `src/http/routes/filters.routes.ts`'s
 * `/me/filters/cleanup*` routes), it is never called as a side effect of
 * `filter.service.ts#updateMyFilters` or anything else, and nothing
 * schedules it (`src/jobs/**` has no entry for it — there is nothing to
 * schedule). `decline_origin = 'auto'` (see
 * `db/migrations/010_eligibility.sql`) is still stamped on a row this
 * declines, distinguishing a user-invoked cleanup decline from a real
 * `'human'` recipient decline, so trust scoring/analytics can tell them
 * apart and a cleanup decline never feeds the sender's trust score
 * negatively — exactly the same non-punitive treatment the old Layer 3
 * gave it, just now only ever triggered by the recipient's own
 * deliberate action. The sender sees the identical generic
 * `interest_declined` notification either way (§11.4 "They passed on
 * this match.") — `decline_origin` is never read by, or exposed through,
 * any Interest-shaped return value in this file.
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
  /**
   * `'human'` for a real recipient decline, `'auto'` for a recipient's
   * own deliberately-invoked `runFilterCleanup` (see the file-level
   * "CORRECTION" note — never written as a side effect of a filter
   * update or by any job), `null` for every non-declined row (see
   * `db/migrations/010_eligibility.sql`). Deliberately NOT read by
   * `mapRow` below — this column is internal bookkeeping for trust
   * scoring/analytics (read directly off this table, same pattern
   * `discovery.service.ts` already uses), never part of the `Interest`
   * shape returned to any caller, so a sender can never learn from any
   * API response whether a decline was automatic.
   */
  decline_origin: 'human' | 'auto' | null;
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
  const { userId, trustLevel } = requireUserActor(ctx);
  const parsedRecipientId = RecipientIdSchema.parse(recipientId);

  if (parsedRecipientId === userId) {
    throw new ValidationError('Cannot send an interest to yourself.');
  }

  // LAYER 2 mutual-eligibility gate (see file-level "MUTUAL-ELIGIBILITY
  // ENFORCEMENT" note): checked BEFORE any of the capacity queries below,
  // and — critically — before the INSERT further down, so a refused send
  // never consumes the sender's outgoing-pending slot or daily quota.
  // Fresh evaluation every call, never a cached discovery grid.
  const eligibility = await evaluateMutualEligibility(ctx, userId, parsedRecipientId);
  if (!eligibility.eligible) {
    // Deliberately the SAME message/shape as the capacity-based refusals
    // below (`RECIPIENT_UNAVAILABLE_MESSAGE`) — see file-level doc: this
    // must never let a sender distinguish "your filters exclude them"
    // from any other reason a send didn't go through, and must never
    // name a filter key or attribute.
    throw new RateLimitError(RECIPIENT_UNAVAILABLE_MESSAGE, { kind: 'recipient_unavailable' });
  }

  const now = ctx.clock.now();

  // Decision-layer addition (Open Question OQ-4, see docs/conformance.md):
  // §6.4's "Send interests: limited" restriction table cell now has a
  // concrete, smaller cap for Limited-trust senders —
  // `trust.outgoingInterestPendingLimitFor` buckets on trustLevel so this
  // module doesn't re-derive the trust-tier comparison itself (same
  // pattern as `trust.linksPerHourLimitFor`).
  const [outgoingLimit, dailyLimit, incomingLimitForRecipient, activeConvoLimit] = await Promise.all([
    outgoingInterestPendingLimitFor(ctx, trustLevel),
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
  // `to === 'declined'` is always the RECIPIENT explicitly declining via
  // this path (see `declineInterest` below) — the opt-in filter-cleanup
  // decline never goes through `atomicTransition`, it has its own UPDATE
  // that stamps `decline_origin = 'auto'` instead (see
  // `runFilterCleanup`/`autoDeclineOne` below). So a real human decline
  // unconditionally stamps 'human' here.
  const originClause = to === 'declined' ? `, decline_origin = 'human'` : '';

  const { rows } = await ctx.db.query<InterestRow>(
    `UPDATE interests SET status = $1, ${stampColumn} = $2${originClause}
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

// ---------------------------------------------------------------------
// Opt-in inbox cleanup (see file-level "CORRECTION" note above). Two
// functions only, both scoped to the CALLING user's own inbox — neither
// takes a `recipientId` parameter, so neither can be pointed at anyone
// else's interests:
//
//   - `previewFilterCleanup` — read-only, no mutation. Tells the caller
//     how many of their own PENDING incoming interests their CURRENT
//     filters would decline, so they can see the count BEFORE deciding
//     to run it.
//   - `runFilterCleanup` — actually declines exactly that set.
//
// Neither is called from anywhere else in this codebase:
// `filter.service.ts#updateMyFilters` has no reference to either, and
// `src/jobs/**` has no entry for either — a user must explicitly invoke
// one (see `src/http/routes/filters.routes.ts`'s `/me/filters/cleanup*`
// routes) for anything to happen. Not a §25 job in INTERFACES.md's
// original list, and deliberately never becomes one.
// ---------------------------------------------------------------------

interface PendingIncomingRow {
  id: string;
  sender_id: string;
}

/** Every PENDING interest addressed to `recipientId` — just enough (`id`, `sender_id`) to re-check eligibility and decline per row without pulling full `Interest` data this never returns to anyone. */
async function loadPendingIncoming(ctx: Ctx, recipientId: string): Promise<PendingIncomingRow[]> {
  const { rows } = await ctx.db.query<PendingIncomingRow>(
    `SELECT id, sender_id FROM interests WHERE recipient_id = $1 AND status = 'pending'`,
    [recipientId],
  );
  return rows;
}

/**
 * Declines exactly one interest with `decline_origin = 'auto'`, guarded
 * atomically by `WHERE status = 'pending'` (same discipline as
 * `atomicTransition`) — if the row was concurrently accepted, canceled,
 * expired, or already declined by the time this UPDATE runs, it matches
 * zero rows and this is a silent no-op (idempotent: nothing left to do).
 * Notifies the sender with the IDENTICAL generic `interest_declined`
 * event/template a real human decline uses (§11.4 "They passed on this
 * match.") — `decline_origin` never appears in the notification payload,
 * so the sender cannot learn this was a cleanup decline rather than a
 * personal one.
 */
async function autoDeclineOne(ctx: Ctx, interestId: string, senderId: string): Promise<boolean> {
  const now = ctx.clock.now();
  const { rowCount } = await ctx.db.query(
    `UPDATE interests SET status = 'declined', declined_at = $1, decline_origin = 'auto'
     WHERE id = $2 AND status = 'pending'`,
    [now, interestId],
  );
  if (!rowCount) return false;

  await notificationService.notify(ctx, {
    userId: senderId,
    eventType: 'interest_declined',
    channel: 'in_app',
    payload: { interestId },
  });
  return true;
}

/**
 * Read-only preview for the opt-in inbox cleanup: re-evaluates every one
 * of the CALLING user's own PENDING incoming interests against their
 * CURRENT hard filters — via the exact same
 * `eligibility.service#evaluateMutualEligibility` Layer 2 relies on — and
 * counts how many a `runFilterCleanup` call would decline right now.
 * Never writes anything; safe to call as often as the user opens their
 * filter-cleanup screen, including immediately after saving a filter
 * change, without side effects. This is what lets the UI say "this would
 * decline 3 pending likes" BEFORE the user confirms.
 */
export async function previewFilterCleanup(ctx: Ctx): Promise<{ wouldDecline: number }> {
  const { userId } = requireUserActor(ctx);
  const pending = await loadPendingIncoming(ctx, userId);
  let wouldDecline = 0;
  for (const row of pending) {
    const { eligible } = await evaluateMutualEligibility(ctx, row.sender_id, userId);
    // `eligible` is also `true` when evaluation errored (fail-open — see
    // eligibility.service.ts's doc): either way, don't count this row as
    // "would decline" rather than risk overstating what cleanup would do.
    if (!eligible) wouldDecline++;
  }
  return { wouldDecline };
}

/**
 * Executes the opt-in inbox cleanup the user just previewed: declines
 * every one of the CALLING user's own PENDING incoming interests that
 * their CURRENT hard filters exclude, and leaves every other row —
 * eligible pending interests, and anything already accepted/declined/
 * expired/canceled — completely untouched. Only ever invoked explicitly
 * (see the section-level note above); never a consequence of a filter
 * update, never scheduled.
 *
 * An interest that was eligible when sent and REMAINS eligible is never
 * written to at all (no UPDATE even attempted) — it survives untouched,
 * including its `status`/`declined_at`/`decline_origin` all staying
 * exactly as they were.
 *
 * IDEMPOTENT / SAFE TO RE-RUN: only ever reads/writes rows currently
 * `status = 'pending'`; a row this call declines is no longer pending, so
 * calling this again — filters unchanged, or changed again — is always a
 * no-op for that row. Fresh per-interest evaluation (not batched) matches
 * `filter.service.ts#subjectPassesFiltersOf`'s existing per-candidate
 * query pattern; introducing a bulk mutual-filter primitive there is out
 * of this build's file ownership.
 */
export async function runFilterCleanup(ctx: Ctx): Promise<{ declined: number }> {
  const { userId } = requireUserActor(ctx);
  const pending = await loadPendingIncoming(ctx, userId);
  let declined = 0;
  for (const row of pending) {
    const { eligible } = await evaluateMutualEligibility(ctx, row.sender_id, userId);
    // `eligible` is also `true` when evaluation errored (fail-open — see
    // eligibility.service.ts's doc): either way, leave this row pending
    // untouched rather than risk declining a legitimate interest.
    if (eligible) continue;
    if (await autoDeclineOne(ctx, row.id, row.sender_id)) declined++;
  }
  return { declined };
}
