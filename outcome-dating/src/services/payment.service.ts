import { z } from 'zod';
import { getPool } from '../db/pool.js';
import { withTransaction } from '../db/tx.js';
import type { Ctx } from '../lib/ctx.js';
import { requireUserActor } from '../lib/ctx.js';
import { ConflictError, NotFoundError, PaymentError, ValidationError } from '../lib/errors.js';
import type { PaymentHold, PaymentHoldStatus, PaymentMethodSummary } from '../domain/types.js';
import * as ledger from './ledger.service.js';

/**
 * payment.service — payment methods (§24.10) and the hold lifecycle
 * (authorize/capture/release/refund) that wraps `ctx.payments`
 * (`PaymentProcessor`, spec §14).
 *
 * Owning agent: D.
 *
 * INVARIANT (the central one in this whole spec, §14.3): a user is never
 * charged unless BOTH holds on a date proposal are authorized.
 * `authorizeHold` only ever authorizes — it never captures. Capturing both
 * sides is `dateProposal.service.ts`'s job, calling `captureHold` for each
 * only after confirming both `payment_holds` rows are `authorized`. This
 * module contains no "capture both" convenience function.
 *
 * ORDERING (see the module's original JSDoc + INTERFACES.md #2): a naive
 * reading of "run every multi-step money operation in one DB transaction"
 * would try to wrap an entire authorize-then-persist (or capture-then-
 * persist) sequence, including the `ctx.payments` network call, inside one
 * `BEGIN...COMMIT`. That's not meaningful — a Postgres transaction can't
 * make an external HTTP call to the processor atomic with a local write,
 * and holding a DB transaction open across a network call is bad practice
 * regardless. So the granularity actually used here is:
 *
 *   1. call `ctx.payments.{authorize,capture,cancel,refund}` OUTSIDE any DB
 *      transaction,
 *   2. once that call returns, open ONE short-lived `withTransaction` that
 *      persists BOTH the `payment_holds` status transition AND the
 *      matching `ledger.recordEntry` row together, atomically — a hold
 *      status change must never be persisted without its ledger entry, or
 *      vice versa (this is the "one DB transaction" the module owns).
 *
 * If the process dies between step 1 and step 2, the processor has moved
 * money (or released/refunded it) with no local record yet. That gap is
 * exactly what `ledger.service#reconcileWithProcessor` (spec §25.9) exists
 * to find and flag — it is never silently "fixed" by retrying inside this
 * module, per the "never auto-corrects financial state" rule.
 *
 * Every hold-lifecycle function here is idempotent/resumable: given the
 * same `paymentHoldId` (or `dateProposalId`+`userId` for `authorizeHold`),
 * calling it again after it already reached its target state is a safe
 * no-op that neither re-calls the processor nor writes a second ledger
 * row. This is what makes a crash-and-retry, or a replayed webhook, safe
 * (spec's "idempotency" requirement) — see `handleProcessorWebhook` too.
 *
 * `dateProposal.service.ts` is this module's only caller for the hold
 * lifecycle; it references holds/amounts by id and cents, never reaching
 * into `ctx.payments` directly itself.
 */

// =====================================================================
// Row mapping
// =====================================================================

interface PaymentMethodRow {
  id: string;
  user_id: string;
  processor: string;
  processor_token: string;
  brand: string | null;
  last4: string | null;
  is_default: boolean;
  verified_at: Date | null;
  created_at: Date;
  deleted_at: Date | null;
}

function mapMethod(row: PaymentMethodRow): PaymentMethodSummary {
  return {
    id: row.id,
    userId: row.user_id,
    processor: row.processor,
    brand: row.brand,
    last4: row.last4,
    isDefault: row.is_default,
    verifiedAt: row.verified_at,
    createdAt: row.created_at,
  };
}

interface PaymentHoldRow {
  id: string;
  date_proposal_id: string;
  user_id: string;
  processor: string;
  processor_intent_id: string | null;
  amount_cents: string;
  currency: string;
  status: PaymentHoldStatus;
  authorized_at: Date | null;
  captured_at: Date | null;
  released_at: Date | null;
  refunded_at: Date | null;
  failure_reason: string | null;
}

function mapHold(row: PaymentHoldRow): PaymentHold {
  return {
    id: row.id,
    dateProposalId: row.date_proposal_id,
    userId: row.user_id,
    processor: row.processor,
    processorIntentId: row.processor_intent_id,
    amountCents: Number(row.amount_cents),
    currency: row.currency,
    status: row.status,
    authorizedAt: row.authorized_at,
    capturedAt: row.captured_at,
    releasedAt: row.released_at,
    refundedAt: row.refunded_at,
    failureReason: row.failure_reason,
  };
}

// =====================================================================
// Payment methods (§24.10)
// =====================================================================

const AddPaymentMethodSchema = z.object({
  processorToken: z.string().min(1),
  brand: z.string().min(1).max(40).optional(),
  last4: z
    .string()
    .regex(/^\d{4}$/)
    .optional(),
  makeDefault: z.boolean().optional(),
});

export interface AddPaymentMethodInput {
  processorToken: string;
  brand?: string;
  last4?: string;
  makeDefault?: boolean;
}

export async function addPaymentMethod(ctx: Ctx, input: AddPaymentMethodInput): Promise<PaymentMethodSummary> {
  const { userId } = requireUserActor(ctx);
  const parsed = AddPaymentMethodSchema.parse(input);

  return withTransaction(async (db) => {
    const { rows: countRows } = await db.query<{ c: string }>(
      `SELECT count(*)::text AS c FROM payment_methods WHERE user_id = $1 AND deleted_at IS NULL`,
      [userId],
    );
    const isFirst = Number(countRows[0]!.c) === 0;
    const makeDefault = parsed.makeDefault === true || isFirst;

    if (makeDefault) {
      await db.query(`UPDATE payment_methods SET is_default = false WHERE user_id = $1 AND deleted_at IS NULL`, [userId]);
    }

    const { rows } = await db.query<PaymentMethodRow>(
      `INSERT INTO payment_methods (user_id, processor, processor_token, brand, last4, is_default, verified_at, created_at)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $7)
       RETURNING *`,
      [userId, ctx.payments.name, parsed.processorToken, parsed.brand ?? null, parsed.last4 ?? null, makeDefault, ctx.clock.now()],
    );
    return mapMethod(rows[0]!);
  }, getPool());
}

export async function listPaymentMethods(ctx: Ctx): Promise<PaymentMethodSummary[]> {
  const { userId } = requireUserActor(ctx);
  const { rows } = await ctx.db.query<PaymentMethodRow>(
    `SELECT * FROM payment_methods WHERE user_id = $1 AND deleted_at IS NULL ORDER BY is_default DESC, created_at ASC`,
    [userId],
  );
  return rows.map(mapMethod);
}

export async function deletePaymentMethod(ctx: Ctx, paymentMethodId: string): Promise<void> {
  const { userId } = requireUserActor(ctx);
  if (!z.string().uuid().safeParse(paymentMethodId).success) throw new ValidationError('paymentMethodId must be a uuid');

  const { rowCount } = await ctx.db.query(
    `UPDATE payment_methods SET deleted_at = $3 WHERE id = $1 AND user_id = $2 AND deleted_at IS NULL`,
    [paymentMethodId, userId, ctx.clock.now()],
  );
  if (!rowCount) throw new NotFoundError('Payment method not found');
}

/** Note the frozen signature takes an explicit `userId`, not the current actor — `dateProposal.service.ts` needs the proposer's *and* the recipient's default method, only one of whom is `ctx.actor`. */
export async function getDefaultPaymentMethod(ctx: Ctx, userId: string): Promise<PaymentMethodSummary | null> {
  if (!z.string().uuid().safeParse(userId).success) throw new ValidationError('userId must be a uuid');

  const { rows } = await ctx.db.query<PaymentMethodRow>(
    `SELECT * FROM payment_methods
     WHERE user_id = $1 AND deleted_at IS NULL
     ORDER BY is_default DESC, created_at DESC
     LIMIT 1`,
    [userId],
  );
  return rows[0] ? mapMethod(rows[0]) : null;
}

// =====================================================================
// Hold lifecycle (§14)
// =====================================================================

const AuthorizeHoldSchema = z.object({
  dateProposalId: z.string().uuid(),
  userId: z.string().uuid(),
  amountCents: z.number().int().min(0),
  currency: z.string().min(1).max(8),
});

export interface AuthorizeHoldInput {
  dateProposalId: string;
  userId: string;
  amountCents: number;
  currency: string;
}

const TERMINAL_OR_ADVANCED_HOLD_STATUSES: readonly PaymentHoldStatus[] = ['authorized', 'capture_pending', 'captured', 'released', 'refunded'];

/**
 * Authorizes (never captures) a hold for one side of a date proposal.
 * Idempotent on `(dateProposalId, userId)`: if a hold already reached
 * `authorized` or beyond, returns it unchanged without calling the
 * processor again. On processor decline, persists `status = 'failed'` and
 * still records the 'authorization' ledger entry with the failure noted in
 * metadata (spec §14.8 — the attempt is part of the audit trail even when
 * declined).
 */
export async function authorizeHold(ctx: Ctx, input: AuthorizeHoldInput): Promise<PaymentHold> {
  const parsed = AuthorizeHoldSchema.parse(input);

  const { rows: existingRows } = await ctx.db.query<PaymentHoldRow>(
    `SELECT * FROM payment_holds WHERE date_proposal_id = $1 AND user_id = $2`,
    [parsed.dateProposalId, parsed.userId],
  );
  const existing = existingRows[0];
  if (existing && TERMINAL_OR_ADVANCED_HOLD_STATUSES.includes(existing.status)) {
    return mapHold(existing);
  }

  const method = await getDefaultPaymentMethod(ctx, parsed.userId);
  if (!method) {
    return persistAuthorizeResult(ctx, parsed, {
      status: 'failed',
      processorIntentId: null,
      failureReason: 'no_payment_method',
    });
  }

  const result = await ctx.payments.authorize({
    paymentMethodToken: await tokenFor(ctx, method),
    amountCents: parsed.amountCents,
    currency: parsed.currency,
    idempotencyKey: `hold:${parsed.dateProposalId}:${parsed.userId}`,
    metadata: { dateProposalId: parsed.dateProposalId, userId: parsed.userId },
  });

  return persistAuthorizeResult(ctx, parsed, result);
}

/** `getDefaultPaymentMethod` returns the PII-safe `PaymentMethodSummary` (no raw token) — this loads the actual `processor_token` for the one call site allowed to see it: handing it to `ctx.payments`. */
async function tokenFor(ctx: Ctx, method: PaymentMethodSummary): Promise<string> {
  const { rows } = await ctx.db.query<{ processor_token: string }>(`SELECT processor_token FROM payment_methods WHERE id = $1`, [method.id]);
  return rows[0]?.processor_token ?? '';
}

async function persistAuthorizeResult(
  ctx: Ctx,
  parsed: z.infer<typeof AuthorizeHoldSchema>,
  result: { status: 'authorized' | 'failed'; processorIntentId: string | null; failureReason: string | null },
): Promise<PaymentHold> {
  return withTransaction(async (db) => {
    const { rows } = await db.query<PaymentHoldRow>(
      `INSERT INTO payment_holds (date_proposal_id, user_id, processor, processor_intent_id, amount_cents, currency, status, authorized_at, failure_reason)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
       ON CONFLICT (date_proposal_id, user_id) DO UPDATE SET
         processor = EXCLUDED.processor,
         processor_intent_id = EXCLUDED.processor_intent_id,
         amount_cents = EXCLUDED.amount_cents,
         currency = EXCLUDED.currency,
         status = EXCLUDED.status,
         authorized_at = EXCLUDED.authorized_at,
         failure_reason = EXCLUDED.failure_reason
       RETURNING *`,
      [
        parsed.dateProposalId,
        parsed.userId,
        ctx.payments.name,
        result.processorIntentId,
        parsed.amountCents,
        parsed.currency,
        result.status,
        result.status === 'authorized' ? ctx.clock.now() : null,
        result.failureReason,
      ],
    );
    const hold = rows[0]!;

    const txCtx = { ...ctx, db };
    await ledger.recordEntry(txCtx, {
      userId: parsed.userId,
      dateProposalId: parsed.dateProposalId,
      paymentHoldId: hold.id,
      type: 'authorization',
      amountCents: parsed.amountCents,
      currency: parsed.currency,
      processorReference: result.processorIntentId,
      metadata: { status: result.status, failureReason: result.failureReason },
    });

    return mapHold(hold);
  }, getPool());
}

async function loadHold(ctx: Ctx, paymentHoldId: string): Promise<PaymentHoldRow> {
  if (!z.string().uuid().safeParse(paymentHoldId).success) throw new ValidationError('paymentHoldId must be a uuid');
  const { rows } = await ctx.db.query<PaymentHoldRow>(`SELECT * FROM payment_holds WHERE id = $1`, [paymentHoldId]);
  if (!rows[0]) throw new NotFoundError('Payment hold not found');
  return rows[0];
}

/** Captures a previously-authorized hold. Caller (`dateProposal.service.ts`) is responsible for only calling this once both sides' holds are authorized (spec §14.3). Idempotent: a hold already `captured` is returned unchanged. */
export async function captureHold(ctx: Ctx, paymentHoldId: string): Promise<PaymentHold> {
  const hold = await loadHold(ctx, paymentHoldId);
  if (hold.status === 'captured') return mapHold(hold);
  if (hold.status !== 'authorized' && hold.status !== 'capture_pending') {
    throw new ConflictError(`Cannot capture a hold in status '${hold.status}'`);
  }
  if (!hold.processor_intent_id) throw new PaymentError('Hold has no processor intent to capture');

  // Mark in-flight before the network call — a crash after this point but
  // before the result is persisted is visible to reconciliation as a hold
  // stuck in 'capture_pending' rather than silently looking untouched.
  if (hold.status === 'authorized') {
    await ctx.db.query(`UPDATE payment_holds SET status = 'capture_pending' WHERE id = $1 AND status = 'authorized'`, [paymentHoldId]);
  }

  const result = await ctx.payments.capture({
    processorIntentId: hold.processor_intent_id,
    idempotencyKey: `capture:${paymentHoldId}`,
  });

  return withTransaction(async (db) => {
    const capturedAmount = result.capturedAmountCents ?? Number(hold.amount_cents);
    const { rows } = await db.query<PaymentHoldRow>(
      `UPDATE payment_holds SET status = $2, captured_at = $3, failure_reason = $4 WHERE id = $1 RETURNING *`,
      [paymentHoldId, result.status, result.status === 'captured' ? ctx.clock.now() : null, result.failureReason],
    );
    const updated = rows[0]!;

    const txCtx = { ...ctx, db };
    await ledger.recordEntry(txCtx, {
      userId: hold.user_id,
      dateProposalId: hold.date_proposal_id,
      paymentHoldId,
      type: 'capture',
      amountCents: result.status === 'captured' ? capturedAmount : 0,
      currency: hold.currency,
      processorReference: hold.processor_intent_id,
      metadata: { status: result.status, failureReason: result.failureReason },
    });

    return mapHold(updated);
  }, getPool());
}

/** Releases (voids) an authorized-but-not-captured hold. Idempotent: a hold already `released` is returned unchanged. Never throws on a processor decline — declines are logged and the hold is left in its current status so a retry (or reconciliation) can resolve it (spec §14.5, §14.6). */
export async function releaseHold(ctx: Ctx, paymentHoldId: string): Promise<PaymentHold> {
  const hold = await loadHold(ctx, paymentHoldId);
  if (hold.status === 'released') return mapHold(hold);
  if (hold.status !== 'authorized') {
    throw new ConflictError(`Cannot release a hold in status '${hold.status}'`);
  }
  if (!hold.processor_intent_id) throw new PaymentError('Hold has no processor intent to release');

  const result = await ctx.payments.cancel({
    processorIntentId: hold.processor_intent_id,
    reason: 'date_proposal_release',
    idempotencyKey: `release:${paymentHoldId}`,
  });

  if (result.status !== 'released') {
    ctx.logger.warn('payment.release_failed', { paymentHoldId, failureReason: result.failureReason });
    return mapHold(hold);
  }

  return withTransaction(async (db) => {
    const { rows } = await db.query<PaymentHoldRow>(
      `UPDATE payment_holds SET status = 'released', released_at = $2 WHERE id = $1 RETURNING *`,
      [paymentHoldId, ctx.clock.now()],
    );
    const updated = rows[0]!;

    const txCtx = { ...ctx, db };
    await ledger.recordEntry(txCtx, {
      userId: hold.user_id,
      dateProposalId: hold.date_proposal_id,
      paymentHoldId,
      type: 'release',
      amountCents: Number(hold.amount_cents),
      currency: hold.currency,
      processorReference: hold.processor_intent_id,
      metadata: { status: result.status },
    });

    return mapHold(updated);
  }, getPool());
}

/**
 * Refunds a captured hold, full or partial cents. Used by the §14.7
 * cancellation policy.
 *
 * ROUNDING RULE (see `dateProposal.service.ts` for where percentages are
 * turned into cents): any percentage-to-cents conversion happens at the
 * CALLER, using `Math.floor(amountCents * percent / 100)` — round DOWN,
 * always in the platform's favor, never refund a fraction of a cent more
 * than the policy strictly implies. This function itself only ever
 * receives already-computed integer cents.
 *
 * IDEMPOTENCY: cumulative refunded cents for a hold is derived by summing
 * this hold's successful `payment_ledger` 'refund' rows (no separate
 * `refunded_amount_cents` column exists — see schema). A refund call is
 * only ever attempted for the *remaining* un-refunded delta, so calling
 * `refundHold(ctx, id, 2000)` twice in a row refunds 2000 cents once, not
 * 4000 — the second call sees `alreadyRefunded >= target` and no-ops.
 * A refund attempt that fails at the processor is logged, not recorded in
 * the ledger — only successful money movement is ever summed as "already
 * refunded", so a failed attempt can safely be retried later without
 * under- or over-counting.
 */
export async function refundHold(ctx: Ctx, paymentHoldId: string, amountCents?: number): Promise<PaymentHold> {
  if (amountCents !== undefined && (!Number.isInteger(amountCents) || amountCents < 0)) {
    throw new ValidationError('amountCents must be a non-negative integer');
  }

  const hold = await loadHold(ctx, paymentHoldId);
  if (hold.status !== 'captured' && hold.status !== 'refunded') {
    throw new ConflictError(`Cannot refund a hold in status '${hold.status}'`);
  }
  if (!hold.processor_intent_id) throw new PaymentError('Hold has no processor intent to refund');

  const target = amountCents ?? Number(hold.amount_cents);
  if (target > Number(hold.amount_cents)) {
    throw new ValidationError('Refund amount exceeds the captured amount');
  }

  const entries = await ledger.listEntriesForDateProposal(ctx, hold.date_proposal_id);
  const alreadyRefunded = entries
    .filter((e) => e.paymentHoldId === paymentHoldId && e.type === 'refund')
    .reduce((sum, e) => sum + e.amountCents, 0);

  if (alreadyRefunded >= target) {
    return mapHold(hold); // idempotent no-op — nothing left to refund toward this target
  }
  const toRefundNow = target - alreadyRefunded;

  const result = await ctx.payments.refund({
    processorIntentId: hold.processor_intent_id,
    amountCents: toRefundNow,
    reason: 'date_proposal_cancellation',
    idempotencyKey: `refund:${paymentHoldId}:${alreadyRefunded}:${toRefundNow}`,
  });

  if (result.status !== 'refunded') {
    ctx.logger.warn('payment.refund_failed', { paymentHoldId, failureReason: result.failureReason });
    return mapHold(hold);
  }

  const totalRefunded = alreadyRefunded + toRefundNow;
  const isFullyRefunded = totalRefunded >= Number(hold.amount_cents);

  return withTransaction(async (db) => {
    const { rows } = await db.query<PaymentHoldRow>(
      `UPDATE payment_holds SET status = $2, refunded_at = $3 WHERE id = $1 RETURNING *`,
      [paymentHoldId, isFullyRefunded ? 'refunded' : hold.status, ctx.clock.now()],
    );
    const updated = rows[0]!;

    const txCtx = { ...ctx, db };
    await ledger.recordEntry(txCtx, {
      userId: hold.user_id,
      dateProposalId: hold.date_proposal_id,
      paymentHoldId,
      type: 'refund',
      amountCents: toRefundNow,
      currency: hold.currency,
      processorReference: result.processorRefundId,
      metadata: { status: result.status },
    });

    return mapHold(updated);
  }, getPool());
}

// =====================================================================
// Webhooks (§24.10, §25.9)
// =====================================================================

const WebhookEventSchema = z.object({
  type: z.enum(['payment_intent.succeeded', 'payment_intent.payment_failed', 'charge.refunded', 'charge.dispute.created', 'charge.dispute.closed']),
  processorIntentId: z.string().min(1),
  amountCents: z.number().int().min(0).optional(),
  processorReference: z.string().optional(),
});

/**
 * Entry point for `POST /webhooks/payments` (spec §24.10) — reconciles an
 * inbound processor event against local `payment_holds` state. The route
 * handler verifies the webhook signature before calling this; this
 * function trusts its input (still zod-validates *shape*, not authenticity).
 *
 * Idempotent: before writing anything, checks whether a ledger row for
 * this hold/type/reference already exists and no-ops if so — a webhook
 * redelivery (the same Stripe event id retried, or two webhooks racing a
 * direct `captureHold`/`refundHold` call) can never double-record.
 *
 * Only touches `payment_holds`/`payment_ledger` (this module's own
 * domain) — it deliberately does NOT reach into `dateProposal.service.ts`
 * to escalate a dispute/chargeback to the proposal's status, since
 * `payment -> ledger` is the only sanctioned outgoing edge for this module
 * (INTERFACES.md's call graph); calling back into `dateProposal.service`
 * would create `payment -> dateProposal -> payment`, a cycle the graph
 * explicitly forbids. Surfacing a dispute event to an admin/dashboard is
 * left to a job outside this module's frozen function list.
 */
export async function handleProcessorWebhook(ctx: Ctx, event: unknown): Promise<void> {
  const parsed = WebhookEventSchema.parse(event);

  const { rows } = await ctx.db.query<PaymentHoldRow>(`SELECT * FROM payment_holds WHERE processor_intent_id = $1`, [parsed.processorIntentId]);
  const hold = rows[0];
  if (!hold) {
    ctx.logger.warn('payment.webhook_unknown_intent', { processorIntentId: parsed.processorIntentId, type: parsed.type });
    return;
  }

  const ledgerType = webhookLedgerType(parsed.type);
  const reference = parsed.processorReference ?? parsed.processorIntentId;

  const { rows: dupRows } = await ctx.db.query(
    `SELECT 1 FROM payment_ledger WHERE payment_hold_id = $1 AND type = $2 AND processor_reference = $3 LIMIT 1`,
    [hold.id, ledgerType, reference],
  );
  if (dupRows.length > 0) return; // already recorded — replayed webhook, no-op

  await withTransaction(async (db) => {
    const amount = parsed.amountCents ?? Number(hold.amount_cents);

    if (parsed.type === 'payment_intent.succeeded' && hold.status !== 'captured') {
      await db.query(`UPDATE payment_holds SET status = 'captured', captured_at = $2 WHERE id = $1`, [hold.id, ctx.clock.now()]);
    } else if (parsed.type === 'payment_intent.payment_failed' && hold.status !== 'captured' && hold.status !== 'refunded') {
      await db.query(`UPDATE payment_holds SET status = 'failed', failure_reason = 'webhook_reported_failure' WHERE id = $1`, [hold.id]);
    } else if (parsed.type === 'charge.refunded') {
      await db.query(`UPDATE payment_holds SET status = 'refunded', refunded_at = $2 WHERE id = $1`, [hold.id, ctx.clock.now()]);
    }
    // dispute/dispute-closed intentionally leave payment_holds.status alone
    // — there is no 'disputed' PaymentHoldStatus (§23.18); only the ledger
    // records the event.

    const txCtx = { ...ctx, db };
    await ledger.recordEntry(txCtx, {
      userId: hold.user_id,
      dateProposalId: hold.date_proposal_id,
      paymentHoldId: hold.id,
      type: ledgerType,
      amountCents: amount,
      currency: hold.currency,
      processorReference: reference,
      metadata: { source: 'webhook', eventType: parsed.type },
    });
  }, getPool());
}

function webhookLedgerType(eventType: z.infer<typeof WebhookEventSchema>['type']): 'capture' | 'refund' | 'dispute' | 'chargeback' {
  switch (eventType) {
    case 'payment_intent.succeeded':
    case 'payment_intent.payment_failed':
      return 'capture';
    case 'charge.refunded':
      return 'refund';
    case 'charge.dispute.created':
      return 'dispute';
    case 'charge.dispute.closed':
      return 'chargeback';
  }
}
