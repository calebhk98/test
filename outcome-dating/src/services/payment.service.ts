import type { Ctx } from '../lib/ctx.js';
import { NotImplementedError } from '../lib/errors.js';
import type { PaymentHold, PaymentMethodSummary } from '../domain/types.js';

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
 * sides is `dateProposal.service.ts`'s job (`acceptDateProposal`, after it
 * confirms both `payment_holds` rows are `authorized`), calling
 * `captureHold` for each. This module must not contain any "capture both"
 * convenience function that could be called with only one side ready.
 *
 * Every state-changing call here:
 *  1. calls the matching `ctx.payments` method,
 *  2. persists the resulting `payment_holds.status` transition,
 *  3. calls `ledger.service#recordEntry` with the matching
 *     `LedgerEntryType` (authorize -> 'authorization', capture ->
 *     'capture', release -> 'release', refund -> 'refund'),
 * all inside one transaction (`withTransaction`) — a hold status change
 * must never be persisted without its ledger entry, or vice versa.
 *
 * `dateProposal.service.ts` is this module's only caller for the hold
 * lifecycle; it references holds/amounts by id and cents, never reaching
 * into `ctx.payments` directly itself.
 */

export interface AddPaymentMethodInput {
  /** Opaque processor-side token — never a raw card number (spec §28.4). */
  processorToken: string;
  brand?: string;
  last4?: string;
  makeDefault?: boolean;
}

export async function addPaymentMethod(ctx: Ctx, input: AddPaymentMethodInput): Promise<PaymentMethodSummary> {
  throw new NotImplementedError('payment.addPaymentMethod');
}

export async function listPaymentMethods(ctx: Ctx): Promise<PaymentMethodSummary[]> {
  throw new NotImplementedError('payment.listPaymentMethods');
}

export async function deletePaymentMethod(ctx: Ctx, paymentMethodId: string): Promise<void> {
  throw new NotImplementedError('payment.deletePaymentMethod');
}

export async function getDefaultPaymentMethod(ctx: Ctx, userId: string): Promise<PaymentMethodSummary | null> {
  throw new NotImplementedError('payment.getDefaultPaymentMethod');
}

export interface AuthorizeHoldInput {
  dateProposalId: string;
  userId: string;
  amountCents: number;
  currency: string;
}

/** Authorizes (never captures) a hold for one side of a date proposal. On processor decline, persists `payment_holds.status = 'failed'` and still records the 'authorization' ledger entry with the failure noted in metadata (spec §14.8 — the attempt is part of the audit trail even when declined). */
export async function authorizeHold(ctx: Ctx, input: AuthorizeHoldInput): Promise<PaymentHold> {
  throw new NotImplementedError('payment.authorizeHold');
}

/** Captures a previously-authorized hold. Caller (`dateProposal.service.ts`) is responsible for only calling this once both sides' holds are authorized (spec §14.3). */
export async function captureHold(ctx: Ctx, paymentHoldId: string): Promise<PaymentHold> {
  throw new NotImplementedError('payment.captureHold');
}

/** Releases (voids) an authorized-but-not-captured hold — used for declines, expiry, and the "release the other side" half of a payment_failed cascade (spec §14.5, §14.6). */
export async function releaseHold(ctx: Ctx, paymentHoldId: string): Promise<PaymentHold> {
  throw new NotImplementedError('payment.releaseHold');
}

/** Refunds a captured hold, full or partial cents. Used by the §14.7 cancellation policy. */
export async function refundHold(ctx: Ctx, paymentHoldId: string, amountCents?: number): Promise<PaymentHold> {
  throw new NotImplementedError('payment.refundHold');
}

/** Entry point for `POST /webhooks/payments` (spec §24.10) — reconciles an inbound processor event against local `payment_holds` state. The route handler verifies the webhook signature before calling this; this function trusts its input. */
export async function handleProcessorWebhook(ctx: Ctx, event: unknown): Promise<void> {
  throw new NotImplementedError('payment.handleProcessorWebhook');
}
