import type { Ctx } from '../../lib/ctx.js';
import { withTransaction } from '../../db/tx.js';
import { ForbiddenError } from '../../lib/errors.js';
import { NOTIFICATION_CONFIG, backoffSeconds } from './config.js';
import { pruneInvalidToken, listActiveDeviceTokensForUser } from './devices.js';
import { getCategoryPreferenceForUser, getContentPreviewForUser } from './preferences.js';
import { isWithinQuietHours, nextQuietHoursEnd, getQuietHoursForUser } from './quietHours.js';
import { pickMessageTemplate } from './templates.js';
import type { PushSender } from './ports/push.port.js';
import type { EmailSender } from './ports/email.port.js';
import type { ExtendedNotificationEventType, NotificationBucket, NotificationOutboxChannel, OutboxStatus } from './types.js';

/**
 * The delivery worker (build brief: "a delivery worker function taking
 * Ctx"). This is what the jobs agent should schedule on a short interval
 * (e.g. every 15-30s — frequent enough that the message coalescing
 * debounce, default 90s, is the actual bottleneck on latency, not the
 * poll interval).
 *
 * Reads due `notification_outbox` rows (status queued/held_quiet_hours/
 * failed_retryable with `next_attempt_at <= now`), and for each one:
 *
 *  1. Category gate — `safety` bypasses this entirely (never
 *     user-configurable); everything else is dropped (terminal, no
 *     retry) if the recipient has that category+channel turned off. THIS
 *     is where preferences are enforced — never at the call site (build
 *     brief).
 *  2. Quiet-hours gate — `safety_notice` (config.ts
 *     `quietHoursBypassEvents`) bypasses; everything else still inside
 *     the recipient's local quiet window is HELD (`held_quiet_hours`,
 *     rescheduled to the window's end) rather than dropped (config.ts
 *     policy + justification).
 *  3. Transport — resolves the final template+data (message events pick
 *     their template here, not at enqueue, because the coalesced count
 *     and preview preference can both still change up to the last
 *     moment) and calls the injected `PushSender`/`EmailSender`.
 *  4. Result handling — `sent` marks the row done; `invalid_token` prunes
 *     the device and (if it was the only device) drops with no retry;
 *     `invalid_recipient` (email) is terminal (dead) with no retry;
 *     `failed` retries with exponential backoff up to
 *     `NOTIFICATION_CONFIG.retry.maxAttempts`, then goes `dead`.
 *
 * A push/email outage therefore only ever produces `failed_retryable`/
 * `dead` OUTBOX rows — it can never throw back into, or roll back, the
 * domain transaction that called `enqueueNotification`, because that
 * transaction has already committed by the time this worker ever runs
 * (build brief: "a push failure never rolls back or blocks the domain
 * transaction that raised it").
 */

export interface NotificationSenders {
  push: PushSender;
  email: EmailSender;
}

export interface DeliveryWorkerResult {
  processed: number;
  sent: number;
  held: number;
  retried: number;
  dead: number;
  droppedPreference: number;
  droppedNoTarget: number;
  prunedTokens: number;
}

interface OutboxRowRaw {
  id: string;
  user_id: string;
  event_type: string;
  category: NotificationBucket;
  channel: NotificationOutboxChannel;
  template_key: string;
  payload: Record<string, unknown>;
  coalesced_count: number;
  attempt_count: number;
  created_at: Date;
}

function emptyResult(): DeliveryWorkerResult {
  return { processed: 0, sent: 0, held: 0, retried: 0, dead: 0, droppedPreference: 0, droppedNoTarget: 0, prunedTokens: 0 };
}

export async function runNotificationDeliveryWorker(
  ctx: Ctx,
  senders: NotificationSenders,
  opts: { limit?: number } = {},
): Promise<DeliveryWorkerResult> {
  if (ctx.actor.type !== 'system' && ctx.actor.type !== 'admin') {
    throw new ForbiddenError('Only a system job or an admin may run notification delivery.');
  }

  const now = ctx.clock.now();
  const limit = opts.limit ?? NOTIFICATION_CONFIG.delivery.batchSize;

  // Claim the batch inside its own short transaction: SELECT ... FOR
  // UPDATE SKIP LOCKED both locks the candidate rows against a
  // concurrently-running worker (a second worker's own FOR UPDATE simply
  // skips whatever this one is holding) and, by immediately pushing
  // `next_attempt_at` out to a short lease window before committing,
  // prevents a row that's mid-delivery (a real network call, which must
  // happen OUTSIDE any open transaction) from being picked up a second
  // time. `processOne` below overwrites the lease with the real outcome
  // once delivery actually finishes.
  const CLAIM_LEASE_MS = 60_000;
  const rows = await withTransaction(async (db) => {
    const { rows: claimed } = await db.query<OutboxRowRaw>(
      `SELECT id, user_id, event_type, category, channel, template_key, payload, coalesced_count, attempt_count, created_at
       FROM notification_outbox
       WHERE status IN ('queued', 'held_quiet_hours', 'failed_retryable') AND next_attempt_at <= $1
       ORDER BY next_attempt_at ASC
       LIMIT $2
       FOR UPDATE SKIP LOCKED`,
      [now, limit],
    );
    if (claimed.length > 0) {
      const ids = claimed.map((r) => r.id);
      const leaseUntil = new Date(now.getTime() + CLAIM_LEASE_MS);
      await db.query(`UPDATE notification_outbox SET next_attempt_at = $2, updated_at = $3 WHERE id = ANY($1::uuid[])`, [
        ids,
        leaseUntil,
        now,
      ]);
    }
    return claimed;
  });

  const result = emptyResult();

  for (const row of rows) {
    result.processed += 1;
    await processOne(ctx, row, senders, now, result);
  }

  return result;
}

async function setStatus(
  ctx: Ctx,
  id: string,
  status: OutboxStatus,
  patch: { nextAttemptAt?: Date; attemptCount?: number; lastError?: string | null; deliveredAt?: Date | null },
  now: Date,
): Promise<void> {
  await ctx.db.query(
    `UPDATE notification_outbox
     SET status = $2, next_attempt_at = COALESCE($3, next_attempt_at), attempt_count = COALESCE($4, attempt_count),
         last_error = $5, delivered_at = COALESCE($6, delivered_at), updated_at = $7
     WHERE id = $1`,
    [id, status, patch.nextAttemptAt ?? null, patch.attemptCount ?? null, patch.lastError ?? null, patch.deliveredAt ?? null, now],
  );
}

async function processOne(
  ctx: Ctx,
  row: OutboxRowRaw,
  senders: NotificationSenders,
  now: Date,
  result: DeliveryWorkerResult,
): Promise<void> {
  const bypassesQuietHours = (NOTIFICATION_CONFIG.quietHoursBypassEvents as readonly string[]).includes(row.event_type);
  const isSafety = row.category === 'safety';

  // ---- 1. Preference gate (never bypassable — safety excepted by design, see file doc) ----
  if (!isSafety) {
    const pref = await getCategoryPreferenceForUser(ctx, row.user_id, row.category as Exclude<NotificationBucket, 'safety'>);
    const channelAllowed = row.channel === 'push' ? pref.push : pref.email;
    if (!channelAllowed) {
      await setStatus(ctx, row.id, 'dropped_preference', {}, now);
      result.droppedPreference += 1;
      return;
    }
  }

  // ---- 2. Quiet hours gate ----
  if (!isSafety && !bypassesQuietHours) {
    const qh = await getQuietHoursForUser(ctx, row.user_id);
    if (isWithinQuietHours(qh, now)) {
      await setStatus(ctx, row.id, 'held_quiet_hours', { nextAttemptAt: nextQuietHoursEnd(qh, now) }, now);
      result.held += 1;
      return;
    }
  }

  // ---- 3. Resolve template + data, then send ----
  const { templateKey, data } = await resolveTemplateAndData(ctx, row);

  if (row.channel === 'push') {
    await deliverPush(ctx, row, templateKey, data, senders.push, now, result);
  } else {
    await deliverEmail(ctx, row, templateKey, data, senders.email, now, result);
  }
}

function truncate(text: string, max: number): string {
  return text.length > max ? `${text.slice(0, max - 1)}…` : text;
}

async function resolveTemplateAndData(
  ctx: Ctx,
  row: OutboxRowRaw,
): Promise<{ templateKey: string; data: Record<string, string> }> {
  if (row.event_type === 'message_received') {
    const previewAllowed = row.coalesced_count <= 1 && (await getContentPreviewForUser(ctx, row.user_id));
    const templateKey = pickMessageTemplate(row.coalesced_count, previewAllowed);
    const data: Record<string, string> = {
      senderFirstName: String(row.payload.senderFirstName ?? ''),
      count: String(row.coalesced_count),
    };
    if (previewAllowed && typeof row.payload.messagePreviewText === 'string') {
      data.previewText = truncate(row.payload.messagePreviewText, NOTIFICATION_CONFIG.contentPreview.previewMaxChars);
    }
    return { templateKey, data };
  }

  const data: Record<string, string> = {};
  for (const [key, value] of Object.entries(row.payload)) {
    if (value === undefined || value === null) continue;
    data[key] = typeof value === 'string' ? value : JSON.stringify(value);
  }
  return { templateKey: row.template_key, data };
}

async function deliverPush(
  ctx: Ctx,
  row: OutboxRowRaw,
  templateKey: string,
  data: Record<string, string>,
  push: PushSender,
  now: Date,
  result: DeliveryWorkerResult,
): Promise<void> {
  const tokens = await listActiveDeviceTokensForUser(ctx, row.user_id);
  if (tokens.length === 0) {
    await setStatus(ctx, row.id, 'dropped_no_target', {}, now);
    result.droppedNoTarget += 1;
    return;
  }

  let sentOk = false;
  let anyTransientFailure = false;
  for (const token of tokens) {
    const sendResult = await push.send({
      token: token.pushToken,
      platform: token.platform,
      templateKey,
      data,
      collapseKey: row.id,
    });
    if (sendResult.status === 'sent') {
      sentOk = true;
    } else if (sendResult.status === 'invalid_token') {
      await pruneInvalidToken(ctx, token.platform, token.pushToken);
      result.prunedTokens += 1;
    } else {
      anyTransientFailure = true;
    }
  }

  if (sentOk) {
    await setStatus(ctx, row.id, 'sent', { deliveredAt: now }, now);
    result.sent += 1;
    return;
  }

  if (!anyTransientFailure) {
    // Every token was invalid and has now been pruned — nothing left to retry against.
    await setStatus(ctx, row.id, 'dropped_no_target', {}, now);
    result.droppedNoTarget += 1;
    return;
  }

  await retryOrDie(ctx, row, 'push transport failure', now, result);
}

async function deliverEmail(
  ctx: Ctx,
  row: OutboxRowRaw,
  templateKey: string,
  data: Record<string, string>,
  email: EmailSender,
  now: Date,
  result: DeliveryWorkerResult,
): Promise<void> {
  const { rows } = await ctx.db.query<{ email: string }>('SELECT email FROM users WHERE id = $1', [row.user_id]);
  const toEmail = rows[0]?.email;
  if (!toEmail) {
    await setStatus(ctx, row.id, 'dropped_no_target', {}, now);
    result.droppedNoTarget += 1;
    return;
  }

  const sendResult = await email.send({ toEmail, templateKey, data });
  if (sendResult.status === 'sent') {
    await setStatus(ctx, row.id, 'sent', { deliveredAt: now }, now);
    result.sent += 1;
    return;
  }
  if (sendResult.status === 'invalid_recipient') {
    await setStatus(ctx, row.id, 'dead', { lastError: sendResult.failureReason }, now);
    result.dead += 1;
    return;
  }
  await retryOrDie(ctx, row, sendResult.failureReason ?? 'email transport failure', now, result);
}

async function retryOrDie(
  ctx: Ctx,
  row: OutboxRowRaw,
  reason: string,
  now: Date,
  result: DeliveryWorkerResult,
): Promise<void> {
  const attemptCount = row.attempt_count + 1;
  if (attemptCount >= NOTIFICATION_CONFIG.retry.maxAttempts) {
    await setStatus(ctx, row.id, 'dead', { attemptCount, lastError: reason }, now);
    result.dead += 1;
    return;
  }
  const nextAttemptAt = new Date(now.getTime() + backoffSeconds(attemptCount) * 1000);
  await setStatus(ctx, row.id, 'failed_retryable', { attemptCount, lastError: reason, nextAttemptAt }, now);
  result.retried += 1;
}

export type { ExtendedNotificationEventType };
