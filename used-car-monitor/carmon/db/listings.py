"""Listings CRUD and the price-history it appends to."""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict, List, Optional

from ..sqlfilters import Filters, compare, eq_lower, prefix_lower
from .schema import LISTING_COLUMNS, SORTABLE, now_str, row_to_dict, today_str


def get_listing(conn: sqlite3.Connection, vin: str) -> Optional[Dict[str, Any]]:
    row = conn.execute("SELECT * FROM listings WHERE vin = ?", (vin,)).fetchone()
    return row_to_dict(row)


def upsert_listing(conn: sqlite3.Connection, listing: Dict[str, Any], seen_date: str | None = None) -> Dict[str, Any]:
    """Insert or update one listing, appending price_history when price/mileage moved.

    Returns a change record: {'vin', 'is_new', 'price_changed', 'mileage_changed',
    'old_price', 'new_price', 'old_mileage', 'new_mileage', 'price_first_seen'}.
    """
    seen_date = seen_date or today_str()
    vin = listing["vin"]
    existing = get_listing(conn, vin)
    change: Dict[str, Any] = {
        "vin": vin,
        "is_new": existing is None,
        "price_changed": False,
        "mileage_changed": False,
        "old_price": existing.get("price_current") if existing else None,
        "new_price": listing.get("price_current"),
        "old_mileage": existing.get("mileage") if existing else None,
        "new_mileage": listing.get("mileage"),
    }

    if existing is None:
        record = {col: listing.get(col) for col in LISTING_COLUMNS}
        record.update(
            {
                "vin": vin,
                "first_seen": seen_date,
                "last_seen": seen_date,
                "price_first_seen": listing.get("price_current"),
                "cpo": 1 if listing.get("cpo") else 0,
                "active": 1,
                "source": listing.get("source") or "marketcheck",
                "updated_at": now_str(),
            }
        )
        if isinstance(record.get("score_breakdown"), (dict, list)):
            record["score_breakdown"] = json.dumps(record["score_breakdown"])
        placeholders = ", ".join("?" for _ in LISTING_COLUMNS)
        conn.execute(
            f"INSERT INTO listings ({', '.join(LISTING_COLUMNS)}) VALUES ({placeholders})",
            [record[col] for col in LISTING_COLUMNS],
        )
        conn.execute(
            "INSERT INTO price_history (vin, date, price, mileage) VALUES (?, ?, ?, ?)",
            (vin, seen_date, listing.get("price_current"), listing.get("mileage")),
        )
        change["price_first_seen"] = listing.get("price_current")
        conn.commit()
        return change

    price_changed = (
        listing.get("price_current") is not None
        and listing.get("price_current") != existing.get("price_current")
    )
    mileage_changed = (
        listing.get("mileage") is not None and listing.get("mileage") != existing.get("mileage")
    )
    change["price_changed"] = bool(price_changed)
    change["mileage_changed"] = bool(mileage_changed)
    change["price_first_seen"] = existing.get("price_first_seen")

    breakdown = listing.get("score_breakdown")
    if isinstance(breakdown, (dict, list)):
        breakdown = json.dumps(breakdown)

    conn.execute(
        """
        UPDATE listings SET
            last_seen = ?, year = COALESCE(?, year), make = COALESCE(?, make),
            model = COALESCE(?, model), trim = COALESCE(?, trim),
            body_type = COALESCE(?, body_type), fuel_type = COALESCE(?, fuel_type),
            city_mpg = COALESCE(?, city_mpg), highway_mpg = COALESCE(?, highway_mpg),
            combined_mpg = COALESCE(?, combined_mpg), mileage = COALESCE(?, mileage), price_current = COALESCE(?, price_current),
            dealer_name = COALESCE(?, dealer_name), dealer_city = COALESCE(?, dealer_city),
            dealer_state = COALESCE(?, dealer_state), distance_miles = COALESCE(?, distance_miles),
            cpo = ?, listing_url = COALESCE(?, listing_url), score = ?, score_breakdown = ?,
            active = 1, updated_at = ?
        WHERE vin = ?
        """,
        (
            seen_date, listing.get("year"), listing.get("make"), listing.get("model"),
            listing.get("trim"), listing.get("body_type"), listing.get("fuel_type"),
            listing.get("city_mpg"), listing.get("highway_mpg"), listing.get("combined_mpg"),
            listing.get("mileage"), listing.get("price_current"), listing.get("dealer_name"),
            listing.get("dealer_city"), listing.get("dealer_state"), listing.get("distance_miles"),
            1 if listing.get("cpo") else 0, listing.get("listing_url"), listing.get("score"),
            breakdown, now_str(), vin,
        ),
    )
    if price_changed or mileage_changed:
        conn.execute(
            "INSERT INTO price_history (vin, date, price, mileage) VALUES (?, ?, ?, ?)",
            (vin, seen_date, listing.get("price_current"), listing.get("mileage")),
        )
    conn.commit()
    return change


def mark_inactive_before(conn: sqlite3.Connection, seen_date: str) -> int:
    """Flag listings not seen in the latest run as inactive (likely sold/removed)."""
    cur = conn.execute("UPDATE listings SET active = 0 WHERE last_seen < ? AND active = 1", (seen_date,))
    conn.commit()
    return cur.rowcount


def search_listings(
    conn: sqlite3.Connection,
    *,
    make: Optional[str] = None,
    model: Optional[str] = None,
    max_price: Optional[int] = None,
    min_price: Optional[int] = None,
    max_mileage: Optional[int] = None,
    min_year: Optional[int] = None,
    max_distance: Optional[float] = None,
    min_score: Optional[float] = None,
    cpo_only: bool = False,
    active_only: bool = True,
    new_since: Optional[str] = None,
    query: Optional[str] = None,
    sort: str = "score",
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    f = Filters()
    if active_only:
        f.add("active = 1")
    eq_lower(f, "make", make)
    prefix_lower(f, "model", model)
    compare(f, "price_current", "<=", max_price)
    compare(f, "price_current", ">=", min_price)
    compare(f, "mileage", "<=", max_mileage)
    compare(f, "year", ">=", min_year)
    compare(f, "distance_miles", "<=", max_distance)
    compare(f, "score", ">=", min_score)
    if cpo_only:
        f.add("cpo = 1")
    if new_since:
        f.add("first_seen >= ?", new_since)
    if query:
        f.add(
            "(LOWER(make) LIKE LOWER(?) OR LOWER(model) LIKE LOWER(?) OR LOWER(trim) LIKE LOWER(?) "
            "OR LOWER(dealer_name) LIKE LOWER(?) OR LOWER(vin) LIKE LOWER(?))",
            *([f"%{query}%"] * 5),
        )

    order = SORTABLE.get(sort, SORTABLE["score"])
    limit = max(1, min(int(limit), 500))
    offset = max(0, int(offset))
    rows = conn.execute(
        f"SELECT * FROM listings {f.where()} ORDER BY {order} LIMIT ? OFFSET ?",
        (*f.params, limit, offset),
    ).fetchall()
    return [row_to_dict(row) for row in rows]


def count_listings(conn: sqlite3.Connection, active_only: bool = True) -> int:
    sql = "SELECT COUNT(*) AS n FROM listings" + (" WHERE active = 1" if active_only else "")
    return int(conn.execute(sql).fetchone()["n"])


def get_price_history(conn: sqlite3.Connection, vin: str) -> List[Dict[str, Any]]:
    rows = conn.execute(
        "SELECT vin, date, price, mileage FROM price_history WHERE vin = ? ORDER BY date ASC, id ASC",
        (vin,),
    ).fetchall()
    return [dict(row) for row in rows]


def new_listings_since(conn: sqlite3.Connection, since_date: str, limit: int = 50) -> List[Dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM listings WHERE first_seen >= ? AND active = 1 ORDER BY score DESC, price_current ASC LIMIT ?",
        (since_date, limit),
    ).fetchall()
    return [row_to_dict(row) for row in rows]


def price_drops_since(conn: sqlite3.Connection, since_date: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Listings whose newest price_history point is lower than the point before it."""
    rows = conn.execute(
        """
        WITH ranked AS (
            SELECT vin, date, price, mileage,
                   ROW_NUMBER() OVER (PARTITION BY vin ORDER BY date DESC, id DESC) AS rn
            FROM price_history
        )
        SELECT l.*, latest.price AS new_price, prev.price AS old_price, latest.date AS drop_date
        FROM listings l
        JOIN ranked latest ON latest.vin = l.vin AND latest.rn = 1
        JOIN ranked prev   ON prev.vin = l.vin AND prev.rn = 2
        WHERE latest.date >= ? AND latest.price IS NOT NULL AND prev.price IS NOT NULL
          AND latest.price < prev.price AND l.active = 1
        ORDER BY (prev.price - latest.price) DESC
        LIMIT ?
        """,
        (since_date, limit),
    ).fetchall()
    results = []
    for row in rows:
        data = row_to_dict(row)
        data["price_drop"] = (data.get("old_price") or 0) - (data.get("new_price") or 0)
        results.append(data)
    return results
