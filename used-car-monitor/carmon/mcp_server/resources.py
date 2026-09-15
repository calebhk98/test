"""MCP 'resources': read-only URIs distinct from tools/call, surfaced via the
resources/list and resources/read JSON-RPC methods."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from .handlers import latest_digest_text
from .protocol import MCPParamError

RESOURCE_DEFS: List[Dict[str, Any]] = [
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


def read_resource(server, uri: str) -> Dict[str, Any]:
    if uri == "carmon://config":
        text = json.dumps(server.config.to_dict(), indent=2, default=str)
        return {"contents": [{"uri": uri, "mimeType": "application/json", "text": text}]}

    if uri == "carmon://digest/latest":
        text = latest_digest_text(server.config)
        return {"contents": [{"uri": uri, "mimeType": "text/markdown", "text": text}]}

    raise MCPParamError(f"Unknown resource uri: {uri}")
