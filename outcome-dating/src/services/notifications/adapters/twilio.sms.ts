import { NotImplementedError } from '../../../lib/errors.js';
import type { SmsSendParams, SmsSendResult, SmsSender } from '../ports/sms.port.js';

/**
 * Twilio adapter for `SmsSender` (§20.2-shaped SMS channel, Twilio is the
 * standard choice for programmable SMS).
 *
 * Documented STUB, exactly like `FcmPushSender`/`SesEmailSender`/
 * `src/services/payments/stripe.processor.ts`: the `twilio` npm SDK is
 * deliberately NOT a dependency of this foundation layer, so every method
 * throws `NotImplementedError`. The JSDoc on `send` is the exact contract a
 * real implementation must satisfy, installing `twilio` and supplying
 * `TWILIO_ACCOUNT_SID`/`TWILIO_AUTH_TOKEN`/`TWILIO_FROM_NUMBER` (or
 * equivalent) should be the only change needed.
 *
 * Construction takes the account credential + sending number so the real
 * implementation's constructor signature doesn't need to change later:
 * `new TwilioSmsSender({ accountSid: getEnv().TWILIO_ACCOUNT_SID, authToken: getEnv().TWILIO_AUTH_TOKEN, fromNumber: getEnv().TWILIO_FROM_NUMBER })`.
 */
export class TwilioSmsSender implements SmsSender {
  readonly name = 'twilio';

  constructor(private readonly config: { accountSid: string; authToken: string; fromNumber: string } | undefined) {}

  /**
   * Real implementation: render `params.templateKey` + `params.data`
   * through this build's own (non-generative, spec §1 rule 9) static SMS
   * template layer to get final message text, capped to a single-segment
   * length where the template allows it, since every extra 160-char
   * segment is its own billed message, then:
   *
   * ```
   * const message = await twilioClient.messages.create({
   *   to: params.toE164,
   *   from: config.fromNumber,
   *   body: renderedText,
   * });
   * ```
   *
   * There is no "data-only, client-rendered" option for SMS the way there
   * is for push (`FcmPushSender`'s doc), the carrier delivers exactly the
   * text sent, so the rendering step above (never raw payload prose, see
   * `outbox.ts`'s `assertPrivacySafePayload` and `templateKey`/`data`
   * discipline) is this adapter's own responsibility, not deferred to a
   * client app.
   *
   * Map a caught error's Twilio error code: `21211`/`21214`/`21610`
   * (invalid/unreachable/blocked number) -> `{ status: 'invalid_number' }`;
   * anything else (`21611` queue overflow, 5xx, network) ->
   * `{ status: 'failed', failureReason: String(error.code ?? error.message) }`.
   * Success -> `{ status: 'sent', providerMessageId: message.sid }`.
   */
  async send(_params: SmsSendParams): Promise<SmsSendResult> {
    throw new NotImplementedError('TwilioSmsSender.send');
  }
}
