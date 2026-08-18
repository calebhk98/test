# Used Car Daily Monitor

A small daily job that searches MarketCheck's Inventory Search API for used cars matching
your criteria, stores them in SQLite (dedup'd by VIN), tracks price and mileage changes over
time, scores every listing deterministically, and then tells you about it four ways:

| Output | Command | What it is |
| --- | --- | --- |
| **Daily digest** | `python3 -m carmon run` | Markdown file: new listings, price drops, top 5 by score |
| **Discord message** | same run, or `python3 -m carmon notify` | Embed posted to a webhook |
| **Website** | `python3 -m carmon serve` | Browse/filter listings, see score breakdowns and price history |
| **JSON API** | same server, `/api/*` | Everything the website shows, as JSON |
| **MCP server** | `python3 -m carmon mcp` | 11 tools so Claude (or any MCP client) can query your data |

Python 3.11+, one runtime dependency (`requests`); everything else is standard library.

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

### Discord webhook (optional)

Discord → **Server Settings → Integrations → Webhooks → New Webhook** → *Copy Webhook URL*,
then put it in `.env` as `DISCORD_WEBHOOK_URL=`. Leave it blank and the run just skips the post.

---

## 2. Try it without an API key

```bash
python3 -m carmon seed-demo      # 18 realistic fake listings, tagged source='demo'
python3 -m carmon digest --days 30
python3 -m carmon serve          # http://127.0.0.1:8787
python3 -m carmon seed-demo --clear
```

---

## 3. Run it manually

```bash
python3 -m carmon run                 # fetch → store → score → digest → Discord
python3 -m carmon run --dry-run       # hit the API, print the digest, write nothing
python3 -m carmon run --no-discord    # skip the Discord post
python3 -m carmon digest --days 7     # re-render from stored data, zero API calls
python3 -m carmon stats               # DB + quota stats as JSON
python3 -m carmon score --make Nissan --model Sentra --mileage 45000 --distance 70
python3 -m carmon sources             # cross-shopping links (see SOURCES.md)
python3 -m carmon selftest            # run the bundled test suite
```

A run costs **5 API calls by default** (5 pages of up to 50 listings), plus 2 more for the
certified pass — about 7/day, ~210/month against the 500 cap. Tune with `search.max_pages`
and `search.certified_max_pages` in `config.json`.

---

## 4. Schedule it daily

```bash
python3 -m carmon cron --at 7:30      # prints the crontab line, and a command to install it
crontab -e
```

The printed line looks like:

```
30 7 * * * cd /path/to/used-car-monitor && /usr/bin/python3 -m carmon run >> /path/to/used-car-monitor/data/cron.log 2>&1
```

Prefer systemd? `deploy/carmon.service` and `deploy/carmon.timer` are ready to copy into
`/etc/systemd/system/` (edit the paths, then `systemctl enable --now carmon.timer`).

---

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

The mileage ramp is calibrated so 40,000 miles still costs exactly −1 (the spec's anchor),
while 39,950 vs 40,050 differ by 0.005 and 60,000 is a full point worse than 40,000.

**Every component is stored and shown** — `score_breakdown` in the DB, a "why:" line in the
digest, a breakdown table on each listing page, and the `explain_score` MCP tool. After
editing weights, run `python3 -m carmon rescore` to recompute stored scores.

---

## 6. Website + JSON API

```bash
python3 -m carmon serve --port 8787
```

Pages: `/` dashboard (filters, score badges), `/listing/<vin>` (score breakdown + price
history + cross-shop links), `/sources`, `/digest`.

| Endpoint | Notes |
| --- | --- |
| `GET /api/health` | always public |
| `GET /api/stats` | listing counts, quota used/remaining, last run |
| `GET /api/listings` | `make model max_price min_price max_mileage min_year max_distance min_score cpo q sort limit offset` |
| `GET /api/listings/<vin>` | listing + `price_history` + `cross_shop` links |
| `GET /api/listings/<vin>/history` | price/mileage points |
| `GET /api/new?days=1` · `GET /api/price-drops?days=1` · `GET /api/top?limit=5` | daily views |
| `GET /api/digest/latest` | latest digest markdown |
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
`list_sources`. Resources: `carmon://config`, `carmon://digest/latest`.

`score_hypothetical` is the interesting one — an assistant can ask "would a 2022 Civic with
45k miles 70 miles away score well?" without anything being in the database.

---

## 8. Data model

`listings` — one row per VIN: `vin` (PK), `first_seen`, `last_seen`, `year`, `make`, `model`,
`trim`, `body_type`, `fuel_type`, `mileage`, `price_current`, `price_first_seen`, `dealer_name`,
`dealer_city`, `dealer_state`, `distance_miles`, `cpo`, `listing_url`, `score`,
`score_breakdown`, `source`, `active`, `updated_at`.

`price_history` — `vin`, `date`, `price`, `mileage`; appended on first sight and again
whenever price or mileage changes, so price drops are visible over time.

`api_usage` — one row per API call (month, endpoint, HTTP status) — this is the quota ledger.
`runs` — one row per daily job: counts, API calls used, digest path, errors.

Listings that stop appearing in results are marked `active = 0` (likely sold) rather than deleted.

---

## 9. Non-goals in v1

No scraping of Autotrader / CarGurus / Cars.com / CarMax — MarketCheck only. No purchase
automation, no contacting dealers. Other sites appear as **manual deep links** only
(see [SOURCES.md](SOURCES.md)); `carmon/scrapers/` holds the adapter interface if that
changes later, with no adapters registered.

The stretch goal (piping the digest through a local LLM for a plain-English summary) is not
implemented — the deterministic pipeline comes first, as the spec asks.

---

## 10. Tests

```bash
python3 -m unittest discover -s tests -t . -v    # or: python3 -m carmon selftest
```

124 tests covering scoring (including the 39,950-vs-40,050-vs-60,000 continuity requirement),
normalization and filtering, quota enforcement, upsert/history bookkeeping, digest rendering,
Discord payload limits and retries, the CLI, every HTTP endpoint, and the MCP protocol layer
end-to-end. No test touches the network — the MarketCheck and Discord clients are injected with
fakes.

## Layout

```
carmon/
  cli.py          config.py       db.py           digest.py
  marketcheck.py  mcp_server.py   notify.py       pipeline.py
  scoring.py      sources.py      webapp.py       demo.py
  scrapers/       adapter interface for future non-MarketCheck sources (empty in v1)
config.json  .env.example  requirements.txt  SPEC.md  SOURCES.md  deploy/  tests/
```
