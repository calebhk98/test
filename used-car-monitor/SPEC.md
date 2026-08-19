# Used Car Daily Monitor — Build Spec

> **Status note (kept for the record).** This is the original spec as written, preserved
> unchanged. Two things listed here as non-goals were later requested and built: the optional
> scrapers (opt-in, capped, robots-obeying — see [docs/scrapers.md](docs/scrapers.md)) and
> data sources beyond MarketCheck (NHTSA and EPA, both free and keyless). Everything else was
> delivered as specified, plus market price comparison, quota pacing and a settings UI. The
> stretch goal — piping the digest through a local LLM — remains unimplemented, deliberately.

## Goal

A small daily job that queries MarketCheck's Inventory Search API for used cars matching my criteria, stores results in a local DB (dedup'd by VIN), tracks price/mileage changes over time, scores each listing against my priorities, and outputs a short daily digest of what's new or changed.

## Data source

MarketCheck Cars API — https://developers.marketcheck.com

* Use the Free tier (500 calls/month, 5 calls/sec, 100-mile radius limit, $0/mo). Do not upgrade tiers without asking me first.
* Primary endpoint: Inventory Search API.
* Sign up for a free API key at the developer portal; store it in a `.env` file (gitignored), never commit it.
* Respect the 5 calls/sec rate limit and log total calls made per month so I can see usage against the 500/month cap.

## Search parameters (config file, not hardcoded)

* ZIP: `38464`
* Radius: `100` miles
* Year: `2021` or newer
* Mileage: under `60000`
* Price: under `20000`
* Body type: sedan/hatchback/small SUV (exclude trucks, vans)
* Fuel type: exclude Electric and Hybrid by default (toggleable flag, off by default)
* Preferred makes/models (higher score): Toyota Corolla, Honda Civic, Hyundai Elantra, Mazda3, Kia Forte
* Caution makes/models (lower score unless CPO): Nissan Versa, Nissan Sentra, Nissan Altima — known CVT reliability issues; only score normally if listing is manufacturer Certified Pre-Owned

## Storage

SQLite, one file, no external DB needed.

Table `listings`:

* `vin` (primary key)
* `first_seen` (date)
* `last_seen` (date)
* `year`, `make`, `model`, `trim`
* `mileage`
* `price_current`
* `dealer_name`, `dealer_city`, `dealer_state`, `distance_miles`
* `cpo` (bool)
* `listing_url`
* `score` (computed, see below)

Table `price_history`:

* `vin`, `date`, `price`, `mileage` — one row appended each time a VIN is seen again with a changed price or mileage, so I can see price drops over time.

## Scoring function (deterministic, not LLM-based)

Simple weighted score, roughly:

* +2 preferred make/model, +0 neutral, -2 caution make/model unless CPO
* +2 if CPO
* +1 if price dropped since first_seen
* -1 per 25 miles of distance beyond 50 miles
* -1 if mileage > 40,000
* Output score alongside raw data; don't hide the inputs — I want to see why something scored well.

If possible, we may want to make the score algorithmic, so a 39,950 mile car is not way worse than a 40,050 car, while it matches a 60,000 car.

## Daily job

* Runs once/day via cron (or a scheduled task, whatever's idiomatic for the chosen stack).
* Fetches current matches, upserts into `listings`, appends to `price_history` on changes.
* Generates a digest (markdown or plain text file, or console output — start simple) covering:
   * New listings since yesterday, sorted by score
   * Price drops since yesterday
   * Top 5 overall by score
* Optional stretch goal: pipe the digest through a local LLM to turn it into 3-4 sentences of plain-English summary. Not required for v1 — get the deterministic pipeline working first.

## Explicit non-goals for v1, possible goals for later

* No scraping of Autotrader/CarGurus/Cars.com/CarMax directly — MarketCheck only.
* No purchase automation, no auto-contacting dealers.

## Tech stack preference

Whatever's fastest to one-shot correctly — Python is fine (requests + sqlite3, stdlib-heavy, minimal deps). Include a `README.md` with setup steps (API key, cron setup, how to run manually) and a `requirements.txt`.

## Delivery additions requested alongside the spec

* A daily message posted to Discord.
* A basic website to browse the results.
* A JSON API, plus an MCP server so AI assistants can query the data.
