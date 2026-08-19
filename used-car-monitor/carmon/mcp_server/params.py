"""Argument extraction and validation helpers shared by tool handlers.

These replace the inline '_as_int(...) then max(min(...))' clamping and the
ad-hoc required/optional coercions that used to be repeated in nearly every
tool handler.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, Optional

from .protocol import ToolError


def require_str(args: Dict[str, Any], key: str) -> str:
    value = args.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ToolError(f"'{key}' is required and must be a non-empty string")
    return value.strip()


def require_int(args: Dict[str, Any], key: str) -> int:
    value = args.get(key)
    if value is None or value == "":
        raise ToolError(f"'{key}' is required and must be an integer")
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ToolError(f"'{key}' must be an integer")


def as_int(value: Any, name: str, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ToolError(f"'{name}' must be an integer")


def clamped_int(args: Dict[str, Any], key: str, default: int, minimum: int = 1, maximum: Optional[int] = None) -> int:
    """Extract an optional integer argument, defaulting and clamping it into
    [minimum, maximum]. Mirrors the two-line 'as_int(...) then max(min(...))'
    pattern that used to be spelled out inline for every 'limit'/'days'/
    'months'/'width'/... argument across the tool handlers.
    """
    value = as_int(args.get(key, default), key, default=default)
    if maximum is not None:
        return max(minimum, min(value, maximum))
    return max(minimum, value)


def opt_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    return int(value)


def opt_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    return float(value)


def opt_number(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def days_ago_str(days: int) -> str:
    return (date.today() - timedelta(days=days)).isoformat()
