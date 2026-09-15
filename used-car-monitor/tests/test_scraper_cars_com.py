"""Tests for the Cars.com scraper adapter.

No network access: every fetch in here goes through a synthetic, injectable `opener`
callable (see `carmon.scrapers.base.Fetcher`), and every page body is a small fixture
written by hand below -- never real page source pulled from the live site. As noted in
`carmon/scrapers/cars_com.py`, the parser has never been exercised against real Cars.com
HTML because robots.txt itself is unreachable (HTTP 403) from this environment; these
tests only prove the adapter behaves correctly against the schema.org / markup shapes it
was written to expect, and that the shared budget/robots/challenge machinery in `base.py`
is wired up correctly.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from carmon import db
from carmon.scrapers import base
from carmon.scrapers.cars_com import CarsComScraper

# base.looks_like_challenge() treats any response under 2500 bytes that contains both
# "<script" and "</html>" as a JS-challenge shell (see carmon/scrapers/base.py). Real
# Cars.com search-results pages are far larger than that; this filler stands in for the
# rest of a real page's markup so JSON-LD fixtures below aren't mistaken for a challenge.
PAGE_PADDING = "<!-- " + ("filler " * 400) + " -->"

SEARCH = {
    "zip": "38464",
    "radius_miles": 100,
    "year_min": 2021,
    "price_max": 20000,
    "mileage_max": 60000,
    "rows_per_page": 20,
}


# --- fixtures ---------------------------------------------------------------

JSON_LD_FIXTURE = """
<html><head>
<script type="application/ld+json">
[
  {
    "@context": "https://schema.org",
    "@type": "Vehicle",
    "name": "2022 Honda Accord EX-L",
    "vehicleIdentificationNumber": "1HGCV1F34NA123456",
    "mileageFromOdometer": "28450",
    "offers": {
      "@type": "Offer",
      "price": "21995",
      "priceCurrency": "USD",
      "seller": {"@type": "AutoDealer", "name": "Music City Honda"}
    },
    "url": "https://www.cars.com/vehicledetail/1HGCV1F34NA123456/"
  },
  {
    "@context": "https://schema.org",
    "@type": "Car",
    "vehicleIdentificationNumber": "5N1AZ2MS8NC123456",
    "brand": {"@type": "Brand", "name": "Nissan"},
    "model": {"@type": "ProductModel", "name": "Rogue"},
    "vehicleConfiguration": "SL",
    "vehicleModelDate": "2023",
    "mileageFromOdometer": "37,412 mi.",
    "bodyType": "SUV",
    "fuelType": "Gasoline",
    "offers": {
      "@type": "Offer",
      "price": "$18,995",
      "seller": {"@type": "AutoDealer", "name": "Riverside Nissan"}
    },
    "url": "https://www.cars.com/vehicledetail/5N1AZ2MS8NC123456/"
  },
  {
    "@context": "https://schema.org",
    "@type": "Product",
    "name": "2021 Kia Soul LX",
    "offers": {"@type": "Offer", "price": "16400"},
    "url": "https://www.cars.com/vehicledetail/no-vin-here/"
  }
]
</script>
</head><body>""" + PAGE_PADDING + """</body></html>
"""

DATA_ATTR_FIXTURE = """
<html><body>
<div class="vehicle-card" data-vin="3VW2B7AJ5FM123456" data-year="2020"
     data-make="Volkswagen" data-model="Jetta" data-trim="S" data-mileage="45,210"
     data-price="$15,990" data-dealer-name="Green Hills VW" data-dealer-city="Nashville"
     data-dealer-state="TN" data-cpo="true"
     data-listing-url="https://www.cars.com/vehicledetail/3VW2B7AJ5FM123456/">
</div>
<div class="vehicle-card" data-vin="JHMFC1F39JX123456" data-year="2018"
     data-make="Honda" data-model="Civic" data-trim="LX" data-mileage="61200"
     data-price="12300" data-dealer-name="Metro Honda" data-dealer-city="Franklin"
     data-dealer-state="TN" data-cpo="false"
     data-listing-url="https://www.cars.com/vehicledetail/JHMFC1F39JX123456/">
</div>
</body></html>
"""

PLAIN_CARD_FIXTURE = """
<html><body>
<div class="vehicle-card">
  <a class="vehicle-card-link" href="/vehicledetail/1FA6P8TH5J5123456/">
    <h2 class="title">2019 Ford Fusion SE</h2>
  </a>
  <span class="primary-price">$18,995</span>
  <div class="mileage">37,412 mi.</div>
  <div class="dealer-name">Best Motors</div>
  <div class="dealer-location">Austin, TX</div>
  <span class="vin">1FA6P8TH5J5123456</span>
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
  {"@type": "Vehicle", "vehicleIdentificationNumber": "VIN00000000000001", "name": "2021 Mazda 3",
   "offers": {"price": "17000"}},
  {"@type": "Vehicle", "vehicleIdentificationNumber": "VIN00000000000002", "name": "2021 Mazda CX-5",
   "offers": {"price": "18000"}},
  {"@type": "Vehicle", "vehicleIdentificationNumber": "VIN00000000000003", "name": "2022 Subaru Outback",
   "offers": {"price": "19000"}}
]
</script></head><body>""" + PAGE_PADDING + """</body></html>
"""

CAP_PAGE_2 = """
<html><head><script type="application/ld+json">
[
  {"@type": "Vehicle", "vehicleIdentificationNumber": "VIN00000000000004", "name": "2022 Subaru Forester",
   "offers": {"price": "19500"}},
  {"@type": "Vehicle", "vehicleIdentificationNumber": "VIN00000000000005", "name": "2021 Toyota RAV4",
   "offers": {"price": "20000"}},
  {"@type": "Vehicle", "vehicleIdentificationNumber": "VIN00000000000006", "name": "2021 Toyota Camry",
   "offers": {"price": "17500"}},
  {"@type": "Vehicle", "vehicleIdentificationNumber": "VIN00000000000007", "name": "2021 Honda CR-V",
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
        scraper = CarsComScraper(self.conn, limits=base.ScrapeLimits(max_pages_per_run=1))
        urls = scraper.search_urls(SEARCH)
        self.assertEqual(len(urls), 1)
        parsed = urlparse(urls[0])
        self.assertEqual(parsed.netloc, "www.cars.com")
        self.assertEqual(parsed.path, "/shopping/results/")
        query = parse_qs(parsed.query)
        self.assertEqual(query["stock_type"], ["used"])
        self.assertEqual(query["zip"], ["38464"])
        self.assertEqual(query["maximum_distance"], ["100"])
        self.assertEqual(query["list_price_max"], ["20000"])
        self.assertEqual(query["mileage_max"], ["60000"])
        self.assertEqual(query["year_min"], ["2021"])

    def test_paging_produces_distinct_urls_capped_at_max_pages(self):
        scraper = CarsComScraper(self.conn, limits=base.ScrapeLimits(max_pages_per_run=3))
        urls = scraper.search_urls(SEARCH)
        self.assertEqual(len(urls), 3)
        self.assertEqual(len(set(urls)), 3)  # distinct
        pages = [parse_qs(urlparse(u).query)["page"][0] for u in urls]
        self.assertEqual(pages, ["1", "2", "3"])

    def test_search_urls_respects_lower_max_pages(self):
        scraper = CarsComScraper(self.conn, limits=base.ScrapeLimits(max_pages_per_run=1))
        urls = scraper.search_urls(SEARCH)
        self.assertEqual(len(urls), 1)


class ParseTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.conn = make_conn(self._tmp.name)
        self.scraper = CarsComScraper(self.conn, limits=base.ScrapeLimits())

    def tearDown(self):
        self.conn.close()
        self._tmp.cleanup()

    def test_parses_json_ld_vehicles(self):
        listings = self.scraper.parse(JSON_LD_FIXTURE, "https://www.cars.com/shopping/results/?page=1")
        by_vin = {item.get("vin"): item for item in listings}

        self.assertIn("1HGCV1F34NA123456", by_vin)
        first = by_vin["1HGCV1F34NA123456"]
        self.assertEqual(first["year"], 2022)
        self.assertEqual(first["make"], "Honda")
        self.assertEqual(first["model"], "Accord")
        self.assertEqual(first["trim"], "EX-L")
        self.assertEqual(first["price_current"], 21995)
        self.assertEqual(first["mileage"], 28450)
        self.assertEqual(first["dealer_name"], "Music City Honda")

        self.assertIn("5N1AZ2MS8NC123456", by_vin)
        second = by_vin["5N1AZ2MS8NC123456"]
        self.assertEqual(second["year"], 2023)
        self.assertEqual(second["make"], "Nissan")
        self.assertEqual(second["model"], "Rogue")
        self.assertEqual(second["trim"], "SL")
        self.assertEqual(second["price_current"], 18995)   # "$18,995" -> 18995
        self.assertEqual(second["mileage"], 37412)          # "37,412 mi." -> 37412
        self.assertEqual(second["body_type"], "SUV")
        self.assertEqual(second["fuel_type"], "Gasoline")
        self.assertEqual(second["dealer_name"], "Riverside Nissan")

        # The third vehicle has no VIN anywhere -- parse() may still return it (it just
        # won't have a usable 'vin'); ScraperBase.run() is what drops it. Confirm no VIN
        # was invented for it.
        no_vin_listings = [item for item in listings if not item.get("vin")]
        self.assertEqual(len(no_vin_listings), 1)
        self.assertEqual(no_vin_listings[0].get("price_current"), 16400)

    def test_parses_data_attribute_cards(self):
        listings = self.scraper.parse(DATA_ATTR_FIXTURE, "https://www.cars.com/shopping/results/?page=1")
        by_vin = {item.get("vin"): item for item in listings}
        self.assertEqual(len(listings), 2)

        vw = by_vin["3VW2B7AJ5FM123456"]
        self.assertEqual(vw["year"], 2020)
        self.assertEqual(vw["make"], "Volkswagen")
        self.assertEqual(vw["model"], "Jetta")
        self.assertEqual(vw["trim"], "S")
        self.assertEqual(vw["mileage"], 45210)          # "45,210" -> 45210
        self.assertEqual(vw["price_current"], 15990)     # "$15,990" -> 15990
        self.assertEqual(vw["dealer_name"], "Green Hills VW")
        self.assertEqual(vw["dealer_city"], "Nashville")
        self.assertEqual(vw["dealer_state"], "TN")
        self.assertTrue(vw["cpo"])

        civic = by_vin["JHMFC1F39JX123456"]
        self.assertEqual(civic["price_current"], 12300)
        self.assertFalse(civic["cpo"])

    def test_parses_plain_html_cards(self):
        listings = self.scraper.parse(PLAIN_CARD_FIXTURE, "https://www.cars.com/shopping/results/?page=1")
        self.assertEqual(len(listings), 1)
        listing = listings[0]
        self.assertEqual(listing["vin"], "1FA6P8TH5J5123456")
        self.assertEqual(listing["year"], 2019)
        self.assertEqual(listing["make"], "Ford")
        self.assertEqual(listing["model"], "Fusion")
        self.assertEqual(listing["trim"], "SE")
        self.assertEqual(listing["price_current"], 18995)   # "$18,995" -> 18995
        self.assertEqual(listing["mileage"], 37412)          # "37,412 mi." -> 37412
        self.assertEqual(listing["dealer_name"], "Best Motors")
        self.assertEqual(listing["dealer_city"], "Austin")
        self.assertEqual(listing["dealer_state"], "TX")

    def test_empty_or_garbage_page_returns_empty_list(self):
        self.assertEqual(self.scraper.parse(EMPTY_FIXTURE, "https://www.cars.com/shopping/results/"), [])
        self.assertEqual(self.scraper.parse("", "https://www.cars.com/shopping/results/"), [])
        self.assertEqual(
            self.scraper.parse("not even html {{{ ]] garbage", "https://www.cars.com/shopping/results/"),
            [],
        )

    def test_vinless_listing_is_dropped_by_run(self):
        opener = CountingOpener((200, JSON_LD_FIXTURE))
        limits = base.ScrapeLimits(max_pages_per_run=1, min_seconds_between_requests=0)
        fetcher = base.Fetcher(self.conn, self.scraper.key, limits, robots=FakeRobots(), opener=opener)
        scraper = CarsComScraper(self.conn, limits=limits, fetcher=fetcher)

        result = scraper.run(SEARCH)

        self.assertEqual(result.status, "ok")
        vins = [item["vin"] for item in result.listings]
        self.assertNotIn("", vins)
        self.assertTrue(all(vin for vin in vins))
        # The two VIN-bearing vehicles made it through; the VIN-less one did not.
        self.assertEqual(len(result.listings), 2)


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
        fetcher = base.Fetcher(self.conn, "cars_com", limits, robots=FakeRobots(), opener=opener)
        scraper = CarsComScraper(self.conn, limits=limits, fetcher=fetcher)

        result = scraper.run(SEARCH)

        self.assertLessEqual(result.pages_fetched, 2)
        self.assertLessEqual(len(opener.calls), 2)
        self.assertLessEqual(len(result.listings), 5)
        self.assertEqual(len(result.listings), 5)  # exactly the cap, even though 7 were on offer

        usage = db.scrape_usage_today(self.conn, source="cars_com")
        self.assertEqual(usage["listings"], 5)
        self.assertEqual(usage["requests"], len(opener.calls))

    def test_fails_closed_when_robots_cannot_be_read(self):
        limits = base.ScrapeLimits(max_pages_per_run=2, min_seconds_between_requests=0)
        opener = CountingOpener((200, JSON_LD_FIXTURE))
        fetcher = base.Fetcher(self.conn, "cars_com", limits, robots=DisallowingRobots(), opener=opener)
        scraper = CarsComScraper(self.conn, limits=limits, fetcher=fetcher)

        result = scraper.run(SEARCH)

        self.assertEqual(result.status, "disallowed")
        self.assertEqual(len(opener.calls), 0)
        self.assertEqual(result.listings, [])

    def test_challenge_response_is_blocked_without_retry(self):
        limits = base.ScrapeLimits(max_pages_per_run=2, min_seconds_between_requests=0)
        opener = CountingOpener((200, CHALLENGE_BODY))
        fetcher = base.Fetcher(self.conn, "cars_com", limits, robots=FakeRobots(), opener=opener)
        scraper = CarsComScraper(self.conn, limits=limits, fetcher=fetcher)

        result = scraper.run(SEARCH)

        self.assertEqual(result.status, "blocked")
        self.assertEqual(len(opener.calls), 1)  # no retry
        self.assertEqual(result.listings, [])


if __name__ == "__main__":
    unittest.main()
