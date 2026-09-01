import { NotImplementedError } from '../../../lib/errors.js';
import type { EmailSendParams, EmailSendResult, EmailSender } from '../ports/email.port.js';

/**
 * Amazon SES adapter for `EmailSender` (spec §20.2 email channel).
 *
 * Documented STUB, same pattern as the push adapters and
 * `src/services/payments/stripe.processor.ts`: the `@aws-sdk/client-sesv2`
 * package is deliberately NOT a dependency of this foundation layer; every
 * method throws `NotImplementedError`.
 *
 * Construction takes the region/credentials so the real implementation's
 * constructor signature doesn't need to change later:
 * `new SesEmailSender({ region: getEnv().SES_REGION, fromAddress: getEnv().SES_FROM_ADDRESS })`
 * (credentials themselves come from the standard AWS credential chain, not
 * a constructor argument, never hardcode a secret key here).
 */
export class SesEmailSender implements EmailSender {
  readonly name = 'ses';

  constructor(private readonly config: { region: string; fromAddress: string } | undefined) {}

  /**
   * Real implementation: render `params.templateKey` + `params.data`
   * through this build's own (non-generative, spec §1 rule 9) static
   * email template layer to get a subject+HTML+text body, then:
   *
   * ```
   * await sesClient.send(new SendEmailCommand({
   *   FromEmailAddress: config.fromAddress,
   *   Destination: { ToAddresses: [params.toEmail] },
   *   Content: { Simple: { Subject: {...}, Body: { Html: {...}, Text: {...} } } },
   * }));
   * ```
   *
   * Map a caught error: `MessageRejected` with a permanent-bounce
   * suppression reason -> `{ status: 'invalid_recipient' }`; anything else
   * -> `{ status: 'failed', failureReason: error.name }`. Success ->
   * `{ status: 'sent', providerMessageId: response.MessageId }`.
   */
  async send(_params: EmailSendParams): Promise<EmailSendResult> {
    throw new NotImplementedError('SesEmailSender.send');
  }
}
