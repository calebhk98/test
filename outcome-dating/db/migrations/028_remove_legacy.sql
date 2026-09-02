-- 028_remove_legacy.sql
--
-- This is a prototype. Nothing has shipped, there are no external
-- consumers, and the project owner's instruction is unambiguous: no
-- backward compatibility anywhere. This migration removes the two
-- concrete pieces of schema that only existed to keep an old
-- representation alive alongside a newer one, and extends the stats
-- region rollup with the peer-comparison metrics the product owner asked
-- to have unlocked (see src/services/stats.service.ts's module doc for
-- the argument: a comparison visible only to the person themselves does
-- not create the status dynamics a public or ranked signal would).

-- =========================================================================
-- 1. post_date_feedback: drop the old `positive` boolean and the
--    `positive`/`outcome` agreement constraint that only existed to keep
--    it from disagreeing with `outcome`.
-- =========================================================================
--
-- `positive` (016_post_date_feedback.sql) was the pre-outcome, two-value
-- feedback axis. `db/migrations/025_integrity.sql` kept it around and
-- added `post_date_feedback_positive_outcome_agree` specifically because,
-- at the time, `src/services/stats.service.ts` and
-- `src/jobs/statsAggregation.job.ts` (both owned by this build) still
-- read `positive` directly as a fallback for historical rows that
-- predated `outcome`. Both of those call sites are rewritten in this same
-- build to read `outcome` only (`getMyDateOutcomes` in stats.service.ts,
-- `FEEDBACK_SQL` in statsAggregation.job.ts), so that reason is gone: the
-- historical backfill 025 already performed (every legacy-only row got an
-- equivalent `outcome` value written) means every row already has the
-- outcome-based truth this table now reads exclusively. There is nothing
-- left in the codebase that reads `positive`, so the column, and the
-- constraint that only existed to protect it from disagreeing with
-- `outcome`, are both dropped outright rather than kept "just in case."
--
-- `safety_concern` (001_init.sql) is the same shape of leftover: it was
-- the boolean safety flag the old, now-deleted
-- `dateProposal.service#submitPostDateFeedback` writer used, superseded
-- by the richer `safety_flag`/`safety_details` pair
-- `postDateFeedback.service.ts#submitCheckIn` writes today. Nothing in
-- this codebase has written to `safety_concern` since that old writer was
-- removed (the HTTP-level translator that briefly stood in for it,
-- `POST /date-proposals/:id/feedback`, mapped its own request field onto
-- `safety_flag`, never onto this column), and nothing reads it. Dropped
-- for the same reason as `positive`.

ALTER TABLE post_date_feedback DROP CONSTRAINT post_date_feedback_positive_outcome_agree;
ALTER TABLE post_date_feedback DROP COLUMN positive;
ALTER TABLE post_date_feedback DROP COLUMN safety_concern;

-- =========================================================================
-- 2. stats_region_activity: five new peer-comparison metrics.
-- =========================================================================
--
-- Extends the rollup 024_stats_comparisons.sql created with the metrics
-- that page's original design withheld as "how others respond to you"
-- (sent-interest acceptance, received-interest conversion and volume,
-- profile views, photo performance). The product owner overruled that:
-- a metric visible only to the person asking about themselves cannot
-- create a public ranking or status dynamic, because nobody else ever
-- sees it and it has no effect on who matches with whom. See
-- src/services/stats.service.ts's module doc for the full argument, and
-- src/jobs/statsAggregation.job.ts#aggregateRegionActivity for how each
-- column below is computed.
--
-- Three of the five (a rate with a genuinely undefined denominator for a
-- user with no relevant history yet) additionally get a `..._sample_size`
-- column: the count of users in the region who actually contributed a
-- value to that particular percentile, separate from the region's total
-- population (`user_count`). The read path suppresses a comparison whose
-- sample size is too small to be anonymous even when the region's overall
-- population is not, the same small-cohort protection this build applies
-- everywhere else, kept because it protects OTHER people from being
-- individually identifiable in a "typical" figure, not because it
-- protects the viewer from their own numbers.

ALTER TABLE stats_region_activity
  ADD COLUMN sent_interest_acceptance_median numeric,
  ADD COLUMN sent_interest_acceptance_p25 numeric,
  ADD COLUMN sent_interest_acceptance_p75 numeric,
  ADD COLUMN sent_interest_acceptance_sample_size integer NOT NULL DEFAULT 0,
  ADD COLUMN received_interest_conversion_median numeric,
  ADD COLUMN received_interest_conversion_p25 numeric,
  ADD COLUMN received_interest_conversion_p75 numeric,
  ADD COLUMN received_interest_conversion_sample_size integer NOT NULL DEFAULT 0,
  ADD COLUMN received_interest_volume_median numeric,
  ADD COLUMN received_interest_volume_p25 numeric,
  ADD COLUMN received_interest_volume_p75 numeric,
  ADD COLUMN profile_views_median numeric,
  ADD COLUMN profile_views_p25 numeric,
  ADD COLUMN profile_views_p75 numeric,
  ADD COLUMN photo_performance_median numeric,
  ADD COLUMN photo_performance_p25 numeric,
  ADD COLUMN photo_performance_p75 numeric,
  ADD COLUMN photo_performance_sample_size integer NOT NULL DEFAULT 0;

-- =========================================================================
-- 3. Known conflicts this migration creates, out of this build's
--    ownership to fix (see the build's own report for the full list of
--    everything searched and removed).
-- =========================================================================
--
-- Dropping `post_date_feedback.positive` breaks two fixtures/tests this
-- build does not own and may not edit:
--
--   - tests/jobs/matchingSignalSweep.test.ts's `insertGoodDateHistory`
--     helper (around line 45) does
--     `INSERT INTO post_date_feedback (date_proposal_id, user_id,
--     positive, outcome) VALUES ($1, $2, true, 'happened_good')`,
--     an explicit value for a column that no longer exists. Fix: drop
--     `positive` (and its value) from that INSERT, `outcome` alone is
--     already sufficient, the row does not need both.
--   - tests/http/happyPath.test.ts submits
--     `POST /date-proposals/:id/feedback` with `{ positive: true,
--     wouldMeetAgain: true }` twice (around line 143), the route this
--     migration's application-layer change removes entirely. Fix: replace
--     both calls with `POST /date-proposals/:id/check-in` and
--     `{ outcome: 'happened_good', wouldMeetAgain: 'yes' }`, the direct
--     equivalent under the one remaining endpoint.
--
-- Both are one-line fixes in files outside this build's file list
-- (tests/jobs/**, tests/http/happyPath.test.ts), reported here rather
-- than edited, the same convention db/migrations/025_integrity.sql
-- already established for a conflict of this shape.
