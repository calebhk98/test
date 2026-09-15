"""Model Context Protocol (MCP) server for the used-car monitor.

Implements the MCP protocol directly as JSON-RPC 2.0 over stdio: one JSON
object per line on stdin, one JSON object per line of response on stdout.
No third-party MCP SDK is used — only the Python standard library.

Usage:
    python3 -m carmon.mcp_server [--config PATH] [--db PATH]

IMPORTANT: stdout is reserved exclusively for JSON-RPC responses. Anything
that might otherwise be printed (logs, tracebacks, debug info) must go to
stderr instead, or it will corrupt the protocol stream.

This used to be a single ~1400-line module; it is now a package split by
layer:

    protocol.py   JSON-RPC 2.0 framing: error codes, envelope builders, the
                  stdio request loop.
    schema.py     JSON Schema building blocks + the shared caveat notes
                  appended to several tool descriptions.
    tools.py      The 25 tool schema definitions (tools/list).
    params.py     Argument extraction/validation/clamping helpers.
    imports.py    Lazy-import helpers for optional dependency chains.
    handlers.py   The 25 tool implementations (tools/call), dispatched by
                  name via TOOL_HANDLERS.
    resources.py  The 'resources/*' methods (carmon://config, .../digest).
    server.py     MCPServer: ties config/db state to the dispatch table,
                  plus build_server/main for the CLI entry point.

Everything a caller previously reached for on the flat module is re-exported
here, so `from carmon.mcp_server import MCPServer` (and
`from carmon.mcp_server import main`) keep working unchanged.
"""

from __future__ import annotations

from .protocol import (
    INTERNAL_ERROR,
    INVALID_PARAMS,
    INVALID_REQUEST,
    METHOD_NOT_FOUND,
    PARSE_ERROR,
    PROTOCOL_VERSION,
    MCPParamError,
    ToolError,
    serve_stdio,
)
from .schema import APPRAISAL_CAVEAT_NOTE, DEMO_WARNING_NOTE, SCRAPER_BLOCKED_NOTE
from .server import MCPServer, build_server, main

__all__ = [
    "MCPServer",
    "MCPParamError",
    "ToolError",
    "PROTOCOL_VERSION",
    "PARSE_ERROR",
    "INVALID_REQUEST",
    "METHOD_NOT_FOUND",
    "INVALID_PARAMS",
    "INTERNAL_ERROR",
    "APPRAISAL_CAVEAT_NOTE",
    "DEMO_WARNING_NOTE",
    "SCRAPER_BLOCKED_NOTE",
    "build_server",
    "serve_stdio",
    "main",
]
