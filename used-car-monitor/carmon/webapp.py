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


# Shown wherever NHTSA complaint counts appear prominently -- they are raw counts, not
# adjusted for how many of a given model are on the road, so a high-volume model naturally
# racks up more of them. The components that keep recurring are the more useful signal.
_NHTSA_VOLUME_CAVEAT = (
    "Raw NHTSA complaint counts are not adjusted for sales volume, so a high-volume model "
    "naturally accumulates more of them — treat the recurring components as the stronger signal."
)


# --------------------------------------------------------------------------
# page chrome (shared CSS/JS + nav/footer), all inline, no external assets
# --------------------------------------------------------------------------

_BASE_CSS = """
:root {
  --bg: #f5f6f8; --panel: #ffffff; --text: #1a1d23; --muted: #5b6270;
  --border: #dfe3ea; --accent: #2563eb; --good: #16a34a; --good-bg: #dcfce7;
  --mid: #b45309; --mid-bg: #fef3c7; --bad: #dc2626; --bad-bg: #fee2e2;
  --input-bg: #ffffff;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #14161a; --panel: #1d2026; --text: #e7e9ee; --muted: #9aa2b1;
    --border: #2c313b; --accent: #60a5fa; --good: #4ade80; --good-bg: #14361f;
    --mid: #fbbf24; --mid-bg: #3a2c0a; --bad: #f87171; --bad-bg: #3a1414;
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
"""

_NAV_LINKS = [
    ("/", "Dashboard"),
    ("/sources", "Sources"),
    ("/digest", "Digest"),
    ("/api/health", "API health"),
]


def _page(title: str, body: str, last_run: Optional[str] = None) -> str:
    nav = "".join(f'<a href="{href}">{_e(label)}</a>' for href, label in _NAV_LINKS)
    footer_bits = "Data source: MarketCheck Inventory Search API (manual cross-shop links only, no scraping)."
    if last_run:
        footer_bits += f" Last run: {_e(last_run)}."
    return f"""<title>{_e(title)}</title>
<style>{_BASE_CSS}</style>
<header class="site">
  <div class="brand">Used Car Monitor</div>
  <nav>{nav}</nav>
</header>
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


def _results_table(conn: Any, listings: List[Dict[str, Any]]) -> str:
    if not listings:
        return '<div class="empty">No listings match those filters.</div>'
    reliability_cache: Dict[Tuple[Any, Any, Any], Optional[Dict[str, Any]]] = {}
    rows = []
    for item in listings:
        rows.append(
            "<tr>"
            f'<td><span class="badge {_score_class(item.get("score"))}">{_e(item.get("score") if item.get("score") is not None else "-")}</span></td>'
            f"<td>{_listing_link(item)}</td>"
            f'<td>{_fmt_money(item.get("price_current"))}</td>'
            f'<td>{_fmt_num(item.get("mileage"))}</td>'
            f'<td>{_fmt_mpg(item.get("combined_mpg"))}</td>'
            f'<td title="NHTSA complaints / recalls for this model year">{_e(_nhtsa_cell(conn, item, reliability_cache))}</td>'
            f'<td>{_e(item.get("distance_miles") if item.get("distance_miles") is not None else "-")}</td>'
            f'<td>{"Yes" if item.get("cpo") else "No"}</td>'
            f'<td>{_e(item.get("dealer_name") or "-")} &middot; {_e(item.get("dealer_city") or "-")}</td>'
            f'<td>{_e(item.get("first_seen") or "-")}</td>'
            "</tr>"
        )
    return f"""<div class="table-wrap"><table>
<thead><tr>
  <th>Score</th><th>Vehicle</th><th>Price</th><th>Mileage</th><th>MPG</th><th>NHTSA</th><th>Dist.</th><th>CPO</th><th>Dealer</th><th>First seen</th>
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
        self.send_header("Content-Type", "application/json")
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
        })

    def _api_stats(self, conn: Any, params: Dict[str, List[str]]) -> None:
        cap = int(self.config.api.get("monthly_call_cap", 500) or 500)
        self._send_json(db.stats(conn, monthly_cap=cap))

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
        try:
            listings = db.search_listings(conn, limit=200, offset=0, **kwargs)
        except Exception:
            listings = []

        tiles = f"""
<div class="tiles">
  <div class="tile"><div class="label">Active listings</div><div class="value">{_e(stats['listings_active'])}</div></div>
  <div class="tile"><div class="label">New today</div><div class="value">{_e(new_today)}</div></div>
  <div class="tile"><div class="label">Price drops today</div><div class="value">{_e(drops_today)}</div></div>
  <div class="tile"><div class="label">API calls this month</div><div class="value">{_e(stats['api_calls_this_month'])} / {_e(stats['api_monthly_cap'])}</div></div>
  <div class="tile"><div class="label">Best score</div><div class="value">{_e(stats['best_score'] if stats['best_score'] is not None else '-')}</div></div>
  <div class="tile"><div class="label">Model-years with NHTSA data</div><div class="value">{_e(nhtsa_model_years)}</div></div>
</div>"""

        def sel(value: str) -> str:
            return " selected" if sort == value else ""

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
      <option value="score"{sel('score')}>Score</option>
      <option value="price"{sel('price')}>Price (low)</option>
      <option value="price_desc"{sel('price_desc')}>Price (high)</option>
      <option value="mileage"{sel('mileage')}>Mileage</option>
      <option value="distance"{sel('distance')}>Distance</option>
      <option value="year"{sel('year')}>Year</option>
      <option value="first_seen"{sel('first_seen')}>First seen</option>
    </select>
  </div>
  <div class="field checkbox"><label class="checkbox"><input type="checkbox" name="cpo" value="1"{cpo_checked}> CPO only</label></div>
  <button type="submit">Filter</button>
</form>"""

        body = tiles + form + f'<div class="section">{_results_table(conn, listings)}</div>'
        self._send_html(_page("Dashboard", body, self._last_run_str(conn)))

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

        badge = f'<span class="badge {_score_class(listing.get("score"))}">{_e(listing.get("score"))}</span>'

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
        self._send_html(_page(title, body, self._last_run_str(conn)))

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
        self._send_html(_page("Sources", body, self._last_run_str(conn)))

    def _page_digest(self, conn: Any, params: Dict[str, List[str]]) -> None:
        path, markdown = self._latest_digest()
        if markdown is None:
            body = '<div class="empty">No digest has been generated yet.</div>'
        else:
            body = f'<p>{_e(str(path))}</p><pre class="digest">{_e(markdown)}</pre>'
        self._send_html(_page("Digest", body, self._last_run_str(conn)))


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
