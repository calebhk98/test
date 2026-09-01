-- 013_safety_fixes.sql
--
-- Risk-review remediation build (docs/risk-review.md) — SAF-1, SAF-6,
-- SAF-2, PRIV-1. Owned entirely by this build; does not alter or drop
-- anything from any earlier migration, and no earlier migration is
-- edited. Two schema additions, both additive/nullable so every existing
-- row (and every sibling build's in-flight migration) is unaffected:
--
--   1. profiles.distance_precision_floor_km  — SAF-2: an optional
--      per-user floor on how coarse OTHER users' view of this profile's
--      distance must be (see src/domain/units/distance.ts and
--      src/services/profile.service.ts's UpdateProfileInput doc).
--
--   2. reports.outcome / outcome_recorded_at — SAF-1: whether a report
--      was later confirmed or found unfounded. Used two ways:
--        - report.service.ts's reporter-credibility scoring excludes/
--          discounts reporters with a history of unfounded reports (the
--          "previously-abusive reporter" the brief calls out by name) —
--          see report.service.ts#reporterCredibility.
--        - report.service.ts#recordReportOutcome is the mechanism for
--          "false reports in this category carry consequences for the
--          reporter" (a negative trust event on the reporter when a
--          minor_suspected report they filed is marked unfounded).
--      Defaults to 'pending' so every existing report row stays exactly
--      as neutral as it was before this migration (no retroactive
--      penalty/credit is implied for reports filed before this build).

ALTER TABLE profiles
  ADD COLUMN distance_precision_floor_km integer
    CHECK (distance_precision_floor_km IS NULL OR distance_precision_floor_km BETWEEN 1 AND 500);

ALTER TABLE reports
  ADD COLUMN outcome text NOT NULL DEFAULT 'pending'
    CHECK (outcome IN ('pending', 'confirmed', 'unfounded')),
  ADD COLUMN outcome_recorded_at timestamptz;

-- Used by report.service.ts#reporterCredibility to count a reporter's
-- own history of unfounded reports quickly (small table, but this keeps
-- the query an index scan rather than a sequential one as report volume
-- grows).
CREATE INDEX idx_reports_reporter_outcome ON reports (reporter_id, outcome);
