"""Daily digest rendering: new listings, price drops, top scores, quota usage."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import db
from .config import Config
from .sources import build_sources


def _money(value: Optional[int]) -> str:
    return f"${value:,.0f}" if value not in (None, "") else "n/a"


def _miles(value: Optional[int]) -> str:
    return f"{value:,} mi" if value not in (None, "") else "n/a"


def _title(listing: Dict[str, Any]) -> str:
    parts = [str(listing.get("year") or ""), listing.get("make") or "", listing.get("model") or ""]
    trim = listing.get("trim")
    if trim:
        parts.append(str(trim))
    return " ".join(p for p in parts if p).strip() or listing.get("vin", "unknown")


def _line(listing: Dict[str, Any], extra: str = "") -> str:
    bits = [
        f"**{_title(listing)}** — score **{listing.get('score', 0):+.2f}**",
        f"{_money(listing.get('price_current'))} · {_miles(listing.get('mileage'))}",
    ]
    distance = listing.get("distance_miles")
    if distance is not None:
        bits.append(f"{distance:.0f} mi away")
    if listing.get("cpo"):
        bits.append("**CPO**")
    dealer = listing.get("dealer_name")
    if dealer:
        city = listing.get("dealer_city") or ""
        state = listing.get("dealer_state") or ""
        bits.append(f"{dealer} ({city}, {state})".replace(" ()", ""))
    if extra:
        bits.append(extra)
    line = " · ".join(bits)
    url = listing.get("listing_url")
    if url:
        line += f"\n  [listing]({url}) · VIN {listing.get('vin')}"
    else:
        line += f"\n  VIN {listing.get('vin')}"
    return f"- {line}"


def _top_reasons(listing: Dict[str, Any], limit: int = 2) -> str:
    breakdown = listing.get("score_breakdown") or []
    if not isinstance(breakdown, list):
        return ""
    ranked = sorted(
        (c for c in breakdown if isinstance(c, dict) and c.get("value")),
        key=lambda c: abs(float(c.get("value") or 0)),
        reverse=True,
    )[:limit]
    if not ranked:
        return ""
    return "; ".join(f"{c['label']} {float(c['value']):+.2f}" for c in ranked)


def render_digest(
    config: Config,
    conn: sqlite3.Connection,
    run_date: Optional[str] = None,
    run_result: Optional[Dict[str, Any]] = None,
    days: int = 1,
) -> str:
    run_date = run_date or date.today().isoformat()
    since = (date.fromisoformat(run_date) - timedelta(days=days - 1)).isoformat()
    digest_config = config.digest
    top_n = int(digest_config.get("top_n", 5))
    new_limit = int(digest_config.get("new_listing_limit", 15))
    drop_limit = int(digest_config.get("price_drop_limit", 15))

    new_listings = db.new_listings_since(conn, since, new_limit)
    drops = db.price_drops_since(conn, since, drop_limit)
    top = db.search_listings(conn, sort="score", limit=top_n)
    stats = db.stats(conn, int(config.api.get("monthly_call_cap", 500)))

    search = config.search
    lines: List[str] = []
    lines.append(f"# Used Car Daily Digest — {run_date}")
    lines.append("")
    lines.append(
        f"_{search.get('year_min')}+ · under {_money(search.get('price_max'))} · under "
        f"{_miles(search.get('mileage_max'))} · within {search.get('radius_miles')} mi of {search.get('zip')}_"
    )
    lines.append("")

    lines.append(f"## New since {since} ({len(new_listings)})")
    if new_listings:
        for listing in new_listings:
            reasons = _top_reasons(listing)
            lines.append(_line(listing, f"why: {reasons}" if reasons else ""))
    else:
        lines.append("- Nothing new today.")
    lines.append("")

    lines.append(f"## Price drops since {since} ({len(drops)})")
    if drops:
        for listing in drops:
            old, new = listing.get("old_price"), listing.get("new_price")
            delta = listing.get("price_drop") or 0
            pct = (100.0 * delta / old) if old else 0.0
            lines.append(_line(listing, f"dropped {_money(delta)} ({pct:.1f}%): {_money(old)} → {_money(new)}"))
    else:
        lines.append("- No price drops today.")
    lines.append("")

    lines.append(f"## Top {top_n} overall by score")
    if top:
        for rank, listing in enumerate(top, 1):
            reasons = _top_reasons(listing, limit=3)
            lines.append(f"{rank}. " + _line(listing, f"why: {reasons}" if reasons else "")[2:])
    else:
        lines.append("- No listings stored yet.")
    lines.append("")

    lines.append("## Status")
    lines.append(
        f"- Tracking **{stats['listings_active']}** active listings "
        f"({stats['listings_total']} seen all-time)."
    )
    lines.append(
        f"- MarketCheck calls this month: **{stats['api_calls_this_month']} / {stats['api_monthly_cap']}** "
        f"({stats['api_calls_remaining']} left)."
    )
    if run_result:
        lines.append(
            f"- This run: fetched {run_result.get('fetched', 0)}, kept {run_result.get('kept', 0)}, "
            f"filtered out {run_result.get('filtered_out', 0)}, API calls {run_result.get('api_calls', 0)}."
        )
        for error in run_result.get("errors") or []:
            lines.append(f"- ⚠️ {error}")
    lines.append("")

    if digest_config.get("include_source_links", True):
        lines.append("## Cross-shop the same search")
        lines.append("_Manual links only — v1 does not scrape these sites._")
        for source in build_sources(search):
            lines.append(f"- [{source.name}]({source.url}) — {source.note}")
        lines.append("")

    lines.append(f"_Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} · data: MarketCheck Inventory Search API_")
    return "\n".join(lines)


def save_digest(config: Config, markdown: str, run_date: Optional[str] = None) -> Path:
    run_date = run_date or date.today().isoformat()
    directory = config.digest_dir
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"digest-{run_date}.md"
    path.write_text(markdown, encoding="utf-8")
    latest = directory / "latest.md"
    latest.write_text(markdown, encoding="utf-8")
    return path


def latest_digest_path(config: Config) -> Optional[Path]:
    directory = config.digest_dir
    if not directory.exists():
        return None
    dated = sorted(directory.glob("digest-*.md"))
    if dated:
        return dated[-1]
    latest = directory / "latest.md"
    return latest if latest.exists() else None


def latest_digest_text(config: Config) -> Optional[str]:
    path = latest_digest_path(config)
    return path.read_text(encoding="utf-8") if path else None
