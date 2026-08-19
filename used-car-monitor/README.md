# Used Car Daily Monitor

A small daily job that searches MarketCheck's Inventory Search API for used cars matching
your criteria, enriches them with free federal NHTSA complaint/recall data and EPA fuel
economy, stores everything in SQLite (dedup'd by VIN), tracks price and mileage changes over
time, scores every listing deterministically, and then tells you about it four ways:

| Output | Command | What it is |
| --- | --- | --- |
| **Daily digest** | `python3 -m carmon run` | Markdown file: new listings, price drops, top 5 by score |
| **Discord message** | same run, or `python3 -m carmon notify` | Sent as a **direct message**, or to a server webhook |
| **Website** | `python3 -m carmon serve` | Browse/filter listings, see score breakdowns and price history |
| **JSON API** | same server, `/api/*` | Everything the website shows, as JSON |
| **MCP server** | `python3 -m carmon mcp` | Tools so Claude (or any MCP client) can query your data |
| **Deal check** | `python3 -m carmon appraise` / `market` / `deals` | Is this price good? Where is the market heading? |
| **Scrapers** | `python3 -m carmon scrape` | Optional, off by default, hard-capped (see §11) |

Python 3.11+, one runtime dependency (`requests`); everything else is standard library.

## Where the data comes from

| Source | Key needed? | What it gives | Cost |
| --- | --- | --- | --- |
| **MarketCheck** Inventory Search | **yes** (free tier) | the listings themselves | 500 calls/month, enforced |
| **NHTSA** Complaints & Recalls (`api.nhtsa.gov`) | **no** | consumer-filed defect complaints and manufacturer recall campaigns per model-year | free, unlimited, cached 30 days |
| **EPA** fueleconomy.gov | **no** | combined MPG when MarketCheck omits it | free, unlimited, cached 180 days |

NHTSA is real federal data — the same underlying dataset every third-party reliability site
repackages. It gives raw counts and descriptions, not a friendly 1–5 score, and it feeds two
components of every listing's score.

**It is looked up automatically.** Every daily run collects the distinct make/model/year
combinations it just fetched and, for any it has never seen before, calls NHTSA (and EPA for
MPG) right then — no separate step, no key, no MarketCheck quota consumed. Results are cached
per model-year, so fifty Civics cost one lookup and a model already known costs nothing. The
digest names each first-time lookup ("first NHTSA lookup: 2022 Kia Forte (31 complaints, 1
recall)"). `python3 -m carmon enrich` forces a refresh; `--force` ignores the cache.

That data then shows up everywhere: MPG and a `complaints / recalls` column on the dashboard,
a full Reliability section on each listing page (top components, each recall campaign, VIN
lookup link), `GET /api/reliability` and per-listing fields in the API, and the
`get_reliability` / `refresh_reliability` / `list_reliability` MCP tools. Neither free source counts against the MarketCheck quota,
and neither can break the daily run: if either is unreachable, the run logs it and carries on
with the last cached values.

> **Read complaint counts carefully.** They are *not* adjusted for sales volume — a 2022 Civic
> shows 878 complaints and a 2022 Corolla 95, partly because Honda sold a lot of Civics. The
> stronger signal is *which components recur* (729 of those Civic complaints are STEERING) and
> whether recalls are still unrepaired on the specific VIN. That is why the complaint weight is
> deliberately small and every listing page links the NHTSA VIN lookup.

RepairPal (repair cost, visit frequency, severity), Edmunds and KBB owner reviews have **no
public API** — Edmunds' is partner/business-only, not self-serve. They are deep links only,
alongside the retailers and aggregators; see [SOURCES.md](SOURCES.md).

---

## 1. Setup

```bash
cd used-car-monitor
python3 -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt

cp .env.example .env
```

### Get a MarketCheck API key (free tier)

1. Go to <https://www.marketcheck.com/apis> (developer portal: <https://docs.marketcheck.com>)
   and sign up for the **free plan**: 500 calls/month, 5 calls/sec, 100-mile radius cap, $0/mo.
2. Copy your key into `.env`:

   ```
   MARKETCHECK_API_KEY=your_key_here
   ```

`.env` is gitignored. Nothing in this repo ever writes your key to disk anywhere else, and
`GET /api/config` deliberately serves `config.json` only — secrets live exclusively in `.env`.

**The free tier is never silently exceeded.** Every API call is logged to the `api_usage`
table, the client refuses to start a request once `api.monthly_call_cap` (500) is reached,
requests are throttled to 5/sec, and a radius above 100 miles is clamped with a warning.
Usage shows up in the digest, on the website, and in `python3 -m carmon stats`.
Upgrading the plan means editing `api.monthly_call_cap` yourself — the code will not do it.

### Discord (optional): direct message or server channel

Pick one transport. `discord.mode` in `config.json` is `"auto"` — DM if a bot is configured,
webhook otherwise — or force it with `"dm"` / `"webhook"` (or `--mode` on the command line).

**(a) Direct message — no server channel.** The digest lands in your Discord DMs, like a
message from a friend.

1. <https://discord.com/developers/applications> → **New Application** → **Bot** → **Reset
   Token**, and copy the token into `.env` as `DISCORD_BOT_TOKEN`.
2. Discord Settings → **Advanced → Developer Mode**, then right-click your own name →
   **Copy User ID** → `.env` as `DISCORD_USER_ID`.
3. One unavoidable Discord rule: **a bot may only DM a user it shares a server with.** That
   is the platform's rule, not this project's, and there is no way around it. The standard
   workaround is a private server containing just you and the bot (Discord → **+** → *Create
   My Own*, then invite the bot from the developer portal's OAuth2 URL generator with the
   `bot` scope). You never have to open that server — the digest still arrives as a DM.
   Also keep **Privacy Settings → Allow direct messages from server members** on.

**(b) Server webhook.** Simpler, but always posts into a channel: Discord → **Server Settings
→ Integrations → Webhooks → New Webhook → Copy URL** → `.env` as `DISCORD_WEBHOOK_URL`.

Leave both unset and the run just skips the message. Test either one with
`python3 -m carmon notify --mode dm` (or `--mode webhook`).

## 2. Try it without an API key

```bash
python3 -m carmon seed-demo      # 18 realistic fake listings, tagged source='demo'
python3 -m carmon enrich         # attach REAL NHTSA + EPA data to them (no key needed)
python3 -m carmon digest --days 30
python3 -m carmon serve          # http://127.0.0.1:8787
python3 -m carmon seed-demo --clear
```

**Demo data cannot be mistaken for real inventory.** It is tagged `source='demo'` and:

* a real `carmon run` **deletes every demo row before storing anything** — the two never mix;
* it **expires by itself** after `demo.auto_clear_hours` (default 12); any command, including
  the web server, clears it once stale;
* while it exists, every surface says so out loud — a stderr warning on each CLI command, a
  red banner on every web page, a `DEMO` badge on each listing, a `⚠️ DEMO DATA` field at the
  top of the Discord message, a blockquote in the digest, and a `warning` field in the API and
  MCP payloads.

---

## 3. Run it manually

```bash
python3 -m carmon run                 # fetch → enrich → store → score → digest → Discord
python3 -m carmon run --dry-run       # hit the APIs, print the digest, write nothing
python3 -m carmon run --no-discord    # skip the Discord post
python3 -m carmon digest --days 7     # re-render from stored data, zero API calls
python3 -m carmon enrich              # refresh NHTSA + EPA data, then rescore (no MarketCheck calls)
python3 -m carmon reliability --make Honda --model Civic --year 2022
python3 -m carmon appraise --make Toyota --model Corolla --year 2022 --mileage 35000 --price 17500
python3 -m carmon deals               # active listings ranked by price versus expected
python3 -m carmon market              # price trends, days on market, per-model stats
python3 -m carmon quota               # calls used vs how much of the month has passed
python3 -m carmon stats               # DB + quota stats as JSON
python3 -m carmon config-check        # validate config.json and report drift
python3 -m carmon score --make Nissan --model Sentra --mileage 45000 --distance 70
python3 -m carmon sources             # cross-shopping links (see SOURCES.md)
python3 -m carmon notify --mode dm    # send the digest as a Discord direct message
python3 -m carmon selftest            # run the bundled test suite
```

A run costs **5 API calls by default** (5 pages of up to 50 listings), plus 2 more for the
certified pass — about 7/day, ~210/month against the 500 cap. Tune with `search.max_pages`
and `search.certified_max_pages` in `config.json`.

---

## 4. Schedule it daily (Windows, macOS or Linux)

```bash
python3 -m carmon cron --at 7:30                      # detects your OS
python3 -m carmon cron --at 7:30 --platform windows   # force the Windows form
```

**Linux / macOS** — it prints the crontab line and a one-liner to install it:

```
30 7 * * * cd /path/to/used-car-monitor && /usr/bin/python3 -m carmon run >> /path/to/used-car-monitor/data/cron.log 2>&1
```

On Linux you can instead use the systemd units in `deploy/` (`carmon.service` + `carmon.timer`,
plus `carmon-web.service` to keep the website up).

**Windows** — it prints a Task Scheduler command to run once in an Administrator prompt:

```
schtasks /Create /SC DAILY /ST 07:30 /TN "UsedCarMonitor" /TR "cmd /c cd /d C:\path\to\used-car-monitor && \"C:\Python311\python.exe\" -m carmon run >> \"C:\path\to\used-car-monitor/data/run.log\" 2>&1"
```

plus the `/Query`, `/Run` and `/Delete` forms. In the Task Scheduler GUI, tick *"Run task as
soon as possible after a scheduled start is missed"* so a sleeping laptop catches up.

### Does this run on Windows?

Yes — Windows, macOS and Linux, from the same checkout. It is pure Python 3.11 standard
library plus `requests`: `pathlib` for every path, `sqlite3` for storage (no server to
install), `http.server` for the website, and no shell-outs, symlinks, or POSIX-only calls
anywhere. Concretely:

* **Paths** in `config.json` are relative and resolved with `pathlib`, so `data/carmon.db`
  works unchanged on both `C:\` and `/home`.
* **Text** is read and written as explicit UTF-8, and the CLI reconfigures stdout/stderr to
  UTF-8 at startup — without that, the pace gauge and status icons crash a *redirected*
  Windows run with `UnicodeEncodeError`, which is exactly what a scheduled task does.
* **Scheduling** is the only genuinely OS-specific part, which is why `carmon cron` emits the
  right form per platform. The systemd units in `deploy/` are Linux-only by nature.

The database file is portable: copy `data/carmon.db` between machines and the history,
scores and NHTSA cache come with it.

## 5. Configuration (`config.json`)

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

`.env` is not a general config file — it holds three secrets and nothing else. Copy the
template with `cp .env.example .env` (the file is named `.env.example`, so it sorts next to
`.env`; there is no `example.env`). Real environment variables override the file, so
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

## 6. Website + JSON API

```bash
python3 -m carmon serve --port 8787
```

Pages: `/` dashboard (filters, score badges), `/listing/<vin>` (score breakdown + price
history + cross-shop links), `/sources`, `/digest`.

**What the sort dropdown does.** The default is **Score, best first** — highest score down,
with ties broken by the lower price. The full list, each with its direction spelled out in the
UI and in a caption above the results table:

| Option | Order |
| --- | --- |
| Score (best first) | `score DESC`, then `price ASC` for ties |
| Price (low → high) / (high → low) | cheapest first / dearest first |
| Mileage (lowest first) | fewest miles first |
| Distance (nearest first) | closest dealer first |
| Year (newest first) | newest model year first |
| First seen (newest first) | most recently discovered listing first |
| Last seen (newest first) | most recently still-listed first |

An unrecognised `sort=` value falls back to score, and the caption says so rather than
pretending the bad value was applied. The same keys work on `GET /api/listings?sort=`.

| Endpoint | Notes |
| --- | --- |
| `GET /api/health` | always public |
| `GET /api/stats` | listing counts, quota used/remaining, last run |
| `GET /api/listings` | `make model max_price min_price max_mileage min_year max_distance min_score cpo q sort limit offset` |
| `GET /api/listings/<vin>` | listing + `price_history` + `cross_shop` links |
| `GET /api/listings/<vin>/history` | price/mileage points |
| `GET /api/new?days=1` · `GET /api/price-drops?days=1` · `GET /api/top?limit=5` | daily views |
| `GET /api/digest/latest` | latest digest markdown |
| `GET /api/reliability` · `GET /api/reliability/<make>/<model>/<year>` | cached NHTSA complaints and recalls |
| `GET /api/market` · `GET /api/market/trend` · `GET /api/appraise` · `GET /api/deals` | market trends and price-versus-expected comparisons |
| `GET /api/sources` · `GET /api/config` · `GET /api/runs` | links, config, run log |

The server binds `127.0.0.1` by default. If you expose it, set `CARMON_API_TOKEN` in `.env`
and send `Authorization: Bearer <token>` — every `/api/*` route except `/api/health` then
requires it.

```bash
curl "http://127.0.0.1:8787/api/listings?min_score=1&sort=score&limit=5"
```

---

## 7. MCP server (for Claude and other AI assistants)

```bash
python3 -m carmon mcp        # JSON-RPC 2.0 over stdio, protocol 2024-11-05
```

Add to Claude Desktop (`claude_desktop_config.json`) or Claude Code (`.mcp.json`):

```json
{
  "mcpServers": {
    "used-car-monitor": {
      "command": "python3",
      "args": ["-m", "carmon.mcp_server"],
      "cwd": "/absolute/path/to/used-car-monitor"
    }
  }
}
```

Tools: `search_listings`, `get_listing`, `get_price_history`, `top_listings`, `new_listings`,
`price_drops`, `get_stats`, `get_latest_digest`, `explain_score`, `score_hypothetical`,
`list_sources`, `get_reliability`, `refresh_reliability`, `list_reliability`, `get_quota_pace`,
`appraise_car`, `market_trend`, `market_report`, `best_deals`, `list_comparables` — 20 in all.
Resources: `carmon://config`, `carmon://digest/latest`.

`appraise_car` is the one to reach for when asking an assistant "is this a good price?" — it
returns the expected price, the gap, the grade, and the caveats, so the answer can cite its
own sample size instead of guessing.

`score_hypothetical` is the interesting one — an assistant can ask "would a 2022 Civic with
45k miles 70 miles away score well?" without anything being in the database.

---

## 8. Data model

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

## 9. Quota pacing and the month-end sweep

500 calls a month only means something next to how much of the month has gone by, so the
raw counter is always shown against the calendar:

```bash
python3 -m carmon quota
```

```
MarketCheck quota for 2026-08
  ████████░░░░░░░|░░░░░░░░░░░░░░░░   (filled = used, | = today)
  used 100 of 500 — 400 left
  day 15 of 31 (48% of the month gone)
  expected ~242 by now → 0.41x pace  🟢 well under pace
  projected month total 207
  ~26 calls/day still affordable for the rest of the month
```

100 calls on the 15th reads **0.41x — well under pace**; the same 100 calls on the 5th reads
**1.24x — running hot**, projecting 620 against a 500 cap. The bands are: well under pace ·
under pace · on pace · running hot · far ahead of pace.

**This is a metric, not a limit.** Nothing throttles or blocks on it. The only hard stop is
still the cap itself, enforced in the client. The same numbers appear in the digest, the
Discord message, the dashboard's pace tile, `GET /api/quota`, and the `get_quota_pace` MCP tool.

### Spending leftover calls before they expire

Unused free-tier calls do not roll over — an unused balance is simply gone at midnight on the
last day of the month. So on that day the run spends what is left rather than wasting it:
deeper pagination first (a normal run only reads the cheapest few pages), then one targeted
query per preferred model, which surfaces cars that price-sorted paging never reaches.

Configured under `api.month_end_sweep`: `enabled`, `trigger_last_days` (default 1),
`reserve_calls` (20, kept back for a retry), `max_extra_calls` (400) and `max_pages_per_query`.
The digest and Discord message report what the sweep spent and what it found.

## 10. Judging a deal: market comparison and trends

The monitor answers "is this price any good?" from your own accumulated data, with no extra
API calls — it is ordinary least squares over the listings already in SQLite.

```bash
python3 -m carmon appraise --make Toyota --model Corolla --year 2022 --mileage 35000 --price 17500
```

```
🟢 good deal: $17,500 versus an expected $18,437 for this mileage and year (-937, -5.1%).
Based on 42 comparable listings (good confidence, price ~ mileage + model year).
Cheaper than 62% of them. This market charges about $98 per 1,000 miles.
  basis: Toyota Corolla within ±1 model year (model_year), method: price ~ mileage + model year, r² 0.944
  comparables: median $18,353, range $15,652–$21,808, n=42
  each newer model year is worth about $892 here
  This compares asking prices only — it knows nothing about condition, trim, options,
  accident history or title status. Always inspect the car itself.
```

Other entry points: `python3 -m carmon appraise --vin <VIN>` for a stored listing,
`python3 -m carmon deals` for everything ranked by how far below expected it sits, and
`python3 -m carmon market` for the trend report. The website has `/market` and `/appraise`
pages plus a "vs market" column, and the MCP server exposes `appraise_car`, `market_trend`,
`market_report`, `best_deals` and `list_comparables`.

### Two questions, two different waiting periods

This matters for a search that runs a month or two before you buy:

| Question | Kind | Ready when |
| --- | --- | --- |
| "Is this 2022 Corolla at 35k miles priced well?" | cross-sectional | **the first run** — every listing fetched is a price/mileage/year data point |
| "Are prices drifting down?" · "How long do these sit?" · "Do sellers cut?" | longitudinal | **weeks** — it needs repeat observations of the same cars |

So day one gives you deal grading; by week three you also get month-over-month medians, days
on market, and price-cut frequency. `python3 -m carmon market` shows all of it:

```
Median asking price by month
  2026-06  ████████████████████████████ $18,522  n=42
  2026-07  ███████████████████████████  $17,842  n=42    -680 (-3.7%)
  2026-08  ███████████████████████████  $17,876  n=42    +34 (+0.2%)

Days on market: median 21.0 (from 18 listings that have since vanished)
Price cuts: 14 of 126 tracked listings (11.1%), median cut $700 (3.9%)

By model
  model                          n     median                range   $/1k mi   days  cuts
  Honda Civic                   42    $19,120      $15,642–$22,236       116     18  12%
  Toyota Corolla                42    $18,353      $15,652–$21,808       120     24   9%
```

### How the estimate works

1. **Comparables** — same make and model, within ±1 model year, including cars that have since
   sold. Sold listings are the *best* evidence of a real market price; dropping them would bias
   the sample toward overpriced inventory that nobody bought.
2. **Fit** — weighted least squares of price against mileage and model year, weighting recent
   sightings more heavily (`market.recency_half_life_days`, default 45). With 12+ comparables it
   fits both variables; with 6+ it fits mileage alone; below that it falls back to the median
   and says so.
3. **Grade** — the gap between asking price and the fitted expectation: ≤−12% great deal, ≤−5%
   good, ±5% fair, ≥+5% above market, ≥+12% well above.
4. **Guards** — an estimate is clamped to stay near the observed price range so a wild
   extrapolation can't masquerade as a bargain, and a car is never compared against itself.

### What it will not pretend to know

Every grade ships with `sample_size`, `confidence` and `basis_level`, and they are not
decoration:

* **Confidence is capped by what the comparables actually are.** If no Kia Fortes are stored,
  the estimate falls back to other makes and confidence is forced to "very low" no matter how
  many cars are in the sample — a large sample of the wrong cars is not confidence.
* **`basis_level`** tells you which rung it used: `model_year` → `model` → `make` → `all`.
  Anything past `model` is a rough bearing, not a valuation.
* **It reads asking prices, not sale prices**, and it knows nothing about condition, trim,
  options, accident history or title status. A car priced 15% below the curve is often priced
  that way for a reason — it is a prompt to go look, not a verdict.

The comparison also feeds the score as a **`vs market`** component (up to ±1.5, full value at
12% off the expected price), which stays at 0 until there are at least 6 comparables.

## 11. Optional scrapers (off by default)

MarketCheck's API is the supported path and stays primary. These adapters exist for when its
free tier is not enough — and they are deliberately timid.

```bash
python3 -m carmon scrape --probe     # one request per adapter: is it reachable from here?
python3 -m carmon scrape --status    # today's usage against the caps
python3 -m carmon scrape             # run the enabled adapters
python3 -m carmon scrape --source repairpal --dry-run
```

### The limits, and where they are enforced

| Limit | Default | Where |
| --- | --- | --- |
| Listings per day, all sources | **100** | SQLite ledger (`scrape_usage`) |
| HTTP requests per day, all sources | **20** | same ledger |
| Pages per source per run | **2** | `ScrapeLimits.max_pages_per_run` |
| Minimum gap between requests | **5s**, or the site's `Crawl-delay` if longer | `Fetcher._sleep` |

The caps live in the database, not in memory, so re-running the command cannot reset them —
a test asserts exactly that. Everything is off until **both** `scrapers.enabled` and the
individual source are switched on in `config.json`.

### Rules that are not configurable

* **robots.txt is always obeyed**, and it **fails closed**: if robots.txt cannot be fetched,
  the whole site is treated as off limits. There is no flag to disable this.
* **No evasion.** One honest User-Agent that says what the tool is (a test asserts it does not
  impersonate a browser), no proxies, no cookie or fingerprint games, no CAPTCHA solving, and
  no retry-with-a-different-identity. If a site answers with a bot challenge, the adapter
  records `blocked` and stops. A challenge is a site saying it does not want automated
  traffic, and the right response is to respect that — `python3 -m carmon sources` gives you
  the browsing links instead.
* **VIN or nothing.** A scraped listing without a VIN is dropped, because VIN is what
  deduplicates against MarketCheck data.

Scraped listings then flow through exactly the same filtering, NHTSA/EPA enrichment, scoring
and market comparison as API ones, tagged with their source.

### What actually works today

Measured from this machine (a datacenter IP) on 2026-08-19:

| Source | Result |
| --- | --- |
| **RepairPal** | ✅ real HTML, robots.txt allows model pages — repair cost and reliability data |
| **Autotrader** | 🚫 search pages answer with a bot challenge (robots.txt itself is fine and permits `/cars-for-sale/`) |
| **Cars.com** | ⛔ even `robots.txt` is 403 behind Cloudflare → fails closed, nothing is fetched |
| CarGurus · CarMax · Carvana · TrueCar | 🚫 403/406 or a JS challenge before robots.txt is even readable |

**A home connection often behaves differently from a datacenter one**, so Autotrader and
Cars.com adapters ship anyway and may work from your laptop — run `carmon scrape --probe` to
find out. Their parsers target schema.org markup (the most stable thing on those pages) but
**have not been validated against live HTML**, because I could not fetch any. If a site's
markup has moved, the adapter reports a parse failure rather than silently returning nothing.

Only RepairPal's parser was written against a real page — and running it live caught a bug
worth knowing about: `repairpal.com/toyota/corolla` quotes the **brand's** figures ($441/yr,
"8th out of 32 for all car brands"), while `repairpal.com/reliability/toyota/corolla` quotes
the **model's** ($362/yr, "1st out of 36 for compact cars"). Storing the first as the second
would be quietly wrong, so the adapter prefers the model page and refuses to save
brand-level rows as model data.

What it collects per model: average annual repair cost, reliability rating out of 5, shop
visits per year, repair severity, and where the model ranks in its class. Those show up
alongside the NHTSA data:

```bash
python3 -m carmon reliability --make Toyota --model Corolla --year 2022
```
```
  complaints: 95   recalls: 0
    - ELECTRICAL SYSTEM: 19
  RepairPal (scraped, opt-in):
    average annual repair cost: $362
    reliability rating: 4.5 / 5.0
    ranking: 1st out of 36 for compact cars
```

### Before you switch one on

Check that site's Terms of Service. Several prohibit automated collection regardless of what
robots.txt says, and that is a separate question from whether the request technically
succeeds. The conservative reading is that these adapters are for occasional personal use at
the volumes above, and `sources.py` keeps ordinary browsing links for everything else.

## 12. Tests

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
  sources.py      demo.py         webapp.py       mcp_server.py
  scrapers/       adapter interface for future non-MarketCheck sources (empty in v1)
config.json  .env.example  requirements.txt  SPEC.md  SOURCES.md  deploy/  tests/
```
