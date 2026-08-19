"""MarketCheck quota pacing.

500 calls/month is only meaningful next to how much of the month has gone by: 100 calls
on the 15th is relaxed, 100 calls on the 5th is not. This module turns the raw counter
into that comparison — expected-by-now, pace ratio, projected month-end total, and how
many calls a day are still affordable.

Nothing here limits anything. The only hard stop remains the cap itself, enforced in
`marketcheck.py`; this is purely the metric, surfaced in the digest, the Discord message,
the website, the API and the MCP server.
"""

from __future__ import annotations

import calendar
import sqlite3
from datetime import date
from typing import Any, Dict, Optional

from . import db

# Pace ratio thresholds -> label. A ratio of 1.0 means "exactly on track to finish the
# month at the cap"; below 1.0 means you are using the quota more slowly than the month
# is passing.
PACE_BANDS = (
    (0.60, "well under pace", "🟢"),
    (0.90, "under pace", "🟢"),
    (1.10, "on pace", "🟡"),
    (1.40, "running hot", "🟠"),
    (float("inf"), "far ahead of pace", "🔴"),
)


def month_progress(today: Optional[date] = None) -> Dict[str, Any]:
    """How far through the month we are."""
    today = today or date.today()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    return {
        "date": today.isoformat(),
        "month": today.strftime("%Y-%m"),
        "day_of_month": today.day,
        "days_in_month": days_in_month,
        "days_remaining": days_in_month - today.day,
        "is_last_day": today.day == days_in_month,
        "elapsed_fraction": round(today.day / days_in_month, 4),
    }


def pace(used: int, cap: int, today: Optional[date] = None) -> Dict[str, Any]:
    """Compare calls used against how much of the month has elapsed."""
    progress = month_progress(today)
    cap = max(1, int(cap))
    used = max(0, int(used))
    elapsed = progress["elapsed_fraction"]
    expected = cap * elapsed
    ratio = (used / expected) if expected > 0 else 0.0
    projected = (used / elapsed) if elapsed > 0 else float(used)
    remaining = max(0, cap - used)
    days_left = progress["days_remaining"]
    # Today is already under way, so the remaining budget is spread over the days left
    # plus the rest of today.
    per_day = remaining / max(1, days_left) if days_left else float(remaining)

    label, icon = next((text, mark) for threshold, text, mark in PACE_BANDS if ratio <= threshold)

    return {
        **progress,
        "used": used,
        "cap": cap,
        "remaining": remaining,
        "expected_by_now": round(expected, 1),
        "difference": round(used - expected, 1),
        "pace_ratio": round(ratio, 2),
        "pace_label": label,
        "pace_icon": icon,
        "projected_month_total": round(projected, 1),
        "projected_overshoot": round(max(0.0, projected - cap), 1),
        "affordable_per_day": round(per_day, 1),
    }


def pace_from_db(conn: sqlite3.Connection, cap: int, today: Optional[date] = None) -> Dict[str, Any]:
    today = today or date.today()
    return pace(db.calls_this_month(conn, today.strftime("%Y-%m")), cap, today)


def summary_line(metrics: Dict[str, Any]) -> str:
    """One-line human summary, e.g.
    '100/500 calls · day 15/31 · expected ~242 by now · 0.41x pace (well under pace) · ~26/day still affordable'
    """
    difference = metrics["difference"]
    direction = "under" if difference <= 0 else "over"
    return (
        f"{metrics['used']}/{metrics['cap']} calls · day {metrics['day_of_month']}/{metrics['days_in_month']} · "
        f"expected ~{metrics['expected_by_now']:.0f} by now ({abs(difference):.0f} {direction}) · "
        f"{metrics['pace_ratio']:.2f}x pace ({metrics['pace_label']}) · "
        f"~{metrics['affordable_per_day']:.0f}/day still affordable"
    )


def bar(metrics: Dict[str, Any], width: int = 24) -> str:
    """A tiny text gauge: filled = quota used, '|' = where the month currently sits."""
    width = max(4, int(width))
    used_cells = min(width, round(width * metrics["used"] / metrics["cap"]))
    month_cell = min(width - 1, round(width * metrics["elapsed_fraction"]))
    cells = ["█" if i < used_cells else "░" for i in range(width)]
    cells[month_cell] = "|" if cells[month_cell] == "░" else "┃"
    return "".join(cells)


# --- month-end sweep ----------------------------------------------------
def sweep_budget(
    used: int, cap: int, sweep_config: Optional[Dict[str, Any]] = None, today: Optional[date] = None
) -> Dict[str, Any]:
    """How many leftover calls the month-end sweep may spend today.

    Unused free-tier calls expire worthless at midnight on the last day of the month, so
    on that day the monitor spends what is left (minus a small reserve) widening the
    search rather than letting it evaporate.
    """
    config = sweep_config or {}
    progress = month_progress(today)
    remaining = max(0, int(cap) - int(used))
    reserve = int(config.get("reserve_calls", 20))
    max_extra = int(config.get("max_extra_calls", 400))
    enabled = bool(config.get("enabled", True))
    trigger_days = int(config.get("trigger_last_days", 1))
    is_window = progress["days_remaining"] < trigger_days or progress["is_last_day"]

    budget = max(0, min(remaining - reserve, max_extra))
    should_sweep = enabled and is_window and budget > 0
    if not enabled:
        reason = "month-end sweep disabled in config"
    elif not is_window:
        reason = (
            f"not the sweep window yet ({progress['days_remaining']} day(s) left in "
            f"{progress['month']}; sweep runs on the last {trigger_days} day(s))"
        )
    elif budget <= 0:
        reason = f"only {remaining} call(s) left, at or below the {reserve}-call reserve"
    else:
        reason = (
            f"last day of {progress['month']} with {remaining} unused call(s) — spending up to "
            f"{budget} of them before they expire (keeping {reserve} in reserve)"
        )

    return {**progress, "remaining": remaining, "reserve": reserve, "budget": budget,
            "should_sweep": should_sweep, "reason": reason}
