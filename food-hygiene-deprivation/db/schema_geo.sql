-- =============================================================================
-- ADDITIVE schema: neighbourhood-level (LSOA) deprivation.
--
-- Run AFTER db/schema.sql + the base load. Adds two open datasets and the
-- bridge that connects food-hygiene premises to neighbourhood deprivation:
--
--   imd_lsoa : English Indices of Deprivation 2019, File 7 (per 2011 LSOA) —
--              the IMD plus all seven sub-domains and population.
--   postcode : ONS "Postcode -> OA(2011) -> LSOA -> MSOA -> LAD" best-fit
--              lookup (August 2021), giving each postcode its 2011 LSOA.
--
-- THE JOIN CHAIN (the whole point of this file):
--   establishment.postcode_norm  =  postcode.postcode_norm
--   postcode.lsoa11cd            =  imd_lsoa.lsoa11cd
--
-- Both sides of the first join are normalised (UPPER, spaces removed) because
-- FHRS and ONS format postcodes slightly differently. The 2011 LSOA vintage is
-- chosen deliberately to match IoD 2019 (which is published on 2011 LSOAs).
-- imd_lsoa is England-only, so Scottish/Welsh/NI postcodes resolve to an LSOA
-- but have no deprivation row — they stay NULL, never invented.
-- =============================================================================
USE food_hygiene;

DROP TABLE IF EXISTS postcode;
DROP TABLE IF EXISTS imd_lsoa;

-- Neighbourhood deprivation (IoD 2019 File 7) --------------------------------
CREATE TABLE imd_lsoa (
  lsoa11cd          VARCHAR(9) PRIMARY KEY,      -- 2011 LSOA code, e.g. E01000001
  lsoa11nm          VARCHAR(120),
  lad_code          VARCHAR(10),                 -- 2019 LAD code
  imd_score         DECIMAL(8,3),                -- higher = more deprived
  imd_rank          INT,                         -- 1 = most deprived of 32,844
  imd_decile        TINYINT,                     -- 1 = most deprived 10%
  income_score      DECIMAL(7,4),
  employment_score  DECIMAL(7,4),
  education_score   DECIMAL(8,3),
  health_score      DECIMAL(8,4),
  crime_score       DECIMAL(8,4),
  barriers_score    DECIMAL(8,3),
  living_score      DECIMAL(8,3),
  income_decile     TINYINT,
  employment_decile TINYINT,
  education_decile  TINYINT,
  health_decile     TINYINT,
  crime_decile      TINYINT,
  barriers_decile   TINYINT,
  living_decile     TINYINT,
  total_population  INT,
  KEY idx_imd_lsoa_decile (imd_decile)
) ENGINE=InnoDB;

-- Postcode -> 2011 LSOA bridge (ONS Aug 2021 best-fit lookup) -----------------
-- Not FK'd to imd_lsoa: this lookup is UK-wide but imd_lsoa is England-only.
CREATE TABLE postcode (
  postcode_norm  VARCHAR(16) PRIMARY KEY,        -- UPPER(no spaces), the join key
  pcds           VARCHAR(8),                     -- canonical formatted postcode
  lsoa11cd       VARCHAR(9),
  lad_code       VARCHAR(10),
  KEY idx_pc_lsoa (lsoa11cd)
) ENGINE=InnoDB;

-- Normalised postcode on the fact table so the bridge join is a plain equi-join.
ALTER TABLE establishment
  ADD COLUMN postcode_norm VARCHAR(16)
    GENERATED ALWAYS AS (UPPER(REPLACE(post_code, ' ', ''))) STORED,
  ADD KEY idx_est_pcnorm (postcode_norm);
