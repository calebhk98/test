import { newId } from '../../lib/ids.js';
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
 * In-memory, deterministic `PaymentProcessor` for dev and tests
 * (spec §14, §32 "no Redis" simplification extends to "no live payment
 * processor either" for the default MVP dev loop).
 *
 * Deterministic failure injection: tests select behavior via magic
 * substrings in `paymentMethodToken` rather than randomness, so a failure
 * path (spec §14.5 "Payment Failure Cases") is exercisable without mocking:
 *
 *   contains "fail_authorize"  -> authorize() returns status: 'failed'
 *   contains "fail_capture"    -> authorize() succeeds, capture() fails
 *   anything else              -> succeeds at every step
 *
 * State lives in a `Map` on the instance, one `FakeProcessor` instance is
 * one isolated "processor account". Tests that need isolation should
 * construct a fresh instance rather than sharing a singleton.
 */

type IntentStatus = 'authorized' | 'captured' | 'released' | 'refunded' | 'failed';

interface FakeIntent {
  id: string;
  token: string;
  amountCents: number;
  currency: string;
  status: IntentStatus;
  capturedAmountCents: number;
  refundedAmountCents: number;
}

export class FakeProcessor implements PaymentProcessor {
  readonly name = 'fake';

  private intents = new Map<string, FakeIntent>();
  private idempotency = new Map<string, unknown>();

  private memoize<T>(key: string, compute: () => T): T {
    if (this.idempotency.has(key)) return this.idempotency.get(key) as T;
    const result = compute();
    this.idempotency.set(key, result);
    return result;
  }

  async authorize(params: AuthorizeParams): Promise<AuthorizeResult> {
    return this.memoize(`authorize:${params.idempotencyKey}`, () => {
      if (params.paymentMethodToken.includes('fail_authorize')) {
        return { status: 'failed', processorIntentId: null, failureReason: 'card_declined' } satisfies AuthorizeResult;
      }

      const id = `pi_fake_${newId()}`;
      this.intents.set(id, {
        id,
        token: params.paymentMethodToken,
        amountCents: params.amountCents,
        currency: params.currency,
        status: 'authorized',
        capturedAmountCents: 0,
        refundedAmountCents: 0,
      });
      return { status: 'authorized', processorIntentId: id, failureReason: null } satisfies AuthorizeResult;
    });
  }

  async capture(params: CaptureParams): Promise<CaptureResult> {
    return this.memoize(`capture:${params.idempotencyKey}`, () => {
      const intent = this.intents.get(params.processorIntentId);
      if (!intent || intent.status !== 'authorized') {
        return { status: 'failed', capturedAmountCents: null, failureReason: 'no_authorized_intent' } satisfies CaptureResult;
      }
      if (intent.token.includes('fail_capture')) {
        intent.status = 'failed';
        return { status: 'failed', capturedAmountCents: null, failureReason: 'capture_declined' } satisfies CaptureResult;
      }

      const amount = params.amountCents ?? intent.amountCents;
      intent.status = 'captured';
      intent.capturedAmountCents = amount;
      return { status: 'captured', capturedAmountCents: amount, failureReason: null } satisfies CaptureResult;
    });
  }

  async cancel(params: CancelParams): Promise<CancelResult> {
    return this.memoize(`cancel:${params.idempotencyKey}`, () => {
      const intent = this.intents.get(params.processorIntentId);
      if (!intent || intent.status !== 'authorized') {
        return { status: 'failed', failureReason: 'no_authorized_intent' } satisfies CancelResult;
      }
      intent.status = 'released';
      return { status: 'released', failureReason: null } satisfies CancelResult;
    });
  }

  async refund(params: RefundParams): Promise<RefundResult> {
    return this.memoize(`refund:${params.idempotencyKey}`, () => {
      const intent = this.intents.get(params.processorIntentId);
      if (!intent || intent.status !== 'captured') {
        return { status: 'failed', processorRefundId: null, failureReason: 'no_captured_intent' } satisfies RefundResult;
      }
      if (intent.refundedAmountCents + params.amountCents > intent.capturedAmountCents) {
        return { status: 'failed', processorRefundId: null, failureReason: 'refund_exceeds_captured' } satisfies RefundResult;
      }
      intent.refundedAmountCents += params.amountCents;
      if (intent.refundedAmountCents === intent.capturedAmountCents) {
        intent.status = 'refunded';
      }
      return { status: 'refunded', processorRefundId: `re_fake_${newId()}`, failureReason: null } satisfies RefundResult;
    });
  }

  /** Test helper: inspect current intent state directly. */
  _debugGetIntent(processorIntentId: string): Readonly<FakeIntent> | undefined {
    return this.intents.get(processorIntentId);
  }
}
