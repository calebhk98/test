import { NotImplementedError } from '../../lib/errors.js';
import type {
  AuthorizeParams,
  AuthorizeResult,
  CancelParams,
  CancelResult,
  CaptureParams,
  CaptureResult,
  PaymentProcessor,
  RefundParams,
  RefundResult,
} from './processor.port.js';

/**
 * Stripe adapter for `PaymentProcessor` (spec §14 "Use a payment processor
 * that supports authorization holds and manual capture, such as Stripe.").
 *
 * This is a documented STUB: the `stripe` npm SDK is deliberately NOT a
 * dependency of this foundation layer (keeps `npm install`/`tsc` green
 * with zero external service credentials), so every method throws
 * `NotImplementedError`. The JSDoc on each method is the exact contract
 * the real implementation must satisfy, a future agent adding real Stripe
 * support should need to change only this file, install `stripe`, and
 * supply `STRIPE_SECRET_KEY`/`STRIPE_WEBHOOK_SECRET` (see .env.example).
 *
 * Construction takes the secret key so the real implementation's
 * constructor signature doesn't need to change later:
 * `new StripeProcessor(getEnv().STRIPE_SECRET_KEY)`.
 */
export class StripeProcessor implements PaymentProcessor {
  readonly name = 'stripe';

  constructor(private readonly secretKey: string | undefined) {}

  /**
   * Real implementation: `stripe.paymentIntents.create({ amount, currency,
   * payment_method: params.paymentMethodToken, confirm: true,
   * capture_method: 'manual', off_session: true, metadata },
   * { idempotencyKey: params.idempotencyKey })`.
   *
   * `capture_method: 'manual'` is what makes this an authorization hold
   * rather than an immediate charge (spec §14.2 Step 1/2), Stripe
   * authorizes and holds the funds but does not transfer them until a
   * later `capture`. Map the returned PaymentIntent's `status`:
   * `requires_capture` -> `{ status: 'authorized' }`; anything indicating
   * a decline (`status === 'requires_payment_method'` after a failed
   * confirm, or a caught `StripeCardError`) -> `{ status: 'failed',
   * failureReason: error.decline_code ?? error.code }`. Always return the
   * created intent's id as `processorIntentId` (even on failure, if one
   * was created) so it's traceable in payment_holds/payment_ledger.
   */
  async authorize(_params: AuthorizeParams): Promise<AuthorizeResult> {
    throw new NotImplementedError('StripeProcessor.authorize');
  }

  /**
   * Real implementation: `stripe.paymentIntents.capture(params.processorIntentId,
   * params.amountCents !== undefined ? { amount_to_capture: params.amountCents } : {},
   * { idempotencyKey: params.idempotencyKey })` (spec §14.2 Step 3, only
   * called once both sides' holds are authorized, see
   * `dateProposal.service.ts`). Map `status === 'succeeded'` ->
   * `{ status: 'captured', capturedAmountCents: intent.amount_received }`;
   * a caught error -> `{ status: 'failed', failureReason: error.code }`.
   */
  async capture(_params: CaptureParams): Promise<CaptureResult> {
    throw new NotImplementedError('StripeProcessor.capture');
  }

  /**
   * Real implementation: `stripe.paymentIntents.cancel(params.processorIntentId,
   * { cancellation_reason: 'requested_by_customer' }, { idempotencyKey:
   * params.idempotencyKey })`, releases an authorized-but-not-captured
   * hold (spec §14.5, §14.6). Only valid while the intent is still in a
   * cancelable state (`requires_capture`, `requires_payment_method`,
   * `requires_confirmation`); a caught `StripeInvalidRequestError` for an
   * already-captured/canceled intent maps to `{ status: 'failed',
   * failureReason: error.code }`.
   */
  async cancel(_params: CancelParams): Promise<CancelResult> {
    throw new NotImplementedError('StripeProcessor.cancel');
  }

  /**
   * Real implementation: `stripe.refunds.create({ payment_intent:
   * params.processorIntentId, amount: params.amountCents, reason:
   * 'requested_by_customer' }, { idempotencyKey: params.idempotencyKey })`
   * (spec §14.7 post-capture cancellation/refund policy). Map
   * `refund.status === 'succeeded' | 'pending'` -> `{ status: 'refunded',
   * processorRefundId: refund.id }`; `'failed'` or a caught error ->
   * `{ status: 'failed', failureReason: refund.failure_reason ?? error.code }`.
   */
  async refund(_params: RefundParams): Promise<RefundResult> {
    throw new NotImplementedError('StripeProcessor.refund');
  }
}

// Webhook handling note (POST /webhooks/payments, spec §24.10, consumed by
// §25.9 payment reconciliation): verify with
// `stripe.webhooks.constructEvent(rawBody, signatureHeader,
// STRIPE_WEBHOOK_SECRET)`, then reconcile `payment_intent.succeeded` /
// `payment_intent.payment_failed` / `charge.refunded` /
// `charge.dispute.created` events against `payment_holds`/`payment_ledger`
// by `processor_intent_id`. This lives in the HTTP layer (owned by
// whichever agent wires up Fastify routes), not in this port, it calls
// back into `ledger.service.ts` and `dateProposal.service.ts`, it doesn't
// implement `PaymentProcessor`.
