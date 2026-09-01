/**
 * Local configuration constants for the notification delivery pipeline.
 *
 * `src/config/config.service.ts` (§21) is the real home for tunable
 * business variables, and every key below is written the way that
 * registry's entries are (name, default, one-line reason) — but
 * `config.service.ts` is out of this build's file-ownership boundary
 * (another agent's file; see the build brief's DO-NOT-TOUCH list), so
 * these live here as documented local constants instead. Each comment
 * names the exact `ConfigKeyRegistry` key it should become — see this
 * build's report, which lists them for whoever owns that file next.
 */

export const NOTIFICATION_CONFIG = {
  quietHours: {
    /**
     * What happens to a notification raised while the recipient is inside
     * their configured quiet hours: HOLD it (deliver right after quiet
     * hours end) rather than DROP it.
     *
     * Justification: a dropped match/message/date-request notification is
     * gone forever — the user opens the app later to a normal-looking
     * inbox with no idea anything happened overnight, which is a worse
     * outcome than a push arriving a few hours late. Holding costs
     * nothing but a few hours of latency and is trivially reversible
     * (still configurable below) if product data later says otherwise.
     * Would become `notifications.quiet_hours_policy` ('hold' | 'drop').
     */
    policy: 'hold' as const,
  },

  /**
   * Event types that bypass quiet hours entirely — delivered the moment
   * they're due regardless of the recipient's local time. Deliberately a
   * short, explicit list: only `safety_notice` (spec §20.1's safety
   * channel) is time-critical enough to interrupt a user's night; a match,
   * a message, or a date proposal can all comfortably wait until morning.
   * Would become `notifications.quiet_hours_bypass_events` (string[]).
   */
  quietHoursBypassEvents: ['safety_notice'] as const,

  message: {
    /**
     * Coalescing/debounce window for `message_received`: the first
     * message in a burst starts this timer; every additional message from
     * the same conversation before it elapses resets the timer (up to the
     * cap below) instead of firing its own push. This is what turns "5
     * messages in a minute" into one "3 new messages from Alex" push
     * (build brief) — the single biggest lever on uninstall rate for a
     * chat-heavy app. Would become
     * `notifications.message_coalesce_debounce_seconds`.
     */
    coalesceDebounceSeconds: 90,
    /**
     * Hard cap on how long a coalescing window may keep postponing
     * delivery, measured from the FIRST message in the batch — guarantees
     * a chatty burst still notifies within 10 minutes rather than being
     * pushed back indefinitely by a steady stream of messages. Would
     * become `notifications.message_coalesce_max_wait_seconds`.
     */
    coalesceMaxWaitSeconds: 600,
  },

  retry: {
    /** Would become `notifications.max_delivery_attempts`. */
    maxAttempts: 5,
    /** Would become `notifications.retry_backoff_base_seconds`. */
    backoffBaseSeconds: 30,
    /** Would become `notifications.retry_backoff_multiplier`. */
    backoffMultiplier: 2,
    /** Would become `notifications.retry_backoff_max_seconds`. */
    backoffMaxSeconds: 3600,
  },

  contentPreview: {
    /**
     * Default for "may a push show raw message text on the lock screen".
     * OFF by default — a lock-screen preview is visible to anyone holding
     * the phone (build brief). Would become
     * `notifications.content_preview_default_enabled`.
     */
    defaultEnabled: false,
    /** Truncation length applied to any opted-in preview text, in characters. */
    previewMaxChars: 80,
  },

  delivery: {
    /** Max outbox rows one `runNotificationDeliveryWorker` invocation processes. Would become `notifications.delivery_batch_size`. */
    batchSize: 200,
  },
} as const;

/** Computes the backoff delay (seconds) before retry number `attemptCount` (1-indexed, i.e. the delay applied AFTER the attemptCount'th failure). */
export function backoffSeconds(attemptCount: number): number {
  const { backoffBaseSeconds, backoffMultiplier, backoffMaxSeconds } = NOTIFICATION_CONFIG.retry;
  const raw = backoffBaseSeconds * Math.pow(backoffMultiplier, Math.max(0, attemptCount - 1));
  return Math.min(raw, backoffMaxSeconds);
}
