/**
 * §20 Notification Delivery job. Thin wrapper around
 * `notifications/delivery.ts#runNotificationDeliveryWorker`, the one
 * piece of the notification pipeline nothing was scheduling (see the
 * wiring build's report: `runNotificationDeliveryWorker` was fully built
 * and tested but registered in no job, so a queued push/email/SMS
 * notification was never actually sent). No domain logic lives here: the
 * worker itself owns every gating decision (preferences, quiet hours,
 * retry/backoff), this file only resolves which `PushSender`/
 * `EmailSender`/`SmsSender` to hand it, using the exact same
 * environment-driven selection `src/http/deps.ts` uses for every other
 * external-integration port (`src/config/adapters.ts`, fakes outside
 * production, a hard failure on a misconfigured production deployment,
 * never a silent fake-in-production fallback).
 *
 * Short interval on purpose: the delivery worker's own doc notes the
 * message-coalescing debounce (default 90s) is meant to be the actual
 * latency bottleneck, not this job's poll interval.
 */
import type { Ctx } from '../lib/ctx.js';
import { getEnv } from '../config/env.js';
import { selectPushSender, selectEmailSender, selectSmsSender } from '../config/adapters.js';
import { runNotificationDeliveryWorker } from '../services/notifications/delivery.js';
import type { DeliveryWorkerResult, NotificationSenders } from '../services/notifications/delivery.js';
import type { JobDefinition } from './types.js';

export async function runNotificationDeliveryJob(ctx: Ctx): Promise<DeliveryWorkerResult> {
  const env = getEnv();
  const senders: NotificationSenders = {
    push: selectPushSender(env),
    email: selectEmailSender(env),
    sms: selectSmsSender(env),
  };
  return runNotificationDeliveryWorker(ctx, senders);
}

export const notificationDeliveryJob: JobDefinition = {
  name: 'notification_delivery',
  description: 'Deliver queued push/email/SMS notifications from notification_outbox, respecting preferences, quiet hours, and retry/backoff (§20).',
  intervalMs: 30 * 1000,
  run: runNotificationDeliveryJob,
};
