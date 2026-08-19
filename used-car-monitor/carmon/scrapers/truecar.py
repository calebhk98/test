"""TrueCar adapter.

TrueCar has no public listings API, so this adapter scrapes its search-results HTML. It
is **opt-in and capped** like every other adapter in this package: it stays off unless
both `scrapers.enabled` and `scrapers.sources.truecar` are switched on in config.json, and
everything above this module (see `carmon/scrapers/base.py`) enforces robots.txt, a slow
request rate, and hard daily caps regardless of what this adapter asks for.

robots.txt is obeyed unconditionally by the base `Fetcher`/`RobotsCache` -- there is no
override here, and there is no config flag anywhere in this project that can turn it off.
Unlike most other sources this package touches, **TrueCar's `robots.txt` is actually
fetchable (HTTP 200) from this machine**, so it was read directly rather than guessed at.
Its `User-agent: *` block disallows, among other things:

  * `/*?*zipcode=`                                -- the zip-code query param, spelled
                                                       exactly that way
  * `*listings/*?*drivetrain=`, `*listings/*?*transmission=`, `*listings/*?*engine=`
                                                    -- three specific filter params on
                                                       listings pages
  * `/used-cars-for-sale/listing/*` (singular)     -- individual vehicle detail pages
  * `/used-cars-for-sale/listings/inventory/*`     -- an inventory sub-path
  * `/user/`, `/my/`, `/dash/`                     -- account-area paths

This adapter avoids every one of those on purpose: `search_urls()` stays on the plural
`/used-cars-for-sale/listings/` search path (never the singular `/listing/` detail path or
the `/listings/inventory/` sub-path), identifies the zip code with `location=` (never
`zipcode=`), and never emits `drivetrain=`, `transmission=`, or `engine=` query params --
those three filters are simply not offered by `search_urls()`. `DISALLOWED_PATH_FRAGMENTS`
below is a second, local, redundant guard on top of the live `RobotsCache` check every
request already goes through in `base.py`: `search_urls()` refuses to emit a URL
containing any of those fragments even if a future edit to this file tried to add one.
robots.txt can change at any time, and the live check in `base.py` remains the actual
authority, not this local copy.

**Even though robots.txt is readable here, the listings page itself is not.** An actual
TrueCar search request from this machine returns **HTTP 403** to a plain, non-browser
client, so `Fetcher.get()` correctly raises `BlockedError` and `ScraperBase.run()` reports
status "blocked" after exactly one request -- which is the correct, intentional end of the
story, not a bug to route around. Per this project's rules, that block is never evaded: no
browser-mimicking User-Agent or headers, no cookies, no proxies, no retries with a new
identity, no CAPTCHA handling. A home/residential connection may well see something
different, since datacenter IPs are disproportionately blocked by this kind of front door,
but that has not been verified from here.

Because a real listings page could not be fetched from this environment, **`parse()` below
has never been exercised against live TrueCar HTML and is unvalidated.** It is written
defensively against markup TrueCar is documented (and generally known) to emit, in order
of how stable each source is expected to be:

  (a) `application/ld+json` schema.org `Car`/`Vehicle`/`Product` blocks -- the most stable
      target, since it is SEO markup a site has a strong incentive to keep well-formed.
  (b) TrueCar is a Next.js application, so its server-rendered pages typically ship a
      `<script id="__NEXT_DATA__">` JSON blob carrying the page's props. This strategy
      looks generically for any object in that blob carrying a VIN, rather than hard-coding
      a specific props schema that is likely to drift, and also looks for TrueCar's
      distinctive price-context fields (a "great/good/fair price"-style rating and a
      market-average comparison) wherever they appear alongside a VIN.
  (c) an `html.parser`-based fallback over listing cards identified by a `data-vin`
      attribute (or a `data-qa`/class hint containing "vin"), reading sibling text nodes
      inside each card, including any price-rating badge text and "$X below/above market
      average"-style copy.

Strategies (b) and (c) both use "carries a VIN" as their signal for "this is a listing" --
a listing lacking a VIN in the source markup is invisible to those two strategies. Strategy
(a) has no such requirement and can surface a VIN-less listing dict; per the base class,
anything reaching `ScraperBase.run()` without a VIN is dropped there, since VIN is what
deduplicates against MarketCheck data. All three strategies return `[]`, never raise, when
nothing recognizable is found -- a markup change should downgrade an adapter to "empty",
not take down the whole run.

Review TrueCar's Terms of Service before enabling this adapter. robots.txt permission is
necessary but not sufficient for this to be a good idea, and automated collection is
commonly restricted by a site's terms even where robots.txt is silent on a given path.
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

SEARCH_PATH = "/used-cars-for-sale/listings/"

# Fragments read directly out of TrueCar's (fetchable) robots.txt `User-agent: *` block.
# search_urls() never builds a URL containing one of these, as a second, local guard on
# top of the live robots.txt check every request already goes through in base.py.
DISALLOWED_PATH_FRAGMENTS = (
    "zipcode=",
    "drivetrain=",
    "transmission=",
    "engine=",
    "/used-cars-for-sale/listing/",       # singular -- vehicle detail pages
    "/used-cars-for-sale/listings/inventory/",
    "/user/",
    "/my/",
    "/dash/",
)

_DEAL_RATING_RE = re.compile(
    r"\b(Great|Good|Fair|High|Overpriced)\s+(?:Price|Deal)\b", re.I
)


@register
class TrueCarScraper(ScraperBase):
    key = "truecar"
    name = "TrueCar"
    site = "https://www.truecar.com"
    kind = "listings"

    # --- search URL construction -----------------------------------------------
    def search_urls(self, search: Dict[str, Any]) -> List[str]:
        zip_code = _clean_str(search.get("zip"))
        if not zip_code:
            return []

        params: Dict[str, str] = {"location": zip_code}

        radius = _to_int(search.get("radius_miles"))
        if radius is not None:
            params["searchRadius"] = str(radius)
        price_max = _to_int(search.get("price_max"))
        if price_max is not None:
            params["priceHigh"] = str(price_max)
        mileage_max = _to_int(search.get("mileage_max"))
        if mileage_max is not None:
            params["mileageHigh"] = str(mileage_max)
        year_min = _to_int(search.get("year_min"))
        if year_min is not None:
            params["yearLow"] = str(year_min)

        max_pages = max(0, int(self.limits.max_pages_per_run))
        urls: List[str] = []
        for page in range(1, max_pages + 1):
            page_params = dict(params)
            page_params["page"] = str(page)
            url = f"{self.site}{SEARCH_PATH}?{urlencode(page_params)}"
            if any(frag in url for frag in DISALLOWED_PATH_FRAGMENTS):
                continue  # should be unreachable given the params built above, but never emit it anyway
            urls.append(url)
        return urls

    # --- parsing -----------------------------------------------------------------
    def parse(self, body: str, url: str) -> List[Dict[str, Any]]:
        if not body or not body.strip():
            return []
        for strategy in (self._parse_json_ld, self._parse_next_data, self._parse_html_cards):
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

        # TrueCar's distinctive price-context datum, when schema.org carries it at all.
        deal_rating = _clean_str(
            obj.get("dealRating") or obj.get("priceRating") or obj.get("priceLabel")
        )
        if deal_rating:
            listing["deal_rating"] = deal_rating
        market_average = _to_int(
            obj.get("marketAverage") or obj.get("marketAveragePrice") or obj.get("averagePrice")
        )
        if market_average is not None:
            listing["market_average"] = market_average

        condition = _clean_str(obj.get("itemCondition")) or ""
        haystack = " ".join(filter(None, [name, condition])).lower()
        if "certified" in haystack:
            listing["cpo"] = True

        return listing

    # (b) __NEXT_DATA__ embedded JSON props blob -------------------------------------
    def _parse_next_data(self, body: str, url: str) -> List[Dict[str, Any]]:
        listings: List[Dict[str, Any]] = []
        seen_vins: set[str] = set()
        for match in _NEXT_DATA_RE.finditer(body):
            raw = match.group(1).strip()
            if not raw:
                continue
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            for node in _walk_dicts(data):
                # A VIN is the anchor that identifies "this dict is a listing" in an
                # otherwise-unknown Next.js props tree; a listing without one is invisible
                # to this strategy (see module docstring).
                vin = _clean_str(_find_ci(node, "vin"))
                if not vin or vin.upper() in seen_vins:
                    continue
                seen_vins.add(vin.upper())
                listings.append(self._listing_from_next_data(node, vin, url))
        return listings

    def _listing_from_next_data(self, node: Dict[str, Any], vin: str, url: str) -> Dict[str, Any]:
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

        # TrueCar's distinctive price-context datum: a "great/good/fair price"-style
        # rating plus a market-average comparison, when the props tree carries them.
        deal_rating = _clean_str(
            _find_ci(node, "dealRating", "priceRating", "priceLabel", "priceIndicator")
        )
        if deal_rating:
            listing["deal_rating"] = deal_rating
        market_average = _to_int(
            _find_ci(node, "marketAverage", "marketAveragePrice", "averagePrice", "marketPrice")
        )
        if market_average is not None:
            listing["market_average"] = market_average

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

            deal_match = _DEAL_RATING_RE.search(chunk)
            if deal_match and "deal_rating" not in listing:
                listing["deal_rating"] = deal_match.group(0)
                continue

            market_match = re.search(
                r"\$([\d,]+)\s+(?:below|above|under|over)\s+market\s+average", chunk, re.I
            )
            if market_match and "market_average" not in listing and "price_current" in listing:
                # The badge states a *difference* from the market average, not the average
                # itself; recover the average from the known asking price plus/minus that
                # difference rather than guessing at the average directly.
                diff = _to_int(market_match.group(1))
                if diff is not None:
                    # "$X below market average" -> the average is X *above* the asking
                    # price; "$X above market average" -> the average is X *below* it.
                    sign = 1 if re.search(r"below|under", chunk, re.I) else -1
                    listing["market_average"] = listing["price_current"] + sign * diff
                continue

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
                and not deal_match
                and not re.search(r"\d", chunk)
            ):
                listing["dealer_name"] = chunk

        listing["listing_url"] = _absolute_url(url, card.get("href")) or url
        return listing
