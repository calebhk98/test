# Configuration and scoring

What every setting does, how scoring works, and how to change it all safely.

[← back to the README](../README.md)

---

## Configuration (`config.json`)

Nothing about the search is hardcoded. The defaults match the spec:

```jsonc
"search": {
  "zip": "38464", "radius_miles": 100,       // free tier caps radius at 100
  "year_min": 2021, "mileage_max": 60000, "price_max": 20000,
  "body_types": ["Sedan","Hatchback","SUV","Wagon","Coupe"],
  "exclude_body_types": ["Pickup","Truck","Van","Minivan", …],
  "exclude_models": ["Tahoe","Suburban","Highlander", …],   // keeps "small SUV" small
  "include_electric_hybrid": false,           // ← the toggle; off by default
  "max_pages": 5, "certified_max_pages": 2
}
```

Filters are applied both in the API query *and* again locally after the response, because
body/fuel vocabularies vary between feeds.

### Scoring

`scoring.mode` picks between two deterministic (non-LLM) scorers:

**`step`** — the spec's rules exactly: +2 preferred, −2 caution unless CPO, +2 CPO,
+1 any price drop, −1 per 25 miles past 50, −1 if mileage > 40,000.

**`smooth`** (default) — the same rules made continuous, so a 39,950-mile car isn't
suddenly a full point better than a 40,050-mile one:

| Component | Rule |
| --- | --- |
| Preferred model | +2 (Corolla, Civic, Elantra, Mazda3, Forte) |
| Caution model | −2 (Versa, Sentra, Altima — CVT history), waived to 0 if CPO |
| CPO | +2 |
| Price drop | ramps 0 → +1.5, full bonus at a 3% drop since `first_seen` |
| Distance | −1 per 25 mi beyond 50 mi, continuous, floored at −3 |
| Mileage | linear ramp: 0 at 20,000 mi → **−1.00 at 40,000 mi** → −2.00 at 60,000 mi |
| Price | ramps 0 at the budget ceiling ($20,000) → +1.5 at $12,000 |
| Model year | ramps 0 at the oldest year you accept (2021) → +1.0 at 2025 |
| Fuel economy | ramps 0 at 28 mpg combined → +1.0 at 40 mpg, mildly negative below (floor −0.5) |
| NHTSA complaints | ramps 0 at 100 complaints → −1.5 at 600 for that model-year |
| NHTSA recalls | −0.15 per recall campaign, floored at −0.75 |
| vs market | up to ±1.5 — full value at 12% below/above the expected price for that mileage and year; 0 until 6+ comparables exist (see §10) |

MPG comes from MarketCheck's `build.city_mpg`/`highway_mpg` when present, otherwise from EPA
(combined = 55% city + 45% highway, the EPA's own weighting). A model-year with no NHTSA data
scores **0** for both reliability components — unknown is neutral, never a penalty.

The mileage ramp is calibrated so 40,000 miles still costs exactly −1 (the spec's anchor),
while 39,950 vs 40,050 differ by 0.005 and 60,000 is a full point worse than 40,000.

**Every component is stored and shown** — `score_breakdown` in the DB, a "why:" line in the
digest, a breakdown table on each listing page, and the `explain_score` MCP tool. After
editing weights, run `python3 -m carmon rescore` to recompute stored scores.

### Configuration: two files, no third place

There are exactly two places anything is configured, and they never overlap:

| File | Holds | Committed? |
| --- | --- | --- |
| `config.json` | everything about the search, scoring, quotas, paths, ports | yes — it has no secrets |
| `.env` | **only** secrets: `MARKETCHECK_API_KEY`, `DISCORD_WEBHOOK_URL`, `CARMON_API_TOKEN` | **no** — gitignored |

`.env` is not a general config file — it holds secrets and nothing else, and it is created
for you: the first `carmon` command writes a blank, documented, `chmod 600` copy listing every
secret with a link to where to get it. There is no example file to copy, which also means the
documentation cannot drift from the code — the template is generated from the same table the
settings page renders. Real environment variables override the file, so
`MARKETCHECK_API_KEY=... python3 -m carmon run` works in CI or a container with no file at all.
A test asserts that no key resembling a secret ever appears in `config.json`.

**Single source of truth.** Values that must agree are defined once and derived, not repeated.
Three scoring weights are written as `"auto"` in `config.json` and resolved from the search
criteria at load time:

| Weight | Derived from |
| --- | --- |
| `price_no_bonus_at` | `search.price_max` |
| `mileage_full_penalty_at` | `search.mileage_max` |
| `year_no_bonus_at` | `search.year_min` |

Change your budget from $20,000 to $15,000 and the price component's zero point moves with it —
no second edit, no drift. The same applies outward: the cross-shopping links, the digest header,
the MarketCheck query and the client-side filters are all built from that one `search` block.

`python3 -m carmon config-check` (also run automatically before every daily job) reports
typo'd weight keys, an unrecognised scoring mode, a radius or call cap above the free tier, and
any hardcoded number that has drifted from the search criteria it is supposed to track.

---

## Changing settings from the website

The **Settings** page edits `config.json` and `.env` in place, so the search criteria, scoring
weights, quotas, Discord transport and scraper switches can be changed without a text editor.

```
GET  /api/settings            → every editable key with its current value and type, plus which
                                secrets are set (masked — never the value)
POST /api/settings            → {"changes": {"search.zip": "37211"}}
POST /api/settings/secrets    → {"changes": {"MARKETCHECK_API_KEY": "…"}}
POST /api/scrapers/toggle     → {"source": "repairpal", "enabled": true}
```

Because that page can hand out credentials and start network activity, the rules around it are
deliberately strict:

* **Type-locked, key-locked.** A key must already exist in `config.json` and the new value must
  be the same JSON type. New keys, new sections and type changes are refused, so the file can
  never be bent into a shape the rest of the code does not expect.
* **`paths` is not editable over HTTP at all.** Repointing the database is a filesystem
  decision, not a web-form one.
* **All or nothing.** A batch with one bad value changes nothing, and the file is validated
  before it is replaced. The previous version is archived to `data/config-history/` and swapped
  atomically, so a crash mid-write cannot leave half a config.
* **Secrets are write-only.** Reading them returns "set / not set" and the last four characters.
  `.env` is rewritten with `chmod 600`, comments preserved.
* **Writes need more than a URL.** They must be POST, carry an `X-Carmon-Write` header (or a
  form confirmation field), pass the same-origin check, and present the bearer token when
  `CARMON_API_TOKEN` is set. On a non-loopback bind with no token, writes are refused outright
  — a dashboard reachable from your network must not hand out API keys anonymously.

The MCP server can *read* settings (masked) and see scraper health, but cannot change either.
Editing configuration is a human action, on the website or in the file.

---

Next: [judging a deal](market-analysis.md) · [website, API and MCP](interfaces.md)
