"""Tests for the Carvana scraper adapter.

No network access: every fetch in here goes through a synthetic, injectable `opener`
callable (see `carmon.scrapers.base.Fetcher`), and every page body is a small fixture
written by hand below -- never real page source pulled from the live site. As noted in
`carmon/scrapers/carvana.py`, the parser has never been exercised against real Carvana
HTML because robots.txt itself is unreachable (HTTP 403 behind a Cloudflare JS challenge)
from this environment; these tests only prove the adapter behaves correctly against the
schema.org / Next.js / markup shapes it was written to expect, and that the shared
budget/robots/challenge machinery in `base.py` is wired up correctly.
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from carmon import db
from carmon.scrapers import base
from carmon.scrapers.carvana import CarvanaScraper

# Harmless filler so fixtures look like a realistic page rather than a bare snippet; it
# contains none of base.CHALLENGE_MARKERS / CHALLENGE_PLATFORMS so it never trips the
# bot-challenge detector on its own.
PAGE_PADDING = "<!-- " + ("filler " * 400) + " -->"

CURRENT_YEAR = datetime.now(timezone.utc).year

SEARCH = {
    "zip": "38464",
    "radius_miles": 100,
    "year_min": 2021,
    "price_max": 20000,
    "mileage_max": 60000,
}


# --- fixtures ---------------------------------------------------------------

JSON_LD_FIXTURE = """
<html><head>
<script type="application/ld+json">
[
  {
    "@context": "https://schema.org",
    "@type": "Vehicle",
    "name": "2021 Honda Accord Sport",
    "vehicleIdentificationNumber": "1HGCV1F34MA111111",
    "mileageFromOdometer": "28,450 miles",
    "bodyType": "Sedan",
    "fuelType": "Gasoline",
    "offers": {"@type": "Offer", "price": "$21,995", "seller": {"@type": "Organization", "name": "Carvana"}},
    "url": "https://www.carvana.com/vehicle/1HGCV1F34MA111111"
  },
  {
    "@context": "https://schema.org",
    "@type": "Car",
    "vehicleIdentificationNumber": "5N1AZ2MS8NC222222",
    "brand": {"@type": "Brand", "name": "Nissan"},
    "model": {"@type": "ProductModel", "name": "Rogue"},
    "vehicleConfiguration": "SL",
    "vehicleModelDate": "2022",
    "mileageFromOdometer": "37,412 mi.",
    "manufacturer_certified": true,
    "offers": {"@type": "Offer", "price": "$18,995"},
    "url": "https://www.carvana.com/vehicle/5N1AZ2MS8NC222222"
  },
  {
    "@context": "https://schema.org",
    "@type": "Vehicle",
    "vehicleIdentificationNumber": "3VW2B7AJ5FM333333",
    "name": "2020 Volkswagen Jetta S",
    "description": "Carvana certified and inspected, ready for delivery to your door.",
    "offers": {"@type": "Offer", "price": "16400"},
    "url": "https://www.carvana.com/vehicle/3VW2B7AJ5FM333333"
  },
  {
    "@context": "https://schema.org",
    "@type": "Product",
    "name": "2021 Kia Soul LX",
    "offers": {"@type": "Offer", "price": "16400"},
    "url": "https://www.carvana.com/vehicle/no-vin-here"
  }
]
</script>
</head><body>""" + PAGE_PADDING + """</body></html>
"""

NEXT_DATA_FIXTURE = """
<html><head>
<script id="__NEXT_DATA__" type="application/json">
{"props": {"pageProps": {"initialState": {"inventory": {"vehicles": [
  {"vin": "1G1ZD5ST8LF444444", "year": 2019, "make": "Chevrolet", "model": "Malibu", "trim": "LT",
   "mileage": 45210, "price": 15990, "bodyType": "Sedan", "fuelType": "Gasoline",
   "stockNumber": "CV55501", "url": "/vehicle/1G1ZD5ST8LF444444"},
  {"vin": "JHMFC1F39JX555555", "year": 2018, "make": "Honda", "model": "Civic", "trim": "LX",
   "mileage": "61,200", "price": "$12,300", "stockNumber": "CV55502",
   "url": "/vehicle/JHMFC1F39JX555555"}
]}}}}}
</script>
</head><body>""" + PAGE_PADDING + """</body></html>
"""

HTML_CARD_FIXTURE = """
<html><body>
<div class="result-tile" data-vin="1C4RJFAG9FC666666" data-year="2019" data-make="Jeep"
     data-model="Grand Cherokee" data-trim="Limited" data-mileage="41,200" data-price="$21,988"
     data-stock-number="CV66601">
  <a href="/vehicle/1C4RJFAG9FC666666"></a>
</div>
<div class="result-tile">
  <a href="/vehicle/no-vin-in-markup">
    <h3 class="title">2020 Toyota Camry SE</h3>
  </a>
  <span class="price">$19,500</span>
  <div class="mileage">33,102 miles</div>
  <div class="stock-number">CV98765</div>
</div>
</body></html>
"""

EMPTY_FIXTURE = "<html><body><p>No results found.</p></body></html>"

CHALLENGE_BODY = (
    "<html><body>Just a moment...<br>Please enable javascript and cookies to "
    "continue.</body></html>"
)

# Fixtures for the end-to-end cap test: seven unique VINs split across two pages.
CAP_PAGE_1 = """
<html><head><script type="application/ld+json">
[
  {"@type": "Vehicle", "vehicleIdentificationNumber": "CVIN0000000000001", "name": "2021 Mazda 3",
   "offers": {"price": "17000"}},
  {"@type": "Vehicle", "vehicleIdentificationNumber": "CVIN0000000000002", "name": "2021 Mazda CX-5",
   "offers": {"price": "18000"}},
  {"@type": "Vehicle", "vehicleIdentificationNumber": "CVIN0000000000003", "name": "2022 Subaru Outback",
   "offers": {"price": "19000"}}
]
</script></head><body>""" + PAGE_PADDING + """</body></html>
"""

CAP_PAGE_2 = """
<html><head><script type="application/ld+json">
[
  {"@type": "Vehicle", "vehicleIdentificationNumber": "CVIN0000000000004", "name": "2022 Subaru Forester",
   "offers": {"price": "19500"}},
  {"@type": "Vehicle", "vehicleIdentificationNumber": "CVIN0000000000005", "name": "2021 Toyota RAV4",
   "offers": {"price": "20000"}},
  {"@type": "Vehicle", "vehicleIdentificationNumber": "CVIN0000000000006", "name": "2021 Toyota Camry",
   "offers": {"price": "17500"}},
  {"@type": "Vehicle", "vehicleIdentificationNumber": "CVIN0000000000007", "name": "2021 Honda CR-V",
   "offers": {"price": "21000"}}
]
</script></head><body>""" + PAGE_PADDING + """</body></html>
"""


class FakeRobots:
    """Permissive stand-in for RobotsCache: everything is allowed, no crawl-delay."""

    def check(self, url: str) -> None:
        return None

    def crawl_delay(self, url: str):
        return None


class DisallowingRobots:
    """Stand-in for what RobotsCache does when robots.txt cannot be read: fail closed."""

    def check(self, url: str) -> None:
        raise base.RobotsDisallowed("example.test: robots.txt could not be read (simulated)")

    def crawl_delay(self, url: str):
        return None


class CountingOpener:
    """Injectable opener that counts calls and serves canned (status, body) responses.

    `responses` may be a single (status, body) tuple served for every call, or a callable
    `url -> (status, body)` for tests that need different bodies per page.
    """

    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def __call__(self, url, headers, timeout):
        self.calls.append(url)
        if callable(self.responses):
            return self.responses(url)
        return self.responses


def make_conn(tmp_dir: Path):
    return db.init_db(Path(tmp_dir) / "test.db")


class SearchUrlsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.conn = make_conn(self._tmp.name)

    def tearDown(self):
        self.conn.close()
        self._tmp.cleanup()

    def test_urls_carry_configured_search_criteria(self):
        scraper = CarvanaScraper(self.conn, limits=base.ScrapeLimits(max_pages_per_run=1))
        urls = scraper.search_urls(SEARCH)
        self.assertEqual(len(urls), 1)
        parsed = urlparse(urls[0])
        self.assertEqual(parsed.netloc, "www.carvana.com")
        self.assertEqual(parsed.path, "/cars/filters")
        query = parse_qs(parsed.query)
        self.assertEqual(query["zip"], ["38464"])
        self.assertEqual(query["price-range"], ["0-20000"])
        self.assertEqual(query["mileage-range"], ["0-60000"])
        self.assertEqual(query["year-range"], [f"2021-{CURRENT_YEAR}"])
        self.assertEqual(query["page"], ["1"])

    def test_paging_produces_distinct_urls_capped_at_max_pages(self):
        scraper = CarvanaScraper(self.conn, limits=base.ScrapeLimits(max_pages_per_run=3))
        urls = scraper.search_urls(SEARCH)
        self.assertEqual(len(urls), 3)
        self.assertEqual(len(set(urls)), 3)  # distinct
        pages = [parse_qs(urlparse(u).query)["page"][0] for u in urls]
        self.assertEqual(pages, ["1", "2", "3"])

    def test_search_urls_respects_lower_max_pages(self):
        scraper = CarvanaScraper(self.conn, limits=base.ScrapeLimits(max_pages_per_run=1))
        urls = scraper.search_urls(SEARCH)
        self.assertEqual(len(urls), 1)

    def test_no_zip_means_no_urls(self):
        scraper = CarvanaScraper(self.conn, limits=base.ScrapeLimits(max_pages_per_run=2))
        self.assertEqual(scraper.search_urls({}), [])


class ParseTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.conn = make_conn(self._tmp.name)
        self.scraper = CarvanaScraper(self.conn, limits=base.ScrapeLimits())

    def tearDown(self):
        self.conn.close()
        self._tmp.cleanup()

    def test_parses_json_ld_vehicles(self):
        listings = self.scraper.parse(JSON_LD_FIXTURE, "https://www.carvana.com/cars/filters?page=1")
        by_vin = {item.get("vin"): item for item in listings}

        self.assertIn("1HGCV1F34MA111111", by_vin)
        first = by_vin["1HGCV1F34MA111111"]
        self.assertEqual(first["year"], 2021)
        self.assertEqual(first["make"], "Honda")
        self.assertEqual(first["model"], "Accord")
        self.assertEqual(first["trim"], "Sport")
        self.assertEqual(first["price_current"], 21995)      # "$21,995" -> 21995
        self.assertEqual(first["mileage"], 28450)             # "28,450 miles" -> 28450
        self.assertEqual(first["body_type"], "Sedan")
        self.assertEqual(first["fuel_type"], "Gasoline")
        self.assertFalse(first["cpo"])

        self.assertIn("5N1AZ2MS8NC222222", by_vin)
        second = by_vin["5N1AZ2MS8NC222222"]
        self.assertEqual(second["year"], 2022)
        self.assertEqual(second["make"], "Nissan")
        self.assertEqual(second["model"], "Rogue")
        self.assertEqual(second["trim"], "SL")
        self.assertEqual(second["price_current"], 18995)      # "$18,995" -> 18995
        self.assertEqual(second["mileage"], 37412)             # "37,412 mi." -> 37412
        self.assertTrue(second["cpo"])   # explicit manufacturer_certified: true

        self.assertIn("3VW2B7AJ5FM333333", by_vin)
        third = by_vin["3VW2B7AJ5FM333333"]
        # "Carvana certified and inspected" is Carvana's own inspection language, not a
        # manufacturer CPO claim -- it must NOT set cpo True.
        self.assertFalse(third["cpo"])
        self.assertEqual(third["price_current"], 16400)

        # The fourth vehicle has no VIN anywhere -- parse() may still return it; it just
        # won't have a usable 'vin'. ScraperBase.run() is what drops it.
        no_vin_listings = [item for item in listings if not item.get("vin")]
        self.assertEqual(len(no_vin_listings), 1)
        self.assertEqual(no_vin_listings[0].get("price_current"), 16400)

        # Every listing produced by this adapter, regardless of strategy: no distance, an
        # explicit delivery-only flag, and Carvana as the dealer of record.
        for item in listings:
            self.assertIsNone(item.get("distance_miles"))
            self.assertTrue(item["delivery_only"])
            self.assertEqual(item["dealer_name"], "Carvana")

    def test_parses_next_data_blob(self):
        listings = self.scraper.parse(NEXT_DATA_FIXTURE, "https://www.carvana.com/cars/filters?page=1")
        by_vin = {item.get("vin"): item for item in listings}
        self.assertEqual(len(listings), 2)

        chevy = by_vin["1G1ZD5ST8LF444444"]
        self.assertEqual(chevy["year"], 2019)
        self.assertEqual(chevy["make"], "Chevrolet")
        self.assertEqual(chevy["model"], "Malibu")
        self.assertEqual(chevy["trim"], "LT")
        self.assertEqual(chevy["mileage"], 45210)
        self.assertEqual(chevy["price_current"], 15990)
        self.assertEqual(chevy["stock_number"], "CV55501")
        self.assertIsNone(chevy["distance_miles"])
        self.assertTrue(chevy["delivery_only"])

        civic = by_vin["JHMFC1F39JX555555"]
        self.assertEqual(civic["mileage"], 61200)              # "61,200" -> 61200
        self.assertEqual(civic["price_current"], 12300)         # "$12,300" -> 12300
        self.assertEqual(civic["stock_number"], "CV55502")

    def test_parses_plain_html_cards(self):
        listings = self.scraper.parse(HTML_CARD_FIXTURE, "https://www.carvana.com/cars/filters?page=1")
        self.assertEqual(len(listings), 2)

        by_vin = {item.get("vin"): item for item in listings if item.get("vin")}
        jeep = by_vin["1C4RJFAG9FC666666"]
        self.assertEqual(jeep["year"], 2019)
        self.assertEqual(jeep["make"], "Jeep")
        self.assertEqual(jeep["model"], "Grand Cherokee")
        self.assertEqual(jeep["trim"], "Limited")
        self.assertEqual(jeep["mileage"], 41200)                # "41,200" -> 41200
        self.assertEqual(jeep["price_current"], 21988)           # "$21,988" -> 21988
        self.assertEqual(jeep["stock_number"], "CV66601")
        self.assertIsNone(jeep["distance_miles"])
        self.assertTrue(jeep["delivery_only"])

        # The second card carries no VIN anywhere in the markup (a real limitation noted
        # in the module docstring); it is still returned by parse() sans VIN.
        no_vin = [item for item in listings if not item.get("vin")]
        self.assertEqual(len(no_vin), 1)
        self.assertEqual(no_vin[0]["year"], 2020)
        self.assertEqual(no_vin[0]["make"], "Toyota")
        self.assertEqual(no_vin[0]["model"], "Camry")
        self.assertEqual(no_vin[0]["trim"], "SE")
        self.assertEqual(no_vin[0]["price_current"], 19500)
        self.assertEqual(no_vin[0]["mileage"], 33102)
        self.assertEqual(no_vin[0]["stock_number"], "CV98765")

    def test_empty_or_garbage_page_returns_empty_list(self):
        self.assertEqual(self.scraper.parse(EMPTY_FIXTURE, "https://www.carvana.com/cars/filters"), [])
        self.assertEqual(self.scraper.parse("", "https://www.carvana.com/cars/filters"), [])
        self.assertEqual(
            self.scraper.parse("not even html {{{ ]] garbage", "https://www.carvana.com/cars/filters"),
            [],
        )

    def test_vinless_listing_is_dropped_by_run(self):
        opener = CountingOpener((200, JSON_LD_FIXTURE))
        limits = base.ScrapeLimits(max_pages_per_run=1, min_seconds_between_requests=0)
        fetcher = base.Fetcher(self.conn, self.scraper.key, limits, robots=FakeRobots(), opener=opener)
        scraper = CarvanaScraper(self.conn, limits=limits, fetcher=fetcher)

        result = scraper.run(SEARCH)

        self.assertEqual(result.status, "ok")
        vins = [item["vin"] for item in result.listings]
        self.assertNotIn("", vins)
        self.assertTrue(all(vin for vin in vins))
        # Three VIN-bearing vehicles made it through; the VIN-less one did not.
        self.assertEqual(len(result.listings), 3)
        for item in result.listings:
            self.assertIsNone(item.get("distance_miles"))
            self.assertTrue(item.get("delivery_only"))


class CapsAndSafetyTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.conn = make_conn(self._tmp.name)

    def tearDown(self):
        self.conn.close()
        self._tmp.cleanup()

    def test_daily_and_page_caps_hold_end_to_end(self):
        limits = base.ScrapeLimits(max_pages_per_run=2, max_listings_per_day=5, min_seconds_between_requests=0)

        def respond(url):
            query = parse_qs(urlparse(url).query)
            page = query.get("page", ["1"])[0]
            return (200, CAP_PAGE_1 if page == "1" else CAP_PAGE_2)

        opener = CountingOpener(respond)
        fetcher = base.Fetcher(self.conn, "carvana", limits, robots=FakeRobots(), opener=opener)
        scraper = CarvanaScraper(self.conn, limits=limits, fetcher=fetcher)

        result = scraper.run(SEARCH)

        self.assertLessEqual(result.pages_fetched, 2)
        self.assertLessEqual(len(opener.calls), 2)
        self.assertLessEqual(len(result.listings), 5)
        self.assertEqual(len(result.listings), 5)  # exactly the cap, even though 7 were on offer

        usage = db.scrape_usage_today(self.conn, source="carvana")
        self.assertEqual(usage["listings"], 5)
        self.assertEqual(usage["requests"], len(opener.calls))

    def test_fails_closed_when_robots_cannot_be_read(self):
        limits = base.ScrapeLimits(max_pages_per_run=2, min_seconds_between_requests=0)
        opener = CountingOpener((200, JSON_LD_FIXTURE))
        fetcher = base.Fetcher(self.conn, "carvana", limits, robots=DisallowingRobots(), opener=opener)
        scraper = CarvanaScraper(self.conn, limits=limits, fetcher=fetcher)

        result = scraper.run(SEARCH)

        self.assertEqual(result.status, "disallowed")
        self.assertEqual(len(opener.calls), 0)
        self.assertEqual(result.listings, [])

    def test_challenge_response_is_blocked_without_retry(self):
        limits = base.ScrapeLimits(max_pages_per_run=2, min_seconds_between_requests=0)
        opener = CountingOpener((200, CHALLENGE_BODY))
        fetcher = base.Fetcher(self.conn, "carvana", limits, robots=FakeRobots(), opener=opener)
        scraper = CarvanaScraper(self.conn, limits=limits, fetcher=fetcher)

        result = scraper.run(SEARCH)

        self.assertEqual(result.status, "blocked")
        self.assertEqual(len(opener.calls), 1)  # no retry
        self.assertEqual(result.listings, [])


if __name__ == "__main__":
    unittest.main()
