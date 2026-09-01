/**
 * SmsSender, the port every SMS adapter implements. Same port/adapter
 * shape as `PushSender` (push.port.ts) / `EmailSender` (email.port.ts) /
 * `src/services/payments/processor.port.ts`.
 *
 * SMS is the one transport channel where every send has a real,
 * per-message dollar cost (push/email are effectively free at this
 * product's scale), see `delivery.ts`'s per-user daily cap and this
 * channel's more aggressive coalescing (`config.ts` `NOTIFICATION_CONFIG.sms`)
 * for the two levers that exist specifically because of that. Nothing in
 * this port itself changes for cost reasons; the cost controls live entirely
 * on the calling side (`outbox.ts`'s eligibility gate, `delivery.ts`'s cap),
 * which is deliberate, an adapter should never have to know why a message
 * did or didn't reach it.
 */

export interface SmsSendParams {
  /** Normalized E.164 destination number (`user_phones.phone_e164`), only ever resolved for a recipient with a currently-VERIFIED number (see `delivery.ts`). */
  toE164: string;
  /** Static template key the SMS renderer resolves to final message text (never free text, spec §1 rule 9, §20, same discipline as `PushSendParams.templateKey`). */
  templateKey: string;
  /**
   * Named substitution slots, all pre-stringified. Same no-raw-prose-field
   * discipline as `PushSendParams.data`/`EmailSendParams.data`, the one
   * exception is `previewText`, populated only when the recipient opted
   * into content previews (default OFF), exactly as for push.
   */
  data: Record<string, string>;
}

export interface SmsSendResult {
  status: 'sent' | 'invalid_number' | 'failed';
  /** Provider-side message SID/id, when available. */
  providerMessageId: string | null;
  /** Present when status !== 'sent'. */
  failureReason: string | null;
}

export interface SmsSender {
  /** Adapter name (e.g. "fake", "twilio"). */
  readonly name: string;

  /**
   * `invalid_number` (the provider rejects the destination as unreachable/
   * malformed/landline-only) is terminal, `delivery.ts` marks the outbox
   * row `dead` immediately, same as `EmailSender`'s `invalid_recipient`.
   * `failed` (transport/provider outage, insufficient account balance,
   * etc.) is retried with backoff like a push/email `failed` result, up to
   * the shared `NOTIFICATION_CONFIG.retry.maxAttempts` cap.
   */
  send(params: SmsSendParams): Promise<SmsSendResult>;
}
