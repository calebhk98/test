"""Request dispatch, routing tables, auth/write checks, and server bootstrapping.

`CarMonHandler` itself only owns: turning a raw HTTP request into (conn, params) plus a
handler function to call, the two auth gates every write must pass, and the small set of
response helpers (`_send_json`, `_send_html`). The handler functions it dispatches to are
defined on `ApiHandlers` (JSON, `/api/*`) and `PageHandlers` (HTML) -- both mixed in below
-- so this module stays about *routing*, not about what each route renders.
"""

from __future__ import annotations

import html
import http.server
import json
import os
import socketserver
import sys
import traceback
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import parse_qs, urlsplit

import carmon
from .. import db, demo
from ..config import Config, get_secret, load_env
from ..settings import writes_allowed
from .api import ApiHandlers
from .forms import ApiError, read_body_dict, truthy
from .pages import PageHandlers
from .render import page as render_page

__all__ = ["CarMonHandler", "create_server", "serve"]


class CarMonHandler(ApiHandlers, PageHandlers, http.server.BaseHTTPRequestHandler):
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

    def do_POST(self) -> None:  # noqa: N802
        self._dispatch("POST")

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
            # Write (mutating) endpoints are POST-only and live in a separate table from the
            # GET routes below -- a GET to e.g. /api/scrapers/run simply is not in the GET
            # table, so it 404s rather than ever reaching a handler that could mutate state.
            handler = self._route_write(path) if method == "POST" else self._route(path, is_api)
            if handler is None:
                if is_api:
                    self._send_json({"error": "not found"}, status=404)
                else:
                    self._send_html(render_page("Not found", '<div class="empty">404 - page not found.</div>'), status=404)
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
                    render_page("Error", f'<div class="empty">Internal error: {html.escape(str(exc))}</div>'), status=500
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
        if path == "/api/scrapers":
            return self._api_scrapers
        if path == "/api/scrapers/events":
            return self._api_scrapers_events
        if path == "/api/settings":
            return self._api_settings_get
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
            if path == "/scrapers":
                return self._page_scrapers
            if path == "/settings":
                return self._page_settings
            if path.startswith("/listing/"):
                vin = path[len("/listing/"):]
                if vin:
                    return lambda conn, params: self._page_listing_detail(conn, params, vin)
        return None

    def _route_write(self, path: str) -> Optional[Callable[[Any, Dict[str, List[str]]], None]]:
        """POST-only routes -- everything that can mutate config, secrets or trigger real
        outbound scraper requests. Deliberately a separate table from `_route` (GET) so a
        write handler can never be reached by a GET request."""
        routes: Dict[str, Callable[[Any, Dict[str, List[str]]], None]] = {
            "/api/scrapers/run": self._api_scrapers_run,
            "/api/scrapers/probe": self._api_scrapers_probe,
            "/api/scrapers/toggle": self._api_scrapers_toggle,
            "/api/settings": self._api_settings_post,
            "/api/settings/secrets": self._api_settings_secrets_post,
            "/scrapers": self._page_scrapers_post,
            "/settings": self._page_settings_post,
        }
        return routes.get(path)

    # -- response helpers -------------------------------------------------
    def _cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, X-Carmon-Write")

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

    # -- write-request body parsing ---------------------------------------
    def _read_body_dict(self) -> Dict[str, Any]:
        return read_body_dict(self.headers, self.rfile)

    def _check_same_origin(self) -> None:
        """Refuse a write if a browser-supplied Origin/Referer names a different host than
        the one this request was addressed to -- what stops another site's page from
        POSTing to a user's localhost dashboard. A request with neither header (curl, a
        same-origin form submission in most browsers) is not rejected by this check alone."""
        host_header = self.headers.get("Host", "")
        for header_name in ("Origin", "Referer"):
            value = self.headers.get(header_name)
            if not value:
                continue
            netloc = urlsplit(value).netloc
            if netloc and netloc != host_header:
                raise ApiError(403, f"cross-origin write refused ({header_name} '{netloc}' != Host '{host_header}')")

    def _require_write_auth(self, body: Dict[str, Any]) -> None:
        """Every write handler calls this first, with its already-parsed body. Enforces all
        four checks a write must pass:
          (a) the bearer token, when CARMON_API_TOKEN is set;
          (b) writes_allowed() for the address this server is actually bound to;
          (c) an explicit write-intent marker (X-Carmon-Write: 1, or confirm=1 in the body);
          (d) a same-origin Origin/Referer, when either header is present.
        Raises ApiError; touches nothing itself.
        """
        token = get_secret("CARMON_API_TOKEN", env=self._env())
        if token:
            header = self.headers.get("Authorization", "")
            if header != f"Bearer {token}":
                raise ApiError(401, "unauthorized")
        bind_host = self.server.server_address[0] or None
        allowed, reason = writes_allowed(bind_host, token)
        if not allowed:
            raise ApiError(403, reason)
        if self.headers.get("X-Carmon-Write") != "1" and not truthy(body.get("confirm")):
            raise ApiError(
                403,
                "write refused: send an 'X-Carmon-Write: 1' header (fetch/curl) or a "
                "confirm=1 field (form POST) to confirm intent",
            )
        self._check_same_origin()

    def _last_run_str(self, conn: Any) -> Optional[str]:
        runs = db.recent_runs(conn, limit=1)
        if runs:
            return runs[0].get("finished_at") or runs[0].get("started_at")
        return None


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
