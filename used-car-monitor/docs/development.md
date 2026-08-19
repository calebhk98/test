# Data model, tests and layout

The database schema, the test suite, and where everything lives.

[← back to the README](../README.md)

---

## Data model

`listings` — one row per VIN: `vin` (PK), `first_seen`, `last_seen`, `year`, `make`, `model`,
`trim`, `body_type`, `fuel_type`, `city_mpg`, `highway_mpg`, `combined_mpg`, `mileage`,
`price_current`, `price_first_seen`, `dealer_name`, `dealer_city`, `dealer_state`,
`distance_miles`, `cpo`, `listing_url`, `score`, `score_breakdown`, `market_expected_price`,
`market_delta_pct`, `market_sample_size`, `market_grade`, `market_confidence`, `source`,
`active`, `updated_at`.

`model_reliability` — one row per make/model/year: complaint and recall counts, crash/fire
counts, injuries, deaths, the top five recurring complaint components, and recall campaign
details. `model_mpg` — cached EPA figures. Both are keyed by model-year, so fifty Civics cost
one lookup, and both carry `fetched_at` for cache expiry.

`price_history` — `vin`, `date`, `price`, `mileage`; appended on first sight and again
whenever price or mileage changes, so price drops are visible over time.

`api_usage` — one row per API call (month, endpoint, HTTP status) — this is the quota ledger.
`runs` — one row per daily job: counts, API calls used, digest path, errors.

Listings that stop appearing in results are marked `active = 0` (likely sold) rather than deleted.

---

## Tests

```bash
python3 -m unittest discover -s tests -t . -v    # or: python3 -m carmon selftest
```

391 tests covering scoring (including the 39,950-vs-40,050-vs-60,000 continuity requirement),
normalization and filtering, quota enforcement, upsert/history bookkeeping, NHTSA and EPA
enrichment (including NHTSA's habit of answering HTTP 400 with a valid "no recalls" body),
config single-source-of-truth guards, quota pacing maths, the month-end sweep, demo-data
expiry, the market fit (checked by generating a synthetic market with a known depreciation
rate and asserting the regression recovers it), digest rendering, both Discord transports and their payload limits, the CLI, every HTTP
endpoint, and the MCP protocol layer end-to-end. No test touches the network — MarketCheck,
Discord, NHTSA and EPA are all injected with fakes, and pace assertions use fixed dates so they
cannot rot.

## Layout

```
carmon/
  cli.py          config.py       db.py           digest.py
  marketcheck.py  nhtsa.py        fueleconomy.py  notify.py
  market.py       pipeline.py     quota.py        scoring.py
  settings.py     sources.py      demo.py         webapp.py
  mcp_server.py
  scrapers/       base.py (robots, caps, no-evasion) + seven adapters
config.json  requirements.txt  SPEC.md  SOURCES.md  docs/  deploy/  tests/
```

---

See also: [setup](setup.md) · [configuration](configuration.md)
