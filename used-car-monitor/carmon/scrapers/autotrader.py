"""Autotrader adapter.

Autotrader has no public listings API. This adapter scrapes public search-result pages
instead, and it is **opt-in and capped**: it stays off unless both `scrapers.enabled` and
`scrapers.sources.autotrader` are switched on in config.json, and everything above this
module (see `carmon/scrapers/base.py`) enforces robots.txt, a slow request rate, and hard
daily caps regardless of what this adapter asks for.

robots.txt is obeyed unconditionally by the base `Fetcher`/`RobotsCache` — there is no
override here. As of the last manual check, Autotrader's `User-agent: *` block allows
`/cars-for-sale/all-cars` (the path this adapter targets) while disallowing `/research/`,
`*keyword=`, `/cars-for-sale/cbh/history/`, `/cars-for-sale/build-and-price`,
`/cars-for-sale/svc/listing-view-count`, and assorted `.xhtml` partials; this module never
targets those paths, and `search_urls()` also filters against a local copy of those
fragments as a second, redundant guard. robots.txt can change at any time, and the live
`RobotsCache` check in `base.py` is the actual authority, not this module.

**The parser has not been validated against live HTML.** From the datacenter IP this
adapter was written on, an actual Autotrader search request returns a bot-challenge shell
(a few KB of page mentioning "captcha"), not real listings, and `Fetcher.get()` correctly
raises `BlockedError` in that situation — which is the correct, intentional end of the
story, not a bug to route around. Per this project's rules, that challenge is never
evaded: no browser-mimicking headers, no cookies, no proxies, no retries with a new
identity, no CAPTCHA handling. If this adapter is blocked, `ScraperBase.run()` reports
status "blocked" and stops after exactly one request.

Because live HTML could not be fetched, `parse()` is written defensively against the
shape of markup Autotrader is documented (and generally known) to emit, in order of how
stable each source is expected to be:

  (a) `application/ld+json` schema.org `Car`/`Vehicle`/`Product` blocks — the most stable
      target, since it is SEO markup a site has a strong incentive to keep well-formed.
  (b) an embedded JSON state blob (`__NEXT_DATA__`, `window.__INITIAL_STATE__`, or a
      similarly named inline `<script>` payload) — found generically by searching the
      decoded JSON for any object carrying a VIN, rather than by hard-coding a specific
      page-state schema that is likely to drift.
  (c) an `html.parser`-based fallback over listing cards identified by a `data-vin`
      attribute, reading the sibling text nodes inside each card.

Strategies (b) and (c) both use "carries a VIN" as their signal for "this is a listing" —
that is a real limitation: a listing lacking a VIN in the source markup is invisible to
those two strategies. Strategy (a) has no such requirement and can surface a VIN-less
listing dict; per the base class, anything reaching `ScraperBase.run()` without a VIN is
then dropped there, since VIN is what deduplicates against MarketCheck data. All three
strategies return `[]`, never raise, when nothing recognizable is found — a markup change
should downgrade an adapter to "empty", not take down the whole run.

Review Autotrader's Terms of Service before enabling this adapter. Automated collection is
commonly restricted by such terms even where robots.txt is silent, and robots.txt
permission is necessary but not sufficient for this to be a good idea.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List
from urllib.parse import urlencode

from .base import ScraperBase, register
from .parsing import (
    CITY_STATE_RE as _CITY_STATE_RE,
    NEXT_DATA_SCRIPT_RE as _NEXT_DATA_RE,
    YEAR_RE as _YEAR_RE,
    absolute_url as _absolute_url,
    clean_str as _clean_str,
    extract_mileage as _extract_mileage,
    extract_year as _extract_year,
    find_ci as _find_ci,
    iter_ld_vehicle_nodes,
    parse_title_free_text as _parse_title_text,
    run_vin_anchored_card_parser,
    scalar as _scalar,
    to_float as _to_float,
    to_signed_int as _to_int,
    walk_dicts as _walk_dicts,
)

SEARCH_PATH = "/cars-for-sale/all-cars"

# Fragments known (from a manual robots.txt read) to be disallowed for User-agent: *.
# search_urls() never builds a URL containing one of these, as a second guard on top of
# the live robots.txt check every request already goes through in base.py.
DISALLOWED_PATH_FRAGMENTS = (
    "/research/",
    "keyword=",
    "/cars-for-sale/cbh/history/",
    "/cars-for-sale/build-and-price",
    "/cars-for-sale/svc/listing-view-count",
    ".xhtml",
)

_PAGE_SIZE = 25

# Autotrader-specific embedded-state convention: a generic `window.__SOMENAME__ = {...};`
# assignment, tried alongside the shared `__NEXT_DATA__` pattern (`_NEXT_DATA_RE`, imported
# from `parsing`) since either has been seen on Next.js-family sites.
_WINDOW_STATE_RE = re.compile(
    r"window\.__[A-Za-z0-9_]+__\s*=\s*(\{.*?\})\s*;\s*(?:</script>|\r?\n)", re.S
)


@register
class AutotraderScraper(ScraperBase):
    key = "autotrader"
    name = "Autotrader"
    site = "https://www.autotrader.com"
    kind = "listings"

    # --- search URL construction -----------------------------------------------
    def search_urls(self, search: Dict[str, Any]) -> List[str]:
        zip_code = _clean_str(search.get("zip"))
        if not zip_code:
            return []

        params: Dict[str, str] = {"zip": zip_code, "numRecords": str(_PAGE_SIZE)}

        radius = _to_int(search.get("radius_miles"))
        if radius is not None:
            params["searchRadius"] = str(radius)
        year_min = _to_int(search.get("year_min"))
        if year_min is not None:
            params["startYear"] = str(year_min)
        price_max = _to_int(search.get("price_max"))
        if price_max is not None:
            params["maxPrice"] = str(price_max)
        mileage_max = _to_int(search.get("mileage_max"))
        if mileage_max is not None:
            params["maxMileage"] = str(mileage_max)

        max_pages = max(0, int(self.limits.max_pages_per_run))
        urls: List[str] = []
        for page in range(max_pages):
            page_params = dict(params)
            page_params["firstRecord"] = str(page * _PAGE_SIZE)
            url = f"{self.site}{SEARCH_PATH}?{urlencode(page_params)}"
            if any(frag in url for frag in DISALLOWED_PATH_FRAGMENTS):
                continue  # should be unreachable given SEARCH_PATH, but never emit it anyway
            urls.append(url)
        return urls

    # --- parsing -----------------------------------------------------------------
    def parse(self, body: str, url: str) -> List[Dict[str, Any]]:
        if not body or not body.strip():
            return []
        for strategy in (self._parse_json_ld, self._parse_embedded_state, self._parse_html_cards):
            try:
                listings = strategy(body, url)
            except Exception:
                listings = []
            if listings:
                return listings
        return []

    # (a) schema.org JSON-LD -------------------------------------------------------
    def _parse_json_ld(self, body: str, url: str) -> List[Dict[str, Any]]:
        listings: List[Dict[str, Any]] = []
        seen_vins: set[str] = set()
        for node in iter_ld_vehicle_nodes(body):
            listing = self._listing_from_ld(node, url)
            vin = listing.get("vin")
            if vin:
                key = vin.upper()
                if key in seen_vins:
                    continue
                seen_vins.add(key)
            listings.append(listing)
        return listings

    def _listing_from_ld(self, obj: Dict[str, Any], url: str) -> Dict[str, Any]:
        listing: Dict[str, Any] = {}
        vin = _clean_str(
            obj.get("vehicleIdentificationNumber") or obj.get("vin") or obj.get("sku")
        )
        if vin:
            listing["vin"] = vin

        name = _clean_str(obj.get("name"))
        year = _extract_year(
            obj.get("vehicleModelDate") or obj.get("modelDate") or obj.get("productionDate")
        )
        make = _scalar(obj.get("brand"))
        model = _scalar(obj.get("model"))
        trim = _clean_str(obj.get("vehicleConfiguration") or obj.get("trim"))

        if (year is None or not make or not model) and name:
            parsed = _parse_title_text(name)
            year = year if year is not None else parsed.get("year")
            make = make or parsed.get("make")
            model = model or parsed.get("model")
            trim = trim or parsed.get("trim")

        if year is not None:
            listing["year"] = year
        if make:
            listing["make"] = make
        if model:
            listing["model"] = model
        if trim:
            listing["trim"] = trim

        body_type = _clean_str(obj.get("bodyType"))
        if body_type:
            listing["body_type"] = body_type
        fuel_type = _clean_str(obj.get("fuelType"))
        if fuel_type:
            listing["fuel_type"] = fuel_type

        mileage = _extract_mileage(obj.get("mileageFromOdometer"))
        if mileage is not None:
            listing["mileage"] = mileage

        offer = obj.get("offers")
        if isinstance(offer, list):
            offer = offer[0] if offer else None
        offer_url = None
        if isinstance(offer, dict):
            price_spec = offer.get("priceSpecification")
            price = _to_int(offer.get("price"))
            if price is None and isinstance(price_spec, dict):
                price = _to_int(price_spec.get("price"))
            if price is not None:
                listing["price_current"] = price
            seller = offer.get("seller")
            if isinstance(seller, dict):
                dealer_name = _clean_str(seller.get("name"))
                if dealer_name:
                    listing["dealer_name"] = dealer_name
                address = seller.get("address")
                if isinstance(address, dict):
                    city = _clean_str(address.get("addressLocality"))
                    state = _clean_str(address.get("addressRegion"))
                    if city:
                        listing["dealer_city"] = city
                    if state:
                        listing["dealer_state"] = state
            offer_url = _clean_str(offer.get("url"))

        listing["listing_url"] = offer_url or _clean_str(obj.get("url")) or url

        condition = _clean_str(obj.get("itemCondition")) or ""
        haystack = " ".join(filter(None, [name, condition])).lower()
        if "certified" in haystack:
            listing["cpo"] = True

        return listing

    # (b) embedded JSON page-state blob --------------------------------------------
    def _parse_embedded_state(self, body: str, url: str) -> List[Dict[str, Any]]:
        blobs: List[str] = []
        for regex in (_NEXT_DATA_RE, _WINDOW_STATE_RE):
            blobs.extend(match.group(1) for match in regex.finditer(body))

        listings: List[Dict[str, Any]] = []
        seen_vins: set[str] = set()
        for blob in blobs:
            try:
                data = json.loads(blob)
            except json.JSONDecodeError:
                continue
            for node in _walk_dicts(data):
                # A VIN is the anchor that identifies "this dict is a listing" in an
                # otherwise-unknown page-state blob; a listing without one is invisible
                # to this strategy (see module docstring).
                vin = _clean_str(_find_ci(node, "vin"))
                if not vin or vin.upper() in seen_vins:
                    continue
                seen_vins.add(vin.upper())
                listings.append(self._listing_from_state_dict(node, vin, url))
        return listings

    def _listing_from_state_dict(self, node: Dict[str, Any], vin: str, url: str) -> Dict[str, Any]:
        listing: Dict[str, Any] = {"vin": vin}

        year = _to_int(_find_ci(node, "year", "modelYear"))
        if year is not None:
            listing["year"] = year
        make = _clean_str(_find_ci(node, "make", "makeName", "brand"))
        if make:
            listing["make"] = make
        model = _clean_str(_find_ci(node, "model", "modelName"))
        if model:
            listing["model"] = model
        trim = _clean_str(_find_ci(node, "trim", "trimName"))
        if trim:
            listing["trim"] = trim
        body_type = _clean_str(_find_ci(node, "bodyType", "bodyStyle"))
        if body_type:
            listing["body_type"] = body_type
        fuel_type = _clean_str(_find_ci(node, "fuelType"))
        if fuel_type:
            listing["fuel_type"] = fuel_type

        mileage = _to_int(_find_ci(node, "mileage", "odometer", "miles"))
        if mileage is not None:
            listing["mileage"] = mileage
        price = _to_int(_find_ci(node, "price", "listPrice", "askingPrice", "currentPrice"))
        if price is not None:
            listing["price_current"] = price

        dealer = _find_ci(node, "dealer", "seller")
        if isinstance(dealer, dict):
            dealer_name = _clean_str(_find_ci(dealer, "name", "dealerName"))
            dealer_city = _clean_str(_find_ci(dealer, "city"))
            dealer_state = _clean_str(_find_ci(dealer, "state"))
        else:
            dealer_name = _clean_str(_find_ci(node, "dealerName", "sellerName"))
            dealer_city = _clean_str(_find_ci(node, "dealerCity"))
            dealer_state = _clean_str(_find_ci(node, "dealerState"))
        if dealer_name:
            listing["dealer_name"] = dealer_name
        if dealer_city:
            listing["dealer_city"] = dealer_city
        if dealer_state:
            listing["dealer_state"] = dealer_state

        distance = _to_float(_find_ci(node, "distance", "distanceMiles"))
        if distance is not None:
            listing["distance_miles"] = distance

        cpo_value = _find_ci(node, "certified", "isCertified", "cpo")
        if isinstance(cpo_value, str):
            cpo = cpo_value.strip().lower() in ("true", "yes", "1", "certified")
        else:
            cpo = bool(cpo_value)
        if cpo:
            listing["cpo"] = True

        listing_url = _clean_str(_find_ci(node, "url", "listingUrl", "vdpUrl", "href"))
        listing["listing_url"] = _absolute_url(url, listing_url) or listing_url or url

        return listing

    # (c) html.parser fallback over listing cards -----------------------------------
    def _parse_html_cards(self, body: str, url: str) -> List[Dict[str, Any]]:
        listings: List[Dict[str, Any]] = []
        seen_vins: set[str] = set()
        for card in run_vin_anchored_card_parser(body):
            vin = _clean_str(card.get("vin"))
            if not vin or vin.upper() in seen_vins:
                continue
            seen_vins.add(vin.upper())
            listings.append(self._listing_from_card(card, url))
        return listings

    def _listing_from_card(self, card: Dict[str, Any], url: str) -> Dict[str, Any]:
        listing: Dict[str, Any] = {"vin": _clean_str(card.get("vin"))}

        for raw_chunk in card.get("parts", []):
            chunk = raw_chunk.strip()
            if not chunk:
                continue
            low = chunk.lower()

            if "certified" in low:
                listing["cpo"] = True

            if _CITY_STATE_RE.match(chunk):
                city, state = chunk.rsplit(",", 1)
                listing.setdefault("dealer_city", city.strip())
                listing.setdefault("dealer_state", state.strip())
                continue

            if "$" in chunk and "price_current" not in listing:
                price = _to_int(chunk)
                if price is not None:
                    listing["price_current"] = price
                    continue

            if re.search(r"\bmi(?:les)?\b", low) and "mileage" not in listing:
                mileage = _to_int(chunk)
                if mileage is not None:
                    listing["mileage"] = mileage
                    continue

            if "year" not in listing and _YEAR_RE.search(chunk):
                for k, v in _parse_title_text(chunk).items():
                    listing.setdefault(k, v)
                continue

            if (
                "dealer_name" not in listing
                and "year" in listing
                and "certified" not in low
                and not re.search(r"\d", chunk)
            ):
                listing["dealer_name"] = chunk

        listing["listing_url"] = _absolute_url(url, card.get("href")) or url
        return listing
