/**
 * src/services/retention.service.ts, the data-retention policy registry
 * and its batched enforcement engine.
 *
 * See docs/retention.md for the full table (window, action, reasoning)
 * this file implements, that document and `RETENTION_POLICIES` below
 * MUST stay in sync; `tests/unit/retention.test.ts` asserts the policy
 * COUNT matches so the doc can't silently drift.
 *
 * DESIGN
 *
 *  - Per data class, either DELETE (the class has no legitimate reason to
 *    survive past its window) or ANONYMIZE (the row/aggregate needs to
 *    keep existing, a conversation's timeline, a device's reputation
 *    score, but its personally-identifying content doesn't need to).
 *    Every policy below says explicitly which.
 *
 *  - BOUNDED, BATCHED, IDEMPOTENT (task brief: "cannot lock the database
 *    by deleting millions of rows in one statement"). Each policy deletes
 *    or anonymizes `batchSize` rows at a time (one `DELETE`/`UPDATE ...
 *    WHERE id IN (SELECT ... LIMIT $batchSize)` statement per batch,
 *    short-lived, small lock footprint, never a table-wide sweep in one
 *    transaction), and stops after `maxBatchesPerRun` batches even if
 *    more rows still match, so one scheduled tick can never balloon into
 *    an unbounded scan of a huge backlog. A capped run just means slower
 *    catch-up, never lost work: the NEXT run's query re-selects whatever
 *    still matches the same age cutoff (computed fresh from `ctx.clock`
 *    each run), so nothing needs to remember where a prior run stopped.
 *    Re-running a policy against a database it already fully processed
 *    matches zero rows and is a costless no-op, that's the whole
 *    idempotency story, no separate "already ran" bookkeeping needed.
 *
 *  - `ctx.clock` drives every cutoff, never `Date.now()`/`new Date()`,
 *    so tests move a `ManualClock` to the window boundary instead of
 *    waiting on real time (task brief).
 *
 *  - COORDINATES WITH ACCOUNT DELETION, doesn't duplicate it.
 *    `profile.service.ts#deleteMyAccount` already hard-deletes a user's
 *    sensitive profile content (answers, tags, filters, photos) the
 *    moment they delete their account, and already draws the exact
 *    "financial + safety audit trail survive, everything else doesn't"
 *    boundary this file's RETAINED_FOREVER list below repeats verbatim,
 *    see that function's own extensive doc for the reasoning (ban-evasion
 *    resistance, tax/dispute obligations). This file's job is the
 *    complementary one: the logs/events/impressions that accumulate for
 *    EVERY user (deleted or not) over ordinary use, which no single
 *    "user deleted their account" action ever touches because they're
 *    not gated on account status at all, a still-active user's own
 *    90-day-old login history is exactly as much a liability as a
 *    deleted user's. Same boundary, different trigger (age, not a user
 *    action).
 */
import type { Ctx } from '../lib/ctx.js';
import { addDays } from '../lib/time.js';
import { DELETED_MESSAGE_PLACEHOLDER } from './profile.service.js';

export type RetentionAction = 'delete' | 'anonymize';

export interface RetentionPolicy {
  /** Stable identifier, also the row/log key an operator greps for. */
  name: string;
  /** The data class in plain words, for docs/retention.md's table. */
  dataClass: string;
  action: RetentionAction;
  windowDays: number;
  /** Why this window and not a different one, the "reasoning written down" the task brief asks for. Kept alongside the code, not just in docs/retention.md, so the two can never drift silently out of sync (tests/unit/retention.test.ts asserts every policy has one). */
  reasoning: string;
  batchSize: number;
  maxBatchesPerRun: number;
  /** Runs exactly ONE batch (<= batchSize rows) and returns how many rows it touched. `< batchSize` (including 0) tells the sweep loop this policy is exhausted for this run. */
  runBatch: (ctx: Ctx, cutoff: Date, batchSize: number) => Promise<number>;
}

/** Batch-deletes rows from `table` whose `ageColumn` is older than `cutoff`, keyed by `idColumn` (that table's primary key, `id` for every table below except `notification_dedup_log`, whose primary key is `dedup_key`; there is no bind-parameter syntax for a SQL identifier, so both are always one of the compile-time literals in `PrunableTable`/`PRUNABLE_ID_COLUMNS` below, never anything derived from request input). */
async function batchDeleteByAgeColumn(ctx: Ctx, table: PrunableTable, ageColumn: string, cutoff: Date, batchSize: number): Promise<number> {
  const idColumn = PRUNABLE_ID_COLUMNS[table];
  const { rowCount } = await ctx.db.query(
    `WITH victims AS (
       SELECT ${idColumn} FROM ${table} WHERE ${ageColumn} < $1 ORDER BY ${ageColumn} LIMIT $2
     )
     DELETE FROM ${table} WHERE ${idColumn} IN (SELECT ${idColumn} FROM victims)`,
    [cutoff, batchSize],
  );
  return rowCount ?? 0;
}

/**
 * Closed allowlist of tables this file is allowed to run
 * `batchDeleteByAgeColumn` against, table/column names are interpolated
 * into the SQL text above (Postgres has no bind-parameter syntax for an
 * identifier), so this union is what keeps that safe: every value is a
 * compile-time literal from this file, never anything derived from
 * request input.
 */
type PrunableTable =
  | 'email_verification_tokens'
  | 'password_reset_tokens'
  | 'phone_verification_codes'
  | 'user_auth_events'
  | 'discovery_events'
  | 'message_flags'
  | 'notification_dedup_log';

/** Each `PrunableTable`'s primary-key column, `id` for every table except `notification_dedup_log`, whose PK is `dedup_key` (db/migrations/011_notifications.sql). */
const PRUNABLE_ID_COLUMNS: Record<PrunableTable, string> = {
  email_verification_tokens: 'id',
  password_reset_tokens: 'id',
  phone_verification_codes: 'id',
  user_auth_events: 'id',
  discovery_events: 'id',
  message_flags: 'id',
  notification_dedup_log: 'dedup_key',
};

const DEFAULT_BATCH_SIZE = 500;
const DEFAULT_MAX_BATCHES_PER_RUN = 50; // 25,000 rows/policy/run at the default batch size

// =========================================================================
// Policies whose data has NO legitimate reason to outlive a short window,
// see docs/retention.md for the full narrative version of each.
// =========================================================================

const verificationCodePolicies: RetentionPolicy[] = (
  [
    ['email_verification_tokens', 'Expired email-verification tokens'],
    ['password_reset_tokens', 'Expired password-reset tokens'],
    ['phone_verification_codes', 'Expired phone-verification codes'],
  ] as const
).map(([table, dataClass]) => ({
  name: `expired_${table}`,
  dataClass,
  action: 'delete' as const,
  windowDays: 7,
  reasoning:
    'A one-time code/token is worthless the moment it expires, it cannot be replayed, and the account action it would have authorized already requires a fresh one. The 7-day buffer past expires_at (rather than deleting the instant it expires) exists purely for support debugging ("did this ever get issued/consumed?"), not because the code itself has any value past expiry.',
  batchSize: DEFAULT_BATCH_SIZE,
  maxBatchesPerRun: DEFAULT_MAX_BATCHES_PER_RUN,
  runBatch: (ctx, cutoff, batchSize) => batchDeleteByAgeColumn(ctx, table, 'expires_at', cutoff, batchSize),
}));

const authEventsPolicy: RetentionPolicy = {
  name: 'raw_auth_events',
  dataClass: 'Raw login events (device fingerprint + IP address per login attempt)',
  action: 'delete',
  windowDays: 90,
  reasoning:
    'user_auth_events is a raw per-login signal carrying an IP address and device fingerprint, exactly the "raw device and IP signals" the task brief names as needing a short window. Its only consumers are near-term fraud/anomaly detection (recent login velocity, new-device alerts); anything durable it should have contributed to (trust score, a moderation flag) has already been written to trust_events/automated_moderation_flags, both retained forever, see RETAINED_FOREVER below, by the time this window closes, so deleting the raw event loses no audit capability.',
  batchSize: DEFAULT_BATCH_SIZE,
  maxBatchesPerRun: DEFAULT_MAX_BATCHES_PER_RUN,
  runBatch: (ctx, cutoff, batchSize) => batchDeleteByAgeColumn(ctx, 'user_auth_events', 'login_at', cutoff, batchSize),
};

const discoveryEventsPolicy: RetentionPolicy = {
  name: 'discovery_impressions',
  dataClass: 'Discovery-grid impressions (who saw whose card, and when)',
  action: 'delete',
  windowDays: 30,
  reasoning:
    'discovery_events is a pure impression log, one row per card shown, at high volume, with no per-row value past the short window photo A/B testing (photo_experiments, a separate bounded aggregate table, see docs/retention.md) and near-term "recently viewed" style features actually use. Kept only 30 days: long enough for those, far short of becoming a year-over-year behavioral history of who looked at whom.',
  batchSize: DEFAULT_BATCH_SIZE,
  maxBatchesPerRun: DEFAULT_MAX_BATCHES_PER_RUN,
  runBatch: (ctx, cutoff, batchSize) => batchDeleteByAgeColumn(ctx, 'discovery_events', 'created_at', cutoff, batchSize),
};

const messageFlagsPolicy: RetentionPolicy = {
  name: 'message_flag_signals',
  dataClass: 'Per-message automated regex flags (external contact / money request / link / crypto / spam / abuse pattern)',
  action: 'delete',
  windowDays: 180,
  reasoning:
    'message_flags is granular, high-volume, automated evidence about ONE message (flag_type + severity), distinct from the curated safety DECISION trail (moderation_actions, automated_moderation_flags, reports, appeals, all retained forever, see RETAINED_FOREVER) that these signals feed into. messages.analysis_flags already carries a denormalized summary on the message row itself (db/migrations/001_init.sql), so pruning the granular per-flag rows after 180 days loses no safety-relevant summary, only the redundant detail rows.',
  batchSize: DEFAULT_BATCH_SIZE,
  maxBatchesPerRun: DEFAULT_MAX_BATCHES_PER_RUN,
  runBatch: (ctx, cutoff, batchSize) => batchDeleteByAgeColumn(ctx, 'message_flags', 'created_at', cutoff, batchSize),
};

const notificationDedupLogPolicy: RetentionPolicy = {
  name: 'notification_dedup_log',
  dataClass: 'Notification idempotency keys (delivery-pipeline internals)',
  action: 'delete',
  windowDays: 30,
  reasoning:
    'notification_dedup_log exists solely so a retried domain operation cannot double-enqueue a notification (notifications/outbox.ts), its useful life is exactly as long as the outbox row it guards could plausibly still be retried, which is on the order of days, not months. Kept 30 days as a generous multiple of the outbox\'s own retry/backoff horizon.',
  batchSize: DEFAULT_BATCH_SIZE,
  maxBatchesPerRun: DEFAULT_MAX_BATCHES_PER_RUN,
  runBatch: (ctx, cutoff, batchSize) => batchDeleteByAgeColumn(ctx, 'notification_dedup_log', 'created_at', cutoff, batchSize),
};

/** Terminal `notification_outbox` statuses, a row in any of these will never be picked up by the delivery worker again (see db/migrations/011_notifications.sql / 015_phone.sql's CHECK constraints for the full status set); `queued`/`held_quiet_hours`/`failed_retryable` are deliberately excluded because those rows are still live work. */
const TERMINAL_OUTBOX_STATUSES = ['sent', 'dead', 'dropped_preference', 'dropped_no_target', 'dropped_rate_limited'] as const;

const notificationOutboxPolicy: RetentionPolicy = {
  name: 'notification_outbox_terminal',
  dataClass: 'Delivered/dead/dropped push+email outbox rows (delivery-pipeline internals, not the in-app notification center)',
  action: 'delete',
  windowDays: 30,
  reasoning:
    'notification_outbox is the push/email delivery QUEUE, not user-visible history (that\'s the notifications table below), once a row reaches a terminal status it is pure operational exhaust. 30 days is enough for delivery-pipeline debugging (why did this push never arrive?) without the queue growing forever at send volume.',
  batchSize: DEFAULT_BATCH_SIZE,
  maxBatchesPerRun: DEFAULT_MAX_BATCHES_PER_RUN,
  runBatch: async (ctx, cutoff, batchSize) => {
    const { rowCount } = await ctx.db.query(
      `WITH victims AS (
         SELECT id FROM notification_outbox
         WHERE created_at < $1 AND status = ANY($3::text[])
         ORDER BY created_at LIMIT $2
       )
       DELETE FROM notification_outbox WHERE id IN (SELECT id FROM victims)`,
      [cutoff, batchSize, TERMINAL_OUTBOX_STATUSES],
    );
    return rowCount ?? 0;
  },
};

const deliveredNotificationsPolicy: RetentionPolicy = {
  name: 'delivered_notifications',
  dataClass: 'In-app notification-center entries, once delivered (not still pending)',
  action: 'delete',
  windowDays: 90,
  reasoning:
    'notifications is the user-visible in-app notification center (notification.service.ts), its historical value drops sharply once an event is old news, but unlike the delivery-pipeline tables above it IS something a user might scroll back through, hence the longer 90-day window (vs. 30 for pure pipeline exhaust). status = \'pending\' rows are never touched by this policy regardless of age, a pending notification is still live work, not history.',
  batchSize: DEFAULT_BATCH_SIZE,
  maxBatchesPerRun: DEFAULT_MAX_BATCHES_PER_RUN,
  runBatch: async (ctx, cutoff, batchSize) => {
    const { rowCount } = await ctx.db.query(
      `WITH victims AS (
         SELECT id FROM notifications
         WHERE created_at < $1 AND status <> 'pending'
         ORDER BY created_at LIMIT $2
       )
       DELETE FROM notifications WHERE id IN (SELECT id FROM victims)`,
      [cutoff, batchSize],
    );
    return rowCount ?? 0;
  },
};

const refreshSessionsPolicy: RetentionPolicy = {
  name: 'stale_refresh_sessions',
  dataClass: 'Revoked or expired refresh-token sessions',
  action: 'delete',
  windowDays: 30,
  reasoning:
    'A refresh_sessions row already past its expires_at, or explicitly revoked, can never again be used to mint an access token (auth.service.ts), it is inert the moment either condition holds. 30 days past that point is a security-incident-investigation buffer ("was this session active around the time of report X"), not a functional need.',
  batchSize: DEFAULT_BATCH_SIZE,
  maxBatchesPerRun: DEFAULT_MAX_BATCHES_PER_RUN,
  runBatch: async (ctx, cutoff, batchSize) => {
    const { rowCount } = await ctx.db.query(
      `WITH victims AS (
         SELECT id FROM refresh_sessions
         WHERE (revoked_at IS NOT NULL AND revoked_at < $1) OR expires_at < $1
         ORDER BY expires_at LIMIT $2
       )
       DELETE FROM refresh_sessions WHERE id IN (SELECT id FROM victims)`,
      [cutoff, batchSize],
    );
    return rowCount ?? 0;
  },
};

// =========================================================================
// Policies that ANONYMIZE rather than delete, the row/aggregate needs to
// keep existing for integrity reasons, but its identifying payload doesn't.
// =========================================================================

const deviceFingerprintPolicy: RetentionPolicy = {
  name: 'stale_device_fingerprint_signals',
  dataClass: 'Device-fingerprint raw metadata (VPN/emulator signals, free-form jsonb payload) for devices unseen in a long time',
  action: 'anonymize',
  windowDays: 180,
  reasoning:
    'device_fingerprints is an AGGREGATE reputation record shared across every account that has ever used that device, unlike user_auth_events (one account, raw, short window), deleting it outright would erase abuse-pattern memory a still-active bad device deserves to keep. So this anonymizes, not deletes: after 180 days of no activity (last_seen_at), the free-form `metadata` jsonb payload (the actual raw signal blob) is cleared while `reputation_score`/`is_vpn`/`is_emulator`, already-derived classification outputs, not raw identifying data, are left intact, preserving the aggregate\'s abuse-detection value without an unbounded-retention raw-data liability.',
  batchSize: DEFAULT_BATCH_SIZE,
  maxBatchesPerRun: DEFAULT_MAX_BATCHES_PER_RUN,
  runBatch: async (ctx, cutoff, batchSize) => {
    const { rowCount } = await ctx.db.query(
      `WITH victims AS (
         SELECT id FROM device_fingerprints
         WHERE last_seen_at < $1 AND metadata <> '{}'::jsonb
         ORDER BY last_seen_at LIMIT $2
       )
       UPDATE device_fingerprints SET metadata = '{}'::jsonb
       WHERE id IN (SELECT id FROM victims)`,
      [cutoff, batchSize],
    );
    return rowCount ?? 0;
  },
};

const dormantChatContentPolicy: RetentionPolicy = {
  name: 'dormant_chat_content',
  dataClass: 'Message bodies belonging to long-archived (dormant) conversations',
  action: 'anonymize',
  windowDays: 730,
  reasoning:
    'Messages are core relationship content a still-active pair of users would reasonably expect to keep, nothing here touches an active/cooling/established conversation, at any age. Only conversations chatDecay.job.ts has already marked \'archived\' (dormant, no date resulted, decayed from inactivity) for a full 2 years get their message BODIES overwritten, one message at a time, with the exact same static placeholder (DELETED_MESSAGE_PLACEHOLDER) profile.service.ts#deleteMyAccount already uses for a deleted user\'s own messages, same "erase content, keep the row" policy this codebase already committed to, applied on an age trigger instead of a delete-my-account trigger. The conversation row, its timeline metadata, and the OTHER participant\'s ability to see the thread existed are all left untouched, exactly like that function\'s own boundary. Caveat documented in docs/retention.md: conversation.service.ts allows a new mutual match to resurrect an \'archived\' conversation (status -> \'active\'), if that happens more than 2 years after archival, the resurrected thread\'s old history reads as placeholder text, the same visual result a user already sees today when the OTHER party in a conversation has deleted their account.',
  batchSize: 200, // smaller than the flat-table default, this one joins conversations, so a batch does more work per row
  maxBatchesPerRun: DEFAULT_MAX_BATCHES_PER_RUN,
  runBatch: async (ctx, cutoff, batchSize) => {
    const { rowCount } = await ctx.db.query(
      `WITH victims AS (
         SELECT m.id FROM messages m
         JOIN conversations c ON c.id = m.conversation_id
         WHERE c.status = 'archived' AND c.archived_at < $1 AND m.body <> $3
         ORDER BY m.id LIMIT $2
       )
       UPDATE messages SET body = $3, analysis_flags = '[]'::jsonb
       WHERE id IN (SELECT id FROM victims)`,
      [cutoff, batchSize, DELETED_MESSAGE_PLACEHOLDER],
    );
    return rowCount ?? 0;
  },
};

export const RETENTION_POLICIES: RetentionPolicy[] = [
  ...verificationCodePolicies,
  authEventsPolicy,
  refreshSessionsPolicy,
  discoveryEventsPolicy,
  messageFlagsPolicy,
  notificationDedupLogPolicy,
  notificationOutboxPolicy,
  deliveredNotificationsPolicy,
  deviceFingerprintPolicy,
  dormantChatContentPolicy,
];

/**
 * Data classes deliberately retained forever, no policy above touches
 * them, and none should. Repeats (does not re-decide)
 * `profile.service.ts#deleteMyAccount`'s own documented boundary:
 *
 *   - FINANCIAL / LEDGER: payment_holds, payment_ledger. Tax/dispute/audit
 *     obligations outlive the account itself in most jurisdictions;
 *     payment_ledger is additionally an append-only immutable ledger by
 *     design (db/migrations/001_init.sql).
 *   - SAFETY AUDIT TRAIL: reports, moderation_actions, trust_events,
 *     appeals, automated_moderation_flags. Deleting a user's own history
 *     here on any timer would let a suspended/banned user launder their
 *     record simply by staying quiet long enough, the exact ban-evasion
 *     hole deleteMyAccount's own doc calls out by name. This is why
 *     `message_flags` (granular, per-message, superseded by a summary
 *     already on the message row, see messageFlagsPolicy above) gets a
 *     window while these five do not: those are the DECISION trail this
 *     one just feeds.
 *   - admin_audit_log: not part of the safety trail proper, but the same
 *     reasoning applies one level up, an admin action log that could be
 *     aged out would undermine the accountability it exists to provide.
 *
 * Exported (not just documented) so a test can assert the retention
 * sweep never issues a DELETE/UPDATE against any of these tables.
 */
export const RETAINED_FOREVER_TABLES: readonly string[] = [
  'payment_holds',
  'payment_ledger',
  'reports',
  'moderation_actions',
  'trust_events',
  'appeals',
  'automated_moderation_flags',
  'admin_audit_log',
];

/**
 * Data this file deliberately does NOT enforce a window on, WITHOUT
 * claiming it should live forever either, see docs/retention.md's "out
 * of scope" section for the full reasoning per table. In short:
 *   - photo_experiments, photo_recommendations: bounded aggregates
 *     (O(1) rows per user×photo, not one row per event) that already
 *     cascade-delete the moment the photo they reference is removed
 *     (user_photos ... ON DELETE CASCADE), there is no independent
 *     unbounded-growth problem to solve here.
 *   - compatibility_scores: also a bounded, continuously-upserted
 *     aggregate (compatibilityRefresh.job.ts), and actively owned by a
 *     concurrent build cutting the compatibility system over right now,
 *     left alone to avoid the two builds' automated jobs racing each
 *     other on the same table.
 *   - question_bank, user_question_answers, and everything under
 *     src/domain/questions/**: the in-flight typed-question-bank cutover
 *     this file's own docs (see questionLocalization.ts) are careful not
 *     to touch.
 *   - users, profiles, answers, user_tags, hard_filters, user_photos:
 *     already governed by the account-deletion boundary
 *     (profile.service.ts#deleteMyAccount) on a USER ACTION trigger, not
 *     an age trigger, bounded per-user data (roughly one row per
 *     user×question, not a log), not the "accumulates forever" problem
 *     this file targets.
 */
export const OUT_OF_SCOPE_TABLES: readonly string[] = [
  'photo_experiments',
  'photo_recommendations',
  'compatibility_scores',
  'question_bank',
  'user_question_answers',
];

export interface RetentionPolicyRunResult {
  policy: string;
  dataClass: string;
  action: RetentionAction;
  affected: number;
  batchesRun: number;
  /** True iff this run stopped because no more rows matched (fully caught up) rather than hitting `maxBatchesPerRun`. False means a backlog remains for the next scheduled run. */
  exhausted: boolean;
}

export interface RetentionSweepResult {
  ranAt: Date;
  policies: RetentionPolicyRunResult[];
  totalAffected: number;
}

/** Runs one policy's batches, bounded by its own `maxBatchesPerRun`, against a cutoff derived from `now`. Shared by `runRetentionSweep` (every policy) and `runRetentionPolicy` (one, by name, for tests that want to isolate a single class). */
async function runOnePolicy(ctx: Ctx, policy: RetentionPolicy, now: Date): Promise<RetentionPolicyRunResult> {
  const cutoff = addDays(now, -policy.windowDays);
  let affected = 0;
  let batchesRun = 0;
  let exhausted = false;

  while (batchesRun < policy.maxBatchesPerRun) {
    const rowsTouched = await policy.runBatch(ctx, cutoff, policy.batchSize);
    batchesRun += 1;
    affected += rowsTouched;
    if (rowsTouched < policy.batchSize) {
      exhausted = true;
      break;
    }
  }

  return { policy: policy.name, dataClass: policy.dataClass, action: policy.action, affected, batchesRun, exhausted };
}

/**
 * Runs every policy once, each bounded to its own `maxBatchesPerRun`,
 * this is the whole job (see src/jobs/retention.job.ts). Policies run
 * sequentially and independently: one policy's rows exhausting early
 * never borrows headroom from another's cap, and a later policy running
 * still happens even if an earlier one hit its cap (partial progress on
 * every class beats full progress on only the first).
 */
export async function runRetentionSweep(ctx: Ctx): Promise<RetentionSweepResult> {
  const now = ctx.clock.now();
  const results: RetentionPolicyRunResult[] = [];
  let totalAffected = 0;

  for (const policy of RETENTION_POLICIES) {
    const result = await runOnePolicy(ctx, policy, now);
    results.push(result);
    totalAffected += result.affected;
  }

  return { ranAt: now, policies: results, totalAffected };
}

/** Runs a single named policy (by `RetentionPolicy.name`), used by tests that want to exercise one class in isolation without paying for every other policy's queries in the same test. Throws if `name` doesn't match any registered policy (a test typo, not a runtime condition). */
export async function runRetentionPolicy(ctx: Ctx, name: string): Promise<RetentionPolicyRunResult> {
  const policy = RETENTION_POLICIES.find((p) => p.name === name);
  if (!policy) throw new Error(`retention.service: unknown policy "${name}"`);
  return runOnePolicy(ctx, policy, ctx.clock.now());
}
