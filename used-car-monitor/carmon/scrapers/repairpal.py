"""RepairPal adapter: per-model ownership-cost and reliability facts.

RepairPal publishes, per make/model, the kind of ownership-cost data no free API offers:
average annual repair cost, a reliability rating out of 5, how often a model sees a shop
each year, what share of those visits are "severe" (a big bill, not an oil change), how the
model ranks against its class, and a short list of commonly reported problems. That is
exactly the signal this project's users want before buying a car that ends up nickel-and-
diming them, and RepairPal has no public API for it — a scraper is the only way in.

Like every other adapter in this package, this one is **opt-in and capped**: it stays off
until `scrapers.enabled` and `scrapers.sources.repairpal` are both switched on in
config.json, it obeys robots.txt (failing closed if that cannot be read), it is rate-limited
and ledger-capped by `ScraperBase`/`Fetcher`, and it does nothing to evade a bot challenge —
a challenge response is recorded as blocked and left alone. Review RepairPal's Terms of
Service before enabling this source; nothing here substitutes for that judgment.

This is a *reference* source (`kind = "reference"`): it does not produce VIN-keyed listings,
it produces one fact-sheet per model, so `run()` is overridden below rather than using
`ScraperBase.run()`, which discards anything without a `vin`.

Parsing tries three strategies, in order of how much we trust the structure to survive a
redesign: `application/ld+json` blocks, then any other embedded JSON payload (e.g. a
framework's hydration blob), then a plain-text regex sweep over the visible page text. Each
strategy is independently wrapped so a missing or reshaped field yields `None` rather than
an exception, and a page that matches nothing at all yields `[]` rather than raising.
"""

from __future__ import annotations

import logging

import json
import re
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from .. import db

LOG = logging.getLogger("carmon.scrapers.repairpal")
from .base import (
    BlockedError,
    BudgetExhausted,
    RobotsDisallowed,
    ScraperBase,
    ScraperError,
    ScrapeResult,
    register,
)
from .parsing import extract_json_ld_blocks, to_float as _to_float

# --- URL helpers -------------------------------------------------------------


def _slugify(value: str) -> str:
    """'Mazda3' -> 'mazda3', 'Grand Cherokee' -> 'grand-cherokee'."""
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def _deslugify(slug: str) -> Optional[str]:
    if not slug:
        return None
    return " ".join(word.capitalize() for word in slug.split("-") if word)


def _make_model_from_url(url: str) -> tuple[Optional[str], Optional[str]]:
    """Best-effort make/model recovered from the URL path, used when the page itself
    does not say. /toyota/corolla and /reliability/toyota/corolla both work."""
    try:
        parts = [p for p in urlparse(url).path.strip("/").split("/") if p]
    except Exception:
        return None, None
    parts = [p for p in parts if p.lower() != "reliability"]
    if len(parts) >= 2:
        return _deslugify(parts[0]), _deslugify(parts[1])
    return None, None


# --- generic JSON field extraction -------------------------------------------

_FIELD_SYNONYMS: Dict[str, tuple[str, ...]] = {
    "make": ("make", "brand"),
    "model": ("model",),
    "annual_repair_cost": ("annualrepaircost", "averageannualrepaircost", "repaircost"),
    "reliability_rating": ("reliabilityrating", "ratingvalue", "rating"),
    "rating_scale": ("bestrating", "ratingscale"),
    "visits_per_year": ("visitsperyear", "shopvisitsperyear"),
    "severity_pct": ("severepct", "severitypercent", "severerepairpercent"),
    "rank_text": ("ranktext", "rank"),
    "common_problems": ("commonproblems", "problems"),
}


def _normkey(key: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(key).lower())


def _walk(obj: Any):
    """Yield every (key, value) pair anywhere in a nested dict/list structure."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k, v
            yield from _walk(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk(item)


def _coerce_name(value: Any) -> Optional[str]:
    try:
        if isinstance(value, str):
            value = value.strip()
            return value or None
        if isinstance(value, dict):
            for key in ("name", "text", "title"):
                candidate = value.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    return candidate.strip()
    except Exception:
        return None
    return None


def _coerce_problems(value: Any) -> Optional[List[str]]:
    items: List[str] = []
    try:
        if isinstance(value, str):
            for part in re.split(r"[,;\n]", value):
                part = part.strip(" .")
                if part:
                    items.append(part)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    items.append(item.strip())
                elif isinstance(item, dict):
                    for key in ("name", "text", "title", "problem"):
                        candidate = item.get(key)
                        if isinstance(candidate, str) and candidate.strip():
                            items.append(candidate.strip())
                            break
    except Exception:
        return None
    items = [i for i in items if i]
    return items[:5] or None


def _coerce_field(field: str, value: Any) -> Optional[Any]:
    try:
        if field in ("make", "model", "rank_text"):
            return _coerce_name(value)
        if field in (
            "annual_repair_cost", "reliability_rating", "rating_scale",
            "visits_per_year", "severity_pct",
        ):
            return _to_float(value)
        if field == "common_problems":
            return _coerce_problems(value)
    except Exception:
        return None
    return None


def _extract_fields(obj: Any) -> Optional[Dict[str, Any]]:
    found: Dict[str, Any] = {}
    try:
        for key, value in _walk(obj):
            nk = _normkey(key)
            if nk and nk not in found:
                found[nk] = value
    except Exception:
        return None

    result: Dict[str, Any] = {}
    for field, synonyms in _FIELD_SYNONYMS.items():
        for syn in synonyms:
            if syn in found:
                coerced = _coerce_field(field, found[syn])
                if coerced is not None:
                    result[field] = coerced
                break
    return result or None


# --- strategy (a): application/ld+json ---------------------------------------

def _parse_ld_json(body: str) -> Optional[Dict[str, Any]]:
    for raw in extract_json_ld_blocks(body):
        try:
            obj = json.loads(raw.strip())
        except (json.JSONDecodeError, ValueError):
            continue
        data = _extract_fields(obj)
        if data:
            return data
    return None


# --- strategy (b): any other embedded JSON payload ---------------------------

_ANY_SCRIPT_RE = re.compile(r"<script[^>]*>(.*?)</script>", re.IGNORECASE | re.DOTALL)


def _parse_embedded_json(body: str) -> Optional[Dict[str, Any]]:
    for raw in _ANY_SCRIPT_RE.findall(body):
        text = raw.strip()
        if not text or text[0] not in "{[":
            continue
        try:
            obj = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            continue
        data = _extract_fields(obj)
        if data:
            return data
    return None


# --- strategy (c): visible-text regex sweep -----------------------------------


class _TextExtractor(HTMLParser):
    """Strips tags, dropping script/style content, to get the words a reader would see."""

    def __init__(self) -> None:
        super().__init__()
        self._skip = False
        self.chunks: List[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in ("script", "style"):
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style"):
            self._skip = False

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self.chunks.append(data)


def _visible_text(body: str) -> str:
    parser = _TextExtractor()
    try:
        parser.feed(body)
    except Exception:
        pass
    return " ".join(chunk.strip() for chunk in parser.chunks if chunk.strip())


_COST_RE = re.compile(r"average annual repair cost[^$]*\$\s*([\d,]+(?:\.\d+)?)", re.IGNORECASE)
_RATING_RE = re.compile(
    r"reliability rating[^0-9]{0,20}([\d.]+)\s*(?:out of|/)\s*([\d.]+)", re.IGNORECASE
)
_VISITS_RE = re.compile(r"([\d.]+)\s*(?:shop\s*)?visits per year", re.IGNORECASE)
_SEVERITY_RE = re.compile(
    r"([\d.]+)\s*%\s*(?:of\s+(?:repairs|visits)\s+)?(?:are\s+)?severe", re.IGNORECASE
)
_RANK_RE = re.compile(
    r"rank\w*[^0-9]{0,20}(\d+\w{0,3}\s+out of\s+\d+[^.]*)", re.IGNORECASE
)
_PROBLEMS_RE = re.compile(r"common problems?:?\s*(.+?)(?:\.\s|\.$|$)", re.IGNORECASE)


def _parse_text(body: str) -> Optional[Dict[str, Any]]:
    text = _visible_text(body)
    if not text:
        return None
    result: Dict[str, Any] = {}
    try:
        match = _COST_RE.search(text)
        if match:
            result["annual_repair_cost"] = _to_float(match.group(1))
        match = _RATING_RE.search(text)
        if match:
            result["reliability_rating"] = _to_float(match.group(1))
            result["rating_scale"] = _to_float(match.group(2))
        match = _VISITS_RE.search(text)
        if match:
            result["visits_per_year"] = _to_float(match.group(1))
        match = _SEVERITY_RE.search(text)
        if match:
            result["severity_pct"] = _to_float(match.group(1))
        match = _RANK_RE.search(text)
        if match:
            result["rank_text"] = match.group(1).strip()
        match = _PROBLEMS_RE.search(text)
        if match:
            problems = _coerce_problems(match.group(1))
            if problems:
                result["common_problems"] = problems
    except Exception:
        pass
    result = {k: v for k, v in result.items() if v is not None}
    return result or None


# --- adapter -------------------------------------------------------------------


@register
class RepairPalScraper(ScraperBase):
    key = "repairpal"
    name = "RepairPal"
    site = "https://repairpal.com"
    kind = "reference"

    def search_urls(self, search: Dict[str, Any]) -> List[str]:
        search = search or {}
        make = search.get("make")
        model = search.get("model")
        if not make or not model:
            return []
        make_slug = _slugify(str(make))
        model_slug = _slugify(str(model))
        if not make_slug or not model_slug:
            return []
        # The /reliability/ page carries MODEL-level figures; the bare /make/model page
        # carries BRAND-level ones ("8th out of 32 for all car brands") that would be wrong
        # to store against a model. Reliability first, the other only as a fallback.
        return [
            f"{self.site}/reliability/{make_slug}/{model_slug}",
            f"{self.site}/{make_slug}/{model_slug}",
        ][:2]

    def parse(self, body: str, url: str) -> List[Dict[str, Any]]:
        data: Optional[Dict[str, Any]] = None
        for extractor in (_parse_ld_json, _parse_embedded_json, _parse_text):
            try:
                candidate = extractor(body)
            except Exception:
                candidate = None
            if candidate and (
                candidate.get("annual_repair_cost") is not None
                or candidate.get("reliability_rating") is not None
            ):
                data = candidate
                break

        if not data:
            return []

        url_make, url_model = _make_model_from_url(url)
        record = {
            "make": data.get("make") or url_make,
            "model": data.get("model") or url_model,
            "annual_repair_cost": data.get("annual_repair_cost"),
            "reliability_rating": data.get("reliability_rating"),
            "rating_scale": data.get("rating_scale") or 5.0,
            "visits_per_year": data.get("visits_per_year"),
            "severity_pct": data.get("severity_pct"),
            "rank_text": data.get("rank_text"),
            "common_problems": data.get("common_problems"),
            "source_url": url,
        }
        return [record]

    def run(self, search: Dict[str, Any]) -> ScrapeResult:
        """Reference-source variant of ScraperBase.run(): keeps fact-sheet dicts, which
        have no `vin`, instead of discarding them the way the listings base class does."""
        result = ScrapeResult(source=self.key)
        urls = list(self.search_urls(search))[: self.limits.max_pages_per_run]
        result.urls = urls

        for url in urls:
            try:
                body = self.fetcher.get(url)
            except BudgetExhausted as exc:
                result.status, result.message = "budget", str(exc)
                break
            except RobotsDisallowed as exc:
                result.status, result.message = "disallowed", str(exc)
                break
            except BlockedError as exc:
                result.status, result.message = "blocked", str(exc)
                break
            except ScraperError as exc:
                result.status, result.message = "error", str(exc)
                break

            result.pages_fetched += 1
            try:
                parsed = self.parse(body, url)
            except Exception as exc:  # a layout change must not crash the daily job
                result.status = "error"
                result.message = (
                    f"parsing failed ({exc}). RepairPal's markup likely changed; "
                    "the adapter needs updating."
                )
                break

            for record in parsed:
                record.setdefault("source", self.key)
            result.listings.extend(parsed)
            self.fetcher.note_listings(url, len(parsed))

            # The model-level page is tried first and is the one worth having. Once it has
            # answered, the brand-level fallback page is pointless traffic — stop early
            # rather than spend a second request per model on data `store()` would reject.
            if any(record_scope(record) == "model" for record in parsed):
                break

        return result


def record_scope(record: Dict[str, Any]) -> str:
    """"model" for model-specific figures, "brand" for whole-marque ones.

    RepairPal's bare /make/model page quotes the *brand's* average annual repair cost and
    ranking. Storing that against a model would be a quiet lie — a Corolla is not "the
    average Toyota" — so scope is tracked and brand-level records are not saved as models.
    """
    url = str(record.get("source_url") or "")
    rank = str(record.get("rank_text") or "").lower()
    if "/reliability/" in url:
        return "model"
    if "car brands" in rank or "all brands" in rank:
        return "brand"
    return "model" if rank else "unknown"


def store(conn, record: Dict[str, Any]) -> None:
    """Persist one parsed RepairPal fact-sheet dict, if it really is model-level data."""
    if record_scope(record) == "brand":
        LOG.info(
            "Skipping brand-level RepairPal figures for %s %s (%s) — not model data",
            record.get("make"), record.get("model"), record.get("rank_text"),
        )
        return
    db.save_repair_cost(conn, record.get("make"), record.get("model"), record)
