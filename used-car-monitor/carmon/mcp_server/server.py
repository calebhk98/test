"""The MCPServer class: JSON-RPC method dispatch plus the per-session state
(config, lazily-opened db connection) every tool handler needs.

Tool schemas live in tools.py, tool implementations in handlers.py, the
'resources/*' methods in resources.py, and the stdio transport/JSON-RPC
envelope in protocol.py -- this module just wires those layers together and
exposes the CLI entry point (`main`) used by `python3 -m carmon.mcp_server`
and by carmon.cli.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, Dict, List, Optional

import carmon
from .. import db as dbmod
from .. import demo as demomod
from ..config import Config, load_config

from . import resources as resourcesmod
from . import tools as toolsmod
from .handlers import TOOL_HANDLERS
from .protocol import (
    INTERNAL_ERROR,
    INVALID_PARAMS,
    INVALID_REQUEST,
    METHOD_NOT_FOUND,
    PROTOCOL_VERSION,
    MCPParamError,
    ToolError,
    error_response,
    result_response,
    serve_stdio,
    text_result,
)


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
            return error_response(None, INVALID_REQUEST, "Request must be a JSON object")

        request_id = message.get("id", None)
        has_id = "id" in message
        method = message.get("method")

        if not isinstance(method, str):
            if has_id:
                return error_response(request_id, INVALID_REQUEST, "Missing or invalid 'method'")
            return None

        params = message.get("params") or {}
        if not isinstance(params, dict):
            if has_id:
                return error_response(request_id, INVALID_PARAMS, "'params' must be an object")
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
                    return error_response(request_id, METHOD_NOT_FOUND, f"Unknown method: {method}")
                return None
        except MCPParamError as exc:
            if has_id:
                return error_response(request_id, INVALID_PARAMS, str(exc))
            return None
        except Exception as exc:  # noqa: BLE001 - last-resort guard, never crash the loop
            if has_id:
                return error_response(request_id, INTERNAL_ERROR, f"Internal error: {exc}")
            return None

        if not has_id:
            # A request with no id (even if not literally 'notifications/*')
            # gets no response per JSON-RPC notification semantics.
            return None
        return result_response(request_id, result)

    # -- method implementations ---------------------------------------------
    def _m_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}, "resources": {}},
            "serverInfo": {"name": "used-car-monitor", "version": carmon.__version__},
        }

    def _m_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"tools": toolsmod.tool_defs()}

    def _m_resources_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"resources": resourcesmod.RESOURCE_DEFS}

    def _m_resources_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        uri = params.get("uri")
        if not isinstance(uri, str) or not uri:
            raise MCPParamError("'uri' is required and must be a string")
        return resourcesmod.read_resource(self, uri)

    def _m_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        if not isinstance(name, str) or not name:
            raise MCPParamError("'name' is required and must be a string")
        arguments = params.get("arguments")
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, dict):
            raise MCPParamError("'arguments' must be an object")

        handler = TOOL_HANDLERS.get(name)
        if handler is None:
            return text_result(f"Unknown tool: {name}", is_error=True, as_json=False)

        try:
            return handler(self, arguments)
        except ToolError as exc:
            return text_result(str(exc), is_error=True, as_json=False)
        except Exception as exc:  # noqa: BLE001
            return text_result(f"Tool '{name}' failed: {exc}", is_error=True, as_json=False)


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
