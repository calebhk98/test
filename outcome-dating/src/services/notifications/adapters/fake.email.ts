import { newId } from '../../../lib/ids.js';
import type { EmailSendParams, EmailSendResult, EmailSender } from '../ports/email.port.js';

/**
 * In-memory, deterministic `EmailSender` for dev and tests. Same
 * magic-substring convention as `FakePushSender`/`FakeProcessor`:
 *
 *   toEmail contains "invalid_recipient"  -> status: 'invalid_recipient'
 *   toEmail contains "fail_send"          -> status: 'failed' (transient)
 *   anything else                         -> status: 'sent'
 */
export class FakeEmailSender implements EmailSender {
  readonly name = 'fake';

  readonly sent: EmailSendParams[] = [];

  async send(params: EmailSendParams): Promise<EmailSendResult> {
    this.sent.push(params);

    if (params.toEmail.includes('invalid_recipient')) {
      return { status: 'invalid_recipient', providerMessageId: null, failureReason: 'hard_bounce' };
    }
    if (params.toEmail.includes('fail_send')) {
      return { status: 'failed', providerMessageId: null, failureReason: 'transient_provider_error' };
    }
    return { status: 'sent', providerMessageId: `fake_email_${newId()}`, failureReason: null };
  }

  clear(): void {
    this.sent.length = 0;
  }
}
