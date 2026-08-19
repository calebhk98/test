"""EPA fuel economy (fueleconomy.gov) — free, public, no API key.

MarketCheck usually returns `build.city_mpg` / `build.highway_mpg`, and that is the primary
source. This module is the fallback for listings where those fields are missing, so the MPG
component of the score isn't silently zero.

The EPA's model names don't match MarketCheck's ("Civic 4Dr", not "Civic"), so a lookup is:
  1. GET /ws/rest/vehicle/menu/model?year=&make=        -> candidate model names
  2. best match by normalized prefix (shortest wins, so "Civic 4Dr" beats "Civic Type R")
  3. GET /ws/rest/vehicle/menu/options?year=&make=&model=  -> vehicle ids for that name
  4. GET /ws/rest/vehicle/{id}                          -> city08 / highway08 / comb08

Results are cached per make/model/year in the `model_mpg` table, so this costs at most a
few calls per new model-year and nothing at all thereafter.
"""

from __future__ import annotations

import logging
import sqlite3
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

from . import db
from .scoring import normalize

LOG = logging.getLogger("carmon.fueleconomy")

BASE_URL = "https://www.fueleconomy.gov/ws/rest/vehicle"

# EPA's own combined-MPG weighting, used when only city/highway are known.
CITY_WEIGHT = 0.55
HIGHWAY_WEIGHT = 0.45


class FuelEconomyError(RuntimeError):
    pass


def combined_from_city_highway(city: Optional[float], highway: Optional[float]) -> Optional[float]:
    """EPA combined estimate: 55% city, 45% highway. Falls back to whichever value exists."""
    if city and highway:
        return round(CITY_WEIGHT * float(city) + HIGHWAY_WEIGHT * float(highway), 1)
    if city:
        return round(float(city), 1)
    if highway:
        return round(float(highway), 1)
    return None


def _append_mpg(city_values: List[float], highway_values: List[float], detail: Dict[str, Any]) -> None:
    """Append one trim's city/highway MPG, in place; skip it if either figure is unusable.

    Mirrors the original inline loop exactly: if city08 parses but highway08 doesn't,
    city_values ends up one entry ahead of highway_values, same as before.
    """
    try:
        city_values.append(float(detail.get("city08")))
        highway_values.append(float(detail.get("highway08")))
    except (TypeError, ValueError):
        pass


class FuelEconomyClient:
    def __init__(
        self,
        conn: sqlite3.Connection,
        enrichment_config: Optional[Dict[str, Any]] = None,
        session: Optional[Any] = None,
    ):
        config = enrichment_config or {}
        self.conn = conn
        self.session = session or requests.Session()
        self.timeout = int(config.get("timeout_seconds", 20))
        self.cache_days = int(config.get("mpg_cache_days", config.get("cache_days", 180)))
        self.min_interval = float(config.get("min_seconds_between_calls", 0.25))
        self.calls_made = 0
        self._last_call_at = 0.0

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        elapsed = time.monotonic() - self._last_call_at
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_call_at = time.monotonic()
        try:
            response = self.session.get(
                f"{BASE_URL}{path}", params=params or {},
                headers={"Accept": "application/json"}, timeout=self.timeout,
            )
        except Exception as exc:
            raise FuelEconomyError(f"fueleconomy.gov request failed: {exc}") from exc
        self.calls_made += 1
        if getattr(response, "status_code", 0) != 200:
            raise FuelEconomyError(f"fueleconomy.gov HTTP {response.status_code}")
        try:
            return response.json()
        except ValueError as exc:
            raise FuelEconomyError("fueleconomy.gov returned non-JSON") from exc

    @staticmethod
    def _items(payload: Any) -> List[Dict[str, Any]]:
        """menuItem is a dict when the API returns exactly one option, a list otherwise."""
        if not payload:
            return []
        items = payload.get("menuItem") if isinstance(payload, dict) else payload
        if isinstance(items, dict):
            return [items]
        return [item for item in (items or []) if isinstance(item, dict)]

    def best_model_name(self, year: int, make: str, model: str) -> Optional[str]:
        candidates = [item.get("value") for item in self._items(self._get("/menu/model", {"year": year, "make": make}))]
        candidates = [name for name in candidates if name]
        if not candidates:
            return None
        target = normalize(model)
        exact = [name for name in candidates if normalize(name) == target]
        if exact:
            return exact[0]
        prefixed = [name for name in candidates if normalize(name).startswith(target)]
        if prefixed:
            return min(prefixed, key=len)  # "Civic 4Dr" over "Civic Type R"
        contained = [name for name in candidates if target and target in normalize(name)]
        return min(contained, key=len) if contained else None

    def _city_highway_values(self, vehicle_ids: List[str]) -> Tuple[List[float], List[float]]:
        """EPA city/highway MPG for a few trims of one model; unusable entries are skipped."""
        city_values: List[float] = []
        highway_values: List[float] = []
        for vehicle_id in vehicle_ids:
            detail = self._get(f"/{vehicle_id}")
            if isinstance(detail, dict):
                _append_mpg(city_values, highway_values, detail)
        return city_values, highway_values

    def lookup(self, year: int, make: str, model: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """Cached EPA city/highway/combined MPG for a model-year, or None if unavailable."""
        if not year or not make or not model:
            return None
        if not force_refresh:
            cached = db.get_mpg(self.conn, make, model, year, max_age_days=self.cache_days)
            if cached:
                return cached
        try:
            matched = self.best_model_name(year, make, model)
            if not matched:
                LOG.info("No EPA model match for %s %s %s", year, make, model)
                return None
            options = self._items(self._get("/menu/options", {"year": year, "make": make, "model": matched}))
            vehicle_ids = [item.get("value") for item in options if item.get("value")]
            if not vehicle_ids:
                return None
            city_values, highway_values = self._city_highway_values(vehicle_ids[:3])
            if not city_values:
                return None
            city = round(sum(city_values) / len(city_values), 1)
            highway = round(sum(highway_values) / len(highway_values), 1) if highway_values else None
            record = {
                "city_mpg": city,
                "highway_mpg": highway,
                "combined_mpg": combined_from_city_highway(city, highway),
                "matched_name": matched,
                "source": "fueleconomy.gov",
            }
            db.save_mpg(self.conn, make, model, year, record)
            return db.get_mpg(self.conn, make, model, year)
        except FuelEconomyError as exc:
            LOG.warning("EPA MPG lookup failed for %s %s %s: %s", year, make, model, exc)
            return db.get_mpg(self.conn, make, model, year)


def enrich_models(
    conn: sqlite3.Connection,
    model_years: List[Dict[str, Any]],
    enrichment_config: Optional[Dict[str, Any]] = None,
    client: Optional[FuelEconomyClient] = None,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    client = client or FuelEconomyClient(conn, enrichment_config)
    updated, skipped = 0, 0
    for entry in model_years:
        found = client.lookup(entry.get("year"), entry.get("make"), entry.get("model"), force_refresh)
        if found:
            updated += 1
        else:
            skipped += 1
    return {"models": len(model_years), "updated": updated, "skipped": skipped, "api_calls": client.calls_made}
