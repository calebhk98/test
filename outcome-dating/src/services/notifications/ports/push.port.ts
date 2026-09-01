import type { DevicePlatform } from '../types.js';

/**
 * PushSender — the port every push adapter implements. Mirrors
 * `src/services/payments/processor.port.ts`'s port/adapter shape exactly:
 * a small interface here, a deterministic in-memory fake for dev/tests,
 * and one documented-but-throwing adapter per real provider so the real
 * SDKs are never a runtime dependency of this foundation layer.
 *
 * `delivery.ts` is the only caller — it resolves a recipient's enabled
 * device tokens (devices.ts) and preference/quiet-hours gating
 * (preferences.ts, quietHours.ts) BEFORE ever calling `send`, so by the
 * time this port is invoked the decision to deliver has already been
 * made; `send` only needs to worry about transport.
 *
 * Implementations MUST NOT throw for an expected per-token failure
 * (unregistered/expired token, provider-side rejection) — those are a
 * normal `status: 'invalid_token' | 'failed'` result, exactly like
 * `PaymentProcessor`'s "declines are a normal result, not an exception"
 * rule. Reserve thrown errors for transport/infrastructure failures.
 */

export interface PushSendParams {
  /** The device's push token (device_tokens.push_token). */
  token: string;
  platform: DevicePlatform;
  /** Static template key the client renders (spec §1 rule 9, §20 — never free text). */
  templateKey: string;
  /**
   * Named substitution slots for the template, all pre-stringified.
   * NEVER a raw prose field (`body`/`text`/`message`) — the shape mirrors
   * notification.service.ts's `NotifyInput.payload` discipline exactly.
   * The one deliberate exception is `previewText`, which is only ever
   * populated by delivery.ts when the recipient has opted into lock-screen
   * content previews (default OFF) — see outbox.ts's privacy-safe payload
   * guard.
   */
  data: Record<string, string>;
  /**
   * Provider-level collapse/coalescing key: a second push with the same
   * `collapseKey` should replace, not stack on top of, an
   * already-delivered-but-unseen push for the same token (FCM
   * `collapseKey`/`android.collapseKey`, APNs `apns-collapse-id`). Set to
   * the outbox row's `coalescing_key` so a device that missed the app
   * being backgrounded doesn't show two lock-screen entries for what the
   * server already merged into one notification.
   */
  collapseKey?: string;
}

export interface PushSendResult {
  status: 'sent' | 'invalid_token' | 'failed';
  /** Provider-side message/receipt id, when available. */
  providerMessageId: string | null;
  /** Present when status !== 'sent'. */
  failureReason: string | null;
}

export interface PushSender {
  /** Adapter name, useful for logging/auditability (e.g. "fake", "fcm", "apns"). */
  readonly name: string;

  /**
   * Send one push to one token. `delivery.ts` fans this out per enabled
   * device token for the recipient and treats the whole attempt as
   * successful if AT LEAST ONE token accepts it — an `invalid_token`
   * result for one of several devices must not fail delivery to the
   * user's other devices, and must trigger that token's automatic pruning
   * (devices.ts `pruneInvalidToken`) rather than a retry.
   */
  send(params: PushSendParams): Promise<PushSendResult>;
}
