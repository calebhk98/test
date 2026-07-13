-- ============================================================================
-- QuestionAnswers.sql
-- One clearly-labelled query block per research question (Stage 1 / Step 3).
-- Run with:   \. QuestionAnswers.sql      (from inside mysql)
--        or:  mysql -t foodHygeine < QuestionAnswers.sql   (from the shell)
-- ============================================================================
USE foodHygeine;


-- ============================================================================
-- Q1. Do average hygiene ratings vary by REGION?
-- ============================================================================
SELECT r.region_name,
       COUNT(e.rating_numeric)                   AS rated_premises,
       ROUND(AVG(e.rating_numeric), 3)           AS avg_rating,
       ROUND(100 * AVG(e.rating_numeric = 5), 1) AS pct_rated_5,
       ROUND(AVG(e.hygiene_score), 2)            AS avg_hygiene_score
FROM establishment e
JOIN local_authority la ON e.la_code = la.la_code
JOIN region r           ON la.region_id = r.region_id
WHERE e.rating_numeric IS NOT NULL
GROUP BY r.region_name
ORDER BY avg_rating DESC;


-- ============================================================================
-- Q2. Which LOCAL AUTHORITIES score best / worst? (is score tied to place?)
--     Best first; change DESC -> ASC for the worst.
--     HAVING keeps only authorities with enough rated premises to be meaningful.
-- ============================================================================
SELECT la.name, r.region_name,
       COUNT(e.rating_numeric)         AS rated_premises,
       ROUND(AVG(e.rating_numeric), 3) AS avg_rating
FROM establishment e
JOIN local_authority la ON e.la_code = la.la_code
JOIN region r           ON la.region_id = r.region_id
WHERE e.rating_numeric IS NOT NULL
GROUP BY la.la_code
HAVING rated_premises >= 300
ORDER BY avg_rating DESC
LIMIT 10;


-- ============================================================================
-- Q3. Do more DEPRIVED areas have lower hygiene?
--     3a: average rating by deprivation quintile (1 = least, 5 = most deprived)
-- ============================================================================
WITH la_q AS (
    SELECT la.la_code,
           NTILE(5) OVER (ORDER BY imd.imd_avg_score ASC) AS quintile
    FROM local_authority la
    JOIN imd_lad imd ON la.lad_code = imd.lad_code
)
SELECT q.quintile,
       COUNT(e.rating_numeric)                   AS rated_premises,
       ROUND(AVG(e.rating_numeric), 3)           AS avg_rating,
       ROUND(100 * AVG(e.rating_numeric = 5), 1) AS pct_rated_5
FROM la_q q
JOIN establishment e ON e.la_code = q.la_code
WHERE e.rating_numeric IS NOT NULL
GROUP BY q.quintile
ORDER BY q.quintile;

-- 3b: one-number summary — Pearson correlation between an authority's deprivation
--     score and its mean rating (negative => more deprived areas score lower).
WITH s AS (
    SELECT imd.imd_avg_score AS x, AVG(e.rating_numeric) AS y
    FROM establishment e
    JOIN local_authority la ON e.la_code = la.la_code
    JOIN imd_lad imd        ON la.lad_code = imd.lad_code
    WHERE e.rating_numeric IS NOT NULL
    GROUP BY la.la_code, imd.imd_avg_score
)
SELECT COUNT(*) AS authorities,
       ROUND((COUNT(*) * SUM(x * y) - SUM(x) * SUM(y)) /
             (SQRT(COUNT(*) * SUM(x * x) - SUM(x) * SUM(x)) *
              SQRT(COUNT(*) * SUM(y * y) - SUM(y) * SUM(y))), 3) AS pearson_r
FROM s;


-- ============================================================================
-- Q4. Which BUSINESS TYPES score best / worst?
-- ============================================================================
SELECT bt.business_type_name,
       COUNT(e.rating_numeric)                   AS rated_premises,
       ROUND(AVG(e.rating_numeric), 3)           AS avg_rating,
       ROUND(100 * AVG(e.rating_numeric = 5), 1) AS pct_rated_5,
       ROUND(AVG(e.hygiene_score), 2)            AS avg_hygiene_score
FROM establishment e
JOIN business_type bt ON e.business_type_id = bt.business_type_id
WHERE e.rating_numeric IS NOT NULL
GROUP BY bt.business_type_id
HAVING rated_premises >= 1000
ORDER BY avg_rating DESC;


-- ============================================================================
-- Q5. How RECENT are inspections, and how many await a first one?
--     5a: how many premises are still awaiting their first inspection
-- ============================================================================
SELECT SUM(rating_date IS NULL)                 AS awaiting_inspection,
       ROUND(100 * AVG(rating_date IS NULL), 1) AS pct_awaiting
FROM establishment;

-- 5b: recency of the premises that HAVE been rated
SELECT ROUND(AVG(DATEDIFF(CURDATE(), rating_date) / 365.25), 2)                 AS avg_age_years,
       ROUND(100 * AVG(rating_date >= CURDATE() - INTERVAL 1 YEAR), 1)          AS pct_rated_last_year,
       ROUND(100 * AVG(rating_date <  CURDATE() - INTERVAL 3 YEAR), 1)          AS pct_older_than_3yr
FROM establishment
WHERE rating_date IS NOT NULL;
