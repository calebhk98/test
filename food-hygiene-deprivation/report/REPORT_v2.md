# UK Food Hygiene Ratings vs. Deprivation — Project Report

> **How to use this file.** The report is organised to mirror the assignment's exact
> Stage / Step numbering, so each answer sits directly under the requirement and
> marking criterion it addresses. Anywhere you see **[YOUR WORDS]**, **[INSERT
> DIAGRAM]**, or **[SCREENSHOT]**, replace it with your own content before submitting.

**Summary of what was built** (all in the `foodHygeine` lab):

| Component | File |
|---|---|
| Connection check | `checkDB.js` |
| MySQL schema (all CREATE statements) | `createDBTables.sql` |
| Least-privilege web-app user | `makeUser.sql` |
| Downloader (all 363 FHRS files + authority list) | `DownloadingMoreData.js` |
| Loader (XML to MySQL) + deprivation (xlsx) + name-matching | `LoadData.js` |
| Data cleaning with an audit trail | `clean.js` |
| Analytical SQL, one block per question | `QuestionAnswers.sql` |
| Read-only Node.js web app | `webapp/server.js`, `webapp/public/index.html` |

**Scale:** 609,914 establishments loaded across 363 local authorities and 12 regions,
joined to deprivation for 289 of those authorities, then cleaned to 608,755 rows after
quarantining 1,159 impossible records.

---

# Stage 1 — Find and critique a dataset

## Stage 1, Step 1 — Choose a source of open data
*Requirement: open, real (not artificial), not too simple; may combine two datasets if linking them helps; a normalised relational model must not already be published.*
*Marking criterion 1.1: Dataset is appropriate.*

This project combines **two** open datasets — food hygiene ratings and area
deprivation — because linking them answers a question neither can alone ("do poorer
areas have worse hygiene?"). Both are real, official UK open data.

**Sources I found and evaluated:**
- **FSA Food Hygiene Ratings open data** — https://ratings.food.gov.uk/open-data —
  **USED** (the establishment fact data; one XML file per authority).
- FSA business-types API — https://api1-ratings.food.gov.uk/business-types/xml —
  *found but not used*: business types were already present as `BusinessType` /
  `BusinessTypeID` inside the establishment XML, so I built the `business_type` table
  from those and avoided a second call.
- IoD 2019 lookup on data.gov.uk —
  https://www.data.gov.uk/dataset/5f124118-f20e-4b28-aa24-2edda9b4e3cb/index-of-multiple-deprivation-december-2019-lookup-in-en —
  *found but not used*: I loaded IoD File 10 directly from gov.uk instead.
- **English Indices of Deprivation 2019** —
  https://www.gov.uk/government/statistics/english-indices-of-deprivation-2019 —
  **USED** (File 10, the LA-district deprivation summaries).
- ONS postcode-to-LSOA (NSPL) geoportal file —
  https://geoportal.statistics.gov.uk/datasets/3635ca7f69df4733af27caf86473ffa1/about —
  *found but not used*: only needed for a street-level (LSOA) join, which was out of
  scope; I joined at Local-Authority-District level instead.

It is not too simple: five tables, ~608k fact rows, and a cross-dataset join with no
shared key. **[YOUR WORDS: confirm you are not aware of a published normalised model
for this exact combination.]**

## Stage 1, Step 2 — Assess the dataset
*Requirement: assess using Quality, Detail, Documentation, Interrelation, Use, Discoverability; and assess the terms of use.*
*Marking criterion 1.2: Dataset assessment — all criteria addressed.*

- **Quality.** Official statutory register; every record has a unique FHRS ID; foreign
  keys held across 609k rows with zero violations. Caveats: some `rating_date` values
  are implausibly old (the cleaner removed 1,159 pre-2006 records), ~24% of rows lack
  coordinates, and ratings are self-published per authority so small inter-authority
  gaps partly reflect inspection backlogs.
- **Detail (level of detail).** Rich at establishment grain: name, postcode, business
  type, headline rating plus three component scores, coordinates, inspection date.
  Missing: history (time depth) and premises size.
- **Documentation.** FHRS ships an open-data schema/ReadMe and the XML is
  self-describing; IoD 2019 has a full technical report and FAQ on gov.uk. Friction was
  mechanical, not conceptual (the FHRS landing page is a JS app that 404s scripted
  requests, so file URLs come from the authorities API).
- **Interrelation.** High value, moderate difficulty — the FHRS-to-deprivation join has
  no shared key (see Stage 2, Step 2).
- **Use.** Good for a "how clean is my area" tool and for targeting inspection effort.
  Cannot answer trend questions (no history), true inspection frequency (only the
  latest date), or sub-authority deprivation (needs a postcode-to-LSOA bridge).
- **Discoverability.** Easy — both are flagship UK open datasets linked from
  data.gov.uk.

**Terms of use.** Both datasets are under the **Open Government Licence v3.0 (OGL)**,
which permits copying, adapting and combining the data (including for coursework)
provided the source is attributed. Required attribution: *"Contains public sector
information licensed under the Open Government Licence v3.0"* — Crown copyright (FSA;
and MHCLG for the deprivation index). No fees, no personal data, no redistribution
limits affect this project. **[YOUR WORDS: add the access date — e.g. accessed 13 July
2026.]**

## Stage 1, Step 3 — Explain your interest and research questions
*Requirement: why is this interesting; give questions a database application could help with.*
*Marking criteria 1.3 (Interest) and 1.4 (Research questions justify a database approach).*

**Interest. [YOUR WORDS]** It would be interesting to see whether food-hygiene
standards line up with area deprivation — i.e. whether poorer areas tend to have lower
hygiene ratings — and how that interacts with region and business type.

**Research questions** (each needs joins/aggregation across tables, so a relational
database is justified over sorting a spreadsheet; all are descriptive, so this is not a
statistics/ML task):
- **Q1 — What type of places have better hygiene?** (by business type)
- **Q2 — Is score correlated with location?** (by region, and by local authority)
- **Q3 — Do poorer locations have lower hygiene?** (the cross-dataset deprivation join)
- **Q4 — How recent / how frequent was the last inspection?**

---

# Stage 2 — Model your data

## Stage 2, Step 1 — Complete E/R model
*Requirement: draw a complete E/R model; justify any subset.*
*Marking criterion 2.1: E/R model identifies all fields and entities.*

Entities and attributes (the model after normalisation — see Stage 2, Step 3):
- **region** (`region_id` PK, `region_name`)
- **business_type** (`business_type_id` PK, `business_type_name`)
- **rating_type** (`rating_value` PK, `rating_numeric`)
- **local_authority** (`la_code` PK, `name`, `region_id` FK, `scheme_type`, `lad_code`)
- **establishment** (`fhrs_id` PK, `business_name`, `post_code`, `rating_date`,
  `hygiene_score`, `structural_score`, `confidence_score`, `longitude`, `latitude`;
  plus foreign keys `business_type_id`, `la_code`, `rating_value`)
- **imd_lad** (`lad_code` PK, `lad_name`, `imd_avg_score`, `imd_rank`)

## Stage 2, Step 2 — Cardinality and relational mapping
*Requirement: add cardinality; if any structure is not relational-compatible, draw a second diagram of the modified structure.*
*Marking criteria 2.2 (E/R diagram: clear, legal, ellipse/rhombus/rectangle notation) and 2.3 (E/R to relational mapping; issues resolved).*

**[INSERT DIAGRAM: Chen-style E/R diagram — rectangles for the six entities, ellipses
for attributes (primary keys underlined), rhombi for the relationships, cardinalities
on the lines. Your drawn diagram already shows the normalised model, including the
`rating_type` entity and the `Rates` relationship. Ensure `scheme_type` appears ONLY on
`local_authority`, not on `establishment`.]**

Relationships and cardinality (all one-to-many; no many-to-many, so no junction tables):
- region **1—N** local_authority (*located in*)
- local_authority **1—N** establishment (*regulates*)
- business_type **1—N** establishment (*categorises*)
- rating_type **1—N** establishment (*rates*)
- local_authority **1—1 (optional)** imd_lad (*maps to*)

**Relational-mapping issue resolved.** The `local_authority`–`imd_lad` link has **no
shared key** (FHRS uses names, IoD uses ONS codes) and is **optional** (74 of 363
authorities never match). It is implemented as a nullable `lad_code` column populated by
name-matching, **not** an enforced foreign key — a hard FK would reject the 74 unmatched
rows. No structure is relational-incompatible, so a single diagram suffices.

## Stage 2, Step 3 — Tables, fields and normalisation
*Requirement: list tables/fields; evaluate against the normal forms; adjust to at least 3NF; state which forms; justify not going further.*
*Marking criterion 2.4: Normalisation analysis is clear, explicit and accurate.*

Starting from a single `establishment`-centric design, two functional dependencies were
identified and removed:

- **1NF** — all columns atomic, no repeating groups. Holds.
- **2NF** — every table has a single-column primary key, so no partial dependencies.
  Holds.
- **3NF/BCNF violations found and fixed:**
  - `rating_value → rating_numeric` (the numeric rating is determined by the text
    rating, a non-key attribute) — **fixed** by extracting **`rating_type(rating_value
    PK, rating_numeric)`** and making `establishment.rating_value` a foreign key.
  - `la_code → scheme_type` (all premises in an authority share its scheme) — **fixed**
    by moving `scheme_type` onto `local_authority` and removing it from `establishment`.

After this decomposition, the only determinant in every table is a candidate key, so the
schema is in **BCNF** (hence 3NF, 2NF, 1NF). The decomposition is **lossless**: rejoining
`establishment` to `rating_type` (on `rating_value`) and to `local_authority` (on
`la_code`) reproduces the original rows. **No 4NF issue** — no table holds two
independent multi-valued facts.

**Query ergonomics.** To avoid re-joining `rating_type` in every aggregate query, a view
**`v_establishment`** re-joins the normalised pieces and re-exposes `rating_numeric` and
`scheme_type`; analysis queries read from the view. The base tables are BCNF; the view
stores nothing.

---

# Stage 3 — Create the database

## Stage 3, Step 1 — Build the structure (all CREATE commands)
*Requirement: build in MySQL; record all CREATE commands.*
*Marking criteria 3.1 (accurately implement the model) and 3.2 (sensible types, keys, constraints).*

Full script: `createDBTables.sql`. InnoDB is the MySQL 8.0 default so `ENGINE=` is
omitted; `rating_date` is nullable to mean "never inspected"; `lad_code` is a plain
nullable column (Stage 2, Step 2).

```sql
USE foodHygeine;

-- children before parents (view first, then FK-referencing tables)
DROP VIEW  IF EXISTS v_establishment;
DROP TABLE IF EXISTS imd_lad;
DROP TABLE IF EXISTS establishment;
DROP TABLE IF EXISTS rating_type;
DROP TABLE IF EXISTS local_authority;
DROP TABLE IF EXISTS business_type;
DROP TABLE IF EXISTS region;

CREATE TABLE region (
  region_id   INT AUTO_INCREMENT PRIMARY KEY,
  region_name VARCHAR(40) NOT NULL UNIQUE
);

CREATE TABLE business_type (
  business_type_id   INT PRIMARY KEY,
  business_type_name VARCHAR(120) NOT NULL
);

CREATE TABLE rating_type (
  rating_value   VARCHAR(30) PRIMARY KEY,  -- '5', 'AwaitingInspection', 'Pass', ...
  rating_numeric TINYINT NULL              -- 0-5 when numeric, else NULL
);

CREATE TABLE local_authority (
  la_code     VARCHAR(10) PRIMARY KEY,
  name        VARCHAR(120) NOT NULL,
  region_id   INT NOT NULL,
  scheme_type VARCHAR(10),                 -- FHRS/FHIS, depends on the authority
  lad_code    VARCHAR(10) NULL,            -- deprivation district (name-matched)
  CONSTRAINT fk_la_region FOREIGN KEY (region_id) REFERENCES region(region_id)
);

CREATE TABLE establishment (
  fhrs_id          BIGINT PRIMARY KEY,
  business_name    VARCHAR(255),
  business_type_id INT,
  post_code        VARCHAR(20),
  rating_value     VARCHAR(30),            -- FK into rating_type
  rating_date      DATE NULL,              -- NULL = awaiting first inspection
  la_code          VARCHAR(10) NOT NULL,
  hygiene_score    SMALLINT NULL,          -- 0 is best, higher is worse
  structural_score SMALLINT NULL,
  confidence_score SMALLINT NULL,
  longitude        DECIMAL(9,6) NULL,
  latitude         DECIMAL(8,6) NULL,
  CONSTRAINT fk_est_la     FOREIGN KEY (la_code)          REFERENCES local_authority(la_code),
  CONSTRAINT fk_est_type   FOREIGN KEY (business_type_id) REFERENCES business_type(business_type_id),
  CONSTRAINT fk_est_rating FOREIGN KEY (rating_value)     REFERENCES rating_type(rating_value),
  KEY idx_est_la   (la_code),
  KEY idx_est_type (business_type_id)
);

CREATE TABLE imd_lad (
  lad_code      VARCHAR(10) PRIMARY KEY, -- ONS district code, e.g. E09000002
  lad_name      VARCHAR(120),
  imd_avg_score DECIMAL(8,3),            -- higher = more deprived
  imd_rank      INT                      -- 1 = most deprived district
);

CREATE VIEW v_establishment AS
SELECT e.fhrs_id, e.business_name, e.business_type_id, e.post_code,
       e.rating_value, rt.rating_numeric, e.rating_date, e.la_code,
       la.scheme_type, e.hygiene_score, e.structural_score, e.confidence_score,
       e.longitude, e.latitude
FROM establishment e
LEFT JOIN rating_type rt     ON e.rating_value = rt.rating_value
LEFT JOIN local_authority la ON e.la_code = la.la_code;
```

Least-privilege web user (`makeUser.sql`) — the app only ever gets SELECT:
```sql
CREATE USER IF NOT EXISTS 'fhrs_read'@'localhost' IDENTIFIED BY 'readonly';
GRANT SELECT ON foodHygeine.* TO 'fhrs_read'@'localhost';
FLUSH PRIVILEGES;
```
A write attempt is refused at the database:
`ERROR 1142 (42000): DELETE command denied to user 'fhrs_read'@'localhost'`.

## Stage 3, Step 2 — Enter instance data
*Requirement: enter a usable sample or all the data; detail how it was added.*
*(Feeds marking criterion 3.1, and the "all tables/fields used multiple times" rule.)*

`DownloadingMoreData.js` fetches the authority list, then downloads all 363 authority
XML files via `curl` (retry/back-off; `curl` shells out so it works behind the lab's
HTTPS proxy). `LoadData.js` then, in one run: inserts distinct **regions** and reads back
their ids; inserts **local authorities**; parses every XML with `fast-xml-parser`,
collecting **business types**, **rating types**, the **scheme per authority**, and
**establishment** rows (keeping only selected authorities, de-duplicating on `fhrs_id`,
bulk-inserting in 2,000-row batches); then downloads IoD 2019 File 10 (`xlsx`), loads
**imd_lad**, and matches each authority to a district by normalised name plus a small
alias table.

Loaded counts: 12 regions, 14 business types, 317 imd_lad districts, 363 local
authorities (289 matched to deprivation), 609,914 establishments (608,755 after
cleaning). All five base tables are populated and every field is exercised across
hundreds of thousands of rows.

**The name-matching (no shared key).** Names are normalised (lower-case; strip "City
of"/"Borough of"; `&`→`and`; de-hyphenate) plus a two-entry alias table
(`Blackburn`→`Blackburn with Darwen`, `Hull City`→`Kingston upon Hull`). This resolves
289 of 363. The 74 unmatched are **not errors**: ~60 are Scotland/Wales/NI (outside the
English index), two are port health authorities with no resident population (River Tees,
Hull and Goole Port), and the rest are post-2019 unitary authorities (e.g. Cumberland,
Buckinghamshire) that did not exist when IoD 2019 was published.

## Stage 3, Step 3 — Reflection
*Requirement: note one or two elements that do or don't work well.*
*Marking criterion 3.3: Critical reflection tied to interest/research questions.*

**Works well:** the grain is right (one row per establishment matches the source);
FHRS IDs are naturally unique so the PK needs no surrogate; keeping `rating_value` (text)
and `rating_numeric` (clean) loses nothing yet makes aggregation trivial; nullable
`rating_date` turns "awaiting inspection" into a countable state; foreign keys held with
zero violations across 609k rows.

**Works less well:** deprivation is only at **authority** grain — LSOA-level would need
the large ONS postcode-to-LSOA file — so within-authority variation is invisible, which
caps how sharply Q3 can be answered. Scotland's FHIS has no 0-5 rating, so every numeric
analysis is implicitly England/Wales/NI only (Scotland is in the `region` table but drops
out of rating averages).

## Stage 3, Step 4 — SQL that answers the questions
*Requirement: list SQL that answers the Stage 1 questions; explain any that can't be.*
*Marking criterion 3.4: Queries are correct and reflect the questions.*

Runnable script with one labelled block per question: `QuestionAnswers.sql`. Headline
results (full dataset):

**Q1 — business types.** Schools/hospitals/supermarkets top (avg ~4.8-4.9);
**independent takeaways worst** (4.331, only 61% rated 5).

**Q2 — location.** By region, a gradient from Northern Ireland / South West at the top
(4.77) to London at the bottom (4.46). By authority, the best are small rural/county
districts (Bassetlaw 4.96, Dorset 4.94); the worst are dominated by London boroughs.

**Q3 — deprivation.** Across the 289 matched English authorities, Pearson **r = −0.377**
(more deprived → lower ratings), with a clean monotonic decline by quintile (4.730 at the
least-deprived fifth to 4.554 at the most). Real but modest (r² ≈ 0.14; ~14% of the
variation), and significant (t ≈ −6.9, p < 0.001).

**Q4 — recency.** 69,291 premises (11.4%) await a first inspection; of those rated, the
average rating is 2.04 years old, 41.5% were rated in the last year and 16.4% are over
three years old. *(True inspection **frequency** cannot be answered — only the latest
date is stored, not a history.)*

---

# Stage 4 — Create a simple web application

## Stage 4, Step 1 — The Node.js application
*Requirement: a node.js web app querying the DB, addressing some questions; the connecting account has appropriate privileges.*
*Marking criteria 4.1 (runs), 4.2 (DB interaction handled), 4.3 (data presented; valid HTML), 4.4 (goals satisfied).*

`webapp/server.js` is an Express app connecting over the local socket with the
**SELECT-only** `fhrs_read` account — appropriate least privilege for a query-only tool
and a hard stop on writes. Queries use `mysql2` parameterised (named-placeholder)
queries. The single-page UI (`webapp/public/index.html`) uses relative fetch paths (so it
works behind the lab's port-proxy) and renders headline stats, ratings by region, the
deprivation gradient plus correlation, a scatter plot with regression line and a
significance test (Chart.js), ratings by business type, an authority leaderboard with a
region filter, an inspection-recency panel, and an establishment search.

```
Endpoints: /api/stats  /api/regions  /api/deprivation  /api/deprivation-points
           /api/business-types  /api/authorities  /api/recency  /api/search
```
Each maps to a research question: business types → Q1; regions and authorities → Q2;
deprivation and deprivation-points → Q3; recency → Q4. UI section headings are labelled
so each answer is explicitly called out.

## Stage 4, Step 2 — Screenshots
*Requirement: screenshots of the main screens, in the report.*

**[SCREENSHOT: dashboard — stat tiles + ratings-by-region table.]**
**[SCREENSHOT: deprivation scatter plot with the trend line and the r / r² / t line.]**
**[SCREENSHOT: establishment search returning results.]**

---

# Referencing
*Marking criterion: referencing includes data, literature and code labelling.*

**Data — sources used** (all Crown copyright, OGL v3.0):
- FSA Food Hygiene Ratings open data — https://ratings.food.gov.uk/open-data
- FSA authorities list — https://api.ratings.food.gov.uk/authorities
- English Indices of Deprivation 2019, File 10 —
  https://www.gov.uk/government/statistics/english-indices-of-deprivation-2019

**Data — found and evaluated but not used** (reached the same data by a simpler route):
FSA business-types API (`api1-ratings.food.gov.uk/business-types/xml`); IoD 2019 lookup
on data.gov.uk; ONS postcode-to-LSOA (NSPL) geoportal file — reasons in Stage 1, Step 1.

**Libraries.** `express`, `mysql2`, `fast-xml-parser`, `xlsx` (npm); `Chart.js`
(vendored locally) for the scatter plot.

**Techniques / standard formulas** (the formulas are standard; the SQL/JS implementing
them is my own):
1. Pearson correlation coefficient (computational form) — Pearson correlation
   coefficient, Wikipedia. https://en.wikipedia.org/wiki/Pearson_correlation_coefficient
2. Coefficient of determination, R² = r² for simple linear regression — Wikipedia.
   https://en.wikipedia.org/wiki/Coefficient_of_determination
3. Significance test t = r·sqrt(n−2)/sqrt(1−r²), df = n−2 — Testing the Significance of
   the Correlation Coefficient, OpenStax / Lumen Learning.
   https://courses.lumenlearning.com/introstats1/chapter/testing-the-significance-of-the-correlation-coefficient/
4. Ordinary least squares slope/intercept — Simple linear regression, Wikipedia.
   https://en.wikipedia.org/wiki/Simple_linear_regression
5. Normal forms (1NF–BCNF, after Codd) — Database normalization, Wikipedia.
   https://en.wikipedia.org/wiki/Database_normalization
6. Open Government Licence v3.0 — The National Archives.
   https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/
7. English Indices of Deprivation 2019 (score/rank meaning is in the FAQ) — GOV.UK.
   https://www.gov.uk/government/statistics/english-indices-of-deprivation-2019 ; FAQ:
   https://assets.publishing.service.gov.uk/media/5dfb3d7ce5274a3432700cf3/IoD2019_FAQ_v4.pdf

**Code provenance.** **[YOUR WORDS — fill honestly; since this is your own work, most is
"written by me"; mark anything adapted.]**

| File | Author / origin |
|---|---|
| `checkDB.js` | [written by me] |
| `createDBTables.sql` | [written by me] |
| `makeUser.sql` | [written by me] |
| `DownloadingMoreData.js` | [written by me] |
| `LoadData.js` | [written by me; `norm()` approach based on standard string-normalisation] |
| `clean.js` | [written by me] |
| `QuestionAnswers.sql` | [written by me; Pearson formula per reference 1] |
| `webapp/server.js` | [written by me] |
| `webapp/public/index.html` | [written by me; Chart.js is third-party, reference above] |

**[YOUR WORDS: add the access/retrieval date for the data URLs — e.g. accessed 13 July 2026.]**

---

# Discretionary extra credit
*Up to 15% for work beyond the basic requirements — highlight these.*

- **Data cleaning with a reversible audit trail** — `clean.js` quarantines the 1,159
  impossible (pre-2006-date) rows into `establishment_rejects` with a reason and
  timestamp before deleting, and writes a cleaning report; nothing is silently lost.
- **Dataset alignment / name reconciliation** — matching two datasets with no shared key
  (289 of 363), and documenting why the remaining 74 legitimately cannot match rather
  than forcing bogus joins.
- **Statistical rigour in the app** — beyond the Pearson r, an in-page regression, R²,
  and a t-test verdict (p < 0.001) with a scatter plot, showing the relationship is
  significant but modest rather than merely asserting it.
- **BCNF normalisation with a convenience view** — a full lossless decomposition to BCNF,
  kept query-friendly by a `v_establishment` view.
