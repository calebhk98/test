"""JSON-RPC 2.0 framing: error codes, envelope builders, and the stdio request loop.

This module knows nothing about carmon's tools or business logic -- it only knows
how to speak JSON-RPC 2.0 over stdio and shape MCP-style tools/call results. The
tool schemas live in tools.py, their implementations in handlers.py, and the
class that ties a live request to config/db state lives in server.py.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, Optional

PROTOCOL_VERSION = "2024-11-05"

# --------------------------------------------------------------------------
# JSON-RPC error codes (standard MCP / JSON-RPC 2.0 codes)
# --------------------------------------------------------------------------
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


class MCPParamError(ValueError):
    """Raised for malformed top-level JSON-RPC params -> maps to -32602."""


class ToolError(ValueError):
    """Raised inside a tool handler for a user-facing error -> isError result."""


def error_response(request_id: Any, code: int, message: str, data: Any = None) -> Dict[str, Any]:
    err: Dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": err}


def result_response(request_id: Any, result: Any) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def text_result(payload: Any, is_error: bool = False, as_json: bool = True) -> Dict[str, Any]:
    """Build an MCP tools/call result with a single text content block."""
    if as_json:
        text = json.dumps(payload, indent=2, default=str)
    else:
        text = str(payload)
    return {"content": [{"type": "text", "text": text}], "isError": is_error}


def write_message(out, message: Dict[str, Any]) -> None:
    out.write(json.dumps(message, default=str))
    out.write("\n")
    out.flush()


def serve_stdio(server, stdin=None, stdout=None) -> None:
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
            write_message(stdout, error_response(None, PARSE_ERROR, f"Parse error: {exc}"))
            continue
        response = server.handle_request(message)
        if response is not None:
            write_message(stdout, response)
