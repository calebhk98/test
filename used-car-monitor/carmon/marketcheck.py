"""MarketCheck Inventory Search API client.

Free tier constraints this client enforces:
  * 500 calls/month  -> every call is logged to the `api_usage` table and the client
                        refuses to start a run that would exceed the cap.
  * 5 calls/second   -> a simple monotonic-clock throttle between requests.
  * 100 mile radius  -> radius is clamped and a warning is logged if config asks for more.

Endpoint: GET https://api.marketcheck.com/v2/search/car/active
"""

from __future__ import annotations

import logging
import sqlite3
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterator, List, Optional

import requests

from . import db

LOG = logging.getLogger("carmon.marketcheck")

FREE_TIER_MAX_RADIUS = 100
MAX_ROWS_PER_PAGE = 50


class QuotaExceeded(RuntimeError):
    """Raised when the configured monthly call cap would be exceeded."""


class MarketCheckError(RuntimeError):
    """Raised for non-retryable API errors."""


@dataclass
class SearchPage:
    num_found: int
    listings: List[Dict[str, Any]] = field(default_factory=list)


class MarketCheckClient:
    def __init__(
        self,
        api_key: str,
        conn: sqlite3.Connection,
        api_config: Optional[Dict[str, Any]] = None,
        session: Optional[Any] = None,
    ):
        if not api_key:
            raise MarketCheckError("MARKETCHECK_API_KEY is empty — see .env.example")
        api_config = api_config or {}
        self.api_key = api_key
        self.conn = conn
        self.base_url = api_config.get("base_url", "https://api.marketcheck.com/v2/search/car/active")
        self.monthly_cap = int(api_config.get("monthly_call_cap", 500))
        self.calls_per_second = float(api_config.get("calls_per_second", 5)) or 5.0
        self.stop_at_cap = bool(api_config.get("stop_at_monthly_cap", True))
        self.timeout = int(api_config.get("timeout_seconds", 30))
        self.max_retries = int(api_config.get("max_retries", 3))
        self.session = session or requests.Session()
        self._min_interval = 1.0 / self.calls_per_second
        self._last_call_at = 0.0
        self.calls_made = 0

    # --- quota / throttling ---------------------------------------------
    def calls_this_month(self) -> int:
        return db.calls_this_month(self.conn)

    def remaining_this_month(self) -> int:
        return max(0, self.monthly_cap - self.calls_this_month())

    def _check_quota(self) -> None:
        if self.stop_at_cap and self.calls_this_month() >= self.monthly_cap:
            raise QuotaExceeded(
                f"Monthly MarketCheck cap reached ({self.monthly_cap} calls). "
                "Free tier resets at the start of the month; raise api.monthly_call_cap "
                "in config.json only if you have actually upgraded the plan."
            )

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_call_at
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_call_at = time.monotonic()

    # --- requests --------------------------------------------------------
    def _get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        self._check_quota()
        attempt = 0
        while True:
            attempt += 1
            self._throttle()
            request_params = dict(params)
            request_params["api_key"] = self.api_key
            try:
                response = self.session.get(self.base_url, params=request_params, timeout=self.timeout)
            except Exception as exc:  # network-level failure
                db.record_api_call(self.conn, self.base_url, None, f"network error: {exc}")
                self.calls_made += 1
                if attempt > self.max_retries:
                    raise MarketCheckError(f"MarketCheck request failed after {attempt} attempts: {exc}") from exc
                time.sleep(min(16, 2 ** attempt))
                continue

            status = response.status_code
            db.record_api_call(self.conn, self.base_url, status, f"start={params.get('start', 0)}")
            self.calls_made += 1

            if status == 200:
                try:
                    return response.json()
                except ValueError as exc:
                    raise MarketCheckError(f"MarketCheck returned non-JSON body: {response.text[:200]}") from exc
            if status in (401, 403):
                raise MarketCheckError(
                    f"MarketCheck rejected the API key (HTTP {status}). Check MARKETCHECK_API_KEY in .env."
                )
            if status == 429:
                if attempt > self.max_retries:
                    raise MarketCheckError("MarketCheck rate limit (HTTP 429) persisted after retries.")
                wait = min(30, 2 ** attempt)
                LOG.warning("Rate limited by MarketCheck; sleeping %ss", wait)
                time.sleep(wait)
                continue
            if 500 <= status < 600:
                if attempt > self.max_retries:
                    raise MarketCheckError(f"MarketCheck server error HTTP {status} after retries.")
                time.sleep(min(16, 2 ** attempt))
                continue
            raise MarketCheckError(f"MarketCheck HTTP {status}: {response.text[:300]}")

    # --- search ----------------------------------------------------------
    def build_params(self, search: Dict[str, Any], start: int = 0, car_type: Optional[str] = None) -> Dict[str, Any]:
        radius = int(search.get("radius_miles", 100) or 100)
        if radius > FREE_TIER_MAX_RADIUS:
            LOG.warning("radius_miles=%s exceeds the free-tier %smi cap; clamping", radius, FREE_TIER_MAX_RADIUS)
            radius = FREE_TIER_MAX_RADIUS
        rows = min(int(search.get("rows_per_page", MAX_ROWS_PER_PAGE) or MAX_ROWS_PER_PAGE), MAX_ROWS_PER_PAGE)
        year_min = int(search.get("year_min", 2021) or 2021)
        params: Dict[str, Any] = {
            "zip": str(search.get("zip", "")),
            "radius": radius,
            "car_type": car_type or search.get("car_type", "used"),
            "year_range": f"{year_min}-{search.get('year_max', 2030)}",
            "price_range": f"{int(search.get('price_min', 0) or 0)}-{int(search.get('price_max', 20000) or 20000)}",
            "miles_range": f"0-{int(search.get('mileage_max', 60000) or 60000)}",
            "start": start,
            "rows": rows,
            "sort_by": "price",
            "sort_order": "asc",
        }
        body_types = search.get("body_types") or []
        if body_types:
            params["body_type"] = ",".join(body_types)
        makes = search.get("makes") or []
        if makes:
            params["make"] = ",".join(makes)
        models = search.get("models") or []
        if models:
            params["model"] = ",".join(models)
        return params

    def search(self, search: Dict[str, Any], car_type: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        """Yield raw listing dicts, paging until exhausted or max_pages is hit."""
        max_pages = int(search.get("max_pages", 5) or 5)
        rows = min(int(search.get("rows_per_page", MAX_ROWS_PER_PAGE) or MAX_ROWS_PER_PAGE), MAX_ROWS_PER_PAGE)
        start = 0
        for page in range(max_pages):
            if self.stop_at_cap and self.remaining_this_month() <= 0:
                LOG.warning("Stopping paging: monthly call cap reached")
                return
            payload = self._get(self.build_params(search, start=start, car_type=car_type))
            listings = payload.get("listings") or []
            num_found = int(payload.get("num_found") or 0)
            LOG.info("page %s: %s listings (num_found=%s)", page + 1, len(listings), num_found)
            for listing in listings:
                yield listing
            start += rows
            if len(listings) < rows or start >= num_found:
                return
