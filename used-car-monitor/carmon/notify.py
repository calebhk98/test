"""Discord delivery for the daily digest.

Posts a compact embed (new listings / price drops / top scores) to an incoming
webhook. Falls back to plain chunked text if the embed would be too large, and
always respects Discord's 2000-char message and 1024-char field limits.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

import requests

from . import db
from .config import Config, get_secret
from .digest import _money, _title

LOG = logging.getLogger("carmon.notify")

MAX_MESSAGE = 2000
MAX_FIELD = 1024
MAX_EMBED_FIELDS = 25
COLOR_GOOD = 0x2ECC71
COLOR_QUIET = 0x95A5A6


class DiscordError(RuntimeError):
    pass


def _clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _listing_bullet(listing: Dict[str, Any], extra: str = "") -> str:
    parts = [f"`{listing.get('score', 0):+.2f}`", _title(listing), _money(listing.get("price_current"))]
    mileage = listing.get("mileage")
    if mileage is not None:
        parts.append(f"{mileage:,} mi")
    distance = listing.get("distance_miles")
    if distance is not None:
        parts.append(f"{distance:.0f} mi away")
    if listing.get("cpo"):
        parts.append("CPO")
    if extra:
        parts.append(extra)
    text = " · ".join(parts)
    url = listing.get("listing_url")
    return f"• [{text}]({url})" if url else f"• {text}"


def _section(title: str, listings: List[Dict[str, Any]], empty: str, formatter=None) -> Dict[str, str]:
    formatter = formatter or (lambda listing: _listing_bullet(listing))
    if not listings:
        body = empty
    else:
        body = ""
        for listing in listings:
            line = formatter(listing) + "\n"
            if len(body) + len(line) > MAX_FIELD - 20:
                body += f"…and {len(listings) - body.count('•')} more"
                break
            body += line
    return {"name": title, "value": _clip(body.strip() or empty, MAX_FIELD), "inline": False}


def build_discord_payload(
    config: Config,
    conn: sqlite3.Connection,
    run_date: Optional[str] = None,
    run_result: Optional[Dict[str, Any]] = None,
    web_url: Optional[str] = None,
    days: int = 1,
) -> Dict[str, Any]:
    run_date = run_date or date.today().isoformat()
    since = (date.fromisoformat(run_date) - timedelta(days=days - 1)).isoformat()
    top_n = int(config.digest.get("top_n", 5))

    new_listings = db.new_listings_since(conn, since, 8)
    drops = db.price_drops_since(conn, since, 8)
    top = db.search_listings(conn, sort="score", limit=top_n)
    stats = db.stats(conn, int(config.api.get("monthly_call_cap", 500)))

    def drop_formatter(listing: Dict[str, Any]) -> str:
        old, new = listing.get("old_price"), listing.get("new_price")
        delta = listing.get("price_drop") or 0
        return _listing_bullet(listing, f"↓{_money(delta)} from {_money(old)}")

    fields = [
        _section(f"🆕 New since {since} ({len(new_listings)})", new_listings, "Nothing new today."),
        _section(f"📉 Price drops ({len(drops)})", drops, "No price drops today.", drop_formatter),
        _section(f"⭐ Top {top_n} by score", top, "No listings stored yet."),
    ]
    status = (
        f"Tracking {stats['listings_active']} active listings · "
        f"MarketCheck quota {stats['api_calls_this_month']}/{stats['api_monthly_cap']} calls this month"
    )
    if run_result:
        status += (
            f"\nRun: fetched {run_result.get('fetched', 0)}, kept {run_result.get('kept', 0)}, "
            f"API calls {run_result.get('api_calls', 0)}"
        )
        for error in (run_result.get("errors") or [])[:2]:
            status += f"\n⚠️ {error}"
    if web_url:
        status += f"\nBrowse: {web_url}"
    fields.append({"name": "Status", "value": _clip(status, MAX_FIELD), "inline": False})

    search = config.search
    embed = {
        "title": f"Used Car Daily Digest — {run_date}",
        "description": _clip(
            f"{search.get('year_min')}+ · under {_money(search.get('price_max'))} · under "
            f"{search.get('mileage_max'):,} mi · within {search.get('radius_miles')} mi of {search.get('zip')}",
            300,
        ),
        "color": COLOR_GOOD if (new_listings or drops) else COLOR_QUIET,
        "fields": fields[:MAX_EMBED_FIELDS],
        "footer": {"text": "Used Car Daily Monitor · MarketCheck Inventory Search"},
    }
    return {"username": "Used Car Monitor", "embeds": [embed]}


def post_to_discord(
    webhook_url: str,
    payload: Dict[str, Any],
    session: Optional[Any] = None,
    max_retries: int = 3,
) -> bool:
    """POST a payload to a Discord webhook, honouring 429 retry_after."""
    if not webhook_url:
        raise DiscordError("DISCORD_WEBHOOK_URL is not set — add it to .env to enable Discord delivery.")
    session = session or requests
    attempt = 0
    while True:
        attempt += 1
        response = session.post(webhook_url, json=payload, timeout=20)
        status = getattr(response, "status_code", 0)
        if status in (200, 201, 204):
            return True
        if status == 429 and attempt <= max_retries:
            try:
                wait = float(response.json().get("retry_after", 2))
            except Exception:
                wait = 2.0
            LOG.warning("Discord rate limited; retrying in %.1fs", wait)
            time.sleep(min(30.0, wait))
            continue
        if 500 <= status < 600 and attempt <= max_retries:
            time.sleep(min(16, 2 ** attempt))
            continue
        body = getattr(response, "text", "")[:300]
        raise DiscordError(f"Discord webhook returned HTTP {status}: {body}")


def send_digest(
    config: Config,
    conn: sqlite3.Connection,
    webhook_url: Optional[str] = None,
    run_date: Optional[str] = None,
    run_result: Optional[Dict[str, Any]] = None,
    web_url: Optional[str] = None,
    session: Optional[Any] = None,
) -> bool:
    webhook_url = webhook_url if webhook_url is not None else get_secret("DISCORD_WEBHOOK_URL")
    payload = build_discord_payload(config, conn, run_date=run_date, run_result=run_result, web_url=web_url)
    return post_to_discord(webhook_url, payload, session=session)


def send_text(webhook_url: str, text: str, session: Optional[Any] = None) -> bool:
    """Send raw text, split into Discord-sized chunks."""
    chunks: List[str] = []
    remaining = text
    while remaining:
        chunks.append(remaining[:MAX_MESSAGE])
        remaining = remaining[MAX_MESSAGE:]
    for chunk in chunks:
        post_to_discord(webhook_url, {"content": chunk}, session=session)
    return True
