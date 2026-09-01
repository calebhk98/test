import { newId } from '../../../lib/ids.js';
import type { SmsSendParams, SmsSendResult, SmsSender } from '../ports/sms.port.js';

/**
 * In-memory, deterministic `SmsSender` for dev and tests — same shape and
 * same magic-substring convention as `FakePushSender`/`FakeEmailSender`:
 *
 *   toE164 contains "invalid_number"  -> status: 'invalid_number'
 *   toE164 contains "fail_send"       -> status: 'failed' (transient)
 *   anything else                     -> status: 'sent'
 *
 * Every attempted send is recorded in `sent` (including failures), so
 * tests can assert on send COUNT for coalescing/cost-cap behavior — e.g.
 * "12 match events in a day -> at most N SmsSender.send calls" — as well
 * as on content. One instance is one isolated "carrier connection";
 * construct a fresh one per test.
 */
export class FakeSmsSender implements SmsSender {
  readonly name = 'fake';

  readonly sent: SmsSendParams[] = [];

  async send(params: SmsSendParams): Promise<SmsSendResult> {
    this.sent.push(params);

    if (params.toE164.includes('invalid_number')) {
      return { status: 'invalid_number', providerMessageId: null, failureReason: 'unreachable_number' };
    }
    if (params.toE164.includes('fail_send')) {
      return { status: 'failed', providerMessageId: null, failureReason: 'transient_provider_error' };
    }
    return { status: 'sent', providerMessageId: `fake_sms_${newId()}`, failureReason: null };
  }

  clear(): void {
    this.sent.length = 0;
  }
}
