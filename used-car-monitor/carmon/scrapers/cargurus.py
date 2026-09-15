"""CarGurus adapter.

CarGurus has no public listings API, so this adapter scrapes its search-results HTML. Like
every other adapter in this package it is **opt-in** (disabled unless both `scrapers.enabled`
and `scrapers.sources.cargurus` are switched on in config.json) and **capped** by the same
daily request/listing ledger and per-run page limit enforced in `base.py`.

robots.txt is obeyed with no exception: `RobotsCache` fails closed, so if robots.txt cannot
be fetched or parsed, the whole site is treated as disallowed and this adapter raises
`RobotsDisallowed` rather than guessing that scraping is permitted. Concretely, **from the
machine this adapter was developed on, `https://www.cargurus.com/robots.txt` itself returns
HTTP 406**, and `looks_like_challenge()` treats any 406 response as a bot wall -- so
`RobotsCache._load()` records that as "could not be read" and every fetch attempt here stops
at the robots check before a single search page is requested. That is the correct outcome
for this environment, not a bug: when permission cannot be established, the answer is no.
From a typical home/residential connection this has been observed to differ, which is why
the adapter is worth having -- but it also means **`search_urls()`/`parse()` below have
never been exercised against a real response from this environment, and the parser is
written entirely from public knowledge of CarGurus' page conventions (schema.org markup,
common inline-JSON hydration patterns, and documented "deal rating" / "$N below market"
badge copy), not validated against live HTML.** Treat it as a best-effort implementation to
be checked -- and likely adjusted -- against a real page the first time it actually runs
somewhere reachable.

This adapter does not do anything to get around a block. If CarGurus answers with a bot
challenge, the fetch is recorded as "blocked" and the run stops -- no retries, no
header/UA rotation, no proxies, no cookie jars, no CAPTCHA handling. That is by design (see
`base.py`'s module docstring).

Before enabling this source, read CarGurus' Terms of Service. Several listing sites
prohibit automated collection outright; `sources.py` keeps a plain browsing link for exactly
that reason, and MarketCheck's API remains the primary, supported source for this project.

Search URLs target CarGurus' inventory-listing endpoint:

    https://www.cargurus.com/Cars/inventorylisting/viewDetailsFilterViewInventoryListing.action
        ?zip=<zip>&distance=<radius>&maxPrice=<price>&maxMileage=<miles>&startYear=<year>
        &inventorySearchWidgetType=AUTO&sourceContext=carGurusHomePageModel&offset=<n*15>

with `offset` advancing by CarGurus' documented page size (15) to page through results, up
to `limits.max_pages_per_run` distinct URLs.

Parse strategy, tried in order and independent of each other (each returns as soon as it
finds something, so a page only needs to satisfy one of them):

  1. `<script type="application/ld+json">` blocks containing schema.org `Car`, `Vehicle`, or
     `Product` objects. Most stable target, as with every other adapter in this package.
  2. An embedded JSON blob -- CarGurus, like most modern listing sites, ships its listing
     data as inline JSON for client-side hydration (either a `<script type="application/
     json">` payload or a `window.__SOMENAME__ = {...};` assignment). This strategy decodes
     any such block it finds and walks the resulting structure for objects carrying a VIN,
     rather than hard-coding one specific hydration variable name -- that name is exactly
     the kind of build-tooling detail expected to drift and cannot be confirmed without a
     live page.
  3. A plain `html.parser` walk over listing-card markup, as a last resort when neither
     structured-data strategy finds anything.

CarGurus' distinctive datum -- versus a plain listings site -- is its **deal rating**
(Great/Good/Fair/High/Overpriced) and a "$N below/above market" delta. All three strategies
feed into one shared extractor (`_extract_deal`) that looks first for plausibly-named
structured fields (`dealRating`, `priceDifference`, and similar) and falls back to scanning
any free-text field for rating words or a "$N below/above market" phrase, since the exact
field names or badge copy CarGurus uses cannot be confirmed from here. `deal_rating` is
normalized to one of the five canonical labels; `deal_delta` is an int, negative meaning
below market. Both are omitted (not invented) when nothing recognizable is found.

Whichever strategy runs, a listing without a VIN may still be returned by `parse()`;
`ScraperBase.run()` is what drops VIN-less listings (VIN is what dedupes against MarketCheck
data), and dropping that decision into the base class keeps it consistent across adapters.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from .base import ScraperBase, register
from .parsing import (
    clean_str as _clean_str,
    find_ci as _find_ci,
    find_vin_in_strings,
    iter_ld_vehicle_nodes,
    name_of as _name_of,
    parse_vehicle_title,
    run_class_card_parser,
    split_dealer_location as _split_dealer_location,
    to_bool as _to_bool,
    to_float as _to_float,
    to_int as _to_int,
    to_signed_int as _to_signed_int,
    walk_dicts as _walk_dicts,
)

SEARCH_PATH = "/Cars/inventorylisting/viewDetailsFilterViewInventoryListing.action"

# CarGurus' documented results-per-page size; offset advances by this amount per page.
_PAGE_SIZE = 15


# --- deal rating / deal delta -------------------------------------------------------

_DEAL_RATING_KEYS = (
    "dealRating", "deal_rating", "priceRating", "priceLabel", "listingType", "dealBadge",
)
_DEAL_DELTA_KEYS = (
    "dealDelta", "deal_delta", "priceDifference", "priceAnalysisAmount",
    "belowMarketAmount", "marketDelta", "savings",
)
_DEAL_WORDS = ("great", "good", "fair", "overpriced", "high")
_MARKET_DELTA_RE = re.compile(r"\$?([\d,]+)\s*(below|above)\s+market", re.IGNORECASE)


def _canonical_rating(value: Any) -> Optional[str]:
    text = _clean_str(value)
    if not text:
        return None
    lowered = text.lower()
    for word in _DEAL_WORDS:
        if word in lowered:
            return "Overpriced" if word == "overpriced" else word.capitalize()
    return None


def _extract_deal(raw: Dict[str, Any]) -> tuple[Optional[str], Optional[int]]:
    """Look for a deal-rating badge and a '$N below/above market' delta.

    CarGurus is not schema.org-standard for these two fields, and the exact field names or
    badge copy in use cannot be confirmed from this environment (see module docstring), so
    this checks a handful of plausible structured field names first, then falls back to
    scanning any string field (including one level of nesting) for rating words or a
    '$N below/above market' phrase.
    """
    if not isinstance(raw, dict):
        return None, None
    candidates = [raw] + [v for v in raw.values() if isinstance(v, dict)]

    rating: Optional[str] = None
    delta: Optional[int] = None
    for candidate in candidates:
        if rating is None:
            for key in _DEAL_RATING_KEYS:
                value = _find_ci(candidate, key)
                if value:
                    rating = _canonical_rating(value)
                    if rating:
                        break
        if delta is None:
            for key in _DEAL_DELTA_KEYS:
                value = _find_ci(candidate, key)
                if value is not None:
                    coerced = _to_signed_int(value)
                    if coerced is not None:
                        delta = coerced
                        break
        if rating is not None and delta is not None:
            return rating, delta

    for candidate in candidates:
        for value in candidate.values():
            if not isinstance(value, str):
                continue
            if rating is None:
                found_rating = _canonical_rating(value)
                if found_rating:
                    rating = found_rating
            if delta is None:
                match = _MARKET_DELTA_RE.search(value)
                if match:
                    amount = int(match.group(1).replace(",", ""))
                    delta = -amount if match.group(2).lower() == "below" else amount
        if rating is not None and delta is not None:
            break
    return rating, delta


# --- shared listing normalizer -------------------------------------------------------

def _listing_from_raw(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Build a normalized listing dict from a loosely-keyed, arbitrary-casing field mapping.

    Shared by all three parse strategies via case-insensitive lookups (`_find_ci`), so a
    schema.org JSON-LD node, a hydration-JSON listing object, and an HTML card's collected
    text/attributes can all be normalized the same way.
    """
    if not isinstance(raw, dict):
        return None

    vin = _clean_str(_find_ci(raw, "vin", "vinNumber", "vehicleIdentificationNumber", "sku"))

    trim = _find_ci(raw, "trim", "vehicleConfiguration")

    title = _find_ci(raw, "title", "name", "heading")
    parsed_title = parse_vehicle_title(title, known_trim=trim) if title else {}
    year = parsed_title.get("year")
    make = parsed_title.get("make")
    model = parsed_title.get("model")
    trim = parsed_title.get("trim", trim)

    year = year or _to_int(_find_ci(raw, "year", "modelDate", "vehicleModelDate"))
    make = make or _name_of(_find_ci(raw, "make", "brand", "manufacturer"))
    model = model or _name_of(_find_ci(raw, "model"))
    trim = _clean_str(trim)

    offers = _find_ci(raw, "offers")
    offers_price = None
    seller_name = None
    if isinstance(offers, dict):
        offers_price = offers.get("price") or _find_ci(offers, "price")
        seller = _find_ci(offers, "seller")
        if isinstance(seller, dict):
            seller_name = _find_ci(seller, "name")

    price = _find_ci(raw, "price", "price_current") or offers_price
    dealer_name = _find_ci(raw, "dealer_name", "dealerName", "seller") or seller_name

    listing: Dict[str, Any] = {
        "vin": vin,
        "year": year,
        "make": make,
        "model": model,
        "trim": trim,
        "body_type": _clean_str(_find_ci(raw, "body_type", "bodyType", "vehicleBodyType")),
        "fuel_type": _clean_str(_find_ci(raw, "fuel_type", "fuelType")),
        "mileage": _to_int(_find_ci(raw, "mileage", "miles", "mileageFromOdometer")),
        "price_current": _to_int(price),
        "dealer_name": _name_of(dealer_name),
        "distance_miles": _to_float(_find_ci(raw, "distance_miles", "distance")),
        "cpo": _to_bool(
            _find_ci(raw, "cpo", "certified", "isCertified")
            or (_find_ci(raw, "stock_type") == "certified")
        ),
        "listing_url": _clean_str(_find_ci(raw, "listing_url", "listingUrl", "url", "@id")),
    }

    dealer_city = _find_ci(raw, "dealer_city", "dealerCity")
    dealer_state = _find_ci(raw, "dealer_state", "dealerState")
    if not dealer_city and not dealer_state:
        dealer_city, dealer_state = _split_dealer_location(
            _find_ci(raw, "dealer_location", "location")
        )
    listing["dealer_city"] = _clean_str(dealer_city)
    listing["dealer_state"] = _clean_str(dealer_state)

    rating, delta = _extract_deal(raw)
    if rating:
        listing["deal_rating"] = rating
    if delta is not None:
        listing["deal_delta"] = delta

    if not listing["vin"]:
        listing["vin"] = find_vin_in_strings(raw)

    return {key: value for key, value in listing.items() if value is not None}


# --- strategy 1: JSON-LD --------------------------------------------------

def _parse_json_ld(body: str) -> List[Dict[str, Any]]:
    listings: List[Dict[str, Any]] = []
    for node in iter_ld_vehicle_nodes(body):
        listing = _listing_from_raw(node)
        if listing:
            listings.append(listing)
    return listings


# --- strategy 2: embedded JSON blob (hydration payload) ---------------------

_SCRIPT_RE = re.compile(r'<script\b([^>]*)>(.*?)</script>', re.IGNORECASE | re.DOTALL)
_WINDOW_ASSIGN_RE = re.compile(r'window\.__[A-Za-z0-9_]+__\s*=\s*(\{.*\});?\s*$', re.DOTALL)

_VIN_KEY_CANDIDATES = ("vin", "vinNumber", "vehicleIdentificationNumber")


def _iter_embedded_json_blocks(body: str):
    """Yield the JSON text of each candidate hydration payload found in <script> tags.

    Two shapes are recognized: a script whose whole body *is* JSON (e.g.
    `<script type="application/json">{...}</script>`, the pattern frameworks like Next.js
    use for `__NEXT_DATA__`), and a plain `<script>` containing a
    `window.__SOMENAME__ = {...};` assignment. JSON-LD scripts are skipped -- strategy 1
    already handles those.
    """
    for attrs, content in _SCRIPT_RE.findall(body):
        if "application/ld+json" in attrs.lower():
            continue
        text = content.strip()
        if not text:
            continue
        if text[0] in "{[":
            yield text
            continue
        match = _WINDOW_ASSIGN_RE.search(text)
        if match:
            yield match.group(1)


def _parse_embedded_json(body: str) -> List[Dict[str, Any]]:
    listings: List[Dict[str, Any]] = []
    seen_ids: set[int] = set()
    for block in _iter_embedded_json_blocks(body):
        try:
            data = json.loads(block)
        except (json.JSONDecodeError, ValueError):
            continue
        for node in _walk_dicts(data):
            if id(node) in seen_ids:
                continue
            if not any(_find_ci(node, key) for key in _VIN_KEY_CANDIDATES):
                continue
            seen_ids.add(id(node))
            listing = _listing_from_raw(node)
            if listing:
                listings.append(listing)
    return listings


# --- strategy 3: plain HTML card walk --------------------------------------

# Last-resort walk over listing-card markup. Looks for a container whose class list
# includes "listing-tile" -- a best guess at CarGurus' listing-card convention, unvalidated
# against live HTML (see module docstring) -- and reads plain text out of inner elements by
# class-name convention, plus a `data-vin` attribute on the container itself when present.

_CARD_CONTAINER_CLASS = "listing-tile"

_CARD_TEXT_FIELD_CLASSES = {
    "title": "title",
    "listing-title": "title",
    "price": "price",
    "mileage": "mileage",
    "dealer-name": "dealer_name",
    "dealer-location": "dealer_location",
    "deal-rating": "deal_rating_text",
    "deal-badge": "deal_rating_text",
    "price-analysis": "deal_delta_text",
    "vin": "vin",
}


def _parse_html_cards(body: str) -> List[Dict[str, Any]]:
    cards = run_class_card_parser(
        body, _CARD_CONTAINER_CLASS, _CARD_TEXT_FIELD_CLASSES, capture_data_attrs={"vin"}
    )
    listings = []
    for fields in cards:
        listing = _listing_from_raw(fields)
        if listing:
            listings.append(listing)
    return listings


@register
class CarGurusScraper(ScraperBase):
    key = "cargurus"
    name = "CarGurus"
    site = "https://www.cargurus.com"
    kind = "listings"

    def search_urls(self, search: Dict[str, Any]) -> List[str]:
        zip_code = _clean_str(search.get("zip"))
        if not zip_code:
            return []

        params: Dict[str, Any] = {
            "zip": zip_code,
            "inventorySearchWidgetType": "AUTO",
            "sourceContext": "carGurusHomePageModel",
        }
        radius = _to_int(search.get("radius_miles"))
        if radius is not None:
            params["distance"] = radius
        price_max = _to_int(search.get("price_max"))
        if price_max is not None:
            params["maxPrice"] = price_max
        mileage_max = _to_int(search.get("mileage_max"))
        if mileage_max is not None:
            params["maxMileage"] = mileage_max
        year_min = _to_int(search.get("year_min"))
        if year_min is not None:
            params["startYear"] = year_min

        max_pages = max(1, int(self.limits.max_pages_per_run))
        urls: List[str] = []
        for page in range(max_pages):
            page_params = dict(params)
            page_params["offset"] = page * _PAGE_SIZE
            urls.append(f"{self.site}{SEARCH_PATH}?{urlencode(page_params)}")
        return urls

    def parse(self, body: str, url: str) -> List[Dict[str, Any]]:
        if not body or not body.strip():
            return []

        for strategy in (_parse_json_ld, _parse_embedded_json, _parse_html_cards):
            try:
                listings = strategy(body)
            except Exception:
                listings = []
            if listings:
                for listing in listings:
                    listing.setdefault("source", self.key)
                return listings
        return []
