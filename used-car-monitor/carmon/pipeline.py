"""The daily job: fetch -> normalize -> filter -> score -> upsert -> report."""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Dict, Iterable, List, Optional

from . import db
from .config import Config, get_secret
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

    try:
        if client is None:
            key = api_key or get_secret("MARKETCHECK_API_KEY", required=True)
            client = MarketCheckClient(key, conn, config.api)

        remaining = client.remaining_this_month()
        LOG.info("MarketCheck quota: %s of %s calls left this month", remaining, client.monthly_cap)

        raw_listings: List[Dict[str, Any]] = list(client.search(search))
        if search.get("include_certified_search", True):
            certified_search = dict(search)
            certified_search["max_pages"] = int(search.get("certified_max_pages", 2) or 2)
            try:
                raw_listings.extend(client.search(certified_search, car_type="certified"))
            except QuotaExceeded as exc:
                result.errors.append(f"certified pass skipped: {exc}")

        seen_vins: set[str] = set()
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
        listing = db.row_to_dict(row)
        result = score_listing(listing, config.scoring)
        conn.execute(
            "UPDATE listings SET score = ?, score_breakdown = ? WHERE vin = ?",
            (result.score, __import__("json").dumps(result.as_dict()["components"]), listing["vin"]),
        )
        count += 1
    conn.commit()
    if owns_conn:
        conn.close()
    return count
