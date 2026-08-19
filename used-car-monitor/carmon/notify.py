"""Discord delivery for the daily digest.

Two transports, chosen by `discord.mode` in config.json (default "auto"):

* **dm** — a real direct message, no server channel involved. Needs a bot application:
  put `DISCORD_BOT_TOKEN` and `DISCORD_USER_ID` in `.env`. The monitor opens a DM channel
  with `POST /users/@me/channels` and posts there, so the digest lands in your Discord DMs
  exactly like a message from a friend.

  One Discord-imposed caveat, and there is no way around it: **a bot can only DM a user it
  shares a server with.** That is a platform rule, not a limitation of this code. The usual
  fix is a private server containing just you and the bot — you never have to look at it,
  and the digest still arrives as a DM rather than in a channel.

* **webhook** — the classic incoming webhook, which always posts into a server channel.
  Needs only `DISCORD_WEBHOOK_URL`.

"auto" prefers the DM transport when a bot token and user id are present, and falls back to
the webhook otherwise. Either way the message respects Discord's 2000-char message and
1024-char embed-field limits.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

import requests

from . import db, demo as demo_module, quota
from .config import Config, get_secret
from .digest import _money, _reliability_note, _title
from .pipeline import attach_cached_enrichment

LOG = logging.getLogger("carmon.notify")

MAX_MESSAGE = 2000
MAX_FIELD = 1024
MAX_EMBED_FIELDS = 25
COLOR_GOOD = 0x2ECC71
COLOR_QUIET = 0x95A5A6

DISCORD_API = "https://discord.com/api/v10"


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
    delta = listing.get("market_delta_pct")
    if delta is not None:
        parts.append(f"{float(delta):+.0f}% vs market")
    mpg = listing.get("combined_mpg")
    if mpg:
        parts.append(f"{float(mpg):.0f} mpg")
    if listing.get("cpo"):
        parts.append("CPO")
    complaints, recalls = listing.get("complaint_count"), listing.get("recall_count")
    if complaints is not None or recalls is not None:
        parts.append(f"NHTSA {complaints or 0}c/{recalls or 0}r")
    if extra:
        parts.append(extra)
    text = " · ".join(parts)
    url = listing.get("listing_url")
    return f"• [{text}]({url})" if url else f"• {text}"


def _bounded_body(listings: List[Dict[str, Any]], formatter) -> str:
    """Join formatted lines until the Discord field-length budget runs out."""
    body = ""
    for added, listing in enumerate(listings):
        line = formatter(listing) + "\n"
        if len(body) + len(line) > MAX_FIELD - 20:
            return body + f"…and {len(listings) - added} more"
        body += line
    return body


def _section(title: str, listings: List[Dict[str, Any]], empty: str, formatter=None) -> Dict[str, str]:
    formatter = formatter or (lambda listing: _listing_bullet(listing))
    body = _bounded_body(listings, formatter) if listings else empty
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

    new_listings = [attach_cached_enrichment(conn, l) for l in db.new_listings_since(conn, since, 8)]
    drops = [attach_cached_enrichment(conn, l) for l in db.price_drops_since(conn, since, 8)]
    top = [attach_cached_enrichment(conn, l) for l in db.search_listings(conn, sort="score", limit=top_n)]
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
    status = f"Tracking {stats['listings_active']} active listings"
    if config.data.get("discord", {}).get("include_pace", True):
        metrics = quota.pace_from_db(conn, int(config.api.get("monthly_call_cap", 500)))
        status += (
            f"\n{metrics['pace_icon']} MarketCheck quota {metrics['used']}/{metrics['cap']} · "
            f"day {metrics['day_of_month']}/{metrics['days_in_month']} · "
            f"expected ~{metrics['expected_by_now']:.0f} by now · "
            f"{metrics['pace_ratio']:.2f}x pace ({metrics['pace_label']}) · "
            f"~{metrics['affordable_per_day']:.0f}/day still affordable"
        )
    else:
        status += (
            f" · MarketCheck quota {stats['api_calls_this_month']}/{stats['api_monthly_cap']} calls this month"
        )
    if run_result:
        status += (
            f"\nRun: fetched {run_result.get('fetched', 0)}, kept {run_result.get('kept', 0)}, "
            f"API calls {run_result.get('api_calls', 0)}"
        )
        sweep = run_result.get("sweep") or {}
        if sweep.get("ran"):
            status += (
                f"\n🧹 Month-end sweep spent {sweep.get('calls_used', 0)} leftover call(s) "
                "that would have expired tonight"
            )
        for error in (run_result.get("errors") or [])[:2]:
            status += f"\n⚠️ {error}"
    if web_url:
        status += f"\nBrowse: {web_url}"
    fields.append({"name": "Status", "value": _clip(status, MAX_FIELD), "inline": False})

    demo_warning = demo_module.demo_banner(conn)
    if demo_warning:
        fields.insert(0, {"name": "⚠️ DEMO DATA", "value": _clip(demo_warning, MAX_FIELD), "inline": False})

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


def _retry_after_seconds(response: Any, default: float = 2.0) -> float:
    try:
        return float(response.json().get("retry_after", default))
    except Exception:
        return default


def _post(
    url: str,
    payload: Dict[str, Any],
    session: Optional[Any] = None,
    headers: Optional[Dict[str, str]] = None,
    max_retries: int = 3,
    what: str = "Discord",
) -> Any:
    """POST to Discord, honouring 429 retry_after and retrying 5xx."""
    session = session or requests
    attempt = 0
    while True:
        attempt += 1
        response = session.post(url, json=payload, headers=headers, timeout=20)
        status = getattr(response, "status_code", 0)
        if status in (200, 201, 204):
            return response
        if status == 429 and attempt <= max_retries:
            wait = _retry_after_seconds(response)
            LOG.warning("%s rate limited; retrying in %.1fs", what, wait)
            time.sleep(min(30.0, wait))
            continue
        if 500 <= status < 600 and attempt <= max_retries:
            time.sleep(min(16, 2 ** attempt))
            continue
        body = getattr(response, "text", "")[:300]
        raise DiscordError(f"{what} returned HTTP {status}: {body}")


def post_to_discord(
    webhook_url: str,
    payload: Dict[str, Any],
    session: Optional[Any] = None,
    max_retries: int = 3,
) -> bool:
    """POST a payload to a Discord webhook (server channel transport)."""
    if not webhook_url:
        raise DiscordError("DISCORD_WEBHOOK_URL is not set — add it to .env to enable Discord delivery.")
    _post(webhook_url, payload, session=session, max_retries=max_retries, what="Discord webhook")
    return True


def open_dm_channel(bot_token: str, user_id: str, session: Optional[Any] = None) -> str:
    """Open (or reuse) the bot's DM channel with a user and return its channel id.

    Discord only lets a bot DM users who share a server with it — see the module docstring.
    A 403 here almost always means that shared server is missing.
    """
    if not bot_token:
        raise DiscordError("DISCORD_BOT_TOKEN is not set — add it to .env to send Discord DMs.")
    if not user_id:
        raise DiscordError(
            "DISCORD_USER_ID is not set. In Discord: Settings -> Advanced -> Developer Mode, "
            "then right-click your name -> Copy User ID."
        )
    response = _post(
        f"{DISCORD_API}/users/@me/channels",
        {"recipient_id": str(user_id)},
        session=session,
        headers={"Authorization": f"Bot {bot_token}"},
        what="Discord DM channel open",
    )
    try:
        channel_id = (response.json() or {}).get("id")
    except Exception as exc:
        raise DiscordError(f"Discord returned an unreadable DM channel response: {exc}") from exc
    if not channel_id:
        raise DiscordError("Discord did not return a DM channel id")
    return str(channel_id)


def post_to_dm(
    bot_token: str,
    user_id: str,
    payload: Dict[str, Any],
    session: Optional[Any] = None,
    channel_id: Optional[str] = None,
) -> bool:
    """Send the digest as a real direct message (no server channel involved)."""
    channel_id = channel_id or open_dm_channel(bot_token, user_id, session=session)
    body = {key: value for key, value in payload.items() if key not in ("username", "avatar_url")}
    try:
        _post(
            f"{DISCORD_API}/channels/{channel_id}/messages",
            body,
            session=session,
            headers={"Authorization": f"Bot {bot_token}"},
            what="Discord DM",
        )
    except DiscordError as exc:
        if "403" in str(exc):
            raise DiscordError(
                f"{exc}\nDiscord refuses bot DMs to users who share no server with the bot. "
                "Create a private server, invite the bot, and keep your DMs open to server members."
            ) from exc
        raise
    return True


def resolve_transport(
    config: Config,
    mode: Optional[str] = None,
    webhook_url: Optional[str] = None,
    bot_token: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Decide whether to send a DM or a webhook post, and say why.

    mode "dm" or "webhook" forces a transport; "auto" (the default) sends a DM when a bot
    token and user id are configured, else falls back to the webhook.
    """
    mode = (mode or config.data.get("discord", {}).get("mode", "auto") or "auto").lower()
    webhook_url = webhook_url if webhook_url is not None else get_secret("DISCORD_WEBHOOK_URL")
    bot_token = bot_token if bot_token is not None else get_secret("DISCORD_BOT_TOKEN")
    user_id = user_id if user_id is not None else get_secret("DISCORD_USER_ID")

    if mode == "dm":
        if not (bot_token and user_id):
            raise DiscordError(
                "discord.mode is 'dm' but DISCORD_BOT_TOKEN and/or DISCORD_USER_ID are missing "
                "from .env. See the Discord DM setup steps in README.md."
            )
        return {"transport": "dm", "bot_token": bot_token, "user_id": user_id}
    if mode == "webhook":
        if not webhook_url:
            raise DiscordError("discord.mode is 'webhook' but DISCORD_WEBHOOK_URL is missing from .env.")
        return {"transport": "webhook", "webhook_url": webhook_url}

    if bot_token and user_id:
        return {"transport": "dm", "bot_token": bot_token, "user_id": user_id}
    if webhook_url:
        return {"transport": "webhook", "webhook_url": webhook_url}
    raise DiscordError(
        "No Discord delivery configured. Set DISCORD_BOT_TOKEN + DISCORD_USER_ID (direct message) "
        "or DISCORD_WEBHOOK_URL (server channel) in .env."
    )


def send_digest(
    config: Config,
    conn: sqlite3.Connection,
    webhook_url: Optional[str] = None,
    run_date: Optional[str] = None,
    run_result: Optional[Dict[str, Any]] = None,
    web_url: Optional[str] = None,
    session: Optional[Any] = None,
    mode: Optional[str] = None,
    bot_token: Optional[str] = None,
    user_id: Optional[str] = None,
) -> str:
    """Deliver the digest and return which transport was used ("dm" or "webhook")."""
    target = resolve_transport(config, mode=mode, webhook_url=webhook_url,
                               bot_token=bot_token, user_id=user_id)
    payload = build_discord_payload(config, conn, run_date=run_date, run_result=run_result, web_url=web_url)
    payload.setdefault("username", config.data.get("discord", {}).get("username", "Used Car Monitor"))
    if target["transport"] == "dm":
        post_to_dm(target["bot_token"], target["user_id"], payload, session=session)
    else:
        post_to_discord(target["webhook_url"], payload, session=session)
    return target["transport"]


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
