"""Tool schema definitions: the 25 entries returned by tools/list.

Each entry's 'description' is the text an AI client reads to decide whether
and how to call the tool, so it is written out in full below -- nothing here
is generated or abbreviated. Only the surrounding JSON Schema structure is
built through the small helpers in schema.py.
"""

from __future__ import annotations

from typing import Any, Dict, List

from . import schema as s


def tool_defs() -> List[Dict[str, Any]]:
    return [
        {
            "name": "search_listings",
            "description": (
                "Search the used-car listings database with filters on make, model, price, "
                "mileage, year, distance, score, CPO status, free-text query, and cached NHTSA "
                "complaint/recall counts (max_complaints, max_recalls — free federal data, raw "
                "and not sales-volume adjusted; listings with no cached NHTSA data are kept, "
                "never excluded, since unknown is not the same as bad). Returns a list of "
                "matching listings sorted as requested." + s.DEMO_WARNING_NOTE
            ),
            "inputSchema": s.object_schema({
                "make": s.prop_string("Exact make match, e.g. 'Toyota' (case-insensitive)."),
                "model": s.prop_string("Model prefix match, e.g. 'Corolla' (case-insensitive)."),
                "max_price": s.prop_int("Maximum current price in dollars."),
                "min_price": s.prop_int("Minimum current price in dollars."),
                "max_mileage": s.prop_int("Maximum odometer mileage."),
                "min_year": s.prop_int("Minimum model year."),
                "max_distance": s.prop_number("Maximum distance from home in miles."),
                "min_score": s.prop_number("Minimum computed score."),
                "max_complaints": s.prop_int(
                    "Only include listings whose model year has at most this many cached NHTSA "
                    "consumer complaints (free federal data, raw counts, NOT sales-volume "
                    "adjusted). Applied as a post-filter over the cached reliability data. "
                    "Listings with no cached NHTSA data are KEPT, not excluded — unknown is not "
                    "treated as bad. Use 'refresh_reliability' first if a model you care about "
                    "has never been looked up."
                ),
                "max_recalls": s.prop_int(
                    "Only include listings whose model year has at most this many cached NHTSA "
                    "recall campaigns (free federal data). Listings with no cached NHTSA data "
                    "are KEPT, not excluded — unknown is not treated as bad."
                ),
                "cpo_only": s.prop_bool("If true, only Certified Pre-Owned listings.", default=False),
                "active_only": s.prop_bool("If true (default), only currently active listings.", default=True),
                "query": s.prop_string("Free-text search across make, model, trim, dealer name, and VIN."),
                "sort": s.prop_string(
                    "Sort order for results.",
                    enum=["score", "price", "price_desc", "mileage", "distance", "year", "first_seen", "last_seen"],
                    default="score",
                ),
                "limit": s.prop_int("Max number of results to return (default 20, max 100).", default=20, minimum=1, maximum=100),
                "offset": s.prop_int("Number of results to skip, for pagination.", default=0, minimum=0),
            }),
        },
        {
            "name": "get_listing",
            "description": (
                "Fetch a single listing by VIN, including its price history, cross-shopping "
                "links to other sites where the same car could be searched for, and any cached "
                "NHTSA reliability data (consumer complaint / recall counts, free federal data — "
                "raw and NOT sales-volume adjusted) and EPA MPG for its model year. Also returns "
                "nhtsa_vin_url and nhtsa_model_url, direct NHTSA.gov links for a human to check "
                "unrepaired recalls on this exact VIN." + s.DEMO_WARNING_NOTE
            ),
            "inputSchema": s.object_schema(
                {"vin": s.prop_string("The vehicle's VIN (unique identifier).")},
                required=["vin"],
            ),
        },
        {
            "name": "get_price_history",
            "description": "Get the recorded price/mileage history for a listing by VIN, oldest first.",
            "inputSchema": s.object_schema(
                {"vin": s.prop_string("The vehicle's VIN.")},
                required=["vin"],
            ),
        },
        {
            "name": "top_listings",
            "description": (
                "Return the best-scoring currently-active listings, highest score first."
                + s.DEMO_WARNING_NOTE
            ),
            "inputSchema": s.object_schema({
                "limit": s.prop_int("Number of listings to return (default 5).", default=5, minimum=1, maximum=100),
            }),
        },
        {
            "name": "new_listings",
            "description": (
                "Return active listings first seen within the last N days, best score first."
                + s.DEMO_WARNING_NOTE
            ),
            "inputSchema": s.object_schema({
                "days": s.prop_int("How many days back to look (default 1).", default=1, minimum=1),
                "limit": s.prop_int("Max number of results (default 50).", default=50, minimum=1, maximum=500),
            }),
        },
        {
            "name": "price_drops",
            "description": (
                "Return active listings whose price dropped within the last N days, biggest "
                "drop first." + s.DEMO_WARNING_NOTE
            ),
            "inputSchema": s.object_schema({
                "days": s.prop_int("How many days back to look (default 1).", default=1, minimum=1),
                "limit": s.prop_int("Max number of results (default 50).", default=50, minimum=1, maximum=500),
            }),
        },
        {
            "name": "get_stats",
            "description": (
                "Get database summary statistics (listing counts, average/min price, best "
                "score) plus MarketCheck API quota usage for the current month. The quota "
                "numbers come with pace context under a 'pace' key (used vs. expected_by_now, "
                "pace_ratio, pace_label) — see 'get_quota_pace' for the full breakdown and a "
                "text gauge. Also reports demo_listings and demo_warning: if demo_listings is "
                "greater than 0, some stored listings are seeded demo data, not real cars, and "
                "demo_warning explains it."
            ),
            "inputSchema": s.EMPTY_SCHEMA,
        },
        {
            "name": "get_quota_pace",
            "description": (
                "How to judge whether MarketCheck API quota use is comfortable this month. "
                "100 calls used by the 15th of the month is relaxed; 100 calls by the 5th is "
                "not — this tool turns the raw monthly call counter into that comparison. "
                "Compare 'used' against 'expected_by_now' (what a perfectly even pace would "
                "have used by today), and read 'pace_ratio': below 1.0 means quota is being "
                "used more slowly than the month is passing, 1.0 means exactly on pace, above "
                "1.0 means running ahead of pace. 'pace_label' and 'pace_icon' give a "
                "human-readable read (e.g. 'well under pace'), 'projected_month_total' "
                "extrapolates the current rate to month-end, and 'affordable_per_day' is how "
                "many more calls/day are still sustainable without exceeding the cap. Also "
                "includes 'summary' (one-line text), 'bar' (a text gauge), and "
                "'month_end_sweep' (whether today is the last-day sweep window that spends "
                "down unused calls before they expire worthless). This is purely "
                "informational and advisory — nothing here limits anything; the only hard "
                "stop on API usage is the monthly cap itself, enforced elsewhere."
            ),
            "inputSchema": s.object_schema({
                "width": s.prop_int(
                    "Character width of the returned text gauge 'bar' (default 24).",
                    default=24,
                    minimum=4,
                ),
            }),
        },
        {
            "name": "get_latest_digest",
            "description": (
                "Return the full markdown text of the most recently generated daily digest, "
                "or a clear message if no digest has been generated yet."
            ),
            "inputSchema": s.EMPTY_SCHEMA,
        },
        {
            "name": "explain_score",
            "description": (
                "Explain why a specific listing (by VIN) received its score: returns both the "
                "score breakdown stored in the database and a freshly recomputed explanation "
                "using the current scoring configuration. The recomputed explanation attaches "
                "cached fuel-economy and NHTSA reliability data (free federal complaint/recall "
                "data, raw counts, not sales-volume adjusted) first, so its 'fuel economy', "
                "'NHTSA complaints', and 'NHTSA recalls' components reflect real data instead "
                "of showing as unknown."
            ),
            "inputSchema": s.object_schema(
                {"vin": s.prop_string("The vehicle's VIN.")},
                required=["vin"],
            ),
        },
        {
            "name": "score_hypothetical",
            "description": (
                "Score a hypothetical car that is not (yet) in the database, using the current "
                "scoring configuration. Useful for questions like 'would a 2022 Civic with "
                "45k miles, 70 miles away, score well?' or for modeling a car end-to-end with "
                "known fuel economy and NHTSA reliability figures (complaint/recall counts are "
                "free federal data — raw counts, NOT adjusted for sales volume, so pass them "
                "only if you already have them, e.g. from 'get_reliability')."
            ),
            "inputSchema": s.object_schema({
                "make": s.prop_string("Vehicle make, e.g. 'Honda'."),
                "model": s.prop_string("Vehicle model, e.g. 'Civic'."),
                "year": s.prop_int("Model year, e.g. 2022. Used for the 'model year' scoring component."),
                "mileage": s.prop_int("Odometer mileage."),
                "distance_miles": s.prop_number("Distance from home in miles."),
                "price_current": s.prop_int("Current asking price in dollars."),
                "price_first_seen": s.prop_int("Original asking price in dollars, if different from price_current (for price-drop scoring)."),
                "cpo": s.prop_bool("Whether the vehicle is Certified Pre-Owned.", default=False),
                "combined_mpg": s.prop_number("EPA combined miles per gallon, if known, for the 'fuel economy' scoring component."),
                "complaint_count": s.prop_int(
                    "Cached NHTSA consumer complaint count for this model year, if known "
                    "(free federal data, raw count, not sales-volume adjusted), for the "
                    "'NHTSA complaints' scoring component."
                ),
                "recall_count": s.prop_int(
                    "Cached NHTSA recall campaign count for this model year, if known "
                    "(free federal data), for the 'NHTSA recalls' scoring component."
                ),
            }),
        },
        {
            "name": "list_sources",
            "description": (
                "List cross-shopping deep links to other places to run the same search "
                "(manufacturer CPO programs, big retailers, marketplace aggregators), grouped "
                "by category, built from the current search configuration."
            ),
            "inputSchema": s.EMPTY_SCHEMA,
        },
        {
            "name": "get_reliability",
            "description": (
                "Look up cached NHTSA reliability data for one make/model/year: consumer-filed "
                "defect complaints and manufacturer recall campaigns. This is free federal data "
                "from api.nhtsa.gov (no API key, no cost) — the same data every third-party "
                "reliability site repackages. Complaint and recall counts are RAW totals, NOT "
                "adjusted for how many of that model were sold, so a high-volume model naturally "
                "racks up more complaints than a rare one; the recurring complaint *components* "
                "(top_components) are a stronger signal than the raw count. This tool only reads "
                "what is already cached in the database and never hits the network — if nothing "
                "is cached yet it returns an error telling you to run `python3 -m carmon enrich` "
                "or call the 'refresh_reliability' tool."
            ),
            "inputSchema": s.object_schema({
                "make": s.prop_string("Vehicle make, e.g. 'Honda'."),
                "model": s.prop_string("Vehicle model, e.g. 'Civic'."),
                "year": s.prop_int("Model year, e.g. 2022."),
            }, required=["make", "model", "year"]),
        },
        {
            "name": "refresh_reliability",
            "description": (
                "Fetch fresh NHTSA consumer complaint and recall data for one make/model/year "
                "directly from api.nhtsa.gov (free federal data, no API key needed) and cache it "
                "in the database. This is the ONLY tool on this server that makes a live network "
                "call — every other tool reads the local database. Complaint and recall counts "
                "returned are RAW totals, NOT adjusted for sales volume, so a high-volume model "
                "naturally shows more complaints than a rare one; the recurring complaint "
                "components are the stronger signal. Prefer calling 'get_reliability' first to "
                "check whether the data is already cached before spending a network call here."
            ),
            "inputSchema": s.object_schema({
                "make": s.prop_string("Vehicle make, e.g. 'Honda'."),
                "model": s.prop_string("Vehicle model, e.g. 'Civic'."),
                "year": s.prop_int("Model year, e.g. 2022."),
                "force": s.prop_bool(
                    "Refetch from NHTSA even if a still-fresh cached entry already exists.",
                    default=False,
                ),
            }, required=["make", "model", "year"]),
        },
        {
            "name": "list_reliability",
            "description": (
                "List every make/model/year currently cached with NHTSA reliability data (free "
                "federal consumer complaint and recall data from api.nhtsa.gov), sorted by "
                "complaint count descending. Counts are raw and NOT adjusted for sales volume, "
                "so this is a 'what has been looked up, and how loud is it' view rather than a "
                "ranked reliability score — check top_components on each row for the recurring, "
                "more meaningful signal."
            ),
            "inputSchema": s.object_schema({
                "limit": s.prop_int(
                    "Max number of cached model/year rows to return (default 25).",
                    default=25,
                    minimum=1,
                    maximum=500,
                ),
            }),
        },
        {
            "name": "appraise_car",
            "description": (
                "Answer 'is this price any good?' for one car, either a hypothetical one "
                "described by make/model/year/mileage/price or a stored listing looked up by "
                "VIN. Returns an expected price and, when a price is given, a grade ('great "
                "deal' through 'well above market')." + s.APPRAISAL_CAVEAT_NOTE
            ),
            "inputSchema": s.object_schema({
                "make": s.prop_string("Vehicle make, e.g. 'Honda'. Recommended unless 'vin' is given."),
                "model": s.prop_string("Vehicle model, e.g. 'Civic'. Recommended unless 'vin' is given."),
                "year": s.prop_int("Model year, e.g. 2022. Recommended unless 'vin' is given."),
                "mileage": s.prop_int("Odometer mileage. Recommended unless 'vin' is given."),
                "price": s.prop_int(
                    "Asking price in dollars. Optional: without it you still get an "
                    "expected price and comparable data, but no grade, delta, or percentile "
                    "since there is nothing to compare against."
                ),
                "vin": s.prop_string(
                    "If given, appraise this stored listing instead of a hypothetical car — "
                    "make/model/year/mileage/price are read from the database and any of "
                    "those arguments passed alongside 'vin' are ignored."
                ),
            }),
        },
        {
            "name": "market_trend",
            "description": (
                "How prices for a make/model (or the whole tracked market, if both are "
                "omitted) have moved month over month, plus how long listings tend to stay on "
                "the market and how often sellers cut prices. This is longitudinal — built "
                "from repeated observations of the same listings over time — so it starts "
                "sparse and fills in as the daily job keeps running for weeks; it is a "
                "different question from 'appraise_car', which works from the first run."
            ),
            "inputSchema": s.object_schema({
                "make": s.prop_string("Exact make match, e.g. 'Toyota' (case-insensitive). Omit for all makes."),
                "model": s.prop_string("Model prefix match, e.g. 'Corolla' (case-insensitive). Omit for all models."),
                "months": s.prop_int("How many recent months of trend data to return (default 6).", default=6, minimum=1, maximum=60),
            }),
        },
        {
            "name": "market_report",
            "description": (
                "A full snapshot of the tracked market: listings tracked, the price trend, a "
                "per-model summary, days-on-market, price-cut frequency, and the current best "
                "deals with their appraisals." + s.APPRAISAL_CAVEAT_NOTE
            ),
            "inputSchema": s.object_schema({
                "months": s.prop_int("How many recent months of trend data to include (default 6).", default=6, minimum=1, maximum=60),
            }),
        },
        {
            "name": "best_deals",
            "description": (
                "Rank currently active listings by how far below their expected price they "
                "sit, each with its full appraisal attached. A listing only appears once it "
                "has at least 'min_sample' comparable listings behind its estimate."
                + s.APPRAISAL_CAVEAT_NOTE
            ),
            "inputSchema": s.object_schema({
                "limit": s.prop_int("Max number of results to return (default 10).", default=10, minimum=1, maximum=100),
                "min_sample": s.prop_int(
                    "Minimum number of comparable listings an appraisal must be based on to be included (default 3).",
                    default=3,
                    minimum=1,
                ),
            }),
        },
        {
            "name": "list_comparables",
            "description": (
                "List the actual stored listings used as comparables for a make/model/year — "
                "the raw data behind an 'appraise_car' estimate, so an assistant can show its "
                "work instead of citing a number with nothing behind it. Includes both active "
                "and sold/expired listings, since a car that left the market is evidence too."
            ),
            "inputSchema": s.object_schema({
                "make": s.prop_string("Vehicle make, e.g. 'Honda'."),
                "model": s.prop_string("Vehicle model, e.g. 'Civic'."),
                "year": s.prop_int("Model year, e.g. 2022. If omitted, comparables are not filtered by year."),
                "year_window": s.prop_int(
                    "How many model years on either side of 'year' to include (default 1). Ignored if 'year' is omitted.",
                    default=1,
                    minimum=0,
                ),
                "limit": s.prop_int("Max number of comparable listings to return (default 25).", default=25, minimum=1, maximum=500),
            }, required=["make", "model"]),
        },
        {
            "name": "scraper_status",
            "description": (
                "Status of the optional scraper adapters: merges each adapter's static "
                "metadata (name, site, kind) with its config toggle, the master "
                "'scrapers.enabled' switch, its last recorded run from the database, and "
                "today's usage against the daily caps. Every registered adapter appears even "
                "if it has never run — those show status 'never run', which just means "
                "nobody has called 'run_scraper' or 'probe_scrapers' for it yet, not that "
                "anything is wrong. This tool is read-only and DOES NOT touch the network — "
                "it only reads what is already in the database, so prefer it over "
                "'run_scraper' or 'probe_scrapers' whenever the question is simply 'is "
                "scraping working?'." + s.SCRAPER_BLOCKED_NOTE
            ),
            "inputSchema": s.object_schema({
                "source": s.prop_string(
                    "Limit to one adapter's key, e.g. 'repairpal' or 'carmax'. Omit "
                    "for every known adapter."
                ),
            }),
        },
        {
            "name": "scraper_events",
            "description": (
                "The raw scraper request log: exactly which URL was fetched (or would have "
                "been, for a probe), when, its HTTP status, how many listings it yielded, and "
                "any note — the evidence behind 'scraper_status'. This tool is read-only and "
                "DOES NOT touch the network; it only reads the local ledger that "
                "'run_scraper' and 'probe_scrapers' already wrote to." + s.SCRAPER_BLOCKED_NOTE
            ),
            "inputSchema": s.object_schema({
                "limit": s.prop_int(
                    "Max number of log rows to return, newest first (default 25).",
                    default=25,
                    minimum=1,
                    maximum=200,
                ),
                "source": s.prop_string("Limit to one adapter's key, e.g. 'repairpal'. Omit for every source."),
            }),
        },
        {
            "name": "probe_scrapers",
            "description": (
                "Reachability check: one lightweight request per registered scraper adapter, "
                "to see whether that site can actually be reached and parsed from here right "
                "now. THIS MAKES REAL OUTBOUND NETWORK REQUESTS to third-party sites and is "
                "subject to the same daily caps as everything else (100 listings/day, 20 "
                "requests/day across all sources combined, at least 5 seconds between "
                "requests) — it spends budget just like a real run. Prefer 'scraper_status' "
                "when the question is just whether scraping is working; only reach for this "
                "tool when you specifically need a fresh, live check." + s.SCRAPER_BLOCKED_NOTE
            ),
            "inputSchema": s.EMPTY_SCHEMA,
        },
        {
            "name": "run_scraper",
            "description": (
                "Run the scraper pipeline for one source or every enabled source, the same "
                "code path as the daily job. THIS MAKES REAL OUTBOUND NETWORK REQUESTS to "
                "third-party sites and consumes the shared daily budget (100 listings/day, 20 "
                "requests/day across all sources combined, at most 2 pages per source per "
                "run, at least 5 seconds between requests). 'dry_run' does NOT skip the "
                "network fetch — fetching the page is how an adapter finds out what is "
                "there — it only controls whether anything found gets written to the "
                "database: with dry_run true (the default here), pages are still fetched and "
                "budget is still spent, but nothing is stored, scored, or enriched. Set "
                "dry_run to false only when you deliberately want to persist what is found. "
                "Naming a source explicitly runs that adapter even if it is individually "
                "disabled in config.json (the master 'scrapers.enabled' switch is still "
                "required either way); omit 'source' to run every source enabled in "
                "config.json instead. If scraping is off entirely ('scrapers.enabled' is "
                "false), this returns a summary explaining that and makes no network requests "
                "at all. Prefer 'scraper_status' when the question is just whether scraping "
                "is working." + s.SCRAPER_BLOCKED_NOTE
            ),
            "inputSchema": s.object_schema({
                "source": s.prop_string(
                    "Run only this adapter's key, e.g. 'repairpal'. Overrides that "
                    "source's individual config.json toggle (the master "
                    "'scrapers.enabled' switch still applies). Omit to run every "
                    "source enabled in config.json."
                ),
                "dry_run": s.prop_bool(
                    "Default true: pages are still fetched over the network and "
                    "budget is still spent, but nothing found is written to the "
                    "database. Set to false to actually store what is found.",
                    default=True,
                ),
            }),
        },
        {
            "name": "get_settings",
            "description": (
                "Read the current editable configuration fields (from config.json's "
                "search/scoring/api/enrichment/scrapers/digest/demo/web/market/discord/"
                "sources sections) plus which secrets are set, masked to their last four "
                "characters. This tool is READ-ONLY: it cannot change any setting or reveal "
                "a secret value, and there is no MCP tool on this server that does either. "
                "To change a setting or a secret, use the website's settings page or edit "
                "config.json / .env directly."
            ),
            "inputSchema": s.EMPTY_SCHEMA,
        },
    ]
