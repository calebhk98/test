/**
 * EmailSender, the port every email adapter implements. Same
 * port/adapter shape as `PushSender` (push.port.ts) and
 * `src/services/payments/processor.port.ts`.
 */

export interface EmailSendParams {
  toEmail: string;
  /** Static template key the email renderer resolves to a subject+body layout (never free text, spec §1 rule 9, §20). */
  templateKey: string;
  /** Named substitution slots, all pre-stringified. Same no-raw-prose-field discipline as `PushSendParams.data`. */
  data: Record<string, string>;
}

export interface EmailSendResult {
  status: 'sent' | 'invalid_recipient' | 'failed';
  /** Provider-side message id, when available. */
  providerMessageId: string | null;
  /** Present when status !== 'sent'. */
  failureReason: string | null;
}

export interface EmailSender {
  /** Adapter name (e.g. "fake", "ses"). */
  readonly name: string;

  /**
   * `invalid_recipient` (hard bounce / malformed address) is terminal,
   * `delivery.ts` marks the outbox row `dead` immediately rather than
   * retrying, since retrying a bad address can never succeed. `failed`
   * (transport/provider outage) is retried with backoff like a push
   * `failed` result.
   */
  send(params: EmailSendParams): Promise<EmailSendResult>;
}
