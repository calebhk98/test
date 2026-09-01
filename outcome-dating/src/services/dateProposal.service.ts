import { z } from 'zod';
import { createHash } from 'node:crypto';
import type { Ctx } from '../lib/ctx.js';
import { requireUserActor } from '../lib/ctx.js';
import { ConflictError, ForbiddenError, NotFoundError, PaymentError, ValidationError } from '../lib/errors.js';
import { addHours, hoursBetween } from '../lib/time.js';
import { DATE_PROPOSAL_POLICY_KEYS } from '../config/config.service.js';
import { getPool } from '../db/pool.js';
import type {
  AttendanceConfirmation,
  DateProposal,
  DateProposalPolicySnapshot,
  DateProposalStatus,
  PostDateFeedback,
} from '../domain/types.js';
import * as venueService from './venue.service.js';
import * as paymentService from './payment.service.js';
import * as voucherService from './voucher.service.js';
import * as conversationService from './conversation.service.js';
import * as notificationService from './notification.service.js';
import * as trustService from './trust.service.js';
import * as postDateFeedbackService from './postDateFeedback.service.js';

/**
 * dateProposal.service — the §13-§15 date proposal orchestrator. This is
 * the module every other payment/voucher/conversation piece ultimately
 * serves; it owns the state machine in §13.3 and the payment choreography
 * in §14.2.
 * Spec: §13, §14, §15.4, §24.8, §25.2 (expiry job).
 *
 * Owning agent: D.
 *
 * STATE MACHINE (spec §13.3 + `completed_unverified` from §15.4). See
 * `ALLOWED_TRANSITIONS` below for the literal, enforced table — every
 * status-changing function checks it (via `assertTransition` or the
 * equivalent inline resumability check in `acceptDateProposal`) and throws
 * `ConflictError` on an illegal transition. All nine "resting" states other
 * than the five in-flight ones (`draft`, `pending_acceptance`, `accepted`,
 * `charged`) are effectively terminal (empty transition lists) — see the
 * table for the two deliberate exceptions kept open for defensive/race
 * reasons (`accepted`/`charged` can still be canceled/refunded).
 *
 * PROCESSOR-CALL / DB-TRANSACTION ORDERING — the single most important
 * design decision in this file, spelled out because it looks, at first
 * glance, like it violates "one DB transaction per money operation":
 *
 *   `acceptDateProposal` makes UP TO THREE separate external processor
 *   calls (authorize recipient, capture proposer, capture recipient),
 *   each followed by its OWN short `payment.service.ts`-owned transaction
 *   that persists that one call's result (hold status + ledger entry)
 *   atomically. It deliberately does NOT wrap all three calls plus the
 *   `date_proposals` status writes in one giant transaction, because:
 *
 *     1. A Postgres transaction cannot make an external HTTP call
 *        (`ctx.payments.*`) atomic with a local write — wrapping the calls
 *        in `BEGIN...COMMIT` would only add a false sense of safety while
 *        holding a connection open across slow network calls.
 *     2. Every one of those three calls, plus every proposal-status write
 *        here, is idempotent/resumable (see `payment.service.ts` and the
 *        early-return checks in `acceptDateProposal` below). So if the
 *        process dies between, say, "proposer capture succeeded" and
 *        "recipient capture attempted", the proposal is left sitting in a
 *        real, inspectable, RESUMABLE state (`status = 'accepted'`,
 *        proposer hold `captured`, recipient hold `authorized`) rather
 *        than a rolled-back black hole. Calling `acceptDateProposal` again
 *        (or a retry job) picks up exactly where it left off — it will not
 *        re-authorize, and will not re-capture, the sides that already
 *        succeeded.
 *     3. Any gap this still leaves between "processor moved money" and
 *        "local DB reflects it" is exactly what `ledger.service#
 *        reconcileWithProcessor` (§25.9) exists to detect and flag — never
 *        silently auto-corrected, per that module's invariant.
 *
 *   Within `acceptDateProposal`, the THE central invariant (nobody is
 *   charged unless both sides are captured) is enforced by ordering, not
 *   by a transaction boundary: capture A is only attempted after A and B
 *   are BOTH `authorized`; if capture A fails, B (still merely authorized)
 *   is released; if capture B fails after A already captured, A is
 *   REFUNDED (not released — it already moved real money, so undoing it
 *   is a refund, not a cancel) — see the §14.5 failure branches inline.
 *
 * NOTIFICATIONS/TRUST ARE BEST-EFFORT, NEVER BLOCKING: `notifyBestEffort`/
 * `recordTrustEventBestEffort` below catch and log rather than propagate.
 * This is a deliberate design choice, not a shortcut: a notification-
 * pipeline or trust-scoring outage must never be able to roll back (or
 * even fail) a financial state transition that already succeeded at the
 * processor. `conversation.establishConversation` in `confirmAttendance`
 * is the one cross-module call that is NOT best-effort — spec §15.4 states
 * "conversation = established" as a definite outcome of that path, so it
 * is called (and must succeed) BEFORE the proposal's own status is
 * persisted as `completed_unverified`, so a failure there leaves the
 * proposal safely un-transitioned (still `ticketed`) rather than
 * inconsistent.
 *
 * NOTIFICATION EVENT GAP (RESOLVED, decision layer): `NotificationEventType`
 * used to have no event for "date canceled/refunded/disputed/no-show/
 * completed" — only `date_proposal_received`, `date_accepted`,
 * `payment_hold_authorized`, `payment_failed`, and `ticket_issued` existed.
 * Five events (`date_canceled`, `date_refunded`, `date_disputed`,
 * `date_no_show`, `date_completed`) plus their static templates have since
 * been added (`src/domain/types.ts`, `notification.service.ts`) and this
 * file now fires them at the corresponding transitions, including
 * `cancelDateProposal` and `markNoShow`, which previously sent no
 * notification at all.
 *
 * DECISION-LAYER ADDITIONS (see docs/conformance.md Open Question OQ-3):
 * `sweepTicketedCompletionWindows` and `listDisputesAwaitingAutoResolution`/
 * `markDisputeResolved` below implement "what actually sets `no_show` and
 * how `disputed` gets resolved" — the original spec never said. Both are
 * pure additions to this file's existing state machine/call graph (no new
 * "may call" edges) — the one piece of dispute auto-resolution that DOES
 * need a new edge (filing an implicit report via `report.service.ts`) lives
 * in the separate `disputeResolution.service.ts` instead; see that file's
 * header for why.
 *
 * `payment_holds` LOOKUP: `payment.service.ts`'s frozen export list has no
 * "get the hold for this user on this proposal" function (only
 * `authorizeHold`/`captureHold`/`releaseHold`/`refundHold`, all addressed
 * by hold id). Since this file needs that lookup purely to find an id to
 * pass to those functions — never to mutate state directly — it reads
 * `payment_holds` with a plain `SELECT` (see `getHoldRow` below). This is
 * safe specifically because both `payment.service.ts` and this file are
 * owned by the same agent (D) and every actual status mutation still goes
 * through the sanctioned `payment.service.ts` functions; it would not be
 * safe for a different agent's module to do the same.
 */

// =====================================================================
// State machine
// =====================================================================

const ALLOWED_TRANSITIONS: Record<DateProposalStatus, readonly DateProposalStatus[]> = {
  draft: ['pending_acceptance', 'payment_failed'],
  pending_acceptance: ['accepted', 'declined', 'expired', 'canceled', 'payment_failed'],
  // 'canceled'/'refunded' here cover the narrow race where cancelDateProposal
  // runs between acceptDateProposal persisting 'accepted' and it reaching
  // 'charged' in the same call.
  accepted: ['charged', 'payment_failed', 'canceled', 'refunded'],
  charged: ['ticketed', 'canceled', 'refunded'],
  ticketed: ['completed', 'completed_unverified', 'disputed', 'no_show', 'canceled', 'refunded'],
  declined: [],
  expired: [],
  canceled: [],
  payment_failed: [],
  completed: [],
  completed_unverified: [],
  no_show: [],
  refunded: [],
  disputed: [],
};

function assertTransition(current: DateProposalStatus, next: DateProposalStatus): void {
  if (!ALLOWED_TRANSITIONS[current].includes(next)) {
    // Plain sentence for the wire — `message` reaches the client verbatim
    // (see src/http/errors.ts), so the raw internal state names and
    // arrow notation this used to interpolate directly (`'accepted' ->
    // 'refunded'`) never should have. `current`/`next` stay available on
    // `details` for a client that wants to branch on them programmatically.
    throw new ConflictError('This date can no longer be updated — its status has already moved on.', { current, next });
  }
}

// =====================================================================
// Row mapping
// =====================================================================

interface DateProposalRow {
  id: string;
  conversation_id: string;
  proposer_id: string;
  recipient_id: string;
  venue_id: string;
  scheduled_start: Date;
  scheduled_end: Date;
  optional_note: string | null;
  status: DateProposalStatus;
  policy_snapshot: DateProposalPolicySnapshot;
  escrow_amount_cents: string;
  created_at: Date;
  accepted_at: Date | null;
  declined_at: Date | null;
  expired_at: Date | null;
  canceled_at: Date | null;
  charged_at: Date | null;
  ticketed_at: Date | null;
  completed_at: Date | null;
}

function mapProposal(row: DateProposalRow): DateProposal {
  return {
    id: row.id,
    conversationId: row.conversation_id,
    proposerId: row.proposer_id,
    recipientId: row.recipient_id,
    venueId: row.venue_id,
    scheduledStart: row.scheduled_start,
    scheduledEnd: row.scheduled_end,
    optionalNote: row.optional_note,
    status: row.status,
    policySnapshot: row.policy_snapshot,
    escrowAmountCents: Number(row.escrow_amount_cents),
    createdAt: row.created_at,
    acceptedAt: row.accepted_at,
    declinedAt: row.declined_at,
    expiredAt: row.expired_at,
    canceledAt: row.canceled_at,
    chargedAt: row.charged_at,
    ticketedAt: row.ticketed_at,
    completedAt: row.completed_at,
  };
}

async function loadProposalRow(ctx: Ctx, dateProposalId: string): Promise<DateProposalRow> {
  if (!z.string().uuid().safeParse(dateProposalId).success) throw new ValidationError('That is not a valid id.');
  const { rows } = await ctx.db.query<DateProposalRow>(`SELECT * FROM date_proposals WHERE id = $1`, [dateProposalId]);
  if (!rows[0]) throw new NotFoundError('Date proposal not found');
  return rows[0];
}

/** Every timestamp column here is stamped from `ctx.clock.now()`, never SQL `now()` — see INTERFACES.md's "ctx.clock for ALL time" rule. Using the DB's own wall clock would silently diverge from `ManualClock`-driven expiry/cutoff tests (and, in principle, from any future non-`SystemClock` production clock). */
async function setStatus(ctx: Ctx, dateProposalId: string, status: DateProposalStatus, timestampColumn?: string): Promise<DateProposalRow> {
  const sql = timestampColumn
    ? `UPDATE date_proposals SET status = $2, ${timestampColumn} = $3 WHERE id = $1 RETURNING *`
    : `UPDATE date_proposals SET status = $2 WHERE id = $1 RETURNING *`;
  const params = timestampColumn ? [dateProposalId, status, ctx.clock.now()] : [dateProposalId, status];
  const { rows } = await ctx.db.query<DateProposalRow>(sql, params);
  return rows[0]!;
}

/**
 * Per-date-proposal mutual exclusion for the state-mutating, money-moving
 * entry points below (`acceptDateProposal`, `declineDateProposal`,
 * `cancelDateProposal`, `markNoShow`). Each of those reads the proposal
 * row, then performs several *separately-committing* checkpoints (payment
 * authorize/capture/refund calls, each in its own `payment.service.ts`
 * transaction, on purpose — see this file's module header on resumability
 * after a crash), rather than one enclosing transaction. That is exactly
 * right for crash-resumability, but it means two truly concurrent calls
 * for the SAME date proposal (a client double-submit, a retried request
 * racing the original) can both read the same starting status and both
 * carry out the money-moving side effects — a real double-capture /
 * double-refund bug, not merely a hypothetical one (test-audit.md
 * Finding 3's "never tested for double-capture", made concrete by
 * `tests/concurrency/dateProposalRace.test.ts`).
 *
 * The fix is a `pg_try_advisory_lock` keyed by the date proposal id, held
 * for the whole call and released in `finally` on a dedicated connection
 * — this mirrors `src/jobs/scheduler.ts`'s job-level lock, the one
 * concurrency-safety pattern already proven correct and copied by the
 * audit. It does not wrap `ctx.db` in a transaction (that would defeat
 * the resumability property above); it only ensures at most one call is
 * ever "inside" one of these functions for a given date proposal id at a
 * time. The loser fails fast with a typed `ConflictError` rather than
 * racing the winner.
 */
function dateProposalLockKey(dateProposalId: string): [number, number] {
  const digest = createHash('sha256').update(`odate_date_proposal:${dateProposalId}`).digest();
  return [digest.readInt32BE(0), digest.readInt32BE(4)];
}

async function withDateProposalLock<T>(dateProposalId: string, fn: () => Promise<T>): Promise<T> {
  const [k1, k2] = dateProposalLockKey(dateProposalId);
  const client = await getPool().connect();
  try {
    const { rows } = await client.query<{ locked: boolean }>('SELECT pg_try_advisory_lock($1, $2) AS locked', [k1, k2]);
    if (!rows[0]?.locked) {
      throw new ConflictError('This date proposal is already being modified by a concurrent request.');
    }
    try {
      return await fn();
    } finally {
      await client.query('SELECT pg_advisory_unlock($1, $2)', [k1, k2]);
    }
  } finally {
    client.release();
  }
}

function assertParticipant(ctx: Ctx, row: DateProposalRow): string {
  const { userId } = requireUserActor(ctx);
  if (row.proposer_id !== userId && row.recipient_id !== userId) {
    throw new ForbiddenError('Not a participant in this date proposal');
  }
  return userId;
}

// =====================================================================
// payment_holds read helper (see module header for why this is a direct
// SELECT rather than a payment.service.ts export).
// =====================================================================

interface HoldLookupRow {
  id: string;
  status: string;
  amount_cents: string;
}

async function getHoldRow(ctx: Ctx, dateProposalId: string, userId: string): Promise<HoldLookupRow | undefined> {
  const { rows } = await ctx.db.query<HoldLookupRow>(
    `SELECT id, status, amount_cents FROM payment_holds WHERE date_proposal_id = $1 AND user_id = $2`,
    [dateProposalId, userId],
  );
  return rows[0];
}

/** vouchers read helper — same reasoning as `getHoldRow` (voucher.service.ts exposes no "find by date proposal" lookup; cancellation needs one). */
async function getVoucherRow(ctx: Ctx, dateProposalId: string): Promise<{ id: string; status: string } | undefined> {
  const { rows } = await ctx.db.query<{ id: string; status: string }>(
    `SELECT id, status FROM vouchers WHERE date_proposal_id = $1`,
    [dateProposalId],
  );
  return rows[0];
}

// =====================================================================
// Best-effort side effects (see module header)
// =====================================================================

async function notifyBestEffort(ctx: Ctx, input: notificationService.NotifyInput): Promise<void> {
  try {
    await notificationService.notify(ctx, input);
  } catch (err) {
    ctx.logger.warn('dateProposal.notify_failed', { eventType: input.eventType, userId: input.userId, err: describeError(err) });
  }
}

async function recordTrustEventBestEffort(ctx: Ctx, input: trustService.RecordTrustEventInput): Promise<void> {
  try {
    await trustService.recordTrustEvent(ctx, input);
  } catch (err) {
    ctx.logger.warn('dateProposal.trust_event_failed', { eventType: input.eventType, userId: input.userId, err: describeError(err) });
  }
}

/**
 * Post-date check-in hook (postDateFeedback.service.ts, additive — see
 * that module's own doc for the full timing design). Eagerly evaluates
 * whether either participant is due an initial check-in prompt the
 * moment this proposal actually reaches `completed`/`completed_unverified`
 * — a responsiveness nicety only; `postDateFeedbackService
 * #runCheckInPromptSweep` independently re-derives the same decision from
 * `date_proposals` on its own schedule (and is what catches tickets that
 * never reach either of the two call sites below at all). Best-effort:
 * a prompt-scheduling hiccup must never roll back an already-persisted
 * date-proposal status change.
 */
async function ensureCheckInPromptSentBestEffort(ctx: Ctx, dateProposalId: string): Promise<void> {
  try {
    await postDateFeedbackService.ensureCheckInPromptSent(ctx, dateProposalId);
  } catch (err) {
    ctx.logger.warn('dateProposal.check_in_prompt_failed', { dateProposalId, err: describeError(err) });
  }
}

function describeError(err: unknown): string {
  return err instanceof Error ? err.message : String(err);
}

/** Rounding rule for every percentage-of-escrow refund in this file: round DOWN, always in the platform's favor — see `payment.service#refundHold`'s doc for the full rationale. */
function percentOfCents(amountCents: number, percent: number): number {
  return Math.floor((amountCents * percent) / 100);
}

// =====================================================================
// proposeDate — §14.2 Step 1
// =====================================================================

const ProposeDateSchema = z
  .object({
    conversationId: z.string().uuid(),
    venueId: z.string().uuid(),
    scheduledStart: z.date(),
    scheduledEnd: z.date(),
    optionalNote: z.string().max(500).optional(),
  })
  .refine((v) => v.scheduledEnd > v.scheduledStart, { message: 'scheduledEnd must be after scheduledStart' });

export interface ProposeDateInput {
  conversationId: string;
  venueId: string;
  scheduledStart: Date;
  scheduledEnd: Date;
  optionalNote?: string;
}

/** Creates the proposal, snapshots policy, and authorizes the proposer's hold. Result status is 'pending_acceptance' on success or 'payment_failed' if authorization is declined (spec §14.2 Step 1). */
export async function proposeDate(ctx: Ctx, input: ProposeDateInput): Promise<DateProposal> {
  const { userId: proposerId } = requireUserActor(ctx);
  const parsed = ProposeDateSchema.parse(input);

  const conversation = await conversationService.getConversation(ctx, parsed.conversationId);
  if (conversation.status !== 'active') {
    throw new ConflictError('You can only propose a date inside an active conversation.');
  }
  let recipientId: string;
  if (conversation.userAId === proposerId) recipientId = conversation.userBId;
  else if (conversation.userBId === proposerId) recipientId = conversation.userAId;
  else throw new ForbiddenError('Not a participant in this conversation');

  const venue = await venueService.getVenue(ctx, parsed.venueId);
  if (!venue.active) throw new ValidationError('Venue is not currently active');

  const policySnapshot = (await ctx.config.snapshotPolicy(DATE_PROPOSAL_POLICY_KEYS)) as DateProposalPolicySnapshot;
  const escrowAmountCents = policySnapshot['date.escrow_amount_cents'];

  const { rows } = await ctx.db.query<DateProposalRow>(
    `INSERT INTO date_proposals
       (conversation_id, proposer_id, recipient_id, venue_id, scheduled_start, scheduled_end, optional_note, status, policy_snapshot, escrow_amount_cents, created_at)
     VALUES ($1, $2, $3, $4, $5, $6, $7, 'draft', $8::jsonb, $9, $10)
     RETURNING *`,
    [
      parsed.conversationId,
      proposerId,
      recipientId,
      parsed.venueId,
      parsed.scheduledStart,
      parsed.scheduledEnd,
      parsed.optionalNote ?? null,
      JSON.stringify(policySnapshot),
      escrowAmountCents,
      ctx.clock.now(), // explicit, not the column's SQL `now()` default — see setStatus's doc comment
    ],
  );
  const created = rows[0]!;

  const hold = await paymentService.authorizeHold(ctx, {
    dateProposalId: created.id,
    userId: proposerId,
    amountCents: escrowAmountCents,
    currency: 'usd',
  });

  if (hold.status !== 'authorized') {
    assertTransition('draft', 'payment_failed');
    const failed = await setStatus(ctx, created.id, 'payment_failed');
    await notifyBestEffort(ctx, { userId: proposerId, eventType: 'payment_failed', channel: 'push', payload: { dateProposalId: created.id } });
    return mapProposal(failed);
  }

  assertTransition('draft', 'pending_acceptance');
  const pending = await setStatus(ctx, created.id, 'pending_acceptance');
  await notifyBestEffort(ctx, { userId: proposerId, eventType: 'payment_hold_authorized', channel: 'push', payload: { dateProposalId: created.id } });
  await notifyBestEffort(ctx, { userId: recipientId, eventType: 'date_proposal_received', channel: 'push', payload: { dateProposalId: created.id } });
  return mapProposal(pending);
}

// =====================================================================
// acceptDateProposal — §14.2 Steps 2-4, §14.5
// =====================================================================

/**
 * Recipient accepts. Authorizes the recipient's hold; if that succeeds,
 * captures BOTH holds and issues the voucher (spec §14.2 Steps 2-4). If
 * the recipient's authorization fails, releases the proposer's hold and
 * sets `payment_failed` (spec §14.5). If a capture fails after both
 * authorizations succeeded, releases/refunds ALL holds and sets
 * `payment_failed` (spec §14.5 "Capture fails after authorization") — see
 * module header for the release-vs-refund distinction and the resumable,
 * multi-checkpoint design of this function.
 */
export async function acceptDateProposal(ctx: Ctx, dateProposalId: string): Promise<DateProposal> {
  return withDateProposalLock(dateProposalId, () => acceptDateProposalLocked(ctx, dateProposalId));
}

async function acceptDateProposalLocked(ctx: Ctx, dateProposalId: string): Promise<DateProposal> {
  const row = await loadProposalRow(ctx, dateProposalId);
  const { userId } = requireUserActor(ctx);
  if (row.recipient_id !== userId) throw new ForbiddenError('Only the recipient can accept a date proposal');

  // Fully idempotent no-op if this call (or an earlier crashed attempt)
  // already finished the whole flow.
  if (row.status === 'charged' || row.status === 'ticketed') return mapProposal(row);

  if (row.status !== 'pending_acceptance' && row.status !== 'accepted') {
    throw new ConflictError('This date proposal can no longer be accepted.', { status: row.status });
  }

  // ---- Step 2: authorize the recipient's hold ----
  const recipientHold = await paymentService.authorizeHold(ctx, {
    dateProposalId,
    userId: row.recipient_id,
    amountCents: Number(row.escrow_amount_cents),
    currency: 'usd',
  });

  if (recipientHold.status !== 'authorized') {
    const proposerHold = await getHoldRow(ctx, dateProposalId, row.proposer_id);
    if (proposerHold?.status === 'authorized') await paymentService.releaseHold(ctx, proposerHold.id);
    assertTransition(row.status === 'accepted' ? 'accepted' : 'pending_acceptance', 'payment_failed');
    const failed = await setStatus(ctx, dateProposalId, 'payment_failed');
    await notifyBestEffort(ctx, { userId: row.proposer_id, eventType: 'payment_failed', channel: 'push', payload: { dateProposalId } });
    await notifyBestEffort(ctx, { userId: row.recipient_id, eventType: 'payment_failed', channel: 'push', payload: { dateProposalId } });
    return mapProposal(failed);
  }

  let current = row;
  if (row.status === 'pending_acceptance') {
    assertTransition('pending_acceptance', 'accepted');
    current = await setStatus(ctx, dateProposalId, 'accepted', 'accepted_at');
    await notifyBestEffort(ctx, { userId: row.proposer_id, eventType: 'date_accepted', channel: 'push', payload: { dateProposalId } });
  }

  // ---- Step 3: capture both holds, only now that both are authorized ----
  const proposerHold = await getHoldRow(ctx, dateProposalId, row.proposer_id);
  if (!proposerHold) throw new PaymentError('Proposer hold is missing — cannot capture');

  const captureA = await paymentService.captureHold(ctx, proposerHold.id);
  if (captureA.status !== 'captured') {
    const recipientHoldRow = await getHoldRow(ctx, dateProposalId, row.recipient_id);
    if (recipientHoldRow?.status === 'authorized') await paymentService.releaseHold(ctx, recipientHoldRow.id);
    assertTransition('accepted', 'payment_failed');
    const failed = await setStatus(ctx, dateProposalId, 'payment_failed');
    await notifyBestEffort(ctx, { userId: row.proposer_id, eventType: 'payment_failed', channel: 'push', payload: { dateProposalId } });
    await notifyBestEffort(ctx, { userId: row.recipient_id, eventType: 'payment_failed', channel: 'push', payload: { dateProposalId } });
    return mapProposal(failed);
  }

  const recipientHoldRow = await getHoldRow(ctx, dateProposalId, row.recipient_id);
  if (!recipientHoldRow) throw new PaymentError('Recipient hold is missing — cannot capture');

  const captureB = await paymentService.captureHold(ctx, recipientHoldRow.id);
  if (captureB.status !== 'captured') {
    // Proposer's side already moved real money — undo with a refund, not a
    // release (§30.5 "do not charge one side alone").
    await paymentService.refundHold(ctx, proposerHold.id);
    assertTransition('accepted', 'payment_failed');
    const failed = await setStatus(ctx, dateProposalId, 'payment_failed');
    await notifyBestEffort(ctx, { userId: row.proposer_id, eventType: 'payment_failed', channel: 'push', payload: { dateProposalId } });
    await notifyBestEffort(ctx, { userId: row.recipient_id, eventType: 'payment_failed', channel: 'push', payload: { dateProposalId } });
    return mapProposal(failed);
  }

  // ---- Step 4: both captured — charge, then ticket ----
  assertTransition('accepted', 'charged');
  current = await setStatus(ctx, dateProposalId, 'charged', 'charged_at');

  await voucherService.issueVoucher(ctx, dateProposalId);

  assertTransition('charged', 'ticketed');
  current = await setStatus(ctx, dateProposalId, 'ticketed', 'ticketed_at');
  await notifyBestEffort(ctx, { userId: row.proposer_id, eventType: 'ticket_issued', channel: 'push', payload: { dateProposalId } });
  await notifyBestEffort(ctx, { userId: row.recipient_id, eventType: 'ticket_issued', channel: 'push', payload: { dateProposalId } });

  return mapProposal(current);
}

// =====================================================================
// declineDateProposal
// =====================================================================

export async function declineDateProposal(ctx: Ctx, dateProposalId: string): Promise<DateProposal> {
  return withDateProposalLock(dateProposalId, () => declineDateProposalLocked(ctx, dateProposalId));
}

async function declineDateProposalLocked(ctx: Ctx, dateProposalId: string): Promise<DateProposal> {
  const row = await loadProposalRow(ctx, dateProposalId);
  const { userId } = requireUserActor(ctx);
  if (row.recipient_id !== userId) throw new ForbiddenError('Only the recipient can decline a date proposal');
  assertTransition(row.status, 'declined');

  const proposerHold = await getHoldRow(ctx, dateProposalId, row.proposer_id);
  if (proposerHold?.status === 'authorized') await paymentService.releaseHold(ctx, proposerHold.id);

  const updated = await setStatus(ctx, dateProposalId, 'declined', 'declined_at');
  return mapProposal(updated);
}

// =====================================================================
// cancelDateProposal — §14.7
// =====================================================================

/**
 * Cancellation, branching on the §14.7 policy read from the proposal's own
 * `policySnapshot` (never live config):
 *  - before acceptance: release the proposer's hold, `status = 'canceled'`.
 *  - after acceptance, more than `full_refund_cutoff_hours` before
 *    `scheduledStart`: refund both users, voucher canceled if issued,
 *    `status = 'refunded'`.
 *  - after acceptance, inside the cutoff: refund per
 *    `late_cancel_refund_percent` (0 by default), `status = 'canceled'`.
 *
 * Either participant may cancel (spec §14.7 "Either user cancels"); an
 * admin actor may also cancel on behalf of the pair — this is the path
 * that realizes spec §30.6 ("venue closes after date accepted... allow
 * refund") since no separate admin-only function was allocated for that.
 */
export async function cancelDateProposal(ctx: Ctx, dateProposalId: string): Promise<DateProposal> {
  return withDateProposalLock(dateProposalId, () => cancelDateProposalLocked(ctx, dateProposalId));
}

async function cancelDateProposalLocked(ctx: Ctx, dateProposalId: string): Promise<DateProposal> {
  const row = await loadProposalRow(ctx, dateProposalId);
  if (ctx.actor.type === 'admin') {
    // allowed regardless of participant check
  } else {
    assertParticipant(ctx, row);
  }

  if (row.status === 'pending_acceptance') {
    assertTransition('pending_acceptance', 'canceled');
    const proposerHold = await getHoldRow(ctx, dateProposalId, row.proposer_id);
    if (proposerHold?.status === 'authorized') await paymentService.releaseHold(ctx, proposerHold.id);
    const updated = await setStatus(ctx, dateProposalId, 'canceled', 'canceled_at');
    await notifyBestEffort(ctx, { userId: row.proposer_id, eventType: 'date_canceled', channel: 'in_app', payload: { dateProposalId } });
    await notifyBestEffort(ctx, { userId: row.recipient_id, eventType: 'date_canceled', channel: 'in_app', payload: { dateProposalId } });
    return mapProposal(updated);
  }

  if (row.status !== 'accepted' && row.status !== 'charged' && row.status !== 'ticketed') {
    throw new ConflictError('This date proposal can no longer be canceled.', { status: row.status });
  }

  const cutoffHours = row.policy_snapshot['date.full_refund_cutoff_hours'];
  const lateCancelPercent = row.policy_snapshot['date.late_cancel_refund_percent'];
  const hoursUntilDate = hoursBetween(ctx.clock.now(), row.scheduled_start);
  const isFullRefund = hoursUntilDate >= cutoffHours;

  for (const participantId of [row.proposer_id, row.recipient_id]) {
    const hold = await getHoldRow(ctx, dateProposalId, participantId);
    if (!hold) continue;
    if (hold.status === 'captured') {
      const refundAmount = isFullRefund ? Number(hold.amount_cents) : percentOfCents(Number(hold.amount_cents), lateCancelPercent);
      if (refundAmount > 0) await paymentService.refundHold(ctx, hold.id, refundAmount);
    } else if (hold.status === 'authorized') {
      await paymentService.releaseHold(ctx, hold.id);
    }
  }

  const voucher = await getVoucherRow(ctx, dateProposalId);
  if (voucher && voucher.status === 'issued') await voucherService.cancelVoucher(ctx, voucher.id);

  const finalStatus: DateProposalStatus = isFullRefund ? 'refunded' : 'canceled';
  assertTransition(row.status, finalStatus);
  // Neither 'refunded' nor a bare late-cancel has a dedicated timestamp
  // column in §23.17 — `canceled_at` is reused for both as "when this
  // cancel-family transition happened".
  const updated = await setStatus(ctx, dateProposalId, finalStatus, 'canceled_at');
  const eventType = finalStatus === 'refunded' ? 'date_refunded' : 'date_canceled';
  await notifyBestEffort(ctx, { userId: row.proposer_id, eventType, channel: 'in_app', payload: { dateProposalId } });
  await notifyBestEffort(ctx, { userId: row.recipient_id, eventType, channel: 'in_app', payload: { dateProposalId } });
  return mapProposal(updated);
}

// =====================================================================
// confirmAttendance — §15.4 no-scan fallback
// =====================================================================

/**
 * §15.4 no-scan fallback. Records the caller's confirmation. If both
 * users have confirmed within `date.no_scan_confirmation_hours` of
 * `scheduledEnd`: `status = 'completed_unverified'` and
 * `conversation.service#establishConversation` is called — this does NOT
 * settle venue payment (spec §15.4 "does not automatically settle venue
 * payment") — see module header for why `establishConversation` is called
 * BEFORE the status write, not best-effort after it. If the window elapses
 * with only one confirmation: `status = 'disputed'`.
 */
export async function confirmAttendance(ctx: Ctx, dateProposalId: string): Promise<{ dateProposal: DateProposal; confirmation: AttendanceConfirmation }> {
  const row = await loadProposalRow(ctx, dateProposalId);
  const userId = assertParticipant(ctx, row);
  if (row.status !== 'ticketed') {
    throw new ConflictError('Attendance can no longer be confirmed for this date.', { status: row.status });
  }

  await ctx.db.query(
    `INSERT INTO date_attendance_confirmations (date_proposal_id, user_id, confirmed_at)
     VALUES ($1, $2, $3)
     ON CONFLICT (date_proposal_id, user_id) DO NOTHING`,
    [dateProposalId, userId, ctx.clock.now()],
  );

  const { rows: confirmationRows } = await ctx.db.query<{ user_id: string; confirmed_at: Date }>(
    `SELECT user_id, confirmed_at FROM date_attendance_confirmations WHERE date_proposal_id = $1`,
    [dateProposalId],
  );
  const myConfirmation = confirmationRows.find((c) => c.user_id === userId)!;
  const confirmation: AttendanceConfirmation = { dateProposalId, userId, confirmedAt: myConfirmation.confirmed_at };

  const windowHours = row.policy_snapshot['date.no_scan_confirmation_hours'];
  const deadline = addHours(row.scheduled_end, windowHours);
  const now = ctx.clock.now();

  if (confirmationRows.length >= 2) {
    assertTransition('ticketed', 'completed_unverified');
    await conversationService.establishConversation(ctx, row.conversation_id);
    const updated = await setStatus(ctx, dateProposalId, 'completed_unverified', 'completed_at');
    await recordTrustEventBestEffort(ctx, { userId: row.proposer_id, eventType: 'completed_date', delta: 3, metadata: { dateProposalId, verified: false } });
    await recordTrustEventBestEffort(ctx, { userId: row.recipient_id, eventType: 'completed_date', delta: 3, metadata: { dateProposalId, verified: false } });
    await ensureCheckInPromptSentBestEffort(ctx, dateProposalId);
    return { dateProposal: mapProposal(updated), confirmation };
  }

  if (confirmationRows.length === 1 && now.getTime() > deadline.getTime()) {
    assertTransition('ticketed', 'disputed');
    const updated = await setStatus(ctx, dateProposalId, 'disputed');
    return { dateProposal: mapProposal(updated), confirmation };
  }

  return { dateProposal: mapProposal(row), confirmation };
}

// =====================================================================
// submitPostDateFeedback
// =====================================================================

interface PostDateFeedbackRow {
  id: string;
  date_proposal_id: string;
  user_id: string;
  positive: boolean;
  would_meet_again: boolean | null;
  safety_concern: boolean;
  notes: string | null;
  created_at: Date;
}

function mapFeedback(row: PostDateFeedbackRow): PostDateFeedback {
  return {
    id: row.id,
    dateProposalId: row.date_proposal_id,
    userId: row.user_id,
    positive: row.positive,
    wouldMeetAgain: row.would_meet_again,
    safetyConcern: row.safety_concern,
    notes: row.notes,
    createdAt: row.created_at,
  };
}

const FeedbackInputSchema = z.object({
  positive: z.boolean(),
  wouldMeetAgain: z.boolean().optional(),
  safetyConcern: z.boolean().optional(),
  notes: z.string().max(2000).optional(),
});

export async function submitPostDateFeedback(
  ctx: Ctx,
  dateProposalId: string,
  input: { positive: boolean; wouldMeetAgain?: boolean; safetyConcern?: boolean; notes?: string },
): Promise<PostDateFeedback> {
  const row = await loadProposalRow(ctx, dateProposalId);
  const userId = assertParticipant(ctx, row);
  if (row.status !== 'completed' && row.status !== 'completed_unverified') {
    throw new ConflictError('Post-date feedback can only be submitted for a completed date');
  }
  const parsed = FeedbackInputSchema.parse(input);

  const { rows } = await ctx.db.query<PostDateFeedbackRow>(
    `INSERT INTO post_date_feedback (date_proposal_id, user_id, positive, would_meet_again, safety_concern, notes)
     VALUES ($1, $2, $3, $4, $5, $6)
     ON CONFLICT (date_proposal_id, user_id) DO UPDATE SET
       positive = EXCLUDED.positive, would_meet_again = EXCLUDED.would_meet_again,
       safety_concern = EXCLUDED.safety_concern, notes = EXCLUDED.notes
     RETURNING *`,
    [dateProposalId, userId, parsed.positive, parsed.wouldMeetAgain ?? null, parsed.safetyConcern ?? false, parsed.notes ?? null],
  );
  return mapFeedback(rows[0]!);
}

// =====================================================================
// getDateProposal
// =====================================================================

export async function getDateProposal(ctx: Ctx, dateProposalId: string): Promise<DateProposal> {
  const row = await loadProposalRow(ctx, dateProposalId);
  if (ctx.actor.type === 'admin' || ctx.actor.type === 'system') return mapProposal(row);
  assertParticipant(ctx, row);
  return mapProposal(row);
}

// =====================================================================
// expireDuePendingProposals — §25.2 job
// =====================================================================

/** §25.2 job: pending_acceptance proposals past `policySnapshot['date.accept_expiry_hours']` -> 'expired', release the proposer's hold. */
export async function expireDuePendingProposals(ctx: Ctx): Promise<{ expired: number }> {
  const { rows } = await ctx.db.query<DateProposalRow>(`SELECT * FROM date_proposals WHERE status = 'pending_acceptance'`);

  let expired = 0;
  const now = ctx.clock.now();
  for (const row of rows) {
    const expiryHours = row.policy_snapshot['date.accept_expiry_hours'];
    const deadline = addHours(row.created_at, expiryHours);
    if (now.getTime() < deadline.getTime()) continue;

    const proposerHold = await getHoldRow(ctx, row.id, row.proposer_id);
    if (proposerHold?.status === 'authorized') await paymentService.releaseHold(ctx, proposerHold.id);

    assertTransition('pending_acceptance', 'expired');
    await setStatus(ctx, row.id, 'expired', 'expired_at');
    await notifyBestEffort(ctx, { userId: row.proposer_id, eventType: 'payment_failed', channel: 'in_app', payload: { dateProposalId: row.id, reason: 'expired' } });
    expired++;
  }
  return { expired };
}

// =====================================================================
// markNoShow
// =====================================================================

/** Admin/automated no-show marking (spec §13.3 `no_show`, feeds `trust.service.ts` negative factors, §6.2). Applies the `no_show_refund_percent` policy from the proposal's own snapshot: the no-show party forfeits that percent (default 0 = forfeits everything); the other party is refunded in full. */
export async function markNoShow(ctx: Ctx, dateProposalId: string, noShowUserId: string): Promise<DateProposal> {
  return withDateProposalLock(dateProposalId, () => markNoShowLocked(ctx, dateProposalId, noShowUserId));
}

async function markNoShowLocked(ctx: Ctx, dateProposalId: string, noShowUserId: string): Promise<DateProposal> {
  if (ctx.actor.type !== 'admin' && ctx.actor.type !== 'system') {
    throw new ForbiddenError('Only admin/system actors can mark a no-show');
  }
  const row = await loadProposalRow(ctx, dateProposalId);
  assertTransition(row.status, 'no_show');
  if (noShowUserId !== row.proposer_id && noShowUserId !== row.recipient_id) {
    throw new ValidationError('noShowUserId must be a participant in this date proposal');
  }
  const otherUserId = noShowUserId === row.proposer_id ? row.recipient_id : row.proposer_id;
  const noShowPercent = row.policy_snapshot['date.no_show_refund_percent'];

  const noShowHold = await getHoldRow(ctx, dateProposalId, noShowUserId);
  if (noShowHold?.status === 'captured') {
    const refundAmount = percentOfCents(Number(noShowHold.amount_cents), noShowPercent);
    if (refundAmount > 0) await paymentService.refundHold(ctx, noShowHold.id, refundAmount);
  }
  const otherHold = await getHoldRow(ctx, dateProposalId, otherUserId);
  if (otherHold?.status === 'captured') {
    await paymentService.refundHold(ctx, otherHold.id, Number(otherHold.amount_cents));
  }

  const voucher = await getVoucherRow(ctx, dateProposalId);
  if (voucher && voucher.status === 'issued') await voucherService.cancelVoucher(ctx, voucher.id);

  const updated = await setStatus(ctx, dateProposalId, 'no_show');
  await recordTrustEventBestEffort(ctx, { userId: noShowUserId, eventType: 'no_show', delta: -8, metadata: { dateProposalId } });
  await notifyBestEffort(ctx, { userId: noShowUserId, eventType: 'date_no_show', channel: 'in_app', payload: { dateProposalId } });
  await notifyBestEffort(ctx, { userId: otherUserId, eventType: 'date_no_show', channel: 'in_app', payload: { dateProposalId } });
  return mapProposal(updated);
}

// =====================================================================
// markCompletedByRedemption
// =====================================================================

/**
 * Called by `redemption.service.ts` only, immediately after a successful
 * venue scan, in the same transaction as the `venue_redemptions` insert
 * and `voucher.service#markRedeemed`. Sets `status = 'completed'` and
 * `completed_at` — NOT `completed_unverified` (that's the separate
 * no-scan path via `confirmAttendance`). Establishing the conversation and
 * firing trust events are `redemption.service.ts`'s responsibility, not
 * this function's. Uses `ctx.db` exactly as given — never opens its own
 * transaction, and never calls `ctx.payments` (no processor interaction
 * belongs on the redemption path itself; venue settlement is out of the
 * user-facing escrow's scope, see `redemption.service.ts`).
 */
export async function markCompletedByRedemption(ctx: Ctx, dateProposalId: string): Promise<DateProposal> {
  const row = await loadProposalRow(ctx, dateProposalId);
  assertTransition(row.status, 'completed');
  const updated = await setStatus(ctx, dateProposalId, 'completed', 'completed_at');
  await notifyBestEffort(ctx, { userId: row.proposer_id, eventType: 'date_completed', channel: 'in_app', payload: { dateProposalId } });
  await notifyBestEffort(ctx, { userId: row.recipient_id, eventType: 'date_completed', channel: 'in_app', payload: { dateProposalId } });
  await ensureCheckInPromptSentBestEffort(ctx, dateProposalId);
  return mapProposal(updated);
}

// =====================================================================
// sweepTicketedCompletionWindows — §15.4 / Open Question OQ-3
// =====================================================================

export interface SweepTicketedCompletionWindowsResult {
  autoNoShow: number;
  autoDisputed: number;
}

/**
 * Decision-layer addition (OQ-3, see this file's module doc and
 * docs/conformance.md): for every `ticketed` proposal whose no-scan
 * confirmation window (`scheduled_end + policySnapshot['date.no_scan_confirmation_hours']`)
 * has closed with the venue never having scanned —
 *
 *   - ZERO attendance confirmations from either party -> `no_show`,
 *     automatically. Refund follows the FROZEN policy snapshot
 *     (`date.no_show_refund_percent`), applied symmetrically to BOTH
 *     participants' captured escrow — unlike the admin/system-driven
 *     `markNoShow` above (which names one specific at-fault party and
 *     makes the other whole), nobody here proved attendance at all, so
 *     there is no "the other party showed up" fact to refund in full.
 *   - EXACTLY ONE confirmation -> `disputed` (spec §15.4). This is the
 *     same rule `confirmAttendance` already applies inline, duplicated
 *     here because that check only fires when the CONFIRMING user happens
 *     to call `confirmAttendance` again after the deadline — this sweep
 *     is what makes the transition happen even if nobody calls back at
 *     all, which is the actual "no human step anywhere" requirement
 *     (spec §18.1).
 *   - Two-or-more confirmations should be unreachable here (already
 *     handled inline, transitioning straight to `completed_unverified`)
 *     — skipped defensively rather than throwing.
 *
 * Idempotent/safe to re-run with any clock: only `status = 'ticketed'`
 * rows are ever candidates, and both outcomes above move the row OUT of
 * `ticketed`, so a proposal this function has already resolved is never
 * selected again on a later run.
 */
export async function sweepTicketedCompletionWindows(ctx: Ctx): Promise<SweepTicketedCompletionWindowsResult> {
  const now = ctx.clock.now();
  const { rows } = await ctx.db.query<DateProposalRow>(`SELECT * FROM date_proposals WHERE status = 'ticketed'`);

  let autoNoShow = 0;
  let autoDisputed = 0;

  for (const row of rows) {
    const windowHours = row.policy_snapshot['date.no_scan_confirmation_hours'];
    const deadline = addHours(row.scheduled_end, windowHours);
    if (now.getTime() <= deadline.getTime()) continue; // window still open

    const { rows: confirmationRows } = await ctx.db.query<{ user_id: string }>(
      `SELECT user_id FROM date_attendance_confirmations WHERE date_proposal_id = $1`,
      [row.id],
    );

    if (confirmationRows.length === 0) {
      await autoMarkNoShowBothParties(ctx, row);
      autoNoShow++;
    } else if (confirmationRows.length === 1) {
      assertTransition('ticketed', 'disputed');
      const updated = await setStatus(ctx, row.id, 'disputed');
      await notifyBestEffort(ctx, { userId: updated.proposer_id, eventType: 'date_disputed', channel: 'in_app', payload: { dateProposalId: row.id } });
      await notifyBestEffort(ctx, { userId: updated.recipient_id, eventType: 'date_disputed', channel: 'in_app', payload: { dateProposalId: row.id } });
      autoDisputed++;
    }
  }

  return { autoNoShow, autoDisputed };
}

async function autoMarkNoShowBothParties(ctx: Ctx, row: DateProposalRow): Promise<void> {
  const noShowPercent = row.policy_snapshot['date.no_show_refund_percent'];

  for (const participantId of [row.proposer_id, row.recipient_id]) {
    const hold = await getHoldRow(ctx, row.id, participantId);
    if (hold?.status === 'captured') {
      const refundAmount = percentOfCents(Number(hold.amount_cents), noShowPercent);
      if (refundAmount > 0) await paymentService.refundHold(ctx, hold.id, refundAmount);
    }
  }

  const voucher = await getVoucherRow(ctx, row.id);
  if (voucher && voucher.status === 'issued') await voucherService.cancelVoucher(ctx, voucher.id);

  assertTransition('ticketed', 'no_show');
  await setStatus(ctx, row.id, 'no_show');

  for (const participantId of [row.proposer_id, row.recipient_id]) {
    await recordTrustEventBestEffort(ctx, { userId: participantId, eventType: 'no_show', delta: -8, metadata: { dateProposalId: row.id, autoResolved: true } });
    await notifyBestEffort(ctx, { userId: participantId, eventType: 'date_no_show', channel: 'in_app', payload: { dateProposalId: row.id } });
  }
}

// =====================================================================
// Automated dispute resolution lookups — §15.4 / Open Question OQ-3
//
// The actual resolving (filing an implicit report via report.service.ts)
// lives in the separate `disputeResolution.service.ts` — see that file's
// header for why it isn't here. These two functions are the read/write
// primitives it composes: a read-only lookup of what's due, and an
// idempotency marker `disputeResolution.service.ts` sets once it has
// finished. Neither reaches outside this file's existing, documented "may
// call" list.
// =====================================================================

export interface DisputeAwaitingAutoResolution {
  dateProposalId: string;
  conversationId: string;
  confirmingUserId: string;
  nonConfirmingUserId: string;
}

/** `disputed` proposals whose auto-resolve deadline (`scheduled_end + no_scan_confirmation_hours + dispute_auto_resolve_hours`, all from the proposal's own frozen policy snapshot, falling back to live config for a proposal created before `date.dispute_auto_resolve_hours` existed) has passed and have not yet been auto-resolved. */
export async function listDisputesAwaitingAutoResolution(ctx: Ctx): Promise<DisputeAwaitingAutoResolution[]> {
  const now = ctx.clock.now();
  const { rows } = await ctx.db.query<DateProposalRow>(
    `SELECT * FROM date_proposals WHERE status = 'disputed' AND dispute_resolved_at IS NULL`,
  );

  const out: DisputeAwaitingAutoResolution[] = [];
  for (const row of rows) {
    const windowHours = row.policy_snapshot['date.no_scan_confirmation_hours'];
    const disputeAutoResolveHours =
      row.policy_snapshot['date.dispute_auto_resolve_hours'] ?? (await ctx.config.get('date.dispute_auto_resolve_hours'));
    const deadline = addHours(addHours(row.scheduled_end, windowHours), disputeAutoResolveHours);
    if (now.getTime() <= deadline.getTime()) continue; // cooldown still running

    const { rows: confirmationRows } = await ctx.db.query<{ user_id: string }>(
      `SELECT user_id FROM date_attendance_confirmations WHERE date_proposal_id = $1`,
      [row.id],
    );
    const confirmingUserId = confirmationRows[0]?.user_id;
    if (!confirmingUserId) continue; // defensive: 'disputed' should always carry exactly one confirmation
    const nonConfirmingUserId = confirmingUserId === row.proposer_id ? row.recipient_id : row.proposer_id;

    out.push({ dateProposalId: row.id, conversationId: row.conversation_id, confirmingUserId, nonConfirmingUserId });
  }
  return out;
}

/**
 * Idempotency marker only — `disputed` stays a terminal `DateProposalStatus`
 * (spec §13.3); this does not change `status`. Safe to call twice (a
 * second call is a no-op via `COALESCE`).
 */
export async function markDisputeResolved(ctx: Ctx, dateProposalId: string): Promise<void> {
  await ctx.db.query(
    `UPDATE date_proposals SET dispute_resolved_at = COALESCE(dispute_resolved_at, $2) WHERE id = $1`,
    [dateProposalId, ctx.clock.now()],
  );
}
