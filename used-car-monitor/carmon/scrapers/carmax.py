"""CarMax adapter.

CarMax has no public listings API, so this adapter scrapes its search-results pages.
It is **opt-in** (disabled unless both `scrapers.enabled` and `scrapers.sources.carmax`
are switched on in config.json) and **capped** by the same daily request/listing ledger
and per-run page limit as every other adapter in this package (see `base.py`). There is
no public API here, either -- there is no code path that reaches carmax.com other than
the same rate-limited, robots-checked, opt-in machinery every adapter uses.

robots.txt is obeyed, with no exception: `RobotsCache` fails closed, so if robots.txt
cannot be fetched or parsed, the whole site is treated as disallowed and this adapter
raises `RobotsDisallowed` rather than guessing that scraping is permitted. Concretely,
**from the datacenter IP this adapter was developed on, `https://www.carmax.com/robots.txt`
itself returns HTTP 403 (Akamai "Access Denied")**, so `search_urls()`/`parse()` below have
never been exercised against a real response from this environment -- every fetch attempt
here stops at the robots check before a single search page is requested. A typical home/
residential connection may be treated differently by Akamai, which is why this adapter is
worth having; but that also means **the parser below is unvalidated against live CarMax
HTML**. It is written against schema.org markup conventions, common JS-app embedded-JSON
payload shapes, and plausible listing-card markup, but none of that has been checked
against a real CarMax response. Treat it as a best-effort implementation to be checked
(and likely adjusted) against a real page the first time it actually runs somewhere
reachable.

This adapter does not do anything to get around a block. If CarMax answers with a bot
challenge, redirect-to-CAPTCHA, or any of the markers in `base.CHALLENGE_MARKERS` /
`base.CHALLENGE_PLATFORMS` (Akamai's own fingerprints included), the fetch is recorded as
"blocked" and the run stops -- no retries, no header/UA rotation, no proxies, no cookie
jars. That is by design (see `base.py`'s module docstring).

Before enabling this source, read CarMax's Terms of Service. Several listing sites
prohibit automated collection outright; `sources.py` keeps plain browsing links for exactly
that reason, and MarketCheck's API remains the primary, supported source for this project.

Manufacturer CPO vs. CarMax's own certification -- why this adapter keeps them separate:
CarMax is a no-haggle retailer: every car is posted at one fixed price, and the great
majority of its inventory is "CarMax Quality Certified" -- CarMax's own reconditioning and
inspection program, not a manufacturer certified-pre-owned (CPO) program backed by the
original automaker's warranty. The scoring model (see `carmon/scoring.py`) gives `cpo` a
real weight (+2, and it waives the caution-model penalty) specifically because manufacturer
CPO carries an OEM-backed warranty and inspection standard. Silently mapping "CarMax
Quality Certified" onto `cpo=True` would hand out that bonus for a program that is not the
same thing and would corrupt the score. So:

  * `cpo` is set only when the page text indicates *manufacturer* certification (e.g. "Honda
    Certified", "Toyota Certified Pre-Owned", "Manufacturer Certified") -- something CarMax
    listings occasionally do carry on top of, or in place of, CarMax's own program.
  * `retailer_certified` (bool) captures CarMax's own "CarMax Quality Certified" badge
    separately, so it is visible in the data without ever feeding the CPO bonus.

Parse strategy, tried in order and independent of each other (each returns as soon as it
finds something, so a page only needs to satisfy one of them):

  1. `<script type="application/ld+json">` blocks containing schema.org `Car`, `Vehicle`,
     or `Product` objects. This is the most stable target because schema.org markup changes
     far less often than CSS class names or JS bundle internals.
  2. An embedded JSON payload -- CarMax's search results are a JavaScript application, and
     apps like this typically hydrate from a JSON blob embedded in a `<script>` tag (e.g.
     `window.__PRELOADED_STATE__ = {...}` or a `<script id="...">application/json`
     block) rather than server-rendered markup. This strategy looks for such a blob and
     walks it for vehicle-shaped objects (stock number, VIN, price, mileage, year/make/
     model present together).
  3. A plain `html.parser` walk over listing-card markup (headings/links/spans, matching on
     class names that plausibly identify a result card) as a last resort when neither
     structured-data strategy finds anything.

Whichever strategy runs, a listing without a VIN is still returned; `ScraperBase.run()` is
what drops VIN-less listings (VIN is what dedupes against MarketCheck data), and dropping
that decision into the base class keeps it consistent across every adapter.
"""

from __future__ import annotations

import json
import re
from datetime import date
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from .base import ScraperBase, register
from .parsing import (
    clean_str as _clean_str,
    find_vin_in_strings,
    ld_offer_price_and_seller,
    iter_ld_vehicle_nodes,
    looks_vehicle_shaped,
    name_of as _name_of,
    parse_vehicle_title,
    run_class_card_parser,
    split_dealer_location as _split_dealer_location,
    to_float as _to_float,
    to_int as _to_int,
    walk_dicts,
)

SEARCH_PATH = "/cars"

# CarMax's own reconditioning/inspection program. This is NOT a manufacturer CPO program
# and must never set `cpo`.
_RETAILER_CERT_RE = re.compile(r"carmax\s+quality\s+certified", re.IGNORECASE)

# Phrases that indicate an actual manufacturer-backed CPO program.
_MANUFACTURER_CPO_RE = re.compile(
    r"(manufacturer\s+certified|factory\s+certified|"
    r"\b[a-z][a-z\-]*\s+certified\s+pre[\s-]?owned\b|\bcertified\s+pre[\s-]?owned\b(?!\s*inspection))",
    re.IGNORECASE,
)


def _certification_flags(*texts: Any) -> tuple[bool, bool]:
    """Return (cpo, retailer_certified) from any certification-ish text found.

    `cpo` fires only on manufacturer-CPO language; CarMax's own "CarMax Quality Certified"
    badge sets `retailer_certified` instead and never `cpo`. See the module docstring for
    why the two must never be conflated.
    """
    cpo = False
    retailer_certified = False
    for text in texts:
        if not text:
            continue
        s = str(text)
        if _RETAILER_CERT_RE.search(s):
            retailer_certified = True
        # Strip any CarMax-certified phrase before checking for manufacturer language, so
        # "CarMax Quality Certified" alone can never trip the manufacturer pattern.
        remainder = _RETAILER_CERT_RE.sub("", s)
        if _MANUFACTURER_CPO_RE.search(remainder):
            cpo = True
    return cpo, retailer_certified


def _dealer_name(store: Any) -> Optional[str]:
    store_name = _name_of(store)
    if not store_name:
        return None
    if store_name.lower().startswith("carmax"):
        return store_name
    return f"CarMax {store_name}"


def _listing_from_fields(fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Build a normalized listing dict from a loosely-keyed field mapping.

    Accepts both schema.org-flavored keys (vehicleIdentificationNumber, sku, offers.price)
    and CarMax card/embedded-JSON-flavored keys (vin, price, mileage, stockNumber, store,
    certification text, etc.) so all three parse strategies can share one normalizer.
    """
    vin = _clean_str(
        fields.get("vin")
        or fields.get("vehicleIdentificationNumber")
    )

    trim = fields.get("trim") or fields.get("vehicleConfiguration")

    title = fields.get("title") or fields.get("name") or fields.get("heading")
    parsed_title = parse_vehicle_title(title, known_trim=trim) if title else {}
    year = parsed_title.get("year")
    make = parsed_title.get("make")
    model = parsed_title.get("model")
    trim = parsed_title.get("trim", trim)

    year = year or _to_int(
        fields.get("year") or fields.get("modelDate") or fields.get("vehicleModelDate")
    )
    make = make or _name_of(fields.get("make") or fields.get("brand") or fields.get("manufacturer"))
    model = model or _name_of(fields.get("model"))
    trim = _clean_str(trim)

    offers = fields.get("offers")
    offers_price = offers.get("price") if isinstance(offers, dict) else None
    price = fields.get("price") or fields.get("price_current") or offers_price

    cert_texts = [
        fields.get("certification"),
        fields.get("certified"),
        fields.get("stock_type"),
        fields.get("badge"),
        fields.get("cpo") if isinstance(fields.get("cpo"), str) else None,
    ]
    cpo, retailer_certified = _certification_flags(*cert_texts)
    # Explicit booleans, if present, are trusted directly (but only ever raise
    # retailer_certified -- a bare `certified: true` from CarMax's own data is CarMax's
    # program, never assumed to be manufacturer CPO).
    if isinstance(fields.get("retailer_certified"), bool):
        retailer_certified = retailer_certified or fields["retailer_certified"]
    if isinstance(fields.get("cpo"), bool):
        cpo = cpo or fields["cpo"]

    store = fields.get("store") or fields.get("dealer_name") or fields.get("seller")
    dealer_name = fields.get("dealer_name") if isinstance(fields.get("dealer_name"), str) and \
        str(fields.get("dealer_name")).lower().startswith("carmax") else None
    dealer_name = dealer_name or _dealer_name(store)

    listing: Dict[str, Any] = {
        "vin": vin,
        "year": year,
        "make": make,
        "model": model,
        "trim": trim,
        "body_type": _clean_str(fields.get("body_type") or fields.get("bodyType") or fields.get("vehicleBodyType")),
        "fuel_type": _clean_str(fields.get("fuel_type") or fields.get("fuelType")),
        "mileage": _to_int(fields.get("mileage") or fields.get("miles") or fields.get("mileageFromOdometer")),
        "price_current": _to_int(price),
        "dealer_name": dealer_name,
        "distance_miles": _to_float(fields.get("distance_miles") or fields.get("distance")),
        "cpo": cpo,
        "retailer_certified": retailer_certified,
        "stock_number": _clean_str(fields.get("stock_number") or fields.get("stockNumber") or fields.get("sku")),
        "listing_url": _clean_str(fields.get("listing_url") or fields.get("url")),
    }

    dealer_city = fields.get("dealer_city")
    dealer_state = fields.get("dealer_state")
    if not dealer_city and not dealer_state:
        dealer_city, dealer_state = _split_dealer_location(
            fields.get("dealer_location") or fields.get("location")
        )
    listing["dealer_city"] = _clean_str(dealer_city)
    listing["dealer_state"] = _clean_str(dealer_state)

    if not listing["vin"]:
        listing["vin"] = find_vin_in_strings(fields)

    return {key: value for key, value in listing.items() if value is not None}


# --- strategy 1: JSON-LD --------------------------------------------------

def _parse_json_ld(body: str) -> List[Dict[str, Any]]:
    listings: List[Dict[str, Any]] = []
    for node in iter_ld_vehicle_nodes(body):
        fields: Dict[str, Any] = dict(node)
        price, seller = ld_offer_price_and_seller(node)
        if price is not None:
            fields.setdefault("price", price)
        if seller is not None:
            fields.setdefault("dealer_name", seller.get("name"))
        fields.setdefault("listing_url", node.get("url") or node.get("@id"))
        listing = _listing_from_fields(fields)
        if listing:
            listings.append(listing)
    return listings


# --- strategy 2: embedded JSON payload (JS-app hydration blob) ------------

# Matches `window.SOMETHING = {...};` assignments and `<script id="..." type="application/
# json">{...}</script>` blocks, either of which CarMax-style JS apps commonly use to hydrate
# search results without a full server render.
_WINDOW_ASSIGN_RE = re.compile(
    r'window\.[A-Za-z0-9_]+\s*=\s*(\{.*?\})\s*;?\s*(?:</script>|$)',
    re.DOTALL,
)
_JSON_SCRIPT_RE = re.compile(
    r'<script[^>]+type=["\']application/json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)

# A node is "vehicle-shaped" if it carries at least a couple of these key hints together --
# avoids treating arbitrary app-state objects (nav menus, feature flags, ...) as listings.
# See `parsing.looks_vehicle_shaped` for why this heuristic (rather than a stricter "has a
# VIN key" anchor, as Carvana/Autotrader/CarGurus/TrueCar use for their own embedded-JSON
# strategies) is the right one for CarMax's hydration blob specifically.


def _walk_for_vehicle_nodes(data: Any) -> List[Dict[str, Any]]:
    return [node for node in walk_dicts(data) if looks_vehicle_shaped(node)]


def _parse_embedded_json(body: str) -> List[Dict[str, Any]]:
    blobs: List[str] = []
    blobs.extend(_JSON_SCRIPT_RE.findall(body))
    blobs.extend(_WINDOW_ASSIGN_RE.findall(body))

    listings: List[Dict[str, Any]] = []
    for blob in blobs:
        try:
            data = json.loads(blob)
        except (json.JSONDecodeError, ValueError):
            continue
        for node in _walk_for_vehicle_nodes(data):
            listing = _listing_from_fields(node)
            if listing:
                listings.append(listing)
    return listings


# --- strategy 3: plain HTML card walk --------------------------------------
# Last-resort walk: pull VIN/title/price/mileage text out of listing-card-ish markup.
# Looks for elements whose class mentions "car-tile" or "result-tile" (plausible CarMax
# result-card conventions) and reads plain text out of common inner elements by class name
# convention.

_PLAIN_CARD_CONTAINER_CLASSES = ("car-tile", "result-tile", "vehicle-tile", "listing-card")

_PLAIN_CARD_FIELD_CLASSES = {
    "title": "title", "car-tile-title": "title", "vehicle-title": "title",
    "price": "price", "car-tile-price": "price",
    "mileage": "mileage", "car-tile-mileage": "mileage",
    "store": "store", "car-tile-store": "store",
    "location": "dealer_location",
    "certification": "certification", "badge": "certification",
    "stock-number": "stock_number",
    "vin": "vin",
}


def _parse_plain_cards(body: str) -> List[Dict[str, Any]]:
    cards = run_class_card_parser(
        body,
        _PLAIN_CARD_CONTAINER_CLASSES,
        _PLAIN_CARD_FIELD_CLASSES,
        capture_data_attrs={"vin", "stock-number"},
    )
    listings = []
    for fields in cards:
        listing = _listing_from_fields(fields)
        if listing:
            listings.append(listing)
    return listings


@register
class CarMaxScraper(ScraperBase):
    key = "carmax"
    name = "CarMax"
    site = "https://www.carmax.com"
    kind = "listings"

    def search_urls(self, search: Dict[str, Any]) -> List[str]:
        zip_code = search.get("zip")
        radius = search.get("radius_miles")
        year_min = search.get("year_min")
        price_max = search.get("price_max")
        mileage_max = search.get("mileage_max")

        params: Dict[str, Any] = {}
        if zip_code is not None:
            params["zip"] = zip_code
        if radius is not None:
            params["distance"] = radius
        if price_max is not None:
            params["price"] = f"0-{price_max}"
        if mileage_max is not None:
            params["mileage"] = f"0-{mileage_max}"
        if year_min is not None:
            # CarMax's own search UI pins the upper bound of the year range to the current
            # model year (observed as 2026 on this machine on 2026-08-18); computed here
            # rather than hardcoded so the adapter does not go stale after the new year.
            params["year"] = f"{year_min}-{date.today().year}"

        max_pages = max(1, int(self.limits.max_pages_per_run))
        urls: List[str] = []
        for page in range(1, max_pages + 1):
            page_params = dict(params)
            page_params["page"] = page
            urls.append(f"{self.site}{SEARCH_PATH}?{urlencode(page_params)}")
        return urls

    def parse(self, body: str, url: str) -> List[Dict[str, Any]]:
        if not body or not body.strip():
            return []

        for strategy in (_parse_json_ld, _parse_embedded_json, _parse_plain_cards):
            try:
                listings = strategy(body)
            except Exception:
                listings = []
            if listings:
                for listing in listings:
                    listing.setdefault("source", self.key)
                return listings
        return []
