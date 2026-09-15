"""Tests for the RepairPal reference-data adapter.

No network access: every fetch goes through an injected opener callable and synthetic
fixture HTML written here, never real page dumps.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from carmon import db
from carmon.scrapers import repairpal
from carmon.scrapers.base import Fetcher, ScrapeLimits
from carmon.scrapers.repairpal import RepairPalScraper, _slugify, store


# --- synthetic fixtures ------------------------------------------------------

FIXTURE_LD_JSON = """
<html><head>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Toyota Corolla",
  "brand": {"@type": "Thing", "name": "Toyota"},
  "model": "Corolla",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.0",
    "bestRating": "5"
  },
  "annualRepairCost": 441,
  "visitsPerYear": 0.3,
  "severePct": 9,
  "rank": "4th out of 32 compact cars",
  "commonProblems": ["Excessive oil consumption", "Ignition coil failure", "Water pump leaks"]
}
</script>
</head><body><h1>Toyota Corolla Reliability</h1>
<p>""" + ("The Toyota Corolla is a compact car known for low running costs. " * 60) + """</p>
</body></html>
"""

# Framework-hydration-style embedded JSON, deliberately missing severity/rank to exercise
# "missing field -> None, not an error".
FIXTURE_EMBEDDED_JSON = """
<html><body>
<script id="__NEXT_DATA__" type="application/json">
{"props": {"pageProps": {"vehicle": {
  "make": "Honda",
  "model": "Civic",
  "reliability": {"ratingValue": 4.5, "bestRating": 5},
  "costs": {"annualRepairCost": 428},
  "visitsPerYear": 0.9,
  "commonProblems": [{"name": "AC compressor failure"}, {"name": "Engine misfire"}]
}}}}
</script>
</body></html>
"""

FIXTURE_PLAIN_TEXT = """
<html><body>
<h1>Mazda Mazda3 Reliability</h1>
<p>The average annual repair cost for a Mazda is $500 which is about average for compact cars.</p>
<p>RepairPal Reliability Rating: 4.0 out of 5.0. This rating ranks it 5th out of 32 compact cars.</p>
<p>Owners visit a shop for unscheduled repairs 0.4 visits per year, and 12% of repairs are severe.</p>
<p>Common Problems: Excessive oil consumption, Ignition coil failure, Water pump leaks</p>
</body></html>
"""

FIXTURE_GARBAGE = "<html><body><p>Nothing relevant on this page at all.</p></body></html>"

CHALLENGE_BODY = "Just a moment... enable javascript and cookies to continue."


class _CountingOpener:
    """Fake `opener` callable(url, headers, timeout) -> (status, body). No network."""

    def __init__(self, body: str, status: int = 200):
        self.body = body
        self.status = status
        self.calls = 0
        self.urls = []

    def __call__(self, url, headers, timeout):
        self.calls += 1
        self.urls.append(url)
        return self.status, self.body


class _AllowAllRobots:
    """Stand-in for RobotsCache that permits everything, so tests need no network."""

    def check(self, url):
        return None

    def crawl_delay(self, url):
        return None


def _make_scraper(conn, opener, limits=None):
    limits = limits or ScrapeLimits(min_seconds_between_requests=0)
    fetcher = Fetcher(conn, "repairpal", limits, robots=_AllowAllRobots(), opener=opener)
    return RepairPalScraper(conn, limits, fetcher)


class SlugifyTests(unittest.TestCase):
    def test_basic_slug(self):
        self.assertEqual(_slugify("Toyota"), "toyota")

    def test_digit_suffix_model(self):
        self.assertEqual(_slugify("Mazda3"), "mazda3")

    def test_two_word_model(self):
        self.assertEqual(_slugify("Grand Cherokee"), "grand-cherokee")

    def test_search_urls_build_two_slugged_urls(self):
        conn = db.init_db(":memory:")
        scraper = _make_scraper(conn, _CountingOpener(FIXTURE_LD_JSON))
        urls = scraper.search_urls({"make": "Mazda", "model": "Mazda3"})
        self.assertEqual(len(urls), 2)
        self.assertTrue(all("mazda/mazda3" in u for u in urls))

        urls = scraper.search_urls({"make": "Jeep", "model": "Grand Cherokee"})
        self.assertEqual(len(urls), 2)
        self.assertTrue(all("jeep/grand-cherokee" in u for u in urls))

    def test_search_urls_empty_without_make_or_model(self):
        conn = db.init_db(":memory:")
        scraper = _make_scraper(conn, _CountingOpener(FIXTURE_LD_JSON))
        self.assertEqual(scraper.search_urls({}), [])
        self.assertEqual(scraper.search_urls({"make": "Toyota"}), [])
        self.assertEqual(scraper.search_urls({"model": "Corolla"}), [])


class ParseTests(unittest.TestCase):
    def setUp(self):
        self.conn = db.init_db(":memory:")
        self.scraper = _make_scraper(self.conn, _CountingOpener(FIXTURE_LD_JSON))

    def test_ld_json_fixture(self):
        records = self.scraper.parse(FIXTURE_LD_JSON, "https://repairpal.com/toyota/corolla")
        self.assertEqual(len(records), 1)
        r = records[0]
        self.assertEqual(r["make"], "Toyota")
        self.assertEqual(r["model"], "Corolla")
        self.assertEqual(r["annual_repair_cost"], 441.0)
        self.assertEqual(r["reliability_rating"], 4.0)
        self.assertEqual(r["rating_scale"], 5.0)
        self.assertEqual(r["visits_per_year"], 0.3)
        self.assertEqual(r["severity_pct"], 9.0)
        self.assertEqual(r["rank_text"], "4th out of 32 compact cars")
        self.assertEqual(
            r["common_problems"],
            ["Excessive oil consumption", "Ignition coil failure", "Water pump leaks"],
        )
        self.assertEqual(r["source_url"], "https://repairpal.com/toyota/corolla")

    def test_embedded_json_fixture_missing_fields_are_none(self):
        records = self.scraper.parse(FIXTURE_EMBEDDED_JSON, "https://repairpal.com/honda/civic")
        self.assertEqual(len(records), 1)
        r = records[0]
        self.assertEqual(r["make"], "Honda")
        self.assertEqual(r["model"], "Civic")
        self.assertEqual(r["annual_repair_cost"], 428.0)
        self.assertEqual(r["reliability_rating"], 4.5)
        self.assertEqual(r["rating_scale"], 5.0)
        self.assertEqual(r["visits_per_year"], 0.9)
        # Not present in this fixture: must come back as None, not raise.
        self.assertIsNone(r["severity_pct"])
        self.assertIsNone(r["rank_text"])
        self.assertEqual(r["common_problems"], ["AC compressor failure", "Engine misfire"])

    def test_plain_text_fixture(self):
        records = self.scraper.parse(FIXTURE_PLAIN_TEXT, "https://repairpal.com/mazda/mazda3")
        self.assertEqual(len(records), 1)
        r = records[0]
        # Neither JSON strategy applies here, so make/model fall back to the URL slug.
        self.assertEqual(r["make"], "Mazda")
        self.assertEqual(r["model"], "Mazda3")
        self.assertEqual(r["annual_repair_cost"], 500.0)
        self.assertEqual(r["reliability_rating"], 4.0)
        self.assertEqual(r["rating_scale"], 5.0)
        self.assertEqual(r["visits_per_year"], 0.4)
        self.assertEqual(r["severity_pct"], 12.0)
        self.assertEqual(r["rank_text"], "5th out of 32 compact cars")
        self.assertEqual(
            r["common_problems"],
            ["Excessive oil consumption", "Ignition coil failure", "Water pump leaks"],
        )

    def test_garbage_page_returns_empty_list_without_raising(self):
        records = self.scraper.parse(FIXTURE_GARBAGE, "https://repairpal.com/nope/nope")
        self.assertEqual(records, [])

    def test_empty_body_returns_empty_list(self):
        self.assertEqual(self.scraper.parse("", "https://repairpal.com/nope/nope"), [])


class StoreTests(unittest.TestCase):
    def test_store_persists_via_db(self):
        conn = db.init_db(":memory:")
        record = {
            "make": "Toyota",
            "model": "Corolla",
            "annual_repair_cost": 441.0,
            "reliability_rating": 4.0,
            "rating_scale": 5.0,
            "visits_per_year": 0.3,
            "severity_pct": 9.0,
            "rank_text": "4th out of 32 compact cars",
            "common_problems": ["Excessive oil consumption"],
            "source_url": "https://repairpal.com/toyota/corolla",
        }
        store(conn, record)
        stored = db.get_repair_cost(conn, "Toyota", "Corolla")
        self.assertIsNotNone(stored)
        self.assertEqual(stored["annual_repair_cost"], 441.0)
        self.assertEqual(stored["common_problems"], ["Excessive oil consumption"])


class CapsAndRunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.conn = db.init_db(self.tmp / "t.db")

    def test_run_caps_pages_per_run_and_updates_ledger(self):
        limits = ScrapeLimits(
            max_pages_per_run=2, max_requests_per_day=3, min_seconds_between_requests=0
        )
        opener = _CountingOpener(FIXTURE_LD_JSON)
        scraper = _make_scraper(self.conn, opener, limits)

        result = scraper.run({"make": "Toyota", "model": "Corolla"})

        # search_urls offers 2 candidate URLs for one model; the run must not exceed
        # max_pages_per_run and must not fetch more than it asked for.
        self.assertLessEqual(result.pages_fetched, 2)
        self.assertLessEqual(opener.calls, 2)
        self.assertEqual(opener.calls, result.pages_fetched)
        self.assertEqual(result.status, "ok")
        self.assertEqual(len(result.listings), result.pages_fetched)

        usage = db.scrape_usage_today(self.conn)
        # The ledger must have logged at least one row per page fetched (it also logs a
        # separate "listings taken" row per page, which is how the daily listing cap is
        # enforced) - so it always reflects at least as many rows as pages fetched.
        self.assertGreaterEqual(usage["requests"], result.pages_fetched)
        self.assertEqual(usage["listings"], result.pages_fetched)

    def test_run_stops_on_challenge_and_does_not_retry(self):
        limits = ScrapeLimits(min_seconds_between_requests=0)
        opener = _CountingOpener(CHALLENGE_BODY, status=200)
        scraper = _make_scraper(self.conn, opener, limits)

        result = scraper.run({"make": "Ford", "model": "Focus"})

        self.assertEqual(result.status, "blocked")
        self.assertEqual(opener.calls, 1)
        self.assertEqual(result.listings, [])

    def test_run_returns_empty_urls_when_search_lacks_make_model(self):
        limits = ScrapeLimits(min_seconds_between_requests=0)
        opener = _CountingOpener(FIXTURE_LD_JSON)
        scraper = _make_scraper(self.conn, opener, limits)

        result = scraper.run({})

        self.assertEqual(result.urls, [])
        self.assertEqual(opener.calls, 0)
        self.assertEqual(result.listings, [])


if __name__ == "__main__":
    unittest.main()


class ScopeGuardTests(unittest.TestCase):
    """RepairPal's bare /make/model page quotes BRAND figures, not model ones.

    Verified against the live site: /toyota/corolla reports $441 and "8th out of 32 for all
    car brands" (that is Toyota overall), while /reliability/toyota/corolla reports $362 and
    "1st out of 36 for compact cars" (that is the Corolla). Storing the first as if it were
    the second would be quietly wrong, so scope is detected and brand rows are refused.
    """

    def setUp(self):
        self.conn = db.init_db(Path(tempfile.mkdtemp()) / "t.db")
        self.brand = {
            "make": "Toyota", "model": "Corolla", "annual_repair_cost": 441.0,
            "reliability_rating": 4.0, "rank_text": "8th out of 32 for all car brands",
            "source_url": "https://repairpal.com/toyota/corolla",
        }
        self.model = {
            "make": "Toyota", "model": "Corolla", "annual_repair_cost": 362.0,
            "reliability_rating": 4.5, "rank_text": "1st out of 36 for compact cars",
            "source_url": "https://repairpal.com/reliability/toyota/corolla",
        }

    def tearDown(self):
        self.conn.close()

    def test_scope_is_detected_from_the_url_and_ranking(self):
        self.assertEqual(repairpal.record_scope(self.brand), "brand")
        self.assertEqual(repairpal.record_scope(self.model), "model")

    def test_brand_level_figures_are_not_stored_as_model_data(self):
        repairpal.store(self.conn, self.brand)
        self.assertIsNone(db.get_repair_cost(self.conn, "Toyota", "Corolla"))

    def test_model_level_figures_are_stored(self):
        repairpal.store(self.conn, self.model)
        stored = db.get_repair_cost(self.conn, "Toyota", "Corolla")
        self.assertEqual(stored["annual_repair_cost"], 362.0)
        self.assertEqual(stored["reliability_rating"], 4.5)

    def test_brand_data_cannot_overwrite_good_model_data(self):
        repairpal.store(self.conn, self.model)
        repairpal.store(self.conn, self.brand)
        self.assertEqual(db.get_repair_cost(self.conn, "Toyota", "Corolla")["annual_repair_cost"], 362.0)

    def test_the_model_specific_url_is_tried_first(self):
        scraper = _make_scraper(self.conn, _CountingOpener(FIXTURE_LD_JSON), ScrapeLimits())
        urls = scraper.search_urls({"make": "Toyota", "model": "Corolla"})
        self.assertIn("/reliability/", urls[0], "the model-level page must be preferred")
