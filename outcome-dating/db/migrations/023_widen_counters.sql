-- 023_widen_counters.sql
--
-- 8-billion-user capacity audit (docs/capacity.md), the schema-overflow
-- half. Owned entirely by this build; does not alter or drop anything
-- this build didn't add, and no earlier migration is edited.
--
-- METHOD: every `integer`/`smallint` column in every prior migration was
-- read (see docs/capacity.md's "hard limits" table for the full list with
-- file:line citations). A 32-bit `integer` overflows at 2,147,483,647.
-- Almost every one already found in this schema is bounded by something
-- OTHER than total user count (a 0-100 score, a 1-5 severity, a photo's
-- position among a handful of photos, a minute-of-day, a schema/question
-- "version" counter, an in-flight attempt count) and none of those grow
-- with population, see docs/capacity.md for why each is safe as-is.
-- Every column that genuinely IS a running total of money or a platform-
-- wide activity count (payment_ledger.amount_cents, payment_holds, venue
-- settlements, photo_experiments.impressions/interests_sent/accepted,
-- stats_platform_daily's per-day sums, refunds_count) was ALREADY
-- `bigint` in 001_init.sql/020_stats.sql, that convention predates this
-- build and did not need fixing.
--
-- The two widenings below are the only columns this audit found that (a)
-- are a COUNT correlated with total platform population and (b) were
-- still `integer`. Neither can plausibly overflow at 8B users under any
-- realistic operating pattern (see each comment for the actual math).
-- They are widened anyway because the fix is free (an `integer`-to-
-- `bigint` widening is a fast, in-place metadata change in Postgres, no
-- table rewrite) and "cannot plausibly overflow" is a weaker guarantee
-- than "cannot overflow", which is what a hard 8-billion-user bound
-- deserves for a population-correlated column.

-- stats_cohort_retention (020_stats.sql): one row per REGISTRATION DAY,
-- not per user. `cohort_size`/`active_d1`/`active_d7`/`active_d30` are
-- COUNT(*) of users who signed up on that single calendar day and are
-- still active N days later. At 8B total users spread over any realistic
-- signup history (even a compressed 1-year rollout is ~21.9M/day average,
-- three orders of magnitude below the ~2.147B/day it would take a SINGLE
-- day's cohort to overflow `integer`), this does not overflow in practice.
-- It is, however, a straightforward function of population, unlike this
-- file's other integer columns, so it gets the free fix.
ALTER TABLE stats_cohort_retention ALTER COLUMN cohort_size TYPE bigint;
ALTER TABLE stats_cohort_retention ALTER COLUMN active_d1 TYPE bigint;
ALTER TABLE stats_cohort_retention ALTER COLUMN active_d7 TYPE bigint;
ALTER TABLE stats_cohort_retention ALTER COLUMN active_d30 TYPE bigint;

-- stats_aggregation_runs.duration_ms (020_stats.sql): wall-clock runtime,
-- in milliseconds, of one nightly rollup job run. `integer` overflows at
-- ~24.8 days of milliseconds. docs/scale-and-sources.md §1.2.2 already
-- documents that the *compatibility* refresh job (a different job, not
-- this stats rollup) stops finishing inside its 24-HOUR window at only a
-- few thousand active users, nowhere near 24.8 days, but this column is
-- shared observability infrastructure for every job that reports through
-- it, present and future, and a duration overflow would silently wrap to
-- a small/negative-looking number rather than error, corrupting exactly
-- the observability signal that would otherwise show a job is failing to
-- keep up with growth. Free fix, same as above.
ALTER TABLE stats_aggregation_runs ALTER COLUMN duration_ms TYPE bigint;
