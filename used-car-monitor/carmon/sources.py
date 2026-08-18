"""Deep links to other places the same search can be run by hand.

v1 does not scrape any of these — SPEC.md lists scraping as an explicit non-goal.
Each entry builds a search URL pre-filled with the criteria from config.json, so
the daily digest, website, API and MCP server can hand you (or an assistant) a
one-click "same search, over there" link.

If MarketCheck turns out not to be worth the quota, `Source.adapter` marks which
of these have a scraper-shaped adapter slot ready in `carmon/scrapers/`.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List
from urllib.parse import quote_plus


@dataclass
class Source:
    key: str
    name: str
    category: str
    url: str
    note: str
    adapter: str = "not-implemented"

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


CATEGORIES = {
    "manufacturer_cpo": (
        "Franchise dealer CPO programs — manufacturer-backed warranties (the strongest "
        "coverage of the three categories). Prices run higher, but this is the lowest-risk lane."
    ),
    "retailer": (
        "Big used-car retailers — no-haggle pricing and a short return window "
        "(CarMax and Carvana both offer 7 days). You pay a small premium for the convenience."
    ),
    "aggregator": (
        "Marketplace aggregators — the widest view of the market; CarGurus adds a deal rating "
        "(great/good/fair/overpriced) versus comparable national listings."
    ),
}


def _search(criteria: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "zip": str(criteria.get("zip", "")),
        "radius": int(criteria.get("radius_miles", 100) or 100),
        "year_min": int(criteria.get("year_min", 2021) or 2021),
        "price_max": int(criteria.get("price_max", 20000) or 20000),
        "mileage_max": int(criteria.get("mileage_max", 60000) or 60000),
    }


def build_sources(search_config: Dict[str, Any]) -> List[Source]:
    """Build the link list from the same criteria the daily job uses."""
    c = _search(search_config)
    zip_code, radius = c["zip"], c["radius"]
    year_min, price_max, miles_max = c["year_min"], c["price_max"], c["mileage_max"]

    sources: List[Source] = [
        # --- manufacturer-backed CPO ------------------------------------
        Source(
            "toyota_certified", "Toyota Certified Used Vehicles", "manufacturer_cpo",
            f"https://www.toyotacertified.com/inventory?zip={zip_code}&distance={radius}"
            f"&maxPrice={price_max}&maxMileage={miles_max}&minYear={year_min}",
            "Manufacturer-backed CPO: 12mo/12k comprehensive + 7yr/100k powertrain from original in-service date.",
            adapter="stub",
        ),
        Source(
            "honda_certified", "Honda Certified Pre-Owned", "manufacturer_cpo",
            f"https://automobiles.honda.com/certified-pre-owned-inventory?zip={zip_code}&radius={radius}"
            f"&maxPrice={price_max}&maxMileage={miles_max}",
            "Manufacturer-backed CPO: 7yr/100k powertrain, non-powertrain coverage extended 1yr/12k.",
            adapter="stub",
        ),
        Source(
            "hyundai_certified", "Hyundai Certified Pre-Owned", "manufacturer_cpo",
            f"https://www.hyundaiusa.com/us/en/certified-pre-owned/inventory?zip={zip_code}&radius={radius}",
            "Manufacturer-backed CPO: remainder of 10yr/100k powertrain + 1yr/12k platinum coverage.",
        ),
        Source(
            "kia_certified", "Kia Certified Pre-Owned", "manufacturer_cpo",
            f"https://www.kia.com/us/en/certified-pre-owned/inventory?zip={zip_code}",
            "Manufacturer-backed CPO: 10yr/100k powertrain from original in-service date.",
        ),
        Source(
            "mazda_certified", "Mazda Certified Pre-Owned", "manufacturer_cpo",
            f"https://www.mazdausa.com/shopping-tools/certified-pre-owned/inventory?zip={zip_code}",
            "Manufacturer-backed CPO: 12mo/12k limited warranty + 7yr/100k powertrain.",
        ),
        # --- big retailers ----------------------------------------------
        Source(
            "carmax", "CarMax", "retailer",
            f"https://www.carmax.com/cars?zip={zip_code}&distance={radius}"
            f"&price=0-{price_max}&mileage=0-{miles_max}&year={year_min}-2026",
            "No-haggle pricing, 7-day return (money-back) window, optional MaxCare extended warranty.",
            adapter="stub",
        ),
        Source(
            "carvana", "Carvana", "retailer",
            f"https://www.carvana.com/cars/filters?zip={zip_code}"
            f"&price-range=0-{price_max}&mileage-range=0-{miles_max}&year-range={year_min}-2026",
            "No-haggle pricing, 7-day return window, delivered or picked up; national inventory (radius ignored).",
            adapter="stub",
        ),
        Source(
            "vroom", "Vroom", "retailer",
            "https://www.vroom.com/cars"
            f"?price_max={price_max}&mileage_max={miles_max}&year_min={year_min}",
            "No-haggle online retailer, national inventory. Verify current return policy before buying.",
        ),
        # --- aggregators -------------------------------------------------
        Source(
            "cargurus", "CarGurus", "aggregator",
            f"https://www.cargurus.com/Cars/inventorylisting/viewDetailsFilterViewInventoryListing.action"
            f"?zip={zip_code}&distance={radius}&maxPrice={price_max}&maxMileage={miles_max}"
            f"&startYear={year_min}&inventorySearchWidgetType=AUTO",
            "Deal rating (great/good/fair/overpriced) versus comparable national listings — good price sanity check.",
            adapter="stub",
        ),
        Source(
            "autotrader", "Autotrader", "aggregator",
            f"https://www.autotrader.com/cars-for-sale/all-cars?zip={zip_code}&searchRadius={radius}"
            f"&maxPrice={price_max}&endYear=2026&startYear={year_min}&maxMileage={miles_max}",
            "Very broad franchise + independent dealer coverage.",
            adapter="stub",
        ),
        Source(
            "cars_com", "Cars.com", "aggregator",
            f"https://www.cars.com/shopping/results/?zip={zip_code}&maximum_distance={radius}"
            f"&list_price_max={price_max}&mileage_max={miles_max}&year_min={year_min}"
            "&stock_type=used",
            "Broad dealer coverage plus dealer reviews and price-history badges.",
            adapter="stub",
        ),
        Source(
            "truecar", "TrueCar", "aggregator",
            f"https://www.truecar.com/used-cars-for-sale/listings/?location={zip_code}"
            f"&searchRadius={radius}&priceHigh={price_max}&mileageHigh={miles_max}&yearLow={year_min}",
            "Shows what others paid for the same car — useful for judging whether a price is out of line.",
        ),
    ]
    return sources


def sources_for_listing(listing: Dict[str, Any], search_config: Dict[str, Any]) -> List[Dict[str, str]]:
    """Cross-shop links for one specific car (same year/make/model elsewhere)."""
    c = _search(search_config)
    year = listing.get("year") or ""
    make = (listing.get("make") or "").strip()
    model = (listing.get("model") or "").strip()
    if not make or not model:
        return []
    q = quote_plus(f"{year} {make} {model}".strip())
    make_slug = quote_plus(make.lower())
    model_slug = quote_plus(model.lower().replace(" ", "-"))
    return [
        {
            "name": "CarGurus (deal rating)",
            "url": f"https://www.cargurus.com/Cars/spt_used-{make_slug}-{model_slug}?zip={c['zip']}&distance={c['radius']}",
        },
        {
            "name": "Cars.com",
            "url": f"https://www.cars.com/shopping/results/?makes[]={make_slug}&models[]={make_slug}-{model_slug}"
                   f"&zip={c['zip']}&maximum_distance={c['radius']}&stock_type=used",
        },
        {
            "name": "CarMax",
            "url": f"https://www.carmax.com/cars/{make_slug}/{model_slug}?zip={c['zip']}&distance={c['radius']}",
        },
        {"name": "Google search", "url": f"https://www.google.com/search?q={q}+for+sale+near+{c['zip']}"},
    ]


def sources_as_dicts(search_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [source.as_dict() for source in build_sources(search_config)]


def grouped_sources(search_config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = {
        key: {"description": text, "sources": []} for key, text in CATEGORIES.items()
    }
    for source in build_sources(search_config):
        grouped.setdefault(source.category, {"description": "", "sources": []})
        grouped[source.category]["sources"].append(source.as_dict())
    return grouped
