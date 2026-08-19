"""JSON Schema building blocks for tool input schemas, plus the shared caveat
notes appended to several tools' descriptions.

Every tool's *description text* is still spelled out in full, verbatim, in
tools.py -- an AI client reads that text to use the tools correctly, so
nothing here abbreviates or generates it. What these helpers remove is the
JSON *structure* boilerplate ("type": "object", "additionalProperties":
False, "type": "integer" + "description" + ...) that used to be hand-written
25 times over.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# Appended to the description of any tool whose numbers come from the local price-vs-mileage
# fit in carmon.market. Keeps an assistant from presenting a deterministic OLS curve over
# locally-stored listings as if it were a professional valuation.
APPRAISAL_CAVEAT_NOTE = (
    " This is NOT a valuation and NOT KBB/Edmunds/etc: it is a deterministic ordinary-least-"
    "squares fit of price against mileage and model year, computed only over listings this "
    "monitor has stored locally. It knows nothing about condition, trim, options, accident "
    "history or title status. Always report 'sample_size', 'confidence' and 'basis_level' "
    "alongside any 'grade' — a basis_level of 'make' or 'all' means the comparison fell back "
    "to different models entirely and is only a rough bearing. Always surface anything in "
    "'notes' to the user; those are caveats, not filler. Price-versus-mileage comparisons work "
    "from the first run; month-over-month trend numbers need weeks of accumulated history."
)

# Appended to the description of any tool whose results can include seeded demo rows.
DEMO_WARNING_NOTE = (
    " If any returned listing is seeded demo data (source 'demo'), the JSON payload "
    "carries a top-level 'warning' field with details. Demo rows are fake and must "
    "never be reported to the user as real cars for sale."
)

# Appended to the description of every scraper-related tool. A 'blocked' or 'disallowed'
# status is the correct, expected outcome of a site declining automated access, not a bug
# to route around — see carmon/scrapers/base.py for why.
SCRAPER_BLOCKED_NOTE = (
    " A status of 'blocked' or 'disallowed' is a normal, expected outcome, not a failure to "
    "work around: 'blocked' means the site answered with a bot challenge (and the adapter "
    "stopped rather than solve it), and 'disallowed' means robots.txt forbids the request — "
    "or could not be read at all, which this project treats as a refusal rather than an "
    "invitation. Never suggest bypassing either one, changing the User-Agent, using a proxy, "
    "spoofing headers, or simply retrying to get past it; the correct response is to leave "
    "that source alone and rely on the MarketCheck API or a plain browser link instead. "
    "Scraping here is opt-in, secondary to the MarketCheck API, and rate-limited: 100 "
    "listings/day and 20 requests/day across all sources combined, at most 2 pages per "
    "source per run, and at least 5 seconds between requests."
)


def _prop(type_: str, description: str, **extra: Any) -> Dict[str, Any]:
    prop: Dict[str, Any] = {"type": type_, "description": description}
    prop.update(extra)
    return prop


def prop_string(description: str, **extra: Any) -> Dict[str, Any]:
    return _prop("string", description, **extra)


def prop_int(description: str, **extra: Any) -> Dict[str, Any]:
    return _prop("integer", description, **extra)


def prop_number(description: str, **extra: Any) -> Dict[str, Any]:
    return _prop("number", description, **extra)


def prop_bool(description: str, **extra: Any) -> Dict[str, Any]:
    return _prop("boolean", description, **extra)


def object_schema(properties: Dict[str, Any], required: Optional[List[str]] = None) -> Dict[str, Any]:
    schema: Dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required:
        schema["required"] = required
    return schema


# Shared by every tool that takes no arguments at all (get_stats, get_latest_digest,
# list_sources, probe_scrapers, get_settings).
EMPTY_SCHEMA = object_schema({})
