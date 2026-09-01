import { NotImplementedError } from '../../../lib/errors.js';
import type { PushSendParams, PushSendResult, PushSender } from '../ports/push.port.js';

/**
 * Firebase Cloud Messaging adapter for `PushSender` (spec §20.2 push
 * channel, FCM is the standard choice for Android and covers web push
 * too).
 *
 * This is a documented STUB, exactly like
 * `src/services/payments/stripe.processor.ts`: the `firebase-admin` npm
 * SDK is deliberately NOT a dependency of this foundation layer, so every
 * method throws `NotImplementedError`. The JSDoc on `send` is the exact
 * contract a real implementation must satisfy, installing
 * `firebase-admin` and supplying `FIREBASE_SERVICE_ACCOUNT_JSON` (or
 * equivalent) should be the only change needed.
 *
 * Construction takes the service account credential so the real
 * implementation's constructor signature doesn't need to change later:
 * `new FcmPushSender(getEnv().FIREBASE_SERVICE_ACCOUNT_JSON)`.
 */
export class FcmPushSender implements PushSender {
  readonly name = 'fcm';

  constructor(private readonly serviceAccountJson: string | undefined) {}

  /**
   * Real implementation:
   *
   * ```
   * await admin.messaging().send({
   *   token: params.token,
   *   data: params.data,               // DATA-ONLY message, no `notification` field.
   *   android: { collapseKey: params.collapseKey, priority: 'high' },
   *   webpush: params.collapseKey ? { headers: { Topic: params.collapseKey } } : undefined,
   * });
   * ```
   *
   * Sending a data-only message (never the `notification` field) is
   * deliberate, not an oversight: FCM's `notification` field is rendered
   * directly by the OS from whatever strings you put in it, bypassing the
   * app's own template rendering, that would make it trivial to
   * accidentally leak `previewText`-style content to a recipient who
   * opted OUT of lock-screen previews (build brief's privacy rule). Data-
   * only messages always go through the client app's own notification
   * builder, which renders `templateKey` + `data` the same static-template
   * way notification.service.ts renders in-app copy.
   *
   * Map a caught error's `error.code`: `'messaging/registration-token-not-registered'`
   * or `'messaging/invalid-registration-token'` -> `{ status: 'invalid_token' }`;
   * anything else -> `{ status: 'failed', failureReason: error.code }`.
   * Success -> `{ status: 'sent', providerMessageId: <returned message name> }`.
   */
  async send(_params: PushSendParams): Promise<PushSendResult> {
    throw new NotImplementedError('FcmPushSender.send');
  }
}
