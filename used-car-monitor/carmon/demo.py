"""Deterministic demo data.

Lets you browse the website, API and MCP server before a MarketCheck key exists.
Everything it writes is tagged `source='demo'`, and it is designed to be impossible to
mistake for real inventory:

* a real `carmon run` deletes every demo row before it stores anything;
* demo data expires by itself after `demo.auto_clear_hours` (default 12) — any command,
  including the web server, clears it once it is stale;
* while demo rows exist, the CLI, digest, Discord message, website, API and MCP server
  all say so out loud.
"""

from __future__ import annotations

import logging
import random
import sqlite3
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from . import db
from .config import Config
from .scoring import score_listing

LOG = logging.getLogger("carmon.demo")

DEMO_SOURCE = "demo"
DEFAULT_AUTO_CLEAR_HOURS = 12

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


def demo_count(conn: sqlite3.Connection) -> int:
    """How many demo listings are currently stored (0 means the DB is all real data)."""
    try:
        row = conn.execute("SELECT COUNT(*) AS n FROM listings WHERE source = ?", (DEMO_SOURCE,)).fetchone()
    except sqlite3.Error:
        return 0
    return int(row["n"]) if row else 0


def demo_age_hours(conn: sqlite3.Connection) -> Optional[float]:
    """Age of the newest demo row in hours, or None when there is no demo data."""
    row = conn.execute(
        "SELECT MAX(updated_at) AS newest FROM listings WHERE source = ?", (DEMO_SOURCE,)
    ).fetchone()
    if not row or not row["newest"]:
        return None
    try:
        seeded = datetime.fromisoformat(row["newest"])
    except ValueError:
        return None
    if seeded.tzinfo is None:
        seeded = seeded.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - seeded).total_seconds() / 3600.0


def maybe_expire(conn: sqlite3.Connection, config: Optional[Config] = None, force: bool = False) -> int:
    """Delete demo data once it is stale (or immediately when `force` is set).

    Called at the start of every CLI command, by the web server, and unconditionally
    (force=True) by a real daily run — so demo rows cannot quietly outlive their welcome
    and be mistaken for real listings.
    """
    if demo_count(conn) == 0:
        return 0
    if force:
        removed = clear_demo(conn)
        LOG.info("Cleared %s demo listing(s) before storing real data.", removed)
        return removed
    hours = DEFAULT_AUTO_CLEAR_HOURS
    if config is not None:
        hours = float(config.data.get("demo", {}).get("auto_clear_hours", DEFAULT_AUTO_CLEAR_HOURS))
    if hours <= 0:
        return 0
    age = demo_age_hours(conn)
    if age is not None and age >= hours:
        removed = clear_demo(conn)
        LOG.info("Demo data was %.1fh old (limit %.1fh) — cleared %s listing(s).", age, hours, removed)
        return removed
    return 0


def demo_banner(conn: sqlite3.Connection) -> Optional[str]:
    """A warning to show wherever listings are displayed, or None if the data is all real."""
    count = demo_count(conn)
    if not count:
        return None
    age = demo_age_hours(conn)
    age_text = f", seeded {age:.1f}h ago" if age is not None else ""
    return (
        f"DEMO DATA: {count} of these listings are fake{age_text}. They are not real cars, "
        "they auto-clear, and a real `carmon run` deletes them first. "
        "Remove them now with `python3 -m carmon seed-demo --clear`."
    )


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
