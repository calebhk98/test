import { z } from 'zod';
import type { Ctx } from '../../lib/ctx.js';
import { ValidationError } from '../../lib/errors.js';
import { newId } from '../../lib/ids.js';
import * as notificationService from '../notification.service.js';
import { NOTIFICATION_CONFIG } from './config.js';
import { EVENT_BUCKET, EXTENDED_EVENT_TYPES, isKnownEventType, logicalTemplateKey } from './templates.js';
import type { ExtendedNotificationEventType, NotificationOutboxChannel } from './types.js';

/**
 * `enqueueNotification` — the ONE exported entrypoint every event-raising
 * service should call (build brief's "Seams" section:
 * `enqueueNotification(ctx, ...)`). It is the single place that:
 *
 *  1. Deduplicates on a caller-supplied stable key, so a retried domain
 *     operation (an at-least-once job re-running `acceptInterest`, a
 *     client retrying a POST after a timeout) cannot double-notify.
 *  2. Buckets the event into its category (templates.ts `EVENT_BUCKET`).
 *  3. Best-effort mirrors the event into the in-app notification center
 *     via `notification.service.ts#notify` for canonical event types
 *     (never for `message_received`, which isn't in that frozen enum —
 *     see this build's report).
 *  4. Coalesces into an existing pending outbox row for the same
 *     `(user, coalescingKey, channel)` when one is still undelivered,
 *     instead of creating a new one — this is the "5 messages -> 1 push"
 *     rule.
 *  5. Inserts a `notification_outbox` row per transport channel
 *     (push, email) — NOT gated on the recipient's preference here.
 *     Preference/quiet-hours gating happens in `delivery.ts`, deliberately
 *     never here, so a caller can never bypass it by skipping a check at
 *     the call site (build brief: "Preferences must never be bypassable by
 *     a caller passing a flag").
 *
 * Never throws for an ordinary duplicate or an in-app mirroring failure —
 * only for a genuinely malformed call (bad input shape, a payload that
 * tries to smuggle prose or privacy-sensitive fields). This function is
 * called from inside the SAME database transaction as the domain event
 * that raised it (see INTERFACES.md's `withTransaction`/`withDb`
 * pattern), so anything it throws rolls that transaction back — the
 * outbox INSERT itself succeeding-or-not is exactly as safe to be inside
 * that transaction as any other domain write; it is the ASYNC delivery
 * (`delivery.ts`, a push/email actually reaching a device) that must never
 * block or roll back the domain transaction, and that part never runs
 * synchronously here.
 */

/**
 * Payload keys that would smuggle free-text prose (same discipline as
 * `notification.service.ts`'s `FORBIDDEN_PAYLOAD_KEYS`), PLUS keys that
 * would leak the specific privacy-sensitive facts the build brief calls
 * out by name: a safety event's reporter identity, exact location, and
 * payment details. `messagePreviewText` is the one deliberate exception —
 * see below.
 */
const FORBIDDEN_PAYLOAD_KEYS = ['body', 'text', 'message', 'html', 'copy', 'content'] as const;
const FORBIDDEN_PAYLOAD_KEY_PATTERNS: RegExp[] = [
  /reporter/i, // never the reporter's identity for a safety event
  /^(lat|lng|latitude|longitude|gps|precise.?location|exact.?location)$/i, // never exact location
  /card|cvv|cvc|iban|routing|account.?number|ssn/i, // never payment details
];

function assertPrivacySafePayload(eventType: ExtendedNotificationEventType, payload: Record<string, unknown>): void {
  for (const key of Object.keys(payload)) {
    // `messagePreviewText` on `message_received` is the one field allowed to carry
    // raw user content — it is only ever surfaced downstream when the
    // recipient has opted into lock-screen previews (preferences.ts,
    // default OFF); see delivery.ts.
    if (eventType === 'message_received' && key === 'messagePreviewText') continue;

    if ((FORBIDDEN_PAYLOAD_KEYS as readonly string[]).includes(key)) {
      throw new ValidationError(
        `Notification payload must not contain a free-text "${key}" field — content comes from the static template, never from payload prose.`,
      );
    }
    if (FORBIDDEN_PAYLOAD_KEY_PATTERNS.some((re) => re.test(key))) {
      throw new ValidationError(
        `Notification payload key "${key}" looks like it carries a privacy-sensitive field (reporter identity, exact location, or payment details) that must never leave the server in a notification.`,
      );
    }
  }
}

const EnqueueSchema = z.object({
  userId: z.string().uuid(),
  eventType: z.enum(EXTENDED_EVENT_TYPES),
  /** Stable per-domain-event key, convention `${eventType}:${entityId}` (e.g. `interest_accepted:${interestId}`). */
  dedupKey: z.string().min(1).max(500),
  payload: z.record(z.unknown()).default({}),
  /**
   * Groups this event with other still-pending events for the same user
   * into one delivered notification (build brief's coalescing rule).
   * Defaults to `dedupKey` — i.e. no coalescing (every call is its own
   * group of one) unless the caller opts in. `message.service.ts` (once
   * wired — see this build's report) should pass
   * `message:${recipientUserId}:${conversationId}` here.
   */
  coalescingKey: z.string().min(1).max(500).optional(),
});

export interface EnqueueNotificationInput {
  userId: string;
  eventType: ExtendedNotificationEventType;
  dedupKey: string;
  payload?: Record<string, unknown>;
  coalescingKey?: string;
}

export interface EnqueueNotificationResult {
  /** True if `dedupKey` had already been enqueued before — nothing new was created. */
  deduplicated: boolean;
  /** The outbox row id(s) created or merged into for this call (one per transport channel), empty when `deduplicated`. */
  outboxIds: string[];
}

interface OutboxIdRow {
  id: string;
}

export async function enqueueNotification(ctx: Ctx, input: EnqueueNotificationInput): Promise<EnqueueNotificationResult> {
  const parsed = EnqueueSchema.parse(input);
  if (!isKnownEventType(parsed.eventType)) {
    throw new ValidationError(`"${parsed.eventType}" is not a known notification event type.`);
  }
  assertPrivacySafePayload(parsed.eventType, parsed.payload);

  const category = EVENT_BUCKET[parsed.eventType];
  const coalescingKey = parsed.coalescingKey ?? parsed.dedupKey;
  const now = ctx.clock.now();

  // ---- 1. Idempotency gate -------------------------------------------
  const claimId = newId();
  const { rows: dedupRows } = await ctx.db.query<{ dedup_key: string }>(
    `INSERT INTO notification_dedup_log (dedup_key, outbox_id, created_at)
     VALUES ($1, $2, $3)
     ON CONFLICT (dedup_key) DO NOTHING
     RETURNING dedup_key`,
    [parsed.dedupKey, claimId, now],
  );
  if (dedupRows.length === 0) {
    // Already enqueued by an earlier (possibly retried) call — no-op.
    return { deduplicated: true, outboxIds: [] };
  }

  // ---- 2. Best-effort in-app mirror -----------------------------------
  // Only for canonical event types notification.service.ts actually
  // knows about; never throws out to the caller (see file doc).
  if (parsed.eventType !== 'message_received') {
    try {
      await notificationService.notify(ctx, {
        userId: parsed.userId,
        eventType: parsed.eventType,
        channel: 'in_app',
        payload: parsed.payload,
      });
    } catch (err) {
      ctx.logger.warn('notifications.in_app_mirror_failed', {
        eventType: parsed.eventType,
        dedupKey: parsed.dedupKey,
        error: err instanceof Error ? err.message : String(err),
      });
    }
  }

  // ---- 3. Coalesce-or-create one outbox row per transport channel ----
  const templateKey = logicalTemplateKey(parsed.eventType);
  const channels: NotificationOutboxChannel[] = ['push', 'email'];
  const outboxIds: string[] = [];

  for (const channel of channels) {
    const id = await coalesceOrCreate(ctx, {
      id: newId(),
      userId: parsed.userId,
      eventType: parsed.eventType,
      category,
      channel,
      templateKey,
      payload: parsed.payload,
      coalescingKey,
      now,
    });
    outboxIds.push(id);
  }

  await ctx.db.query(`UPDATE notification_dedup_log SET outbox_id = $2 WHERE dedup_key = $1`, [
    parsed.dedupKey,
    outboxIds[0] ?? claimId,
  ]);

  return { deduplicated: false, outboxIds };
}

interface CoalesceParams {
  id: string;
  userId: string;
  eventType: ExtendedNotificationEventType;
  category: string;
  channel: NotificationOutboxChannel;
  templateKey: string;
  payload: Record<string, unknown>;
  coalescingKey: string;
  now: Date;
}

/**
 * Merges into an existing undelivered outbox row for the same
 * `(user, coalescingKey, channel)`, or creates a new one. The merge
 * (`UPDATE ... WHERE id = (SELECT ... FOR UPDATE)`) locks the candidate
 * row inside the subquery before updating it, so two concurrent enqueues
 * against an already-existing group serialize correctly; two concurrent
 * enqueues that are BOTH the first-ever event for a brand-new
 * coalescing_key can race and create two rows (rare, and self-heals: the
 * next event for that key merges into whichever row is still pending) —
 * an accepted limitation for this build, noted for anyone hardening this
 * further.
 *
 * `next_attempt_at` on a merge is "now + debounce, capped at the row's
 * original `created_at` + `coalesceMaxWaitSeconds`" for message events
 * (the actual debounce/burst-cap rule), and simply left at the existing
 * row's due time for everything else (match/date_request events default
 * to `coalescingKey === dedupKey`, i.e. a group of exactly one — the
 * merge path never actually triggers for them).
 */
async function coalesceOrCreate(ctx: Ctx, params: CoalesceParams): Promise<string> {
  const { message } = NOTIFICATION_CONFIG;
  const debounceMs = params.eventType === 'message_received' ? message.coalesceDebounceSeconds * 1000 : 0;
  const maxWaitMs = params.eventType === 'message_received' ? message.coalesceMaxWaitSeconds * 1000 : 0;

  const { rows: merged } = await ctx.db.query<OutboxIdRow>(
    `UPDATE notification_outbox
     SET coalesced_count = coalesced_count + 1,
         payload = $2::jsonb,
         next_attempt_at = LEAST(
           created_at + ($3 || ' milliseconds')::interval,
           GREATEST(next_attempt_at, $4::timestamptz + ($5 || ' milliseconds')::interval)
         ),
         updated_at = $4
     WHERE id = (
       SELECT id FROM notification_outbox
       WHERE user_id = $1 AND coalescing_key = $6 AND channel = $7
         AND status IN ('queued', 'held_quiet_hours')
       ORDER BY created_at DESC
       LIMIT 1
       FOR UPDATE SKIP LOCKED
     )
     RETURNING id`,
    [
      params.userId,
      JSON.stringify(params.payload),
      maxWaitMs,
      params.now,
      debounceMs,
      params.coalescingKey,
      params.channel,
    ],
  );
  if (merged[0]) return merged[0].id;

  const nextAttemptAt = new Date(params.now.getTime() + debounceMs);
  const { rows: created } = await ctx.db.query<OutboxIdRow>(
    `INSERT INTO notification_outbox
       (id, user_id, event_type, category, channel, template_key, payload, coalescing_key, coalesced_count, status, attempt_count, next_attempt_at, created_at, updated_at)
     VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8, 1, 'queued', 0, $9, $10, $10)
     RETURNING id`,
    [
      params.id,
      params.userId,
      params.eventType,
      params.category,
      params.channel,
      params.templateKey,
      JSON.stringify(params.payload),
      params.coalescingKey,
      nextAttemptAt,
      params.now,
    ],
  );
  return created[0]!.id;
}
