"""Running the optional scraper adapters — a separate concern from the MarketCheck daily run.

Scraped listings go through exactly the same filtering, enrichment and scoring as
MarketCheck ones (via `carmon.pipeline`), and dedupe against them by VIN. Everything is off
unless `scrapers.enabled` and the individual source are both switched on in config.json; the
daily caps live in `carmon/scrapers/base.py` and are enforced against a ledger table, not an
in-memory counter.
"""

from __future__ import annotations

import logging
import sqlite3
import sys
from datetime import date
from typing import Any, Dict, List, Optional

from . import db
from .config import Config
from .pipeline import enrich_listings, filter_reason
from .scoring import score_listing

LOG = logging.getLogger("carmon.scrape_runner")


def run_scrapers(
    config: Config,
    conn: Optional[sqlite3.Connection] = None,
    sources: Optional[List[str]] = None,
    run_date: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Run the enabled scraper adapters and fold what they find into the same pipeline.

    Two behaviours worth being explicit about:

    * ``dry_run`` still fetches. It suppresses *storage*, not network traffic — the point of
      a dry run is to see what a source actually returns and whether it parses, which cannot
      be answered without asking. It spends daily budget exactly like a real run. This
      matches ``carmon run --dry-run``, which also queries MarketCheck and writes nothing.
    * Naming ``sources`` explicitly overrides the per-source toggle in config.json, so
      ``carmon scrape --source repairpal`` runs that adapter even when it is switched off.
      The master ``scrapers.enabled`` switch is never bypassed.
    """
    from .scrapers import REGISTRY, ScrapeLimits  # imported lazily: adapters are optional

    owns_conn = conn is None
    conn = conn or db.init_db(config.db_path)
    run_date = run_date or date.today().isoformat()
    scraper_config = config.data.get("scrapers", {}) or {}
    summary: Dict[str, Any] = {"enabled": bool(scraper_config.get("enabled")), "sources": {},
                               "kept": 0, "new": 0, "skipped": []}

    if not summary["enabled"]:
        summary["message"] = (
            "Scrapers are off. Turn on `scrapers.enabled` and the individual source in config.json "
            "(or on the website's Settings page) after reviewing that site's Terms of Service."
        )
        if owns_conn:
            conn.close()
        return summary

    limits = ScrapeLimits.from_config(scraper_config)
    enabled_sources = scraper_config.get("sources", {}) or {}
    # Walk every registered adapter, not just the enabled ones, so the summary can say why
    # a source did nothing instead of silently omitting it.
    wanted = sources or sorted(set(REGISTRY) | set(enabled_sources))
    usage = db.scrape_usage_today(conn)
    summary["budget_before"] = {
        "requests_used": usage["requests"], "requests_cap": limits.max_requests_per_day,
        "listings_used": usage["listings"], "listings_cap": limits.max_listings_per_day,
    }

    summary["dry_run"] = bool(dry_run)
    if dry_run:
        summary["dry_run_note"] = (
            "Dry run: pages were still fetched and parsed (and counted against the daily caps) "
            "but nothing was stored."
        )
    if sources:
        summary["override_note"] = (
            f"Explicitly requested {', '.join(sources)} — per-source config toggles were bypassed "
            "for this run. The master scrapers.enabled switch still applies."
        )

    for key in wanted:
        _run_one_source(key, REGISTRY.get(key), config, conn, limits, enabled_sources,
                        bool(sources), run_date, dry_run, summary)

    usage = db.scrape_usage_today(conn)
    summary["budget_after"] = {
        "requests_used": usage["requests"], "requests_cap": limits.max_requests_per_day,
        "listings_used": usage["listings"], "listings_cap": limits.max_listings_per_day,
    }
    if owns_conn:
        conn.close()
    return summary


def _run_one_source(
    key: str,
    scraper_class: Any,
    config: Config,
    conn: sqlite3.Connection,
    limits: Any,
    enabled_sources: Dict[str, Any],
    forced: bool,
    run_date: str,
    dry_run: bool,
    summary: Dict[str, Any],
) -> None:
    """Run (or skip) one adapter, folding its result into `summary` in place."""
    if scraper_class is None:
        summary["skipped"].append(f"{key}: no adapter registered")
        return
    if not forced and not enabled_sources.get(key):
        summary["skipped"].append(f"{key}: disabled in config")
        return

    scraper = scraper_class(conn, limits)

    if getattr(scraper_class, "kind", "listings") == "reference":
        # A reference source is keyed by model, not by the listing search, so it runs once
        # per model we actually care about: whatever is already stored, then the preferred
        # list. Without this it would be handed a search with no make/model and quietly do
        # nothing.
        entry = _run_reference_scraper(config, conn, scraper, scraper_class, dry_run)
        db.save_scraper_status(conn, key, entry)
        summary["sources"][key] = entry
        return

    result = scraper.run(dict(config.search))
    entry = result.as_dict()
    kept = [listing for listing in result.listings if not filter_reason(listing, config.search)]

    if kept and not dry_run:
        entry["new"] = _store_scraped_listings(config, conn, kept, run_date)
        summary["new"] += entry["new"]

    entry["kept_after_filters"] = len(kept)
    db.save_scraper_status(conn, key, entry)
    summary["kept"] += len(kept)
    summary["sources"][key] = entry


def _store_scraped_listings(
    config: Config, conn: sqlite3.Connection, kept: List[Dict[str, Any]], run_date: str
) -> int:
    """Enrich, score and upsert scraped listings that survived filtering. Returns new-VIN count."""
    try:
        enrich_listings(config, conn, kept)
    except Exception as exc:
        LOG.warning("Enrichment for scraped listings skipped: %s", exc)

    new_count = 0
    for listing in kept:
        existing = db.get_listing(conn, listing["vin"])
        listing["price_first_seen"] = (
            existing.get("price_first_seen") if existing else listing.get("price_current")
        )
        score = score_listing(listing, config.scoring)
        listing["score"] = score.score
        listing["score_breakdown"] = score.as_dict()["components"]
        change = db.upsert_listing(conn, listing, seen_date=run_date)
        new_count += 1 if change["is_new"] else 0
    return new_count


def reference_models(config: Config, conn: sqlite3.Connection, limit: int = 10) -> List[Dict[str, str]]:
    """Which make/model pairs a reference source (RepairPal) should be asked about.

    Models already in the database first — those are cars actually for sale near you — then
    the preferred list, so a fresh database still gets useful data on day one.
    """
    seen: Dict[tuple, Dict[str, str]] = {}
    for row in db.distinct_model_years(conn, active_only=True):
        key = (str(row["make"]).lower(), str(row["model"]).lower())
        seen.setdefault(key, {"make": row["make"], "model": row["model"]})
    for entry in config.scoring.get("preferred", []) or []:
        make, model = entry.get("make"), entry.get("model")
        if make and model:
            seen.setdefault((make.lower(), model.lower()), {"make": make, "model": model})
    return list(seen.values())[:limit]


def _run_reference_scraper(
    config: Config,
    conn: sqlite3.Connection,
    scraper: Any,
    scraper_class: Any,
    dry_run: bool,
) -> Dict[str, Any]:
    """Run a per-model reference adapter over the models worth knowing about."""
    store = getattr(sys.modules[scraper_class.__module__], "store", None)
    models = reference_models(config, conn)
    entry: Dict[str, Any] = {
        "source": scraper_class.key, "status": "ok", "message": "", "pages_fetched": 0,
        "listings": 0, "stored": 0, "models": [], "urls": [],
    }
    if not models:
        entry.update(status="empty", message="no models to look up yet")
        return entry

    for model in models:
        # Each model costs a request, so stop as soon as the shared daily budget is gone.
        if scraper.fetcher.budget_left()["requests"] <= 0:
            entry["status"] = "budget"
            entry["message"] = "daily request cap reached; remaining models skipped"
            break
        if not _run_one_reference_model(scraper, model, entry, dry_run, store, conn):
            break  # a wall for one model is a wall for all of them
    return entry


def _run_one_reference_model(scraper: Any, model: Dict[str, str], entry: Dict[str, Any],
                             dry_run: bool, store: Any, conn: sqlite3.Connection) -> bool:
    """Run one model through a reference scraper; returns False if the run should stop here."""
    result = scraper.run(model)
    entry["pages_fetched"] += result.pages_fetched
    entry["listings"] += len(result.listings)
    entry["urls"].extend(result.urls)
    entry["models"].append({
        "make": model["make"], "model": model["model"],
        "status": result.status, "records": len(result.listings),
    })
    keep_going = True
    if result.status != "ok":
        entry["status"] = result.status
        entry["message"] = result.message
        if result.status in ("blocked", "disallowed", "budget"):
            keep_going = False
    if not dry_run and store:
        for record in result.listings:
            store(conn, record)
            entry["stored"] += 1
    return keep_going


def probe_scrapers(config: Config, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
    """One request per adapter: can this source actually be reached and parsed from here?"""
    from .scrapers import REGISTRY, ScrapeLimits

    owns_conn = conn is None
    conn = conn or db.init_db(config.db_path)
    limits = ScrapeLimits.from_config(config.data.get("scrapers", {}))
    results = []
    for key, scraper_class in sorted(REGISTRY.items()):
        scraper = scraper_class(conn, limits)
        search = dict(config.search)
        if getattr(scraper_class, "kind", "listings") == "reference":
            preferred = (config.scoring.get("preferred") or [{}])[0]
            search.update({"make": preferred.get("make", "Toyota"), "model": preferred.get("model", "Corolla")})
        try:
            entry = scraper.probe(search)
        except Exception as exc:
            entry = {"source": key, "name": getattr(scraper_class, "name", key),
                     "status": "error", "message": str(exc)}
        db.save_scraper_status(conn, key, entry)
        results.append(entry)
    if owns_conn:
        conn.close()
    return results
