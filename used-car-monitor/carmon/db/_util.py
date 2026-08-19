"""Small helpers shared across the db package: JSON columns and cache-staleness."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple


def model_key(make: Optional[str], model: Optional[str], year: Optional[int]) -> Tuple[str, str, int]:
    """Normalize a make/model/year into the lower-cased key the enrichment tables use."""
    return ((make or "").strip().lower(), (model or "").strip().lower(), int(year or 0))


def decode_json_columns(data: Dict[str, Any], *fields: str, on_error: str = "none") -> None:
    """Decode JSON text columns of `data` in place.

    Non-string or empty values are left alone. `on_error` controls what happens to a column
    that fails to parse: "none" (the default) replaces it with None; "keep" leaves the raw
    string as stored.
    """
    for field in fields:
        value = data.get(field)
        if not (isinstance(value, str) and value):
            continue
        try:
            data[field] = json.loads(value)
        except json.JSONDecodeError:
            if on_error == "none":
                data[field] = None


def is_stale(fetched_at: Optional[str], max_age_days: Optional[int]) -> bool:
    """Whether a cached row's `fetched_at` timestamp is older than `max_age_days`.

    An unparseable timestamp counts as stale (better to refetch than trust it), and no age
    limit at all (`max_age_days is None`) means nothing is ever stale.
    """
    if max_age_days is None or not fetched_at:
        return False
    try:
        fetched = datetime.fromisoformat(fetched_at)
    except ValueError:
        return True
    return (datetime.now(timezone.utc) - fetched).days > max_age_days
