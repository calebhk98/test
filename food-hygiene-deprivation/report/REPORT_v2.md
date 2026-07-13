# UK Food Hygiene Ratings vs. Deprivation — Project Report

> **How to use this file.** This is a rubric-aligned draft built around the actual
> `foodHygeine` lab implementation (the tutorial schema, not the richer reference
> schema). Anywhere you see **[YOUR WORDS]**, **[INSERT DIAGRAM]**, or
> **[SCREENSHOT]**, replace it with your own content before submitting. Every
> section header maps to a marking criterion; the mapping is called out in italics.

**Brief:** take an open dataset, critique it, model it, implement it as a MySQL
database with instance data, and front it with a small Node.js web application that
answers some of the questions raised in the critique.

**What was built**

| Component | File |
|---|---|
| Connection check | `checkDB.js` |
| MySQL schema (all `CREATE` statements) | `createDBTables.sql` |
| Least-privilege web-app user | `makeUser.sql` |
| Downloader (all 363 FHRS files + authority list) | `DownloadingMoreData.js` |
| Loader (XML → MySQL) + deprivation (xlsx) + name-matching | `LoadData.js` |
| Data cleaning with an audit trail | `clean.js` |
| Analytical SQL answering the questions | `analyzeDeprivation.sql` |
| Read-only Node.js web app | `webapp/server.js`, `webapp/public/index.html` |

**Scale of the loaded database:** **609,914 establishments** loaded across **363
local authorities** and **12 regions**, joined to deprivation for **289** of those
authorities, then cleaned to **608,755** rows after quarantining **1,159**
impossible records.

---

## Stage 1 — Find and critique the dataset

### 1.1 Data sources and how they were found
*(Criterion: dataset appropriate; discoverability)*

| Dataset | Source URL | Format | Used for |
|---|---|---|---|
| Food Hygiene Ratings (FHRS/FHIS) | `https://ratings.food.gov.uk/open-data` → one XML per authority (`OpenDataFiles/FHRS{code}en-GB.xml`) | XML | The `establishment` fact table |
| Authorities + regions | `https://api.ratings.food.gov.uk/authorities` | JSON | Region mapping + each authority's file URL |
| English Indices of Deprivation 2019, **File 10** | `https://assets.publishing.service.gov.uk/media/5d8b3cfbe5274a08be69aa91/File_10_-_IoD2019_Local_Authority_District_Summaries__lower-tier__.xlsx` | XLSX | Deprivation score per district (`imd_lad`) |

The FSA `authorities` API was the key that unlocked everything: one call returns,
for every authority, its **region** and the **URL of its open-data file**, so the
downloader needs no scraping and the region dimension arrives for free.

This combines **two** open datasets (hygiene + deprivation) with a real benefit to
linking them — which is exactly what turns "sort a spreadsheet" into a database
question.

### 1.2 Assessment of the dataset
*(Criterion: dataset assessment — all six criteria addressed)*

- **Quality.** An official statutory register. Every record has a unique FHRS ID;
  foreign keys held across 609k rows with zero violations. Caveats: `rating_date`
  values reach implausibly far back (the cleaner removed **1,159** pre-2006
  records), ~24% of rows lack coordinates, and ratings are self-published per
  authority so small inter-authority gaps partly reflect inspection backlogs, not
  hygiene.
- **Level of detail.** Rich at establishment grain: name, postcode, business type,
  the headline rating **and** the three component scores, coordinates, and the
  inspection date. Missing: time depth (no history) and premises size.
- **Documentation.** FHRS ships an open-data schema/ReadMe and the XML is
  self-describing; IoD 2019 has a full technical report + FAQ on gov.uk. The
  friction was mechanical (the landing page is a JS app that 404s scripted
  requests, so real file URLs come from the `authorities` API).
- **Interrelation.** High value, moderate difficulty — see §2.3; there is no shared
  key between FHRS (names) and IoD (ONS codes).
- **Use.** Good for a "how clean is my area" tool and for targeting inspection
  effort. Cannot answer trend questions (no history), true inspection *frequency*
  (only the latest date), or sub-authority deprivation (needs a postcode→LSOA
  bridge).
- **Discoverability.** Easy — both are flagship UK open datasets linked from
  data.gov.uk.

### 1.3 Terms of use / licence
*(Criterion: dataset assessment — terms of use)*  **[NEW — was missing]**

Both datasets are published under the **Open Government Licence v3.0 (OGL)**. Under
OGL the data may be copied, adapted, and combined, including for this coursework,
provided the source is **attributed**. The required attribution statements are:
- Food hygiene data: *"Contains public sector information licensed under the Open
  Government Licence v3.0"* — © Crown copyright, Food Standards Agency.
- Deprivation data: *"Contains public sector information licensed under the OGL
  v3.0"* — © Crown copyright, Ministry of Housing, Communities & Local Government
  (English Indices of Deprivation 2019).

There are no fees, no personal data, and no redistribution restrictions that affect
this project. **[YOUR WORDS: confirm you have checked the licence page and add the
retrieval date.]**

### 1.4 Interest and research questions
*(Criterion: interest; research questions justify a DB approach)*

**[YOUR WORDS: one paragraph on why this interests you personally.]** The dataset is
interesting because it links a consumer-facing safety metric to a social one, and
answering that link requires *joining two independently-published datasets on a key
that does not exist* — a database problem, not a spreadsheet or ML one.

Questions a database can answer (each needs joins/aggregation across tables, so a
relational approach is justified over sorting a sheet, and it is descriptive rather
than predictive so it is not an ML task):

- **Q1.** Do average hygiene ratings vary by **region**?
- **Q2.** Which **local authorities** score best/worst, and is score tied to place?
- **Q3.** Do **more deprived** areas have **lower** hygiene ratings? (the cross-dataset join)
- **Q4.** Which **business types** score best/worst?
- **Q5.** How **recent** are inspections, and how many premises await a first one?

---

## Stage 2 — Model the data

### 2.1 Entities, attributes and the E/R model
*(Criterion: E/R model identifies all fields and entities)*

Five entities:
- **region** (`region_id` PK, `region_name`)
- **business_type** (`business_type_id` PK, `business_type_name`)
- **local_authority** (`la_code` PK, `name`, `region_id` FK, `lad_code`)
- **establishment** (`fhrs_id` PK, `business_name`, `business_type_id` FK,
  `post_code`, `rating_value`, `rating_numeric`, `rating_date`, `la_code` FK,
  `scheme_type`, `hygiene_score`, `structural_score`, `confidence_score`,
  `longitude`, `latitude`)
- **imd_lad** (`lad_code` PK, `lad_name`, `imd_avg_score`, `imd_rank`)

Relationships:
- region **1—m** local_authority (*located in*)
- local_authority **1—m** establishment (*regulates*)
- business_type **1—m** establishment (*categorises*)
- local_authority **1—1 (optional)** imd_lad (*maps to*) — **no enforced FK** (see §2.3)

### 2.2 E/R diagram (Chen notation)
*(Criterion: diagram is clear, legal, ellipse/rhombus/rectangle notation)*

**[INSERT DIAGRAM: your Chen-style E/R diagram — rectangles for the five entities,
ellipses for attributes with primary keys underlined, rhombi for the four
relationships, cardinalities on the connecting lines.]**

> Note for the diagram: the version reviewed showed only the **key** attribute per
> entity. For full marks either (a) draw *all* attributes as ellipses, or (b) state
> explicitly that it is a key-only overview and list the remaining attributes in the
> text (as in §2.1). Also confirm the `business_type_id` ellipse connects to
> `business_type`.

### 2.3 E/R → relational mapping (resolving relational issues)
*(Criterion: modelling clear/sensible; relational issues resolved)*  **[EXPANDED]**

The model is entirely **one-to-many** — there are no many-to-many relationships, so
no junction tables are needed and every relationship maps to a foreign key on the
"many" side. Two points need care for the relational model:

1. **The `local_authority`–`imd_lad` link has no shared key and is *optional*.**
   FHRS identifies authorities by name; IoD uses ONS district codes. There is no
   common key, so the link is realised as a nullable `lad_code` column populated by
   **fuzzy name-matching** (§3.2), *not* an enforced foreign key. If it were a hard
   FK, the 74 authorities that cannot match (Scotland/Wales/NI, which the English
   index does not cover, plus post-2019 boundary changes and port health
   authorities) would be rejected on insert. Modelling it as a plain nullable
   column keeps the match best-effort and preserves those rows with `lad_code =
   NULL`.
2. **Scheme differences.** Scotland uses FHIS (pass/fail) rather than the 0–5 FHRS
   scale. The relational model represents this faithfully by keeping the raw
   `rating_value` text and leaving `rating_numeric` NULL for non-numeric values, so
   averages ignore them automatically.

No structure is incompatible with the relational model, so a **single** diagram
suffices; the only adjustment from a "pure" E/R reading is demoting the `maps to`
relationship to an unenforced link for the reason above.

### 2.4 Normalisation analysis
*(Criterion: analysis clear, explicit, accurate; at least 3NF)*  **[NEW — was missing]**

- **1NF.** All columns are atomic; there are no repeating groups (addresses are not
  modelled as multiple columns in this schema). ✔ In 1NF.
- **2NF.** Every table has a **single-column** primary key, so there are no partial
  dependencies on part of a composite key. ✔ In 2NF.
- **3NF / BCNF — two functional dependencies to examine on `establishment`:**
  - `rating_value → rating_numeric` — the numeric rating is fully determined by the
    text rating (`'5'`→5, `'AwaitingInspection'`→NULL). Since `rating_value` is a
    non-key attribute, this is a transitive dependency `fhrs_id → rating_value →
    rating_numeric` and therefore a **3NF/BCNF violation**.
  - `la_code → scheme_type` — every establishment in an authority shares that
    authority's scheme (FHRS/FHIS), so `scheme_type` depends on `la_code`, not
    directly on `fhrs_id`: another transitive dependency.

**Decision.** **[YOUR WORDS — pick one and defend it:]**
  - *(a) Normalise to BCNF:* extract `rating_type(rating_value PK, rating_numeric)`
    and drop `rating_numeric` from `establishment`; move `scheme_type` onto
    `local_authority` (where it depends on the key). After this every determinant is
    a candidate key → **BCNF**, and joining back reproduces all rows losslessly. This
    is the cleaner design.
  - *(b) Keep the current form and justify it:* `rating_numeric` is a controlled,
    derived convenience column and `scheme_type` is denormalised onto the fact table
    for single-table query simplicity and speed; both are maintained solely by the
    loader, so the update-anomaly risk normalisation guards against does not arise in
    a load-once snapshot.

State which you chose. The database is at least in **3NF** once (a) is applied, or is
a **deliberate, justified denormalisation from BCNF** under (b) — either satisfies
"at least 3NF" provided the reasoning is explicit.

**No 4NF issue:** no table holds two independent multi-valued facts.

---

## Stage 3 — Create the database

### 3.1 CREATE commands
*(Criterion: accurately implement the model; sensible types/keys/constraints)*

Full script: `createDBTables.sql`. Design notes: InnoDB is the MySQL 8.0 default so
`ENGINE=` is omitted; `rating_value` keeps the raw text while `rating_numeric` holds
the clean 0–5 (NULL otherwise) so averages stay honest; `rating_date` is nullable to
mean "never inspected"; `lad_code` is a plain nullable column (see §2.3).

```sql
USE foodHygeine;

-- Drops the children before parents, or the foreign keys block the drops, and it errors
DROP TABLE IF EXISTS imd_lad;
DROP TABLE IF EXISTS establishment;
DROP TABLE IF EXISTS local_authority;
DROP TABLE IF EXISTS business_type;
DROP TABLE IF EXISTS region;

CREATE TABLE region (
  region_id   INT AUTO_INCREMENT PRIMARY KEY, -- made-up id, auto-numbered
  region_name VARCHAR(40) NOT NULL UNIQUE     -- EX London, can't repeat
);

CREATE TABLE business_type (
  business_type_id   INT PRIMARY KEY,          -- the FSA's own id for the type
  business_type_name VARCHAR(120) NOT NULL     -- EX Restaurant/Cafe/Canteen
);

CREATE TABLE local_authority (
  la_code   VARCHAR(10) PRIMARY KEY, -- council code, EX 501
  name      VARCHAR(120) NOT NULL,
  region_id INT NOT NULL,            -- which region this council sits in
  lad_code  VARCHAR(10) NULL,        -- deprivation district, filled in later by name-matching
  CONSTRAINT fk_la_region FOREIGN KEY (region_id) REFERENCES region(region_id)
);

CREATE TABLE establishment (
  fhrs_id          BIGINT PRIMARY KEY, -- unique id from the FSA
  business_name    VARCHAR(255),
  business_type_id INT,
  post_code        VARCHAR(20),
  rating_value     VARCHAR(30),        -- '0'-'5', or 'AwaitingInspection', 'Pass', etc
  rating_numeric   TINYINT NULL,       -- 0-5 when numeric, else NULL
  rating_date      DATE NULL,          -- NULL = awaiting first inspection
  la_code          VARCHAR(10) NOT NULL,
  scheme_type      VARCHAR(10),
  hygiene_score    SMALLINT NULL,      -- 0 is best, higher is worse
  structural_score SMALLINT NULL,
  confidence_score SMALLINT NULL,
  longitude        DECIMAL(9,6) NULL,
  latitude         DECIMAL(8,6) NULL,
  CONSTRAINT fk_est_la   FOREIGN KEY (la_code)          REFERENCES local_authority(la_code),
  CONSTRAINT fk_est_type FOREIGN KEY (business_type_id) REFERENCES business_type(business_type_id),
  KEY idx_est_la     (la_code),
  KEY idx_est_type   (business_type_id),
  KEY idx_est_rating (rating_numeric)
);

CREATE TABLE imd_lad (
  lad_code      VARCHAR(10) PRIMARY KEY, -- ONS district code, e.g. E09000002
  lad_name      VARCHAR(120),
  imd_avg_score DECIMAL(8,3),            -- higher = more deprived
  imd_rank      INT                      -- 1 = most deprived district
);
```

Least-privilege web user (`makeUser.sql`) — the app only ever gets `SELECT`:

```sql
CREATE USER IF NOT EXISTS 'fhrs_read'@'localhost' IDENTIFIED BY 'readonly';
GRANT SELECT ON foodHygeine.* TO 'fhrs_read'@'localhost';
FLUSH PRIVILEGES;
```

A write attempt by the app user is refused at the database, not just in the app:
`ERROR 1142 (42000): DELETE command denied to user 'fhrs_read'@'localhost'`.

### 3.2 Entering the instance data
*(Criterion: detail how data was added; enough that all tables/fields used repeatedly)*

`DownloadingMoreData.js` fetches the authority list, then downloads **all 363**
authority XML files via `curl` (with retry/back-off, and a `curl` shell-out so it
works behind the lab's HTTPS proxy where Node's `fetch` does not). `LoadData.js`
then, in one run:
1. inserts distinct **regions**, reads back their generated ids;
2. inserts **local authorities** pointing at those region ids;
3. parses every XML with `fast-xml-parser`, collecting **business types** and
   **establishment** rows, keeping only authorities we selected (referential
   integrity), de-duplicating on `fhrs_id`, and bulk-inserting in 2,000-row batches;
4. downloads IoD 2019 File 10 (`xlsx`), loads **`imd_lad`**, and matches each
   authority to a district by **normalised name** + a small alias table.

Loaded counts (from the run):
```
regions:                12
business types:         14
imd_lad districts:     317
local authorities:     363   (289 matched to a deprivation district)
establishments:    609,914   (608,755 after cleaning)
```

**The awkward join (name reconciliation).** With no shared key, the loader
normalises names (lower-case; strip "City of"/"Borough of"; `&`→`and`; de-hyphenate)
plus a two-entry alias table (`Blackburn`→`Blackburn with Darwen`,
`Hull City`→`Kingston upon Hull`). This resolves **289 of 363**. The 74 unmatched
are **not errors**: ~60 are Scotland/Wales/NI (outside the English index), two are
**port health authorities** with no resident population (River Tees, Hull and Goole
Port), and the rest are **post-2019 unitary authorities** (e.g. Cumberland,
Buckinghamshire) that did not exist when IoD 2019 was published.

All five tables are populated and every field is exercised across hundreds of
thousands of rows.

### 3.3 Reflection: how well does the database reflect the data?
*(Criterion: critical reflection tied to the research questions)*

**Well:** the grain is right (one row per establishment matches the source); FHRS
IDs are naturally unique so the PK needs no surrogate; keeping `rating_value` (text)
+ `rating_numeric` (clean) loses nothing yet makes aggregation trivial; nullable
`rating_date` turns "awaiting inspection" into a countable state; foreign keys held
with zero violations across 609k rows.

**Less well:** deprivation is only at **authority** grain (LSOA-level would need the
big ONS postcode→LSOA file), so within-authority variation is invisible — the single
biggest fidelity gap, and it caps how sharply Q3 can be answered. Scotland's FHIS has
no 0–5 rating, so every numeric analysis is implicitly England/Wales/NI only.
**[YOUR WORDS: add one more point of your own.]**

### 3.4 Questions answered in SQL
*(Criterion: queries correct and reflect the identified questions)*

Full runnable script: `analyzeDeprivation.sql`. Headline results (full dataset):

**Q1 — ratings by region.** A gradient from the South West / Northern Ireland at the
top to London at the bottom.

| Region | Avg rating | % rated 5 | Avg hygiene (0=best) |
|---|--:|--:|--:|
| Northern Ireland | 4.773 | 83.6 | 2.32 |
| South West | 4.766 | 84.5 | 2.73 |
| … | | | |
| West Midlands | 4.579 | 75.4 | 3.16 |
| **London** | **4.456** | **68.3** | **3.56** |

**Q2 — best/worst authorities.** Best are small rural/county districts (Bassetlaw
4.96, Dorset 4.94); worst are dominated by London boroughs. Location matters.

**Q3 — deprivation vs hygiene.** Across the **289** matched English authorities,
Pearson **r = −0.377** (more deprived → lower ratings), with a clean monotonic
decline by quintile:

| Deprivation quintile | Avg rating | % rated 5 |
|---|--:|--:|
| 1 – least deprived | 4.730 | 82.2 |
| 2 | 4.727 | 82.1 |
| 3 | 4.665 | 79.4 |
| 4 | 4.605 | 75.6 |
| 5 – most deprived | 4.554 | 73.9 |

Real but **modest** (r² ≈ 0.14 — deprivation explains ~14% of the variation), and
statistically significant (t ≈ −6.9, p < 0.001).

**Q4 — business types.** The strongest single signal: schools/hospitals/supermarkets
top (avg ≈ 4.8–4.9), **independent takeaways worst** (4.331, only 61% rated 5).

**Q5 — recency.** **[YOUR WORDS: fill from your `awaiting_inspection` figure — the
stats endpoint reported 69,291 awaiting a first inspection.]**

---

## Stage 4 — The web application

### 4.1 The application
*(Criterion: app runs; DB interaction; appropriate privileges; goals satisfied)*

`webapp/server.js` is an Express app that connects over the local socket with the
**`SELECT`-only** `fhrs_read` account — the correct privilege for a query-only tool
and a hard stop on writes. All parameterised endpoints use `mysql2` named
placeholders; the connection is a small pool. The single-page UI
(`webapp/public/index.html`) uses **relative** fetch paths (so it works behind the
lab's port-proxy) and renders: headline stats, ratings by region, the deprivation
gradient + correlation, a **scatter plot with regression line and significance test**
(Chart.js), ratings by business type, an authority leaderboard with a region filter,
and an establishment search box.

```
Endpoints: /api/stats  /api/regions  /api/deprivation  /api/deprivation-points
           /api/business-types  /api/authorities  /api/search
```

Each endpoint maps to a Stage-1 question: `/api/regions`→Q1, `/api/authorities`→Q2,
`/api/deprivation`+`/api/deprivation-points`→Q3, `/api/business-types`→Q4.

### 4.2 Screenshots
*(Criterion: screenshots of main screens in the report)*

**[SCREENSHOT: the main dashboard — stat tiles + region table.]**
**[SCREENSHOT: the deprivation scatter plot with the trend line and the r / r² / t line.]**
**[SCREENSHOT: the establishment search returning results.]**

---

## Referencing and code provenance
*(Criterion: clear referencing of data, literature and code)*  **[NEW — required]**

**Data.** FSA Food Hygiene Ratings open data and the FSA authorities API (© Crown
copyright, OGL v3.0). English Indices of Deprivation 2019, File 10 (© Crown
copyright, MHCLG, OGL v3.0). URLs in §1.1.

**Libraries.** `express`, `mysql2`, `fast-xml-parser`, `xlsx` (npm); `Chart.js`
(vendored locally) for the scatter plot.

**Code provenance.** **[YOUR WORDS — fill the right-hand column honestly. Since this
is your own prior work, most will be "written by me"; mark anything you adapted from
docs/examples.]**

| File | Author / origin |
|---|---|
| `checkDB.js` | [written by me / adapted from …] |
| `createDBTables.sql` | [written by me] |
| `makeUser.sql` | [written by me] |
| `DownloadingMoreData.js` | [written by me] |
| `LoadData.js` | [written by me; `norm()` regex approach based on …] |
| `clean.js` | [written by me] |
| `analyzeDeprivation.sql` | [written by me; Pearson formula per standard definition] |
| `webapp/server.js` | [written by me] |
| `webapp/public/index.html` | [written by me; Chart.js is third-party] |

---

## Discretionary extra credit (highlight these)
*(Up to 15% for work beyond the basic requirements)*

- **Data cleaning with a reversible audit trail** — `clean.js` quarantines the 1,159
  impossible (pre-2006-date) rows into `establishment_rejects` *with a reason and
  timestamp* before deleting, so cleaning is transparent and reversible, and writes
  a `report-cleaning.md`.
- **Dataset alignment / name reconciliation** — normalising two datasets with no
  shared key from 262→289 matches, and *documenting why the remaining 74 legitimately
  cannot match* rather than forcing bogus joins.
- **Statistical rigour in the app** — not just the Pearson r, but an in-page
  regression, r², and a t-test verdict (p < 0.001) with a scatter plot, so the claim
  is shown to be significant-but-modest rather than asserted.
