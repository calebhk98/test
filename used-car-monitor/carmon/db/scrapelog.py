"""Scraper request ledger (what enforces the daily caps) and adapter health status."""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional

from ..sqlfilters import Filters, eq
from .schema import now_str, today_str


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
    f = Filters()
    f.add("day = ?", day)
    eq(f, "source", source)
    row = conn.execute(
        f"SELECT COALESCE(SUM(CASE WHEN kind != 'listings' THEN 1 ELSE 0 END), 0) AS requests, "
        f"COALESCE(SUM(listings), 0) AS listings FROM scrape_usage {f.where()}",
        f.params,
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


def save_scraper_status(conn: sqlite3.Connection, source: str, result: Dict[str, Any]) -> None:
    """Record the outcome of one adapter run, keeping running ok/failure tallies."""
    status = str(result.get("status") or "unknown")
    message = result.get("message") or ""
    now = now_str()
    ok = status == "ok"
    existing = conn.execute("SELECT * FROM scraper_status WHERE source = ?", (source,)).fetchone()
    ok_runs = (existing["ok_runs"] if existing else 0) + (1 if ok else 0)
    failed_runs = (existing["failed_runs"] if existing else 0) + (0 if ok else 1)
    conn.execute(
        """
        INSERT INTO scraper_status
            (source, last_run_at, status, message, pages, listings, kept, ok_runs, failed_runs,
             last_ok_at, last_error, last_error_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source) DO UPDATE SET
            last_run_at = excluded.last_run_at, status = excluded.status,
            message = excluded.message, pages = excluded.pages, listings = excluded.listings,
            kept = excluded.kept, ok_runs = excluded.ok_runs, failed_runs = excluded.failed_runs,
            last_ok_at = COALESCE(excluded.last_ok_at, scraper_status.last_ok_at),
            last_error = COALESCE(excluded.last_error, scraper_status.last_error),
            last_error_at = COALESCE(excluded.last_error_at, scraper_status.last_error_at)
        """,
        (
            source, now, status, message, int(result.get("pages_fetched") or 0),
            int(result.get("listings") or 0), int(result.get("kept_after_filters") or 0),
            ok_runs, failed_runs,
            now if ok else None,
            None if ok else (message or status),
            None if ok else now,
        ),
    )
    conn.commit()


def get_scraper_status(conn: sqlite3.Connection, source: Optional[str] = None) -> List[Dict[str, Any]]:
    if source:
        rows = conn.execute("SELECT * FROM scraper_status WHERE source = ?", (source,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM scraper_status ORDER BY source").fetchall()
    return [dict(row) for row in rows]


def recent_scrape_events(conn: sqlite3.Connection, limit: int = 25, source: Optional[str] = None) -> List[Dict[str, Any]]:
    """The raw request log — what was fetched, when, and with what result."""
    f = Filters()
    eq(f, "source", source)
    rows = conn.execute(
        f"SELECT ts, day, source, kind, url, status, listings, note FROM scrape_usage {f.where()} "
        "ORDER BY id DESC LIMIT ?",
        (*f.params, max(1, min(int(limit), 200))),
    ).fetchall()
    return [dict(row) for row in rows]
