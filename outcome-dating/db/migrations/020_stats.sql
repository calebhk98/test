-- 020_stats.sql
--
-- Stats pages (product owner: "a stats page, 1 for admins and 1 for
-- users... should allow tons of data"). Owned entirely by the stats
-- build; does not alter or drop anything from any earlier migration, and
-- no earlier migration is edited.
--
-- PERFORMANCE STRATEGY (see src/jobs/statsAggregation.job.ts for the full
-- writeup): both pages read from small, pre-aggregated rollup tables
-- (below) rather than scanning raw event tables at request time. The
-- rollup tables are populated by a background job that re-aggregates a
-- bounded trailing time window on every run (default 35 days for the
-- daily platform rollup, 60 days for retention cohorts), using ONE
-- indexed, grouped query per source table/metric per run, never a
-- per-day loop and never an unbounded full-history scan. The indexes
-- added below are exactly what makes each of those grouped queries a
-- bounded index-range scan instead of a sequential scan.
--
-- Everything in this file is either (a) a new index on an existing table
-- (purely additive, never touches existing data or constraints), or (b) a
-- brand-new table this build owns outright.

-- =========================================================================
-- Supporting indexes for bounded day-range rollup queries.
-- =========================================================================

CREATE INDEX IF NOT EXISTS idx_users_created_at ON users (created_at);
-- Cheap, index-only "current total" gauges (count of matching rows via a
-- partial index, not a sequential scan of the whole table), see
-- adminStats.service.ts's currentGaugeCounts.
CREATE INDEX IF NOT EXISTS idx_users_email_verified_partial ON users (id) WHERE email_verified_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_email_verified_at_range ON users (email_verified_at) WHERE email_verified_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_shadowbanned_partial ON users (id) WHERE shadowbanned = true;
CREATE INDEX IF NOT EXISTS idx_profiles_completeness_complete ON profiles (user_id) WHERE profile_completeness >= 100;
CREATE INDEX IF NOT EXISTS idx_profiles_updated_at_complete ON profiles (updated_at) WHERE profile_completeness >= 100;

CREATE INDEX IF NOT EXISTS idx_discovery_events_created_at ON discovery_events (created_at);

CREATE INDEX IF NOT EXISTS idx_interests_created_at ON interests (created_at);
CREATE INDEX IF NOT EXISTS idx_interests_accepted_at ON interests (accepted_at) WHERE accepted_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_interests_declined_at ON interests (declined_at) WHERE declined_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_interests_expired_at ON interests (expired_at) WHERE expired_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations (created_at);

CREATE INDEX IF NOT EXISTS idx_date_proposals_created_at ON date_proposals (created_at);
CREATE INDEX IF NOT EXISTS idx_date_proposals_accepted_at ON date_proposals (accepted_at) WHERE accepted_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_date_proposals_completed_at ON date_proposals (completed_at) WHERE completed_at IS NOT NULL;
-- `scheduled_end` is the bucketing key for statuses with no dedicated
-- transition-timestamp column (no_show, disputed, refunded, see the job
-- file for why) and for the repeat-date-rate gauge.
CREATE INDEX IF NOT EXISTS idx_date_proposals_scheduled_end ON date_proposals (scheduled_end);
CREATE INDEX IF NOT EXISTS idx_date_proposals_status_scheduled_end ON date_proposals (status, scheduled_end);

CREATE INDEX IF NOT EXISTS idx_venue_redemptions_created_at ON venue_redemptions (created_at);

CREATE INDEX IF NOT EXISTS idx_payment_ledger_created_at_type ON payment_ledger (created_at, type);

CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports (created_at);
CREATE INDEX IF NOT EXISTS idx_blocks_created_at ON blocks (created_at);
CREATE INDEX IF NOT EXISTS idx_moderation_actions_created_at ON moderation_actions (created_at);
CREATE INDEX IF NOT EXISTS idx_post_date_feedback_created_at ON post_date_feedback (created_at);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages (created_at);

-- =========================================================================
-- stats_platform_daily, one row per calendar day (UTC), admin stats page.
-- Every column is a COUNT (or cents sum) of events whose own timestamp
-- fell on that day. Rows in the trailing rollup window are fully
-- overwritten (UPSERT) on every job run; older rows are frozen (never
-- re-touched) once every source status transition for that day has had
-- time to settle.
-- =========================================================================
CREATE TABLE stats_platform_daily (
  day                     date PRIMARY KEY,
  registrations           bigint NOT NULL DEFAULT 0,
  verified_emails         bigint NOT NULL DEFAULT 0,
  profiles_completed      bigint NOT NULL DEFAULT 0,
  discovery_impressions   bigint NOT NULL DEFAULT 0,
  interests_sent          bigint NOT NULL DEFAULT 0,
  interests_accepted      bigint NOT NULL DEFAULT 0,
  interests_declined      bigint NOT NULL DEFAULT 0,
  interests_expired       bigint NOT NULL DEFAULT 0,
  conversations_opened    bigint NOT NULL DEFAULT 0,
  date_proposals_sent     bigint NOT NULL DEFAULT 0,
  date_proposals_accepted bigint NOT NULL DEFAULT 0,
  dates_completed         bigint NOT NULL DEFAULT 0,
  dates_no_show           bigint NOT NULL DEFAULT 0,
  dates_disputed          bigint NOT NULL DEFAULT 0,
  voucher_redemptions     bigint NOT NULL DEFAULT 0,
  reports                 bigint NOT NULL DEFAULT 0,
  blocks                  bigint NOT NULL DEFAULT 0,
  shadowban_actions       bigint NOT NULL DEFAULT 0,
  positive_feedback       bigint NOT NULL DEFAULT 0,
  negative_feedback       bigint NOT NULL DEFAULT 0,
  messages_sent           bigint NOT NULL DEFAULT 0,
  authorizations_cents    bigint NOT NULL DEFAULT 0,
  captures_cents          bigint NOT NULL DEFAULT 0,
  refunds_cents           bigint NOT NULL DEFAULT 0,
  refunds_count           bigint NOT NULL DEFAULT 0,
  releases_cents          bigint NOT NULL DEFAULT 0,
  updated_at              timestamptz NOT NULL DEFAULT now()
);

-- =========================================================================
-- stats_cohort_retention, one row per registration-day cohort. Retention
-- is measured against `users.last_active_at` (the only activity signal
-- available at the point this was built without adding a new activity-log
-- table to a file outside this build's ownership boundary), an honest
-- proxy ("was this user still active at least N days into their tenure"),
-- documented as such rather than presented as a precise daily-active
-- measurement. See the job file for the exact query.
-- =========================================================================
CREATE TABLE stats_cohort_retention (
  cohort_date   date PRIMARY KEY,
  cohort_size   integer NOT NULL DEFAULT 0,
  active_d1     integer NOT NULL DEFAULT 0,
  active_d7     integer NOT NULL DEFAULT 0,
  active_d30    integer NOT NULL DEFAULT 0,
  computed_at   timestamptz NOT NULL DEFAULT now()
);

-- =========================================================================
-- stats_platform_gauges, small key/value table for running metrics that
-- are not naturally day-bucketed sums (e.g. repeat-date rate, which needs
-- a per-user distinct-count across a window, not a per-day count).
-- =========================================================================
CREATE TABLE stats_platform_gauges (
  key           text PRIMARY KEY,
  value_numeric double precision NOT NULL,
  computed_at   timestamptz NOT NULL DEFAULT now()
);

-- =========================================================================
-- stats_aggregation_runs, freshness/observability log for the rollup job.
-- The admin stats page surfaces the most recent row so "as of" staleness
-- is always honestly visible rather than implied to be live.
-- =========================================================================
CREATE TABLE stats_aggregation_runs (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  run_at            timestamptz NOT NULL DEFAULT now(),
  window_start_day  date NOT NULL,
  window_end_day    date NOT NULL,
  days_upserted     integer NOT NULL DEFAULT 0,
  duration_ms       integer NOT NULL DEFAULT 0
);

CREATE INDEX idx_stats_aggregation_runs_run_at ON stats_aggregation_runs (run_at DESC);

-- =========================================================================
-- stats_user_cache, cache-aside store for the more expensive parts of the
-- USER stats page (currently: per-filter "what would widening this cost
-- me" pool estimates, which require several bounded-but-nontrivial
-- discovery-pool evaluations). Computed lazily on first request per user,
-- reused until stale. Never holds anything about a SECOND identifiable
-- user, every cached payload is scoped to (and only ever read back for)
-- the one user_id it belongs to.
-- =========================================================================
CREATE TABLE stats_user_cache (
  user_id       uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  cache_key     text NOT NULL,
  computed_at   timestamptz NOT NULL DEFAULT now(),
  payload       jsonb NOT NULL,

  PRIMARY KEY (user_id, cache_key)
);
