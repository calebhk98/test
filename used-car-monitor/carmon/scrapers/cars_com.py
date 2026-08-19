"""Cars.com adapter.

Cars.com has no public listings API, so this adapter scrapes its search-results HTML.
It is **opt-in** (disabled unless both `scrapers.enabled` and `scrapers.sources.cars_com`
are switched on in config.json) and **capped** by the same daily request/listing ledger
and per-run page limit as every other adapter in this package (see `base.py`).

robots.txt is obeyed, with no exception: `RobotsCache` fails closed, so if robots.txt
cannot be fetched or parsed, the whole site is treated as disallowed and this adapter
raises `RobotsDisallowed` rather than guessing that scraping is permitted. Concretely,
**from the datacenter IP this adapter was developed on, `https://www.cars.com/robots.txt`
itself returns HTTP 403 (Cloudflare)**, so `search_urls()`/`parse()` below have never been
exercised against a real response from this environment -- every fetch attempt here stops
at the robots check before a single search page is requested. From a typical home/residential
connection robots.txt has been observed to load and to permit `/shopping/results/`, which is
why this adapter is worth having; but that also means **the parser below is written entirely
against schema.org markup conventions and has not been validated against live Cars.com HTML**.
Treat it as a best-effort implementation to be checked (and likely adjusted) against a real
page the first time it actually runs somewhere reachable.

This adapter does not do anything to get around a block. If Cars.com answers with a bot
challenge, redirect-to-CAPTCHA, or any of the markers in `base.CHALLENGE_MARKERS`, the
fetch is recorded as "blocked" and the run stops -- no retries, no header/UA rotation, no
proxies, no cookie jars. That is by design (see `base.py`'s module docstring).

Before enabling this source, read Cars.com's Terms of Service. Several listing sites
prohibit automated collection outright; `sources.py` keeps plain browsing links for exactly
that reason, and MarketCheck's API remains the primary, supported source for this project.

Parse strategy, tried in order and independent of each other (each returns as soon as it
finds something, so a page only needs to satisfy one of them):

  1. `<script type="application/ld+json">` blocks containing schema.org `Car`, `Vehicle`,
     or `Product` objects (Cars.com, like many listing sites, embeds structured data for
     SEO). This is the most stable target because schema.org markup changes far less often
     than CSS class names.
  2. An embedded JSON payload -- Cars.com has historically rendered listing cards as
     `<div class="vehicle-card" data-...>` elements carrying the vehicle's data as
     JSON-ish HTML data attributes (vin, price, mileage, title, dealer, etc.). This
     strategy scans for `vehicle-card`-shaped tags and reads their data attributes.
  3. A plain `html.parser` walk over listing card markup (headings/links/spans) as a last
     resort when neither structured-data strategy finds anything, for pages that only ever
     rendered plain HTML without JSON-LD or data attributes.

Whichever strategy runs, a listing without a VIN is still returned; `ScraperBase.run()` is
what drops VIN-less listings (VIN is what dedupes against MarketCheck data), and dropping
that decision into the base class keeps it consistent across every adapter.
"""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from .base import ScraperBase, register

SEARCH_PATH = "/shopping/results/"

# Fallback VIN pattern (17 chars, excludes I/O/Q per the VIN standard) used when a field
# mapping has no clearly-named VIN key but a string field happens to contain one.
_VIN_RE = re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b")


def _to_int(value: Any) -> Optional[int]:
    """Best-effort int coercion for strings like '$18,995' or '37,412 mi.'. Never raises."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = str(value)
    digits = re.sub(r"[^0-9]", "", text)
    if not digits:
        return None
    try:
        return int(digits)
    except ValueError:
        return None


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    text = str(value)
    match = re.search(r"-?\d+(?:\.\d+)?", text.replace(",", ""))
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def _clean_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _name_of(value: Any) -> Optional[str]:
    """schema.org fields are sometimes a plain string, sometimes {'name': '...'}."""
    if isinstance(value, dict):
        return _clean_str(value.get("name"))
    return _clean_str(value)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    text = str(value).strip().lower()
    return text in ("true", "1", "yes", "certified", "cpo")


def _split_dealer_location(location: Any) -> tuple[Optional[str], Optional[str]]:
    """'Nashville, TN' -> ('Nashville', 'TN'). Anything else -> (None, None)."""
    text = _clean_str(location)
    if not text or "," not in text:
        return None, None
    city, _, state = text.rpartition(",")
    city = city.strip() or None
    state = state.strip() or None
    if state and len(state) > 3:
        # Not a plausible two-letter (or "N/A"-ish) state code; leave state unset.
        state = None
    return city, state


def _listing_from_fields(fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Build a normalized listing dict from a loosely-keyed field mapping.

    Accepts both schema.org-flavored keys (vehicleIdentificationNumber, sku, offers.price)
    and Cars.com card-flavored keys (vin, price, mileage, title/heading, dealer-name,
    dealer-city, dealer-state, cpo, stock-type) so the JSON-LD and data-attribute
    strategies can share one normalizer.
    """
    vin = _clean_str(
        fields.get("vin")
        or fields.get("vehicleIdentificationNumber")
        or fields.get("sku")
    )

    year = None
    make = None
    model = None
    trim = fields.get("trim") or fields.get("vehicleConfiguration")

    title = fields.get("title") or fields.get("name") or fields.get("heading")
    if title:
        match = re.match(
            r"\s*(\d{4})\s+([A-Za-z0-9\-]+)\s+(.+)", str(title)
        )
        if match:
            year = int(match.group(1))
            make = match.group(2)
            rest = match.group(3).strip()
            if trim:
                model = rest
            else:
                parts = rest.split(None, 1)
                model = parts[0] if parts else None
                trim = parts[1] if len(parts) > 1 else None

    year = year or _to_int(
        fields.get("year") or fields.get("modelDate")
        or fields.get("vehicleModelDate") or fields.get("productionDate")
    )
    make = make or _name_of(fields.get("make") or fields.get("brand") or fields.get("manufacturer"))
    model = model or _name_of(fields.get("model"))
    trim = _clean_str(trim)

    offers = fields.get("offers")
    offers_price = offers.get("price") if isinstance(offers, dict) else None
    price = fields.get("price") or fields.get("price_current") or offers_price
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
        "dealer_name": _name_of(fields.get("dealer_name") or fields.get("dealerName") or fields.get("seller")),
        "distance_miles": _to_float(fields.get("distance_miles") or fields.get("distance")),
        "cpo": _to_bool(fields.get("cpo") or fields.get("certified") or fields.get("stock_type") == "certified"),
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
        # Fall back to scanning any string field for a bare 17-char VIN pattern.
        for value in fields.values():
            if isinstance(value, str):
                found = _VIN_RE.search(value.upper())
                if found:
                    listing["vin"] = found.group(0)
                    break

    return {key: value for key, value in listing.items() if value is not None}


# --- strategy 1: JSON-LD --------------------------------------------------

_JSON_LD_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)

_VEHICLE_TYPES = {"car", "vehicle", "product"}


def _iter_ld_objects(raw_json: str):
    try:
        data = json.loads(raw_json)
    except (json.JSONDecodeError, ValueError):
        return
    stack = [data]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            if "@graph" in node and isinstance(node["@graph"], list):
                stack.extend(node["@graph"])
            yield node
            stack.extend(v for v in node.values() if isinstance(v, (dict, list)))
        elif isinstance(node, list):
            stack.extend(node)


def _parse_json_ld(body: str) -> List[Dict[str, Any]]:
    listings: List[Dict[str, Any]] = []
    for block in _JSON_LD_RE.findall(body):
        for node in _iter_ld_objects(block):
            node_type = node.get("@type")
            if isinstance(node_type, list):
                types = {str(t).lower() for t in node_type}
            else:
                types = {str(node_type).lower()} if node_type else set()
            if not types & _VEHICLE_TYPES:
                continue
            fields: Dict[str, Any] = dict(node)
            offers = node.get("offers")
            if isinstance(offers, dict):
                fields.setdefault("price", offers.get("price"))
            seller = None
            if isinstance(offers, dict):
                seller = offers.get("seller")
            if isinstance(seller, dict):
                fields.setdefault("dealer_name", seller.get("name"))
            fields.setdefault("listing_url", node.get("url") or node.get("@id"))
            listing = _listing_from_fields(fields)
            if listing:
                listings.append(listing)
    return listings


# --- strategy 2: embedded JSON / data-attribute cards ---------------------

class _VehicleCardScanner(HTMLParser):
    """Collects data-* attributes off elements carrying a 'vehicle-card' class."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cards: List[Dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: List[tuple]) -> None:
        attr_map = dict(attrs)
        classes = attr_map.get("class", "") or ""
        if "vehicle-card" not in classes.split() and "vehicle-card" not in classes:
            return
        fields: Dict[str, str] = {}
        for key, value in attrs:
            if value is None:
                continue
            if key.startswith("data-"):
                fields[key[len("data-"):].replace("-", "_")] = value
        if fields:
            self.cards.append(fields)

    # data-* attributes can also land on self-closing/void-ish tags parsed as start tags;
    # handle_startendtag reuses handle_starttag via HTMLParser's default behavior.


def _parse_data_attribute_cards(body: str) -> List[Dict[str, Any]]:
    scanner = _VehicleCardScanner()
    try:
        scanner.feed(body)
    except Exception:
        return []
    listings = []
    for fields in scanner.cards:
        listing = _listing_from_fields(fields)
        if listing:
            listings.append(listing)
    return listings


# --- strategy 3: plain HTML card walk --------------------------------------

class _PlainCardParser(HTMLParser):
    """Last-resort walk: pull VIN/title/price/mileage text out of listing-card-ish markup.

    Looks for elements whose class mentions "vehicle-card" (same container as strategy 2,
    covering pages that render the card wrapper but skip the data-* attributes) and reads
    plain text out of common inner elements by class name convention.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cards: List[Dict[str, Any]] = []
        self._depth: List[str] = []
        self._card: Optional[Dict[str, Any]] = None
        self._card_depth = 0
        self._text_target: Optional[str] = None
        self._buffer = ""

    def handle_starttag(self, tag: str, attrs: List[tuple]) -> None:
        attr_map = dict(attrs)
        classes = attr_map.get("class", "") or ""
        class_list = classes.split()
        self._depth.append(tag)

        if self._card is None and "vehicle-card" in class_list:
            self._card = {}
            self._card_depth = len(self._depth)
            if attr_map.get("data-vin"):
                self._card["vin"] = attr_map["data-vin"]
            if attr_map.get("href") and tag == "a":
                self._card.setdefault("listing_url", attr_map["href"])
            return

        if self._card is None:
            return

        if tag == "a" and attr_map.get("href"):
            self._card.setdefault("listing_url", attr_map["href"])

        mapping = {
            "title": "title", "vehicle-card-link": "title",
            "primary-price": "price", "price": "price",
            "mileage": "mileage",
            "dealer-name": "dealer_name",
            "dealer-location": "dealer_location", "miles-from-user": "distance_miles",
            "stock-type": "cpo",
            "vin": "vin",
        }
        for css_class, field_name in mapping.items():
            if css_class in class_list:
                self._text_target = field_name
                self._buffer = ""
                break

    def handle_data(self, data: str) -> None:
        if self._text_target is not None:
            self._buffer += data

    def handle_endtag(self, tag: str) -> None:
        if self._text_target is not None:
            value = self._buffer.strip()
            if value and self._card is not None:
                self._card[self._text_target] = value
            self._text_target = None
            self._buffer = ""

        if self._depth:
            self._depth.pop()

        if self._card is not None and len(self._depth) < self._card_depth:
            self.cards.append(self._card)
            self._card = None
            self._card_depth = 0


def _parse_plain_cards(body: str) -> List[Dict[str, Any]]:
    parser = _PlainCardParser()
    try:
        parser.feed(body)
    except Exception:
        return []
    listings = []
    for fields in parser.cards:
        if "cpo" in fields:
            fields["cpo"] = "certified" in str(fields["cpo"]).lower()
        listing = _listing_from_fields(fields)
        if listing:
            listings.append(listing)
    return listings


@register
class CarsComScraper(ScraperBase):
    key = "cars_com"
    name = "Cars.com"
    site = "https://www.cars.com"
    kind = "listings"

    def search_urls(self, search: Dict[str, Any]) -> List[str]:
        params = {
            "stock_type": "used",
            "zip": search.get("zip"),
            "maximum_distance": search.get("radius_miles"),
            "list_price_max": search.get("price_max"),
            "mileage_max": search.get("mileage_max"),
            "year_min": search.get("year_min"),
            "page_size": search.get("rows_per_page") or 20,
        }
        params = {key: value for key, value in params.items() if value is not None}

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

        for strategy in (_parse_json_ld, _parse_data_attribute_cards, _parse_plain_cards):
            try:
                listings = strategy(body)
            except Exception:
                listings = []
            if listings:
                for listing in listings:
                    listing.setdefault("source", self.key)
                return listings
        return []
