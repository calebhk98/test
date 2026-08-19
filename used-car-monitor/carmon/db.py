"""SQLite storage: listings, price history, API-usage log, and run log."""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

SCHEMA = """
CREATE TABLE IF NOT EXISTS listings (
    vin             TEXT PRIMARY KEY,
    first_seen      TEXT NOT NULL,
    last_seen       TEXT NOT NULL,
    year            INTEGER,
    make            TEXT,
    model           TEXT,
    trim            TEXT,
    body_type       TEXT,
    fuel_type       TEXT,
    city_mpg        INTEGER,
    highway_mpg     INTEGER,
    combined_mpg    REAL,
    mileage         INTEGER,
    price_current   INTEGER,
    price_first_seen INTEGER,
    dealer_name     TEXT,
    dealer_city     TEXT,
    dealer_state    TEXT,
    distance_miles  REAL,
    cpo             INTEGER DEFAULT 0,
    listing_url     TEXT,
    score           REAL,
    score_breakdown TEXT,
    market_expected_price REAL,
    market_delta_pct      REAL,
    market_sample_size    INTEGER,
    market_grade          TEXT,
    market_confidence     TEXT,
    source          TEXT DEFAULT 'marketcheck',
    active          INTEGER DEFAULT 1,
    updated_at      TEXT
);

CREATE TABLE IF NOT EXISTS price_history (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    vin      TEXT NOT NULL,
    date     TEXT NOT NULL,
    price    INTEGER,
    mileage  INTEGER,
    FOREIGN KEY (vin) REFERENCES listings(vin)
);

CREATE TABLE IF NOT EXISTS api_usage (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ts        TEXT NOT NULL,
    month     TEXT NOT NULL,
    endpoint  TEXT,
    status    INTEGER,
    note      TEXT
);

CREATE TABLE IF NOT EXISTS model_repair_cost (
    make               TEXT NOT NULL,
    model              TEXT NOT NULL,
    annual_repair_cost REAL,
    reliability_rating REAL,
    rating_scale       REAL,
    visits_per_year    REAL,
    severity_pct       REAL,
    rank_text          TEXT,
    common_problems    TEXT,
    source             TEXT,
    source_url         TEXT,
    fetched_at         TEXT,
    PRIMARY KEY (make, model)
);

CREATE TABLE IF NOT EXISTS scrape_usage (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ts        TEXT NOT NULL,
    day       TEXT NOT NULL,
    source    TEXT NOT NULL,
    kind      TEXT,
    url       TEXT,
    status    INTEGER,
    listings  INTEGER DEFAULT 0,
    note      TEXT
);

CREATE TABLE IF NOT EXISTS runs (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date       TEXT NOT NULL,
    started_at     TEXT NOT NULL,
    finished_at    TEXT,
    status         TEXT,
    api_calls      INTEGER DEFAULT 0,
    listings_seen  INTEGER DEFAULT 0,
    new_count      INTEGER DEFAULT 0,
    price_drop_count INTEGER DEFAULT 0,
    digest_path    TEXT,
    error          TEXT
);

CREATE TABLE IF NOT EXISTS model_reliability (
    make             TEXT NOT NULL,
    model            TEXT NOT NULL,
    year             INTEGER NOT NULL,
    complaint_count  INTEGER,
    recall_count     INTEGER,
    crash_complaints INTEGER,
    fire_complaints  INTEGER,
    injuries         INTEGER,
    deaths           INTEGER,
    top_components   TEXT,
    recalls          TEXT,
    source           TEXT DEFAULT 'nhtsa',
    fetched_at       TEXT,
    PRIMARY KEY (make, model, year)
);

CREATE TABLE IF NOT EXISTS model_mpg (
    make         TEXT NOT NULL,
    model        TEXT NOT NULL,
    year         INTEGER NOT NULL,
    city_mpg     REAL,
    highway_mpg  REAL,
    combined_mpg REAL,
    matched_name TEXT,
    source       TEXT,
    fetched_at   TEXT,
    PRIMARY KEY (make, model, year)
);

CREATE INDEX IF NOT EXISTS idx_listings_score ON listings(score DESC);
CREATE INDEX IF NOT EXISTS idx_listings_first_seen ON listings(first_seen);
CREATE INDEX IF NOT EXISTS idx_listings_last_seen ON listings(last_seen);
CREATE INDEX IF NOT EXISTS idx_listings_model ON listings(make, model, year);
CREATE INDEX IF NOT EXISTS idx_price_history_vin ON price_history(vin, date);
CREATE INDEX IF NOT EXISTS idx_api_usage_month ON api_usage(month);
CREATE INDEX IF NOT EXISTS idx_scrape_usage_day ON scrape_usage(day, source);
"""

LISTING_COLUMNS = [
    "vin", "first_seen", "last_seen", "year", "make", "model", "trim", "body_type",
    "fuel_type", "city_mpg", "highway_mpg", "combined_mpg", "mileage", "price_current",
    "price_first_seen", "dealer_name",
    "dealer_city", "dealer_state", "distance_miles", "cpo", "listing_url", "score",
    "score_breakdown", "source", "active", "updated_at",
]

SORTABLE = {
    "score": "score DESC, price_current ASC",
    "price": "price_current ASC",
    "price_desc": "price_current DESC",
    "mileage": "mileage ASC",
    "distance": "distance_miles ASC",
    "year": "year DESC",
    "first_seen": "first_seen DESC",
    "last_seen": "last_seen DESC",
}


def today_str() -> str:
    return date.today().isoformat()


def now_str() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(db_path: Path | str) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


MIGRATIONS = {
    "listings": {
        "city_mpg": "INTEGER",
        "highway_mpg": "INTEGER",
        "combined_mpg": "REAL",
        # Market comparison, recomputed after each run (see market.py / pipeline.py).
        "market_expected_price": "REAL",
        "market_delta_pct": "REAL",
        "market_sample_size": "INTEGER",
        "market_grade": "TEXT",
        "market_confidence": "TEXT",
    },
}


def migrate(conn: sqlite3.Connection) -> List[str]:
    """Add columns that older databases predate. Safe to run on every startup."""
    applied: List[str] = []
    for table, columns in MIGRATIONS.items():
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        for column, column_type in columns.items():
            if column not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
                applied.append(f"{table}.{column}")
    if applied:
        conn.commit()
    return applied


def init_db(db_path: Path | str) -> sqlite3.Connection:
    conn = connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    migrate(conn)
    return conn


def row_to_dict(row: sqlite3.Row | None) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    data = dict(row)
    if "cpo" in data:
        data["cpo"] = bool(data["cpo"])
    if "active" in data:
        data["active"] = bool(data["active"])
    breakdown = data.get("score_breakdown")
    if isinstance(breakdown, str) and breakdown:
        try:
            data["score_breakdown"] = json.loads(breakdown)
        except json.JSONDecodeError:
            data["score_breakdown"] = None
    return data


# --- listings -----------------------------------------------------------
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
    clauses: List[str] = []
    params: List[Any] = []
    if active_only:
        clauses.append("active = 1")
    if make:
        clauses.append("LOWER(make) = LOWER(?)")
        params.append(make)
    if model:
        clauses.append("LOWER(model) LIKE LOWER(?)")
        params.append(f"{model}%")
    if max_price is not None:
        clauses.append("price_current <= ?")
        params.append(max_price)
    if min_price is not None:
        clauses.append("price_current >= ?")
        params.append(min_price)
    if max_mileage is not None:
        clauses.append("mileage <= ?")
        params.append(max_mileage)
    if min_year is not None:
        clauses.append("year >= ?")
        params.append(min_year)
    if max_distance is not None:
        clauses.append("distance_miles <= ?")
        params.append(max_distance)
    if min_score is not None:
        clauses.append("score >= ?")
        params.append(min_score)
    if cpo_only:
        clauses.append("cpo = 1")
    if new_since:
        clauses.append("first_seen >= ?")
        params.append(new_since)
    if query:
        clauses.append(
            "(LOWER(make) LIKE LOWER(?) OR LOWER(model) LIKE LOWER(?) OR LOWER(trim) LIKE LOWER(?) "
            "OR LOWER(dealer_name) LIKE LOWER(?) OR LOWER(vin) LIKE LOWER(?))"
        )
        params.extend([f"%{query}%"] * 5)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    order = SORTABLE.get(sort, SORTABLE["score"])
    limit = max(1, min(int(limit), 500))
    offset = max(0, int(offset))
    rows = conn.execute(
        f"SELECT * FROM listings {where} ORDER BY {order} LIMIT ? OFFSET ?",
        (*params, limit, offset),
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


# --- API usage ----------------------------------------------------------
def record_api_call(conn: sqlite3.Connection, endpoint: str, status: Optional[int], note: str = "") -> None:
    ts = now_str()
    conn.execute(
        "INSERT INTO api_usage (ts, month, endpoint, status, note) VALUES (?, ?, ?, ?, ?)",
        (ts, ts[:7], endpoint, status, note),
    )
    conn.commit()


def calls_this_month(conn: sqlite3.Connection, month: Optional[str] = None) -> int:
    month = month or now_str()[:7]
    row = conn.execute("SELECT COUNT(*) AS n FROM api_usage WHERE month = ?", (month,)).fetchone()
    return int(row["n"])


def usage_by_month(conn: sqlite3.Connection, limit: int = 12) -> List[Dict[str, Any]]:
    rows = conn.execute(
        "SELECT month, COUNT(*) AS calls FROM api_usage GROUP BY month ORDER BY month DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(row) for row in rows]


# --- runs ---------------------------------------------------------------
def start_run(conn: sqlite3.Connection, run_date: Optional[str] = None) -> int:
    cur = conn.execute(
        "INSERT INTO runs (run_date, started_at, status) VALUES (?, ?, 'running')",
        (run_date or today_str(), now_str()),
    )
    conn.commit()
    return int(cur.lastrowid)


def finish_run(conn: sqlite3.Connection, run_id: int, **fields: Any) -> None:
    allowed = {"status", "api_calls", "listings_seen", "new_count", "price_drop_count", "digest_path", "error"}
    sets, params = ["finished_at = ?"], [now_str()]
    for key, value in fields.items():
        if key in allowed:
            sets.append(f"{key} = ?")
            params.append(value)
    params.append(run_id)
    conn.execute(f"UPDATE runs SET {', '.join(sets)} WHERE id = ?", params)
    conn.commit()


def recent_runs(conn: sqlite3.Connection, limit: int = 10) -> List[Dict[str, Any]]:
    rows = conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(row) for row in rows]


def stats(conn: sqlite3.Connection, monthly_cap: int = 500) -> Dict[str, Any]:
    total = count_listings(conn, active_only=False)
    active = count_listings(conn, active_only=True)
    row = conn.execute(
        "SELECT AVG(price_current) AS avg_price, MIN(price_current) AS min_price, "
        "MAX(score) AS best_score FROM listings WHERE active = 1"
    ).fetchone()
    used = calls_this_month(conn)
    last_run = conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 1").fetchone()
    return {
        "listings_total": total,
        "listings_active": active,
        "avg_price": round(row["avg_price"], 2) if row["avg_price"] else None,
        "min_price": row["min_price"],
        "best_score": row["best_score"],
        "api_calls_this_month": used,
        "api_monthly_cap": monthly_cap,
        "api_calls_remaining": max(0, monthly_cap - used),
        "usage_by_month": usage_by_month(conn),
        "last_run": dict(last_run) if last_run else None,
    }


# --- enrichment caches (NHTSA reliability, EPA fuel economy) -------------
def _model_key(make: Optional[str], model: Optional[str], year: Optional[int]) -> Tuple[str, str, int]:
    return ((make or "").strip().lower(), (model or "").strip().lower(), int(year or 0))


def get_reliability(
    conn: sqlite3.Connection, make: str, model: str, year: int, max_age_days: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """Cached NHTSA facts for a make/model/year, or None if absent or stale."""
    row = conn.execute(
        "SELECT * FROM model_reliability WHERE make = ? AND model = ? AND year = ?", _model_key(make, model, year)
    ).fetchone()
    if row is None:
        return None
    data = dict(row)
    for field in ("top_components", "recalls"):
        if isinstance(data.get(field), str) and data[field]:
            try:
                data[field] = json.loads(data[field])
            except json.JSONDecodeError:
                data[field] = None
    if max_age_days is not None and data.get("fetched_at"):
        try:
            fetched = datetime.fromisoformat(data["fetched_at"])
            if (datetime.now(timezone.utc) - fetched).days > max_age_days:
                return None
        except ValueError:
            return None
    return data


def save_reliability(conn: sqlite3.Connection, make: str, model: str, year: int, facts: Dict[str, Any]) -> None:
    key = _model_key(make, model, year)
    conn.execute(
        """
        INSERT INTO model_reliability
            (make, model, year, complaint_count, recall_count, crash_complaints, fire_complaints,
             injuries, deaths, top_components, recalls, source, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(make, model, year) DO UPDATE SET
            complaint_count = excluded.complaint_count, recall_count = excluded.recall_count,
            crash_complaints = excluded.crash_complaints, fire_complaints = excluded.fire_complaints,
            injuries = excluded.injuries, deaths = excluded.deaths,
            top_components = excluded.top_components, recalls = excluded.recalls,
            source = excluded.source, fetched_at = excluded.fetched_at
        """,
        (
            *key,
            facts.get("complaint_count"), facts.get("recall_count"), facts.get("crash_complaints"),
            facts.get("fire_complaints"), facts.get("injuries"), facts.get("deaths"),
            json.dumps(facts.get("top_components") or []), json.dumps(facts.get("recalls") or []),
            facts.get("source", "nhtsa"), now_str(),
        ),
    )
    conn.commit()


def get_mpg(
    conn: sqlite3.Connection, make: str, model: str, year: int, max_age_days: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    row = conn.execute(
        "SELECT * FROM model_mpg WHERE make = ? AND model = ? AND year = ?", _model_key(make, model, year)
    ).fetchone()
    if row is None:
        return None
    data = dict(row)
    if max_age_days is not None and data.get("fetched_at"):
        try:
            fetched = datetime.fromisoformat(data["fetched_at"])
            if (datetime.now(timezone.utc) - fetched).days > max_age_days:
                return None
        except ValueError:
            return None
    return data


def save_mpg(conn: sqlite3.Connection, make: str, model: str, year: int, mpg: Dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO model_mpg (make, model, year, city_mpg, highway_mpg, combined_mpg, matched_name, source, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(make, model, year) DO UPDATE SET
            city_mpg = excluded.city_mpg, highway_mpg = excluded.highway_mpg,
            combined_mpg = excluded.combined_mpg, matched_name = excluded.matched_name,
            source = excluded.source, fetched_at = excluded.fetched_at
        """,
        (
            *_model_key(make, model, year), mpg.get("city_mpg"), mpg.get("highway_mpg"),
            mpg.get("combined_mpg"), mpg.get("matched_name"), mpg.get("source", "fueleconomy.gov"), now_str(),
        ),
    )
    conn.commit()


def distinct_model_years(conn: sqlite3.Connection, active_only: bool = True) -> List[Dict[str, Any]]:
    """Every make/model/year combination currently stored — the enrichment work list."""
    clauses = ["make IS NOT NULL", "model IS NOT NULL", "year IS NOT NULL"]
    if active_only:
        clauses.append("active = 1")
    rows = conn.execute(
        f"SELECT DISTINCT make, model, year FROM listings WHERE {' AND '.join(clauses)} ORDER BY make, model, year"
    ).fetchall()
    return [dict(row) for row in rows]


def save_appraisal(
    conn: sqlite3.Connection, vin: str, appraisal: Dict[str, Any], commit: bool = True
) -> None:
    """Store the market comparison for a listing so the UI and scorer can read it cheaply.

    Pass commit=False when writing many rows in a loop and commit once at the end.
    """
    conn.execute(
        "UPDATE listings SET market_expected_price = ?, market_delta_pct = ?, "
        "market_sample_size = ?, market_grade = ?, market_confidence = ? WHERE vin = ?",
        (
            appraisal.get("expected_price"), appraisal.get("delta_pct"),
            appraisal.get("sample_size"), appraisal.get("grade"), appraisal.get("confidence"), vin,
        ),
    )
    if commit:
        conn.commit()


# --- scraper usage ledger ------------------------------------------------
def record_scrape(
    conn: sqlite3.Connection, source: str, kind: str, url: str,
    status: Optional[int] = None, listings: int = 0, note: str = "",
) -> None:
    """Log one scraper request. This ledger is what enforces the daily caps."""
    ts = now_str()
    conn.execute(
        "INSERT INTO scrape_usage (ts, day, source, kind, url, status, listings, note) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (ts, ts[:10], source, kind, url, status, listings, note),
    )
    conn.commit()


def scrape_usage_today(conn: sqlite3.Connection, source: Optional[str] = None, day: Optional[str] = None) -> Dict[str, int]:
    """Requests made and listings taken today, per source or across all of them.

    Only rows that represent an actual HTTP fetch count as requests; the `listings` rows are
    tallies of what a fetched page yielded, not extra traffic.
    """
    day = day or today_str()
    clauses, params = ["day = ?"], [day]
    if source:
        clauses.append("source = ?")
        params.append(source)
    where = " AND ".join(clauses)
    row = conn.execute(
        f"SELECT COALESCE(SUM(CASE WHEN kind != 'listings' THEN 1 ELSE 0 END), 0) AS requests, "
        f"COALESCE(SUM(listings), 0) AS listings FROM scrape_usage WHERE {where}",
        params,
    ).fetchone()
    return {"requests": int(row["requests"]), "listings": int(row["listings"]), "day": day}


def scrape_usage_by_source(conn: sqlite3.Connection, day: Optional[str] = None) -> List[Dict[str, Any]]:
    day = day or today_str()
    rows = conn.execute(
        "SELECT source, COALESCE(SUM(CASE WHEN kind != 'listings' THEN 1 ELSE 0 END), 0) AS requests, "
        "COALESCE(SUM(listings), 0) AS listings "
        "FROM scrape_usage WHERE day = ? GROUP BY source ORDER BY source",
        (day,),
    ).fetchall()
    return [dict(row) for row in rows]


def save_repair_cost(conn: sqlite3.Connection, make: str, model: str, data: Dict[str, Any]) -> None:
    """Store scraped repair-cost / reliability facts for a model (see scrapers/repairpal.py)."""
    key = ((make or "").strip().lower(), (model or "").strip().lower())
    problems = data.get("common_problems")
    conn.execute(
        """
        INSERT INTO model_repair_cost
            (make, model, annual_repair_cost, reliability_rating, rating_scale, visits_per_year,
             severity_pct, rank_text, common_problems, source, source_url, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(make, model) DO UPDATE SET
            annual_repair_cost = excluded.annual_repair_cost,
            reliability_rating = excluded.reliability_rating,
            rating_scale = excluded.rating_scale,
            visits_per_year = excluded.visits_per_year,
            severity_pct = excluded.severity_pct,
            rank_text = excluded.rank_text,
            common_problems = excluded.common_problems,
            source = excluded.source, source_url = excluded.source_url,
            fetched_at = excluded.fetched_at
        """,
        (
            *key, data.get("annual_repair_cost"), data.get("reliability_rating"),
            data.get("rating_scale"), data.get("visits_per_year"), data.get("severity_pct"),
            data.get("rank_text"),
            json.dumps(problems) if isinstance(problems, (list, dict)) else problems,
            data.get("source", "repairpal"), data.get("source_url"), now_str(),
        ),
    )
    conn.commit()


def get_repair_cost(conn: sqlite3.Connection, make: str, model: str) -> Optional[Dict[str, Any]]:
    row = conn.execute(
        "SELECT * FROM model_repair_cost WHERE make = ? AND model = ?",
        ((make or "").strip().lower(), (model or "").strip().lower()),
    ).fetchone()
    if row is None:
        return None
    data = dict(row)
    if isinstance(data.get("common_problems"), str) and data["common_problems"]:
        try:
            data["common_problems"] = json.loads(data["common_problems"])
        except json.JSONDecodeError:
            pass
    return data
