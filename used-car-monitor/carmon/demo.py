"""Deterministic demo data.

Lets you browse the website, API and MCP server before a MarketCheck key exists.
Everything it writes is tagged `source='demo'` so it is obvious in the UI and easy
to delete (`python -m carmon seed-demo --clear`).
"""

from __future__ import annotations

import random
import sqlite3
from datetime import date, timedelta
from typing import Any, Dict, List

from . import db
from .config import Config
from .scoring import score_listing

FLEET = [
    ("Toyota", "Corolla", "LE", "Sedan"),
    ("Toyota", "Corolla Hatchback", "SE", "Hatchback"),
    ("Honda", "Civic", "Sport", "Sedan"),
    ("Honda", "Civic", "EX", "Sedan"),
    ("Hyundai", "Elantra", "SEL", "Sedan"),
    ("Mazda", "Mazda3", "Select", "Sedan"),
    ("Kia", "Forte", "GT-Line", "Sedan"),
    ("Nissan", "Sentra", "SV", "Sedan"),
    ("Nissan", "Altima", "S", "Sedan"),
    ("Nissan", "Versa", "SV", "Sedan"),
    ("Subaru", "Impreza", "Premium", "Hatchback"),
    ("Chevrolet", "Trax", "LT", "SUV"),
    ("Kia", "Seltos", "S", "SUV"),
    ("Hyundai", "Kona", "SEL", "SUV"),
    ("Volkswagen", "Jetta", "S", "Sedan"),
]

DEALERS = [
    ("Lawrenceburg Auto Group", "Lawrenceburg", "TN", 8.0),
    ("Columbia Motor Co", "Columbia", "TN", 31.0),
    ("Florence Certified Cars", "Florence", "AL", 44.0),
    ("Franklin Premier Autos", "Franklin", "TN", 72.0),
    ("Huntsville Value Motors", "Huntsville", "AL", 95.0),
]


def clear_demo(conn: sqlite3.Connection) -> int:
    vins = [row["vin"] for row in conn.execute("SELECT vin FROM listings WHERE source = 'demo'").fetchall()]
    conn.executemany("DELETE FROM price_history WHERE vin = ?", [(vin,) for vin in vins])
    conn.execute("DELETE FROM listings WHERE source = 'demo'")
    conn.commit()
    return len(vins)


def seed(config: Config, conn: sqlite3.Connection, count: int = 18, seed_value: int = 20260818) -> List[str]:
    """Insert `count` demo listings with a few days of price history behind them."""
    rng = random.Random(seed_value)
    today = date.today()
    vins: List[str] = []

    for index in range(count):
        make, model, trim, body = FLEET[index % len(FLEET)]
        dealer_name, city, state, base_distance = DEALERS[index % len(DEALERS)]
        year = rng.choice([2021, 2021, 2022, 2022, 2023])
        mileage = rng.randrange(12000, 58000, 250)
        price = rng.randrange(12500, 19900, 50)
        cpo = rng.random() < 0.3
        distance = round(base_distance + rng.uniform(-6, 9), 1)
        vin = f"DEMO{seed_value}{index:03d}".ljust(17, "X")[:17]
        first_seen = today - timedelta(days=rng.randint(0, 9))

        listing: Dict[str, Any] = {
            "vin": vin,
            "year": year,
            "make": make,
            "model": model,
            "trim": trim,
            "body_type": body,
            "fuel_type": "Unleaded",
            "mileage": mileage,
            "price_current": price,
            "dealer_name": dealer_name,
            "dealer_city": city,
            "dealer_state": state,
            "distance_miles": distance,
            "cpo": cpo,
            "listing_url": f"https://example-dealer.test/vehicle/{vin}",
            "source": "demo",
        }
        listing["price_first_seen"] = price
        score = score_listing(listing, config.scoring)
        listing["score"] = score.score
        listing["score_breakdown"] = score.as_dict()["components"]
        db.upsert_listing(conn, listing, seen_date=first_seen.isoformat())

        # A third of the fleet gets a price drop (and a couple of extra miles) today.
        if rng.random() < 0.34:
            drop = rng.randrange(200, 1200, 50)
            listing = dict(listing)
            listing["price_current"] = price - drop
            listing["mileage"] = mileage + rng.randint(20, 400)
            listing["price_first_seen"] = price
            score = score_listing(listing, config.scoring)
            listing["score"] = score.score
            listing["score_breakdown"] = score.as_dict()["components"]
            db.upsert_listing(conn, listing, seen_date=today.isoformat())
        else:
            db.upsert_listing(conn, listing, seen_date=today.isoformat())
        vins.append(vin)

    return vins
