-- 021_retention_i18n.sql
-- Data retention, accessibility (photo alt text), and localization
-- (locale preference + question-bank translation) schema. Additive only,
-- every statement below either creates a brand-new table or ALTERs an
-- existing one with IF NOT EXISTS / a new column, exactly like
-- 002_agent_a.sql / 009_units_attributes.sql / 015_phone.sql did before
-- it. Nothing here drops or alters the MEANING of any existing column,
-- and nothing here touches a table owned by the concurrent question-bank
-- cutover (question_bank, user_question_answers) beyond adding a new,
-- separate table FK'd to question_bank(id), see
-- src/domain/i18n/questionLocalization.ts's module doc for why that's
-- safe to do without editing that table.

-- =========================================================================
-- PART 1, retention: supporting indexes.
--
-- src/services/retention.service.ts's batched sweep filters "everything
-- older than a cutoff" across a table with (at most) an existing
-- (user_id, created_at) composite index, fine for "this user's rows",
-- wrong shape for "every row past this age regardless of user", which is
-- what a retention sweep actually needs. Each index below is a plain
-- (or minimally filtered) btree on exactly the column each policy filters
-- by, so a batch's `ORDER BY <age column> LIMIT <batchSize>` is an index
-- scan, not a sequential scan, however large the table gets.
-- =========================================================================

CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_expires ON email_verification_tokens (expires_at);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_expires ON password_reset_tokens (expires_at);
CREATE INDEX IF NOT EXISTS idx_phone_verification_codes_expires ON phone_verification_codes (expires_at);
CREATE INDEX IF NOT EXISTS idx_user_auth_events_login_at ON user_auth_events (login_at);
CREATE INDEX IF NOT EXISTS idx_refresh_sessions_expires ON refresh_sessions (expires_at);
CREATE INDEX IF NOT EXISTS idx_discovery_events_created_at ON discovery_events (created_at);
CREATE INDEX IF NOT EXISTS idx_message_flags_created_at ON message_flags (created_at);
CREATE INDEX IF NOT EXISTS idx_notification_dedup_log_created_at ON notification_dedup_log (created_at);
CREATE INDEX IF NOT EXISTS idx_device_fingerprints_last_seen_at ON device_fingerprints (last_seen_at);
-- archived_at is only ever set alongside status = 'archived' (see
-- conversation.service.ts), but the partial predicate is written
-- explicitly so the index is only ever consulted for exactly the rows
-- dormantChatContentPolicy scans, never bloated by every other status.
CREATE INDEX IF NOT EXISTS idx_conversations_archived_at_retention ON conversations (archived_at) WHERE status = 'archived';
-- notification_outbox / notifications already have a (user_id,
-- created_at) index each (011_notifications.sql), good for "one user's
-- history", not for "every terminal-status row past this age across all
-- users", which is what the retention sweep's batch query needs.
CREATE INDEX IF NOT EXISTS idx_notification_outbox_created_at_retention ON notification_outbox (created_at)
  WHERE status IN ('sent', 'dead', 'dropped_preference', 'dropped_no_target', 'dropped_rate_limited');
CREATE INDEX IF NOT EXISTS idx_notifications_created_at_retention ON notifications (created_at) WHERE status <> 'pending';

-- =========================================================================
-- PART 2, accessibility: photo alt text.
--
-- One column pair on `user_photos` itself (not a side table) so a
-- description is structurally inseparable from the photo row it
-- describes, see src/services/photoAltText.service.ts's module doc for
-- the full "travels with the photo everywhere it appears" reasoning and
-- for why this build adds the column here rather than editing
-- photo.service.ts's own migration history.
-- =========================================================================

ALTER TABLE user_photos ADD COLUMN IF NOT EXISTS alt_text text;
ALTER TABLE user_photos ADD COLUMN IF NOT EXISTS alt_text_updated_at timestamptz;

-- =========================================================================
-- PART 3, localization: per-user locale preference.
--
-- A separate table (not a `users`/`profiles` column) so this build never
-- needs a write lock on either of those two heavily-contended, many-
-- agent-owned tables just to save a language preference, the same
-- "don't fight over the hot table" reasoning notification_quiet_hours /
-- notification_content_preview (011_notifications.sql) already applied
-- to their own per-user settings. Absence of a row means "no stored
-- preference yet" (src/domain/i18n/locales.ts#resolveLocale falls back to
-- the request's Accept-Language header, then DEFAULT_LOCALE), same
-- "no row = default" convention config_entries/notification_preferences
-- already use, so no seeding pass is needed for existing users.
-- =========================================================================

CREATE TABLE IF NOT EXISTS user_locale_preferences (
  user_id     uuid PRIMARY KEY REFERENCES users (id) ON DELETE CASCADE,
  -- BCP-47-ish tag, e.g. 'en', 'es', 'es-MX', validated at the
  -- application layer (src/http/routes/i18n.routes.ts), not by a CHECK
  -- here, so a new locale can be negotiated the moment
  -- src/domain/i18n/locales.ts#LOCALE_REGISTRY gains an entry, with no
  -- migration required.
  locale      text NOT NULL,
  updated_at  timestamptz NOT NULL DEFAULT now()
);

-- =========================================================================
-- PART 4, localization: question-bank translations.
--
-- Additive sibling to 008_questions.sql's `question_bank` table, FK'd to
-- it, never editing it. Keyed by (question_bank_id, locale), the exact
-- immutable per-VERSION row id an answer itself pins to (see
-- 008_questions.sql's "answer-version pinning" doc), precisely so a
-- translation is pinned to the exact English wording it was translated
-- FROM, same as an answer is pinned to the exact wording it was given TO.
-- See src/domain/i18n/questionLocalization.ts for the full reasoning and
-- the exact integration point the question-bank owner would adopt.
-- =========================================================================

CREATE TABLE IF NOT EXISTS question_bank_translations (
  question_bank_id  uuid NOT NULL REFERENCES question_bank (id) ON DELETE CASCADE,
  locale            text NOT NULL,
  -- NULL = question text not translated yet (falls back to the pinned
  -- question_bank row's own English question_text), distinct from an
  -- empty string, which is never written.
  question_text     text,
  -- Per-option/scale-endpoint label overrides. Keyed by the STABLE
  -- ChoiceOption.key (never the English label) for single_choice/
  -- multi_choice/frequency questions, or by the fixed keys "minLabel"/
  -- "maxLabel"/"midLabel" for a scale question, see
  -- questionLocalization.ts#localizeQuestionDefinition for how each is
  -- applied. Defaults to '{}' (no option labels translated yet) so a
  -- translator can localize the question text alone first, or vice versa.
  labels            jsonb NOT NULL DEFAULT '{}'::jsonb,
  updated_at        timestamptz NOT NULL DEFAULT now(),

  PRIMARY KEY (question_bank_id, locale)
);
