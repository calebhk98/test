-- =============================================================================
-- Food Hygiene Ratings + Deprivation : database schema
-- Target: MySQL 8 / MariaDB 10.11 (uses only portable SQL)
--
-- Sources modelled:
--   * FSA Food Hygiene Rating Scheme (FHRS) open data  -- per-establishment XML
--   * FSA authorities API                              -- local authority + region
--   * English Indices of Deprivation 2019 (File 10)    -- LA-district deprivation
--
-- Notes on the grain / semantics that drove the design:
--   * FHRS rating_value is 0..5 where 5 is BEST. Non-numeric values
--     ('AwaitingInspection','Exempt', Scottish 'Pass', etc.) are kept as text in
--     rating_value, with rating_numeric left NULL so averages ignore them.
--   * Component scores (hygiene/structural/confidence) are FHRS-only and run the
--     OTHER way: 0 is best, larger is worse. Scotland (FHIS) has no scores.
-- =============================================================================

DROP DATABASE IF EXISTS food_hygiene;
CREATE DATABASE food_hygiene CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE food_hygiene;

-- ---------------------------------------------------------------------------
-- Reference: FSA reporting regions (12 across the UK)
-- ---------------------------------------------------------------------------
CREATE TABLE region (
  region_id    INT AUTO_INCREMENT PRIMARY KEY,
  region_name  VARCHAR(40) NOT NULL UNIQUE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Reference: business types (from the FSA business-types API)
-- ---------------------------------------------------------------------------
CREATE TABLE business_type (
  business_type_id    INT PRIMARY KEY,
  business_type_name  VARCHAR(120) NOT NULL
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Deprivation summary, one row per English Local Authority District (IoD 2019).
-- England only -- there is no equivalent UK-wide deprivation index.
-- ---------------------------------------------------------------------------
CREATE TABLE imd_lad (
  lad_code                         VARCHAR(10)  PRIMARY KEY,   -- ONS code e.g. E06000001
  lad_name                         VARCHAR(120) NOT NULL,
  imd_avg_rank                     DECIMAL(10,2),              -- higher rank value = less deprived
  imd_rank_of_avg_rank             INT,
  imd_avg_score                    DECIMAL(8,3),               -- higher score = MORE deprived
  imd_rank_of_avg_score            INT,                        -- 1 = most deprived district
  prop_lsoa_in_most_deprived_decile DECIMAL(6,4),              -- 0..1
  rank_prop_most_deprived          INT,
  imd_extent                       DECIMAL(8,4),
  rank_extent                      INT,
  imd_local_concentration          DECIMAL(12,2),
  rank_local_concentration         INT,
  KEY idx_imd_score (imd_avg_score)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Local authorities (the food authorities that publish the data).
-- la_code is the FSA LocalAuthorityIdCode, which is also the join key found in
-- each establishment record (LocalAuthorityCode).
-- lad_code links to the deprivation table where a confident name match exists.
-- ---------------------------------------------------------------------------
CREATE TABLE local_authority (
  la_code              VARCHAR(10) PRIMARY KEY,
  la_id                INT NOT NULL UNIQUE,        -- FSA LocalAuthorityId
  name                 VARCHAR(120) NOT NULL,
  friendly_name        VARCHAR(120),
  region_id            INT NOT NULL,
  scheme_type          TINYINT,                    -- 1 = FHRS, 2 = FHIS (Scotland)
  url                  VARCHAR(255),
  email                VARCHAR(255),
  establishment_count  INT,
  last_published_date  DATETIME,
  lad_code             VARCHAR(10) NULL,           -- mapped to imd_lad (England only)
  CONSTRAINT fk_la_region FOREIGN KEY (region_id) REFERENCES region(region_id),
  CONSTRAINT fk_la_lad    FOREIGN KEY (lad_code)  REFERENCES imd_lad(lad_code),
  KEY idx_la_region (region_id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- The fact table: one row per rated establishment.
-- ---------------------------------------------------------------------------
CREATE TABLE establishment (
  fhrs_id            BIGINT PRIMARY KEY,                 -- FHRSID, globally unique
  la_business_id     VARCHAR(100),                       -- LA's own id (not always numeric)
  business_name      VARCHAR(255),
  business_type_id   INT,
  address_line1      VARCHAR(255),
  address_line2      VARCHAR(255),
  address_line3      VARCHAR(255),
  address_line4      VARCHAR(255),
  post_code          VARCHAR(20),
  rating_value       VARCHAR(30),                        -- raw rating (numeric or text)
  rating_numeric     TINYINT NULL,                       -- 0..5 for FHRS, else NULL
  rating_date        DATE NULL,                          -- NULL = not yet inspected
  la_code            VARCHAR(10) NOT NULL,
  scheme_type        VARCHAR(10),                        -- 'FHRS' or 'FHIS'
  new_rating_pending BOOLEAN,
  longitude          DECIMAL(9,6) NULL,
  latitude           DECIMAL(8,6) NULL,
  hygiene_score      SMALLINT NULL,                      -- FHRS only; 0 best, higher worse
  structural_score   SMALLINT NULL,
  confidence_score   SMALLINT NULL,
  CONSTRAINT fk_est_la   FOREIGN KEY (la_code)          REFERENCES local_authority(la_code),
  CONSTRAINT fk_est_type FOREIGN KEY (business_type_id) REFERENCES business_type(business_type_id),
  KEY idx_est_la       (la_code),
  KEY idx_est_type     (business_type_id),
  KEY idx_est_rating   (rating_numeric),
  KEY idx_est_postcode (post_code),
  KEY idx_est_date     (rating_date)
) ENGINE=InnoDB;
