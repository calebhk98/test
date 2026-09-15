"""Tool handler implementations: one function per MCP tool, dispatched by
name from TOOL_HANDLERS. Each handler takes the live MCPServer instance (for
its lazy db connection and config) and the tool's already-decoded arguments
dict, and returns an MCP tools/call result built via protocol.text_result.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .. import db as dbmod
from .. import demo as demomod
from .. import market as marketmod
from .. import quota as quotamod
from .. import scoring as scoringmod
from .. import settings as settingsmod
from .. import sources as sourcesmod
from ..result_shapes import count_envelope, reliability_row_to_dict
from ..result_shapes import nhtsa_urls as _shaped_nhtsa_urls

from .imports import import_required, try_import
from .params import (
    as_int,
    clamped_int,
    days_ago_str,
    opt_float,
    opt_int,
    opt_number,
    require_int,
    require_str,
)
from .protocol import ToolError, text_result

# --------------------------------------------------------------------------
# Shared helpers
#
# These fold in the pieces that used to be duplicated across handlers: the
# demo-data warning, the '{count, listings, ...}' envelope shared by every
# listing-shaped tool, cached-enrichment attachment, and the NHTSA.gov URL
# lookups -- each of which used to be its own inline try/except ImportError.
# `count_envelope` and `reliability_row_to_dict` are the same data shape the
# web API builds too (see carmon.result_shapes); what stays here is MCP-only:
# the text_result/isError envelope and the lazy nhtsa import.
# --------------------------------------------------------------------------

def with_demo_warning(server, payload: Dict[str, Any], listings: List[Optional[Dict[str, Any]]]) -> Dict[str, Any]:
    """Add a top-level 'warning' key when any of the given listings is demo data.

    Does not set isError: the data is still returned, it is just flagged so an
    assistant never presents seeded demo rows as real cars.
    """
    if any(listing and listing.get("source") == demomod.DEMO_SOURCE for listing in listings):
        payload["warning"] = demomod.demo_banner(server.conn)
    return payload


def listings_result(server, rows: List[Dict[str, Any]], **extra: Any) -> Dict[str, Any]:
    """Build the '{..., count, listings}' + demo-warning + text-result envelope
    shared by search_listings, top_listings, new_listings, price_drops,
    best_deals and list_comparables."""
    payload = count_envelope("listings", rows, **extra)
    return text_result(with_demo_warning(server, payload, rows))


def attach_enrichment(server, listing: Dict[str, Any]) -> Dict[str, Any]:
    """Attach cached NHTSA/EPA facts to a listing dict, DB-only, never the network."""
    (attach_cached_enrichment,) = try_import("pipeline", "attach_cached_enrichment")
    if attach_cached_enrichment is None:
        return listing
    try:
        return attach_cached_enrichment(server.conn, listing)
    except Exception:  # noqa: BLE001 - enrichment is a bonus, never fail the tool over it
        return listing


def nhtsa_model_url(make: str, model: str, year: int) -> Optional[str]:
    (recall_lookup_url,) = try_import("nhtsa", "recall_lookup_url")
    return recall_lookup_url(make, model, year) if recall_lookup_url else None


def nhtsa_urls(vin: str, listing: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """Return (vin_url, model_url) NHTSA.gov links for a listing, via a lazy
    nhtsa import. Both are None if the nhtsa module is unavailable."""
    recall_lookup_url, vin_recall_url = try_import("nhtsa", "recall_lookup_url", "vin_recall_url")
    return _shaped_nhtsa_urls(
        vin, listing.get("make"), listing.get("model"), listing.get("year"),
        vin_recall_url, recall_lookup_url,
    )


def latest_digest_text(config) -> str:
    (latest_digest_path,) = try_import("digest", "latest_digest_path")
    if latest_digest_path is None:
        return "No digest yet: the digest module is not available."
    try:
        path = latest_digest_path(config)
    except Exception as exc:  # noqa: BLE001
        return f"No digest yet: could not determine latest digest ({exc})."
    if not path:
        return "No digest yet: no digest has been generated."
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        return f"No digest yet: could not read digest file {path} ({exc})."


def _scraper_source_row(key, adapter, row, usage, configured_sources) -> Dict[str, Any]:
    """One row of scraper_status's 'sources' list: static adapter metadata
    merged with its config toggle and its last recorded run from the
    database. `field` flattens the repeated '<x> if row else <default>'
    ternary that used to appear once per column."""

    def field(name, default=None):
        return row.get(name, default) if row else default

    return {
        "source": key,
        "name": getattr(adapter, "name", key),
        "site": getattr(adapter, "site", None),
        "kind": getattr(adapter, "kind", "listings"),
        "registered": adapter is not None,
        "config_enabled": bool(configured_sources.get(key, False)),
        "status": field("status", "never run"),
        "message": field("message", "") or "",
        "last_run_at": field("last_run_at"),
        "pages": field("pages", 0),
        "listings": field("listings", 0),
        "kept": field("kept", 0),
        "ok_runs": field("ok_runs", 0),
        "failed_runs": field("failed_runs", 0),
        "last_ok_at": field("last_ok_at"),
        "last_error": field("last_error"),
        "last_error_at": field("last_error_at"),
        "requests_today": usage.get("requests", 0),
        "listings_today": usage.get("listings", 0),
    }


# --------------------------------------------------------------------------
# Listings & search
# --------------------------------------------------------------------------

def t_search_listings(server, args: Dict[str, Any]) -> Dict[str, Any]:
    limit = clamped_int(args, "limit", 20, 1, 100)
    offset = as_int(args.get("offset", 0), "offset", default=0)
    sort = args.get("sort", "score") or "score"
    if sort not in dbmod.SORTABLE:
        raise ToolError(
            f"Invalid sort '{sort}'. Must be one of: {', '.join(sorted(dbmod.SORTABLE))}"
        )
    max_complaints = opt_int(args.get("max_complaints"))
    max_recalls = opt_int(args.get("max_recalls"))
    # Fetch a bit more than requested when post-filtering by NHTSA data, since some
    # rows may be dropped; db-level limit/offset still apply to the base query.
    rows = dbmod.search_listings(
        server.conn,
        make=args.get("make") or None,
        model=args.get("model") or None,
        max_price=opt_int(args.get("max_price")),
        min_price=opt_int(args.get("min_price")),
        max_mileage=opt_int(args.get("max_mileage")),
        min_year=opt_int(args.get("min_year")),
        max_distance=opt_float(args.get("max_distance")),
        min_score=opt_float(args.get("min_score")),
        cpo_only=bool(args.get("cpo_only", False)),
        active_only=bool(args.get("active_only", True)),
        query=args.get("query") or None,
        sort=sort,
        limit=limit,
        offset=offset,
    )
    if max_complaints is not None or max_recalls is not None:
        filtered = []
        for row in rows:
            row = attach_enrichment(server, row)
            complaints = row.get("complaint_count")
            recalls = row.get("recall_count")
            # No cached NHTSA data (None) means "unknown", which is kept rather
            # than excluded — unknown is not the same as bad.
            if max_complaints is not None and complaints is not None and complaints > max_complaints:
                continue
            if max_recalls is not None and recalls is not None and recalls > max_recalls:
                continue
            filtered.append(row)
        rows = filtered
    return listings_result(server, rows)


def t_get_listing(server, args: Dict[str, Any]) -> Dict[str, Any]:
    vin = require_str(args, "vin")
    listing = dbmod.get_listing(server.conn, vin)
    if listing is None:
        return text_result(f"No listing found with VIN '{vin}'.", is_error=True, as_json=False)
    listing = attach_enrichment(server, listing)
    history = dbmod.get_price_history(server.conn, vin)
    cross_shop = sourcesmod.sources_for_listing(listing, server.config.search)
    vin_url, model_url = nhtsa_urls(vin, listing)
    appraisal = marketmod.appraise_vin(server.conn, vin, server.config)
    return text_result(with_demo_warning(server, {
        "listing": listing,
        "price_history": history,
        "cross_shop_links": cross_shop,
        "nhtsa_vin_url": vin_url,
        "nhtsa_model_url": model_url,
        "appraisal": appraisal.as_dict() if appraisal is not None else None,
    }, [listing]))


def t_get_price_history(server, args: Dict[str, Any]) -> Dict[str, Any]:
    vin = require_str(args, "vin")
    listing = dbmod.get_listing(server.conn, vin)
    if listing is None:
        return text_result(f"No listing found with VIN '{vin}'.", is_error=True, as_json=False)
    history = dbmod.get_price_history(server.conn, vin)
    return text_result({"vin": vin, "price_history": history})


def t_top_listings(server, args: Dict[str, Any]) -> Dict[str, Any]:
    limit = clamped_int(args, "limit", 5, 1, 100)
    rows = dbmod.search_listings(server.conn, active_only=True, sort="score", limit=limit)
    return listings_result(server, rows)


def t_new_listings(server, args: Dict[str, Any]) -> Dict[str, Any]:
    days = clamped_int(args, "days", 1, 1)
    limit = clamped_int(args, "limit", 50, 1, 500)
    since = days_ago_str(days)
    rows = dbmod.new_listings_since(server.conn, since, limit=limit)
    return listings_result(server, rows, since=since)


def t_price_drops(server, args: Dict[str, Any]) -> Dict[str, Any]:
    days = clamped_int(args, "days", 1, 1)
    limit = clamped_int(args, "limit", 50, 1, 500)
    since = days_ago_str(days)
    rows = dbmod.price_drops_since(server.conn, since, limit=limit)
    return listings_result(server, rows, since=since)


# --------------------------------------------------------------------------
# Stats, quota, digest, scoring
# --------------------------------------------------------------------------

def t_get_stats(server, args: Dict[str, Any]) -> Dict[str, Any]:
    monthly_cap = int(server.config.api.get("monthly_call_cap", 500) or 500)
    result = dbmod.stats(server.conn, monthly_cap=monthly_cap)
    result["pace"] = quotamod.pace(result["api_calls_this_month"], monthly_cap)
    result["demo_listings"] = demomod.demo_count(server.conn)
    result["demo_warning"] = demomod.demo_banner(server.conn)
    return text_result(result)


def t_get_quota_pace(server, args: Dict[str, Any]) -> Dict[str, Any]:
    width = clamped_int(args, "width", 24, 4)
    monthly_cap = int(server.config.api.get("monthly_call_cap", 500) or 500)
    metrics = quotamod.pace_from_db(server.conn, monthly_cap)
    sweep_config = server.config.data.get("api", {}).get("month_end_sweep", {})
    result = dict(metrics)
    result["summary"] = quotamod.summary_line(metrics)
    result["bar"] = quotamod.bar(metrics, width=width)
    result["month_end_sweep"] = quotamod.sweep_budget(metrics["used"], metrics["cap"], sweep_config)
    return text_result(result)


def t_get_latest_digest(server, args: Dict[str, Any]) -> Dict[str, Any]:
    text = latest_digest_text(server.config)
    is_error = text.startswith("No digest")
    return text_result(text, is_error=is_error, as_json=False)


def t_explain_score(server, args: Dict[str, Any]) -> Dict[str, Any]:
    vin = require_str(args, "vin")
    listing = dbmod.get_listing(server.conn, vin)
    if listing is None:
        return text_result(f"No listing found with VIN '{vin}'.", is_error=True, as_json=False)
    listing = attach_enrichment(server, listing)
    recomputed = scoringmod.score_listing(listing, server.config.scoring)
    return text_result({
        "vin": vin,
        "stored_score": listing.get("score"),
        "stored_breakdown": listing.get("score_breakdown"),
        "recomputed": recomputed.as_dict(),
        "explanation": recomputed.explain(),
    })


def t_score_hypothetical(server, args: Dict[str, Any]) -> Dict[str, Any]:
    listing = {
        "make": args.get("make") or "",
        "model": args.get("model") or "",
        "year": opt_int(args.get("year")),
        "mileage": opt_number(args.get("mileage")),
        "distance_miles": opt_number(args.get("distance_miles")),
        "price_current": opt_number(args.get("price_current")),
        "price_first_seen": opt_number(args.get("price_first_seen")),
        "cpo": bool(args.get("cpo", False)),
        "combined_mpg": opt_number(args.get("combined_mpg")),
        "complaint_count": opt_int(args.get("complaint_count")),
        "recall_count": opt_int(args.get("recall_count")),
    }
    result = scoringmod.score_listing(listing, server.config.scoring)
    return text_result({
        "input": listing,
        "result": result.as_dict(),
        "explanation": result.explain(),
    })


def t_list_sources(server, args: Dict[str, Any]) -> Dict[str, Any]:
    grouped = sourcesmod.grouped_sources(server.config.search)
    return text_result({"sources": grouped})


# --------------------------------------------------------------------------
# NHTSA reliability
# --------------------------------------------------------------------------

def t_get_reliability(server, args: Dict[str, Any]) -> Dict[str, Any]:
    make = require_str(args, "make")
    model = require_str(args, "model")
    year = require_int(args, "year")
    record = dbmod.get_reliability(server.conn, make, model, year)
    if record is None:
        return text_result(
            f"No cached NHTSA reliability data for {year} {make} {model}. Run "
            "`python3 -m carmon enrich` to populate the cache for current listings, or "
            "call the 'refresh_reliability' tool to fetch just this model/year now.",
            is_error=True,
            as_json=False,
        )
    record = dict(record)
    record["nhtsa_url"] = nhtsa_model_url(make, model, year)
    record["caveat"] = (
        "Complaint and recall counts are raw federal totals from NHTSA, NOT adjusted for "
        "how many of this model were sold — a high-volume model naturally accumulates more "
        "complaints than a rare one. The recurring complaint components (top_components) "
        "are a stronger signal than the raw counts."
    )
    return text_result(record)


def t_refresh_reliability(server, args: Dict[str, Any]) -> Dict[str, Any]:
    make = require_str(args, "make")
    model = require_str(args, "model")
    year = require_int(args, "year")
    force = bool(args.get("force", False))
    NHTSAClient, NHTSAError = import_required("nhtsa", "NHTSA client", "NHTSAClient", "NHTSAError")

    enrichment_config = server.config.data.get("enrichment", {})
    client = NHTSAClient(server.conn, enrichment_config)
    try:
        facts = client.facts_for(make, model, year, force_refresh=force)
    except NHTSAError as exc:
        return text_result(
            f"NHTSA lookup failed for {year} {make} {model}: {exc}", is_error=True, as_json=False
        )
    except Exception as exc:  # noqa: BLE001 - network calls can fail in many ways
        return text_result(
            f"NHTSA lookup failed for {year} {make} {model}: {exc}", is_error=True, as_json=False
        )
    if facts is None:
        return text_result(
            f"Could not fetch NHTSA data for {year} {make} {model}: the request failed and "
            "nothing was already cached.",
            is_error=True,
            as_json=False,
        )
    result = dict(facts)
    result["nhtsa_url"] = nhtsa_model_url(make, model, year)
    result["api_calls_made"] = client.calls_made
    return text_result(result)


def t_list_reliability(server, args: Dict[str, Any]) -> Dict[str, Any]:
    limit = clamped_int(args, "limit", 25, 1, 500)
    rows = server.conn.execute(
        "SELECT * FROM model_reliability ORDER BY complaint_count DESC LIMIT ?", (limit,)
    ).fetchall()
    models = [reliability_row_to_dict(row) for row in rows]
    return text_result({"count": len(models), "models": models})


# --------------------------------------------------------------------------
# Market / appraisal
# --------------------------------------------------------------------------

def t_appraise_car(server, args: Dict[str, Any]) -> Dict[str, Any]:
    vin = args.get("vin") or None
    if vin:
        result = marketmod.appraise_vin(server.conn, vin, server.config)
        if result is None:
            return text_result(f"No listing found with VIN '{vin}'.", is_error=True, as_json=False)
        return text_result(result.as_dict())

    car = {
        "make": args.get("make") or "",
        "model": args.get("model") or "",
        "year": opt_int(args.get("year")),
        "mileage": opt_number(args.get("mileage")),
        "price_current": opt_number(args.get("price")),
    }
    result = marketmod.appraise(server.conn, car, server.config)
    return text_result(result.as_dict())


def t_market_trend(server, args: Dict[str, Any]) -> Dict[str, Any]:
    make = args.get("make") or None
    model = args.get("model") or None
    months = clamped_int(args, "months", 6, 1, 60)
    trend = marketmod.price_trend(server.conn, make=make, model=model, months=months)
    return text_result({
        "make": make,
        "model": model,
        "months": months,
        "trend": trend,
        "days_on_market": marketmod.days_on_market(server.conn, make=make, model=model),
        "price_cuts": marketmod.price_cut_stats(server.conn, make=make, model=model),
        "data_note": (
            "Cross-sectional price-versus-mileage comparisons (see 'appraise_car') work "
            "from the first run. This trend, days-on-market and price-cut data is "
            "longitudinal and needs weeks of accumulated history to be meaningful."
        ),
    })


def t_market_report(server, args: Dict[str, Any]) -> Dict[str, Any]:
    months = clamped_int(args, "months", 6, 1, 60)
    return text_result(marketmod.market_report(server.conn, months=months, config=server.config))


def t_best_deals(server, args: Dict[str, Any]) -> Dict[str, Any]:
    limit = clamped_int(args, "limit", 10, 1, 100)
    min_sample = clamped_int(args, "min_sample", 3, 1)
    rows = marketmod.best_deals(server.conn, limit=limit, min_sample=min_sample, config=server.config)
    return listings_result(server, rows)


def t_list_comparables(server, args: Dict[str, Any]) -> Dict[str, Any]:
    make = require_str(args, "make")
    model = require_str(args, "model")
    year = opt_int(args.get("year"))
    year_window = clamped_int(args, "year_window", 1, 0)
    limit = clamped_int(args, "limit", 25, 1, 500)
    rows = marketmod.comparables(server.conn, make=make, model=model, year=year, year_window=year_window)
    rows = rows[:limit]
    return listings_result(server, rows)


# --------------------------------------------------------------------------
# Scrapers
# --------------------------------------------------------------------------

def t_scraper_status(server, args: Dict[str, Any]) -> Dict[str, Any]:
    source = args.get("source") or None
    (registry,) = try_import("scrapers", "REGISTRY")
    registry = registry or {}

    scraper_config = server.config.data.get("scrapers", {}) or {}
    master_enabled = bool(scraper_config.get("enabled"))
    configured_sources = scraper_config.get("sources", {}) or {}
    status_rows = {row["source"]: row for row in dbmod.get_scraper_status(server.conn)}
    usage_by_source = {row["source"]: row for row in dbmod.scrape_usage_by_source(server.conn)}

    keys = set(registry) | set(configured_sources) | set(status_rows)
    if source:
        if source not in keys:
            raise ToolError(
                f"Unknown scraper source '{source}'. Known: {', '.join(sorted(keys)) or '(none registered)'}"
            )
        keys = {source}

    sources_out = [
        _scraper_source_row(
            key, registry.get(key), status_rows.get(key),
            usage_by_source.get(key, {"requests": 0, "listings": 0}),
            configured_sources,
        )
        for key in sorted(keys)
    ]

    usage_today = dbmod.scrape_usage_today(server.conn)
    usage_today["requests_cap"] = int(scraper_config.get("max_requests_per_day", 20) or 20)
    usage_today["listings_cap"] = int(scraper_config.get("max_listings_per_day", 100) or 100)

    return text_result({
        "scrapers_enabled": master_enabled,
        "sources": sources_out,
        "usage_today": usage_today,
        "limits": {
            "max_pages_per_run": int(scraper_config.get("max_pages_per_run", 2) or 2),
            "min_seconds_between_requests": scraper_config.get("min_seconds_between_requests", 5),
        },
    })


def t_scraper_events(server, args: Dict[str, Any]) -> Dict[str, Any]:
    limit = clamped_int(args, "limit", 25, 1, 200)
    source = args.get("source") or None
    rows = dbmod.recent_scrape_events(server.conn, limit=limit, source=source)
    return text_result({"count": len(rows), "events": rows})


def t_probe_scrapers(server, args: Dict[str, Any]) -> Dict[str, Any]:
    probe_scrapers_fn = import_required("pipeline", "Scraper pipeline", "probe_scrapers")
    results = probe_scrapers_fn(server.config, server.conn)
    return text_result({"count": len(results), "results": results})


def t_run_scraper(server, args: Dict[str, Any]) -> Dict[str, Any]:
    source = args.get("source") or None
    dry_run = bool(args.get("dry_run", True))
    run_scrapers_fn = import_required("pipeline", "Scraper pipeline", "run_scrapers")
    result = run_scrapers_fn(
        server.config, server.conn, sources=[source] if source else None, dry_run=dry_run
    )
    return text_result(result)


# --------------------------------------------------------------------------
# Settings
# --------------------------------------------------------------------------

def t_get_settings(server, args: Dict[str, Any]) -> Dict[str, Any]:
    return text_result({
        "fields": settingsmod.editable_settings(server.config),
        "secrets": settingsmod.secrets_status(),
    })


TOOL_HANDLERS = {
    "search_listings": t_search_listings,
    "get_listing": t_get_listing,
    "get_price_history": t_get_price_history,
    "top_listings": t_top_listings,
    "new_listings": t_new_listings,
    "price_drops": t_price_drops,
    "get_stats": t_get_stats,
    "get_quota_pace": t_get_quota_pace,
    "get_latest_digest": t_get_latest_digest,
    "explain_score": t_explain_score,
    "score_hypothetical": t_score_hypothetical,
    "list_sources": t_list_sources,
    "get_reliability": t_get_reliability,
    "refresh_reliability": t_refresh_reliability,
    "list_reliability": t_list_reliability,
    "appraise_car": t_appraise_car,
    "market_trend": t_market_trend,
    "market_report": t_market_report,
    "best_deals": t_best_deals,
    "list_comparables": t_list_comparables,
    "scraper_status": t_scraper_status,
    "scraper_events": t_scraper_events,
    "probe_scrapers": t_probe_scrapers,
    "run_scraper": t_run_scraper,
    "get_settings": t_get_settings,
}
