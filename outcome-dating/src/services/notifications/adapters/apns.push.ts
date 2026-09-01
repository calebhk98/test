import { NotImplementedError } from '../../../lib/errors.js';
import type { PushSendParams, PushSendResult, PushSender } from '../ports/push.port.js';

/**
 * Apple Push Notification service adapter for `PushSender` (spec §20.2
 * push channel — required for iOS).
 *
 * Documented STUB, same pattern as `fcm.push.ts` and
 * `src/services/payments/stripe.processor.ts`: no APNs SDK/HTTP2 client is
 * a dependency of this foundation layer; every method throws
 * `NotImplementedError`. The JSDoc is the exact contract a real
 * implementation must satisfy.
 *
 * Construction takes the provider-token auth material so the real
 * implementation's constructor signature doesn't need to change later:
 * `new ApnsPushSender({ keyId: getEnv().APNS_KEY_ID, teamId: getEnv().APNS_TEAM_ID,
 * signingKey: getEnv().APNS_SIGNING_KEY, bundleId: getEnv().APNS_BUNDLE_ID })`.
 */
export class ApnsPushSender implements PushSender {
  readonly name = 'apns';

  constructor(
    private readonly credentials:
      | { keyId: string; teamId: string; signingKey: string; bundleId: string }
      | undefined,
  ) {}

  /**
   * Real implementation: POST to
   * `https://api.push.apple.com/3/device/{params.token}` over HTTP/2,
   * with:
   *
   * ```
   * headers: {
   *   'apns-topic': credentials.bundleId,
   *   'apns-push-type': 'alert',
   *   'apns-collapse-id': params.collapseKey,          // <= 64 bytes, truncate if needed
   *   authorization: `bearer ${signedProviderJwt}`,     // ES256 JWT, keyId/teamId/signingKey, cached ~55min
   * },
   * body: {
   *   aps: { 'content-available': 1 },   // silent/background — no `alert` field, same
   *                                       // data-only reasoning as fcm.push.ts: the CLIENT
   *                                       // renders templateKey+data locally, never Apple.
   *   templateKey: params.templateKey,
   *   ...params.data,
   * },
   * ```
   *
   * Map the HTTP response: `200` -> `{ status: 'sent', providerMessageId:
   * response.headers['apns-id'] }`. `400` with reason `'BadDeviceToken'`,
   * or `410` (`'Unregistered'`) -> `{ status: 'invalid_token' }`. Anything
   * else (`429`, `5xx`, network error) -> `{ status: 'failed',
   * failureReason: reason }`.
   */
  async send(_params: PushSendParams): Promise<PushSendResult> {
    throw new NotImplementedError('ApnsPushSender.send');
  }
}
