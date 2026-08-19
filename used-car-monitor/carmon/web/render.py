"""Shared HTML/CSS rendering: page chrome, one CSS stylesheet, and every table/badge/tile
helper used by more than one page.

Nothing here touches the network or the request -- every function takes plain data
(a listing dict, an appraisal dict, a sqlite connection) and returns an HTML string.
"""

from __future__ import annotations

import html
from typing import Any, Dict, List, Optional, Tuple

from .. import db, demo, market, quota

__all__ = [
    "e", "fmt_money", "fmt_num", "fmt_mpg", "score_class", "demo_tag",
    "sort_caption", "pace_tile", "grade_class", "grade_badge", "appraisal_block",
    "listing_link", "results_table", "trend_chart_svg", "trend_row", "model_row",
    "deal_row", "page", "NAV_LINKS", "SCRAPER_STATUS_CLASSES", "CONDITION_BLIND_NOTE",
    "NHTSA_VOLUME_CAVEAT", "SORT_LABELS",
]


# --------------------------------------------------------------------------
# basic formatting / escaping
# --------------------------------------------------------------------------
def e(value: Any) -> str:
    """Escape any value for HTML text context."""
    if value is None:
        return ""
    return html.escape(str(value))


def fmt_money(value: Any) -> str:
    if value is None:
        return "-"
    try:
        return f"${int(value):,}"
    except (TypeError, ValueError):
        return html.escape(str(value))


def fmt_num(value: Any) -> str:
    if value is None:
        return "-"
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return html.escape(str(value))


def fmt_mpg(value: Any) -> str:
    if value is None:
        return "—"
    try:
        return f"{float(value):.1f}"
    except (TypeError, ValueError):
        return "—"


def score_class(score: Optional[float]) -> str:
    if score is None:
        return "neutral"
    if score >= 2:
        return "good"
    if score >= 0:
        return "mid"
    return "bad"


def demo_tag(item: Dict[str, Any]) -> str:
    if item.get("source") != demo.DEMO_SOURCE:
        return ""
    return ' <span class="badge demo" title="Demo data seeded for browsing -- not a real listing">DEMO</span>'


# Order here drives both the dashboard <select> and the sort caption below it. Keys must
# match db.SORTABLE exactly (see carmon/db.py) -- that dict is the single source of truth
# for what sort= actually does; this just adds a human label for each key.
SORT_LABELS = {
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


def sort_caption(requested: Optional[str]) -> str:
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


def pace_tile(metrics: Dict[str, Any]) -> str:
    cls = _PACE_CLASSES.get(metrics.get("pace_label"), "")
    summary = quota.summary_line(metrics)
    expected = metrics.get("expected_by_now")
    expected_str = f"{expected:.0f}" if isinstance(expected, (int, float)) else "-"
    return f"""<div class="tile pace {cls}" title="{e(summary)}">
  <div class="label">API pace {e(metrics.get('pace_icon'))}</div>
  <div class="value">{e(metrics.get('used'))}/{e(metrics.get('cap'))}</div>
  <div class="pace-sub">{e(metrics.get('pace_label'))} &middot; expected ~{expected_str} by now</div>
  <code class="pace-bar">{e(quota.bar(metrics))}</code>
</div>"""


# Shown wherever NHTSA complaint counts appear prominently -- they are raw counts, not
# adjusted for how many of a given model are on the road, so a high-volume model naturally
# racks up more of them. The components that keep recurring are the more useful signal.
NHTSA_VOLUME_CAVEAT = (
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
CONDITION_BLIND_NOTE = (
    "This compares asking price against other listings' mileage and model year only -- it "
    "is not an appraisal of this car's condition, and is blind to trim, options, accident "
    "history and title status."
)


def grade_class(grade: Optional[str]) -> str:
    return _GRADE_CLASSES.get(grade, "neutral")


def grade_badge(appraisal: Dict[str, Any]) -> str:
    grade = appraisal.get("grade")
    if not grade:
        return '<span class="badge neutral">—</span>'
    icon = appraisal.get("grade_icon") or ""
    return f'<span class="badge {grade_class(grade)}">{e(icon)} {e(grade)}</span>'


def _basis_warning_block(appraisal: Dict[str, Any]) -> str:
    """Visible warning whenever the comparables are not actually the same model."""
    if appraisal.get("basis_level") in ("make", "all"):
        return (
            f'<p class="note">⚠️ Comparing against {e(appraisal.get("basis"))} -- not the '
            "same model, so read this as a rough bearing rather than a grade.</p>"
        )
    return ""


def _thin_comparable_warning(appraisal: Dict[str, Any]) -> str:
    """Same "different model" condition as `_basis_warning_block`, but as the small inline
    icon used in table cells (dashboard 'vs market' column, /market's deal rows) instead of
    a full paragraph -- both read `basis_level` the same way, so the check lives once."""
    if appraisal.get("basis_level") not in ("make", "all"):
        return ""
    return (
        ' <span title="Comparing against a different model -- thin comparable data" '
        'aria-label="different-model comparison">⚠️</span>'
    )


def appraisal_block(appraisal: Optional[Dict[str, Any]]) -> str:
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
    range_str = f"{fmt_money(comp_range[0])} – {fmt_money(comp_range[1])}" if comp_range else "—"
    per_mile = appraisal.get("dollars_per_1k_miles")
    per_mile_str = f"${per_mile:,.0f}" if per_mile is not None else "—"
    kv_rows = [
        ("Grade", grade_badge(appraisal)),
        ("Expected price", fmt_money(appraisal.get("expected_price"))),
        ("Actual price", fmt_money(appraisal.get("actual_price"))),
        ("Delta", delta_str),
        ("Percentile", percentile_str),
        ("Comparable median", fmt_money(appraisal.get("comparable_median"))),
        ("Comparable range", range_str),
        ("$ / 1,000 miles", per_mile_str),
        ("Sample size / confidence", f"{e(appraisal.get('sample_size'))} listings &middot; {e(appraisal.get('confidence'))} confidence"),
        ("Basis", e(appraisal.get("basis"))),
        ("Method", e(appraisal.get("method"))),
    ]
    kv_html = "".join(f"<tr><td>{e(label)}</td><td>{value}</td></tr>" for label, value in kv_rows)
    notes_html = "".join(f'<p class="note">{e(n)}</p>' for n in appraisal.get("notes") or [])
    return f"""<p class="note">{e(CONDITION_BLIND_NOTE)}</p>
{_basis_warning_block(appraisal)}
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
    cls = grade_class(appraisal["grade"])
    sign = f"{appraisal['delta_pct']:+.1f}%"
    warn = _thin_comparable_warning(appraisal)
    return (
        "<td>"
        f'<span class="badge {cls}" title="{e(appraisal["grade"])}">{sign}</span>{warn}'
        f'<div class="mv-sample">n={e(appraisal["sample_size"])} &middot; {e(appraisal["confidence"])}</div>'
        "</td>"
    )


def trend_chart_svg(trend: List[Dict[str, Any]]) -> str:
    """Inline SVG line chart of median price by month -- no chart library, drawn by hand.

    Colors come from CSS classes tied to the page's --accent/--muted/--border variables
    (see BASE_CSS), so the chart stays readable in both light and dark themes.
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
        tooltip = f"{e(t['month'])}: {fmt_money(t['median_price'])} ({e(t['observations'])} observations)"
        dots.append(f'<circle class="chart-point" cx="{x:.1f}" cy="{y:.1f}" r="3.5"><title>{tooltip}</title></circle>')
        labels.append(
            f'<text class="chart-label" x="{x:.1f}" y="{height - 8:.1f}" text-anchor="middle">{e(t["month"][5:])}</text>'
        )

    baseline_y = pad_top + plot_h
    axis = f'<line class="chart-axis" x1="{pad_left}" y1="{baseline_y:.1f}" x2="{width - pad_right}" y2="{baseline_y:.1f}" />'
    hi_label = f'<text class="chart-label" x="{pad_left - 8}" y="{pad_top + 4}" text-anchor="end">{fmt_money(round(hi))}</text>'
    lo_label = f'<text class="chart-label" x="{pad_left - 8}" y="{baseline_y:.1f}" text-anchor="end">{fmt_money(round(lo))}</text>'
    line = f'<polyline class="chart-line" points="{poly}" fill="none" />' if n > 1 else ""

    return f"""<svg class="trend-chart" viewBox="0 0 {width} {height}" role="img" aria-label="Median listing price by month">
  {axis}
  {line}
  {''.join(dots)}
  {''.join(labels)}
  {hi_label}
  {lo_label}
</svg>"""


def trend_row(t: Dict[str, Any]) -> str:
    change_pct = t.get("change_pct")
    change_str = f"{change_pct:+.1f}%" if change_pct is not None else "—"
    return (
        "<tr>"
        f"<td>{e(t['month'])}</td>"
        f"<td>{e(t['observations'])}</td>"
        f"<td>{e(t['cars'])}</td>"
        f"<td>{fmt_money(t['median_price'])}</td>"
        f"<td>{fmt_money(t['mean_price'])}</td>"
        f"<td>{fmt_money(t['min_price'])}</td>"
        f"<td>{fmt_money(t['max_price'])}</td>"
        f"<td>{fmt_num(t.get('median_mileage'))}</td>"
        f"<td>{change_str}</td>"
        "</tr>"
    )


def model_row(m: Dict[str, Any]) -> str:
    dom = m.get("days_on_market") or {}
    cuts = m.get("price_cuts") or {}
    median_days = dom.get("median_days")
    cut_share = cuts.get("cut_share_pct")
    r2 = m.get("r_squared")
    per_mile = m.get("dollars_per_1k_miles")
    per_mile_str = f"${per_mile:,.0f}" if per_mile is not None else "—"
    range_str = f"{fmt_money(m['min_price'])}&ndash;{fmt_money(m['max_price'])}"
    r2_str = f"{r2:.2f}" if r2 is not None else "—"
    days_str = f"{median_days:.0f}" if median_days is not None else "—"
    cut_str = f"{cut_share:.0f}%" if cut_share is not None else "—"
    return (
        "<tr>"
        f"<td>{e(m['make'])} {e(m['model'])}</td>"
        f"<td>{e(m['sample_size'])}</td>"
        f"<td>{fmt_money(m['median_price'])}</td>"
        f"<td>{range_str}</td>"
        f"<td>{fmt_num(m['median_mileage'])}</td>"
        f"<td>{per_mile_str}</td>"
        f"<td>{r2_str}</td>"
        f"<td>{days_str}</td>"
        f"<td>{cut_str}</td>"
        "</tr>"
    )


def deal_row(item: Dict[str, Any]) -> str:
    appraisal = item.get("appraisal") or {}
    delta, delta_pct = appraisal.get("delta"), appraisal.get("delta_pct")
    delta_str = f"{delta:+,.0f} ({delta_pct:+.1f}%)" if delta is not None and delta_pct is not None else "—"
    warn = _thin_comparable_warning(appraisal)
    return (
        "<tr>"
        f"<td>{listing_link(item)}</td>"
        f"<td>{fmt_money(item.get('price_current'))}</td>"
        f"<td>{fmt_money(appraisal.get('expected_price'))}</td>"
        f"<td>{delta_str}</td>"
        f"<td>{grade_badge(appraisal)}{warn}</td>"
        f"<td>{e(appraisal.get('sample_size'))} &middot; {e(appraisal.get('confidence'))}</td>"
        "</tr>"
    )


# --------------------------------------------------------------------------
# page chrome (shared CSS/JS + nav/footer), all inline, no external assets
# --------------------------------------------------------------------------

BASE_CSS = """
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
.secret-help { color: var(--muted); font-size: 0.8rem; margin: 0.2rem 0 0; max-width: 32rem; }
"""

NAV_LINKS = [
    ("/", "Dashboard"),
    ("/market", "Market"),
    ("/appraise", "Appraise"),
    ("/sources", "Sources"),
    ("/digest", "Digest"),
    ("/scrapers", "Scrapers"),
    ("/settings", "Settings"),
    ("/api/health", "API health"),
]

# Status badges on the /scrapers page reuse the good/mid/bad palette. "blocked" and
# "disallowed" are expected, healthy outcomes (a site declining automated access), not
# failures, so they get the same "mid" (amber) treatment as "budget", not "bad".
SCRAPER_STATUS_CLASSES = {
    "ok": "good",
    "blocked": "mid",
    "disallowed": "mid",
    "budget": "mid",
    "empty": "mid",
    "error": "bad",
    "unparsed": "bad",
    "never run": "neutral",
}


def page(title: str, body: str, last_run: Optional[str] = None, demo_warning: Optional[str] = None) -> str:
    nav = "".join(f'<a href="{href}">{e(label)}</a>' for href, label in NAV_LINKS)
    footer_bits = "Data source: MarketCheck Inventory Search API (manual cross-shop links only, no scraping)."
    if last_run:
        footer_bits += f" Last run: {e(last_run)}."
    banner_html = f'<div class="demo-banner">⚠️ {e(demo_warning)}</div>' if demo_warning else ""
    return f"""<title>{e(title)}</title>
<style>{BASE_CSS}</style>
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


def listing_link(listing: Dict[str, Any]) -> str:
    label = " ".join(
        str(part) for part in (listing.get("year"), listing.get("make"), listing.get("model"), listing.get("trim"))
        if part
    ).strip() or listing.get("vin", "")
    return f'<a href="/listing/{e(listing.get("vin"))}">{e(label)}</a>'


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


def results_table(conn: Any, listings: List[Dict[str, Any]], config: Optional[Any] = None) -> str:
    if not listings:
        return '<div class="empty">No listings match those filters.</div>'
    reliability_cache: Dict[Tuple[Any, Any, Any], Optional[Dict[str, Any]]] = {}
    market_cache: Dict[Any, Any] = {}
    rows = []
    for item in listings:
        rows.append(
            "<tr>"
            f'<td><span class="badge {score_class(item.get("score"))}">{e(item.get("score") if item.get("score") is not None else "-")}</span></td>'
            f"<td>{listing_link(item)}{demo_tag(item)}</td>"
            f'<td>{fmt_money(item.get("price_current"))}</td>'
            f'<td>{fmt_num(item.get("mileage"))}</td>'
            f'<td>{fmt_mpg(item.get("combined_mpg"))}</td>'
            f'<td title="NHTSA complaints / recalls for this model year">{e(_nhtsa_cell(conn, item, reliability_cache))}</td>'
            f'<td>{e(item.get("distance_miles") if item.get("distance_miles") is not None else "-")}</td>'
            f'<td>{"Yes" if item.get("cpo") else "No"}</td>'
            f'<td>{e(item.get("dealer_name") or "-")} &middot; {e(item.get("dealer_city") or "-")}</td>'
            f'<td>{e(item.get("first_seen") or "-")}</td>'
            f"{_vs_market_cell(conn, config, market_cache, item)}"
            "</tr>"
        )
    return f"""<div class="table-wrap"><table>
<thead><tr>
  <th>Score</th><th>Vehicle</th><th>Price</th><th>Mileage</th><th>MPG</th><th>NHTSA</th><th>Dist.</th><th>CPO</th><th>Dealer</th><th>First seen</th><th>Vs market</th>
</tr></thead>
<tbody>{''.join(rows)}</tbody>
</table></div>"""
