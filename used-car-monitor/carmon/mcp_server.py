"""Model Context Protocol (MCP) server for the used-car monitor.

Implements the MCP protocol directly as JSON-RPC 2.0 over stdio: one JSON
object per line on stdin, one JSON object per line of response on stdout.
No third-party MCP SDK is used — only the Python standard library.

Usage:
    python3 -m carmon.mcp_server [--config PATH] [--db PATH]

IMPORTANT: stdout is reserved exclusively for JSON-RPC responses. Anything
that might otherwise be printed (logs, tracebacks, debug info) must go to
stderr instead, or it will corrupt the protocol stream.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

import carmon
from . import db as dbmod
from . import scoring as scoringmod
from . import sources as sourcesmod
from .config import Config, load_config

PROTOCOL_VERSION = "2024-11-05"

# --------------------------------------------------------------------------
# JSON-RPC error codes (standard MCP / JSON-RPC 2.0 codes)
# --------------------------------------------------------------------------
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


def _error(request_id: Any, code: int, message: str, data: Any = None) -> Dict[str, Any]:
    err: Dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": err}


def _result(request_id: Any, result: Any) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _text_result(payload: Any, is_error: bool = False, as_json: bool = True) -> Dict[str, Any]:
    """Build an MCP tools/call result with a single text content block."""
    if as_json:
        text = json.dumps(payload, indent=2, default=str)
    else:
        text = str(payload)
    return {"content": [{"type": "text", "text": text}], "isError": is_error}


# --------------------------------------------------------------------------
# Tool schema definitions
# --------------------------------------------------------------------------

def _tool_defs() -> List[Dict[str, Any]]:
    return [
        {
            "name": "search_listings",
            "description": (
                "Search the used-car listings database with filters on make, model, price, "
                "mileage, year, distance, score, CPO status, and free-text query. Returns a "
                "list of matching listings sorted as requested."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "make": {"type": "string", "description": "Exact make match, e.g. 'Toyota' (case-insensitive)."},
                    "model": {"type": "string", "description": "Model prefix match, e.g. 'Corolla' (case-insensitive)."},
                    "max_price": {"type": "integer", "description": "Maximum current price in dollars."},
                    "min_price": {"type": "integer", "description": "Minimum current price in dollars."},
                    "max_mileage": {"type": "integer", "description": "Maximum odometer mileage."},
                    "min_year": {"type": "integer", "description": "Minimum model year."},
                    "max_distance": {"type": "number", "description": "Maximum distance from home in miles."},
                    "min_score": {"type": "number", "description": "Minimum computed score."},
                    "cpo_only": {"type": "boolean", "description": "If true, only Certified Pre-Owned listings.", "default": False},
                    "active_only": {"type": "boolean", "description": "If true (default), only currently active listings.", "default": True},
                    "query": {"type": "string", "description": "Free-text search across make, model, trim, dealer name, and VIN."},
                    "sort": {
                        "type": "string",
                        "description": "Sort order for results.",
                        "enum": ["score", "price", "price_desc", "mileage", "distance", "year", "first_seen", "last_seen"],
                        "default": "score",
                    },
                    "limit": {"type": "integer", "description": "Max number of results to return (default 20, max 100).", "default": 20, "minimum": 1, "maximum": 100},
                    "offset": {"type": "integer", "description": "Number of results to skip, for pagination.", "default": 0, "minimum": 0},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "get_listing",
            "description": (
                "Fetch a single listing by VIN, including its price history and cross-shopping "
                "links to other sites where the same car could be searched for."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "vin": {"type": "string", "description": "The vehicle's VIN (unique identifier)."},
                },
                "required": ["vin"],
                "additionalProperties": False,
            },
        },
        {
            "name": "get_price_history",
            "description": "Get the recorded price/mileage history for a listing by VIN, oldest first.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "vin": {"type": "string", "description": "The vehicle's VIN."},
                },
                "required": ["vin"],
                "additionalProperties": False,
            },
        },
        {
            "name": "top_listings",
            "description": "Return the best-scoring currently-active listings, highest score first.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Number of listings to return (default 5).", "default": 5, "minimum": 1, "maximum": 100},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "new_listings",
            "description": "Return active listings first seen within the last N days, best score first.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "How many days back to look (default 1).", "default": 1, "minimum": 1},
                    "limit": {"type": "integer", "description": "Max number of results (default 50).", "default": 50, "minimum": 1, "maximum": 500},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "price_drops",
            "description": "Return active listings whose price dropped within the last N days, biggest drop first.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "How many days back to look (default 1).", "default": 1, "minimum": 1},
                    "limit": {"type": "integer", "description": "Max number of results (default 50).", "default": 50, "minimum": 1, "maximum": 500},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "get_stats",
            "description": (
                "Get database summary statistics (listing counts, average/min price, best "
                "score) plus MarketCheck API quota usage for the current month."
            ),
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "get_latest_digest",
            "description": (
                "Return the full markdown text of the most recently generated daily digest, "
                "or a clear message if no digest has been generated yet."
            ),
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "explain_score",
            "description": (
                "Explain why a specific listing (by VIN) received its score: returns both the "
                "score breakdown stored in the database and a freshly recomputed explanation "
                "using the current scoring configuration."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "vin": {"type": "string", "description": "The vehicle's VIN."},
                },
                "required": ["vin"],
                "additionalProperties": False,
            },
        },
        {
            "name": "score_hypothetical",
            "description": (
                "Score a hypothetical car that is not (yet) in the database, using the current "
                "scoring configuration. Useful for questions like 'would a 2022 Civic with "
                "45k miles, 70 miles away, score well?'."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "make": {"type": "string", "description": "Vehicle make, e.g. 'Honda'."},
                    "model": {"type": "string", "description": "Vehicle model, e.g. 'Civic'."},
                    "mileage": {"type": "integer", "description": "Odometer mileage."},
                    "distance_miles": {"type": "number", "description": "Distance from home in miles."},
                    "price_current": {"type": "integer", "description": "Current asking price in dollars."},
                    "price_first_seen": {"type": "integer", "description": "Original asking price in dollars, if different from price_current (for price-drop scoring)."},
                    "cpo": {"type": "boolean", "description": "Whether the vehicle is Certified Pre-Owned.", "default": False},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "list_sources",
            "description": (
                "List cross-shopping deep links to other places to run the same search "
                "(manufacturer CPO programs, big retailers, marketplace aggregators), grouped "
                "by category, built from the current search configuration."
            ),
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    ]


def _resources_list() -> List[Dict[str, Any]]:
    return [
        {
            "uri": "carmon://config",
            "name": "Configuration",
            "description": "The active carmon configuration (search/scoring/api/digest/paths settings) as JSON.",
            "mimeType": "application/json",
        },
        {
            "uri": "carmon://digest/latest",
            "name": "Latest digest",
            "description": "The most recently generated daily digest, as markdown.",
            "mimeType": "text/markdown",
        },
    ]


# --------------------------------------------------------------------------
# Server
# --------------------------------------------------------------------------

class MCPServer:
    """Holds config/db state and dispatches JSON-RPC requests to handlers."""

    def __init__(self, config: Config):
        self.config = config
        self._conn = None

    @property
    def conn(self):
        if self._conn is None:
            self._conn = dbmod.connect(self.config.db_path)
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    # -- top-level dispatch -------------------------------------------------
    def handle_request(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle one parsed JSON-RPC message. Returns a response dict, or None
        if the message was a notification (no 'id') and requires no reply."""
        if not isinstance(message, dict):
            return _error(None, INVALID_REQUEST, "Request must be a JSON object")

        request_id = message.get("id", None)
        has_id = "id" in message
        method = message.get("method")

        if not isinstance(method, str):
            if has_id:
                return _error(request_id, INVALID_REQUEST, "Missing or invalid 'method'")
            return None

        params = message.get("params") or {}
        if not isinstance(params, dict):
            if has_id:
                return _error(request_id, INVALID_PARAMS, "'params' must be an object")
            return None

        try:
            if method == "initialize":
                result = self._m_initialize(params)
            elif method == "notifications/initialized":
                return None
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = self._m_tools_list(params)
            elif method == "tools/call":
                result = self._m_tools_call(params)
            elif method == "resources/list":
                result = self._m_resources_list(params)
            elif method == "resources/read":
                result = self._m_resources_read(params)
            elif method == "shutdown":
                result = {}
            else:
                if has_id:
                    return _error(request_id, METHOD_NOT_FOUND, f"Unknown method: {method}")
                return None
        except MCPParamError as exc:
            if has_id:
                return _error(request_id, INVALID_PARAMS, str(exc))
            return None
        except Exception as exc:  # noqa: BLE001 - last-resort guard, never crash the loop
            if has_id:
                return _error(request_id, INTERNAL_ERROR, f"Internal error: {exc}")
            return None

        if not has_id:
            # A request with no id (even if not literally 'notifications/*')
            # gets no response per JSON-RPC notification semantics.
            return None
        return _result(request_id, result)

    # -- method implementations ---------------------------------------------
    def _m_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}, "resources": {}},
            "serverInfo": {"name": "used-car-monitor", "version": carmon.__version__},
        }

    def _m_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"tools": _tool_defs()}

    def _m_resources_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"resources": _resources_list()}

    def _m_resources_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        uri = params.get("uri")
        if not isinstance(uri, str) or not uri:
            raise MCPParamError("'uri' is required and must be a string")

        if uri == "carmon://config":
            text = json.dumps(self.config.to_dict(), indent=2, default=str)
            return {"contents": [{"uri": uri, "mimeType": "application/json", "text": text}]}

        if uri == "carmon://digest/latest":
            text = self._latest_digest_text()
            return {"contents": [{"uri": uri, "mimeType": "text/markdown", "text": text}]}

        raise MCPParamError(f"Unknown resource uri: {uri}")

    def _m_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        if not isinstance(name, str) or not name:
            raise MCPParamError("'name' is required and must be a string")
        arguments = params.get("arguments")
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, dict):
            raise MCPParamError("'arguments' must be an object")

        handler = self._TOOL_HANDLERS.get(name)
        if handler is None:
            return _text_result(f"Unknown tool: {name}", is_error=True, as_json=False)

        try:
            return handler(self, arguments)
        except ToolError as exc:
            return _text_result(str(exc), is_error=True, as_json=False)
        except Exception as exc:  # noqa: BLE001
            return _text_result(f"Tool '{name}' failed: {exc}", is_error=True, as_json=False)

    # -- tool implementations -------------------------------------------
    def _t_search_listings(self, args: Dict[str, Any]) -> Dict[str, Any]:
        limit = _as_int(args.get("limit", 20), "limit", default=20)
        limit = max(1, min(limit, 100))
        offset = _as_int(args.get("offset", 0), "offset", default=0)
        sort = args.get("sort", "score") or "score"
        if sort not in dbmod.SORTABLE:
            raise ToolError(
                f"Invalid sort '{sort}'. Must be one of: {', '.join(sorted(dbmod.SORTABLE))}"
            )
        rows = dbmod.search_listings(
            self.conn,
            make=args.get("make") or None,
            model=args.get("model") or None,
            max_price=_opt_int(args.get("max_price")),
            min_price=_opt_int(args.get("min_price")),
            max_mileage=_opt_int(args.get("max_mileage")),
            min_year=_opt_int(args.get("min_year")),
            max_distance=_opt_float(args.get("max_distance")),
            min_score=_opt_float(args.get("min_score")),
            cpo_only=bool(args.get("cpo_only", False)),
            active_only=bool(args.get("active_only", True)),
            query=args.get("query") or None,
            sort=sort,
            limit=limit,
            offset=offset,
        )
        return _text_result({"count": len(rows), "listings": rows})

    def _t_get_listing(self, args: Dict[str, Any]) -> Dict[str, Any]:
        vin = _require_str(args, "vin")
        listing = dbmod.get_listing(self.conn, vin)
        if listing is None:
            return _text_result(f"No listing found with VIN '{vin}'.", is_error=True, as_json=False)
        history = dbmod.get_price_history(self.conn, vin)
        cross_shop = sourcesmod.sources_for_listing(listing, self.config.search)
        return _text_result({
            "listing": listing,
            "price_history": history,
            "cross_shop_links": cross_shop,
        })

    def _t_get_price_history(self, args: Dict[str, Any]) -> Dict[str, Any]:
        vin = _require_str(args, "vin")
        listing = dbmod.get_listing(self.conn, vin)
        if listing is None:
            return _text_result(f"No listing found with VIN '{vin}'.", is_error=True, as_json=False)
        history = dbmod.get_price_history(self.conn, vin)
        return _text_result({"vin": vin, "price_history": history})

    def _t_top_listings(self, args: Dict[str, Any]) -> Dict[str, Any]:
        limit = _as_int(args.get("limit", 5), "limit", default=5)
        limit = max(1, min(limit, 100))
        rows = dbmod.search_listings(self.conn, active_only=True, sort="score", limit=limit)
        return _text_result({"count": len(rows), "listings": rows})

    def _t_new_listings(self, args: Dict[str, Any]) -> Dict[str, Any]:
        days = _as_int(args.get("days", 1), "days", default=1)
        days = max(1, days)
        limit = _as_int(args.get("limit", 50), "limit", default=50)
        limit = max(1, min(limit, 500))
        since = _days_ago_str(days)
        rows = dbmod.new_listings_since(self.conn, since, limit=limit)
        return _text_result({"since": since, "count": len(rows), "listings": rows})

    def _t_price_drops(self, args: Dict[str, Any]) -> Dict[str, Any]:
        days = _as_int(args.get("days", 1), "days", default=1)
        days = max(1, days)
        limit = _as_int(args.get("limit", 50), "limit", default=50)
        limit = max(1, min(limit, 500))
        since = _days_ago_str(days)
        rows = dbmod.price_drops_since(self.conn, since, limit=limit)
        return _text_result({"since": since, "count": len(rows), "listings": rows})

    def _t_get_stats(self, args: Dict[str, Any]) -> Dict[str, Any]:
        monthly_cap = int(self.config.api.get("monthly_call_cap", 500) or 500)
        result = dbmod.stats(self.conn, monthly_cap=monthly_cap)
        return _text_result(result)

    def _t_get_latest_digest(self, args: Dict[str, Any]) -> Dict[str, Any]:
        text = self._latest_digest_text()
        is_error = text.startswith("No digest")
        return _text_result(text, is_error=is_error, as_json=False)

    def _t_explain_score(self, args: Dict[str, Any]) -> Dict[str, Any]:
        vin = _require_str(args, "vin")
        listing = dbmod.get_listing(self.conn, vin)
        if listing is None:
            return _text_result(f"No listing found with VIN '{vin}'.", is_error=True, as_json=False)
        recomputed = scoringmod.score_listing(listing, self.config.scoring)
        return _text_result({
            "vin": vin,
            "stored_score": listing.get("score"),
            "stored_breakdown": listing.get("score_breakdown"),
            "recomputed": recomputed.as_dict(),
            "explanation": recomputed.explain(),
        })

    def _t_score_hypothetical(self, args: Dict[str, Any]) -> Dict[str, Any]:
        listing = {
            "make": args.get("make") or "",
            "model": args.get("model") or "",
            "mileage": _opt_number(args.get("mileage")),
            "distance_miles": _opt_number(args.get("distance_miles")),
            "price_current": _opt_number(args.get("price_current")),
            "price_first_seen": _opt_number(args.get("price_first_seen")),
            "cpo": bool(args.get("cpo", False)),
        }
        result = scoringmod.score_listing(listing, self.config.scoring)
        return _text_result({
            "input": listing,
            "result": result.as_dict(),
            "explanation": result.explain(),
        })

    def _t_list_sources(self, args: Dict[str, Any]) -> Dict[str, Any]:
        grouped = sourcesmod.grouped_sources(self.config.search)
        return _text_result({"sources": grouped})

    _TOOL_HANDLERS = {
        "search_listings": _t_search_listings,
        "get_listing": _t_get_listing,
        "get_price_history": _t_get_price_history,
        "top_listings": _t_top_listings,
        "new_listings": _t_new_listings,
        "price_drops": _t_price_drops,
        "get_stats": _t_get_stats,
        "get_latest_digest": _t_get_latest_digest,
        "explain_score": _t_explain_score,
        "score_hypothetical": _t_score_hypothetical,
        "list_sources": _t_list_sources,
    }

    # -- helpers -----------------------------------------------------------
    def _latest_digest_text(self) -> str:
        try:
            from .digest import latest_digest_path  # lazy import: digest.py may not exist yet
        except ImportError:
            return "No digest yet: the digest module is not available."
        try:
            path = latest_digest_path(self.config)
        except Exception as exc:  # noqa: BLE001
            return f"No digest yet: could not determine latest digest ({exc})."
        if not path:
            return "No digest yet: no digest has been generated."
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            return f"No digest yet: could not read digest file {path} ({exc})."


class MCPParamError(ValueError):
    """Raised for malformed top-level JSON-RPC params -> maps to -32602."""


class ToolError(ValueError):
    """Raised inside a tool handler for a user-facing error -> isError result."""


def _require_str(args: Dict[str, Any], key: str) -> str:
    value = args.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ToolError(f"'{key}' is required and must be a non-empty string")
    return value.strip()


def _as_int(value: Any, name: str, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ToolError(f"'{name}' must be an integer")


def _opt_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    return int(value)


def _opt_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    return float(value)


def _opt_number(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _days_ago_str(days: int) -> str:
    from datetime import date, timedelta

    return (date.today() - timedelta(days=days)).isoformat()


# --------------------------------------------------------------------------
# stdio loop
# --------------------------------------------------------------------------

def _write_message(out, message: Dict[str, Any]) -> None:
    out.write(json.dumps(message, default=str))
    out.write("\n")
    out.flush()


def serve_stdio(server: MCPServer, stdin=None, stdout=None) -> None:
    """Read JSON-RPC requests line-by-line from stdin, write responses to stdout.

    Exits cleanly on EOF. Blank lines are ignored. Malformed JSON produces a
    parse-error response (id null) rather than crashing the loop.
    """
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    for raw_line in stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            _write_message(stdout, _error(None, PARSE_ERROR, f"Parse error: {exc}"))
            continue
        response = server.handle_request(message)
        if response is not None:
            _write_message(stdout, response)


def build_server(config_path: Optional[str], db_path: Optional[str]) -> MCPServer:
    config = load_config(config_path)
    if db_path:
        config.paths["db"] = db_path
    return MCPServer(config)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="carmon.mcp_server",
        description="Used Car Monitor MCP server (JSON-RPC 2.0 over stdio).",
    )
    parser.add_argument("--config", dest="config", default=None, help="Path to config.json")
    parser.add_argument("--db", dest="db", default=None, help="Path to the sqlite DB (overrides config)")
    args = parser.parse_args(argv)

    server = build_server(args.config, args.db)
    try:
        serve_stdio(server)
    finally:
        server.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
