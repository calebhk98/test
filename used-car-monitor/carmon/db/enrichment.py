"""Enrichment caches: NHTSA reliability, EPA fuel economy, and RepairPal repair cost."""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict, List, Optional

from . import _util
from .schema import now_str


def get_reliability(
    conn: sqlite3.Connection, make: str, model: str, year: int, max_age_days: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """Cached NHTSA facts for a make/model/year, or None if absent or stale."""
    row = conn.execute(
        "SELECT * FROM model_reliability WHERE make = ? AND model = ? AND year = ?",
        _util.model_key(make, model, year),
    ).fetchone()
    if row is None:
        return None
    data = dict(row)
    _util.decode_json_columns(data, "top_components", "recalls")
    if _util.is_stale(data.get("fetched_at"), max_age_days):
        return None
    return data


def save_reliability(conn: sqlite3.Connection, make: str, model: str, year: int, facts: Dict[str, Any]) -> None:
    key = _util.model_key(make, model, year)
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
        "SELECT * FROM model_mpg WHERE make = ? AND model = ? AND year = ?",
        _util.model_key(make, model, year),
    ).fetchone()
    if row is None:
        return None
    data = dict(row)
    if _util.is_stale(data.get("fetched_at"), max_age_days):
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
            *_util.model_key(make, model, year), mpg.get("city_mpg"), mpg.get("highway_mpg"),
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
    _util.decode_json_columns(data, "common_problems", on_error="keep")
    return data
