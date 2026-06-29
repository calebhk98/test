# Food Hygiene Ratings vs. Deprivation

A MySQL database and a small read-only Node.js web app that join the UK **Food
Standards Agency Food Hygiene Ratings** (FHRS/FHIS open data) to the **English
Indices of Deprivation 2019**, to ask: *do hygiene scores vary by region, business
type and deprivation?*

**The full write-up — schema, methodology, reflections and findings — is in
[`report/REPORT.md`](report/REPORT.md).**

## Headline findings (608,982 establishments, 363 authorities)

* **Region matters:** London is a clear outlier (avg rating 4.46 / 68% top-rated)
  vs. the South West & Northern Ireland (~4.77 / ~84%).
* **Deprivation matters, moderately:** Pearson **r = −0.378** across 289 English
  authorities; most-deprived quintile averages 4.55 vs. 4.73 for the least.
* **Business type matters most:** schools 4.90, **takeaways 4.33** (only 61% top-rated).
* **Recency:** 11% await a first inspection; mean rating age 2.1 years.

## Layout

```
db/schema.sql        all CREATE statements
db/users.sql         fhrs_admin (loader) + fhrs_app (SELECT-only, used by the app)
etl/01_download.js   download 363 FHRS XML files (curl + retry)
etl/02_load.js       parse XML/xlsx and bulk-load into MySQL
db/schema_bcnf.sql   BCNF/4NF refinement (lossless decomposition, proven)
etl/04_clean.js      data cleaning: quarantine impossible rows, flag-and-keep incomplete ones
db/schema_geo.sql    additive: imd_lsoa + postcode tables (neighbourhood grain)
etl/00_download_geo.sh  fetch IoD File 7 + ONS postcode->LSOA lookup
etl/03_load_geo.js   load LSOA deprivation + resolve postcodes
queries/analysis.sql analytical queries answering the project questions
queries/analysis_geo.sql neighbourhood-level deprivation queries
webapp/              Express app + single-page UI (read-only)
report/REPORT.md     full report incl. reflections and results
report/EXTENDING.md  cardinality, normalisation, Excel option, useful datasets
report/GEO_ENRICHMENT.md  the LSOA datasets, recorded joins, coverage, findings
report/CLEANING_REPORT.md what the cleaning pass removed and flagged
```

## Run it

```bash
npm install
mysql < db/schema.sql
mysql < db/users.sql
node etl/01_download.js     # ~571 MB of source XML
node etl/02_load.js         # loads ~609k rows
node etl/04_clean.js        # quarantine impossible rows -> establishment_rejects (see report/CLEANING_REPORT.md)
node webapp/server.js       # http://localhost:3000

# Optional neighbourhood-level deprivation enrichment (see report/GEO_ENRICHMENT.md):
bash etl/00_download_geo.sh # IoD File 7 + ONS postcode->LSOA(2011) lookup
mysql < db/schema_geo.sql
node etl/03_load_geo.js
mysql food_hygiene < queries/analysis_geo.sql
```

Connection settings and credentials are in `config.js` (overridable via
`DB_*` environment variables). Built and tested on MariaDB 10.11 (MySQL-compatible)
and Node 22.

## Data sources

* FSA Food Hygiene Ratings open data — <https://ratings.food.gov.uk/open-data>
* FSA authorities & business-types APIs — `api.ratings.food.gov.uk`
* English Indices of Deprivation 2019 (File 10 LAD + File 7 LSOA) — <https://www.gov.uk/government/statistics/english-indices-of-deprivation-2019>
* ONS Postcode → OA(2011) → LSOA → MSOA → LAD best-fit lookup (Aug 2021) — Open Geography Portal item `3e265c6a114f425fbd92e863977e698a`

All sources are Open Government Licence v3.0. Exact download URLs are in
`etl/00_download_geo.sh` and `report/GEO_ENRICHMENT.md`.
