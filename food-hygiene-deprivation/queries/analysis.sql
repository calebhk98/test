-- =============================================================================
-- Analytical queries answering the project questions.
-- Run against database `food_hygiene`.
--
-- Rating conventions (important):
--   * rating_numeric : 0..5, where 5 = BEST. FHRS only (England/Wales/NI).
--   * hygiene_score  : 0 = best, higher = worse (component score). FHRS only.
--   * Scotland (FHIS) is pass/fail with no numeric rating, so the numeric
--     analyses below are implicitly FHRS-only (rating_numeric IS NOT NULL).
-- =============================================================================
USE food_hygiene;

-- -----------------------------------------------------------------------------
-- Q1. Which regions have better scores?
--   Average rating, % achieving the top score of 5, and average hygiene
--   component (lower = cleaner) per FSA region.
-- -----------------------------------------------------------------------------
SELECT r.region_name,
       COUNT(e.rating_numeric)                              AS rated_premises,
       ROUND(AVG(e.rating_numeric), 3)                      AS avg_rating,
       ROUND(100 * AVG(e.rating_numeric = 5), 1)            AS pct_rated_5,
       ROUND(100 * AVG(e.rating_numeric <= 1), 1)           AS pct_rated_0_1,
       ROUND(AVG(e.hygiene_score), 2)                       AS avg_hygiene_score
FROM establishment e
JOIN local_authority la ON e.la_code = la.la_code
JOIN region r           ON la.region_id = r.region_id
WHERE e.rating_numeric IS NOT NULL
GROUP BY r.region_name
ORDER BY avg_rating DESC;

-- -----------------------------------------------------------------------------
-- Q2. Is score correlated with location? Best & worst local authorities
--   (min 500 rated premises to avoid tiny-sample noise).
-- -----------------------------------------------------------------------------
( SELECT 'BEST 10'  AS bucket, la.name, r.region_name,
         COUNT(e.rating_numeric) AS rated, ROUND(AVG(e.rating_numeric),3) AS avg_rating
  FROM establishment e JOIN local_authority la ON e.la_code=la.la_code
       JOIN region r ON la.region_id=r.region_id
  WHERE e.rating_numeric IS NOT NULL
  GROUP BY la.la_code HAVING rated >= 500 ORDER BY avg_rating DESC LIMIT 10 )
UNION ALL
( SELECT 'WORST 10', la.name, r.region_name,
         COUNT(e.rating_numeric), ROUND(AVG(e.rating_numeric),3)
  FROM establishment e JOIN local_authority la ON e.la_code=la.la_code
       JOIN region r ON la.region_id=r.region_id
  WHERE e.rating_numeric IS NOT NULL
  GROUP BY la.la_code HAVING COUNT(e.rating_numeric) >= 500
  ORDER BY AVG(e.rating_numeric) ASC LIMIT 10 );

-- -----------------------------------------------------------------------------
-- Q3a. Do poorer locations have lower hygiene?
--   Pearson correlation between local-authority deprivation (IMD average
--   score; higher = more deprived) and the LA's average food-hygiene rating.
--   Computed across all English LAs that matched a deprivation district.
--   Negative r => more deprived areas tend to have LOWER ratings.
-- -----------------------------------------------------------------------------
WITH la_stats AS (
  SELECT la.la_code,
         imd.imd_avg_score                 AS x,   -- deprivation
         AVG(e.rating_numeric)             AS y    -- mean rating
  FROM establishment e
  JOIN local_authority la ON e.la_code = la.la_code
  JOIN imd_lad imd        ON la.lad_code = imd.lad_code
  WHERE e.rating_numeric IS NOT NULL
  GROUP BY la.la_code, imd.imd_avg_score
)
SELECT COUNT(*) AS n_local_authorities,
       ROUND( (COUNT(*)*SUM(x*y) - SUM(x)*SUM(y)) /
              ( SQRT(COUNT(*)*SUM(x*x) - SUM(x)*SUM(x)) *
                SQRT(COUNT(*)*SUM(y*y) - SUM(y)*SUM(y)) ), 3) AS pearson_r
FROM la_stats;

-- -----------------------------------------------------------------------------
-- Q3b. Same question, bucketed: split English LAs into deprivation quintiles
--   (Q1 = least deprived ... Q5 = most deprived) and show the establishment-
--   weighted average rating in each.
-- -----------------------------------------------------------------------------
WITH la_q AS (
  SELECT la.la_code,
         NTILE(5) OVER (ORDER BY imd.imd_avg_score ASC) AS deprivation_quintile
  FROM local_authority la
  JOIN imd_lad imd ON la.lad_code = imd.lad_code
)
SELECT q.deprivation_quintile,                       -- 1 = least deprived, 5 = most
       CASE q.deprivation_quintile WHEN 1 THEN 'least deprived'
            WHEN 5 THEN 'most deprived' ELSE '' END  AS label,
       COUNT(e.rating_numeric)                       AS rated_premises,
       ROUND(AVG(e.rating_numeric), 3)               AS avg_rating,
       ROUND(100 * AVG(e.rating_numeric = 5), 1)     AS pct_rated_5,
       ROUND(AVG(e.hygiene_score), 2)                AS avg_hygiene_score
FROM la_q q
JOIN establishment e ON e.la_code = q.la_code
WHERE e.rating_numeric IS NOT NULL
GROUP BY q.deprivation_quintile
ORDER BY q.deprivation_quintile;

-- -----------------------------------------------------------------------------
-- Q4. What type of places have better / worse hygiene?
-- -----------------------------------------------------------------------------
SELECT bt.business_type_name,
       COUNT(e.rating_numeric)                    AS rated_premises,
       ROUND(AVG(e.rating_numeric), 3)            AS avg_rating,
       ROUND(100 * AVG(e.rating_numeric = 5), 1)  AS pct_rated_5,
       ROUND(AVG(e.hygiene_score), 2)             AS avg_hygiene_score
FROM establishment e
JOIN business_type bt ON e.business_type_id = bt.business_type_id
WHERE e.rating_numeric IS NOT NULL
GROUP BY bt.business_type_id
HAVING rated_premises >= 1000
ORDER BY avg_rating DESC;

-- -----------------------------------------------------------------------------
-- Q5. How recent / how frequent are inspections?
--   Age of the current rating, and the share still awaiting a first inspection.
-- -----------------------------------------------------------------------------
SELECT
  COUNT(*)                                                         AS total_premises,
  SUM(rating_date IS NULL)                                         AS awaiting_inspection,
  ROUND(100*AVG(rating_date IS NULL), 1)                           AS pct_awaiting,
  ROUND(AVG(DATEDIFF(CURDATE(), rating_date))/365.25, 2)           AS avg_rating_age_years,
  ROUND(MAX(DATEDIFF(CURDATE(), rating_date))/365.25, 1)           AS oldest_rating_years,
  ROUND(100*AVG(DATEDIFF(CURDATE(), rating_date) <= 365), 1)       AS pct_inspected_last_1y,
  ROUND(100*AVG(DATEDIFF(CURDATE(), rating_date) > 365*3), 1)      AS pct_older_than_3y
FROM establishment;

-- Inspection age banded by region (are some regions more up to date?)
SELECT r.region_name,
       ROUND(AVG(DATEDIFF(CURDATE(), e.rating_date))/365.25, 2) AS avg_age_years,
       ROUND(100*AVG(e.rating_date IS NULL), 1)                 AS pct_awaiting
FROM establishment e
JOIN local_authority la ON e.la_code = la.la_code
JOIN region r           ON la.region_id = r.region_id
GROUP BY r.region_name
ORDER BY avg_age_years ASC;
