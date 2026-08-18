"""Adapter slots for non-MarketCheck sources.

v1 deliberately ships **no scrapers** — SPEC.md lists scraping Autotrader/CarGurus/
Cars.com/CarMax as an explicit non-goal, and `carmon/sources.py` covers those sites
with plain deep links instead.

This package exists so that, if MarketCheck's free tier turns out not to be worth
the quota, a source can be added without touching the pipeline: implement
`ListingSource.fetch()` to return dicts shaped like `pipeline.normalize_listing()`
output (vin, year, make, model, trim, body_type, fuel_type, mileage, price_current,
dealer_*, distance_miles, cpo, listing_url, source) and register it in `REGISTRY`.

Before enabling any such adapter, check the target site's Terms of Service and
robots.txt — several of these sites prohibit automated collection, and some offer
official feeds or affiliate APIs that are the supported path instead.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Protocol


class ListingSource(Protocol):
    """Interface every alternative source must implement."""

    key: str
    name: str

    def fetch(self, search: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
        """Yield normalized listing dicts for the given search config."""
        ...


REGISTRY: Dict[str, ListingSource] = {}


def register(source: ListingSource) -> ListingSource:
    REGISTRY[source.key] = source
    return source


def available() -> List[str]:
    return sorted(REGISTRY)
