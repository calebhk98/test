# Extending the database & design notes

Answers to six follow-up questions: more questions the DB could answer, the Excel
pivot-table option, useful extra datasets, which datasets were used, the
cardinality of the model, and normalisation to BCNF/4NF.

---

## 1. Which datasets did I actually use?

| # | Dataset | Status | Role |
|---|---|---|---|
| 1 | FSA **FHRS/FHIS** open data (363 per-authority XML files) | **Used** | `establishment` fact table (608,982 rows) |
| 2 | FSA **authorities** API (JSON) | **Used** | region + the download URL for each authority |
| 3 | FSA **business-types** API (XML) | **Used** | `business_type` lookup |
| 4 | **IoD 2019 File 10** – LA-district summaries (XLSX) | **Used** | `imd_lad` deprivation table |
| 5 | **IoD 2019 File 7** – LSOA scores (CSV) | Downloaded, **not loaded** | needs a postcode→LSOA bridge to be joinable |
| 6 | ONS **postcode→LSOA/NSPL** lookup (the large geoportal file) | **Not used** | would unlock the LSOA-level join (see §3) |

So 4 of the 6 candidate sources are in the database; the two unused ones are
exactly what's needed to push deprivation analysis below LA level.

---

## 2. What else could the DB answer (with small additions)?

The current snapshot already supports region / type / recency / deprivation
questions. Cheap additions that unlock new questions:

* **Inspection *frequency* (not just recency).** Today only the *latest* rating
  date is stored, so "how often is a place inspected?" is unanswerable. Capturing
  periodic extracts into an `establishment_rating_history(fhrs_id, rating_date,
  rating_value, …)` child table turns the snapshot into a time series and answers
  *trends* ("are ratings improving?") and *re-inspection intervals*.
* **Per-capita questions.** A `population(lad_code, population)` table gives
  premises-per-1,000-people and lets you normalise "London has more takeaways"
  against population.
* **Which *facet* of deprivation drives the effect.** Load the IoD sub-domains
  (income, employment, crime, health, education, barriers, living environment —
  already present as separate sheets in File 10) into `imd_domain` to ask "is it
  *income* deprivation or *crime* that tracks hygiene?".
* **Spatial / "near me".** A spatial index on `(latitude, longitude)` enables
  radius queries; ~76 % of rows already have coordinates.
* **Convenience views & generated columns** — e.g. a `rating_age_days` generated
  column and a `v_region_summary` view so the app and pivot users don't re-derive
  the same aggregates.

---

## 3. What other datasets/tables would be useful?

| Dataset | Unlocks |
|---|---|
| **ONS Postcode Directory / NSPL** (postcode → LSOA, LAD, region, lat/long) | LSOA-level deprivation join; fixes the **280 postcodes that straddle LA boundaries**; fills the ~24 % missing coordinates |
| **IoD 2019 File 7 (LSOA)** + NSPL | Street-level deprivation and the seven sub-domains |
| **Census / ONS population** (LSOA or LAD) | Premises density, per-capita rates |
| **ONS LAD boundary-change lookup** | Resolves the **9 unmatched post-2019 unitary authorities** (Somerset, North Yorkshire, …) |
| **SIMD / WIMD / NIMDM** (Scotland, Wales, NI deprivation indices) | Extends the deprivation analysis beyond England |
| **ONS Rural–Urban Classification** | Tests "are rural areas really cleaner, or just less dense?" |
| **Companies House / brand data** | Chain vs. independent (the current data has no operator field) |

The recurring difficulty is the **join key**: FHRS uses authority *names*, ONS/IoD
use *codes*, and boundaries changed in 2019–2023 — which is why NSPL (a proper
postcode bridge) is the single highest-value addition.

---

## 4. Could a pivot table in Excel answer these questions?

**Partly.** The FHRS extract is 608,982 rows — under Excel's 1,048,576-row sheet
limit — so it loads, and a PivotTable handles the *single-table group-by*
questions well:

* **Q1 region averages, Q4 business-type averages, Q5 recency banding** → these are
  literally "group by X, average the rating", which is what a pivot does best.

Where a plain pivot table struggles or can't go:

1. **The cross-dataset join.** PivotTables don't join tables. Bringing in
   deprivation means `XLOOKUP`/Power Query against the IoD file on a *fuzzy
   authority name* — and the boundary mismatches would **silently drop rows**.
   You'd really use **Power Pivot (the Data Model)**, which supports table
   relationships and >1M rows, rather than a classic pivot.
2. **The correlation.** Pearson *r* is not a pivot aggregation — you'd build a
   one-row-per-LA helper sheet and use `CORREL()`. Quintile buckets need a `RANK`/
   `PERCENTILE` helper column (the SQL `NTILE` equivalent).
3. **Data cleaning.** Deriving the numeric 0–5 from mixed text/number values,
   treating "AwaitingInspection" as NULL, and excluding Scotland's pass/fail all
   happen *before* the pivot — easier in SQL than in cells.

**Verdict:** Excel/Power Pivot is fine for the descriptive breakdowns and is great
for non-technical exploration, but the multi-dataset join and the correlation are
where the relational database clearly wins.

---

## 5. Cardinality of the model

**Relationship cardinality — every relationship is one-to-many; there are no
many-to-many links**, which is why the model is a clean snowflake and normalises
without junction tables:

```
region (1) ───< local_authority (N)         12  ──< 363
imd_lad (1) ──< local_authority (N, optional) 317 ──< 289 matched   (effectively 1:1)
local_authority (1) ───< establishment (N)   363 ──< 608,982
business_type  (1) ───< establishment (N)     15 ──< 608,982
rating_type    (1) ───< establishment (N)     13 ──< 608,982   (after BCNF split)
```

**Data (column) cardinality** — relevant for indexing:

| Column | Distinct values | Cardinality |
|---|--:|---|
| `fhrs_id` | 608,982 | unique (PK) |
| `post_code` | 254,039 | very high |
| `la_code` | 363 | medium |
| `business_type_id` | 15 | low |
| `rating_value` | 13 | low |
| `region_id` | 12 | low |

A future many-to-many *would* appear if we added, say, allergen tags or
multiple inspection officers per premise — those would need junction tables.

---

## 6. Can we get it to BCNF / 4NF?  Yes — and it's done.

I tested the candidate functional dependencies against all 608,982 rows:

| Dependency | Holds? | Implication |
|---|---|---|
| `rating_value → rating_numeric` | **Yes** (0 exceptions) | `rating_numeric` depends on a non-key → **BCNF violation** |
| `la_code → scheme_type` | **Yes** (0 exceptions) | `scheme_type` transitively depends on the key → **3NF/BCNF violation** |
| `post_code → la_code` | **No** (280 postcodes span 2+ LAs) | correctly *not* enforced |
| `rating_value → scheme` | **No** (`Exempt` is in both schemes) | scheme must come from the LA, not the rating |

**The fix** (`db/schema_bcnf.sql`), a lossless decomposition:

* Extract **`rating_type(rating_value PK, rating_numeric, status_category)`** and
  drop `rating_numeric` from the fact table — removes `rating_value → rating_numeric`.
* Drop `scheme_type` from `establishment` (it already lives on `local_authority`,
  where it depends on the key) — removes the transitive dependency.

After this, the only determinant in every table is a candidate key → **BCNF**.
No table holds two independent multi-valued facts → **4NF**.

**Proof it's lossless:** reconstructing the original rows by joining
`establishment → rating_type` and `establishment → local_authority` reproduces all
608,982 rows with **0 mismatches**, and the fact table shrank from **250 MB to
124 MB** by removing the redundancy.

> Note: the four `address_line*` columns are atomic (so 1NF holds) but are a
> repeating-group *smell*; splitting them into an `address` table would be a
> modelling nicety, not a normal-form requirement.
