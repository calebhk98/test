// Simple read-only web application over the food_hygiene database.
// Connects with the SELECT-only `fhrs_app` account (see db/users.sql) so the
// web tier can never modify data — appropriate least privilege for a query app.
const express = require('express');
const mysql = require('mysql2/promise');
const path = require('path');
const cfg = require('../config');

const app = express();
const PORT = process.env.PORT || 3000;

const pool = mysql.createPool({
  host: cfg.db.host, port: cfg.db.port, database: cfg.db.database,
  user: cfg.app.user, password: cfg.app.password,
  connectionLimit: 5, namedPlaceholders: true,
});

// Tiny helper: run a query and return rows, or surface a 500.
const handler = (fn) => async (req, res) => {
  try { res.json(await fn(req)); }
  catch (e) { console.error(e); res.status(500).json({ error: e.message }); }
};
const q = async (sql, params = {}) => (await pool.query(sql, params))[0];

app.use(express.static(path.join(__dirname, 'public')));

// Headline counts.
app.get('/api/stats', handler(async () => (await q(`
  SELECT
    (SELECT COUNT(*) FROM establishment)                       AS establishments,
    (SELECT COUNT(*) FROM local_authority)                     AS local_authorities,
    (SELECT COUNT(*) FROM region)                              AS regions,
    (SELECT COUNT(*) FROM establishment WHERE rating_date IS NULL) AS awaiting_inspection,
    (SELECT ROUND(AVG(rating_numeric),3) FROM establishment)  AS avg_rating
`))[0]));

// Q1: ratings by region.
app.get('/api/regions', handler(() => q(`
  SELECT r.region_name,
         COUNT(e.rating_numeric)                   AS rated_premises,
         ROUND(AVG(e.rating_numeric),3)            AS avg_rating,
         ROUND(100*AVG(e.rating_numeric=5),1)      AS pct_rated_5,
         ROUND(AVG(e.hygiene_score),2)             AS avg_hygiene_score
  FROM establishment e
  JOIN local_authority la ON e.la_code=la.la_code
  JOIN region r           ON la.region_id=r.region_id
  WHERE e.rating_numeric IS NOT NULL
  GROUP BY r.region_name ORDER BY avg_rating DESC`)));

// Q4: ratings by business type.
app.get('/api/business-types', handler(() => q(`
  SELECT bt.business_type_name,
         COUNT(e.rating_numeric)              AS rated_premises,
         ROUND(AVG(e.rating_numeric),3)       AS avg_rating,
         ROUND(100*AVG(e.rating_numeric=5),1) AS pct_rated_5,
         ROUND(AVG(e.hygiene_score),2)        AS avg_hygiene_score
  FROM establishment e
  JOIN business_type bt ON e.business_type_id=bt.business_type_id
  WHERE e.rating_numeric IS NOT NULL
  GROUP BY bt.business_type_id HAVING rated_premises>=1000
  ORDER BY avg_rating DESC`)));

// Q3: deprivation quintiles + the headline correlation.
app.get('/api/deprivation', handler(async () => {
  const buckets = await q(`
    WITH la_q AS (
      SELECT la.la_code,
             NTILE(5) OVER (ORDER BY imd.imd_avg_score ASC) AS quintile
      FROM local_authority la JOIN imd_lad imd ON la.lad_code=imd.lad_code)
    SELECT q.quintile,
           COUNT(e.rating_numeric)              AS rated_premises,
           ROUND(AVG(e.rating_numeric),3)       AS avg_rating,
           ROUND(100*AVG(e.rating_numeric=5),1) AS pct_rated_5
    FROM la_q q JOIN establishment e ON e.la_code=q.la_code
    WHERE e.rating_numeric IS NOT NULL
    GROUP BY q.quintile ORDER BY q.quintile`);
  const corr = (await q(`
    WITH s AS (SELECT imd.imd_avg_score x, AVG(e.rating_numeric) y
      FROM establishment e
      JOIN local_authority la ON e.la_code=la.la_code
      JOIN imd_lad imd ON la.lad_code=imd.lad_code
      WHERE e.rating_numeric IS NOT NULL
      GROUP BY la.la_code, imd.imd_avg_score)
    SELECT COUNT(*) n,
      ROUND((COUNT(*)*SUM(x*y)-SUM(x)*SUM(y))/
        (SQRT(COUNT(*)*SUM(x*x)-SUM(x)*SUM(x))*SQRT(COUNT(*)*SUM(y*y)-SUM(y)*SUM(y))),3) pearson_r
    FROM s`))[0];
  return { buckets, correlation: corr };
}));

// Q2: local-authority leaderboard (optionally filtered by region).
app.get('/api/authorities', handler((req) => {
  const order = req.query.sort === 'worst' ? 'ASC' : 'DESC';
  return q(`
    SELECT la.name, r.region_name,
           COUNT(e.rating_numeric)        AS rated_premises,
           ROUND(AVG(e.rating_numeric),3) AS avg_rating,
           imd.imd_avg_score              AS deprivation_score
    FROM establishment e
    JOIN local_authority la ON e.la_code=la.la_code
    JOIN region r           ON la.region_id=r.region_id
    LEFT JOIN imd_lad imd    ON la.lad_code=imd.lad_code
    WHERE e.rating_numeric IS NOT NULL
      AND (:region = '' OR r.region_name = :region)
    GROUP BY la.la_code HAVING rated_premises >= 300
    ORDER BY avg_rating ${order} LIMIT 15`,
    { region: req.query.region || '' });
}));

// Establishment search by name and/or postcode prefix.
app.get('/api/search', handler((req) => q(`
  SELECT e.business_name, bt.business_type_name, e.post_code,
         e.rating_value, e.rating_date, la.name AS local_authority
  FROM establishment e
  JOIN local_authority la   ON e.la_code=la.la_code
  LEFT JOIN business_type bt ON e.business_type_id=bt.business_type_id
  WHERE (:name = '' OR e.business_name LIKE CONCAT('%', :name, '%'))
    AND (:pc   = '' OR e.post_code   LIKE CONCAT(:pc, '%'))
  ORDER BY e.business_name LIMIT 50`,
  { name: req.query.name || '', pc: (req.query.postcode || '').toUpperCase() })));

app.listen(PORT, () => console.log(`Food-hygiene web app on http://localhost:${PORT}`));
