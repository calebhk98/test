"""Self-contained JSON API + HTML dashboard for browsing the listings DB.

Stdlib only (http.server / socketserver / sqlite3 / json / urllib). No Flask/FastAPI,
no external CSS/JS/CDN assets -- every page embeds its own CSS/JS inline.

Each request opens its own sqlite connection (sqlite3.Connection objects are not
thread-safe) and closes it in a `finally` block. The server runs on a
socketserver.ThreadingTCPServer so slow clients don't block each other.

Auth: if CARMON_API_TOKEN is configured (see carmon.config.get_secret), every
/api/* route except /api/health requires `Authorization: Bearer <token>`. If it
is unset, the API is open -- this is meant to run on localhost / a trusted LAN.
"""

from __future__ import annotations

import html
import http.server
import json
import os
import socketserver
import sys
import traceback
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlsplit

import carmon
from . import db
from . import demo
from . import market
from . import quota
from .config import Config, get_secret, load_env
from .nhtsa import recall_lookup_url, vin_recall_url
from .sources import grouped_sources, sources_for_listing

__all__ = ["CarMonHandler", "create_server", "serve"]


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

class ApiError(Exception):
    """Raised by handlers to short-circuit with a JSON error response."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def _parse_int(params: Dict[str, List[str]], name: str) -> Optional[int]:
    values = params.get(name)
    if not values or values[0] == "":
        return None
    try:
        return int(values[0])
    except (TypeError, ValueError):
        raise ApiError(400, f"invalid integer for '{name}': {values[0]!r}")


def _parse_float(params: Dict[str, List[str]], name: str) -> Optional[float]:
    values = params.get(name)
    if not values or values[0] == "":
        return None
    try:
        return float(values[0])
    except (TypeError, ValueError):
        raise ApiError(400, f"invalid number for '{name}': {values[0]!r}")


def _parse_str(params: Dict[str, List[str]], name: str) -> Optional[str]:
    values = params.get(name)
    if not values or values[0] == "":
        return None
    return values[0]


def _parse_bool(params: Dict[str, List[str]], name: str, default: bool = False) -> bool:
    values = params.get(name)
    if not values or values[0] == "":
        return default
    return values[0].strip().lower() in ("1", "true", "yes", "on")


def _since_date(days: int) -> str:
    return (date.today() - timedelta(days=max(0, days))).isoformat()


def _score_class(score: Optional[float]) -> str:
    if score is None:
        return "neutral"
    if score >= 2:
        return "good"
    if score >= 0:
        return "mid"
    return "bad"


def _fmt_money(value: Any) -> str:
    if value is None:
        return "-"
    try:
        return f"${int(value):,}"
    except (TypeError, ValueError):
        return html.escape(str(value))


def _fmt_num(value: Any) -> str:
    if value is None:
        return "-"
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return html.escape(str(value))


def _e(value: Any) -> str:
    """Escape any value for HTML text context."""
    if value is None:
        return ""
    return html.escape(str(value))


def _fmt_mpg(value: Any) -> str:
    if value is None:
        return "—"
    try:
        return f"{float(value):.1f}"
    except (TypeError, ValueError):
        return "—"


def _demo_tag(item: Dict[str, Any]) -> str:
    if item.get("source") != "demo":
        return ""
    return ' <span class="badge demo" title="Demo data seeded for browsing -- not a real listing">DEMO</span>'


# Order here drives both the dashboard <select> and the sort caption below it. Keys must
# match db.SORTABLE exactly (see carmon/db.py) -- that dict is the single source of truth
# for what sort= actually does; this just adds a human label for each key.
_SORT_LABELS = {
    "score": "Score (best first)",
    "price": "Price (low → high)",
    "price_desc": "Price (high → low)",
    "mileage": "Mileage (lowest first)",
    "distance": "Distance (nearest first)",
    "year": "Year (newest first)",
    "first_seen": "First seen (newest first)",
    "last_seen": "Last seen (newest first)",
}

_SORT_CAPTIONS = {
    "score": "Sorted by score, best first (ties broken by lower price)",
    "price": "Sorted by price, low to high",
    "price_desc": "Sorted by price, high to low",
    "mileage": "Sorted by mileage, lowest first",
    "distance": "Sorted by distance, nearest first",
    "year": "Sorted by year, newest first",
    "first_seen": "Sorted by first seen, newest first",
    "last_seen": "Sorted by last seen, newest first",
}


def _sort_caption(requested: Optional[str]) -> str:
    """Human sentence describing the active sort -- falls back to score for an
    unrecognised sort= value and says so, rather than echoing the bad input."""
    key = requested if requested in db.SORTABLE else "score"
    caption = _SORT_CAPTIONS[key]
    if requested and requested not in db.SORTABLE:
        caption += f" (unrecognised sort '{requested}', showing the default instead)"
    return caption


# -- quota pace tile -------------------------------------------------------
# Pace bands map onto the two "good" colors already used for score badges, plus a new
# amber-for-on-pace and a distinct orange/red pair for the two overrun bands, so the tile
# reads at a glance without introducing an unrelated palette.
_PACE_CLASSES = {
    "well under pace": "pace-good",
    "under pace": "pace-good",
    "on pace": "pace-mid",
    "running hot": "pace-hot",
    "far ahead of pace": "pace-bad",
}


def _pace_tile(metrics: Dict[str, Any]) -> str:
    cls = _PACE_CLASSES.get(metrics.get("pace_label"), "")
    summary = quota.summary_line(metrics)
    expected = metrics.get("expected_by_now")
    expected_str = f"{expected:.0f}" if isinstance(expected, (int, float)) else "-"
    return f"""<div class="tile pace {cls}" title="{_e(summary)}">
  <div class="label">API pace {_e(metrics.get('pace_icon'))}</div>
  <div class="value">{_e(metrics.get('used'))}/{_e(metrics.get('cap'))}</div>
  <div class="pace-sub">{_e(metrics.get('pace_label'))} &middot; expected ~{expected_str} by now</div>
  <code class="pace-bar">{_e(quota.bar(metrics))}</code>
</div>"""


# Shown wherever NHTSA complaint counts appear prominently -- they are raw counts, not
# adjusted for how many of a given model are on the road, so a high-volume model naturally
# racks up more of them. The components that keep recurring are the more useful signal.
_NHTSA_VOLUME_CAVEAT = (
    "Raw NHTSA complaint counts are not adjusted for sales volume, so a high-volume model "
    "naturally accumulates more of them — treat the recurring components as the stronger signal."
)

# --------------------------------------------------------------------------
# market appraisals -- shared between /api/appraise, /api/deals, /market,
# /appraise and the listing detail page's "Versus the market" section.
# --------------------------------------------------------------------------

# Grade badges reuse the same good/mid/bad palette as score badges so they read
# consistently in both themes without a new color system.
_GRADE_CLASSES = {
    "great deal": "good",
    "good deal": "good",
    "fair price": "mid",
    "above market": "bad",
    "well above market": "bad",
}

# The single caveat every appraisal-bearing page must carry: this is a listings-price
# comparison, not a valuation of the specific car in front of you.
_CONDITION_BLIND_NOTE = (
    "This compares asking price against other listings' mileage and model year only -- it "
    "is not an appraisal of this car's condition, and is blind to trim, options, accident "
    "history and title status."
)


def _grade_class(grade: Optional[str]) -> str:
    return _GRADE_CLASSES.get(grade, "neutral")


def _grade_badge(appraisal: Dict[str, Any]) -> str:
    grade = appraisal.get("grade")
    if not grade:
        return '<span class="badge neutral">—</span>'
    icon = appraisal.get("grade_icon") or ""
    return f'<span class="badge {_grade_class(grade)}">{_e(icon)} {_e(grade)}</span>'


def _basis_warning(appraisal: Dict[str, Any]) -> str:
    """Visible warning whenever the comparables are not actually the same model."""
    if appraisal.get("basis_level") in ("make", "all"):
        return (
            f'<p class="note">⚠️ Comparing against {_e(appraisal.get("basis"))} -- not the '
            "same model, so read this as a rough bearing rather than a grade.</p>"
        )
    return ""


def _appraisal_block(appraisal: Optional[Dict[str, Any]]) -> str:
    """Full appraisal detail: grade, sample/confidence, comparables, and every caveat note
    visible (never hidden) -- used on the /appraise page and the listing detail page, each
    of which shows exactly one appraisal, so the condition-blind note appears once."""
    if not appraisal:
        return '<div class="empty">Not enough comparable data stored yet for a market read.</div>'
    delta, delta_pct = appraisal.get("delta"), appraisal.get("delta_pct")
    delta_str = f"{delta:+,.0f} ({delta_pct:+.1f}%)" if delta is not None and delta_pct is not None else "—"
    percentile = appraisal.get("percentile")
    percentile_str = f"Cheaper than {100 - percentile:.0f}% of comparables" if percentile is not None else "—"
    comp_range = appraisal.get("comparable_range")
    range_str = f"{_fmt_money(comp_range[0])} – {_fmt_money(comp_range[1])}" if comp_range else "—"
    per_mile = appraisal.get("dollars_per_1k_miles")
    per_mile_str = f"${per_mile:,.0f}" if per_mile is not None else "—"
    kv_rows = [
        ("Grade", _grade_badge(appraisal)),
        ("Expected price", _fmt_money(appraisal.get("expected_price"))),
        ("Actual price", _fmt_money(appraisal.get("actual_price"))),
        ("Delta", delta_str),
        ("Percentile", percentile_str),
        ("Comparable median", _fmt_money(appraisal.get("comparable_median"))),
        ("Comparable range", range_str),
        ("$ / 1,000 miles", per_mile_str),
        ("Sample size / confidence", f"{_e(appraisal.get('sample_size'))} listings &middot; {_e(appraisal.get('confidence'))} confidence"),
        ("Basis", _e(appraisal.get("basis"))),
        ("Method", _e(appraisal.get("method"))),
    ]
    kv_html = "".join(f"<tr><td>{_e(label)}</td><td>{value}</td></tr>" for label, value in kv_rows)
    notes_html = "".join(f'<p class="note">{_e(n)}</p>' for n in appraisal.get("notes") or [])
    return f"""<p class="note">{_e(_CONDITION_BLIND_NOTE)}</p>
{_basis_warning(appraisal)}
<table class="kv">{kv_html}</table>
{notes_html}"""


def _mileage_bucket(mileage: Any) -> Optional[int]:
    try:
        return int(mileage) // 5000
    except (TypeError, ValueError):
        return None


def _row_appraisal(
    conn: Any, config: Any, cache: Dict[Tuple[Any, Any, Any, Optional[int]], Any], item: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Compact per-row market read for the dashboard's 'vs market' column.

    Appraising every row on a 200-row page would refit the comparables regression 200
    times over. The price-independent part of an estimate (expected price, sample size,
    confidence, basis) only depends on make/model/year and roughly how many miles are on
    the car, so it is cached per request keyed on a 5,000-mile bucket; each row's own price
    is then used only to compute that row's own delta and grade against the shared estimate.
    """
    make, model, year, mileage = item.get("make"), item.get("model"), item.get("year"), item.get("mileage")
    price = item.get("price_current")
    if not make or not model or mileage is None or not price:
        return None
    key = (make, model, year, _mileage_bucket(mileage))
    if key not in cache:
        cache[key] = market.appraise(conn, {"make": make, "model": model, "year": year, "mileage": mileage}, config)
    base = cache[key]
    if base.expected_price is None:
        return None
    delta_pct = 100.0 * (float(price) - base.expected_price) / base.expected_price
    grade, icon = next((label, ic) for threshold, label, ic in market.DEAL_BANDS if delta_pct <= threshold)
    return {
        "delta_pct": delta_pct,
        "grade": grade,
        "grade_icon": icon,
        "sample_size": base.sample_size,
        "confidence": base.confidence,
        "basis_level": base.basis_level,
    }


def _vs_market_cell(conn: Any, config: Any, cache: Dict[Any, Any], item: Dict[str, Any]) -> str:
    appraisal = _row_appraisal(conn, config, cache, item)
    if appraisal is None:
        return "<td>—</td>"
    cls = _grade_class(appraisal["grade"])
    sign = f"{appraisal['delta_pct']:+.1f}%"
    warn = ""
    if appraisal["basis_level"] in ("make", "all"):
        warn = (
            ' <span title="Comparing against a different model -- thin comparable data" '
            'aria-label="different-model comparison">⚠️</span>'
        )
    return (
        "<td>"
        f'<span class="badge {cls}" title="{_e(appraisal["grade"])}">{sign}</span>{warn}'
        f'<div class="mv-sample">n={_e(appraisal["sample_size"])} &middot; {_e(appraisal["confidence"])}</div>'
        "</td>"
    )


def _trend_chart_svg(trend: List[Dict[str, Any]]) -> str:
    """Inline SVG line chart of median price by month -- no chart library, drawn by hand.

    Colors come from CSS classes tied to the page's --accent/--muted/--border variables
    (see _BASE_CSS), so the chart stays readable in both light and dark themes.
    """
    prices = [t["median_price"] for t in trend if t.get("median_price") is not None]
    if len(prices) < 1:
        return '<div class="empty">No monthly price history yet -- this fills in as the daily job runs.</div>'

    width, height = 640, 220
    pad_left, pad_right, pad_top, pad_bottom = 60, 16, 20, 30
    plot_w, plot_h = width - pad_left - pad_right, height - pad_top - pad_bottom
    lo, hi = min(prices), max(prices)
    if lo == hi:
        lo, hi = lo - 1, hi + 1
    n = len(trend)

    def x_at(i: int) -> float:
        return pad_left if n == 1 else pad_left + plot_w * i / (n - 1)

    def y_at(v: float) -> float:
        return pad_top + plot_h * (1 - (v - lo) / (hi - lo))

    points = [(x_at(i), y_at(t["median_price"])) for i, t in enumerate(trend)]
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)

    dots, labels = [], []
    for t, (x, y) in zip(trend, points):
        tooltip = f"{_e(t['month'])}: {_fmt_money(t['median_price'])} ({_e(t['observations'])} observations)"
        dots.append(f'<circle class="chart-point" cx="{x:.1f}" cy="{y:.1f}" r="3.5"><title>{tooltip}</title></circle>')
        labels.append(
            f'<text class="chart-label" x="{x:.1f}" y="{height - 8:.1f}" text-anchor="middle">{_e(t["month"][5:])}</text>'
        )

    baseline_y = pad_top + plot_h
    axis = f'<line class="chart-axis" x1="{pad_left}" y1="{baseline_y:.1f}" x2="{width - pad_right}" y2="{baseline_y:.1f}" />'
    hi_label = f'<text class="chart-label" x="{pad_left - 8}" y="{pad_top + 4}" text-anchor="end">{_fmt_money(round(hi))}</text>'
    lo_label = f'<text class="chart-label" x="{pad_left - 8}" y="{baseline_y:.1f}" text-anchor="end">{_fmt_money(round(lo))}</text>'
    line = f'<polyline class="chart-line" points="{poly}" fill="none" />' if n > 1 else ""

    return f"""<svg class="trend-chart" viewBox="0 0 {width} {height}" role="img" aria-label="Median listing price by month">
  {axis}
  {line}
  {''.join(dots)}
  {''.join(labels)}
  {hi_label}
  {lo_label}
</svg>"""


def _trend_row(t: Dict[str, Any]) -> str:
    change_pct = t.get("change_pct")
    change_str = f"{change_pct:+.1f}%" if change_pct is not None else "—"
    return (
        "<tr>"
        f"<td>{_e(t['month'])}</td>"
        f"<td>{_e(t['observations'])}</td>"
        f"<td>{_e(t['cars'])}</td>"
        f"<td>{_fmt_money(t['median_price'])}</td>"
        f"<td>{_fmt_money(t['mean_price'])}</td>"
        f"<td>{_fmt_money(t['min_price'])}</td>"
        f"<td>{_fmt_money(t['max_price'])}</td>"
        f"<td>{_fmt_num(t.get('median_mileage'))}</td>"
        f"<td>{change_str}</td>"
        "</tr>"
    )


def _model_row(m: Dict[str, Any]) -> str:
    dom = m.get("days_on_market") or {}
    cuts = m.get("price_cuts") or {}
    median_days = dom.get("median_days")
    cut_share = cuts.get("cut_share_pct")
    r2 = m.get("r_squared")
    per_mile = m.get("dollars_per_1k_miles")
    per_mile_str = f"${per_mile:,.0f}" if per_mile is not None else "—"
    range_str = f"{_fmt_money(m['min_price'])}&ndash;{_fmt_money(m['max_price'])}"
    r2_str = f"{r2:.2f}" if r2 is not None else "—"
    days_str = f"{median_days:.0f}" if median_days is not None else "—"
    cut_str = f"{cut_share:.0f}%" if cut_share is not None else "—"
    return (
        "<tr>"
        f"<td>{_e(m['make'])} {_e(m['model'])}</td>"
        f"<td>{_e(m['sample_size'])}</td>"
        f"<td>{_fmt_money(m['median_price'])}</td>"
        f"<td>{range_str}</td>"
        f"<td>{_fmt_num(m['median_mileage'])}</td>"
        f"<td>{per_mile_str}</td>"
        f"<td>{r2_str}</td>"
        f"<td>{days_str}</td>"
        f"<td>{cut_str}</td>"
        "</tr>"
    )


def _deal_row(item: Dict[str, Any]) -> str:
    appraisal = item.get("appraisal") or {}
    delta, delta_pct = appraisal.get("delta"), appraisal.get("delta_pct")
    delta_str = f"{delta:+,.0f} ({delta_pct:+.1f}%)" if delta is not None and delta_pct is not None else "—"
    warn = ""
    if appraisal.get("basis_level") in ("make", "all"):
        warn = (
            ' <span title="Comparing against a different model -- thin comparable data" '
            'aria-label="different-model comparison">⚠️</span>'
        )
    return (
        "<tr>"
        f"<td>{_listing_link(item)}</td>"
        f"<td>{_fmt_money(item.get('price_current'))}</td>"
        f"<td>{_fmt_money(appraisal.get('expected_price'))}</td>"
        f"<td>{delta_str}</td>"
        f"<td>{_grade_badge(appraisal)}{warn}</td>"
        f"<td>{_e(appraisal.get('sample_size'))} &middot; {_e(appraisal.get('confidence'))}</td>"
        "</tr>"
    )


# --------------------------------------------------------------------------
# page chrome (shared CSS/JS + nav/footer), all inline, no external assets
# --------------------------------------------------------------------------

_BASE_CSS = """
:root {
  --bg: #f5f6f8; --panel: #ffffff; --text: #1a1d23; --muted: #5b6270;
  --border: #dfe3ea; --accent: #2563eb; --good: #16a34a; --good-bg: #dcfce7;
  --mid: #b45309; --mid-bg: #fef3c7; --bad: #dc2626; --bad-bg: #fee2e2;
  --hot: #c2410c; --hot-bg: #ffedd5;
  --input-bg: #ffffff;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #14161a; --panel: #1d2026; --text: #e7e9ee; --muted: #9aa2b1;
    --border: #2c313b; --accent: #60a5fa; --good: #4ade80; --good-bg: #14361f;
    --mid: #fbbf24; --mid-bg: #3a2c0a; --bad: #f87171; --bad-bg: #3a1414;
    --hot: #fb923c; --hot-bg: #431407;
    --input-bg: #12141a;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--text);
  font: 15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
header.site {
  display: flex; flex-wrap: wrap; gap: 1rem; align-items: center;
  padding: 0.9rem 1.25rem; border-bottom: 1px solid var(--border); background: var(--panel);
}
header.site .brand { font-weight: 700; margin-right: auto; }
header.site nav a { margin-right: 1rem; color: var(--text); font-weight: 500; }
header.site nav a:hover { color: var(--accent); }
main { padding: 1.25rem; max-width: 1200px; margin: 0 auto; }
footer.site {
  padding: 1rem 1.25rem; color: var(--muted); font-size: 0.85rem;
  border-top: 1px solid var(--border); margin-top: 2rem;
}
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 0.75rem; margin-bottom: 1.5rem; }
.tile {
  background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
  padding: 0.9rem 1rem;
}
.tile .label { color: var(--muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.03em; }
.tile .value { font-size: 1.6rem; font-weight: 700; margin-top: 0.2rem; }
.tile.pace { border-width: 2px; }
.tile.pace.pace-good { border-color: var(--good); background: var(--good-bg); }
.tile.pace.pace-good .label, .tile.pace.pace-good .value, .tile.pace.pace-good .pace-sub { color: var(--good); }
.tile.pace.pace-mid { border-color: var(--mid); background: var(--mid-bg); }
.tile.pace.pace-mid .label, .tile.pace.pace-mid .value, .tile.pace.pace-mid .pace-sub { color: var(--mid); }
.tile.pace.pace-hot { border-color: var(--hot); background: var(--hot-bg); }
.tile.pace.pace-hot .label, .tile.pace.pace-hot .value, .tile.pace.pace-hot .pace-sub { color: var(--hot); }
.tile.pace.pace-bad { border-color: var(--bad); background: var(--bad-bg); }
.tile.pace.pace-bad .label, .tile.pace.pace-bad .value, .tile.pace.pace-bad .pace-sub { color: var(--bad); }
.tile .pace-sub { font-size: 0.78rem; margin-top: 0.2rem; font-weight: 600; }
.tile code.pace-bar {
  display: block; margin-top: 0.4rem; font-size: 0.85rem; letter-spacing: 0.05em;
  overflow-x: auto; white-space: pre;
}
.sort-caption { color: var(--muted); font-size: 0.85rem; margin: 0 0 0.5rem; }
.demo-banner {
  background: var(--bad-bg); color: var(--bad); border: 2px solid var(--bad);
  border-radius: 8px; padding: 0.75rem 1.1rem; margin: 0.9rem auto 0; max-width: 1200px;
  font-weight: 700; font-size: 0.95rem;
}
.badge.demo { background: var(--bad-bg); color: var(--bad); font-size: 0.7rem; padding: 0.1rem 0.4rem; }
form.filters {
  display: flex; flex-wrap: wrap; gap: 0.6rem; align-items: end;
  background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
  padding: 1rem; margin-bottom: 1.25rem;
}
form.filters .field { display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.8rem; color: var(--muted); }
form.filters input[type=text], form.filters input[type=number], form.filters select {
  background: var(--input-bg); color: var(--text); border: 1px solid var(--border);
  border-radius: 6px; padding: 0.4rem 0.5rem; font-size: 0.9rem;
}
form.filters label.checkbox { flex-direction: row; align-items: center; gap: 0.4rem; }
form.filters button {
  background: var(--accent); color: #fff; border: none; border-radius: 6px;
  padding: 0.5rem 1rem; font-weight: 600; cursor: pointer;
}
table { width: 100%; border-collapse: collapse; background: var(--panel); }
.table-wrap { overflow-x: auto; border: 1px solid var(--border); border-radius: 10px; }
th, td { text-align: left; padding: 0.55rem 0.7rem; border-bottom: 1px solid var(--border); white-space: nowrap; }
th { color: var(--muted); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.03em; }
tr:last-child td { border-bottom: none; }
.badge {
  display: inline-block; min-width: 2.2em; text-align: center; padding: 0.15rem 0.5rem;
  border-radius: 999px; font-weight: 700; font-size: 0.85rem;
}
.badge.good { background: var(--good-bg); color: var(--good); }
.badge.mid { background: var(--mid-bg); color: var(--mid); }
.badge.bad { background: var(--bad-bg); color: var(--bad); }
.badge.neutral { background: var(--border); color: var(--muted); }
.section { margin-bottom: 1.75rem; }
.section h2 { font-size: 1.05rem; margin: 0 0 0.6rem; }
pre.digest {
  background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
  padding: 1rem; white-space: pre-wrap; word-wrap: break-word; overflow-x: auto;
}
.cat { background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 1rem; margin-bottom: 1rem; }
.cat h3 { margin: 0 0 0.25rem; }
.cat p.desc { color: var(--muted); margin: 0 0 0.6rem; }
.cat ul { margin: 0; padding-left: 1.1rem; }
.cat li { margin-bottom: 0.35rem; }
.note {
  background: var(--mid-bg); color: var(--mid); border-radius: 8px; padding: 0.6rem 0.9rem;
  margin-bottom: 1rem; font-size: 0.9rem;
}
.empty { color: var(--muted); padding: 1rem; }
.kv { border-collapse: collapse; }
.kv td { padding: 0.35rem 0.6rem; }
.kv td:first-child { color: var(--muted); width: 12rem; }
.mv-sample { color: var(--muted); font-size: 0.75rem; margin-top: 0.15rem; white-space: nowrap; }
.trend-chart { width: 100%; max-width: 700px; height: auto; margin-bottom: 0.75rem; }
.trend-chart .chart-axis { stroke: var(--border); stroke-width: 1; }
.trend-chart .chart-line { stroke: var(--accent); stroke-width: 2; }
.trend-chart .chart-point { fill: var(--accent); }
.trend-chart .chart-label { fill: var(--muted); font-size: 10px; }
"""

_NAV_LINKS = [
    ("/", "Dashboard"),
    ("/market", "Market"),
    ("/appraise", "Appraise"),
    ("/sources", "Sources"),
    ("/digest", "Digest"),
    ("/api/health", "API health"),
]


def _page(title: str, body: str, last_run: Optional[str] = None, demo_warning: Optional[str] = None) -> str:
    nav = "".join(f'<a href="{href}">{_e(label)}</a>' for href, label in _NAV_LINKS)
    footer_bits = "Data source: MarketCheck Inventory Search API (manual cross-shop links only, no scraping)."
    if last_run:
        footer_bits += f" Last run: {_e(last_run)}."
    banner_html = f'<div class="demo-banner">⚠️ {_e(demo_warning)}</div>' if demo_warning else ""
    return f"""<title>{_e(title)}</title>
<style>{_BASE_CSS}</style>
<header class="site">
  <div class="brand">Used Car Monitor</div>
  <nav>{nav}</nav>
</header>
{banner_html}
<main>
{body}
</main>
<footer class="site">{footer_bits}</footer>
"""


def _listing_link(listing: Dict[str, Any]) -> str:
    label = " ".join(
        str(part) for part in (listing.get("year"), listing.get("make"), listing.get("model"), listing.get("trim"))
        if part
    ).strip() or listing.get("vin", "")
    return f'<a href="/listing/{_e(listing.get("vin"))}">{_e(label)}</a>'


def _nhtsa_cell(conn: Any, item: Dict[str, Any], cache: Dict[Tuple[Any, Any, Any], Optional[Dict[str, Any]]]) -> str:
    """Compact 'complaints / recalls' cell for a listing's model-year, from cached data only."""
    make, model, year = item.get("make"), item.get("model"), item.get("year")
    key = (make, model, year)
    if key not in cache:
        cache[key] = db.get_reliability(conn, make, model, year) if make and model and year else None
    facts = cache[key]
    if not facts:
        return "—"
    complaints, recalls = facts.get("complaint_count"), facts.get("recall_count")
    if complaints is None and recalls is None:
        return "—"
    complaints_str = complaints if complaints is not None else "-"
    recalls_str = recalls if recalls is not None else "-"
    return f"{complaints_str} / {recalls_str}"


def _results_table(conn: Any, listings: List[Dict[str, Any]], config: Optional[Any] = None) -> str:
    if not listings:
        return '<div class="empty">No listings match those filters.</div>'
    reliability_cache: Dict[Tuple[Any, Any, Any], Optional[Dict[str, Any]]] = {}
    market_cache: Dict[Any, Any] = {}
    rows = []
    for item in listings:
        rows.append(
            "<tr>"
            f'<td><span class="badge {_score_class(item.get("score"))}">{_e(item.get("score") if item.get("score") is not None else "-")}</span></td>'
            f"<td>{_listing_link(item)}{_demo_tag(item)}</td>"
            f'<td>{_fmt_money(item.get("price_current"))}</td>'
            f'<td>{_fmt_num(item.get("mileage"))}</td>'
            f'<td>{_fmt_mpg(item.get("combined_mpg"))}</td>'
            f'<td title="NHTSA complaints / recalls for this model year">{_e(_nhtsa_cell(conn, item, reliability_cache))}</td>'
            f'<td>{_e(item.get("distance_miles") if item.get("distance_miles") is not None else "-")}</td>'
            f'<td>{"Yes" if item.get("cpo") else "No"}</td>'
            f'<td>{_e(item.get("dealer_name") or "-")} &middot; {_e(item.get("dealer_city") or "-")}</td>'
            f'<td>{_e(item.get("first_seen") or "-")}</td>'
            f"{_vs_market_cell(conn, config, market_cache, item)}"
            "</tr>"
        )
    return f"""<div class="table-wrap"><table>
<thead><tr>
  <th>Score</th><th>Vehicle</th><th>Price</th><th>Mileage</th><th>MPG</th><th>NHTSA</th><th>Dist.</th><th>CPO</th><th>Dealer</th><th>First seen</th><th>Vs market</th>
</tr></thead>
<tbody>{''.join(rows)}</tbody>
</table></div>"""


# --------------------------------------------------------------------------
# request handler
# --------------------------------------------------------------------------

class CarMonHandler(http.server.BaseHTTPRequestHandler):
    server_version = f"CarMon/{carmon.__version__}"

    # Populated by create_server() via a partial subclass / instance attrs on the server.
    config: Config = None  # type: ignore[assignment]

    # -- logging ------------------------------------------------------
    def log_message(self, fmt: str, *args: Any) -> None:
        if os.environ.get("CARMON_HTTP_LOG"):
            super().log_message(fmt, *args)

    # -- dispatch -------------------------------------------------------
    def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
        self._dispatch("GET")

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self._cors_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _dispatch(self, method: str) -> None:
        parsed = urlsplit(self.path)
        path = parsed.path.rstrip("/") or "/"
        params = parse_qs(parsed.query)
        is_api = path == "/api" or path.startswith("/api/")

        if is_api:
            token = get_secret("CARMON_API_TOKEN", env=self._env())
            if path != "/api/health" and token:
                header = self.headers.get("Authorization", "")
                if header != f"Bearer {token}":
                    self._send_json({"error": "unauthorized"}, status=401)
                    return

        conn = None
        try:
            conn = db.connect(self.config.db_path)
            demo.maybe_expire(conn, self.config)
            handler = self._route(path, is_api)
            if handler is None:
                if is_api:
                    self._send_json({"error": "not found"}, status=404)
                else:
                    self._send_html(_page("Not found", '<div class="empty">404 - page not found.</div>'), status=404)
                return
            handler(conn, params)
        except ApiError as exc:
            self._send_json({"error": exc.message}, status=exc.status)
        except Exception as exc:  # pragma: no cover - defensive
            if os.environ.get("CARMON_HTTP_LOG"):
                traceback.print_exc(file=sys.stderr)
            if is_api:
                self._send_json({"error": f"internal error: {exc}"}, status=500)
            else:
                self._send_html(
                    _page("Error", f'<div class="empty">Internal error: {_e(exc)}</div>'), status=500
                )
        finally:
            if conn is not None:
                conn.close()

    def _env(self) -> Dict[str, str]:
        return load_env()

    def _route(self, path: str, is_api: bool) -> Optional[Callable[[Any, Dict[str, List[str]]], None]]:
        if path == "/api/health":
            return self._api_health
        if path == "/api/stats":
            return self._api_stats
        if path == "/api/quota":
            return self._api_quota
        if path == "/api/listings":
            return self._api_listings
        if path == "/api/new":
            return self._api_new
        if path == "/api/price-drops":
            return self._api_price_drops
        if path == "/api/top":
            return self._api_top
        if path == "/api/digest/latest":
            return self._api_digest_latest
        if path == "/api/sources":
            return self._api_sources
        if path == "/api/config":
            return self._api_config
        if path == "/api/runs":
            return self._api_runs
        if path == "/api/market":
            return self._api_market
        if path == "/api/market/trend":
            return self._api_market_trend
        if path == "/api/appraise":
            return self._api_appraise
        if path == "/api/deals":
            return self._api_deals
        if path == "/api/reliability":
            return self._api_reliability_list
        if path.startswith("/api/reliability/"):
            rest = path[len("/api/reliability/"):]
            parts = [p for p in rest.split("/")]
            if len(parts) == 3 and all(parts):
                make, model, year = parts
                return lambda conn, params: self._api_reliability_detail(conn, params, make, model, year)
            return None
        if path.startswith("/api/listings/"):
            rest = path[len("/api/listings/"):]
            if rest.endswith("/history"):
                vin = rest[: -len("/history")]
                return lambda conn, params: self._api_listing_history(conn, params, vin)
            if rest:
                return lambda conn, params: self._api_listing_detail(conn, params, rest)
            return None
        if not is_api:
            if path == "/":
                return self._page_dashboard
            if path == "/sources":
                return self._page_sources
            if path == "/digest":
                return self._page_digest
            if path == "/market":
                return self._page_market
            if path == "/appraise":
                return self._page_appraise
            if path.startswith("/listing/"):
                vin = path[len("/listing/"):]
                if vin:
                    return lambda conn, params: self._page_listing_detail(conn, params, vin)
        return None

    # -- response helpers -------------------------------------------------
    def _cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")

    def _send_json(self, payload: Any, status: int = 200) -> None:
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors_headers()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, body_html: str, status: int = 200) -> None:
        body = body_html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _last_run_str(self, conn: Any) -> Optional[str]:
        runs = db.recent_runs(conn, limit=1)
        if runs:
            return runs[0].get("finished_at") or runs[0].get("started_at")
        return None

    # -- filter parsing shared by /api/listings and the dashboard --------
    def _search_kwargs(self, params: Dict[str, List[str]]) -> Dict[str, Any]:
        cpo_raw = params.get("cpo")
        return {
            "make": _parse_str(params, "make"),
            "model": _parse_str(params, "model"),
            "max_price": _parse_int(params, "max_price"),
            "min_price": _parse_int(params, "min_price"),
            "max_mileage": _parse_int(params, "max_mileage"),
            "min_year": _parse_int(params, "min_year"),
            "max_distance": _parse_float(params, "max_distance"),
            "min_score": _parse_float(params, "min_score"),
            "cpo_only": _parse_bool(params, "cpo") if cpo_raw else False,
            "active_only": _parse_bool(params, "active", default=True),
            "new_since": _parse_str(params, "new_since"),
            "query": _parse_str(params, "q"),
            "sort": _parse_str(params, "sort") or "score",
        }

    # -- JSON API handlers -------------------------------------------------
    def _api_health(self, conn: Any, params: Dict[str, List[str]]) -> None:
        self._send_json({
            "status": "ok",
            "version": carmon.__version__,
            "listings": db.count_listings(conn, active_only=True),
            "demo_listings": demo.demo_count(conn),
            "demo_warning": demo.demo_banner(conn),
        })

    def _api_stats(self, conn: Any, params: Dict[str, List[str]]) -> None:
        cap = int(self.config.api.get("monthly_call_cap", 500) or 500)
        data = db.stats(conn, monthly_cap=cap)
        data["pace"] = quota.pace_from_db(conn, cap)
        data["demo_listings"] = demo.demo_count(conn)
        data["demo_warning"] = demo.demo_banner(conn)
        self._send_json(data)

    def _api_quota(self, conn: Any, params: Dict[str, List[str]]) -> None:
        cap = int(self.config.api.get("monthly_call_cap", 500) or 500)
        metrics = quota.pace_from_db(conn, cap)
        payload = dict(metrics)
        payload["summary"] = quota.summary_line(metrics)
        payload["bar"] = quota.bar(metrics)
        self._send_json(payload)

    def _api_listings(self, conn: Any, params: Dict[str, List[str]]) -> None:
        kwargs = self._search_kwargs(params)
        limit = _parse_int(params, "limit")
        offset = _parse_int(params, "offset") or 0
        limit = 50 if limit is None else max(1, min(limit, 500))
        max_complaints = _parse_int(params, "max_complaints")
        max_recalls = _parse_int(params, "max_recalls")
        results = db.search_listings(conn, limit=limit, offset=offset, **kwargs)
        if max_complaints is not None or max_recalls is not None:
            results = self._filter_by_nhtsa(conn, results, max_complaints, max_recalls)
        filters = {k: v for k, v in kwargs.items() if v not in (None, False)}
        if max_complaints is not None:
            filters["max_complaints"] = max_complaints
        if max_recalls is not None:
            filters["max_recalls"] = max_recalls
        self._send_json({
            "count": len(results),
            "limit": limit,
            "offset": offset,
            "filters": filters,
            "listings": results,
        })

    def _filter_by_nhtsa(
        self,
        conn: Any,
        listings: List[Dict[str, Any]],
        max_complaints: Optional[int],
        max_recalls: Optional[int],
    ) -> List[Dict[str, Any]]:
        """Drop listings whose cached NHTSA counts exceed the caps. Unknown (uncached) counts
        are never dropped -- absence of data is not evidence of a problem."""
        cache: Dict[Tuple[Any, Any, Any], Optional[Dict[str, Any]]] = {}
        kept = []
        for item in listings:
            make, model, year = item.get("make"), item.get("model"), item.get("year")
            key = (make, model, year)
            if key not in cache:
                cache[key] = db.get_reliability(conn, make, model, year) if make and model and year else None
            facts = cache[key]
            if facts:
                complaints, recalls = facts.get("complaint_count"), facts.get("recall_count")
                if max_complaints is not None and complaints is not None and complaints > max_complaints:
                    continue
                if max_recalls is not None and recalls is not None and recalls > max_recalls:
                    continue
            kept.append(item)
        return kept

    def _api_listing_detail(self, conn: Any, params: Dict[str, List[str]], vin: str) -> None:
        listing = db.get_listing(conn, vin)
        if listing is None:
            self._send_json({"error": f"unknown vin: {vin}"}, status=404)
            return
        listing = dict(listing)
        listing["price_history"] = db.get_price_history(conn, vin)
        listing["cross_shop"] = sources_for_listing(listing, self.config.search)
        try:
            from . import pipeline
        except ImportError:
            pipeline = None  # type: ignore[assignment]
        if pipeline is not None:
            listing = pipeline.attach_cached_enrichment(conn, listing)
        listing["nhtsa_vin_url"] = vin_recall_url(vin)
        make, model, year = listing.get("make"), listing.get("model"), listing.get("year")
        if make and model and year:
            listing["nhtsa_model_url"] = recall_lookup_url(make, model, year)
        appraisal = market.appraise_vin(conn, vin, self.config)
        listing["appraisal"] = appraisal.as_dict() if appraisal else None
        self._send_json(listing)

    def _api_reliability_detail(
        self, conn: Any, params: Dict[str, List[str]], make: str, model: str, year: str
    ) -> None:
        from urllib.parse import unquote

        make, model = unquote(make), unquote(model)
        try:
            year_int = int(unquote(year))
        except ValueError:
            raise ApiError(400, f"invalid year: {year!r}")
        record = db.get_reliability(conn, make, model, year_int)
        if record is None:
            self._send_json(
                {
                    "error": (
                        f"no cached NHTSA reliability data for {year_int} {make} {model}; "
                        "run `python3 -m carmon enrich` to fetch it"
                    )
                },
                status=404,
            )
            return
        record = dict(record)
        record["nhtsa_url"] = recall_lookup_url(make, model, year_int)
        self._send_json(record)

    def _api_reliability_list(self, conn: Any, params: Dict[str, List[str]]) -> None:
        rows = conn.execute("SELECT * FROM model_reliability ORDER BY complaint_count DESC").fetchall()
        models = []
        for row in rows:
            data = dict(row)
            for field in ("top_components", "recalls"):
                if isinstance(data.get(field), str) and data[field]:
                    try:
                        data[field] = json.loads(data[field])
                    except json.JSONDecodeError:
                        data[field] = None
            models.append(data)
        self._send_json({"count": len(models), "models": models})

    def _api_listing_history(self, conn: Any, params: Dict[str, List[str]], vin: str) -> None:
        listing = db.get_listing(conn, vin)
        if listing is None:
            self._send_json({"error": f"unknown vin: {vin}"}, status=404)
            return
        self._send_json({"vin": vin, "history": db.get_price_history(conn, vin)})

    def _api_new(self, conn: Any, params: Dict[str, List[str]]) -> None:
        days = _parse_int(params, "days") or 1
        limit = _parse_int(params, "limit") or 25
        limit = max(1, min(limit, 500))
        listings = db.new_listings_since(conn, _since_date(days), limit=limit)
        self._send_json({"count": len(listings), "days": days, "since": _since_date(days), "listings": listings})

    def _api_price_drops(self, conn: Any, params: Dict[str, List[str]]) -> None:
        days = _parse_int(params, "days") or 1
        limit = _parse_int(params, "limit") or 25
        limit = max(1, min(limit, 500))
        listings = db.price_drops_since(conn, _since_date(days), limit=limit)
        self._send_json({"count": len(listings), "days": days, "since": _since_date(days), "listings": listings})

    def _api_top(self, conn: Any, params: Dict[str, List[str]]) -> None:
        limit = _parse_int(params, "limit") or 5
        limit = max(1, min(limit, 500))
        listings = db.search_listings(conn, sort="score", limit=limit)
        self._send_json({"count": len(listings), "listings": listings})

    def _api_digest_latest(self, conn: Any, params: Dict[str, List[str]]) -> None:
        path, markdown = self._latest_digest()
        self._send_json({"path": str(path) if path else None, "markdown": markdown})

    def _api_sources(self, conn: Any, params: Dict[str, List[str]]) -> None:
        self._send_json({"categories": grouped_sources(self.config.search)})

    def _api_config(self, conn: Any, params: Dict[str, List[str]]) -> None:
        self._send_json(self.config.to_dict())

    def _api_runs(self, conn: Any, params: Dict[str, List[str]]) -> None:
        limit = _parse_int(params, "limit") or 10
        limit = max(1, min(limit, 500))
        runs = db.recent_runs(conn, limit=limit)
        self._send_json({"count": len(runs), "runs": runs})

    def _api_market(self, conn: Any, params: Dict[str, List[str]]) -> None:
        months = _parse_int(params, "months") or 6
        months = max(1, min(months, 36))
        self._send_json(market.market_report(conn, months=months, config=self.config))

    def _api_market_trend(self, conn: Any, params: Dict[str, List[str]]) -> None:
        make = _parse_str(params, "make")
        model = _parse_str(params, "model")
        months = _parse_int(params, "months") or 6
        months = max(1, min(months, 36))
        self._send_json({
            "make": make,
            "model": model,
            "trend": market.price_trend(conn, make=make, model=model, months=months),
        })

    def _api_appraise(self, conn: Any, params: Dict[str, List[str]]) -> None:
        car = {
            "make": _parse_str(params, "make"),
            "model": _parse_str(params, "model"),
            "year": _parse_int(params, "year"),
            "mileage": _parse_int(params, "mileage"),
            "price_current": _parse_int(params, "price"),
        }
        result = market.appraise(conn, car, self.config)
        self._send_json(result.as_dict())

    def _api_deals(self, conn: Any, params: Dict[str, List[str]]) -> None:
        limit = _parse_int(params, "limit") or 10
        limit = max(1, min(limit, 200))
        deals = market.best_deals(conn, limit=limit, config=self.config)
        self._send_json({"count": len(deals), "deals": deals})

    def _latest_digest(self) -> Tuple[Optional[Path], Optional[str]]:
        try:
            from . import digest as digest_module
        except ImportError:
            return None, None
        latest_fn = getattr(digest_module, "latest_digest_path", None)
        if latest_fn is None:
            return None, None
        path = latest_fn(self.config)
        if not path:
            return None, None
        path = Path(path)
        try:
            return path, path.read_text(encoding="utf-8")
        except OSError:
            return path, None

    # -- HTML pages ---------------------------------------------------------
    def _page_dashboard(self, conn: Any, params: Dict[str, List[str]]) -> None:
        cap = int(self.config.api.get("monthly_call_cap", 500) or 500)
        stats = db.stats(conn, monthly_cap=cap)
        new_today = len(db.new_listings_since(conn, _since_date(0), limit=500))
        drops_today = len(db.price_drops_since(conn, _since_date(0), limit=500))
        nhtsa_model_years = conn.execute("SELECT COUNT(*) AS n FROM model_reliability").fetchone()["n"]

        kwargs = self._search_kwargs(params)
        sort = kwargs.get("sort") or "score"
        resolved_sort = sort if sort in db.SORTABLE else "score"
        try:
            listings = db.search_listings(conn, limit=200, offset=0, **kwargs)
        except Exception:
            listings = []

        pace_metrics = quota.pace_from_db(conn, cap)

        tiles = f"""
<div class="tiles">
  <div class="tile"><div class="label">Active listings</div><div class="value">{_e(stats['listings_active'])}</div></div>
  <div class="tile"><div class="label">New today</div><div class="value">{_e(new_today)}</div></div>
  <div class="tile"><div class="label">Price drops today</div><div class="value">{_e(drops_today)}</div></div>
  {_pace_tile(pace_metrics)}
  <div class="tile"><div class="label">Best score</div><div class="value">{_e(stats['best_score'] if stats['best_score'] is not None else '-')}</div></div>
  <div class="tile"><div class="label">Model-years with NHTSA data</div><div class="value">{_e(nhtsa_model_years)}</div></div>
</div>"""

        def sel(value: str) -> str:
            return " selected" if resolved_sort == value else ""

        q = _e(_parse_str(params, "q") or "")
        make = _e(_parse_str(params, "make") or "")
        max_price = _e(_parse_str(params, "max_price") or "")
        max_mileage = _e(_parse_str(params, "max_mileage") or "")
        min_score = _e(_parse_str(params, "min_score") or "")
        cpo_checked = " checked" if _parse_bool(params, "cpo") else ""

        form = f"""
<form class="filters" method="get" action="/">
  <div class="field"><label for="q">Search</label><input type="text" id="q" name="q" value="{q}" placeholder="make, model, dealer, VIN"></div>
  <div class="field"><label for="make">Make</label><input type="text" id="make" name="make" value="{make}"></div>
  <div class="field"><label for="max_price">Max price</label><input type="number" id="max_price" name="max_price" value="{max_price}"></div>
  <div class="field"><label for="max_mileage">Max mileage</label><input type="number" id="max_mileage" name="max_mileage" value="{max_mileage}"></div>
  <div class="field"><label for="min_score">Min score</label><input type="number" step="0.1" id="min_score" name="min_score" value="{min_score}"></div>
  <div class="field"><label for="sort">Sort</label>
    <select id="sort" name="sort">
      {"".join(f'<option value="{key}"{sel(key)}>{_e(label)}</option>' for key, label in _SORT_LABELS.items())}
    </select>
  </div>
  <div class="field checkbox"><label class="checkbox"><input type="checkbox" name="cpo" value="1"{cpo_checked}> CPO only</label></div>
  <button type="submit">Filter</button>
</form>"""

        sort_caption = f'<p class="sort-caption">{_e(_sort_caption(sort))}</p>'
        body = tiles + form + f'<div class="section">{sort_caption}{_results_table(conn, listings, self.config)}</div>'
        self._send_html(_page("Dashboard", body, self._last_run_str(conn), demo_warning=demo.demo_banner(conn)))

    def _page_listing_detail(self, conn: Any, params: Dict[str, List[str]], vin: str) -> None:
        listing = db.get_listing(conn, vin)
        if listing is None:
            self._send_html(
                _page("Listing not found", f'<div class="empty">No listing found for VIN {_e(vin)}.</div>'),
                status=404,
            )
            return
        history = db.get_price_history(conn, vin)
        cross_shop = sources_for_listing(listing, self.config.search)

        make, model, year = listing.get("make"), listing.get("model"), listing.get("year")

        city_mpg, highway_mpg, combined_mpg = (
            listing.get("city_mpg"), listing.get("highway_mpg"), listing.get("combined_mpg"),
        )
        if combined_mpg is None and make and model and year:
            cached_mpg = db.get_mpg(conn, make, model, year)
            if cached_mpg:
                city_mpg = city_mpg if city_mpg is not None else cached_mpg.get("city_mpg")
                highway_mpg = highway_mpg if highway_mpg is not None else cached_mpg.get("highway_mpg")
                combined_mpg = cached_mpg.get("combined_mpg")

        title = " ".join(
            str(part) for part in (listing.get("year"), listing.get("make"), listing.get("model"), listing.get("trim"))
            if part
        ) or vin

        fields = [
            ("VIN", listing.get("vin")),
            ("Year / Make / Model / Trim", " / ".join(str(x) for x in (
                listing.get("year"), listing.get("make"), listing.get("model"), listing.get("trim")) if x)),
            ("Body / Fuel", f"{listing.get('body_type') or '-'} / {listing.get('fuel_type') or '-'}"),
            ("MPG (city / hwy / combined)", f"{_fmt_mpg(city_mpg)} / {_fmt_mpg(highway_mpg)} / {_fmt_mpg(combined_mpg)}"),
            ("Price", _fmt_money(listing.get("price_current"))),
            ("Price when first seen", _fmt_money(listing.get("price_first_seen"))),
            ("Mileage", _fmt_num(listing.get("mileage"))),
            ("Distance", f"{listing.get('distance_miles')} mi" if listing.get("distance_miles") is not None else "-"),
            ("CPO", "Yes" if listing.get("cpo") else "No"),
            ("Dealer", f"{listing.get('dealer_name') or '-'} - {listing.get('dealer_city') or '-'}, {listing.get('dealer_state') or '-'}"),
            ("Active", "Yes" if listing.get("active") else "No (likely sold/removed)"),
            ("First seen", listing.get("first_seen")),
            ("Last seen", listing.get("last_seen")),
            ("Score", listing.get("score")),
        ]
        kv_rows = "".join(f"<tr><td>{_e(k)}</td><td>{_e(v)}</td></tr>" for k, v in fields)

        breakdown = listing.get("score_breakdown") or []
        if breakdown:
            breakdown_rows = "".join(
                f"<tr><td>{_e(item.get('label'))}</td><td>{_e(item.get('value'))}</td><td>{_e(item.get('detail'))}</td></tr>"
                for item in breakdown
            )
            breakdown_html = f"""<div class="table-wrap"><table>
<thead><tr><th>Component</th><th>Value</th><th>Detail</th></tr></thead>
<tbody>{breakdown_rows}</tbody></table></div>"""
        else:
            breakdown_html = '<div class="empty">No score breakdown recorded.</div>'

        if history:
            hist_rows = []
            prev_price = None
            for point in history:
                price = point.get("price")
                delta = "-"
                if prev_price is not None and price is not None:
                    diff = price - prev_price
                    delta = f"{'+' if diff > 0 else ''}{diff:,}"
                hist_rows.append(
                    f"<tr><td>{_e(point.get('date'))}</td><td>{_fmt_money(price)}</td>"
                    f"<td>{delta}</td><td>{_fmt_num(point.get('mileage'))}</td></tr>"
                )
                prev_price = price if price is not None else prev_price
            history_html = f"""<div class="table-wrap"><table>
<thead><tr><th>Date</th><th>Price</th><th>&Delta;</th><th>Mileage</th></tr></thead>
<tbody>{''.join(hist_rows)}</tbody></table></div>"""
        else:
            history_html = '<div class="empty">No price history recorded yet.</div>'

        if cross_shop:
            cross_html = "<ul>" + "".join(
                f'<li><a href="{_e(link["url"])}" target="_blank" rel="noopener">{_e(link["name"])}</a></li>'
                for link in cross_shop
            ) + "</ul>"
        else:
            cross_html = '<div class="empty">No cross-shop links for this vehicle.</div>'

        listing_url = listing.get("listing_url")
        source_link = (
            f'<p><a href="{_e(listing_url)}" target="_blank" rel="noopener">View original listing</a></p>'
            if listing_url else ""
        )

        badge = f'<span class="badge {_score_class(listing.get("score"))}">{_e(listing.get("score"))}</span>{_demo_tag(listing)}'

        appraisal_obj = market.appraise_vin(conn, vin, self.config)
        market_html = _appraisal_block(appraisal_obj.as_dict() if appraisal_obj else None)

        nhtsa_vin_url = vin_recall_url(vin)
        nhtsa_model_url = recall_lookup_url(make, model, year) if make and model and year else None
        reliability = db.get_reliability(conn, make, model, year) if make and model and year else None

        if reliability:
            top_components = reliability.get("top_components") or []
            if top_components:
                comp_rows = "".join(
                    f"<tr><td>{_e(name)}</td><td>{_e(count)}</td></tr>" for name, count in top_components
                )
                comp_html = f"""<div class="table-wrap"><table>
<thead><tr><th>Component</th><th>Complaints</th></tr></thead>
<tbody>{comp_rows}</tbody></table></div>"""
            else:
                comp_html = '<div class="empty">No component breakdown recorded.</div>'

            recalls = reliability.get("recalls") or []
            if recalls:
                recall_rows = "".join(
                    f"<tr><td>{_e(r.get('campaign'))}</td><td>{_e(r.get('component'))}</td>"
                    f"<td>{_e(r.get('consequence'))}</td><td>{_e(r.get('remedy'))}</td></tr>"
                    for r in recalls
                )
                recall_html = f"""<div class="table-wrap"><table>
<thead><tr><th>Campaign</th><th>Component</th><th>Consequence</th><th>Remedy</th></tr></thead>
<tbody>{recall_rows}</tbody></table></div>"""
            else:
                recall_html = '<div class="empty">No recall campaigns recorded.</div>'

            reliability_kv = [
                ("Complaints filed", _fmt_num(reliability.get("complaint_count"))),
                ("Recall campaigns", _fmt_num(reliability.get("recall_count"))),
                ("Crash-related complaints", _fmt_num(reliability.get("crash_complaints"))),
                ("Fire-related complaints", _fmt_num(reliability.get("fire_complaints"))),
                ("Injuries reported", _fmt_num(reliability.get("injuries"))),
                ("Deaths reported", _fmt_num(reliability.get("deaths"))),
                ("NHTSA data fetched", reliability.get("fetched_at") or "-"),
            ]
            reliability_kv_html = "".join(f"<tr><td>{_e(k)}</td><td>{_e(v)}</td></tr>" for k, v in reliability_kv)

            reliability_html = f"""
<p class="note">{_e(_NHTSA_VOLUME_CAVEAT)}</p>
<table class="kv">{reliability_kv_html}</table>
<h3>Top complaint components</h3>
{comp_html}
<h3>Recalls</h3>
{recall_html}
<p><a href="{_e(nhtsa_vin_url)}" target="_blank" rel="noopener">Look up this VIN on NHTSA</a>
 &middot; <a href="{_e(nhtsa_model_url or nhtsa_vin_url)}" target="_blank" rel="noopener">NHTSA recalls for {_e(year)} {_e(make)} {_e(model)}</a></p>
"""
        else:
            reliability_html = (
                '<div class="empty">No cached NHTSA data for this model year yet. '
                'Run <code>python3 -m carmon enrich</code> to fetch it.</div>'
                f'<p><a href="{_e(nhtsa_vin_url)}" target="_blank" rel="noopener">Look up this VIN on NHTSA</a></p>'
            )

        body = f"""
<h1>{_e(title)} {badge}</h1>
{source_link}
<div class="section">
  <h2>Listing details</h2>
  <table class="kv">{kv_rows}</table>
</div>
<div class="section">
  <h2>Score breakdown</h2>
  {breakdown_html}
</div>
<div class="section">
  <h2>Versus the market</h2>
  {market_html}
</div>
<div class="section">
  <h2>Reliability (NHTSA)</h2>
  {reliability_html}
</div>
<div class="section">
  <h2>Price history</h2>
  {history_html}
</div>
<div class="section">
  <h2>Cross-shop this vehicle</h2>
  {cross_html}
</div>
"""
        self._send_html(_page(title, body, self._last_run_str(conn), demo_warning=demo.demo_banner(conn)))

    def _page_sources(self, conn: Any, params: Dict[str, List[str]]) -> None:
        grouped = grouped_sources(self.config.search)
        blocks = []
        for _key, group in grouped.items():
            items = "".join(
                f'<li><a href="{_e(src["url"])}" target="_blank" rel="noopener">{_e(src["name"])}</a>'
                f' &mdash; {_e(src["note"])}</li>'
                for src in group.get("sources", [])
            )
            title = _e((group.get("description") or "").split(" -- ")[0]) or ""
            heading = _e(_key.replace("_", " ").title())
            blocks.append(f"""<div class="cat">
  <h3>{heading}</h3>
  <p class="desc">{_e(group.get('description') or '')}</p>
  <ul>{items or '<li>No sources configured.</li>'}</ul>
</div>""")
        body = f"""
<div class="note">These are manual cross-shopping links only. This app does not scrape any of these
sites; each link just pre-fills the same search criteria on that site's own search page so you can
check it by hand.</div>
{''.join(blocks)}
"""
        self._send_html(_page("Sources", body, self._last_run_str(conn), demo_warning=demo.demo_banner(conn)))

    def _page_digest(self, conn: Any, params: Dict[str, List[str]]) -> None:
        path, markdown = self._latest_digest()
        if markdown is None:
            body = '<div class="empty">No digest has been generated yet.</div>'
        else:
            body = f'<p>{_e(str(path))}</p><pre class="digest">{_e(markdown)}</pre>'
        self._send_html(_page("Digest", body, self._last_run_str(conn), demo_warning=demo.demo_banner(conn)))

    def _page_market(self, conn: Any, params: Dict[str, List[str]]) -> None:
        months = _parse_int(params, "months") or 6
        months = max(1, min(months, 36))
        report = market.market_report(conn, months=months, config=self.config)
        trend, models, deals = report["trend"], report["models"], report["best_deals"]
        dom, cuts = report["days_on_market"], report["price_cuts"]

        latest_median = trend[-1]["median_price"] if trend else None
        cut_share = cuts.get("cut_share_pct")
        median_days = dom.get("median_days")
        tiles = f"""
<div class="tiles">
  <div class="tile"><div class="label">Listings tracked</div><div class="value">{_e(report['listings_tracked'])}</div></div>
  <div class="tile"><div class="label">Median price (latest month)</div><div class="value">{_fmt_money(latest_median) if latest_median is not None else '—'}</div></div>
  <div class="tile"><div class="label">Median days on market</div><div class="value">{f"{median_days:.0f}" if median_days is not None else '—'}</div></div>
  <div class="tile"><div class="label">Listings that cut price</div><div class="value">{f"{cut_share:.0f}%" if cut_share is not None else '—'}</div></div>
</div>"""

        if trend:
            trend_html = (
                '<div class="table-wrap"><table><thead><tr>'
                "<th>Month</th><th>Observations</th><th>Cars</th><th>Median</th><th>Mean</th>"
                "<th>Min</th><th>Max</th><th>Median mileage</th><th>Change</th>"
                "</tr></thead><tbody>" + "".join(_trend_row(t) for t in trend) + "</tbody></table></div>"
            )
        else:
            trend_html = '<div class="empty">No monthly price history yet -- this fills in as the daily job runs.</div>'
        chart_html = _trend_chart_svg(trend)

        if models:
            models_html = (
                '<div class="table-wrap"><table><thead><tr>'
                "<th>Make / Model</th><th>Sample</th><th>Median price</th><th>Range</th>"
                "<th>Median mileage</th><th>$ / 1k miles</th><th>r&sup2;</th><th>Median days</th><th>Price cuts</th>"
                "</tr></thead><tbody>" + "".join(_model_row(m) for m in models) + "</tbody></table></div>"
            )
        else:
            models_html = '<div class="empty">No model has enough comparable listings stored yet.</div>'

        if deals:
            deals_html = (
                '<div class="table-wrap"><table><thead><tr>'
                "<th>Car</th><th>Price</th><th>Expected</th><th>Delta</th><th>Grade</th><th>Sample / confidence</th>"
                "</tr></thead><tbody>" + "".join(_deal_row(d) for d in deals) + "</tbody></table></div>"
            )
        else:
            deals_html = '<div class="empty">No active listing has enough comparable data to grade yet.</div>'

        body = f"""
<h1>Market</h1>
{tiles}
<p class="note">{_e(_CONDITION_BLIND_NOTE)}</p>
<div class="section">
  <h2>Monthly trend</h2>
  <p class="note">{_e(report['data_note'])}</p>
  {chart_html}
  {trend_html}
</div>
<div class="section">
  <h2>By model</h2>
  {models_html}
</div>
<div class="section">
  <h2>Best deals right now</h2>
  {deals_html}
</div>
"""
        self._send_html(_page("Market", body, self._last_run_str(conn), demo_warning=demo.demo_banner(conn)))

    def _page_appraise(self, conn: Any, params: Dict[str, List[str]]) -> None:
        make = _parse_str(params, "make") or ""
        model = _parse_str(params, "model") or ""
        year = _parse_int(params, "year")
        mileage = _parse_int(params, "mileage")
        price = _parse_int(params, "price")

        form = f"""
<form class="filters" method="get" action="/appraise">
  <div class="field"><label for="make">Make</label><input type="text" id="make" name="make" value="{_e(make)}"></div>
  <div class="field"><label for="model">Model</label><input type="text" id="model" name="model" value="{_e(model)}"></div>
  <div class="field"><label for="year">Year</label><input type="number" id="year" name="year" value="{_e(year) if year is not None else ''}"></div>
  <div class="field"><label for="mileage">Mileage</label><input type="number" id="mileage" name="mileage" value="{_e(mileage) if mileage is not None else ''}"></div>
  <div class="field"><label for="price">Asking price (optional)</label><input type="number" id="price" name="price" value="{_e(price) if price is not None else ''}"></div>
  <button type="submit">Appraise</button>
</form>"""

        if make and model:
            car = {"make": make, "model": model, "year": year, "mileage": mileage, "price_current": price}
            appraisal_obj = market.appraise(conn, car, self.config)
            appraisal = appraisal_obj.as_dict()
            result_html = f'<p>{_e(appraisal["summary"])}</p>{_appraisal_block(appraisal)}'
        else:
            result_html = '<div class="empty">Fill in at least a make and model to get an estimate.</div>'

        body = f"""
<h1>Appraise a car</h1>
<p class="sort-caption">Estimate a fair price from comparable listings already tracked here -- a
cross-sectional read on price versus mileage and year, not a valuation.</p>
{form}
<div class="section">{result_html}</div>
"""
        self._send_html(_page("Appraise", body, self._last_run_str(conn), demo_warning=demo.demo_banner(conn)))


# --------------------------------------------------------------------------
# server bootstrapping
# --------------------------------------------------------------------------

class _Server(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


def create_server(config: Config, host: Optional[str] = None, port: Optional[int] = None) -> _Server:
    """Build (but do not start) a ThreadingTCPServer bound to CarMonHandler."""
    web_cfg = config.web or {}
    resolved_host = host if host is not None else web_cfg.get("host", "127.0.0.1")
    resolved_port = port if port is not None else int(web_cfg.get("port", 8787) or 8787)

    handler_cls = type("_BoundCarMonHandler", (CarMonHandler,), {"config": config})
    server = _Server((resolved_host, resolved_port), handler_cls)
    return server


def serve(config: Config, host: Optional[str] = None, port: Optional[int] = None) -> None:
    """Create and run the server until interrupted (blocking)."""
    server = create_server(config, host=host, port=port)
    bound_host, bound_port = server.server_address[:2]
    print(f"carmon web server listening on http://{bound_host}:{bound_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
