-- 015_phone.sql
--
-- Optional phone number + SMS notification channel build.
--
-- Corrects an earlier misreading: the product owner has clarified that a
-- phone number must never be MANDATORY (not requiring one is what keeps
-- the product usable for people who don't carry a conventional phone
-- number), but an OPTIONAL phone number, verified by one-time code, is
-- fully allowed, including as an opt-in SMS delivery channel. This
-- migration adds exactly the storage this needs; it does not touch, and
-- does not make required, anything any other table already has.
--
-- Two new tables, both owned by auth.service.ts (phone lives with the
-- account, not the profile):
--
--   user_phones               -- at most one phone per user; the current,
--                                 normalized (E.164) number + its verification
--                                 state. Deleting this row (removePhone) is
--                                 the entire "turn off SMS immediately" story.
--                                 delivery.ts re-checks this table live on
--                                 every SMS send, so a removed/never-verified
--                                 phone can never receive one, regardless of
--                                 what's cached anywhere else.
--   phone_verification_codes  -- one-time verification codes, hashed at
--                                 rest exactly like email_verification_tokens/
--                                 password_reset_tokens (002_agent_a.sql /
--                                 001_init.sql), never the raw code.
--
-- Plus two additive changes to the notification delivery pipeline's own
-- tables (011_notifications.sql, this build's sibling), so a third
-- transport channel, SMS, can flow through the exact same outbox/
-- preference/quiet-hours/coalescing machinery push and email already do:
--
--   notification_preferences.sms  -- new per-category toggle, defaulting
--                                     to OFF for every category (unlike
--                                     push/email's per-category defaults,
--                                     SMS costs real money per message, so
--                                     nothing turns it on but the user).
--   notification_outbox.channel   -- CHECK widened to allow 'sms'.
--   notification_outbox.status    -- CHECK widened to allow
--                                     'dropped_rate_limited', the outcome
--                                     of this build's per-user SMS cost cap
--                                     (see delivery.ts), terminal, like
--                                     the other dropped_* statuses, never
--                                     retried.

-- =========================================================================
-- user_phones (§5.2/§5.3-adjacent: optional, never required, see
-- auth.service.ts module doc)
-- =========================================================================
CREATE TABLE user_phones (
  user_id       uuid PRIMARY KEY REFERENCES users (id) ON DELETE CASCADE,
  -- Normalized E.164: '+' followed by 7-15 digits, no spaces/punctuation.
  -- auth.service.ts normalizes before this ever reaches the database.
  phone_e164    text NOT NULL CHECK (phone_e164 ~ '^\+[1-9]\d{6,14}$'),
  -- ISO 3166-1 alpha-2, e.g. 'US', kept alongside the E.164 number itself
  -- per the build brief ("store it normalised (E.164) with the country").
  country_code  text NOT NULL CHECK (country_code ~ '^[A-Z]{2}$'),
  -- NULL until a one-time code for THIS number is successfully consumed.
  -- Changing the number (re-calling requestPhoneVerification with a new
  -- number) resets this to NULL, a change always requires re-verification,
  -- exactly like adding a number the first time.
  verified_at   timestamptz,
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
);

-- A VERIFIED phone number can back only one account at a time (abuse/SMS-
-- pooling defense), but an unverified/pending number is not constrained
-- this way, so two people typing the same wrong number, or one number
-- mid-transfer between two people's accounts, never produces a confusing
-- conflict before either has actually proven ownership via the code.
CREATE UNIQUE INDEX idx_user_phones_e164_verified ON user_phones (phone_e164) WHERE verified_at IS NOT NULL;

-- =========================================================================
-- phone_verification_codes (one-time code issue/consume, rate-limited,
-- see auth.service.ts)
-- =========================================================================
CREATE TABLE phone_verification_codes (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id        uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  -- The number this code verifies. Carried on the code row (not just
  -- inferred from user_phones at consume time) so an in-flight code always
  -- verifies the exact number it was issued for, even in the narrow window
  -- where a user requests a new number before consuming an older code,
  -- auth.service.ts's requestPhoneVerification proactively consumes any
  -- still-pending codes for the user before issuing a new one, so this is
  -- defense in depth, not the only guard.
  phone_e164     text NOT NULL,
  -- SHA-256 hex of the code, same "never store the raw secret" discipline
  -- as password_reset_tokens.token_hash / email_verification_tokens.token_hash.
  code_hash      text NOT NULL,
  attempt_count  integer NOT NULL DEFAULT 0,
  created_at     timestamptz NOT NULL DEFAULT now(),
  expires_at     timestamptz NOT NULL,
  consumed_at    timestamptz
);

-- Drives both the "max N requests per hour" rate limit (count rows created
-- in a trailing window for this user) and "find my current pending code"
-- (most recent unconsumed row).
CREATE INDEX idx_phone_verification_codes_user_created ON phone_verification_codes (user_id, created_at DESC);

-- =========================================================================
-- notification_preferences.sms (additive column, default OFF for every
-- category, see notifications/preferences.ts DEFAULT_PREFERENCES)
-- =========================================================================
ALTER TABLE notification_preferences ADD COLUMN sms boolean NOT NULL DEFAULT false;

-- =========================================================================
-- notification_outbox: widen channel + status CHECKs for the new SMS
-- transport and its cost-cap outcome (see notifications/delivery.ts)
-- =========================================================================
ALTER TABLE notification_outbox DROP CONSTRAINT notification_outbox_channel_check;
ALTER TABLE notification_outbox ADD CONSTRAINT notification_outbox_channel_check
  CHECK (channel IN ('push', 'email', 'sms'));

ALTER TABLE notification_outbox DROP CONSTRAINT notification_outbox_status_check;
ALTER TABLE notification_outbox ADD CONSTRAINT notification_outbox_status_check
  CHECK (status IN (
    'queued', 'held_quiet_hours', 'sent',
    'failed_retryable', 'dead',
    'dropped_preference', 'dropped_no_target', 'dropped_rate_limited'
  ));
