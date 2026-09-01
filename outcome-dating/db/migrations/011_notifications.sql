-- 011_notifications.sql
--
-- Notification DELIVERY build (this build; "NOTIFICATION DELIVERY" agent).
-- notification.service.ts (§20, another agent's file, read-only to this
-- build) already owns the `notifications` table from 001_init.sql — the
-- in-app notification center's source of truth. This migration does NOT
-- touch that table or any table owned by another agent's migration; it
-- adds five new tables that the delivery pipeline
-- (src/services/notifications/**) owns outright:
--
--   device_tokens                 -- push device registration (per user)
--   notification_preferences      -- per user x category channel toggles
--   notification_quiet_hours      -- per-user local-time quiet window
--   notification_content_preview  -- per-user lock-screen preview opt-in
--   notification_outbox           -- the actual push/email delivery queue
--   notification_dedup_log        -- stable-key idempotency for enqueues
--
-- See src/services/notifications/README-shaped module docs (outbox.ts,
-- preferences.ts, devices.ts) for the policies these tables back.

-- =========================================================================
-- device_tokens (§20.2 push channel)
-- =========================================================================
CREATE TABLE device_tokens (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  platform      text NOT NULL CHECK (platform IN ('ios', 'android', 'web')),
  -- Stable per-install identifier (vendor/installation id), kept for
  -- observability/debugging only — NOT part of the uniqueness key below.
  device_id     text NOT NULL,
  push_token    text NOT NULL,
  enabled       boolean NOT NULL DEFAULT true,
  created_at    timestamptz NOT NULL DEFAULT now(),
  last_seen_at  timestamptz NOT NULL DEFAULT now(),

  -- A push token is unique to one live installation at the processor
  -- (FCM/APNs never hand the same token to two concurrently-live
  -- installs). Re-registering the same (platform, push_token) is
  -- therefore an UPSERT on this key, not a new row (build brief: "must
  -- not duplicate"). It is ALSO the mechanism that makes a token moving
  -- to a new user (shared/resold device) safe: the row's `user_id` is
  -- reassigned in place, so the previous owner's next
  -- "which tokens belong to me" query simply no longer returns this row
  -- — there is no separate revoke step to forget, and no window where
  -- two users both appear to own the token.
  CONSTRAINT device_tokens_platform_token_key UNIQUE (platform, push_token)
);

CREATE INDEX idx_device_tokens_user_enabled ON device_tokens (user_id) WHERE enabled;
CREATE INDEX idx_device_tokens_device ON device_tokens (user_id, device_id);

-- =========================================================================
-- notification_preferences (per user x category channel toggles)
-- =========================================================================
-- Absence of a row for (user_id, category) means "use the code-level
-- default" (src/services/notifications/preferences.ts DEFAULT_PREFERENCES)
-- — same "no row = default" convention config_entries uses (§21), so a
-- brand-new user needs no seeding pass. 'safety' is deliberately NOT a
-- legal value here: safety_notice is not user-configurable (see
-- outbox.ts) so no preference row can ever apply to it.
CREATE TABLE notification_preferences (
  user_id     uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  category    text NOT NULL CHECK (category IN ('match', 'message', 'date_request', 'account_activity', 'marketing')),
  push        boolean NOT NULL,
  email       boolean NOT NULL,
  in_app      boolean NOT NULL,
  updated_at  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, category)
);

-- =========================================================================
-- notification_quiet_hours (per-user local-time quiet window, §20 delivery policy)
-- =========================================================================
-- Absence of a row means quiet hours are OFF (24/7 delivery allowed) —
-- matches `enabled` defaulting to false below, so an explicit row is only
-- ever written once a user actually sets a window.
CREATE TABLE notification_quiet_hours (
  user_id       uuid PRIMARY KEY REFERENCES users (id) ON DELETE CASCADE,
  enabled       boolean NOT NULL DEFAULT false,
  -- Minutes since local midnight, [0, 1439]. start > end is a valid
  -- overnight window (e.g. 1320=22:00 -> 480=08:00) and is handled by
  -- wraparound in quietHours.ts, not by a CHECK here.
  start_minute  integer NOT NULL DEFAULT 1320 CHECK (start_minute BETWEEN 0 AND 1439),
  end_minute    integer NOT NULL DEFAULT 480 CHECK (end_minute BETWEEN 0 AND 1439),
  -- IANA time zone name; the window is evaluated in the USER's own local
  -- time (build brief), never server time.
  timezone      text NOT NULL DEFAULT 'UTC',
  updated_at    timestamptz NOT NULL DEFAULT now()
);

-- =========================================================================
-- notification_content_preview (lock-screen preview opt-in; default OFF)
-- =========================================================================
-- Absence of a row means previews are OFF — a lock-screen preview is
-- visible to anyone holding the phone, so this is an opt-IN, never
-- opt-out (build brief).
CREATE TABLE notification_content_preview (
  user_id     uuid PRIMARY KEY REFERENCES users (id) ON DELETE CASCADE,
  enabled     boolean NOT NULL DEFAULT false,
  updated_at  timestamptz NOT NULL DEFAULT now()
);

-- =========================================================================
-- notification_dedup_log (idempotency: a retried domain op must not double-notify)
-- =========================================================================
-- One row per caller-supplied `dedupKey` (convention:
-- `${eventType}:${entityId}`, see outbox.ts). `INSERT ... ON CONFLICT
-- (dedup_key) DO NOTHING` is the atomic "have I seen this domain event
-- before" check enqueueNotification performs before doing anything else.
CREATE TABLE notification_dedup_log (
  dedup_key   text PRIMARY KEY,
  outbox_id   uuid NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now()
);

-- =========================================================================
-- notification_outbox (the actual push/email delivery queue)
-- =========================================================================
-- One row per (user, coalescing group, channel) currently in flight.
-- `channel` is deliberately only 'push' | 'email' here — the in-app
-- notification center is notification.service.ts's `notifications` table
-- (§20), which enqueueNotification calls into directly for canonical
-- event types; it is not re-modeled in this outbox (see outbox.ts doc).
CREATE TABLE notification_outbox (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  -- Superset of notification.service.ts's NotificationEventType plus
  -- 'message_received' (not in that frozen enum — see this build's
  -- report). Stored as free text, not a CHECK-constrained enum, so this
  -- table never needs a migration to add an event the delivery layer
  -- wants to support ahead of the shared enum catching up.
  event_type        text NOT NULL,
  category          text NOT NULL CHECK (category IN ('match', 'message', 'date_request', 'account_activity', 'marketing', 'safety')),
  channel           text NOT NULL CHECK (channel IN ('push', 'email')),
  template_key      text NOT NULL,
  payload           jsonb NOT NULL DEFAULT '{}'::jsonb,
  -- Rows with the same (user_id, coalescing_key, channel) while status is
  -- still 'queued'/'held_quiet_hours' are MERGED (coalesced_count++, see
  -- outbox.ts), not duplicated. Defaults to the row's own dedup key when
  -- the caller doesn't ask for batching, which makes coalescing a no-op
  -- (every row is its own group of one).
  coalescing_key    text NOT NULL,
  coalesced_count   integer NOT NULL DEFAULT 1,
  status            text NOT NULL DEFAULT 'queued'
                       CHECK (status IN (
                         'queued', 'held_quiet_hours', 'sent',
                         'failed_retryable', 'dead',
                         'dropped_preference', 'dropped_no_target'
                       )),
  attempt_count     integer NOT NULL DEFAULT 0,
  -- Delivery worker picks up rows where next_attempt_at <= now. Also
  -- doubles as: the coalescing debounce deadline (status='queued'), the
  -- quiet-hours-end deadline (status='held_quiet_hours'), and the backoff
  -- deadline (status='failed_retryable').
  next_attempt_at   timestamptz NOT NULL DEFAULT now(),
  last_error        text,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now(),
  delivered_at      timestamptz
);

CREATE INDEX idx_notification_outbox_due ON notification_outbox (next_attempt_at)
  WHERE status IN ('queued', 'held_quiet_hours', 'failed_retryable');
CREATE INDEX idx_notification_outbox_coalescing ON notification_outbox (user_id, coalescing_key, channel)
  WHERE status IN ('queued', 'held_quiet_hours');
CREATE INDEX idx_notification_outbox_user ON notification_outbox (user_id, created_at DESC);
