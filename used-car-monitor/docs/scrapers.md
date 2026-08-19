# Optional scrapers

The optional adapters, the limits they obey, and which sites actually allow them.

[← back to the README](../README.md)

---

MarketCheck's API is the supported path and stays primary. These adapters exist for when its
free tier is not enough — and they are deliberately timid.

```bash
python3 -m carmon scrape --probe     # one request per adapter: is it reachable from here?
python3 -m carmon scrape --status    # per-adapter health and today's usage against the caps
python3 -m carmon scrape             # run the enabled adapters
python3 -m carmon scrape --source repairpal --dry-run
```

Two things to know about those flags: `--dry-run` still **fetches** (that is the point — you
want to see what a source returns and whether it parses) and still spends daily budget; it
only suppresses storage. And `--source` overrides that source's config toggle, though never
the master `scrapers.enabled` switch.

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

Seven adapters ship. Probed live from this machine (a datacenter IP) on 2026-08-19 with
`python3 -m carmon scrape --probe`:

| Source | Result | Why |
| --- | --- | --- |
| **RepairPal** | ✅ ok | robots.txt permits model pages; real HTML, parsed cleanly |
| **CarGurus** | ⛔ disallowed | robots.txt is readable and **explicitly disallows `/Cars/inventorylisting/`** — the search path. This one is a settled no, not a network problem |
| **CarMax** | ⛔ disallowed | robots.txt itself returns 403 (Akamai) → fail closed |
| **Cars.com** | ⛔ disallowed | robots.txt returns 403 (Cloudflare) → fail closed |
| **Carvana** | ⛔ disallowed | robots.txt behind a Cloudflare JS challenge → fail closed |
| **Autotrader** | 🚫 blocked | robots.txt permits `/cars-for-sale/`, but search pages answer with a bot challenge |
| **TrueCar** | 🚫 blocked | robots.txt permits the listings path, but it answers HTTP 403 |

Read that table as the feature working, not failing. Six of seven sites decline automated
access, and the monitor detects that and stops — which is the behaviour you want from
something running unattended on your machine every morning.

**CarGurus deserves a note**: its robots.txt is served happily to an honest bot, and it says
`Disallow: /Cars/inventorylisting/`. That is an explicit "no" to the exact page the adapter
would read, so the adapter will refuse regardless of what network you run it from. It stays in
the tree in case that ever changes; meanwhile CarGurus' deal rating is a browsing link.

**A home connection often behaves differently from a datacenter one**, so the Autotrader,
Cars.com, CarMax, Carvana and TrueCar adapters may well work from your laptop — run
`python3 -m carmon scrape --probe` to find out. Their parsers target schema.org markup (the
most stable thing on those pages) but **have not been validated against live HTML**, because
none could be fetched here. If a site's markup has moved, the adapter reports a parse failure
rather than silently returning nothing.

Only RepairPal's parser was written against a real page — and running it live caught a bug
worth knowing about: `repairpal.com/toyota/corolla` quotes the **brand's** figures ($441/yr,
"8th out of 32 for all car brands"), while `repairpal.com/reliability/toyota/corolla` quotes
the **model's** ($362/yr, "1st out of 36 for compact cars"). Storing the first as the second
would be quietly wrong, so the adapter prefers the model page and refuses to save brand-level
rows as model data.

What RepairPal adds per model: average annual repair cost, reliability rating out of 5, shop
visits per year, repair severity, and class ranking — shown next to the NHTSA data:

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

### Watching them from the website, API and MCP

Every adapter reports its own health, so you can see whether a source is working without
reading logs:

```bash
python3 -m carmon scrape --status     # per-adapter state, last run, last error, usage vs caps
```

The same information is on the website's **Scrapers** page — one row per adapter with its
state, last run, last error, pages and listings taken, and ok/failed tallies, plus buttons to
probe or run one — and through `GET /api/scrapers`, `GET /api/scrapers/events` and the
`scraper_status` / `scraper_events` MCP tools. Sources can be switched on and off from that
page (or `POST /api/scrapers/toggle`), which writes the same `config.json` toggles.

### Before you switch one on

Check that site's Terms of Service. Several prohibit automated collection regardless of what
robots.txt says, and that is a separate question from whether the request technically
succeeds. The conservative reading is that these adapters are for occasional personal use at
the volumes above, and `sources.py` keeps ordinary browsing links for everything else.

---

See also: [SOURCES.md](../SOURCES.md) for the browsing links, and [judging a deal](market-analysis.md) for the built-in price comparison.
