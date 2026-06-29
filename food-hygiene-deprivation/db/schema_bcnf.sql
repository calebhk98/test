-- =============================================================================
-- BCNF / 4NF refinement of the schema.
--
-- The original `establishment` table has two functional dependencies whose
-- determinant is NOT a candidate key (verified empirically against the data):
--
--   (1) rating_value -> rating_numeric    ('5'->5, 'AwaitingInspection'->NULL ...)
--   (2) la_code      -> scheme_type       (every premise in an LA shares a scheme)
--
-- (1) is a BCNF violation; (2) is a transitive dependency (3NF & BCNF violation).
-- Both create redundancy. This script removes them by:
--
--   * extracting a RATING_TYPE lookup keyed on rating_value, and
--   * dropping scheme_type from establishment (it already lives on
--     local_authority, where it legitimately depends on the key).
--
-- The result is BCNF, and since no table contains independent multi-valued
-- facts, it is also 4NF. The decomposition is lossless: the original row is
-- recovered by joining establishment -> rating_type and establishment ->
-- local_authority.
-- =============================================================================

DROP DATABASE IF EXISTS food_hygiene_bcnf;
CREATE DATABASE food_hygiene_bcnf CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE food_hygiene_bcnf;

-- Dimensions carried over unchanged (each is already BCNF/4NF) -----------------
CREATE TABLE region        LIKE food_hygiene.region;
CREATE TABLE business_type LIKE food_hygiene.business_type;
CREATE TABLE imd_lad       LIKE food_hygiene.imd_lad;
CREATE TABLE local_authority LIKE food_hygiene.local_authority;  -- keeps scheme_type (depends on key)

-- NEW: rating lookup. rating_value is the key; rating_numeric and the status
-- category depend only on it. (Note: rating_value does NOT determine scheme,
-- because 'Exempt' occurs under both FHRS and FHIS, so scheme is not stored here.)
CREATE TABLE rating_type (
  rating_value    VARCHAR(30) PRIMARY KEY,
  rating_numeric  TINYINT NULL,                 -- 0..5 for FHRS, else NULL
  status_category ENUM('fhrs_rated','fhis_outcome','awaiting','exempt') NOT NULL
) ENGINE=InnoDB;

-- Fact table WITHOUT the redundant columns -----------------------------------
CREATE TABLE establishment (
  fhrs_id            BIGINT PRIMARY KEY,
  la_business_id     VARCHAR(100),
  business_name      VARCHAR(255),
  business_type_id   INT,
  address_line1      VARCHAR(255),
  address_line2      VARCHAR(255),
  address_line3      VARCHAR(255),
  address_line4      VARCHAR(255),
  post_code          VARCHAR(20),
  rating_value       VARCHAR(30),                -- FK -> rating_type (rating_numeric lives there now)
  rating_date        DATE NULL,
  la_code            VARCHAR(10) NOT NULL,        -- scheme_type reached via local_authority now
  new_rating_pending BOOLEAN,
  longitude          DECIMAL(9,6) NULL,           -- premise-level, NOT determined by postcode
  latitude           DECIMAL(8,6) NULL,
  hygiene_score      SMALLINT NULL,
  structural_score   SMALLINT NULL,
  confidence_score   SMALLINT NULL,
  CONSTRAINT fk2_est_la     FOREIGN KEY (la_code)          REFERENCES local_authority(la_code),
  CONSTRAINT fk2_est_type   FOREIGN KEY (business_type_id) REFERENCES business_type(business_type_id),
  CONSTRAINT fk2_est_rating FOREIGN KEY (rating_value)     REFERENCES rating_type(rating_value),
  KEY idx2_est_la     (la_code),
  KEY idx2_est_type   (business_type_id),
  KEY idx2_est_rating (rating_value)
) ENGINE=InnoDB;

-- ---- Populate losslessly from the loaded database ---------------------------
INSERT INTO region          SELECT * FROM food_hygiene.region;
INSERT INTO business_type   SELECT * FROM food_hygiene.business_type;
INSERT INTO imd_lad         SELECT * FROM food_hygiene.imd_lad;
INSERT INTO local_authority SELECT * FROM food_hygiene.local_authority;

INSERT INTO rating_type (rating_value, rating_numeric, status_category)
SELECT rating_value, rating_numeric,
       CASE WHEN rating_numeric IS NOT NULL                       THEN 'fhrs_rated'
            WHEN rating_value IN ('Pass','Improvement Required',
                                  'Pass and Eat Safe')            THEN 'fhis_outcome'
            WHEN rating_value LIKE '%waiting%'                    THEN 'awaiting'
            WHEN rating_value = 'Exempt'                          THEN 'exempt'
            ELSE 'awaiting' END
FROM food_hygiene.establishment
GROUP BY rating_value, rating_numeric;

INSERT INTO establishment
  (fhrs_id, la_business_id, business_name, business_type_id,
   address_line1, address_line2, address_line3, address_line4, post_code,
   rating_value, rating_date, la_code, new_rating_pending,
   longitude, latitude, hygiene_score, structural_score, confidence_score)
SELECT
   fhrs_id, la_business_id, business_name, business_type_id,
   address_line1, address_line2, address_line3, address_line4, post_code,
   rating_value, rating_date, la_code, new_rating_pending,
   longitude, latitude, hygiene_score, structural_score, confidence_score
FROM food_hygiene.establishment;
