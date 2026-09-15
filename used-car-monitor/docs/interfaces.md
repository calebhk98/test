# Website, JSON API and MCP server

The three ways to read the data: a browsable website, a JSON API, and an MCP server.

[← back to the README](../README.md)

---

## Website + JSON API

```bash
python3 -m carmon serve --port 8787
```

Pages: `/` dashboard (filters, score badges), `/listing/<vin>` (score breakdown + price
history + cross-shop links), `/market`, `/appraise`, `/scrapers`, `/settings`, `/sources`,
`/digest`.

The **Scrapers** page shows one row per adapter — state, last run, last error, pages and
listings taken, ok/failed tallies — with buttons to probe or run one, and switches to turn
sources on and off. The **Settings** page edits `config.json` and `.env`, with each secret
showing what it is for, how to get it, and a link to where. Both are write-protected; see
[configuration](configuration.md#changing-settings-from-the-website) for the rules.

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
| `GET /api/scrapers` · `GET /api/scrapers/events` | per-adapter health, last run, last error, and the request log |
| `POST /api/scrapers/run` · `/probe` · `/toggle` | run, probe or switch a scraper (write-protected, see below) |
| `GET /api/settings` · `POST /api/settings` · `POST /api/settings/secrets` | read and change config.json and .env |

The server binds `127.0.0.1` by default. If you expose it, set `CARMON_API_TOKEN` in `.env`
and send `Authorization: Bearer <token>` — every `/api/*` route except `/api/health` then
requires it.

```bash
curl "http://127.0.0.1:8787/api/listings?min_score=1&sort=score&limit=5"
```

---

## MCP server (for Claude and other AI assistants)

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
`appraise_car`, `market_trend`, `market_report`, `best_deals`, `list_comparables`,
`scraper_status`, `scraper_events`, `probe_scrapers`, `run_scraper`, `get_settings` — 25 in all.

The MCP server can *read* settings (secrets masked) and see scraper health, but cannot change
either: editing configuration is a human action, on the website or in `config.json`.
Resources: `carmon://config`, `carmon://digest/latest`.

`appraise_car` is the one to reach for when asking an assistant "is this a good price?" — it
returns the expected price, the gap, the grade, and the caveats, so the answer can cite its
own sample size instead of guessing.

`score_hypothetical` is the interesting one — an assistant can ask "would a 2022 Civic with
45k miles 70 miles away score well?" without anything being in the database.

---

---

Next: [judging a deal](market-analysis.md) · [data model and tests](development.md)
