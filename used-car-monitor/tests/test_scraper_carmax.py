"""Tests for the CarMax scraper adapter.

No network access: every fetch in here goes through a synthetic, injectable `opener`
callable (see `carmon.scrapers.base.Fetcher`), and every page body is a small fixture
written by hand below -- never real page source pulled from the live site. As noted in
`carmon/scrapers/carmax.py`, the parser has never been exercised against real CarMax HTML
because robots.txt itself is unreachable (HTTP 403, Akamai) from this environment; these
tests only prove the adapter behaves correctly against the schema.org / embedded-JSON /
markup shapes it was written to expect, and that the shared budget/robots/challenge
machinery in `base.py` is wired up correctly.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from carmon import db
from carmon.scrapers import base
from carmon.scrapers.carmax import CarMaxScraper

# base.looks_like_challenge() treats a short page carrying a challenge-platform fingerprint
# as a bot wall (see carmon/scrapers/base.py). Real CarMax search-results pages are far
# larger than that; this filler stands in for the rest of a real page's markup so the
# fixtures below aren't mistaken for a challenge on size alone.
PAGE_PADDING = "<!-- " + ("filler " * 400) + " -->"

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
    "name": "2022 Honda Accord EX-L",
    "vehicleIdentificationNumber": "1HGCV1F34NA123456",
    "mileageFromOdometer": "28450",
    "offers": {
      "@type": "Offer",
      "price": "21995",
      "priceCurrency": "USD",
      "seller": {"@type": "AutoDealer", "name": "Nashville"}
    },
    "url": "https://www.carmax.com/car/1HGCV1F34NA123456"
  },
  {
    "@context": "https://schema.org",
    "@type": "Car",
    "vehicleIdentificationNumber": "5N1AZ2MS8NC123456",
    "brand": {"@type": "Brand", "name": "Nissan"},
    "model": {"@type": "ProductModel", "name": "Rogue"},
    "vehicleConfiguration": "SL",
    "vehicleModelDate": "2023",
    "mileageFromOdometer": "37,412 miles",
    "bodyType": "SUV",
    "fuelType": "Gasoline",
    "offers": {
      "@type": "Offer",
      "price": "$18,995",
      "seller": {"@type": "AutoDealer", "name": "CarMax Franklin"}
    },
    "url": "https://www.carmax.com/car/5N1AZ2MS8NC123456"
  },
  {
    "@context": "https://schema.org",
    "@type": "Product",
    "name": "2021 Kia Soul LX",
    "offers": {"@type": "Offer", "price": "16400"},
    "url": "https://www.carmax.com/car/no-vin-here"
  }
]
</script>
</head><body>""" + PAGE_PADDING + """</body></html>
"""

EMBEDDED_JSON_FIXTURE = """
<html><head></head><body>
<script id="__CARMAX_STATE__" type="application/json">
{
  "search": {
    "results": [
      {
        "vin": "3VW2B7AJ5FM123456",
        "stockNumber": "24681012",
        "year": 2020,
        "make": "Volkswagen",
        "model": "Jetta",
        "trim": "S",
        "mileage": "45,210",
        "price": "$15,990",
        "store": "Cool Springs",
        "certification": "Manufacturer Certified",
        "url": "https://www.carmax.com/car/3VW2B7AJ5FM123456"
      },
      {
        "vin": "JHMFC1F39JX123456",
        "stockNumber": "13579246",
        "year": 2018,
        "make": "Honda",
        "model": "Civic",
        "trim": "LX",
        "mileage": 61200,
        "price": 12300,
        "store": "Antioch",
        "url": "https://www.carmax.com/car/JHMFC1F39JX123456"
      }
    ]
  }
}
</script>
""" + PAGE_PADDING + """
</body></html>
"""

PLAIN_CARD_FIXTURE = """
<html><body>
<div class="car-tile">
  <a class="car-tile-title" href="/car/1FA6P8TH5J5123456">
    2019 Ford Fusion SE
  </a>
  <span class="car-tile-price">$18,995</span>
  <div class="car-tile-mileage">37,412 miles</div>
  <div class="car-tile-store">Nashville</div>
  <span class="stock-number">98765432</span>
  <span class="vin">1FA6P8TH5J5123456</span>
</div>
</body></html>
"""

RETAILER_CERTIFIED_FIXTURE = """
<html><head>
<script type="application/ld+json">
[
  {
    "@context": "https://schema.org",
    "@type": "Vehicle",
    "name": "2021 Toyota Camry SE",
    "vehicleIdentificationNumber": "4T1G11AK5NU123456",
    "mileageFromOdometer": "29800",
    "certification": "CarMax Quality Certified",
    "offers": {
      "@type": "Offer",
      "price": "19995",
      "seller": {"@type": "AutoDealer", "name": "CarMax Cool Springs"}
    },
    "url": "https://www.carmax.com/car/4T1G11AK5NU123456"
  }
]
</script>
</head><body>""" + PAGE_PADDING + """</body></html>
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
        raise base.RobotsDisallowed("www.carmax.com: robots.txt could not be read (simulated)")

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
        scraper = CarMaxScraper(self.conn, limits=base.ScrapeLimits(max_pages_per_run=1))
        urls = scraper.search_urls(SEARCH)
        self.assertEqual(len(urls), 1)
        parsed = urlparse(urls[0])
        self.assertEqual(parsed.netloc, "www.carmax.com")
        self.assertEqual(parsed.path, "/cars")
        query = parse_qs(parsed.query)
        self.assertEqual(query["zip"], ["38464"])
        self.assertEqual(query["distance"], ["100"])
        self.assertEqual(query["price"], ["0-20000"])
        self.assertEqual(query["mileage"], ["0-60000"])
        self.assertTrue(query["year"][0].startswith("2021-"))

    def test_paging_produces_distinct_urls_capped_at_max_pages(self):
        scraper = CarMaxScraper(self.conn, limits=base.ScrapeLimits(max_pages_per_run=3))
        urls = scraper.search_urls(SEARCH)
        self.assertEqual(len(urls), 3)
        self.assertEqual(len(set(urls)), 3)  # distinct
        pages = [parse_qs(urlparse(u).query)["page"][0] for u in urls]
        self.assertEqual(pages, ["1", "2", "3"])

    def test_search_urls_respects_lower_max_pages(self):
        scraper = CarMaxScraper(self.conn, limits=base.ScrapeLimits(max_pages_per_run=1))
        urls = scraper.search_urls(SEARCH)
        self.assertEqual(len(urls), 1)


class ParseTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.conn = make_conn(self._tmp.name)
        self.scraper = CarMaxScraper(self.conn, limits=base.ScrapeLimits())

    def tearDown(self):
        self.conn.close()
        self._tmp.cleanup()

    def test_parses_json_ld_vehicles(self):
        listings = self.scraper.parse(JSON_LD_FIXTURE, "https://www.carmax.com/cars?page=1")
        by_vin = {item.get("vin"): item for item in listings}

        self.assertIn("1HGCV1F34NA123456", by_vin)
        first = by_vin["1HGCV1F34NA123456"]
        self.assertEqual(first["year"], 2022)
        self.assertEqual(first["make"], "Honda")
        self.assertEqual(first["model"], "Accord")
        self.assertEqual(first["trim"], "EX-L")
        self.assertEqual(first["price_current"], 21995)
        self.assertEqual(first["mileage"], 28450)
        self.assertEqual(first["dealer_name"], "CarMax Nashville")

        self.assertIn("5N1AZ2MS8NC123456", by_vin)
        second = by_vin["5N1AZ2MS8NC123456"]
        self.assertEqual(second["year"], 2023)
        self.assertEqual(second["make"], "Nissan")
        self.assertEqual(second["model"], "Rogue")
        self.assertEqual(second["trim"], "SL")
        self.assertEqual(second["price_current"], 18995)   # "$18,995" -> 18995
        self.assertEqual(second["mileage"], 37412)          # "37,412 miles" -> 37412
        self.assertEqual(second["body_type"], "SUV")
        self.assertEqual(second["fuel_type"], "Gasoline")
        self.assertEqual(second["dealer_name"], "CarMax Franklin")  # already prefixed

        # The third vehicle has no VIN anywhere -- parse() may still return it (it just
        # won't have a usable 'vin'); ScraperBase.run() is what drops it.
        no_vin_listings = [item for item in listings if not item.get("vin")]
        self.assertEqual(len(no_vin_listings), 1)
        self.assertEqual(no_vin_listings[0].get("price_current"), 16400)

    def test_parses_embedded_json_payload(self):
        listings = self.scraper.parse(EMBEDDED_JSON_FIXTURE, "https://www.carmax.com/cars?page=1")
        by_vin = {item.get("vin"): item for item in listings}
        self.assertEqual(len(listings), 2)

        vw = by_vin["3VW2B7AJ5FM123456"]
        self.assertEqual(vw["year"], 2020)
        self.assertEqual(vw["make"], "Volkswagen")
        self.assertEqual(vw["model"], "Jetta")
        self.assertEqual(vw["trim"], "S")
        self.assertEqual(vw["mileage"], 45210)          # "45,210" -> 45210
        self.assertEqual(vw["price_current"], 15990)     # "$15,990" -> 15990
        self.assertEqual(vw["dealer_name"], "CarMax Cool Springs")
        self.assertEqual(vw["stock_number"], "24681012")
        self.assertTrue(vw["cpo"])  # "Manufacturer Certified"
        self.assertFalse(vw.get("retailer_certified", False))

        civic = by_vin["JHMFC1F39JX123456"]
        self.assertEqual(civic["price_current"], 12300)
        self.assertEqual(civic["stock_number"], "13579246")
        self.assertFalse(civic["cpo"])

    def test_parses_plain_html_cards(self):
        listings = self.scraper.parse(PLAIN_CARD_FIXTURE, "https://www.carmax.com/cars?page=1")
        self.assertEqual(len(listings), 1)
        listing = listings[0]
        self.assertEqual(listing["vin"], "1FA6P8TH5J5123456")
        self.assertEqual(listing["year"], 2019)
        self.assertEqual(listing["make"], "Ford")
        self.assertEqual(listing["model"], "Fusion")
        self.assertEqual(listing["trim"], "SE")
        self.assertEqual(listing["price_current"], 18995)   # "$18,995" -> 18995
        self.assertEqual(listing["mileage"], 37412)          # "37,412 miles" -> 37412
        self.assertEqual(listing["dealer_name"], "CarMax Nashville")
        self.assertEqual(listing["stock_number"], "98765432")

    def test_carmax_quality_certified_is_retailer_certified_not_cpo(self):
        listings = self.scraper.parse(
            RETAILER_CERTIFIED_FIXTURE, "https://www.carmax.com/cars?page=1"
        )
        self.assertEqual(len(listings), 1)
        listing = listings[0]
        self.assertEqual(listing["vin"], "4T1G11AK5NU123456")
        self.assertFalse(listing["cpo"])
        self.assertTrue(listing["retailer_certified"])

    def test_price_string_coercion(self):
        from carmon.scrapers.carmax import _to_int
        self.assertEqual(_to_int("$18,995"), 18995)
        self.assertEqual(_to_int("37K mi"), 37000)
        self.assertEqual(_to_int("37,412 miles"), 37412)
        self.assertIsNone(_to_int("call for price"))
        self.assertIsNone(_to_int(None))

    def test_empty_or_garbage_page_returns_empty_list(self):
        self.assertEqual(self.scraper.parse(EMPTY_FIXTURE, "https://www.carmax.com/cars"), [])
        self.assertEqual(self.scraper.parse("", "https://www.carmax.com/cars"), [])
        self.assertEqual(
            self.scraper.parse("not even html {{{ ]] garbage", "https://www.carmax.com/cars"),
            [],
        )

    def test_vinless_listing_is_dropped_by_run(self):
        opener = CountingOpener((200, JSON_LD_FIXTURE))
        limits = base.ScrapeLimits(max_pages_per_run=1, min_seconds_between_requests=0)
        fetcher = base.Fetcher(self.conn, self.scraper.key, limits, robots=FakeRobots(), opener=opener)
        scraper = CarMaxScraper(self.conn, limits=limits, fetcher=fetcher)

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
        fetcher = base.Fetcher(self.conn, "carmax", limits, robots=FakeRobots(), opener=opener)
        scraper = CarMaxScraper(self.conn, limits=limits, fetcher=fetcher)

        result = scraper.run(SEARCH)

        self.assertLessEqual(result.pages_fetched, 2)
        self.assertLessEqual(len(opener.calls), 2)
        self.assertLessEqual(len(result.listings), 5)
        self.assertEqual(len(result.listings), 5)  # exactly the cap, even though 7 were on offer

        usage = db.scrape_usage_today(self.conn, source="carmax")
        self.assertEqual(usage["listings"], 5)
        self.assertEqual(usage["requests"], len(opener.calls))

    def test_fails_closed_when_robots_cannot_be_read(self):
        limits = base.ScrapeLimits(max_pages_per_run=2, min_seconds_between_requests=0)
        opener = CountingOpener((200, JSON_LD_FIXTURE))
        fetcher = base.Fetcher(self.conn, "carmax", limits, robots=DisallowingRobots(), opener=opener)
        scraper = CarMaxScraper(self.conn, limits=limits, fetcher=fetcher)

        result = scraper.run(SEARCH)

        self.assertEqual(result.status, "disallowed")
        self.assertEqual(len(opener.calls), 0)
        self.assertEqual(result.listings, [])

    def test_challenge_response_is_blocked_without_retry(self):
        limits = base.ScrapeLimits(max_pages_per_run=2, min_seconds_between_requests=0)
        opener = CountingOpener((200, CHALLENGE_BODY))
        fetcher = base.Fetcher(self.conn, "carmax", limits, robots=FakeRobots(), opener=opener)
        scraper = CarMaxScraper(self.conn, limits=limits, fetcher=fetcher)

        result = scraper.run(SEARCH)

        self.assertEqual(result.status, "blocked")
        self.assertEqual(len(opener.calls), 1)  # no retry
        self.assertEqual(result.listings, [])


if __name__ == "__main__":
    unittest.main()
