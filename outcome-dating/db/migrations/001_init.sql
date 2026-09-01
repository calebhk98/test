-- 001_init.sql
-- Outcome-Aligned Dating App — initial schema.
-- Source: SPEC.md §23 (26-table schema) plus tables the spec implies but
-- does not enumerate there (each noted below with its justifying section).
--
-- Conventions:
--   * All primary keys are `uuid` via gen_random_uuid(), except join/config
--     tables whose natural key the spec gives directly (config_entries.key,
--     feature_flags.key, answers (user_id,question_id), user_tags
--     (user_id,tag_id)).
--   * All timestamps are `timestamptz`.
--   * All money is `bigint` minor-unit cents. Never numeric/float.
--   * Every enumerated status/type set from the spec is a `text` column with
--     a `CHECK (... IN (...))` constraint (not a native Postgres ENUM) so
--     values can be extended with an ordinary migration rather than
--     ALTER TYPE ceremony.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =========================================================================
-- 1. users                                                          §23.1
-- =========================================================================
CREATE TABLE users (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email               text NOT NULL UNIQUE,
  password_hash       text NOT NULL,
  birthdate           date NOT NULL,
  status              text NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'suspended', 'deleted')),
  trust_score         integer NOT NULL DEFAULT 50
                        CHECK (trust_score BETWEEN 0 AND 100),
  trust_level         text NOT NULL DEFAULT 'standard'
                        CHECK (trust_level IN ('limited', 'standard', 'trusted', 'elite')), -- §6.1
  shadowbanned        boolean NOT NULL DEFAULT false,
  suspended           boolean NOT NULL DEFAULT false,
  email_verified_at   timestamptz,
  created_at          timestamptz NOT NULL DEFAULT now(),
  last_active_at      timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT users_min_age CHECK (birthdate <= (CURRENT_DATE - INTERVAL '18 years')) -- §5.1
);

CREATE INDEX idx_users_status ON users (status);

-- =========================================================================
-- 2. user_auth_events                                               §23.2
-- =========================================================================
CREATE TABLE user_auth_events (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id             uuid REFERENCES users (id) ON DELETE CASCADE, -- nullable: failed login with unknown email
  device_fingerprint  text,
  ip_address          inet,
  login_at            timestamptz NOT NULL DEFAULT now(),
  success             boolean NOT NULL
);

CREATE INDEX idx_user_auth_events_user_id ON user_auth_events (user_id, login_at DESC);
CREATE INDEX idx_user_auth_events_fingerprint ON user_auth_events (device_fingerprint);

-- =========================================================================
-- device_fingerprints  (implied: "device/auth signals" — §6.2, §19.2)
-- Aggregate reputation per device, distinct from the per-login event log
-- above. Feeds the trust score ("consistent location/device behavior") and
-- moderation signals ("suspicious device/IP signals").
-- =========================================================================
CREATE TABLE device_fingerprints (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  fingerprint_hash      text NOT NULL UNIQUE,
  first_seen_at         timestamptz NOT NULL DEFAULT now(),
  last_seen_at          timestamptz NOT NULL DEFAULT now(),
  distinct_user_count   integer NOT NULL DEFAULT 0,
  is_vpn                boolean NOT NULL DEFAULT false,
  is_emulator           boolean NOT NULL DEFAULT false,
  reputation_score      integer NOT NULL DEFAULT 50 CHECK (reputation_score BETWEEN 0 AND 100),
  metadata              jsonb NOT NULL DEFAULT '{}'::jsonb
);

-- =========================================================================
-- 3. profiles                                                       §23.3
-- =========================================================================
CREATE TABLE profiles (
  user_id                  uuid PRIMARY KEY REFERENCES users (id) ON DELETE CASCADE,
  display_name             text NOT NULL,
  bio                      text NOT NULL DEFAULT '',
  city                     text,
  latitude                 double precision,     -- true coordinates, never returned to other users directly (§7.1, §28.5)
  longitude                double precision,
  location_fuzzed          boolean NOT NULL DEFAULT true, -- §7.1 "exact location MUST NOT be shown"
  age                      integer NOT NULL CHECK (age >= 18),
  gender                   text NOT NULL,
  seeking                  text NOT NULL,
  relationship_intention   text NOT NULL,
  profile_completeness     integer NOT NULL DEFAULT 0 CHECK (profile_completeness BETWEEN 0 AND 100), -- §7.1, §9.4 phase 2
  updated_at               timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_profiles_city ON profiles (city);

-- =========================================================================
-- 4. user_photos                                                    §23.4
-- =========================================================================
CREATE TABLE user_photos (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  image_url             text NOT NULL,
  position              integer NOT NULL DEFAULT 0,
  is_primary            boolean NOT NULL DEFAULT false,
  moderation_status     text NOT NULL DEFAULT 'pending'
                          CHECK (moderation_status IN ('pending', 'approved', 'rejected', 'flagged')), -- §7.2
  face_detected         boolean,
  blur_score            double precision,
  brightness_score      double precision,
  group_photo_detected  boolean,
  perceptual_hash       text, -- §7.2 duplicate/scam image detection
  created_at            timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_user_photos_user_id ON user_photos (user_id, position);
CREATE INDEX idx_user_photos_perceptual_hash ON user_photos (perceptual_hash);
-- Exactly one primary photo per user (§7.1/§7.2 "first photo must contain a visible face").
CREATE UNIQUE INDEX uq_user_photos_one_primary ON user_photos (user_id) WHERE is_primary;

-- =========================================================================
-- 5. photo_experiments                                              §23.5
-- =========================================================================
CREATE TABLE photo_experiments (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id             uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  photo_id            uuid NOT NULL REFERENCES user_photos (id) ON DELETE CASCADE,
  impressions         bigint NOT NULL DEFAULT 0,
  interests_sent      bigint NOT NULL DEFAULT 0,
  interests_accepted  bigint NOT NULL DEFAULT 0,
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now(),

  UNIQUE (user_id, photo_id)
);

CREATE INDEX idx_photo_experiments_user_id ON photo_experiments (user_id);

-- =========================================================================
-- 6. questions                                                      §23.6
-- =========================================================================
CREATE TABLE questions (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug                  text NOT NULL UNIQUE,
  category              text NOT NULL,
  question_text         text NOT NULL,
  self_left_label       text NOT NULL,
  self_right_label      text NOT NULL,
  partner_left_label    text NOT NULL,
  partner_right_label   text NOT NULL,
  weight                double precision NOT NULL DEFAULT 1.0 CHECK (weight >= 0), -- §16.2 base_weight
  polarity              text NOT NULL DEFAULT 'standard'
                          CHECK (polarity IN ('standard', 'reversed')), -- §16.2
  sensitive             boolean NOT NULL DEFAULT false, -- §8.5
  active                boolean NOT NULL DEFAULT true,
  created_at            timestamptz NOT NULL DEFAULT now(),
  updated_at            timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_questions_category ON questions (category) WHERE active;

-- =========================================================================
-- 7. answers                                                        §23.7
-- =========================================================================
CREATE TABLE answers (
  user_id         uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  question_id     uuid NOT NULL REFERENCES questions (id) ON DELETE CASCADE,
  self_value      smallint CHECK (self_value BETWEEN 1 AND 5),     -- nullable: "prefer not to say" (§8.5)
  partner_value   smallint CHECK (partner_value BETWEEN 1 AND 5),  -- nullable: "prefer not to say" (§8.5)
  updated_at      timestamptz NOT NULL DEFAULT now(),

  PRIMARY KEY (user_id, question_id)
);

CREATE INDEX idx_answers_question_id ON answers (question_id);

-- =========================================================================
-- 8. interest_tags                                                  §23.8
-- =========================================================================
CREATE TABLE interest_tags (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name                text NOT NULL UNIQUE,
  category            text NOT NULL,
  public_description  text NOT NULL DEFAULT '',
  created_at          timestamptz NOT NULL DEFAULT now()
);

-- =========================================================================
-- 9. user_tags                                                      §23.9
-- =========================================================================
CREATE TABLE user_tags (
  user_id     uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  tag_id      uuid NOT NULL REFERENCES interest_tags (id) ON DELETE CASCADE,
  visibility  text NOT NULL DEFAULT 'public'
                CHECK (visibility IN ('public', 'private_reciprocal', 'hidden')), -- §8.4, §23.9
  created_at  timestamptz NOT NULL DEFAULT now(),

  PRIMARY KEY (user_id, tag_id)
);

CREATE INDEX idx_user_tags_tag_id ON user_tags (tag_id);

-- =========================================================================
-- 10. hard_filters                                                  §23.10
-- =========================================================================
CREATE TABLE hard_filters (
  user_id      uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  filter_key   text NOT NULL,
  operator     text NOT NULL CHECK (operator IN ('eq', 'neq', 'gte', 'lte', 'gt', 'lt', 'in')), -- §9.2 examples
  value        jsonb NOT NULL, -- number, string, or array depending on filter_key/operator
  enabled      boolean NOT NULL DEFAULT true,
  updated_at   timestamptz NOT NULL DEFAULT now(),

  PRIMARY KEY (user_id, filter_key)
);

CREATE INDEX idx_hard_filters_user_id ON hard_filters (user_id) WHERE enabled;

-- =========================================================================
-- 11. discovery_events                                              §23.11
-- =========================================================================
CREATE TABLE discovery_events (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  viewer_user_id      uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  candidate_user_id   uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  primary_photo_id    uuid REFERENCES user_photos (id) ON DELETE SET NULL, -- §7.3 A/B impression tracking
  source              text NOT NULL DEFAULT 'discovery_grid',
  created_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_discovery_events_viewer ON discovery_events (viewer_user_id, created_at DESC);
CREATE INDEX idx_discovery_events_candidate ON discovery_events (candidate_user_id, created_at DESC);

-- =========================================================================
-- compatibility_scores  (§16.3 — precomputed pairwise scores)
-- Explicitly given a schema by the spec (§16.3) for the nightly/incremental
-- refresh job (§25.4), even though it lives outside the §23 table list.
-- =========================================================================
CREATE TABLE compatibility_scores (
  user_id       uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  candidate_id  uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  score         double precision NOT NULL CHECK (score BETWEEN 0 AND 1),
  computed_at   timestamptz NOT NULL DEFAULT now(),

  PRIMARY KEY (user_id, candidate_id)
);

CREATE INDEX idx_compatibility_scores_user_score ON compatibility_scores (user_id, score DESC);

-- =========================================================================
-- 12. interests                                                     §23.12
-- =========================================================================
CREATE TABLE interests (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  sender_id        uuid NOT NULL REFERENCES users (id),
  recipient_id     uuid NOT NULL REFERENCES users (id),
  status           text NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending', 'accepted', 'declined', 'expired', 'canceled')), -- §11.4
  policy_snapshot  jsonb NOT NULL, -- §21.3
  created_at       timestamptz NOT NULL DEFAULT now(),
  expires_at       timestamptz NOT NULL,
  accepted_at      timestamptz,
  declined_at      timestamptz,
  canceled_at      timestamptz,
  expired_at       timestamptz,

  CONSTRAINT interests_not_self CHECK (sender_id <> recipient_id)
);

-- One pending interest per (sender, recipient) pair — re-sending after
-- decline/expiry/cancel is allowed, but not while one is already pending.
CREATE UNIQUE INDEX uq_interests_pending_pair
  ON interests (sender_id, recipient_id) WHERE status = 'pending';

CREATE INDEX idx_interests_recipient_status ON interests (recipient_id, status);
CREATE INDEX idx_interests_sender_status ON interests (sender_id, status);
CREATE INDEX idx_interests_expiry_job ON interests (status, expires_at) WHERE status = 'pending'; -- §25.1

-- =========================================================================
-- 13. conversations                                                 §23.13
-- =========================================================================
CREATE TABLE conversations (
  id                       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_a_id                uuid NOT NULL REFERENCES users (id),
  user_b_id                uuid NOT NULL REFERENCES users (id),
  status                   text NOT NULL DEFAULT 'active'
                             CHECK (status IN ('active', 'cooling', 'archived', 'established')), -- §23.13
  created_at               timestamptz NOT NULL DEFAULT now(),
  last_message_at          timestamptz,
  first_date_completed_at  timestamptz,
  archived_at              timestamptz,

  CONSTRAINT conversations_not_self CHECK (user_a_id <> user_b_id),
  CONSTRAINT conversations_ordered_pair CHECK (user_a_id < user_b_id) -- canonical ordering, enables the uniqueness index below
);

-- At most one conversation per unordered user pair.
CREATE UNIQUE INDEX uq_conversations_pair ON conversations (user_a_id, user_b_id);
CREATE INDEX idx_conversations_user_a ON conversations (user_a_id, status);
CREATE INDEX idx_conversations_user_b ON conversations (user_b_id, status);
CREATE INDEX idx_conversations_decay_job ON conversations (status, last_message_at) WHERE status IN ('active', 'cooling'); -- §25.3

-- =========================================================================
-- 14. messages                                                      §23.14
-- =========================================================================
CREATE TABLE messages (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id  uuid NOT NULL REFERENCES conversations (id) ON DELETE CASCADE,
  sender_id        uuid NOT NULL REFERENCES users (id),
  body             text NOT NULL,
  created_at       timestamptz NOT NULL DEFAULT now(),
  read_at          timestamptz,
  analysis_flags   jsonb NOT NULL DEFAULT '[]'::jsonb -- denormalized summary; full detail in message_flags (§12.4, §18.2)
);

CREATE INDEX idx_messages_conversation_created ON messages (conversation_id, created_at);
CREATE INDEX idx_messages_sender_rate ON messages (sender_id, created_at); -- §12.3 rate limiting

-- =========================================================================
-- 15. message_flags                                                 §23.15
-- =========================================================================
CREATE TABLE message_flags (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  message_id   uuid NOT NULL REFERENCES messages (id) ON DELETE CASCADE,
  flag_type    text NOT NULL
                 CHECK (flag_type IN (
                   'external_contact', 'money_request', 'link', 'crypto', 'spam_pattern', 'abuse_pattern'
                 )), -- §23.15
  severity     integer NOT NULL CHECK (severity BETWEEN 1 AND 5),
  created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_message_flags_message_id ON message_flags (message_id);

-- =========================================================================
-- 16. venues                                                        §23.16
-- =========================================================================
CREATE TABLE venues (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name               text NOT NULL,
  address            text NOT NULL,
  latitude           double precision NOT NULL,
  longitude          double precision NOT NULL,
  category           text NOT NULL
                       CHECK (category IN (
                         'coffee', 'dessert', 'drinks', 'walk', 'museum', 'arcade',
                         'live_music', 'comedy', 'class_activity', 'food_market'
                       )), -- §13.2
  active             boolean NOT NULL DEFAULT true,
  margin_percent     double precision NOT NULL DEFAULT 0 CHECK (margin_percent BETWEEN 0 AND 100),
  time_slot_config   jsonb NOT NULL DEFAULT '{}'::jsonb, -- §13.2 "available time slots"
  redemption_method  text NOT NULL DEFAULT 'qr_scan'
                       CHECK (redemption_method IN ('qr_scan', 'staff_manual_code')), -- §13.2, §15.3
  created_at         timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_venues_category_active ON venues (category) WHERE active;

-- =========================================================================
-- venue_staff  (implied — §4.2 "Venue Staff" role)
-- Venue staff are users with elevated, venue-scoped, narrowly-permissioned
-- access (can redeem vouchers; cannot see chats/emails/card details).
-- =========================================================================
CREATE TABLE venue_staff (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  venue_id    uuid NOT NULL REFERENCES venues (id) ON DELETE CASCADE,
  active      boolean NOT NULL DEFAULT true,
  created_at  timestamptz NOT NULL DEFAULT now(),

  UNIQUE (user_id, venue_id)
);

CREATE INDEX idx_venue_staff_venue_id ON venue_staff (venue_id) WHERE active;

-- =========================================================================
-- admin_users  (implied — §4.3 "Admin" role)
-- =========================================================================
CREATE TABLE admin_users (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     uuid NOT NULL UNIQUE REFERENCES users (id) ON DELETE CASCADE,
  active      boolean NOT NULL DEFAULT true,
  created_at  timestamptz NOT NULL DEFAULT now()
);

-- =========================================================================
-- 17. date_proposals                                                §23.17
-- =========================================================================
CREATE TABLE date_proposals (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id       uuid NOT NULL REFERENCES conversations (id),
  proposer_id           uuid NOT NULL REFERENCES users (id),
  recipient_id          uuid NOT NULL REFERENCES users (id),
  venue_id              uuid NOT NULL REFERENCES venues (id),
  scheduled_start        timestamptz NOT NULL,
  scheduled_end          timestamptz NOT NULL,
  optional_note         text,
  status                text NOT NULL DEFAULT 'draft'
                          CHECK (status IN (
                            'draft', 'pending_acceptance', 'accepted', 'declined', 'expired',
                            'canceled', 'payment_failed', 'charged', 'ticketed', 'completed',
                            'completed_unverified', 'no_show', 'refunded', 'disputed'
                          )), -- §13.3 plus completed_unverified (§15.4)
  policy_snapshot       jsonb NOT NULL, -- §21.3
  escrow_amount_cents   bigint NOT NULL CHECK (escrow_amount_cents >= 0),
  created_at            timestamptz NOT NULL DEFAULT now(),
  accepted_at           timestamptz,
  declined_at           timestamptz,
  expired_at            timestamptz,
  canceled_at           timestamptz,
  charged_at            timestamptz,
  ticketed_at           timestamptz,
  completed_at          timestamptz,

  CONSTRAINT date_proposals_not_self CHECK (proposer_id <> recipient_id),
  CONSTRAINT date_proposals_end_after_start CHECK (scheduled_end > scheduled_start)
);

CREATE INDEX idx_date_proposals_conversation ON date_proposals (conversation_id);
CREATE INDEX idx_date_proposals_proposer ON date_proposals (proposer_id);
CREATE INDEX idx_date_proposals_recipient ON date_proposals (recipient_id);
CREATE INDEX idx_date_proposals_expiry_job ON date_proposals (status, created_at) WHERE status = 'pending_acceptance'; -- §25.2
CREATE INDEX idx_date_proposals_venue ON date_proposals (venue_id, scheduled_start);

-- =========================================================================
-- date_attendance_confirmations  (implied — §15.4 no-scan fallback)
-- Tracks each user's self-reported attendance confirmation, independent
-- from the (separate, quality-oriented) post_date_feedback below.
-- =========================================================================
CREATE TABLE date_attendance_confirmations (
  date_proposal_id  uuid NOT NULL REFERENCES date_proposals (id) ON DELETE CASCADE,
  user_id           uuid NOT NULL REFERENCES users (id),
  confirmed_at      timestamptz NOT NULL DEFAULT now(),

  PRIMARY KEY (date_proposal_id, user_id)
);

-- =========================================================================
-- 18. payment_holds                                                 §23.18
-- =========================================================================
CREATE TABLE payment_holds (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  date_proposal_id      uuid NOT NULL REFERENCES date_proposals (id),
  user_id               uuid NOT NULL REFERENCES users (id),
  processor             text NOT NULL, -- e.g. "fake" | "stripe" — see PaymentProcessor port
  processor_intent_id   text,
  amount_cents          bigint NOT NULL CHECK (amount_cents >= 0),
  currency              text NOT NULL DEFAULT 'usd',
  status                text NOT NULL DEFAULT 'pending'
                          CHECK (status IN (
                            'pending', 'authorized', 'capture_pending', 'captured',
                            'released', 'failed', 'refunded'
                          )), -- §23.18
  authorized_at         timestamptz,
  captured_at           timestamptz,
  released_at           timestamptz,
  refunded_at           timestamptz,
  failure_reason        text,

  UNIQUE (date_proposal_id, user_id) -- one hold per user per proposal (proposer's, recipient's)
);

CREATE INDEX idx_payment_holds_date_proposal ON payment_holds (date_proposal_id);
CREATE INDEX idx_payment_holds_user ON payment_holds (user_id);
CREATE INDEX idx_payment_holds_status ON payment_holds (status);

-- =========================================================================
-- 19. payment_ledger                                                §23.19
-- Immutable: application code MUST only INSERT here, never UPDATE/DELETE
-- (§14.8 "immutable ledger"). No ON DELETE CASCADE from users — financial
-- records are retained even if the user's profile is later anonymized
-- (§29).
-- =========================================================================
CREATE TABLE payment_ledger (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               uuid NOT NULL REFERENCES users (id),
  date_proposal_id      uuid NOT NULL REFERENCES date_proposals (id),
  payment_hold_id       uuid REFERENCES payment_holds (id),
  type                  text NOT NULL
                          CHECK (type IN ('authorization', 'capture', 'release', 'refund', 'dispute', 'chargeback')), -- §14.8
  amount_cents          bigint NOT NULL,
  currency              text NOT NULL DEFAULT 'usd',
  processor_reference   text,
  metadata              jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at            timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_payment_ledger_user ON payment_ledger (user_id, created_at DESC);
CREATE INDEX idx_payment_ledger_date_proposal ON payment_ledger (date_proposal_id);
CREATE INDEX idx_payment_ledger_type ON payment_ledger (type);

-- =========================================================================
-- payment_methods (implied — §24.10 payment-methods endpoints, §28.4)
-- Stores only processor-side tokens/references, never card numbers.
-- =========================================================================
CREATE TABLE payment_methods (
  id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  processor              text NOT NULL,
  processor_token        text NOT NULL, -- opaque token/payment-method-id from the processor
  brand                  text,
  last4                  text,
  is_default             boolean NOT NULL DEFAULT false,
  verified_at            timestamptz, -- §5.4 "verified payment method" trust signal
  created_at             timestamptz NOT NULL DEFAULT now(),
  deleted_at             timestamptz
);

CREATE INDEX idx_payment_methods_user ON payment_methods (user_id) WHERE deleted_at IS NULL;

-- =========================================================================
-- 20. vouchers                                                      §23.20
-- =========================================================================
CREATE TABLE vouchers (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  date_proposal_id   uuid NOT NULL UNIQUE REFERENCES date_proposals (id),
  venue_id           uuid NOT NULL REFERENCES venues (id),
  code               text NOT NULL UNIQUE, -- human-enterable fallback code (§15.3)
  qr_payload         text NOT NULL,        -- signed compact token, see src/lib/signing.ts (§15.2)
  status             text NOT NULL DEFAULT 'issued'
                       CHECK (status IN ('issued', 'redeemed', 'expired', 'canceled')), -- §23.20
  issued_at          timestamptz NOT NULL DEFAULT now(),
  expires_at         timestamptz NOT NULL,
  redeemed_at        timestamptz
);

CREATE INDEX idx_vouchers_status_expiry ON vouchers (status, expires_at) WHERE status = 'issued'; -- §25.8

-- =========================================================================
-- 21. venue_redemptions                                             §23.21
-- =========================================================================
CREATE TABLE venue_redemptions (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  voucher_id       uuid NOT NULL REFERENCES vouchers (id),
  venue_id         uuid NOT NULL REFERENCES venues (id),
  venue_staff_id   uuid REFERENCES venue_staff (id), -- nullable: fallback/manual admin redemption
  method           text NOT NULL CHECK (method IN ('qr_scan', 'manual_code')), -- §15.3
  created_at       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_venue_redemptions_voucher ON venue_redemptions (voucher_id);

-- =========================================================================
-- post_date_feedback  (implied — §2, §15.4, §26.2 "post-date positive feedback rate")
-- Distinct from date_attendance_confirmations: this is quality feedback
-- collected once attendance is already established (via redemption or the
-- no-scan fallback), not a completion signal itself.
-- =========================================================================
CREATE TABLE post_date_feedback (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  date_proposal_id    uuid NOT NULL REFERENCES date_proposals (id) ON DELETE CASCADE,
  user_id             uuid NOT NULL REFERENCES users (id),
  positive            boolean NOT NULL, -- §26.2 "post-date positive feedback rate"
  would_meet_again    boolean,
  safety_concern      boolean NOT NULL DEFAULT false,
  notes               text,
  created_at          timestamptz NOT NULL DEFAULT now(),

  UNIQUE (date_proposal_id, user_id)
);

CREATE INDEX idx_post_date_feedback_date_proposal ON post_date_feedback (date_proposal_id);

-- =========================================================================
-- 22. reports                                                       §23.22
-- =========================================================================
CREATE TABLE reports (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  reporter_id       uuid NOT NULL REFERENCES users (id),
  reported_id       uuid NOT NULL REFERENCES users (id),
  conversation_id   uuid REFERENCES conversations (id),
  message_id        uuid REFERENCES messages (id),
  category          text NOT NULL
                      CHECK (category IN (
                        'fake_profile', 'scam_money_request', 'harassment', 'unsafe_behavior',
                        'misleading_photos', 'minor_suspected', 'spam', 'no_show',
                        'inappropriate_content', 'other'
                      )), -- §18.3
  severity          integer NOT NULL DEFAULT 1 CHECK (severity BETWEEN 1 AND 5),
  details            text,
  created_at        timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT reports_not_self CHECK (reporter_id <> reported_id)
);

CREATE INDEX idx_reports_reported_id ON reports (reported_id, created_at DESC);
CREATE INDEX idx_reports_reporter_id ON reports (reporter_id, created_at DESC);

-- =========================================================================
-- blocks  (implied — §4.1 "report/block users", §10.2, §18.2 "block count")
-- =========================================================================
CREATE TABLE blocks (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  blocker_id   uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  blocked_id   uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  created_at   timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT blocks_not_self CHECK (blocker_id <> blocked_id),
  UNIQUE (blocker_id, blocked_id)
);

CREATE INDEX idx_blocks_blocked_id ON blocks (blocked_id); -- §10.2 "neither user has blocked the other"

-- =========================================================================
-- 23. moderation_actions                                            §23.23
-- =========================================================================
CREATE TABLE moderation_actions (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     uuid NOT NULL REFERENCES users (id),
  action      text NOT NULL
                CHECK (action IN ('none', 'warning', 'restriction', 'shadowban', 'suspension')), -- §18.4
  reason      text NOT NULL,
  score       double precision NOT NULL DEFAULT 0, -- §18.5
  metadata    jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_moderation_actions_user_id ON moderation_actions (user_id, created_at DESC);

-- =========================================================================
-- appeals  (implied — §18.6 automated appeals)
-- =========================================================================
CREATE TABLE appeals (
  id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  moderation_action_id   uuid REFERENCES moderation_actions (id),
  method                 text NOT NULL
                           CHECK (method IN (
                             'liveness_check', 'payment_verification', 'cooldown', 'existing_signals'
                           )), -- §18.6
  status                 text NOT NULL DEFAULT 'pending'
                           CHECK (status IN ('pending', 'approved', 'rejected')),
  submitted_at           timestamptz NOT NULL DEFAULT now(),
  resolved_at            timestamptz,
  metadata               jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_appeals_user_id ON appeals (user_id, submitted_at DESC);
CREATE INDEX idx_appeals_status ON appeals (status) WHERE status = 'pending';

-- =========================================================================
-- 24. trust_events                                                  §23.24
-- =========================================================================
CREATE TABLE trust_events (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     uuid NOT NULL REFERENCES users (id),
  event_type  text NOT NULL, -- e.g. verified_email, completed_date, report_received, no_show, chargeback (§6.2)
  delta       double precision NOT NULL,
  metadata    jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_trust_events_user_id ON trust_events (user_id, created_at DESC);

-- =========================================================================
-- notifications  (implied — §20 notification system)
-- =========================================================================
CREATE TABLE notifications (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  event_type   text NOT NULL
                 CHECK (event_type IN (
                   'interest_received', 'interest_accepted', 'interest_declined', 'interest_expiring_soon',
                   'chat_opened', 'date_proposal_received', 'date_accepted', 'payment_hold_authorized',
                   'payment_failed', 'ticket_issued', 'date_reminder', 'venue_redeemed',
                   'post_date_feedback_request', 'chat_cooling', 'trust_level_changed', 'safety_notice'
                 )), -- §20.1
  channel      text NOT NULL CHECK (channel IN ('push', 'email', 'in_app')), -- §20.2
  template_key text NOT NULL, -- static/template copy key — never generated text (§1, §20)
  payload      jsonb NOT NULL DEFAULT '{}'::jsonb,
  status       text NOT NULL DEFAULT 'pending'
                 CHECK (status IN ('pending', 'sent', 'failed', 'read')),
  created_at   timestamptz NOT NULL DEFAULT now(),
  sent_at      timestamptz,
  read_at      timestamptz
);

CREATE INDEX idx_notifications_user_id ON notifications (user_id, created_at DESC);
CREATE INDEX idx_notifications_pending ON notifications (status) WHERE status = 'pending';

-- =========================================================================
-- 25. config_entries                                                §23.25
-- =========================================================================
CREATE TABLE config_entries (
  key          text PRIMARY KEY,
  value_json   jsonb NOT NULL,
  description  text NOT NULL DEFAULT '',
  version      integer NOT NULL DEFAULT 1,
  updated_by   text NOT NULL,
  updated_at   timestamptz NOT NULL DEFAULT now()
);

-- =========================================================================
-- 26. feature_flags                                                 §23.26
-- =========================================================================
CREATE TABLE feature_flags (
  key               text PRIMARY KEY,
  enabled           boolean NOT NULL DEFAULT false,
  rollout_percent   integer NOT NULL DEFAULT 0 CHECK (rollout_percent BETWEEN 0 AND 100),
  segments          text[] NOT NULL DEFAULT '{}',
  updated_at        timestamptz NOT NULL DEFAULT now()
);

-- =========================================================================
-- admin_audit_log  (implied — §4.3, §21.2, §27, §28.6 "log admin actions")
-- =========================================================================
CREATE TABLE admin_audit_log (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  admin_user_id   uuid NOT NULL REFERENCES users (id),
  action          text NOT NULL, -- e.g. "config.set", "question.create", "venue.deactivate"
  target_type     text NOT NULL, -- e.g. "config_entries", "questions", "venues", "users"
  target_id       text,
  before_json     jsonb,
  after_json      jsonb,
  created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_admin_audit_log_admin ON admin_audit_log (admin_user_id, created_at DESC);
CREATE INDEX idx_admin_audit_log_target ON admin_audit_log (target_type, target_id);
