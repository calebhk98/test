import { newId } from '../../../lib/ids.js';
import type { PushSendParams, PushSendResult, PushSender } from '../ports/push.port.js';

/**
 * In-memory, deterministic `PushSender` for dev and tests, same shape as
 * `src/services/payments/fake.processor.ts`'s `FakeProcessor`: magic
 * substrings in the input (here, `token`) select behavior deterministically
 * instead of randomness, so failure paths are exercisable without mocking:
 *
 *   token contains "invalid_token"  -> status: 'invalid_token'
 *   token contains "fail_send"      -> status: 'failed' (transient)
 *   anything else                   -> status: 'sent'
 *
 * Every attempted send is recorded in `sent` (including failures, so tests
 * can assert on send COUNT for coalescing, e.g. "5 messages -> exactly 1
 * PushSender.send call", as well as on content). One instance is one
 * isolated "device fleet"; construct a fresh one per test.
 */
export class FakePushSender implements PushSender {
  readonly name = 'fake';

  readonly sent: PushSendParams[] = [];

  async send(params: PushSendParams): Promise<PushSendResult> {
    this.sent.push(params);

    if (params.token.includes('invalid_token')) {
      return { status: 'invalid_token', providerMessageId: null, failureReason: 'not_registered' };
    }
    if (params.token.includes('fail_send')) {
      return { status: 'failed', providerMessageId: null, failureReason: 'transient_provider_error' };
    }
    return { status: 'sent', providerMessageId: `fake_push_${newId()}`, failureReason: null };
  }

  clear(): void {
    this.sent.length = 0;
  }
}
