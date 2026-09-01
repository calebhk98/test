-- 024_stats_comparisons.sql
--
-- Backs the user stats page's new peer-comparison section (product owner:
-- comparing only against a person's own past "feels bad" and the page
-- needs aggregates and distributions, never an identifiable person). Owned
-- entirely by the stats build; does not alter or drop anything from any
-- earlier migration, and no earlier migration is edited.
--
-- WHAT LIVES HERE, AND WHY IT IS A ROLLUP, NOT A LIVE QUERY: a comparison
-- like "most people answer around 40 questions" needs a median/quartile
-- over the WHOLE active population, and "how common is this interest tag
-- near you" needs a count over every user near a given point, for every
-- possible point. Computing either live, per page view, would mean
-- scanning a population that grows with the whole platform on every
-- request, which is exactly the anti-pattern stats_platform_daily and
-- friends (020_stats.sql) already avoid for the admin page. So, same
-- strategy: src/jobs/statsAggregation.job.ts writes these two tables on
-- its normal run, one bounded grouped query each, and the read path
-- (src/services/stats.service.ts) only ever does an indexed point lookup
-- by region key against a small table (one row per region, or one row per
-- region/tag pair) instead of a population scan.
--
-- GEOGRAPHIC BUCKETING: "region_key" is a coarse rectangular grid cell
-- (see REGION_GRID_DEGREES in statsAggregation.job.ts), not the precise
-- per-viewer haversine radius filter.service.ts uses for pool counts. A
-- rollup job aggregates across every user in one pass and cannot afford a
-- separate radius query per viewer; a fixed grid is the standard
-- "close enough, computed once" approach for this kind of offline
-- aggregate. The key is an internal join key only, never returned to a
-- client.
--
-- PRIVACY: both tables store only counts and statistical summaries
-- (median/quartiles), never a user id, tag owner, or any other
-- per-person value. The read path additionally applies the same
-- small-cohort suppression the rest of this build already uses
-- (MIN_SUPPRESSIBLE_COHORT, stats.service.ts) before a region's numbers
-- ever reach a response, so a thinly-populated region cannot be used to
-- infer one specific neighbor. stats_region_tag_prevalence only counts a
-- tag toward a region if its owner set the tag's visibility to 'public'
-- or 'private_reciprocal' -- a tag a user marked 'hidden' (never shown to
-- anyone, in any context) is excluded from this aggregate too, even
-- though only a count, never the tag holder's identity, would ever be
-- exposed.

-- =========================================================================
-- stats_region_activity -- one row per region, refreshed in full on every
-- rollup run (TRUNCATE + single grouped INSERT..SELECT, never a per-region
-- write loop, so the round trip count does not grow with the number of
-- regions).
-- =========================================================================
CREATE TABLE stats_region_activity (
  region_key                 text PRIMARY KEY,
  user_count                 integer NOT NULL DEFAULT 0,
  questions_answered_median  numeric,
  questions_answered_p25     numeric,
  questions_answered_p75     numeric,
  enabled_filters_median     numeric,
  enabled_filters_p25        numeric,
  enabled_filters_p75        numeric,
  computed_at                timestamptz NOT NULL DEFAULT now()
);

-- =========================================================================
-- stats_region_tag_prevalence -- one row per (region, interest tag) that
-- has at least one holder in that region; refreshed the same way as
-- stats_region_activity.
-- =========================================================================
CREATE TABLE stats_region_tag_prevalence (
  region_key   text NOT NULL,
  tag_id       uuid NOT NULL REFERENCES interest_tags (id) ON DELETE CASCADE,
  user_count   integer NOT NULL DEFAULT 0,
  computed_at  timestamptz NOT NULL DEFAULT now(),

  PRIMARY KEY (region_key, tag_id)
);

CREATE INDEX idx_stats_region_tag_prevalence_region ON stats_region_tag_prevalence (region_key);
