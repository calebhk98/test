"""MarketCheck API-call ledger and the daily-run log."""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional

from .listings import count_listings
from .schema import now_str, today_str


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
