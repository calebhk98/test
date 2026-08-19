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

from typing import Any, Dict, List, Optional

from urllib.parse import urlencode

from .base import ScraperBase, register
from .parsing import (
    clean_str as _clean_str,
    find_vin_in_strings,
    iter_ld_vehicle_nodes,
    ld_offer_price_and_seller,
    name_of as _name_of,
    parse_vehicle_title,
    run_class_card_parser,
    run_data_attribute_card_scanner,
    split_dealer_location as _split_dealer_location,
    to_bool as _to_bool,
    to_float as _to_float,
    to_int as _to_int,
)

SEARCH_PATH = "/shopping/results/"


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

    trim = fields.get("trim") or fields.get("vehicleConfiguration")

    title = fields.get("title") or fields.get("name") or fields.get("heading")
    parsed_title = parse_vehicle_title(title, known_trim=trim) if title else {}
    year = parsed_title.get("year")
    make = parsed_title.get("make")
    model = parsed_title.get("model")
    trim = parsed_title.get("trim", trim)

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


# --- strategy 2: embedded JSON / data-attribute cards ---------------------
# Cars.com's markup convention (or at least the convention this unvalidated parser is
# written against) puts each card's full data on data-* attributes of one element carrying
# a "vehicle-card" class, rather than nested inner elements -- see `parsing.
# DataAttributeCardScanner` for why that needs nothing more than a marker class.

def _parse_data_attribute_cards(body: str) -> List[Dict[str, Any]]:
    listings = []
    for fields in run_data_attribute_card_scanner(body, "vehicle-card"):
        listing = _listing_from_fields(fields)
        if listing:
            listings.append(listing)
    return listings


# --- strategy 3: plain HTML card walk --------------------------------------
# Last-resort walk: pull VIN/title/price/mileage text out of listing-card-ish markup.
# Looks for elements whose class mentions "vehicle-card" (same container as strategy 2,
# covering pages that render the card wrapper but skip the data-* attributes) and reads
# plain text out of common inner elements by class name convention.

_PLAIN_CARD_FIELD_CLASSES = {
    "title": "title", "vehicle-card-link": "title",
    "primary-price": "price", "price": "price",
    "mileage": "mileage",
    "dealer-name": "dealer_name",
    "dealer-location": "dealer_location", "miles-from-user": "distance_miles",
    "stock-type": "cpo",
    "vin": "vin",
}


def _parse_plain_cards(body: str) -> List[Dict[str, Any]]:
    cards = run_class_card_parser(
        body, "vehicle-card", _PLAIN_CARD_FIELD_CLASSES, capture_data_attrs={"vin"}
    )
    listings = []
    for fields in cards:
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
