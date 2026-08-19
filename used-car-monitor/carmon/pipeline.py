"""The daily job: fetch -> normalize -> filter -> score -> upsert -> report."""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Dict, Iterable, List, Optional

from . import db, demo as demo_module, fueleconomy, market, nhtsa, quota
from .config import Config, get_secret
from .fueleconomy import combined_from_city_highway
from .marketcheck import MarketCheckClient, MarketCheckError, QuotaExceeded
from .scoring import normalize, score_listing

LOG = logging.getLogger("carmon.pipeline")


@dataclass
class RunResult:
    run_date: str
    fetched: int = 0
    kept: int = 0
    filtered_out: int = 0
    new_vins: List[str] = field(default_factory=list)
    price_change_vins: List[str] = field(default_factory=list)
    api_calls: int = 0
    api_calls_this_month: int = 0
    api_monthly_cap: int = 500
    errors: List[str] = field(default_factory=list)
    filter_reasons: Dict[str, int] = field(default_factory=dict)
    enrichment: Dict[str, Any] = field(default_factory=dict)
    sweep: Dict[str, Any] = field(default_factory=dict)
    market: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "run_date": self.run_date,
            "fetched": self.fetched,
            "kept": self.kept,
            "filtered_out": self.filtered_out,
            "new_count": len(self.new_vins),
            "price_change_count": len(self.price_change_vins),
            "api_calls": self.api_calls,
            "api_calls_this_month": self.api_calls_this_month,
            "api_monthly_cap": self.api_monthly_cap,
            "errors": self.errors,
            "filter_reasons": self.filter_reasons,
            "enrichment": self.enrichment,
            "sweep": self.sweep,
            "market": self.market,
        }


# --- normalization -------------------------------------------------------
def normalize_listing(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Map a MarketCheck listing payload onto our `listings` columns."""
    vin = (raw.get("vin") or "").strip().upper()
    if not vin:
        return None
    build = raw.get("build") or {}
    dealer = raw.get("dealer") or {}
    price = raw.get("price")
    miles = raw.get("miles")
    certified = raw.get("is_certified")
    cpo = bool(certified in (1, "1", True)) or str(raw.get("inventory_type", "")).lower() == "certified"
    return {
        "vin": vin,
        "year": _as_int(build.get("year") or raw.get("year")),
        "make": build.get("make") or raw.get("make"),
        "model": build.get("model") or raw.get("model"),
        "trim": build.get("trim") or raw.get("trim"),
        "body_type": build.get("body_type"),
        "fuel_type": build.get("fuel_type"),
        "city_mpg": _as_int(build.get("city_mpg")),
        "highway_mpg": _as_int(build.get("highway_mpg")),
        "combined_mpg": combined_from_city_highway(
            _as_int(build.get("city_mpg")), _as_int(build.get("highway_mpg"))
        ),
        "mileage": _as_int(miles),
        "price_current": _as_int(price),
        "dealer_name": dealer.get("name"),
        "dealer_city": dealer.get("city"),
        "dealer_state": dealer.get("state"),
        "distance_miles": _as_float(raw.get("dist")),
        "cpo": cpo,
        "listing_url": raw.get("vdp_url") or raw.get("url"),
        "source": "marketcheck",
        "inventory_type": raw.get("inventory_type"),
    }


def _as_int(value: Any) -> Optional[int]:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _as_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# --- client-side filtering ----------------------------------------------
def filter_reason(listing: Dict[str, Any], search: Dict[str, Any]) -> Optional[str]:
    """Return a reason string if the listing should be dropped, else None.

    The API filters most of this server-side, but body/fuel vocabularies vary by
    feed, so we re-check locally rather than trusting the query alone.
    """
    year_min = search.get("year_min")
    if year_min and listing.get("year") and listing["year"] < int(year_min):
        return "year below minimum"

    mileage_max = search.get("mileage_max")
    if mileage_max and listing.get("mileage") is not None and listing["mileage"] > int(mileage_max):
        return "mileage above maximum"

    price_max = search.get("price_max")
    if price_max and listing.get("price_current") is not None and listing["price_current"] > int(price_max):
        return "price above maximum"
    price_min = search.get("price_min")
    if price_min and listing.get("price_current") is not None and listing["price_current"] < int(price_min):
        return "price below minimum (likely a placeholder price)"

    radius = search.get("radius_miles")
    if radius and listing.get("distance_miles") is not None and listing["distance_miles"] > float(radius) + 1:
        return "outside radius"

    body = normalize(listing.get("body_type"))
    excluded_bodies = [normalize(b) for b in search.get("exclude_body_types") or []]
    if body and any(body == bad or bad in body for bad in excluded_bodies if bad):
        return f"excluded body type ({listing.get('body_type')})"
    allowed_bodies = [normalize(b) for b in search.get("body_types") or []]
    if body and allowed_bodies and not any(good in body or body in good for good in allowed_bodies if good):
        return f"body type not in allow list ({listing.get('body_type')})"

    if not search.get("include_electric_hybrid", False):
        fuel = normalize(listing.get("fuel_type"))
        for bad in search.get("excluded_fuel_types") or []:
            if fuel and normalize(bad) and normalize(bad) in fuel:
                return f"excluded fuel type ({listing.get('fuel_type')})"

    model = normalize(listing.get("model"))
    for bad_model in search.get("exclude_models") or []:
        if model and normalize(bad_model) and model.startswith(normalize(bad_model)):
            return f"excluded model ({listing.get('model')})"

    if str(listing.get("inventory_type") or "").lower() == "new":
        return "new car, not used"

    return None


# --- the run -------------------------------------------------------------
def run_daily(
    config: Config,
    conn: Optional[sqlite3.Connection] = None,
    api_key: Optional[str] = None,
    client: Optional[MarketCheckClient] = None,
    run_date: Optional[str] = None,
    dry_run: bool = False,
) -> RunResult:
    """Fetch today's matches, upsert them, and return a summary of what changed."""
    owns_conn = conn is None
    conn = conn or db.init_db(config.db_path)
    run_date = run_date or date.today().isoformat()
    search = config.search
    result = RunResult(
        run_date=run_date,
        api_monthly_cap=int(config.api.get("monthly_call_cap", 500)),
    )
    run_id = db.start_run(conn, run_date)

    # A real run never coexists with demo data — clear it before storing anything, so a
    # digest or website can never mix fake listings in with real ones.
    if not dry_run:
        cleared = demo_module.maybe_expire(conn, config, force=True)
        if cleared:
            result.errors.append(f"cleared {cleared} demo listing(s) before this run")

    try:
        if client is None:
            key = api_key or get_secret("MARKETCHECK_API_KEY", required=True)
            client = MarketCheckClient(key, conn, config.api)

        remaining = client.remaining_this_month()
        LOG.info("MarketCheck quota: %s of %s calls left this month", remaining, client.monthly_cap)

        raw_listings: List[Dict[str, Any]] = list(client.search(search))

        # Leftover free-tier calls expire at month end — spend them instead of wasting them.
        try:
            sweep_report = run_month_end_sweep(config, conn, client, run_date)
            if sweep_report.get("ran"):
                raw_listings.extend(sweep_report.pop("listings", []))
                result.sweep = sweep_report
            else:
                sweep_report.pop("listings", None)
                result.sweep = sweep_report
        except Exception as exc:  # a sweep failure must never sink the normal run
            LOG.warning("Month-end sweep skipped: %s", exc)
            result.sweep = {"ran": False, "reason": f"sweep failed: {exc}"}

        if search.get("include_certified_search", True):
            certified_search = dict(search)
            certified_search["max_pages"] = int(search.get("certified_max_pages", 2) or 2)
            try:
                raw_listings.extend(client.search(certified_search, car_type="certified"))
            except QuotaExceeded as exc:
                result.errors.append(f"certified pass skipped: {exc}")

        seen_vins: set[str] = set()
        candidates: List[Dict[str, Any]] = []
        for raw in raw_listings:
            result.fetched += 1
            listing = normalize_listing(raw)
            if not listing:
                result.filter_reasons["missing VIN"] = result.filter_reasons.get("missing VIN", 0) + 1
                result.filtered_out += 1
                continue
            if listing["vin"] in seen_vins:
                continue
            reason = filter_reason(listing, search)
            if reason:
                result.filter_reasons[reason] = result.filter_reasons.get(reason, 0) + 1
                result.filtered_out += 1
                continue
            seen_vins.add(listing["vin"])
            candidates.append(listing)

        # NHTSA complaints/recalls and EPA MPG — free, keyless, cached per model-year.
        try:
            result.enrichment = enrich_listings(config, conn, candidates)
        except Exception as exc:  # enrichment must never break the daily job
            LOG.warning("Enrichment skipped: %s", exc)
            result.errors.append(f"enrichment skipped: {exc}")

        for listing in candidates:
            existing = db.get_listing(conn, listing["vin"])
            listing["price_first_seen"] = (
                existing.get("price_first_seen") if existing else listing.get("price_current")
            )
            score = score_listing(listing, config.scoring)
            listing["score"] = score.score
            listing["score_breakdown"] = score.as_dict()["components"]

            if dry_run:
                result.kept += 1
                continue

            change = db.upsert_listing(conn, listing, seen_date=run_date)
            result.kept += 1
            if change["is_new"]:
                result.new_vins.append(listing["vin"])
            elif change["price_changed"]:
                result.price_change_vins.append(listing["vin"])

        if not dry_run:
            db.mark_inactive_before(conn, run_date)
            # Market comparison runs last: it needs every listing from this run in place
            # before it can say what "the market" looks like.
            try:
                result.market = refresh_market_values(config, conn)
            except Exception as exc:  # never let analysis sink a successful fetch
                LOG.warning("Market refresh skipped: %s", exc)
                result.errors.append(f"market refresh skipped: {exc}")

    except (MarketCheckError, QuotaExceeded) as exc:
        result.errors.append(str(exc))
        LOG.error("Run failed: %s", exc)
    finally:
        result.api_calls = client.calls_made if client else 0
        result.api_calls_this_month = db.calls_this_month(conn)
        db.finish_run(
            conn,
            run_id,
            status="error" if result.errors else "ok",
            api_calls=result.api_calls,
            listings_seen=result.kept,
            new_count=len(result.new_vins),
            price_drop_count=len(result.price_change_vins),
            error="; ".join(result.errors) or None,
        )
        if owns_conn:
            conn.close()
    return result


def rescore_all(config: Config, conn: Optional[sqlite3.Connection] = None) -> int:
    """Recompute scores for every stored listing (use after editing scoring config)."""
    owns_conn = conn is None
    conn = conn or db.init_db(config.db_path)
    rows = conn.execute("SELECT * FROM listings").fetchall()
    count = 0
    for row in rows:
        listing = attach_cached_enrichment(conn, db.row_to_dict(row))
        result = score_listing(listing, config.scoring)
        conn.execute(
            "UPDATE listings SET score = ?, score_breakdown = ? WHERE vin = ?",
            (result.score, json.dumps(result.as_dict()["components"]), listing["vin"]),
        )
        count += 1
    conn.commit()
    if owns_conn:
        conn.close()
    return count


# --- enrichment (NHTSA reliability, EPA fuel economy) --------------------
def attach_cached_enrichment(conn: sqlite3.Connection, listing: Dict[str, Any]) -> Dict[str, Any]:
    """Attach cached NHTSA/EPA facts to a listing dict. Reads the DB only, never the network."""
    make, model, year = listing.get("make"), listing.get("model"), listing.get("year")
    if not (make and model and year):
        return listing
    facts = db.get_reliability(conn, make, model, year)
    if facts:
        listing["complaint_count"] = facts.get("complaint_count")
        listing["recall_count"] = facts.get("recall_count")
        listing["top_complaint_components"] = facts.get("top_components")
        listing["nhtsa_fetched_at"] = facts.get("fetched_at")
    if not listing.get("combined_mpg"):
        mpg = db.get_mpg(conn, make, model, year)
        if mpg:
            listing.setdefault("city_mpg", mpg.get("city_mpg"))
            listing.setdefault("highway_mpg", mpg.get("highway_mpg"))
            listing["combined_mpg"] = mpg.get("combined_mpg")
            listing["mpg_source"] = mpg.get("source")
    return listing


def enrich_listings(
    config: Config,
    conn: sqlite3.Connection,
    listings: List[Dict[str, Any]],
    nhtsa_client: Optional[nhtsa.NHTSAClient] = None,
    mpg_client: Optional[fueleconomy.FuelEconomyClient] = None,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    """Fetch NHTSA complaints/recalls (and EPA MPG where missing) for every model-year seen.

    Both services are free and keyless, and results are cached per model-year, so this costs
    a handful of requests on the first run and almost nothing afterwards. Failures are logged
    and swallowed: enrichment never breaks the daily job.
    """
    enrichment_config = config.data.get("enrichment", {})
    summary: Dict[str, Any] = {"nhtsa": None, "mpg": None}

    model_years: Dict[tuple, Dict[str, Any]] = {}
    for listing in listings:
        make, model, year = listing.get("make"), listing.get("model"), listing.get("year")
        if make and model and year:
            model_years.setdefault((str(make).lower(), str(model).lower(), int(year)),
                                   {"make": make, "model": model, "year": year})
    work = list(model_years.values())[: int(enrichment_config.get("max_models_per_run", 40))]

    if enrichment_config.get("nhtsa_enabled", True) and work:
        client = nhtsa_client or nhtsa.NHTSAClient(conn, enrichment_config)
        summary["nhtsa"] = nhtsa.enrich_models(conn, work, enrichment_config, client, force_refresh)

    if enrichment_config.get("epa_mpg_enabled", True):
        missing = [
            entry for key, entry in model_years.items()
            if not any(
                l.get("combined_mpg") for l in listings
                if (str(l.get("make", "")).lower(), str(l.get("model", "")).lower(), int(l.get("year") or 0)) == key
            )
        ][: int(enrichment_config.get("max_models_per_run", 40))]
        if missing:
            client = mpg_client or fueleconomy.FuelEconomyClient(conn, enrichment_config)
            summary["mpg"] = fueleconomy.enrich_models(conn, missing, enrichment_config, client, force_refresh)

    for listing in listings:
        attach_cached_enrichment(conn, listing)
    return summary


# --- month-end sweep ----------------------------------------------------
def sweep_queries(config: Config, pages: int) -> List[Dict[str, Any]]:
    """Extra searches worth running when leftover quota would otherwise expire.

    Deep pagination first (the daily run only reads the cheapest few pages), then one
    targeted query per preferred model, which surfaces cars that price-sorted paging
    never reaches. Each query is a full search config the normal client can execute.
    """
    search = config.search
    queries: List[Dict[str, Any]] = [
        {"label": "deep pagination", "search": dict(search, max_pages=pages)},
    ]
    for entry in config.scoring.get("preferred", []) or []:
        make, model = entry.get("make"), entry.get("model")
        if not make:
            continue
        targeted = dict(search, max_pages=2)
        targeted["makes"] = [make]
        if model:
            targeted["models"] = [model]
        queries.append({"label": f"{make} {model}".strip(), "search": targeted})
    return queries


def run_month_end_sweep(
    config: Config,
    conn: sqlite3.Connection,
    client: MarketCheckClient,
    run_date: Optional[str] = None,
    today: Optional[date] = None,
) -> Dict[str, Any]:
    """Spend leftover free-tier calls on the last day of the month, before they expire.

    Free-tier calls do not roll over, so an unused balance at midnight on the last day is
    simply thrown away. This widens the search with whatever is left, keeping a reserve,
    and returns the raw listings it found plus a report of what it did.
    """
    sweep_config = config.api.get("month_end_sweep", {}) or {}
    if today is None and run_date:
        # `--date 2026-08-31` should sweep as if it were the 31st, not today.
        try:
            today = date.fromisoformat(run_date)
        except ValueError:
            today = None
    used = db.calls_this_month(conn)
    plan = quota.sweep_budget(used, int(config.api.get("monthly_call_cap", 500)), sweep_config, today)
    report: Dict[str, Any] = {
        "ran": False, "reason": plan["reason"], "budget": plan["budget"],
        "calls_used": 0, "queries": [], "listings": [],
    }
    if not plan["should_sweep"]:
        return report

    budget = plan["budget"]
    start_calls = client.calls_made
    pages = int(sweep_config.get("max_pages_per_query", 10))
    LOG.info("Month-end sweep: %s", plan["reason"])

    for query in sweep_queries(config, pages):
        spent = client.calls_made - start_calls
        if spent >= budget:
            break
        remaining_budget = budget - spent
        search = dict(query["search"])
        # Never let one query overrun the sweep budget.
        search["max_pages"] = max(1, min(int(search.get("max_pages", 1)), remaining_budget))
        try:
            found = list(client.search(search))
        except (MarketCheckError, QuotaExceeded) as exc:
            report["queries"].append({"label": query["label"], "error": str(exc)})
            break
        report["queries"].append({"label": query["label"], "listings": len(found)})
        report["listings"].extend(found)

    report["ran"] = True
    report["calls_used"] = client.calls_made - start_calls
    return report


# --- market comparison --------------------------------------------------
def refresh_market_values(
    config: Config, conn: Optional[sqlite3.Connection] = None, active_only: bool = True
) -> Dict[str, Any]:
    """Appraise every stored listing against the local market and rescore with the result.

    Runs after the fetch, because "the market" is defined by the listings that were just
    stored. Costs no API calls — it is arithmetic over the local database.
    """
    owns_conn = conn is None
    conn = conn or db.init_db(config.db_path)
    where = "WHERE active = 1 AND source != 'demo'" if active_only else "WHERE source != 'demo'"
    rows = conn.execute(f"SELECT * FROM listings {where}").fetchall()

    graded, thin = 0, 0
    deltas: List[float] = []
    for row in rows:
        listing = db.row_to_dict(row)
        appraisal = market.appraise(conn, listing, config).as_dict()
        db.save_appraisal(conn, listing["vin"], appraisal, commit=False)
        if appraisal.get("delta_pct") is not None:
            deltas.append(float(appraisal["delta_pct"]))
            if appraisal.get("sample_size", 0) >= int(config.data.get("market", {}).get("min_sample_for_grade", 6)):
                graded += 1
            else:
                thin += 1

        listing.update({
            "market_delta_pct": appraisal.get("delta_pct"),
            "market_sample_size": appraisal.get("sample_size"),
            "market_grade": appraisal.get("grade"),
        })
        attach_cached_enrichment(conn, listing)
        result = score_listing(listing, config.scoring)
        conn.execute(
            "UPDATE listings SET score = ?, score_breakdown = ? WHERE vin = ?",
            (result.score, json.dumps(result.as_dict()["components"]), listing["vin"]),
        )
    conn.commit()

    summary = {
        "listings_appraised": len(rows),
        "graded": graded,
        "thin_sample": thin,
        "median_delta_pct": round(sorted(deltas)[len(deltas) // 2], 1) if deltas else None,
        "below_market": sum(1 for delta in deltas if delta < -5),
    }
    if owns_conn:
        conn.close()
    return summary
