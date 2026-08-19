"""Adapter slots for non-MarketCheck sources.

Optional, opt-in, and heavily rate-limited. MarketCheck's API remains the primary source;
these adapters exist for when its free tier is not enough.

`base.py` holds the restraint: robots.txt always obeyed (and failing closed when it cannot
be read), hard daily caps enforced through a SQLite ledger, a minimum delay between
requests, and no attempt whatsoever to work around bot protection. A site that answers with
a challenge is recorded as blocked and left alone.

Everything here is **off by default** — `scrapers.enabled` plus the individual source must
both be switched on in config.json. Check a site's Terms of Service before enabling it;
several prohibit automated collection outright, and `sources.py` keeps plain browsing links
for exactly that reason.
"""

from __future__ import annotations

from .base import (  # noqa: F401  (re-exported for adapters and callers)
    REGISTRY,
    BlockedError,
    BudgetExhausted,
    Fetcher,
    RobotsCache,
    RobotsDisallowed,
    ScrapeLimits,
    ScrapeResult,
    ScraperBase,
    ScraperError,
    available,
    register,
)

# Importing an adapter module registers it. Adapters stay disabled until switched on in
# config.json under `scrapers.sources`. A broken or missing adapter must not take down the
# rest of the tool, so each import is attempted independently and failures are logged.
import importlib as _importlib  # noqa: E402
import logging as _logging  # noqa: E402

_LOG = _logging.getLogger("carmon.scrapers")

ADAPTER_MODULES = ("repairpal", "autotrader", "cars_com")

for _name in ADAPTER_MODULES:
    try:
        _importlib.import_module(f"{__name__}.{_name}")
    except Exception as _exc:  # noqa: BLE001 - a bad adapter is not a fatal condition
        _LOG.warning("Scraper adapter %r could not be loaded: %s", _name, _exc)
