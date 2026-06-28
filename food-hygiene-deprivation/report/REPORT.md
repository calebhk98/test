# UK Food Hygiene Ratings vs. Deprivation — Project Report

**Author's brief:** build a MySQL database from open data, use it to ask whether
hygiene scores vary by region, business type and deprivation, and front it with a
small Node.js web application.

**What was built**

| Component | Location |
|---|---|
| MySQL/MariaDB schema (all `CREATE` statements) | `db/schema.sql` |
| Least-privilege DB users | `db/users.sql` |
| Downloader (363 FHRS files + deprivation files) | `etl/01_download.js` |
| Loader (XML/xlsx → MySQL) | `etl/02_load.js` |
| Analytical SQL answering the questions | `queries/analysis.sql` |
| Read-only Node.js web app | `webapp/server.js`, `webapp/public/index.html` |

**Scale of the loaded database:** **608,982 establishments** across **363 local
authorities** and **12 regions**, joined to deprivation scores for **289** of those
authorities. The `establishment` table is ~250 MB.

---

## 1. Data sources & how they were found

| Dataset | Source | Format | Used for |
|---|---|---|---|
| Food Hygiene Ratings (FHRS/FHIS) | `ratings.food.gov.uk/open-data` → one XML per authority (`OpenDataFiles/FHRS{code}en-GB.xml`) | XML | The fact table |
| Authorities + regions | `api.ratings.food.gov.uk/authorities` | JSON | Region mapping, file URLs |
| Business types | `api1-ratings.food.gov.uk/business-types/xml` | XML | Type reference table |
| English Indices of Deprivation 2019, **File 10** (LA-district summaries) | gov.uk / `assets.publishing.service.gov.uk` | XLSX | Deprivation per district |
| IoD 2019 **File 7** (LSOA scores) | gov.uk | CSV | Downloaded for reference / finer analysis (not loaded) |

The FSA `authorities` API was the key that made everything else easy: a single
call yields, for every authority, its **region name** and the **URL of its open-data
file**, so the downloader needs no scraping and the region dimension comes for free.

---

## 2. Database structure (all CREATE commands)

The full script is `db/schema.sql`. Design decisions worth calling out:

* **Star-ish shape** — one fact table (`establishment`) referencing four
  dimensions (`local_authority`, `region`, `business_type`, `imd_lad`).
* **Two rating conventions are preserved.** FHRS `rating_value` is `0..5` where
  **5 is best**; component scores (`hygiene_score` etc.) run the *other* way
  (**0 is best**). Non-numeric values (`AwaitingInspection`, `Exempt`, Scotland's
  `Pass`) are kept verbatim in `rating_value`, with `rating_numeric` left `NULL`
  so averages quietly ignore them.
* **`rating_date` is nullable** — `NULL` means "never inspected" (the XML carries
  an `xsi:nil` element), which is exactly what we want to count later.

```sql
DROP DATABASE IF EXISTS food_hygiene;
CREATE DATABASE food_hygiene CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE food_hygiene;

CREATE TABLE region (
  region_id    INT AUTO_INCREMENT PRIMARY KEY,
  region_name  VARCHAR(40) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE business_type (
  business_type_id    INT PRIMARY KEY,
  business_type_name  VARCHAR(120) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE imd_lad (
  lad_code                          VARCHAR(10)  PRIMARY KEY,   -- ONS code e.g. E06000001
  lad_name                          VARCHAR(120) NOT NULL,
  imd_avg_rank                      DECIMAL(10,2),
  imd_rank_of_avg_rank              INT,
  imd_avg_score                     DECIMAL(8,3),               -- higher = MORE deprived
  imd_rank_of_avg_score             INT,                        -- 1 = most deprived district
  prop_lsoa_in_most_deprived_decile DECIMAL(6,4),
  rank_prop_most_deprived           INT,
  imd_extent                        DECIMAL(8,4),
  rank_extent                       INT,
  imd_local_concentration           DECIMAL(12,2),
  rank_local_concentration          INT,
  KEY idx_imd_score (imd_avg_score)
) ENGINE=InnoDB;

CREATE TABLE local_authority (
  la_code              VARCHAR(10) PRIMARY KEY,    -- FSA LocalAuthorityIdCode
  la_id                INT NOT NULL UNIQUE,
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
  rating_value       VARCHAR(30),                  -- raw rating (numeric or text)
  rating_numeric     TINYINT NULL,                 -- 0..5 for FHRS, else NULL
  rating_date        DATE NULL,                    -- NULL = not yet inspected
  la_code            VARCHAR(10) NOT NULL,
  scheme_type        VARCHAR(10),                  -- 'FHRS' or 'FHIS'
  new_rating_pending BOOLEAN,
  longitude          DECIMAL(9,6) NULL,
  latitude           DECIMAL(8,6) NULL,
  hygiene_score      SMALLINT NULL,                -- 0 best, higher worse
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
```

User creation (`db/users.sql`) — the web app only ever gets `SELECT`:

```sql
CREATE USER IF NOT EXISTS 'fhrs_admin'@'localhost' IDENTIFIED BY '…';   -- loader
GRANT ALL PRIVILEGES ON food_hygiene.* TO 'fhrs_admin'@'localhost';

CREATE USER IF NOT EXISTS 'fhrs_app'@'127.0.0.1' IDENTIFIED BY '…';     -- web app
GRANT SELECT ON food_hygiene.* TO 'fhrs_app'@'127.0.0.1';
```

A write attempt by the app user is rejected at the database, not just the app:
`ERROR 1142 (42000): DELETE command denied to user 'fhrs_app'@'localhost'`.

---

## 3. Entering the instance data

`etl/01_download.js` pulls all 363 authority XML files (≈571 MB) via `curl` with
retry/back-off; `etl/02_load.js` parses them with `fast-xml-parser` and bulk-inserts
in 1,000-row batches. Loaded counts:

```
regions:                12
business types:         15
imd_lad districts:     317
local authorities:     363   (289 matched to a deprivation district)
establishments:    608,982
```

**Joining FHRS to deprivation (the awkward bit).** FHRS identifies authorities by
FSA code and *name*; IoD 2019 uses ONS district codes. There is no shared key, so
the loader normalises names (lower-case, strip "City of"/"Borough of", `&`→`and`,
de-hyphenate) plus a two-entry alias table, and matches on the result. This
resolves **289** of the 363 authorities. The **9 unmatched English** ones are not
errors — they are *post-2019 boundary changes* (Somerset, North Yorkshire,
Cumberland, Buckinghamshire, the two Northamptonshires, Westmorland and Furness —
all unitary authorities created **after** IoD 2019 was published) plus two **port
health authorities** (Hull and Goole Port, River Tees) that have no resident
population and therefore no deprivation score. The other 65 unmatched are in
Scotland, Wales and Northern Ireland, which the English index simply does not
cover.

---

## 4. Reflection: how well does the database reflect the data?

**Well:**
* The grain is right — one row per establishment is exactly the source grain, and
  FHRS IDs are globally unique, so the primary key is natural and no duplicates
  slipped in.
* Keeping `rating_value` (text) **and** `rating_numeric` (clean 0–5) means nothing
  is lost *and* aggregation is trivial. The same trick on `rating_date` (nullable)
  turns "awaiting inspection" into a first-class, countable state.
* Foreign keys held with zero violations across 609k rows, which is itself
  evidence the source data is internally consistent.

**Less well / compromises:**
* **Deprivation is only LA-grain.** IoD is published per LSOA (≈1,500 people);
  joining at that resolution needs a postcode→LSOA lookup (the very large ONS file
  the brief mentioned). I deliberately joined at **Local Authority District**
  level instead — small, clean, and good enough to answer the question — but it
  means within-authority variation in deprivation is invisible. This is the single
  biggest fidelity gap.
* **Cross-scheme comparison is limited.** Scotland's FHIS is pass/fail with no 0–5
  rating and no component scores, so every numeric analysis is implicitly
  FHRS-only (England/Wales/NI). The schema represents Scotland faithfully; the
  *analysis* just can't put it on the same axis.
* Address lines are kept as four loose columns exactly as supplied (sparse and
  inconsistent) rather than being normalised — fine for display, not for
  geocoding.

---

## 5. The questions, answered in SQL

Full runnable script: `queries/analysis.sql`. Headline results below.

### Q1 — What regions have better scores?
A clear north-west-to-south gradient, and London is a distinct outlier at the
bottom.

| Region | Avg rating | % rated 5 | Avg hygiene (0=best) |
|---|--:|--:|--:|
| Northern Ireland | 4.77 | 83.6 | 2.33 |
| South West | 4.77 | 84.6 | 2.74 |
| North East | 4.74 | 83.3 | 2.50 |
| … | | | |
| West Midlands | 4.57 | 75.0 | 3.19 |
| **London** | **4.46** | **68.3** | **3.57** |

### Q2 — Is score correlated with location?
Yes. The best authorities are smaller rural/county districts (Bassetlaw 4.96,
Dorset 4.94); the worst are dominated by **London boroughs** (Newham 3.95, Waltham
Forest 4.00, Ealing 4.17). Location matters a lot.

### Q3 — Do poorer locations have lower hygiene?
**Yes, moderately.** Pearson correlation between an authority's deprivation score
and its mean hygiene rating, across the 289 matched English authorities:

> **r = −0.378**  (negative ⇒ more deprived → lower ratings)

Bucketing authorities into deprivation quintiles shows a clean monotonic decline:

| Deprivation quintile | Avg rating | % rated 5 |
|---|--:|--:|
| 1 – least deprived | 4.729 | 82.1 |
| 2 | 4.726 | 82.0 |
| 3 | 4.665 | 79.4 |
| 4 | 4.605 | 75.6 |
| 5 – most deprived | 4.551 | 73.7 |

The effect is real but modest — deprivation explains part of the regional pattern,
not all of it (London is both deprived *and* has many takeaways; see Q4).

### Q4 — What type of places have better hygiene?
The strongest single signal in the whole dataset.

| Business type | Avg rating | % rated 5 | Avg hygiene |
|---|--:|--:|--:|
| School/college/university | 4.90 | 92.0 | 1.93 |
| Hospitals/childcare/caring | 4.84 | 88.2 | 2.37 |
| Supermarkets | 4.79 | 87.4 | 1.92 |
| Restaurant/Cafe/Canteen | 4.60 | 75.3 | 3.48 |
| Retailers – other | 4.51 | 71.2 | 2.90 |
| **Takeaway/sandwich shop** | **4.33** | **60.9** | **4.56** |

Institutional caterers (schools, hospitals) are cleanest; **independent takeaways
are the worst by a wide margin** — only 61% achieve top marks.

### Q5 — How recent / how frequent are inspections?
* **11.2%** of premises are still **awaiting their first inspection**.
* Mean age of the current rating is **2.1 years**; **41%** were inspected in the
  last year, but **16.5%** are **older than 3 years**.
* Recency varies by region: most of England averages ~1.5–1.8 years, but
  **Scotland's ratings average 4.25 years old** — a different inspection regime.
* The data only carries the *latest* rating date, so true inspection *frequency*
  can't be measured — see §6 "Use / what's missing".

---

## 6. Reflection questions

**Quality — is the data reliable?** Largely yes. It is an official government
statutory register, every record carries a unique FHRS ID, foreign keys held
across 609k rows with no violations, and the figures are plausible and consistent
with the known national skew toward high ratings. Caveats: `rating_date` ranges
back to **1993** (977 records pre-2005, almost all Scottish), which are
implausibly stale and hint at premises that closed but were never removed;
**~24% of records have no coordinates**; and ratings are self-published per
authority, so small differences between authorities partly reflect different
inspection backlogs rather than real hygiene.

**Detail — how much, and is it helpful?** Rich at the establishment level: name,
address, postcode, business type, the headline rating *and* the three component
scores, coordinates, and the inspection date. That is enough for the
type/region/recency questions without any other source. What is missing is *time
depth* (history) and *size* (a corner shop and a stadium kitchen look identical).

**Documentation — how clear, where, easy to find?** The FHRS data is **well
documented** — the FSA publishes an open-data schema/ReadMe and the XML is
self-describing. The IoD 2019 is **excellently documented** (a research report,
technical report and an FAQ on gov.uk). The friction was *mechanical*, not
conceptual: the open-data landing page is a JavaScript app that 404s for scripted
requests, so the real file URLs had to be discovered via the `authorities` API,
and the IoD download links are buried under datestamped `assets.publishing…` paths.

**Interrelation — useful to connect to other sets? Which? How easy?** This is the
heart of the project, and the answer is "very useful, moderately hard". Joining
hygiene to **deprivation** turned a flat register into an answer to a social
question. The difficulty is the lack of a shared key: FHRS uses names, ONS uses
codes, and **administrative boundaries changed after 2019**, which is precisely
why 9 English authorities wouldn't match. Other natural joins: ONS postcode→LSOA
(for street-level deprivation), population (for premises-per-head), and business
registration data (for chain vs. independent).

**Use — what for? what can't you ask? what's missing?** Good for: a consumer
"how clean is my area" tool, prioritising inspection resource toward deprived
areas and takeaways, and the regional/type analysis above. **Can't ask:** (1)
*trend* questions — there is no history, only the current snapshot, so "are ratings
improving?" is impossible; (2) true inspection *frequency* — only the latest date
is given; (3) anything sub-authority about deprivation without the big postcode
lookup; (4) chain-level analysis — there is no operator/brand field.

**Discoverability — how easy was it to find?** Easy. UK food-hygiene open data is a
flagship FSA dataset, linked straight from `data.gov.uk`, and IoD 2019 is the
canonical deprivation source with no real alternative. The domain is mature and
the alternatives are complementary (ONS geographies, census) rather than competing.

---

## 7. The web application

`webapp/server.js` is an Express app that connects with the **`SELECT`-only**
`fhrs_app` account — the appropriate privilege for a query-only tool, and a hard
stop on accidental or malicious writes. All endpoints use **parameterised**
queries. The single-page UI (`webapp/public/index.html`) shows the headline
counts, ratings by region, the deprivation gradient + correlation, ratings by
business type, an authority leaderboard, and an establishment search. See
`report/webapp-screenshot.png`.

```
Endpoints: /api/stats  /api/regions  /api/deprivation
           /api/business-types  /api/authorities  /api/search
```

---

## 8. How to reproduce

```bash
npm install
mysql < db/schema.sql            # create tables
mysql < db/users.sql             # create least-privilege users
node etl/01_download.js          # ~571 MB of FHRS XML (curl + retry)
node etl/02_load.js              # parse + load 609k rows
mysql food_hygiene < queries/analysis.sql   # the answers
node webapp/server.js            # http://localhost:3000
```
