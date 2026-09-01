/**
 * Public surface of the notification DELIVERY layer. Raising services
 * (interest/conversation/dateProposal/message/trust/moderation) should
 * only ever need `enqueueNotification` from here — everything else is for
 * the jobs worker, the HTTP layer's device/preference/quiet-hours
 * endpoints (owned elsewhere — not wired by this build, see the report),
 * and tests.
 */

export { enqueueNotification } from './outbox.js';
export type { EnqueueNotificationInput, EnqueueNotificationResult } from './outbox.js';

export { runNotificationDeliveryWorker } from './delivery.js';
export type { NotificationSenders, DeliveryWorkerResult } from './delivery.js';

export { registerDeviceToken, unregisterDeviceToken, listMyDeviceTokens, listActiveDeviceTokensForUser, pruneInvalidToken } from './devices.js';
export type { RegisterDeviceInput } from './devices.js';

export {
  getMyNotificationPreferences,
  getPreferencesForUser,
  getCategoryPreferenceForUser,
  updateMyNotificationPreference,
  getMyContentPreviewSetting,
  getContentPreviewForUser,
  updateMyContentPreviewSetting,
  DEFAULT_PREFERENCES,
} from './preferences.js';

export { getMyQuietHours, getQuietHoursForUser, updateMyQuietHours, isWithinQuietHours, nextQuietHoursEnd } from './quietHours.js';

export { NOTIFICATION_CONFIG, backoffSeconds } from './config.js';
export { EVENT_BUCKET, MESSAGE_TEMPLATES, pickMessageTemplate } from './templates.js';
export type { DevicePlatform, ExtendedNotificationEventType, NotificationCategory, NotificationOutboxChannel, CategoryPrefs, QuietHours } from './types.js';

export type { PushSender, PushSendParams, PushSendResult } from './ports/push.port.js';
export type { EmailSender, EmailSendParams, EmailSendResult } from './ports/email.port.js';
export type { SmsSender, SmsSendParams, SmsSendResult } from './ports/sms.port.js';
export { FakePushSender } from './adapters/fake.push.js';
export { FakeEmailSender } from './adapters/fake.email.js';
export { FakeSmsSender } from './adapters/fake.sms.js';
export { FcmPushSender } from './adapters/fcm.push.js';
export { ApnsPushSender } from './adapters/apns.push.js';
export { SesEmailSender } from './adapters/ses.email.js';
export { TwilioSmsSender } from './adapters/twilio.sms.js';

import { FakePushSender } from './adapters/fake.push.js';
import { FakeEmailSender } from './adapters/fake.email.js';
import { FakeSmsSender } from './adapters/fake.sms.js';
import type { NotificationSenders } from './delivery.js';

/** Convenience dev/test senders — deterministic in-memory fakes, no credentials required. Production wiring (choosing FCM/APNs/SES/Twilio vs these fakes) is the jobs/index.ts owner's call; see this build's report for the exact env-driven switch to add there. */
export function defaultDevSenders(): NotificationSenders {
  return { push: new FakePushSender(), email: new FakeEmailSender(), sms: new FakeSmsSender() };
}
