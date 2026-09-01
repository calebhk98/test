/**
 * PaymentProcessor, the port every payment adapter implements.
 *
 * Spec §14 requires "a payment processor that supports authorization holds
 * and manual capture" and forbids storing card numbers (§28.4), callers
 * only ever pass an opaque `paymentMethodToken` from `payment_methods`
 * (never raw card data). The four operations below map 1:1 onto the §14.2
 * escrow flow:
 *
 *   authorize  -> Step 1/2: hold funds without charging (proposer, then recipient)
 *   capture    -> Step 3: charge a previously-authorized hold, once both are authorized
 *   cancel     -> release an authorized-but-not-captured hold (expiry, decline, payment_failed cascade)
 *   refund     -> return captured funds (post-capture cancellation per §14.7)
 *
 * `dateProposal.service.ts` is the only caller that should invoke this
 * directly, it owns the two-hold choreography (§14.2-§14.6) and writes
 * the resulting `payment_holds` rows and `payment_ledger` entries (via
 * `ledger.service.ts`). `payment.service.ts` wraps this port with the
 * user-facing `/payment-methods` endpoints (§24.10) and exposes the
 * currently-configured adapter to the rest of the app.
 *
 * Implementations MUST be idempotent-safe to retry on network failure
 * (callers may retry with the same `idempotencyKey`) and MUST NOT throw
 * for an expected decline, declines are a normal `status: 'failed'`
 * result, not an exception. Reserve thrown errors for transport/
 * infrastructure failures (network, auth, malformed config).
 */

export interface AuthorizeParams {
  /** Opaque token identifying the payment method at the processor (payment_methods.processor_token). Never a raw card number. */
  paymentMethodToken: string;
  amountCents: number;
  currency: string;
  /** Idempotency key for safe retries, callers pass e.g. `hold:{dateProposalId}:{userId}`. */
  idempotencyKey: string;
  metadata?: Record<string, string>;
}

export interface AuthorizeResult {
  status: 'authorized' | 'failed';
  /** Processor-side reference (e.g. Stripe PaymentIntent id). Present when status is 'authorized', and also when 'failed' if the processor created-then-declined an intent. */
  processorIntentId: string | null;
  failureReason: string | null;
}

export interface CaptureParams {
  processorIntentId: string;
  /** Defaults to the full authorized amount if omitted. */
  amountCents?: number;
  idempotencyKey: string;
}

export interface CaptureResult {
  status: 'captured' | 'failed';
  capturedAmountCents: number | null;
  failureReason: string | null;
}

export interface CancelParams {
  processorIntentId: string;
  reason?: string;
  idempotencyKey: string;
}

export interface CancelResult {
  status: 'released' | 'failed';
  failureReason: string | null;
}

export interface RefundParams {
  processorIntentId: string;
  amountCents: number;
  reason?: string;
  idempotencyKey: string;
}

export interface RefundResult {
  status: 'refunded' | 'failed';
  processorRefundId: string | null;
  failureReason: string | null;
}

export interface PaymentProcessor {
  /** Adapter name, stored on payment_holds.processor for auditability (e.g. "fake", "stripe"). */
  readonly name: string;

  /** Create an authorization hold. No charge yet (spec §14.2 Step 1/2). */
  authorize(params: AuthorizeParams): Promise<AuthorizeResult>;

  /** Capture a previously-authorized hold (spec §14.2 Step 3). Only called once both sides' holds are authorized. */
  capture(params: CaptureParams): Promise<CaptureResult>;

  /** Release (void) an authorized-but-not-captured hold, expiry, decline, or payment_failed cascade (spec §14.5, §14.6, §14.7). */
  cancel(params: CancelParams): Promise<CancelResult>;

  /** Refund a previously-captured amount, full or partial (spec §14.7 cancellation policy). */
  refund(params: RefundParams): Promise<RefundResult>;
}
