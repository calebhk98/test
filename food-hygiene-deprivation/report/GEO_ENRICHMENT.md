# Neighbourhood-level enrichment (extra open datasets + recorded joins)

This extends the database with two more **open** datasets so deprivation can be
measured at the **neighbourhood (LSOA, ~1,500 residents)** level instead of the
whole local authority. Everything here is reproducible on a clean machine — the
exact source URLs, the load steps and every join are recorded.

## Datasets added (both open, citable, versioned)

| Table | Source dataset | URL | Licence |
|---|---|---|---|
| `imd_lsoa` | **English Indices of Deprivation 2019 — File 7** (all scores/ranks/deciles + population, per 2011 LSOA) | gov.uk → `assets.publishing.service.gov.uk/media/5dc407b440f0b6379a7acc8d/File_7_-_All_IoD2019_Scores__Ranks__Deciles_and_Population_Denominators_3.csv` | Open Government Licence v3.0 |
| `postcode` | **ONS "Postcode → OA(2011) → LSOA → MSOA → LAD" Best-Fit Lookup, August 2021** | Open Geography Portal item `3e265c6a114f425fbd92e863977e698a` → `arcgis.com/sharing/rest/content/items/3e265c6a114f425fbd92e863977e698a/data` | Open Government Licence v3.0 |

**Why these exact versions:** IoD 2019 is published on **2011 LSOAs**, so the
postcode lookup must also use 2011 LSOAs — hence the August-2021 lookup (a 2021/22
release switches to 2021 LSOAs and would silently fail to join). Choosing
compatible *vintages* is the single most important reproducibility decision here.

## Reproduce on a fresh environment

```bash
# (after the base build in README.md)
bash etl/00_download_geo.sh        # fetches File 7 + the 24 MB postcode zip
mysql < db/schema_geo.sql          # CREATE imd_lsoa, postcode; ALTER establishment
node etl/03_load_geo.js            # load 32,844 LSOAs + resolve postcodes
mysql food_hygiene < queries/analysis_geo.sql
```

## The recorded join chain

The bridge from a food premise to its neighbourhood's deprivation is two equi-joins:

```sql
establishment e
  JOIN postcode p ON e.postcode_norm = p.postcode_norm   -- premise's postcode -> ONS record
  JOIN imd_lsoa l ON p.lsoa11cd      = l.lsoa11cd         -- that postcode's 2011 LSOA -> IMD
```

* `establishment.postcode_norm` is a **stored generated column**
  `UPPER(REPLACE(post_code,' ',''))` (defined in `db/schema_geo.sql`); `postcode`
  is normalised the same way at load time. Normalisation is required because FHRS
  and ONS punctuate/space postcodes differently.
* `imd_lsoa` is **England-only**. Scottish/Welsh/NI postcodes resolve to an LSOA
  in `postcode` but have **no** `imd_lsoa` row, so they drop out of the deprivation
  join — they are never given a fabricated score.

## Coverage (nothing invented — unmatched stays unmatched)

| Step | Count | Note |
|---|--:|---|
| Distinct establishment postcodes | 253,697 | |
| …resolved in the ONS lookup | 251,763 | **99.2 %**; remainder are terminated/invalid/Crown-dependency postcodes |
| Establishments with a postcode match | 503,731 | of 608,982 |
| **Rated** establishments with LSOA deprivation | **369,767** | the analysis base (English, rated, postcode-resolved) |

## What the finer grain reveals

**1. The deprivation→hygiene gradient is cleaner and monotonic at neighbourhood
level** (IMD decile 1 = most deprived 10%):

| IMD decile | Avg rating | % rated 5 |
|---|--:|--:|
| 1 – most deprived | 4.453 | 69.2 |
| 5 | 4.643 | 77.5 |
| 10 – least deprived | 4.725 | 81.6 |

**2. Which *facet* of deprivation tracks hygiene?** Per-premise Pearson *r*:

| Domain | r |
|---|--:|
| Crime | −0.111 |
| Income | −0.109 |
| IMD overall | −0.104 |
| Living environment | −0.083 |
| Employment | −0.074 |
| Health / Education | ≈ −0.06 |
| Barriers to housing | −0.038 |

Crime and income deprivation track hygiene most; housing barriers least.

> **A statistics lesson worth noting:** the per-premise correlation (−0.10) is
> much weaker than the per-**local-authority** correlation (−0.38 in
> `queries/analysis.sql`). That is the *ecological correlation* effect —
> aggregating to areas averages out individual noise and inflates *r*. The
> neighbourhood figure is the more honest measure of how much a single premise's
> rating is explained by where it sits.

**3. Deprived neighbourhoods have far more food outlets** ("food-swamp" effect) —
premises per 1,000 residents falls from **9.45** (most deprived decile) to **4.36**
(least deprived), more than 2×. This reframes question 1: London/deprived areas
don't just rate lower, they have many *more* premises (and more takeaways, the
worst-rated type) per head.

## New questions this unlocks

* Income vs. crime vs. education as predictors of hygiene (done above).
* Food-outlet density per capita by area (done above) → "food deserts/swamps".
* Per-domain decile breakdowns for any business type (e.g. are takeaways in
  high-crime LSOAs worse than takeaways elsewhere?) — all reachable from the same
  three-table join.
