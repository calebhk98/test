-- 002_agent_a.sql
-- Additive migration owned by Agent A (auth/profile/photo/photoExperiment).
-- 001_init.sql has no tables for auth token lifecycle (§28.2 rotating
-- refresh tokens, email verification, password reset) or for persisting
-- photo A/B test recommendations + their approve/reject decision (§7.3),
-- this migration adds exactly those, plus one column §5.1 needs
-- (terms-of-service acceptance) that 001 didn't carry. Nothing here alters
-- or drops anything from 001_init.sql.

-- =========================================================================
-- users.terms_accepted_at                                          §5.1
-- §5.1 requires "acceptance of terms" as one of the five required signup
-- fields; 001_init.sql's `users` table has no column for it. Nullable at
-- the DB level (existing/seeded rows have none) but `auth.register`
-- enforces it's always provided for new signups.
-- =========================================================================
ALTER TABLE users ADD COLUMN IF NOT EXISTS terms_accepted_at timestamptz;

-- =========================================================================
-- refresh_sessions                                                 §28.2
-- One row per login "session family". `token_hash` is the sha256 of the
-- *current* valid compact refresh token for this session (never the raw
-- token, see src/lib/hash.ts#sha256Hex). `auth.refresh` rotates by
-- updating `token_hash` + `expires_at` in place and stamping `rotated_at`;
-- presenting a token whose hash no longer matches the stored one is reuse
-- of an already-rotated token, and revokes the whole session (§28.2 "reuse
-- of a stolen-then-superseded refresh token is detectable").
-- =========================================================================
CREATE TABLE refresh_sessions (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(), -- also the JWT-ish payload's `sessionId`
  user_id      uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  token_hash   text NOT NULL,
  created_at   timestamptz NOT NULL DEFAULT now(),
  expires_at   timestamptz NOT NULL,
  rotated_at   timestamptz,
  revoked_at   timestamptz
);

CREATE INDEX idx_refresh_sessions_user ON refresh_sessions (user_id);
CREATE INDEX idx_refresh_sessions_active ON refresh_sessions (id) WHERE revoked_at IS NULL;

-- =========================================================================
-- email_verification_tokens                                        §6.2
-- One-time, expiring, hashed tokens (never store the raw token, mirrors
-- refresh_sessions above). A verified email is a §6.2 trust factor.
-- =========================================================================
CREATE TABLE email_verification_tokens (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  token_hash   text NOT NULL UNIQUE,
  created_at   timestamptz NOT NULL DEFAULT now(),
  expires_at   timestamptz NOT NULL,
  consumed_at  timestamptz
);

CREATE INDEX idx_email_verification_tokens_user ON email_verification_tokens (user_id);

-- =========================================================================
-- password_reset_tokens                                            §28.2
-- =========================================================================
CREATE TABLE password_reset_tokens (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  token_hash   text NOT NULL UNIQUE,
  created_at   timestamptz NOT NULL DEFAULT now(),
  expires_at   timestamptz NOT NULL,
  consumed_at  timestamptz
);

CREATE INDEX idx_password_reset_tokens_user ON password_reset_tokens (user_id);

-- =========================================================================
-- photo_recommendations                                            §7.3
-- Persists each computed photo A/B recommendation so `getMyPhotoTestResults`
-- reads stable state (not a fresh recompute per call) and so a user's
-- approve/reject decision sticks, `refreshAllRecommendations` (§25.5)
-- refreshes only rows still `pending`, never overwriting an already
-- decided one for the same (user, photo) pair.
-- =========================================================================
CREATE TABLE photo_recommendations (
  id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  photo_id               uuid NOT NULL REFERENCES user_photos (id) ON DELETE CASCADE,
  current_position       integer NOT NULL,
  recommended_position   integer NOT NULL,
  lift_percent           double precision NOT NULL,
  status                 text NOT NULL DEFAULT 'pending'
                           CHECK (status IN ('pending', 'approved', 'rejected')),
  created_at             timestamptz NOT NULL DEFAULT now(),
  updated_at             timestamptz NOT NULL DEFAULT now(),

  UNIQUE (user_id, photo_id)
);

CREATE INDEX idx_photo_recommendations_user ON photo_recommendations (user_id) WHERE status = 'pending';
