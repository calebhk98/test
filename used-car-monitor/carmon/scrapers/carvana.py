"""Carvana adapter.

Carvana has no public listings API, so this adapter -- like the other optional adapters
in this package -- scrapes its search-results HTML. It is **opt-in** (disabled unless both
`scrapers.enabled` and `scrapers.sources.carvana` are switched on in config.json) and
**capped** by the same daily request/listing ledger and per-run page limit as every other
adapter here (see `base.py`).

robots.txt is obeyed, with no exception: `RobotsCache` fails closed, so if robots.txt
cannot be fetched or parsed, the whole site is treated as disallowed and this adapter
raises `RobotsDisallowed` rather than guessing that scraping is permitted. Concretely,
**from the machine this adapter was developed on, `https://www.carvana.com/robots.txt`
itself returns HTTP 403 behind a Cloudflare JS challenge ("Enable JavaScript and cookies
to continue")**, so `search_urls()`/`parse()` below have never been exercised against a
real response from this environment -- every fetch attempt here stops at the robots check
before a single search page is requested. A home/residential connection may see different
behavior than a datacenter IP does, which is why this adapter is worth having on file --
but that also means **the parser below is written entirely against schema.org markup
conventions and the general shape of Next.js pages, and has not been validated against
live Carvana HTML.** Treat it as a best-effort implementation to be checked (and likely
adjusted) against a real page the first time it actually runs somewhere reachable.

This adapter does not do anything to get around a block. If Carvana answers with a bot
challenge, redirect-to-CAPTCHA, or any of the markers in `base.CHALLENGE_MARKERS`, the
fetch is recorded as "blocked" and the run stops -- no retries, no header/UA rotation, no
proxies, no cookie jars. That is by design (see `base.py`'s module docstring).

Before enabling this source, read Carvana's Terms of Service. Several listing sites
prohibit automated collection outright; `sources.py` keeps plain browsing links for exactly
that reason, and MarketCheck's API remains the primary, supported source for this project.

Carvana sells nationally and ships/delivers every car it lists -- its inventory is not
radius-bound to a physical lot the way a traditional dealer's is. `distance_miles` is
therefore left `None` on every listing this adapter produces (this adapter never invents a
distance), and `delivery_only` is set `True` on every listing so the rest of the pipeline
can tell Carvana's national stock apart from local dealer inventory. The project's distance
scoring already treats "distance unknown" as 0 points, which is the right outcome here --
no special-casing needed downstream.

Carvana is also a no-haggle retailer with its own 7-day/400-mile return window and its own
"CarvanaCertified" inspection process -- that is a Carvana-run inspection, not manufacturer
Certified Pre-Owned. `cpo` is therefore left `False` unless a page explicitly signals
*manufacturer* certification (e.g. a "manufacturer certified" / "factory certified" /
"manufacturer CPO" phrase or an explicit manufacturer-certification field); the mere
presence of Carvana's own "certified"/"inspected" marketing language does not set it.

Parse strategy, tried in order and independent of each other (each returns as soon as it
finds something, so a page only needs to satisfy one of them):

  1. `<script type="application/ld+json">` blocks containing schema.org `Car`, `Vehicle`,
     or `Product` objects. This is the most stable target because schema.org markup
     changes far less often than CSS class names or JS bundle internals.
  2. An embedded JSON state blob. Carvana is a Next.js application and typically ships a
     `<script id="__NEXT_DATA__">` payload carrying page props; this strategy walks that
     JSON looking for any object that carries a VIN, rather than hard-coding a specific
     page-state schema that is likely to drift.
  3. A plain `html.parser` walk over listing-card markup (elements whose class mentions
     "result-tile" or "vehicle-card" -- the conventions Carvana's site and similar
     inventory sites have used) reading both `data-*` attributes and nested text by class
     name, as a last resort when neither structured-data strategy finds anything.

Whichever strategy runs, a listing without a VIN may still be returned; `ScraperBase.run()`
is what drops VIN-less listings (VIN is what dedupes against MarketCheck data), and
dropping that decision into the base class keeps it consistent across every adapter.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from .base import ScraperBase, register
from .parsing import (
    clean_str as _clean_str,
    find_ci as _find_ci,
    find_vin_in_strings,
    iter_ld_vehicle_nodes,
    ld_offer_price_and_seller,
    name_of as _name_of,
    parse_vehicle_title,
    run_class_card_parser,
    split_dealer_location as _split_dealer_location,
    to_int as _to_int,
    walk_dicts as _walk_dicts,
)

SEARCH_PATH = "/cars/filters"

_NEXT_DATA_RE = re.compile(
    r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)

# Explicit manufacturer-certification signals. Carvana's own "CarvanaCertified" inspection
# language must NOT trip this -- only real manufacturer/factory CPO language or fields do.
_MANUFACTURER_CPO_KEYS = (
    "manufacturer_certified", "manufacturercertified", "factory_certified",
    "factorycertified", "oem_certified", "oemcertified", "is_manufacturer_cpo",
)
_MANUFACTURER_CPO_PHRASES = (
    "manufacturer certified", "manufacturer cpo", "factory certified", "oem certified",
)


def _is_manufacturer_cpo(fields: Dict[str, Any]) -> bool:
    """True only for explicit *manufacturer* CPO signals -- never Carvana's own inspection."""
    for key in _MANUFACTURER_CPO_KEYS:
        if key in fields:
            value = fields[key]
            if isinstance(value, bool) and value:
                return True
            if isinstance(value, str) and value.strip().lower() in ("true", "1", "yes"):
                return True
    for value in fields.values():
        if isinstance(value, str):
            low = value.lower()
            if any(phrase in low for phrase in _MANUFACTURER_CPO_PHRASES):
                return True
    return False


def _listing_from_fields(fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Build a normalized listing dict from a loosely-keyed field mapping.

    Accepts schema.org-flavored keys (vehicleIdentificationNumber, offers.price, ...) and
    Carvana-card/state-flavored keys (vin, price, mileage, stockNumber, title, ...) so all
    three parse strategies can share one normalizer. `dealer_name` is always forced to
    "Carvana" (Carvana is the seller, not a marketplace of dealers); `distance_miles` is
    always left unset here (the caller forces it to None) and `delivery_only` is always
    forced True -- see the module docstring for why.
    """
    vin = _clean_str(
        fields.get("vin")
        or fields.get("vehicleIdentificationNumber")
        or fields.get("sku")
    )

    trim = fields.get("trim") or fields.get("trimName") or fields.get("vehicleConfiguration")

    title = fields.get("title") or fields.get("name") or fields.get("heading")
    parsed_title = parse_vehicle_title(title, known_trim=trim) if title else {}
    year = parsed_title.get("year")
    make = parsed_title.get("make")
    model = parsed_title.get("model")
    trim = parsed_title.get("trim", trim)

    year = year or _to_int(
        fields.get("year") or fields.get("modelYear") or fields.get("modelDate")
        or fields.get("vehicleModelDate") or fields.get("productionDate")
    )
    make = make or _name_of(fields.get("make") or fields.get("brand") or fields.get("manufacturer"))
    model = model or _name_of(fields.get("model"))
    trim = _clean_str(trim)

    offers = fields.get("offers")
    offers_price = offers.get("price") if isinstance(offers, dict) else None
    price = fields.get("price") or fields.get("price_current") or fields.get("listPrice") or offers_price

    stock_number = _clean_str(
        fields.get("stock_number") or fields.get("stockNumber") or fields.get("stockNum")
    )

    listing: Dict[str, Any] = {
        "vin": vin,
        "year": year,
        "make": make,
        "model": model,
        "trim": trim,
        "body_type": _clean_str(
            fields.get("body_type") or fields.get("bodyType") or fields.get("vehicleBodyType")
        ),
        "fuel_type": _clean_str(fields.get("fuel_type") or fields.get("fuelType")),
        "mileage": _to_int(
            fields.get("mileage") or fields.get("miles") or fields.get("odometer")
            or fields.get("mileageFromOdometer")
        ),
        "price_current": _to_int(price),
        "dealer_name": "Carvana",
        "distance_miles": None,
        "delivery_only": True,
        "cpo": _is_manufacturer_cpo(fields),
        "listing_url": _clean_str(fields.get("listing_url") or fields.get("url")),
        "stock_number": stock_number,
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

    # distance_miles/delivery_only/dealer_name are meaningful even when "falsy"-ish
    # (None/True are real values here), so they are exempted from the generic pruning
    # below, which otherwise drops keys the source page simply did not mention.
    always_keep = {"distance_miles", "delivery_only", "dealer_name"}
    return {
        key: value for key, value in listing.items()
        if value is not None or key in always_keep
    }


# --- strategy 1: JSON-LD --------------------------------------------------

def _parse_json_ld(body: str, url: str) -> List[Dict[str, Any]]:
    listings: List[Dict[str, Any]] = []
    for node in iter_ld_vehicle_nodes(body):
        fields: Dict[str, Any] = dict(node)
        price, _seller = ld_offer_price_and_seller(node)
        # Carvana is always the seller of record for its own listings; a seller name
        # embedded in the page (if any) is deliberately not used to override that -- see
        # `_listing_from_fields`, which forces dealer_name to "Carvana" regardless.
        if price is not None:
            fields.setdefault("price", price)
        fields.setdefault("listing_url", node.get("url") or node.get("@id"))
        listing = _listing_from_fields(fields)
        if listing:
            listings.append(listing)
    return listings


# --- strategy 2: embedded __NEXT_DATA__ state blob -------------------------

def _parse_next_data(body: str, url: str) -> List[Dict[str, Any]]:
    listings: List[Dict[str, Any]] = []
    seen_vins: set[str] = set()
    for match in _NEXT_DATA_RE.finditer(body):
        raw = match.group(1).strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            continue
        for node in _walk_dicts(data):
            # A VIN is the anchor that identifies "this dict is a listing" inside an
            # otherwise-unknown Next.js props blob; a listing without one is invisible to
            # this strategy (JSON-LD, strategy 1, has no such requirement).
            vin = _clean_str(_find_ci(node, "vin"))
            if not vin or vin.upper() in seen_vins:
                continue
            seen_vins.add(vin.upper())
            fields = dict(node)
            fields["vin"] = vin
            listing = _listing_from_fields(fields)
            if listing:
                listings.append(listing)
    return listings


# --- strategy 3: plain HTML card walk --------------------------------------
# Last-resort walk over listing-card markup: data-* attributes plus nested text. Looks for
# elements whose class mentions one of `_CARD_CLASS_MARKERS`. Within a card, both `data-*`
# attributes (data-vin, data-price, ...) and the plain text inside inner elements matching
# `_CARD_FIELD_CLASSES` by class name are collected -- whichever a given page actually
# uses. A field is kept on FIRST sight (`overwrite=False`): unlike cars.com/CarMax/
# CarGurus' plain-card fallback, Carvana's markup convention has been assumed to render a
# card's canonical value before any repeated/secondary rendering of the same class.

_CARD_CLASS_MARKERS = ("result-tile", "vehicle-card")

_CARD_FIELD_CLASSES = {
    "title": "title", "vehicle-title": "title",
    "price": "price", "result-price": "price",
    "mileage": "mileage", "result-mileage": "mileage",
    "dealer-location": "dealer_location", "location": "dealer_location",
    "stock-number": "stock_number",
    "vin": "vin",
}


def _parse_html_cards(body: str, url: str) -> List[Dict[str, Any]]:
    cards = run_class_card_parser(
        body, _CARD_CLASS_MARKERS, _CARD_FIELD_CLASSES,
        capture_data_attrs=True, overwrite=False,
    )
    listings = []
    for fields in cards:
        title = fields.get("title")
        if title and ("year" not in fields and "make" not in fields):
            fields.setdefault("title", title)
        listing = _listing_from_fields(fields)
        if listing:
            listings.append(listing)
    return listings


@register
class CarvanaScraper(ScraperBase):
    key = "carvana"
    name = "Carvana"
    site = "https://www.carvana.com"
    kind = "listings"

    def search_urls(self, search: Dict[str, Any]) -> List[str]:
        zip_code = _clean_str(search.get("zip"))
        if not zip_code:
            return []

        price_max = _to_int(search.get("price_max"))
        mileage_max = _to_int(search.get("mileage_max"))
        year_min = _to_int(search.get("year_min"))

        params: Dict[str, str] = {"zip": zip_code}
        if price_max is not None:
            params["price-range"] = f"0-{price_max}"
        if mileage_max is not None:
            params["mileage-range"] = f"0-{mileage_max}"
        if year_min is not None:
            # Carvana's own filter UI caps the upper end of a year range at the current
            # model year; there is no "no upper bound" search.year_max in this project's
            # config to carry instead, so the current calendar year stands in for it.
            current_year = datetime.now(timezone.utc).year
            params["year-range"] = f"{year_min}-{current_year}"

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

        for strategy in (_parse_json_ld, _parse_next_data, _parse_html_cards):
            try:
                listings = strategy(body, url)
            except Exception:
                listings = []
            if listings:
                for listing in listings:
                    listing.setdefault("source", self.key)
                return listings
        return []
