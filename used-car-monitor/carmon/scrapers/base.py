"""Shared machinery for the optional scrapers: robots, rate limits, and hard daily caps.

Every adapter goes through this module, and this module is where the restraint lives:

* **robots.txt is always obeyed.** There is no config flag to turn that off. If robots.txt
  cannot be fetched at all, the source is treated as forbidden (fail closed) rather than
  assumed permissive.
* **Hard daily caps**, enforced against a SQLite ledger rather than an in-memory counter, so
  they survive restarts and repeated runs: by default 100 listings/day and 20 requests/day
  across all sources, and 2 pages per source per run.
* **One request at a time, slowly** — a minimum delay between requests (default 5s), and any
  `Crawl-delay` in robots.txt wins if it is longer.
* **Off by default.** Both `scrapers.enabled` and each individual source must be switched on.
* **No evasion, by design.** One honest User-Agent that says what this is, no proxy rotation,
  no cookie or fingerprint games, no CAPTCHA solving. If a site answers with a bot challenge,
  the adapter records "blocked" and stops. That is the correct outcome, not a problem to
  engineer around: a site that challenges you is telling you it does not want automated
  traffic, and MarketCheck's API is the supported path this project uses first.

Adapters implement `search_urls()` and `parse()`; everything above is handled here.
"""

from __future__ import annotations

import logging
import re
import sqlite3
import time
import urllib.error
import urllib.request
import urllib.robotparser
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse

from .. import db

LOG = logging.getLogger("carmon.scrapers")

DEFAULT_USER_AGENT = (
    "CarMonitorBot/1.0 (+personal used-car search; low volume; contact: see README)"
)

# Phrases that mean "a bot wall answered, not the page you asked for".
CHALLENGE_MARKERS = (
    "just a moment", "enable javascript and cookies", "access denied", "captcha",
    "attention required", "cf-browser-verification", "px-captcha", "are you a human",
    "request unsuccessful", "incapsula",
)

# Fingerprints of the challenge platforms themselves. A short, script-only page is only
# treated as a wall when one of these is present — plenty of legitimate pages are small,
# and guessing from size alone produced false positives.
CHALLENGE_PLATFORMS = (
    "cf_chl", "cdn-cgi/challenge-platform", "challenge-platform", "__cf_chl",
    "_incapsula_", "distil_r_captcha", "perimeterx", "px-cloud", "akam/", "_abck",
)


class ScraperError(RuntimeError):
    """Anything that stopped an adapter, with a message meant for a human."""


class BlockedError(ScraperError):
    """The site answered with a bot challenge or refusal.

    Deliberately terminal: we do not retry harder, rotate identity, or try to look more
    like a browser. See the module docstring.
    """


class RobotsDisallowed(ScraperError):
    """robots.txt forbids this path (or could not be read, which we treat the same)."""


class BudgetExhausted(ScraperError):
    """A daily cap has been reached. Not an error condition — just a stop."""


@dataclass
class ScrapeLimits:
    max_listings_per_day: int = 100
    max_requests_per_day: int = 20
    max_pages_per_run: int = 2
    min_seconds_between_requests: float = 5.0
    timeout_seconds: int = 25
    user_agent: str = DEFAULT_USER_AGENT

    @classmethod
    def from_config(cls, config: Optional[Dict[str, Any]]) -> "ScrapeLimits":
        config = config or {}
        return cls(
            max_listings_per_day=int(config.get("max_listings_per_day", 100)),
            max_requests_per_day=int(config.get("max_requests_per_day", 20)),
            max_pages_per_run=int(config.get("max_pages_per_run", 2)),
            min_seconds_between_requests=float(config.get("min_seconds_between_requests", 5)),
            timeout_seconds=int(config.get("timeout_seconds", 25)),
            user_agent=str(config.get("user_agent") or DEFAULT_USER_AGENT),
        )


@dataclass
class ScrapeResult:
    source: str
    listings: List[Dict[str, Any]] = field(default_factory=list)
    pages_fetched: int = 0
    status: str = "ok"          # ok | blocked | disallowed | budget | error | disabled
    message: str = ""
    urls: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source, "status": self.status, "message": self.message,
            "pages_fetched": self.pages_fetched, "listings": len(self.listings), "urls": self.urls,
        }


def looks_like_challenge(body: str, status: int = 200) -> bool:
    """True when the response is a bot wall rather than the requested page."""
    if status in (401, 403, 406, 429, 503):
        return True
    sample = body[:8000].lower()
    if any(marker in sample for marker in CHALLENGE_MARKERS):
        return True
    if any(platform in sample for platform in CHALLENGE_PLATFORMS):
        return True
    # A short, script-only shell *with* a challenge fingerprint is a wall; a short page on
    # its own is just a short page.
    return False


class RobotsCache:
    """One robots.txt fetch per host per process, obeyed strictly and failing closed."""

    def __init__(self, user_agent: str = DEFAULT_USER_AGENT, timeout: int = 15):
        self.user_agent = user_agent
        self.timeout = timeout
        self._cache: Dict[str, Tuple[Optional[urllib.robotparser.RobotFileParser], str]] = {}

    def _load(self, host_root: str) -> Tuple[Optional[urllib.robotparser.RobotFileParser], str]:
        if host_root in self._cache:
            return self._cache[host_root]
        parser = urllib.robotparser.RobotFileParser()
        url = f"{host_root}/robots.txt"
        try:
            request = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8", errors="replace")
            if looks_like_challenge(body, getattr(response, "status", 200)):
                result = (None, "robots.txt itself is behind a bot challenge")
            else:
                parser.parse(body.splitlines())
                result = (parser, "")
        except Exception as exc:
            result = (None, f"robots.txt could not be read ({exc})")
        self._cache[host_root] = result
        return result

    def check(self, url: str) -> None:
        """Raise RobotsDisallowed unless robots.txt clearly permits this URL."""
        parts = urlparse(url)
        host_root = f"{parts.scheme}://{parts.netloc}"
        parser, problem = self._load(host_root)
        if parser is None:
            raise RobotsDisallowed(
                f"{parts.netloc}: {problem}. Treating the whole site as off limits — "
                "when permission cannot be established, the answer is no."
            )
        if not parser.can_fetch(self.user_agent, url):
            raise RobotsDisallowed(f"{parts.netloc}: robots.txt disallows {parts.path or '/'}")

    def crawl_delay(self, url: str) -> Optional[float]:
        parts = urlparse(url)
        parser, _ = self._load(f"{parts.scheme}://{parts.netloc}")
        if parser is None:
            return None
        try:
            delay = parser.crawl_delay(self.user_agent)
            return float(delay) if delay else None
        except Exception:
            return None


class Fetcher:
    """Polite HTTP GET: robots-checked, rate-limited, ledger-logged, challenge-aware."""

    def __init__(
        self,
        conn: sqlite3.Connection,
        source: str,
        limits: Optional[ScrapeLimits] = None,
        robots: Optional[RobotsCache] = None,
        opener: Optional[Any] = None,
    ):
        self.conn = conn
        self.source = source
        self.limits = limits or ScrapeLimits()
        self.robots = robots or RobotsCache(self.limits.user_agent)
        self.opener = opener  # injectable for tests: callable(url, headers, timeout) -> (status, body)
        self._last_request_at = 0.0
        self.requests_made = 0

    # --- budget ---------------------------------------------------------
    def budget_left(self) -> Dict[str, int]:
        used = db.scrape_usage_today(self.conn)
        return {
            "requests": max(0, self.limits.max_requests_per_day - used["requests"]),
            "listings": max(0, self.limits.max_listings_per_day - used["listings"]),
        }

    def _check_budget(self) -> None:
        left = self.budget_left()
        if left["requests"] <= 0:
            raise BudgetExhausted(
                f"daily request cap reached ({self.limits.max_requests_per_day} requests across all "
                "sources). Resets at midnight."
            )
        if left["listings"] <= 0:
            raise BudgetExhausted(
                f"daily listing cap reached ({self.limits.max_listings_per_day} listings across all "
                "sources). Resets at midnight."
            )

    # --- fetching -------------------------------------------------------
    def _sleep(self, url: str) -> None:
        delay = self.limits.min_seconds_between_requests
        crawl_delay = self.robots.crawl_delay(url)
        if crawl_delay:
            delay = max(delay, crawl_delay)  # the site's own request wins if it is slower
        elapsed = time.monotonic() - self._last_request_at
        if self._last_request_at and elapsed < delay:
            time.sleep(delay - elapsed)
        self._last_request_at = time.monotonic()

    def get(self, url: str, kind: str = "page") -> str:
        """Fetch one URL. Raises RobotsDisallowed, BudgetExhausted, BlockedError or ScraperError."""
        self._check_budget()
        self.robots.check(url)
        self._sleep(url)

        headers = {
            "User-Agent": self.limits.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        try:
            if self.opener is not None:
                status, body = self.opener(url, headers, self.limits.timeout_seconds)
            else:
                request = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(request, timeout=self.limits.timeout_seconds) as response:
                    status = getattr(response, "status", 200)
                    body = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            body = ""
            status = exc.code
            db.record_scrape(self.conn, self.source, kind, url, status, 0, "http error")
            self.requests_made += 1
            raise BlockedError(
                f"{urlparse(url).netloc} answered HTTP {status}. Not retrying: this project does not "
                "work around bot protection. Sites often behave differently from a home connection "
                "than from a datacenter, so this may simply work on your own machine."
            ) from exc
        except Exception as exc:
            db.record_scrape(self.conn, self.source, kind, url, None, 0, f"network error: {exc}")
            self.requests_made += 1
            raise ScraperError(f"request failed: {exc}") from exc

        self.requests_made += 1
        db.record_scrape(self.conn, self.source, kind, url, status, 0, "")
        if looks_like_challenge(body, status):
            raise BlockedError(
                f"{urlparse(url).netloc} returned a bot challenge instead of the page. Stopping here "
                "by design — no CAPTCHA solving, no identity rotation. Try from your home network, or "
                "just use the site in a browser via `python3 -m carmon sources`."
            )
        return body

    def note_listings(self, url: str, count: int) -> None:
        """Record listings taken, which counts against the daily listing cap."""
        db.record_scrape(self.conn, self.source, "listings", url, 200, count, "")


class ScraperBase:
    """Base class for source adapters.

    Subclasses set `key`, `name`, `site` and implement:
        search_urls(search: dict) -> list[str]      # at most max_pages_per_run URLs
        parse(body: str, url: str) -> list[dict]    # normalized listing dicts
    """

    key: str = "base"
    name: str = "Base"
    site: str = ""
    kind: str = "listings"   # "listings" or "reference" (reference sources add facts, not cars)

    def __init__(self, conn: sqlite3.Connection, limits: Optional[ScrapeLimits] = None,
                 fetcher: Optional[Fetcher] = None):
        self.conn = conn
        self.limits = limits or ScrapeLimits()
        self.fetcher = fetcher or Fetcher(conn, self.key, self.limits)

    def search_urls(self, search: Dict[str, Any]) -> List[str]:
        raise NotImplementedError

    def parse(self, body: str, url: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def run(self, search: Dict[str, Any]) -> ScrapeResult:
        result = ScrapeResult(source=self.key)
        urls = list(self.search_urls(search))[: self.limits.max_pages_per_run]
        result.urls = urls
        seen_vins: set[str] = set()

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
                    f"parsing failed ({exc}). These sites change their markup often; the adapter "
                    "needs updating."
                )
                break

            room = self.fetcher.budget_left()["listings"]
            kept = []
            for listing in parsed:
                if room <= 0:
                    result.message = "daily listing cap reached mid-page; stopping early"
                    break
                vin = (listing.get("vin") or "").strip().upper()
                if not vin or vin in seen_vins:
                    continue  # without a VIN it cannot be deduplicated against MarketCheck data
                seen_vins.add(vin)
                listing["vin"] = vin
                listing.setdefault("source", self.key)
                kept.append(listing)
                room -= 1
            result.listings.extend(kept)
            self.fetcher.note_listings(url, len(kept))
            if room <= 0:
                break
        return result

    # --- reachability -----------------------------------------------------
    def probe(self, search: Dict[str, Any]) -> Dict[str, Any]:
        """Can this source be scraped from here at all? Costs one request."""
        urls = list(self.search_urls(search))[:1]
        if not urls:
            return {"source": self.key, "status": "error", "message": "no search URL"}
        try:
            body = self.fetcher.get(urls[0], kind="probe")
        except (RobotsDisallowed, BlockedError, BudgetExhausted, ScraperError) as exc:
            status = {
                RobotsDisallowed: "disallowed", BlockedError: "blocked",
                BudgetExhausted: "budget", ScraperError: "error",
            }[type(exc)]
            return {"source": self.key, "name": self.name, "status": status, "message": str(exc)}
        try:
            found = len(self.parse(body, urls[0]))
        except Exception as exc:
            return {"source": self.key, "name": self.name, "status": "unparsed",
                    "message": f"page fetched but could not be parsed: {exc}"}
        return {
            "source": self.key, "name": self.name, "status": "ok" if found else "empty",
            "message": f"fetched {len(body):,} bytes, parsed {found} item(s)",
        }


REGISTRY: Dict[str, type] = {}


def register(scraper_class: type) -> type:
    REGISTRY[scraper_class.key] = scraper_class
    return scraper_class


def available() -> List[str]:
    return sorted(REGISTRY)
