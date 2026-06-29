-- =============================================================================
-- Neighbourhood-level (LSOA) deprivation analysis.
-- Requires db/schema_geo.sql + etl/03_load_geo.js.
--
-- THE JOIN (recorded so anyone can reproduce):
--   establishment e
--     JOIN postcode  p ON e.postcode_norm = p.postcode_norm   -- premise -> postcode
--     JOIN imd_lsoa  l ON p.lsoa11cd      = l.lsoa11cd         -- postcode -> neighbourhood
-- This replaces the coarse LA-average deprivation with the deprivation of the
-- ~1,500-person neighbourhood each premise actually sits in.
-- =============================================================================
USE food_hygiene;

-- -----------------------------------------------------------------------------
-- Q0. Coverage: how much of the data survives the bridge? (honesty check)
-- -----------------------------------------------------------------------------
SELECT
  (SELECT COUNT(*) FROM establishment)                                   AS establishments,
  (SELECT COUNT(*) FROM establishment e JOIN postcode p
        ON e.postcode_norm=p.postcode_norm)                             AS got_a_postcode_match,
  (SELECT COUNT(*) FROM establishment e JOIN postcode p
        ON e.postcode_norm=p.postcode_norm
        JOIN imd_lsoa l ON p.lsoa11cd=l.lsoa11cd
      WHERE e.rating_numeric IS NOT NULL)                               AS rated_with_lsoa_deprivation;

-- -----------------------------------------------------------------------------
-- Q1. Hygiene by neighbourhood deprivation DECILE (1 = most deprived 10%).
--   Finer than the LA quintiles in queries/analysis.sql.
-- -----------------------------------------------------------------------------
SELECT l.imd_decile,
       COUNT(*)                                  AS rated_premises,
       ROUND(AVG(e.rating_numeric),3)            AS avg_rating,
       ROUND(100*AVG(e.rating_numeric=5),1)      AS pct_rated_5,
       ROUND(AVG(e.hygiene_score),2)             AS avg_hygiene_score
FROM establishment e
JOIN postcode p ON e.postcode_norm = p.postcode_norm
JOIN imd_lsoa l ON p.lsoa11cd = l.lsoa11cd
WHERE e.rating_numeric IS NOT NULL AND l.imd_decile IS NOT NULL
GROUP BY l.imd_decile
ORDER BY l.imd_decile;

-- -----------------------------------------------------------------------------
-- Q2. WHICH DOMAIN of deprivation tracks hygiene most? Pearson r between each
--   neighbourhood deprivation score and the premise rating, in one pass.
--   (Negative r => more deprived neighbourhoods score lower.)
-- -----------------------------------------------------------------------------
WITH j AS (
  SELECT e.rating_numeric AS y,
         l.imd_score, l.income_score, l.employment_score, l.education_score,
         l.health_score, l.crime_score, l.barriers_score, l.living_score
  FROM establishment e
  JOIN postcode p ON e.postcode_norm = p.postcode_norm
  JOIN imd_lsoa l ON p.lsoa11cd = l.lsoa11cd
  WHERE e.rating_numeric IS NOT NULL
), n AS (SELECT COUNT(*) c FROM j)
SELECT 'IMD (overall)'    AS domain, ROUND((n.c*SUM(imd_score*y)-SUM(imd_score)*SUM(y))/(SQRT(n.c*SUM(imd_score*imd_score)-POW(SUM(imd_score),2))*SQRT(n.c*SUM(y*y)-POW(SUM(y),2))),3) AS pearson_r FROM j,n GROUP BY n.c
UNION ALL SELECT 'Income',        ROUND((n.c*SUM(income_score*y)-SUM(income_score)*SUM(y))/(SQRT(n.c*SUM(income_score*income_score)-POW(SUM(income_score),2))*SQRT(n.c*SUM(y*y)-POW(SUM(y),2))),3) FROM j,n GROUP BY n.c
UNION ALL SELECT 'Employment',    ROUND((n.c*SUM(employment_score*y)-SUM(employment_score)*SUM(y))/(SQRT(n.c*SUM(employment_score*employment_score)-POW(SUM(employment_score),2))*SQRT(n.c*SUM(y*y)-POW(SUM(y),2))),3) FROM j,n GROUP BY n.c
UNION ALL SELECT 'Education',     ROUND((n.c*SUM(education_score*y)-SUM(education_score)*SUM(y))/(SQRT(n.c*SUM(education_score*education_score)-POW(SUM(education_score),2))*SQRT(n.c*SUM(y*y)-POW(SUM(y),2))),3) FROM j,n GROUP BY n.c
UNION ALL SELECT 'Health',        ROUND((n.c*SUM(health_score*y)-SUM(health_score)*SUM(y))/(SQRT(n.c*SUM(health_score*health_score)-POW(SUM(health_score),2))*SQRT(n.c*SUM(y*y)-POW(SUM(y),2))),3) FROM j,n GROUP BY n.c
UNION ALL SELECT 'Crime',         ROUND((n.c*SUM(crime_score*y)-SUM(crime_score)*SUM(y))/(SQRT(n.c*SUM(crime_score*crime_score)-POW(SUM(crime_score),2))*SQRT(n.c*SUM(y*y)-POW(SUM(y),2))),3) FROM j,n GROUP BY n.c
UNION ALL SELECT 'Barriers',      ROUND((n.c*SUM(barriers_score*y)-SUM(barriers_score)*SUM(y))/(SQRT(n.c*SUM(barriers_score*barriers_score)-POW(SUM(barriers_score),2))*SQRT(n.c*SUM(y*y)-POW(SUM(y),2))),3) FROM j,n GROUP BY n.c
UNION ALL SELECT 'Living env.',   ROUND((n.c*SUM(living_score*y)-SUM(living_score)*SUM(y))/(SQRT(n.c*SUM(living_score*living_score)-POW(SUM(living_score),2))*SQRT(n.c*SUM(y*y)-POW(SUM(y),2))),3) FROM j,n GROUP BY n.c;

-- -----------------------------------------------------------------------------
-- Q3. Premises per 1,000 residents, by deprivation decile (uses LSOA population).
--   Are deprived neighbourhoods saturated with more food outlets?
-- -----------------------------------------------------------------------------
-- Premises are counted per LSOA first (one row per neighbourhood) so the
-- population is never multiplied by the premise join.
SELECT l.imd_decile,
       SUM(COALESCE(pc.premises,0))                                       AS premises,
       SUM(l.total_population)                                            AS population,
       ROUND(1000*SUM(COALESCE(pc.premises,0))/NULLIF(SUM(l.total_population),0),2) AS premises_per_1000
FROM imd_lsoa l
LEFT JOIN (
  SELECT p.lsoa11cd, COUNT(*) AS premises
  FROM establishment e JOIN postcode p ON e.postcode_norm = p.postcode_norm
  GROUP BY p.lsoa11cd
) pc ON pc.lsoa11cd = l.lsoa11cd
WHERE l.imd_decile IS NOT NULL
GROUP BY l.imd_decile
ORDER BY l.imd_decile;
