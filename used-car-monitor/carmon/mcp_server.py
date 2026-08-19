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
from . import demo as demomod
from . import quota as quotamod
from . import scoring as scoringmod
from . import sources as sourcesmod
from .config import Config, load_config

PROTOCOL_VERSION = "2024-11-05"

# Appended to the description of any tool whose results can include seeded demo rows.
DEMO_WARNING_NOTE = (
    " If any returned listing is seeded demo data (source 'demo'), the JSON payload "
    "carries a top-level 'warning' field with details. Demo rows are fake and must "
    "never be reported to the user as real cars for sale."
)

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
                "mileage, year, distance, score, CPO status, free-text query, and cached NHTSA "
                "complaint/recall counts (max_complaints, max_recalls — free federal data, raw "
                "and not sales-volume adjusted; listings with no cached NHTSA data are kept, "
                "never excluded, since unknown is not the same as bad). Returns a list of "
                "matching listings sorted as requested." + DEMO_WARNING_NOTE
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
                    "max_complaints": {
                        "type": "integer",
                        "description": (
                            "Only include listings whose model year has at most this many cached NHTSA "
                            "consumer complaints (free federal data, raw counts, NOT sales-volume "
                            "adjusted). Applied as a post-filter over the cached reliability data. "
                            "Listings with no cached NHTSA data are KEPT, not excluded — unknown is not "
                            "treated as bad. Use 'refresh_reliability' first if a model you care about "
                            "has never been looked up."
                        ),
                    },
                    "max_recalls": {
                        "type": "integer",
                        "description": (
                            "Only include listings whose model year has at most this many cached NHTSA "
                            "recall campaigns (free federal data). Listings with no cached NHTSA data "
                            "are KEPT, not excluded — unknown is not treated as bad."
                        ),
                    },
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
                "Fetch a single listing by VIN, including its price history, cross-shopping "
                "links to other sites where the same car could be searched for, and any cached "
                "NHTSA reliability data (consumer complaint / recall counts, free federal data — "
                "raw and NOT sales-volume adjusted) and EPA MPG for its model year. Also returns "
                "nhtsa_vin_url and nhtsa_model_url, direct NHTSA.gov links for a human to check "
                "unrepaired recalls on this exact VIN." + DEMO_WARNING_NOTE
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
            "description": (
                "Return the best-scoring currently-active listings, highest score first."
                + DEMO_WARNING_NOTE
            ),
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
            "description": (
                "Return active listings first seen within the last N days, best score first."
                + DEMO_WARNING_NOTE
            ),
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
            "description": (
                "Return active listings whose price dropped within the last N days, biggest "
                "drop first." + DEMO_WARNING_NOTE
            ),
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
                "score) plus MarketCheck API quota usage for the current month. The quota "
                "numbers come with pace context under a 'pace' key (used vs. expected_by_now, "
                "pace_ratio, pace_label) — see 'get_quota_pace' for the full breakdown and a "
                "text gauge. Also reports demo_listings and demo_warning: if demo_listings is "
                "greater than 0, some stored listings are seeded demo data, not real cars, and "
                "demo_warning explains it."
            ),
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "get_quota_pace",
            "description": (
                "How to judge whether MarketCheck API quota use is comfortable this month. "
                "100 calls used by the 15th of the month is relaxed; 100 calls by the 5th is "
                "not — this tool turns the raw monthly call counter into that comparison. "
                "Compare 'used' against 'expected_by_now' (what a perfectly even pace would "
                "have used by today), and read 'pace_ratio': below 1.0 means quota is being "
                "used more slowly than the month is passing, 1.0 means exactly on pace, above "
                "1.0 means running ahead of pace. 'pace_label' and 'pace_icon' give a "
                "human-readable read (e.g. 'well under pace'), 'projected_month_total' "
                "extrapolates the current rate to month-end, and 'affordable_per_day' is how "
                "many more calls/day are still sustainable without exceeding the cap. Also "
                "includes 'summary' (one-line text), 'bar' (a text gauge), and "
                "'month_end_sweep' (whether today is the last-day sweep window that spends "
                "down unused calls before they expire worthless). This is purely "
                "informational and advisory — nothing here limits anything; the only hard "
                "stop on API usage is the monthly cap itself, enforced elsewhere."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "width": {
                        "type": "integer",
                        "description": "Character width of the returned text gauge 'bar' (default 24).",
                        "default": 24,
                        "minimum": 4,
                    },
                },
                "additionalProperties": False,
            },
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
                "using the current scoring configuration. The recomputed explanation attaches "
                "cached fuel-economy and NHTSA reliability data (free federal complaint/recall "
                "data, raw counts, not sales-volume adjusted) first, so its 'fuel economy', "
                "'NHTSA complaints', and 'NHTSA recalls' components reflect real data instead "
                "of showing as unknown."
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
                "45k miles, 70 miles away, score well?' or for modeling a car end-to-end with "
                "known fuel economy and NHTSA reliability figures (complaint/recall counts are "
                "free federal data — raw counts, NOT adjusted for sales volume, so pass them "
                "only if you already have them, e.g. from 'get_reliability')."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "make": {"type": "string", "description": "Vehicle make, e.g. 'Honda'."},
                    "model": {"type": "string", "description": "Vehicle model, e.g. 'Civic'."},
                    "year": {"type": "integer", "description": "Model year, e.g. 2022. Used for the 'model year' scoring component."},
                    "mileage": {"type": "integer", "description": "Odometer mileage."},
                    "distance_miles": {"type": "number", "description": "Distance from home in miles."},
                    "price_current": {"type": "integer", "description": "Current asking price in dollars."},
                    "price_first_seen": {"type": "integer", "description": "Original asking price in dollars, if different from price_current (for price-drop scoring)."},
                    "cpo": {"type": "boolean", "description": "Whether the vehicle is Certified Pre-Owned.", "default": False},
                    "combined_mpg": {"type": "number", "description": "EPA combined miles per gallon, if known, for the 'fuel economy' scoring component."},
                    "complaint_count": {
                        "type": "integer",
                        "description": (
                            "Cached NHTSA consumer complaint count for this model year, if known "
                            "(free federal data, raw count, not sales-volume adjusted), for the "
                            "'NHTSA complaints' scoring component."
                        ),
                    },
                    "recall_count": {
                        "type": "integer",
                        "description": (
                            "Cached NHTSA recall campaign count for this model year, if known "
                            "(free federal data), for the 'NHTSA recalls' scoring component."
                        ),
                    },
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
        {
            "name": "get_reliability",
            "description": (
                "Look up cached NHTSA reliability data for one make/model/year: consumer-filed "
                "defect complaints and manufacturer recall campaigns. This is free federal data "
                "from api.nhtsa.gov (no API key, no cost) — the same data every third-party "
                "reliability site repackages. Complaint and recall counts are RAW totals, NOT "
                "adjusted for how many of that model were sold, so a high-volume model naturally "
                "racks up more complaints than a rare one; the recurring complaint *components* "
                "(top_components) are a stronger signal than the raw count. This tool only reads "
                "what is already cached in the database and never hits the network — if nothing "
                "is cached yet it returns an error telling you to run `python3 -m carmon enrich` "
                "or call the 'refresh_reliability' tool."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "make": {"type": "string", "description": "Vehicle make, e.g. 'Honda'."},
                    "model": {"type": "string", "description": "Vehicle model, e.g. 'Civic'."},
                    "year": {"type": "integer", "description": "Model year, e.g. 2022."},
                },
                "required": ["make", "model", "year"],
                "additionalProperties": False,
            },
        },
        {
            "name": "refresh_reliability",
            "description": (
                "Fetch fresh NHTSA consumer complaint and recall data for one make/model/year "
                "directly from api.nhtsa.gov (free federal data, no API key needed) and cache it "
                "in the database. This is the ONLY tool on this server that makes a live network "
                "call — every other tool reads the local database. Complaint and recall counts "
                "returned are RAW totals, NOT adjusted for sales volume, so a high-volume model "
                "naturally shows more complaints than a rare one; the recurring complaint "
                "components are the stronger signal. Prefer calling 'get_reliability' first to "
                "check whether the data is already cached before spending a network call here."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "make": {"type": "string", "description": "Vehicle make, e.g. 'Honda'."},
                    "model": {"type": "string", "description": "Vehicle model, e.g. 'Civic'."},
                    "year": {"type": "integer", "description": "Model year, e.g. 2022."},
                    "force": {
                        "type": "boolean",
                        "description": "Refetch from NHTSA even if a still-fresh cached entry already exists.",
                        "default": False,
                    },
                },
                "required": ["make", "model", "year"],
                "additionalProperties": False,
            },
        },
        {
            "name": "list_reliability",
            "description": (
                "List every make/model/year currently cached with NHTSA reliability data (free "
                "federal consumer complaint and recall data from api.nhtsa.gov), sorted by "
                "complaint count descending. Counts are raw and NOT adjusted for sales volume, "
                "so this is a 'what has been looked up, and how loud is it' view rather than a "
                "ranked reliability score — check top_components on each row for the recurring, "
                "more meaningful signal."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Max number of cached model/year rows to return (default 25).",
                        "default": 25,
                        "minimum": 1,
                        "maximum": 500,
                    },
                },
                "additionalProperties": False,
            },
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
            # Cheap no-op when there is no demo data; keeps demo rows from quietly
            # outliving their welcome across a long-running MCP session.
            demomod.maybe_expire(self._conn, self.config)
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
        max_complaints = _opt_int(args.get("max_complaints"))
        max_recalls = _opt_int(args.get("max_recalls"))
        # Fetch a bit more than requested when post-filtering by NHTSA data, since some
        # rows may be dropped; db-level limit/offset still apply to the base query.
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
        if max_complaints is not None or max_recalls is not None:
            filtered = []
            for row in rows:
                row = self._attach_enrichment(row)
                complaints = row.get("complaint_count")
                recalls = row.get("recall_count")
                # No cached NHTSA data (None) means "unknown", which is kept rather
                # than excluded — unknown is not the same as bad.
                if max_complaints is not None and complaints is not None and complaints > max_complaints:
                    continue
                if max_recalls is not None and recalls is not None and recalls > max_recalls:
                    continue
                filtered.append(row)
            rows = filtered
        return _text_result(self._with_demo_warning({"count": len(rows), "listings": rows}, rows))

    def _t_get_listing(self, args: Dict[str, Any]) -> Dict[str, Any]:
        vin = _require_str(args, "vin")
        listing = dbmod.get_listing(self.conn, vin)
        if listing is None:
            return _text_result(f"No listing found with VIN '{vin}'.", is_error=True, as_json=False)
        listing = self._attach_enrichment(listing)
        history = dbmod.get_price_history(self.conn, vin)
        cross_shop = sourcesmod.sources_for_listing(listing, self.config.search)
        nhtsa_vin_url = None
        nhtsa_model_url = None
        try:
            from .nhtsa import recall_lookup_url, vin_recall_url  # lazy: keeps module load light
        except ImportError:
            pass
        else:
            nhtsa_vin_url = vin_recall_url(vin)
            if listing.get("make") and listing.get("model") and listing.get("year"):
                nhtsa_model_url = recall_lookup_url(listing["make"], listing["model"], listing["year"])
        return _text_result(self._with_demo_warning({
            "listing": listing,
            "price_history": history,
            "cross_shop_links": cross_shop,
            "nhtsa_vin_url": nhtsa_vin_url,
            "nhtsa_model_url": nhtsa_model_url,
        }, [listing]))

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
        return _text_result(self._with_demo_warning({"count": len(rows), "listings": rows}, rows))

    def _t_new_listings(self, args: Dict[str, Any]) -> Dict[str, Any]:
        days = _as_int(args.get("days", 1), "days", default=1)
        days = max(1, days)
        limit = _as_int(args.get("limit", 50), "limit", default=50)
        limit = max(1, min(limit, 500))
        since = _days_ago_str(days)
        rows = dbmod.new_listings_since(self.conn, since, limit=limit)
        return _text_result(self._with_demo_warning({"since": since, "count": len(rows), "listings": rows}, rows))

    def _t_price_drops(self, args: Dict[str, Any]) -> Dict[str, Any]:
        days = _as_int(args.get("days", 1), "days", default=1)
        days = max(1, days)
        limit = _as_int(args.get("limit", 50), "limit", default=50)
        limit = max(1, min(limit, 500))
        since = _days_ago_str(days)
        rows = dbmod.price_drops_since(self.conn, since, limit=limit)
        return _text_result(self._with_demo_warning({"since": since, "count": len(rows), "listings": rows}, rows))

    def _t_get_stats(self, args: Dict[str, Any]) -> Dict[str, Any]:
        monthly_cap = int(self.config.api.get("monthly_call_cap", 500) or 500)
        result = dbmod.stats(self.conn, monthly_cap=monthly_cap)
        result["pace"] = quotamod.pace(result["api_calls_this_month"], monthly_cap)
        result["demo_listings"] = demomod.demo_count(self.conn)
        result["demo_warning"] = demomod.demo_banner(self.conn)
        return _text_result(result)

    def _t_get_quota_pace(self, args: Dict[str, Any]) -> Dict[str, Any]:
        width = _as_int(args.get("width", 24), "width", default=24)
        width = max(4, width)
        monthly_cap = int(self.config.api.get("monthly_call_cap", 500) or 500)
        metrics = quotamod.pace_from_db(self.conn, monthly_cap)
        sweep_config = self.config.data.get("api", {}).get("month_end_sweep", {})
        result = dict(metrics)
        result["summary"] = quotamod.summary_line(metrics)
        result["bar"] = quotamod.bar(metrics, width=width)
        result["month_end_sweep"] = quotamod.sweep_budget(
            metrics["used"], metrics["cap"], sweep_config
        )
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
        listing = self._attach_enrichment(listing)
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
            "year": _opt_int(args.get("year")),
            "mileage": _opt_number(args.get("mileage")),
            "distance_miles": _opt_number(args.get("distance_miles")),
            "price_current": _opt_number(args.get("price_current")),
            "price_first_seen": _opt_number(args.get("price_first_seen")),
            "cpo": bool(args.get("cpo", False)),
            "combined_mpg": _opt_number(args.get("combined_mpg")),
            "complaint_count": _opt_int(args.get("complaint_count")),
            "recall_count": _opt_int(args.get("recall_count")),
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

    def _t_get_reliability(self, args: Dict[str, Any]) -> Dict[str, Any]:
        make = _require_str(args, "make")
        model = _require_str(args, "model")
        year = _require_int(args, "year")
        record = dbmod.get_reliability(self.conn, make, model, year)
        if record is None:
            return _text_result(
                f"No cached NHTSA reliability data for {year} {make} {model}. Run "
                "`python3 -m carmon enrich` to populate the cache for current listings, or "
                "call the 'refresh_reliability' tool to fetch just this model/year now.",
                is_error=True,
                as_json=False,
            )
        record = dict(record)
        record["nhtsa_url"] = self._nhtsa_model_url(make, model, year)
        record["caveat"] = (
            "Complaint and recall counts are raw federal totals from NHTSA, NOT adjusted for "
            "how many of this model were sold — a high-volume model naturally accumulates more "
            "complaints than a rare one. The recurring complaint components (top_components) "
            "are a stronger signal than the raw counts."
        )
        return _text_result(record)

    def _t_refresh_reliability(self, args: Dict[str, Any]) -> Dict[str, Any]:
        make = _require_str(args, "make")
        model = _require_str(args, "model")
        year = _require_int(args, "year")
        force = bool(args.get("force", False))
        try:
            from .nhtsa import NHTSAClient, NHTSAError  # lazy: this is the one network-calling tool
        except ImportError as exc:
            return _text_result(f"NHTSA client is not available: {exc}", is_error=True, as_json=False)

        enrichment_config = self.config.data.get("enrichment", {})
        client = NHTSAClient(self.conn, enrichment_config)
        try:
            facts = client.facts_for(make, model, year, force_refresh=force)
        except NHTSAError as exc:
            return _text_result(
                f"NHTSA lookup failed for {year} {make} {model}: {exc}", is_error=True, as_json=False
            )
        except Exception as exc:  # noqa: BLE001 - network calls can fail in many ways
            return _text_result(
                f"NHTSA lookup failed for {year} {make} {model}: {exc}", is_error=True, as_json=False
            )
        if facts is None:
            return _text_result(
                f"Could not fetch NHTSA data for {year} {make} {model}: the request failed and "
                "nothing was already cached.",
                is_error=True,
                as_json=False,
            )
        result = dict(facts)
        result["nhtsa_url"] = self._nhtsa_model_url(make, model, year)
        result["api_calls_made"] = client.calls_made
        return _text_result(result)

    def _t_list_reliability(self, args: Dict[str, Any]) -> Dict[str, Any]:
        limit = _as_int(args.get("limit", 25), "limit", default=25)
        limit = max(1, min(limit, 500))
        rows = self.conn.execute(
            "SELECT * FROM model_reliability ORDER BY complaint_count DESC LIMIT ?", (limit,)
        ).fetchall()
        models = [self._reliability_row_to_dict(row) for row in rows]
        return _text_result({"count": len(models), "models": models})

    _TOOL_HANDLERS = {
        "search_listings": _t_search_listings,
        "get_listing": _t_get_listing,
        "get_price_history": _t_get_price_history,
        "top_listings": _t_top_listings,
        "new_listings": _t_new_listings,
        "price_drops": _t_price_drops,
        "get_stats": _t_get_stats,
        "get_quota_pace": _t_get_quota_pace,
        "get_latest_digest": _t_get_latest_digest,
        "explain_score": _t_explain_score,
        "score_hypothetical": _t_score_hypothetical,
        "list_sources": _t_list_sources,
        "get_reliability": _t_get_reliability,
        "refresh_reliability": _t_refresh_reliability,
        "list_reliability": _t_list_reliability,
    }

    # -- helpers -----------------------------------------------------------
    def _with_demo_warning(self, payload: Dict[str, Any], listings: List[Optional[Dict[str, Any]]]) -> Dict[str, Any]:
        """Add a top-level 'warning' key when any of the given listings is demo data.

        Does not set isError: the data is still returned, it is just flagged so an
        assistant never presents seeded demo rows as real cars.
        """
        if any(listing and listing.get("source") == demomod.DEMO_SOURCE for listing in listings):
            payload["warning"] = demomod.demo_banner(self.conn)
        return payload

    def _attach_enrichment(self, listing: Dict[str, Any]) -> Dict[str, Any]:
        """Attach cached NHTSA/EPA facts to a listing dict, DB-only, never the network."""
        try:
            from .pipeline import attach_cached_enrichment  # lazy: optional heavier dependency chain
        except ImportError:
            return listing
        try:
            return attach_cached_enrichment(self.conn, listing)
        except Exception:  # noqa: BLE001 - enrichment is a bonus, never fail the tool over it
            return listing

    def _nhtsa_model_url(self, make: str, model: str, year: int) -> Optional[str]:
        try:
            from .nhtsa import recall_lookup_url  # lazy: same optional dependency chain
        except ImportError:
            return None
        return recall_lookup_url(make, model, year)

    def _reliability_row_to_dict(self, row: Any) -> Dict[str, Any]:
        data = dict(row)
        for field_name in ("top_components", "recalls"):
            if isinstance(data.get(field_name), str) and data[field_name]:
                try:
                    data[field_name] = json.loads(data[field_name])
                except json.JSONDecodeError:
                    data[field_name] = None
        return data

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


def _require_int(args: Dict[str, Any], key: str) -> int:
    value = args.get(key)
    if value is None or value == "":
        raise ToolError(f"'{key}' is required and must be an integer")
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ToolError(f"'{key}' must be an integer")


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
