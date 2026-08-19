"""Data-shaping helpers shared by the web JSON API (`carmon.web`) and the MCP tool
handlers (`carmon.mcp_server`).

Both layers answer many of the same questions over the same `carmon.db` rows: a
listing's NHTSA.gov links, a "count + rows" collection envelope, a cached
`model_reliability` row with its JSON-text columns decoded. This module holds only the
*data* shape common to both -- turning rows/fields into the same plain dict/tuple shape
each layer's own envelope (an HTTP JSON response vs an MCP tools/call content block)
wraps around. HTTP status codes/escaping stay in `carmon.web`; MCP tool-error and
content-envelope concerns stay in `carmon.mcp_server` -- neither is duplicated here.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional, Tuple


def count_envelope(key: str, rows: List[Any], **extra: Any) -> Dict[str, Any]:
    """The `{..., "count": len(rows), key: rows}` shape used by every listing/collection
    endpoint in both layers (`/api/new`, `/api/top`, `/api/deals`, ... and MCP's
    `listings_result`, `list_reliability`, ...). `extra` is merged in first so `count`
    and `key` always win if a caller's extra kwargs happen to collide."""
    payload: Dict[str, Any] = dict(extra)
    payload["count"] = len(rows)
    payload[key] = rows
    return payload


def nhtsa_urls(
    vin: str,
    make: Any,
    model: Any,
    year: Any,
    vin_recall_url: Optional[Callable[[str], str]],
    recall_lookup_url: Optional[Callable[[Any, Any, Any], str]],
) -> Tuple[Optional[str], Optional[str]]:
    """(vin_url, model_url) NHTSA.gov links for one listing -- computed identically on the
    listing detail page, the `/api/listings/<vin>` endpoint, and the MCP `get_listing`
    tool. The two resolver functions are passed in rather than imported here so the MCP
    layer can keep resolving them lazily (nhtsa is treated as an optional dependency
    there via `carmon.mcp_server.imports`), while the web layer -- which always has them
    -- just passes its already-imported functions straight through.
    """
    vin_url = vin_recall_url(vin) if vin_recall_url else None
    model_url = (
        recall_lookup_url(make, model, year)
        if recall_lookup_url and make and model and year
        else None
    )
    return vin_url, model_url


def reliability_row_to_dict(row: Any) -> Dict[str, Any]:
    """A `model_reliability` row to a plain dict with its JSON-text columns
    (`top_components`, `recalls`) decoded -- shared by the web API's `/api/reliability`
    list and the MCP `list_reliability` tool, which both list every cached row the same
    way."""
    data = dict(row)
    for field_name in ("top_components", "recalls"):
        if isinstance(data.get(field_name), str) and data[field_name]:
            try:
                data[field_name] = json.loads(data[field_name])
            except json.JSONDecodeError:
                data[field_name] = None
    return data
