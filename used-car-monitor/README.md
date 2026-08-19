# Used Car Daily Monitor

A daily job that searches for used cars matching your criteria, tracks how their prices move,
scores them against your priorities, and tells you what changed — by Discord message, a local
website, a JSON API, and an MCP server your AI assistant can query.

Python 3.11+, one dependency (`requests`), SQLite for storage. Runs on Windows, macOS and Linux.

```bash
pip install -r requirements.txt
python3 -m carmon seed-demo     # fake listings, so you can look around immediately
python3 -m carmon serve         # http://127.0.0.1:8787
```

Then get a free [MarketCheck API key](https://www.marketcheck.com/apis), put it in the `.env`
the first command created for you (or on the website's Settings page), and:

```bash
python3 -m carmon run           # fetch → enrich → score → digest → Discord
python3 -m carmon cron --at 7:30   # schedule it daily on this OS
```

## What it does

| | |
| --- | --- |
| **Finds cars** | MarketCheck Inventory Search, filtered to your ZIP, radius, budget, mileage and body types |
| **Remembers them** | SQLite, deduplicated by VIN, with a price/mileage history per car |
| **Scores them** | 11 deterministic components — preferred and caution models, CPO, price, mileage, distance, year, MPG, NHTSA complaints and recalls, and price versus the local market. Every component shows its reasoning |
| **Judges the price** | Fits price against mileage and model year across comparable listings, then grades the asking price — with the sample size and confidence attached |
| **Checks reliability** | Free NHTSA complaint and recall data per model-year, looked up automatically; optional RepairPal repair costs |
| **Tells you** | A markdown digest, a Discord direct message or webhook post, a browsable website, a JSON API, and 25 MCP tools |

## Documentation

| Guide | What's in it |
| --- | --- |
| [Setup and daily operation](docs/setup.md) | Install, API key, Discord (DM or channel), demo data, scheduling on Windows/macOS/Linux |
| [Where the data comes from](docs/data-sources.md) | MarketCheck, NHTSA, EPA — and how the 500-call free tier is paced and never exceeded |
| [Configuration and scoring](docs/configuration.md) | Every setting, the two scoring modes, single-source-of-truth rules, and editing it all from the website |
| [Judging a deal](docs/market-analysis.md) | How the price comparison works, what it refuses to claim, and which trends need weeks of data |
| [Website, API and MCP](docs/interfaces.md) | Pages, every endpoint, and the MCP tool list |
| [Optional scrapers](docs/scrapers.md) | Seven adapters, the caps and robots rules they obey, and what actually works today |
| [Data model, tests and layout](docs/development.md) | Tables, the test suite, and where the code lives |

## Commands

```bash
python3 -m carmon run              # the daily job
python3 -m carmon digest --days 7  # re-render from stored data, no API calls
python3 -m carmon appraise --make Toyota --model Corolla --year 2022 --mileage 35000 --price 17500
python3 -m carmon deals            # active listings ranked by price versus expected
python3 -m carmon market           # price trends, days on market, per-model stats
python3 -m carmon quota            # calls used vs how much of the month has passed
python3 -m carmon reliability --make Honda --model Civic --year 2022
python3 -m carmon settings --set search.zip=37211
python3 -m carmon scrape --probe   # optional scrapers: what can this machine reach?
python3 -m carmon serve            # website + JSON API
python3 -m carmon mcp              # MCP server on stdio
python3 -m carmon selftest         # the full test suite
```

## Principles

A few decisions worth knowing before you rely on it:

* **The free tier is never quietly exceeded.** Every API call is logged, the client refuses to
  start one past the monthly cap, and the digest shows usage against how much of the month has
  actually elapsed — 100 calls on the 15th reads very differently from 100 on the 5th.
* **Nothing hides its reasoning.** Scores show every component and why. Price grades carry
  their sample size, confidence, and what they were compared against. Estimates drawn from the
  wrong comparables say so.
* **Unknown is neutral, never a penalty.** Missing MPG or NHTSA data scores zero rather than
  pushing a car down.
* **Demo data cannot be mistaken for real.** It auto-clears, a real run deletes it first, and
  every surface flags it while it exists.
* **The scrapers decline politely.** robots.txt is always obeyed and fails closed, daily caps
  live in the database, and a bot challenge ends the attempt — no evasion, ever.

## Non-negotiables

No purchase automation and no contacting dealers — this finds and ranks cars, you decide.
Scraping is opt-in, off by default, and capped; the browsing links in
`python3 -m carmon sources` are the supported way to use the sites that decline automation.
