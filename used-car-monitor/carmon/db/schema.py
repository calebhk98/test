"""Schema, migrations, connection setup, and the row/dict conversion every query relies on."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import _util

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

CREATE TABLE IF NOT EXISTS scraper_status (
    source       TEXT PRIMARY KEY,
    last_run_at  TEXT,
    status       TEXT,
    message      TEXT,
    pages        INTEGER DEFAULT 0,
    listings     INTEGER DEFAULT 0,
    kept         INTEGER DEFAULT 0,
    ok_runs      INTEGER DEFAULT 0,
    failed_runs  INTEGER DEFAULT 0,
    last_ok_at   TEXT,
    last_error   TEXT,
    last_error_at TEXT
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
    _util.decode_json_columns(data, "score_breakdown")
    return data
