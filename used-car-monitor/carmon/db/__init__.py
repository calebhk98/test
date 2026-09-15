"""SQLite storage: listings, price history, API-usage log, and run log.

Split by concern into sibling modules, re-exported here so `carmon.db.whatever` keeps
working exactly as it did when this was one file:

* `schema`     — table DDL, migrations, connection setup, row/dict conversion.
* `listings`   — listings CRUD and price history.
* `usage`      — API-call ledger and the daily-run log.
* `enrichment` — NHTSA/EPA/RepairPal caches and the stored market appraisal.
* `scrapelog`  — scraper request ledger and adapter health status.
"""

from __future__ import annotations

from .enrichment import (
    distinct_model_years,
    get_mpg,
    get_reliability,
    get_repair_cost,
    save_appraisal,
    save_mpg,
    save_reliability,
    save_repair_cost,
)
from .listings import (
    count_listings,
    get_listing,
    get_price_history,
    mark_inactive_before,
    new_listings_since,
    price_drops_since,
    search_listings,
    upsert_listing,
)
from .schema import (
    LISTING_COLUMNS,
    MIGRATIONS,
    SCHEMA,
    SORTABLE,
    connect,
    init_db,
    migrate,
    now_str,
    row_to_dict,
    today_str,
)
from .scrapelog import (
    get_scraper_status,
    record_scrape,
    recent_scrape_events,
    save_scraper_status,
    scrape_usage_by_source,
    scrape_usage_today,
)
from .usage import (
    calls_this_month,
    finish_run,
    record_api_call,
    recent_runs,
    start_run,
    stats,
    usage_by_month,
)

__all__ = [
    "SCHEMA", "MIGRATIONS", "LISTING_COLUMNS", "SORTABLE",
    "today_str", "now_str", "connect", "migrate", "init_db", "row_to_dict",
    "get_listing", "upsert_listing", "mark_inactive_before", "search_listings",
    "count_listings", "get_price_history", "new_listings_since", "price_drops_since",
    "record_api_call", "calls_this_month", "usage_by_month",
    "start_run", "finish_run", "recent_runs", "stats",
    "get_reliability", "save_reliability", "get_mpg", "save_mpg", "distinct_model_years",
    "save_appraisal", "save_repair_cost", "get_repair_cost",
    "record_scrape", "scrape_usage_today", "scrape_usage_by_source",
    "save_scraper_status", "get_scraper_status", "recent_scrape_events",
]
