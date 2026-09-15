"""The scraper guard rails: robots obedience, hard caps, politeness, and no evasion.

These are the tests that matter most in this part of the project — the adapters can be
rewritten freely, but these limits are the promise.
"""

import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from carmon import db
from carmon.scrapers import base


class FakeRobots:
    """Stand-in for RobotsCache: permits everything, or refuses everything."""

    def __init__(self, allow=True, crawl_delay=None, message="robots.txt disallows this"):
        self.allow = allow
        self._crawl_delay = crawl_delay
        self.message = message
        self.checked = []

    def check(self, url):
        self.checked.append(url)
        if not self.allow:
            raise base.RobotsDisallowed(self.message)

    def crawl_delay(self, url):
        return self._crawl_delay


class CountingOpener:
    def __init__(self, body="<html><body>ok</body></html>", status=200):
        self.body = body
        self.status = status
        self.calls = []

    def __call__(self, url, headers, timeout):
        self.calls.append({"url": url, "headers": headers, "timeout": timeout})
        return self.status, self.body


class DummyScraper(base.ScraperBase):
    key = "dummy"
    name = "Dummy"
    site = "https://example.test"

    def __init__(self, conn, limits=None, fetcher=None, pages=3, per_page=3):
        super().__init__(conn, limits, fetcher)
        self.pages = pages
        self.per_page = per_page

    def search_urls(self, search):
        return [f"https://example.test/search?page={index}" for index in range(1, self.pages + 1)]

    def parse(self, body, url):
        page = url.rsplit("=", 1)[-1]
        return [
            {"vin": f"VIN{page}{index:012d}", "price_current": 15000, "mileage": 30000,
             "make": "Toyota", "model": "Corolla", "year": 2022}
            for index in range(self.per_page)
        ]


class RobotsPolicyTests(unittest.TestCase):
    def setUp(self):
        self.conn = db.init_db(Path(tempfile.mkdtemp()) / "s.db")
        self.limits = base.ScrapeLimits(min_seconds_between_requests=0)

    def tearDown(self):
        self.conn.close()

    def test_disallowed_path_is_never_fetched(self):
        opener = CountingOpener()
        fetcher = base.Fetcher(self.conn, "dummy", self.limits, robots=FakeRobots(allow=False), opener=opener)
        with self.assertRaises(base.RobotsDisallowed):
            fetcher.get("https://example.test/search")
        self.assertEqual(opener.calls, [], "nothing may be requested when robots.txt says no")

    def test_a_run_stops_cleanly_when_disallowed(self):
        opener = CountingOpener()
        scraper = DummyScraper(self.conn, self.limits, base.Fetcher(
            self.conn, "dummy", self.limits, robots=FakeRobots(allow=False), opener=opener))
        result = scraper.run({})
        self.assertEqual(result.status, "disallowed")
        self.assertEqual(result.listings, [])
        self.assertEqual(opener.calls, [])

    def test_unreadable_robots_fails_closed(self):
        """The important one: no robots.txt means no permission, not free rein."""
        robots = base.RobotsCache("TestAgent")
        robots._cache["https://blocked.test"] = (None, "robots.txt could not be read (HTTP 403)")
        with self.assertRaises(base.RobotsDisallowed) as ctx:
            robots.check("https://blocked.test/anything")
        self.assertIn("off limits", str(ctx.exception))

    def test_robots_parsing_respects_disallow(self):
        robots = base.RobotsCache("TestAgent")
        parser = base.urllib.robotparser.RobotFileParser()
        parser.parse(["User-agent: *", "Disallow: /private/", "Crawl-delay: 7"])
        robots._cache["https://example.test"] = (parser, "")
        robots.check("https://example.test/public/page")  # allowed, no raise
        with self.assertRaises(base.RobotsDisallowed):
            robots.check("https://example.test/private/page")
        self.assertEqual(robots.crawl_delay("https://example.test/public"), 7.0)


class DailyCapTests(unittest.TestCase):
    def setUp(self):
        self.conn = db.init_db(Path(tempfile.mkdtemp()) / "s.db")

    def tearDown(self):
        self.conn.close()

    def _scraper(self, limits, opener=None, pages=5, per_page=3):
        opener = opener or CountingOpener()
        fetcher = base.Fetcher(self.conn, "dummy", limits, robots=FakeRobots(), opener=opener)
        return DummyScraper(self.conn, limits, fetcher, pages=pages, per_page=per_page), opener

    def test_pages_per_run_is_capped(self):
        limits = base.ScrapeLimits(max_pages_per_run=2, min_seconds_between_requests=0)
        scraper, opener = self._scraper(limits)
        result = scraper.run({})
        self.assertEqual(result.pages_fetched, 2)
        self.assertEqual(len(opener.calls), 2, "a run must never fetch more than max_pages_per_run")

    def test_listing_cap_stops_collection(self):
        limits = base.ScrapeLimits(max_pages_per_run=5, max_listings_per_day=4,
                                   min_seconds_between_requests=0)
        scraper, _ = self._scraper(limits, pages=5, per_page=3)
        result = scraper.run({})
        self.assertLessEqual(len(result.listings), 4)
        self.assertLessEqual(db.scrape_usage_today(self.conn)["listings"], 4)

    def test_request_cap_survives_restarts(self):
        """The cap lives in SQLite, so running the command again cannot reset it."""
        limits = base.ScrapeLimits(max_requests_per_day=3, max_pages_per_run=2,
                                   min_seconds_between_requests=0)
        first, _ = self._scraper(limits)
        first.run({})
        second, opener = self._scraper(limits)     # a fresh process would look like this
        second.run({})
        self.assertEqual(db.scrape_usage_today(self.conn)["requests"], 3)
        self.assertEqual(len(opener.calls), 1, "only the one remaining request may be spent")

    def test_run_reports_budget_exhaustion_rather_than_failing(self):
        limits = base.ScrapeLimits(max_requests_per_day=1, min_seconds_between_requests=0)
        scraper, _ = self._scraper(limits)
        scraper.run({})
        again, _ = self._scraper(limits)
        result = again.run({})
        self.assertEqual(result.status, "budget")
        self.assertIn("cap reached", result.message)

    def test_usage_is_recorded_per_source(self):
        limits = base.ScrapeLimits(max_pages_per_run=2, min_seconds_between_requests=0)
        scraper, _ = self._scraper(limits)
        scraper.run({})
        rows = {row["source"]: row for row in db.scrape_usage_by_source(self.conn)}
        self.assertIn("dummy", rows)
        self.assertGreaterEqual(rows["dummy"]["requests"], 2)


class PolitenessTests(unittest.TestCase):
    def setUp(self):
        self.conn = db.init_db(Path(tempfile.mkdtemp()) / "s.db")

    def tearDown(self):
        self.conn.close()

    def test_requests_are_spaced_out(self):
        limits = base.ScrapeLimits(max_pages_per_run=2, min_seconds_between_requests=0.25)
        fetcher = base.Fetcher(self.conn, "dummy", limits, robots=FakeRobots(), opener=CountingOpener())
        scraper = DummyScraper(self.conn, limits, fetcher, pages=2)
        started = time.monotonic()
        scraper.run({})
        self.assertGreaterEqual(time.monotonic() - started, 0.25)

    def test_site_crawl_delay_wins_when_it_is_slower(self):
        limits = base.ScrapeLimits(max_pages_per_run=2, min_seconds_between_requests=0.05)
        robots = FakeRobots(crawl_delay=0.3)
        fetcher = base.Fetcher(self.conn, "dummy", limits, robots=robots, opener=CountingOpener())
        scraper = DummyScraper(self.conn, limits, fetcher, pages=2)
        started = time.monotonic()
        scraper.run({})
        self.assertGreaterEqual(time.monotonic() - started, 0.3)

    def test_the_user_agent_is_honest_about_what_this_is(self):
        agent = base.DEFAULT_USER_AGENT.lower()
        self.assertIn("carmonitorbot", agent)
        for browser_lie in ("mozilla", "chrome", "safari", "webkit", "gecko"):
            self.assertNotIn(browser_lie, agent,
                             "the default agent must not impersonate a browser")

    def test_only_plain_headers_are_sent(self):
        opener = CountingOpener()
        limits = base.ScrapeLimits(min_seconds_between_requests=0)
        fetcher = base.Fetcher(self.conn, "dummy", limits, robots=FakeRobots(), opener=opener)
        fetcher.get("https://example.test/page")
        headers = {key.lower() for key in opener.calls[0]["headers"]}
        self.assertEqual(headers, {"user-agent", "accept", "accept-language"})
        self.assertNotIn("cookie", headers)
        self.assertNotIn("referer", headers)


class NoEvasionTests(unittest.TestCase):
    """A bot wall is a stop sign, not an obstacle."""

    def setUp(self):
        self.conn = db.init_db(Path(tempfile.mkdtemp()) / "s.db")
        self.limits = base.ScrapeLimits(min_seconds_between_requests=0, max_pages_per_run=3)

    def tearDown(self):
        self.conn.close()

    def test_challenge_pages_are_recognised(self):
        for body in ("<html>Just a moment...</html>",
                     "<html>Enable JavaScript and cookies to continue</html>",
                     "<html><h1>Access Denied</h1></html>",
                     "<html>Please complete the CAPTCHA</html>",
                     "<html>Attention Required! | Cloudflare</html>",
                     '<html><script src="/cdn-cgi/challenge-platform/h/g/orchestrate"></script></html>',
                     "<html><script>window._cf_chl_opt={};</script></html>"):
            self.assertTrue(base.looks_like_challenge(body), body[:40])
        self.assertFalse(base.looks_like_challenge("<html><body>" + "listing " * 500 + "</body></html>"))

    def test_a_small_ordinary_page_is_not_mistaken_for_a_wall(self):
        """Size alone must not condemn a page — short legitimate pages exist."""
        small_but_real = (
            '<html><head><script type="application/ld+json">'
            '{"@type":"Car","vin":"ABC","offers":{"price":15000}}</script></head>'
            "<body><h1>2022 Toyota Corolla</h1></body></html>"
        )
        self.assertLess(len(small_but_real), 2500)
        self.assertFalse(base.looks_like_challenge(small_but_real))

    def test_http_403_counts_as_blocked(self):
        self.assertTrue(base.looks_like_challenge("anything", 403))
        self.assertTrue(base.looks_like_challenge("anything", 429))

    def test_a_blocked_fetch_is_not_retried(self):
        opener = CountingOpener(body="<html>Just a moment... enable javascript and cookies</html>")
        fetcher = base.Fetcher(self.conn, "dummy", self.limits, robots=FakeRobots(), opener=opener)
        scraper = DummyScraper(self.conn, self.limits, fetcher, pages=3)
        result = scraper.run({})
        self.assertEqual(result.status, "blocked")
        self.assertEqual(len(opener.calls), 1, "no retry, no second identity, no second attempt")
        self.assertIn("no CAPTCHA solving", result.message)

    def test_blocked_message_points_at_the_supported_route(self):
        opener = CountingOpener(body="<html>Access Denied</html>")
        fetcher = base.Fetcher(self.conn, "dummy", self.limits, robots=FakeRobots(), opener=opener)
        with self.assertRaises(base.BlockedError) as ctx:
            fetcher.get("https://example.test/page")
        self.assertIn("browser", str(ctx.exception).lower())


class ParseFailureTests(unittest.TestCase):
    def setUp(self):
        self.conn = db.init_db(Path(tempfile.mkdtemp()) / "s.db")
        self.limits = base.ScrapeLimits(min_seconds_between_requests=0)

    def tearDown(self):
        self.conn.close()

    def test_a_layout_change_is_reported_not_crashed(self):
        class BrokenScraper(DummyScraper):
            def parse(self, body, url):
                raise ValueError("markup changed")

        fetcher = base.Fetcher(self.conn, "dummy", self.limits, robots=FakeRobots(), opener=CountingOpener())
        result = BrokenScraper(self.conn, self.limits, fetcher).run({})
        self.assertEqual(result.status, "error")
        self.assertIn("needs updating", result.message)

    def test_listings_without_a_vin_are_dropped(self):
        class NoVinScraper(DummyScraper):
            def parse(self, body, url):
                return [{"price_current": 15000}, {"vin": "GOODVIN000000001", "price_current": 15000}]

        fetcher = base.Fetcher(self.conn, "dummy", self.limits, robots=FakeRobots(), opener=CountingOpener())
        result = NoVinScraper(self.conn, self.limits, fetcher, pages=1).run({})
        self.assertEqual([listing["vin"] for listing in result.listings], ["GOODVIN000000001"])

    def test_duplicate_vins_are_collapsed(self):
        class DupeScraper(DummyScraper):
            def parse(self, body, url):
                return [{"vin": "SAME000000000001"}, {"vin": "same000000000001"}]

        fetcher = base.Fetcher(self.conn, "dummy", self.limits, robots=FakeRobots(), opener=CountingOpener())
        result = DupeScraper(self.conn, self.limits, fetcher, pages=1).run({})
        self.assertEqual(len(result.listings), 1)

    def test_source_is_tagged_on_every_listing(self):
        fetcher = base.Fetcher(self.conn, "dummy", self.limits, robots=FakeRobots(), opener=CountingOpener())
        result = DummyScraper(self.conn, self.limits, fetcher, pages=1).run({})
        self.assertTrue(all(listing["source"] == "dummy" for listing in result.listings))


class LimitsConfigTests(unittest.TestCase):
    def test_defaults_match_the_documented_caps(self):
        limits = base.ScrapeLimits()
        self.assertEqual(limits.max_listings_per_day, 100)
        self.assertEqual(limits.max_pages_per_run, 2)
        self.assertEqual(limits.max_requests_per_day, 20)
        self.assertGreaterEqual(limits.min_seconds_between_requests, 5)

    def test_config_overrides_are_read(self):
        limits = base.ScrapeLimits.from_config({"max_listings_per_day": 50, "max_pages_per_run": 1,
                                                "min_seconds_between_requests": 9})
        self.assertEqual(limits.max_listings_per_day, 50)
        self.assertEqual(limits.max_pages_per_run, 1)
        self.assertEqual(limits.min_seconds_between_requests, 9)

    def test_blank_user_agent_falls_back_to_the_honest_default(self):
        self.assertEqual(base.ScrapeLimits.from_config({"user_agent": ""}).user_agent,
                         base.DEFAULT_USER_AGENT)


if __name__ == "__main__":
    unittest.main()


class RunnerIntegrationTests(unittest.TestCase):
    """pipeline.run_scrapers: the wiring between adapters and the normal pipeline."""

    def setUp(self):
        from carmon.config import load_config
        self.tmp = Path(tempfile.mkdtemp())
        self.config = load_config()
        self.config.data["paths"]["db"] = str(self.tmp / "r.db")
        self.config.data["enrichment"]["nhtsa_enabled"] = False
        self.config.data["enrichment"]["epa_mpg_enabled"] = False
        self.conn = db.init_db(self.config.db_path)

        class FixtureScraper(base.ScraperBase):
            key = "fixture"
            name = "Fixture"
            site = "https://example.test"

            def search_urls(self, search):
                return ["https://example.test/search"]

            def parse(self, body, url):
                return [
                    {"vin": "SCRAPED000000001", "year": 2022, "make": "Toyota", "model": "Corolla",
                     "trim": "LE", "body_type": "Sedan", "fuel_type": "Unleaded", "mileage": 32000,
                     "price_current": 17500, "dealer_name": "Test Motors", "dealer_city": "Columbia",
                     "dealer_state": "TN", "distance_miles": 30.0, "cpo": False,
                     "listing_url": "https://example.test/car/1"},
                    # Filtered out downstream: a pickup is not what we are shopping for.
                    {"vin": "SCRAPED000000002", "year": 2022, "make": "Ford", "model": "F-150",
                     "body_type": "Pickup", "mileage": 30000, "price_current": 19000,
                     "distance_miles": 20.0},
                ]

        self.scraper_class = FixtureScraper
        base.REGISTRY["fixture"] = FixtureScraper
        self.original_fetcher = base.Fetcher

        opener = CountingOpener()
        robots = FakeRobots()

        def patched_fetcher(conn, source, limits=None, robots_arg=None, opener_arg=None, **kwargs):
            return self.original_fetcher(conn, source, limits, robots=robots, opener=opener)

        base.Fetcher = patched_fetcher
        self.opener = opener

    def tearDown(self):
        base.Fetcher = self.original_fetcher
        base.REGISTRY.pop("fixture", None)
        self.conn.close()

    def test_disabled_by_default_and_nothing_is_fetched(self):
        from carmon.pipeline import run_scrapers
        self.config.data["scrapers"]["enabled"] = False
        summary = run_scrapers(self.config, self.conn)
        self.assertFalse(summary["enabled"])
        self.assertIn("Terms of Service", summary["message"])
        self.assertEqual(self.opener.calls, [], "a disabled scraper must not touch the network")

    def test_a_source_switched_off_is_skipped(self):
        from carmon.pipeline import run_scrapers
        self.config.data["scrapers"]["enabled"] = True
        self.config.data["scrapers"]["sources"] = {"fixture": False}
        summary = run_scrapers(self.config, self.conn)
        self.assertEqual(summary["sources"], {})
        self.assertTrue(any("disabled in config" in item for item in summary["skipped"]))

    def test_scraped_listings_go_through_the_normal_filters_and_scoring(self):
        from carmon.pipeline import run_scrapers
        self.config.data["scrapers"].update({
            "enabled": True, "sources": {"fixture": True}, "min_seconds_between_requests": 0,
        })
        summary = run_scrapers(self.config, self.conn, run_date="2026-08-19")
        self.assertEqual(summary["kept"], 1, "the pickup must be filtered out, the Corolla kept")

        stored = db.get_listing(self.conn, "SCRAPED000000001")
        self.assertIsNotNone(stored)
        self.assertEqual(stored["source"], "fixture")
        self.assertIsNotNone(stored["score"])
        self.assertTrue(stored["score_breakdown"])
        self.assertIsNone(db.get_listing(self.conn, "SCRAPED000000002"))

    def test_dry_run_stores_nothing(self):
        from carmon.pipeline import run_scrapers
        self.config.data["scrapers"].update({
            "enabled": True, "sources": {"fixture": True}, "min_seconds_between_requests": 0,
        })
        run_scrapers(self.config, self.conn, dry_run=True)
        self.assertEqual(db.count_listings(self.conn, active_only=False), 0)

    def test_budget_is_reported_before_and_after(self):
        from carmon.pipeline import run_scrapers
        self.config.data["scrapers"].update({
            "enabled": True, "sources": {"fixture": True}, "min_seconds_between_requests": 0,
        })
        summary = run_scrapers(self.config, self.conn)
        self.assertEqual(summary["budget_before"]["requests_used"], 0)
        self.assertGreaterEqual(summary["budget_after"]["requests_used"], 1)
        self.assertEqual(summary["budget_after"]["listings_cap"], 100)


class HealthTrackingTests(unittest.TestCase):
    """Per-adapter health, which is what the website, API and MCP all read."""

    def setUp(self):
        self.conn = db.init_db(Path(tempfile.mkdtemp()) / "h.db")

    def tearDown(self):
        self.conn.close()

    def test_a_successful_run_is_recorded(self):
        db.save_scraper_status(self.conn, "repairpal", {
            "status": "ok", "message": "", "pages_fetched": 2, "listings": 2, "kept_after_filters": 2})
        row = db.get_scraper_status(self.conn, "repairpal")[0]
        self.assertEqual(row["status"], "ok")
        self.assertEqual(row["pages"], 2)
        self.assertEqual(row["ok_runs"], 1)
        self.assertEqual(row["failed_runs"], 0)
        self.assertIsNotNone(row["last_ok_at"])
        self.assertIsNone(row["last_error"])

    def test_a_block_is_recorded_as_a_failure_with_its_reason(self):
        db.save_scraper_status(self.conn, "autotrader", {
            "status": "blocked", "message": "bot challenge instead of the page"})
        row = db.get_scraper_status(self.conn, "autotrader")[0]
        self.assertEqual(row["status"], "blocked")
        self.assertEqual(row["failed_runs"], 1)
        self.assertIn("bot challenge", row["last_error"])
        self.assertIsNotNone(row["last_error_at"])

    def test_tallies_accumulate_across_runs(self):
        for status in ("ok", "blocked", "ok", "error"):
            db.save_scraper_status(self.conn, "cars_com", {"status": status, "message": status})
        row = db.get_scraper_status(self.conn, "cars_com")[0]
        self.assertEqual(row["ok_runs"], 2)
        self.assertEqual(row["failed_runs"], 2)
        self.assertEqual(row["status"], "error", "the latest state wins")

    def test_the_last_success_survives_a_later_failure(self):
        db.save_scraper_status(self.conn, "repairpal", {"status": "ok"})
        first_ok = db.get_scraper_status(self.conn, "repairpal")[0]["last_ok_at"]
        db.save_scraper_status(self.conn, "repairpal", {"status": "blocked", "message": "wall"})
        row = db.get_scraper_status(self.conn, "repairpal")[0]
        self.assertEqual(row["last_ok_at"], first_ok, "you should still see when it last worked")
        self.assertEqual(row["status"], "blocked")

    def test_events_are_listed_newest_first_and_can_be_filtered(self):
        db.record_scrape(self.conn, "repairpal", "page", "https://a.test/1", 200, 1, "")
        db.record_scrape(self.conn, "carmax", "probe", "https://b.test/2", 403, 0, "denied")
        events = db.recent_scrape_events(self.conn, limit=10)
        self.assertEqual(events[0]["source"], "carmax")
        self.assertEqual(len(db.recent_scrape_events(self.conn, source="repairpal")), 1)

    def test_event_limit_is_bounded(self):
        for index in range(30):
            db.record_scrape(self.conn, "repairpal", "page", f"https://a.test/{index}", 200, 0, "")
        self.assertEqual(len(db.recent_scrape_events(self.conn, limit=5)), 5)
        self.assertLessEqual(len(db.recent_scrape_events(self.conn, limit=9999)), 200)

    def test_a_run_writes_health_for_every_source_it_touched(self):
        from carmon.config import load_config
        from carmon.pipeline import run_scrapers

        config = load_config()
        tmp = Path(tempfile.mkdtemp())
        config.data["paths"]["db"] = str(tmp / "run.db")
        config.data["scrapers"].update({"enabled": True, "sources": {"fixture2": True},
                                        "min_seconds_between_requests": 0})
        config.data["enrichment"]["nhtsa_enabled"] = False
        config.data["enrichment"]["epa_mpg_enabled"] = False
        conn = db.init_db(config.db_path)

        class Fixture2(base.ScraperBase):
            key = "fixture2"
            name = "Fixture Two"
            site = "https://example.test"

            def search_urls(self, search):
                return ["https://example.test/s"]

            def parse(self, body, url):
                return [{"vin": "HEALTH0000000001", "make": "Toyota", "model": "Corolla",
                         "year": 2022, "mileage": 30000, "price_current": 17000,
                         "body_type": "Sedan", "distance_miles": 20.0}]

        base.REGISTRY["fixture2"] = Fixture2
        original = base.Fetcher
        base.Fetcher = lambda conn_, source, limits=None, **kwargs: original(
            conn_, source, limits, robots=FakeRobots(), opener=CountingOpener())
        try:
            run_scrapers(config, conn, run_date="2026-08-19")
        finally:
            base.Fetcher = original
            base.REGISTRY.pop("fixture2", None)

        row = db.get_scraper_status(conn, "fixture2")[0]
        self.assertEqual(row["status"], "ok")
        self.assertEqual(row["kept"], 1)
        conn.close()


class ReferenceSourceTests(unittest.TestCase):
    """A reference adapter (RepairPal) is keyed by model, not by the listing search."""

    def setUp(self):
        from carmon.config import load_config
        self.tmp = Path(tempfile.mkdtemp())
        self.config = load_config()
        self.config.data["paths"]["db"] = str(self.tmp / "ref.db")
        self.config.data["scrapers"].update({
            "enabled": True, "sources": {"reference_fixture": True}, "min_seconds_between_requests": 0,
        })
        self.conn = db.init_db(self.config.db_path)
        self.opener = CountingOpener()

        class ReferenceFixture(base.ScraperBase):
            key = "reference_fixture"
            name = "Reference Fixture"
            site = "https://example.test"
            kind = "reference"

            def search_urls(self, search):
                make, model = search.get("make"), search.get("model")
                return [f"https://example.test/{make}/{model}"] if make and model else []

            def parse(self, body, url):
                make, model = url.rsplit("/", 2)[-2:]
                return [{"make": make, "model": model, "annual_repair_cost": 400.0}]

        base.REGISTRY["reference_fixture"] = ReferenceFixture
        self.original_fetcher = base.Fetcher
        opener, robots = self.opener, FakeRobots()
        base.Fetcher = lambda conn_, source, limits=None, **kwargs: self.original_fetcher(
            conn_, source, limits, robots=robots, opener=opener)
        # A module-level store() is how the runner persists reference records.
        import sys as _sys
        _sys.modules[ReferenceFixture.__module__].store = getattr(
            _sys.modules[ReferenceFixture.__module__], "store", None)

    def tearDown(self):
        base.Fetcher = self.original_fetcher
        base.REGISTRY.pop("reference_fixture", None)
        self.conn.close()

    def test_models_come_from_the_database_then_the_preferred_list(self):
        from carmon.pipeline import reference_models
        db.upsert_listing(self.conn, {"vin": "REF0000000000001", "make": "Subaru",
                                      "model": "Impreza", "year": 2022, "price_current": 17000})
        models = reference_models(self.config, self.conn)
        pairs = [(entry["make"], entry["model"]) for entry in models]
        self.assertEqual(pairs[0], ("Subaru", "Impreza"), "cars actually for sale come first")
        self.assertIn(("Toyota", "Corolla"), pairs, "the preferred list fills in the rest")

    def test_an_empty_database_still_looks_up_the_preferred_models(self):
        from carmon.pipeline import reference_models
        models = reference_models(self.config, self.conn)
        self.assertTrue(models)
        self.assertIn(("Honda", "Civic"), [(m["make"], m["model"]) for m in models])

    def test_the_runner_asks_once_per_model(self):
        from carmon.pipeline import run_scrapers
        summary = run_scrapers(self.config, self.conn)
        entry = summary["sources"]["reference_fixture"]
        self.assertEqual(entry["status"], "ok")
        self.assertEqual(len(entry["models"]), 5, "one lookup per preferred model")
        self.assertEqual(len(self.opener.calls), 5)

    def test_the_runner_stops_when_the_request_budget_runs_out(self):
        from carmon.pipeline import run_scrapers
        self.config.data["scrapers"]["max_requests_per_day"] = 2
        summary = run_scrapers(self.config, self.conn)
        entry = summary["sources"]["reference_fixture"]
        self.assertLessEqual(len(self.opener.calls), 2)
        self.assertIn(entry["status"], ("budget", "ok"))
