"""Request parsing shared by the JSON API and the HTML forms.

Every write endpoint accepts a body either as JSON or as
``application/x-www-form-urlencoded`` (curl/fetch tend to send the former, plain HTML
`<form>` posts the latter) and every GET endpoint reads its filters out of the query
string -- this module is the one place that turns those raw strings into typed Python
values, so the parsing rules (and their error messages) live in exactly one spot instead
of being re-implemented per handler.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs


class ApiError(Exception):
    """Raised by a handler to short-circuit the request with a JSON/HTML error response."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


# -- query-string parameters --------------------------------------------------------
def parse_int(params: Dict[str, List[str]], name: str) -> Optional[int]:
    values = params.get(name)
    if not values or values[0] == "":
        return None
    try:
        return int(values[0])
    except (TypeError, ValueError):
        raise ApiError(400, f"invalid integer for '{name}': {values[0]!r}")


def parse_float(params: Dict[str, List[str]], name: str) -> Optional[float]:
    values = params.get(name)
    if not values or values[0] == "":
        return None
    try:
        return float(values[0])
    except (TypeError, ValueError):
        raise ApiError(400, f"invalid number for '{name}': {values[0]!r}")


def parse_str(params: Dict[str, List[str]], name: str) -> Optional[str]:
    values = params.get(name)
    if not values or values[0] == "":
        return None
    return values[0]


def parse_bool(params: Dict[str, List[str]], name: str, default: bool = False) -> bool:
    values = params.get(name)
    if not values or values[0] == "":
        return default
    return values[0].strip().lower() in ("1", "true", "yes", "on")


def truthy(value: Any, default: bool = False) -> bool:
    """Coerce a JSON bool, a form string ('1'/'true'/'on'/...), or None to a real bool --
    used for write-intent markers and settings/scraper toggles submitted either as JSON or
    as application/x-www-form-urlencoded fields."""
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def since_date(days: int) -> str:
    return (date.today() - timedelta(days=max(0, days))).isoformat()


# -- request body (POST) -------------------------------------------------------------
MAX_BODY_BYTES = 65536  # 64KB -- generous for a settings/toggle payload, stingy enough
# that a client cannot use a write endpoint to make this process buffer something huge.


def read_body_dict(headers: Any, rfile: Any) -> Dict[str, Any]:
    """Parse a POST body as JSON or application/x-www-form-urlencoded (both are accepted
    on every write endpoint -- curl/fetch tend to send JSON, plain HTML forms send the
    latter). Always returns a dict; malformed JSON or an oversized body raises ApiError."""
    try:
        length = int(headers.get("Content-Length") or 0)
    except (TypeError, ValueError):
        length = 0
    if length < 0:
        length = 0
    if length > MAX_BODY_BYTES:
        raise ApiError(400, f"request body too large (max {MAX_BODY_BYTES} bytes)")
    raw = rfile.read(length) if length else b""
    if not raw:
        return {}
    content_type = (headers.get("Content-Type") or "").split(";")[0].strip().lower()
    if content_type == "application/json":
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ApiError(400, f"malformed JSON body: {exc}")
        if not isinstance(data, dict):
            raise ApiError(400, "JSON body must be an object")
        return data
    # Default: application/x-www-form-urlencoded (also covers a missing/blank header,
    # which is what a bare `curl -d k=v` sends).
    parsed = parse_qs(raw.decode("utf-8", errors="replace"), keep_blank_values=True)
    return {key: values[0] for key, values in parsed.items() if values}


# -- settings/secrets form <-> dotted-changes round-trip ------------------------------
def coerce_setting_value(value: Any, type_name: str) -> Any:
    if type_name == "bool":
        return truthy(value)
    if type_name == "number":
        try:
            return float(value)
        except (TypeError, ValueError):
            raise ApiError(400, f"invalid number: {value!r}")
    if type_name == "list":
        if isinstance(value, list):
            return value
        text = "" if value is None else str(value)
        return [part.strip() for part in text.split(",") if part.strip()]
    return "" if value is None else str(value)


def _changes_dict_from_raw(raw_changes: Any) -> Optional[Dict[str, Any]]:
    """Shared by the settings and secrets forms: a JSON caller may send `changes` as an
    object already, or (from a plain HTML form, which has no nested-object fields) as a
    JSON-encoded string. Returns None when neither shape is present, so the caller can
    fall back to reading individual form fields."""
    if isinstance(raw_changes, dict):
        return raw_changes
    if isinstance(raw_changes, str) and raw_changes.strip():
        try:
            parsed = json.loads(raw_changes)
        except json.JSONDecodeError:
            raise ApiError(400, "'changes' must be a JSON object")
        if not isinstance(parsed, dict):
            raise ApiError(400, "'changes' must be a JSON object")
        return parsed
    return None


def settings_changes_from_body(config: Any, body: Dict[str, Any], editable_settings) -> Tuple[Dict[str, Any], bool]:
    """A JSON caller sends {"changes": {...}, "dry_run": ...} with values already the
    right type. A plain <form> POST from the /settings page instead marks every field it
    rendered with a 'present.<dotted key>' hidden input (a checkbox otherwise vanishes
    from the body instead of submitting 'false' when unchecked), so presence of that
    marker -- not the raw value -- decides whether a bool field changed.

    `editable_settings` is passed in (rather than imported) to avoid a dependency from
    this request-parsing module onto carmon.settings.
    """
    dry_run = truthy(body.get("dry_run"))
    changes = _changes_dict_from_raw(body.get("changes"))
    if changes is not None:
        return changes, dry_run

    fields = editable_settings(config)
    changes = {}
    for dotted, info in fields.items():
        if f"present.{dotted}" not in body:
            continue
        if info["type"] == "bool":
            changes[dotted] = dotted in body
        else:
            changes[dotted] = coerce_setting_value(body.get(dotted, ""), info["type"])
    return changes, dry_run


def secret_changes_from_body(body: Dict[str, Any]) -> Dict[str, str]:
    """Mirrors settings_changes_from_body for the secrets form: JSON callers send
    {"changes": {KEY: value}}; the /settings page's secrets form instead submits one
    'secret.<KEY>' field per known secret, left blank to mean 'leave it alone'."""
    changes = _changes_dict_from_raw(body.get("changes"))
    if changes is not None:
        return changes
    prefix = "secret."
    return {
        key[len(prefix):]: value
        for key, value in body.items()
        if key.startswith(prefix) and key[len(prefix):] and value
    }
