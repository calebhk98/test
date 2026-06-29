# Data-cleaning report

Run at: 2026-06-29 02:47:03 UTC

| | rows |
|---|--:|
| establishments before | 608982 |
| **removed (quarantined)** | **1165** |
| establishments after | 607817 |
| total rows in establishment_rejects | 1165 |

## Rules that REMOVE rows (impossible / corrupt data)

Matching rows are copied to `establishment_rejects` with the reason, then deleted.

| rule | what it catches | removed |
|---|---|--:|
| `empty_business_name` | Business name is null or blank (no identity) | 0 |
| `empty_rating_value` | Rating value is null or blank | 0 |
| `impossible_future_date` | Rating date is in the future (after today) | 0 |
| `pre_scheme_date` | Rating date predates any scheme existing (< 2006; FHIS began 2006, FHRS 2010) | 1165 |
| `coords_outside_uk` | Geocode falls outside the UK bounding box (lat 49.8-60.9, long -8.65-1.77) | 0 |
| `invalid_component_score` | Component score outside the permitted FHRS values (hygiene/structural (0,5,10,15,20,25), confidence (0,5,10,20,30)) | 0 |

## Rules that FLAG rows (incomplete but legitimate — KEPT)

| rule | why it is kept | count |
|---|---|--:|
| `missing_postcode` | No postcode — valid for some premises (e.g. mobile caterers) but cannot be geo-joined | 102330 |
| `awaiting_first_inspection` | No rating date because the premise is awaiting its first inspection (legitimate) | 68463 |
| `numeric_rating_without_scores` | FHRS premise has a 0-5 rating but no component scores recorded | 5508 |
| `fhrs_date_pre_rollout` | FHRS rating date between 2006 and the 2010 national rollout (suspect, retained) | 1012 |

## Examples of removed rows

**`pre_scheme_date`**

| fhrs_id | business_name | post_code | rating_value | rating_date | scheme | lat | long |
|---|---|---|---|---|---|---|---|
| 18737 | Regency Filling Station | AB55 4AL | Exempt | 1993-12-01 | FHIS | 57.444756 | -3.126918 |
| 20043 | St Mary's Lodge | IV32 7QE | Pass | 1995-08-24 | FHIS | 57.571598 | -3.150950 |
| 1952923 | Cruachan Caravan Park Reception Shop | FK21 8TY | Pass | 1996-07-30 | FHIS |  |  |
| 560817 | Achmore Village Hall | IV53 8UT | Exempt | 1996-10-22 | FHIS | 57.341414 | -5.566806 |
| 1952903 | Cartwheel Inn | PH10 6ND | Pass | 1997-08-25 | FHIS | 56.592097 | -3.337463 |

## How to inspect or reverse

```sql
-- everything that was removed, with reasons
SELECT reject_reason, COUNT(*) FROM establishment_rejects GROUP BY reject_reason;

-- the per-run rule log
SELECT * FROM cleaning_log ORDER BY log_id;

-- restore one row if a removal was wrong
-- INSERT INTO establishment (<cols>) SELECT <cols> FROM establishment_rejects WHERE fhrs_id = ?;
```
