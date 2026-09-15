"""Tests for the CarGurus scraper adapter.

No network access: every fetch in here goes through a synthetic, injectable `opener`
callable (see `carmon.scrapers.base.Fetcher`), and every page body is a small fixture
written by hand below -- never real page source pulled from the live site. As noted in
`carmon/scrapers/cargurus.py`, the parser has never been exercised against real CarGurus
HTML because `https://www.cargurus.com/robots.txt` itself returns HTTP 406 from this
environment (and `looks_like_challenge()` treats any 406 as a bot wall, so `RobotsCache`
fails closed before a single search page is requested). These tests only prove the adapter
behaves correctly against the structured-data / markup shapes it was written to expect, and
that the shared budget/robots/challenge machinery in `base.py` is wired up correctly.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from carmon import db
from carmon.scrapers import base
from carmon.scrapers.cargurus import CarGurusScraper

# base.looks_like_challenge() treats a short script-only shell containing a challenge
# fingerprint as a wall. Real CarGurus search-results pages are far larger than our small
# fixtures; this filler stands in for the rest of a real page's markup so the JSON-LD /
# embedded-JSON fixtures below aren't mistaken for a challenge purely on size.
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
    "name": "2022 Toyota Camry SE",
    "vehicleIdentificationNumber": "4T1G11AK1NU123456",
    "mileageFromOdometer": "22,150",
    "bodyType": "Sedan",
    "fuelType": "Gasoline",
    "offers": {
      "@type": "Offer",
      "price": "23995",
      "seller": {"@type": "AutoDealer", "name": "Capital Toyota"}
    },
    "dealRating": "Great Deal",
    "priceDifference": "-1450",
    "url": "https://www.cargurus.com/Cars/inventorylisting/vdp.action?listingId=1001"
  },
  {
    "@context": "https://schema.org",
    "@type": "Car",
    "vehicleIdentificationNumber": "1C4RJFBG5MC123456",
    "brand": {"@type": "Brand", "name": "Jeep"},
    "model": {"@type": "ProductModel", "name": "Grand Cherokee"},
    "vehicleConfiguration": "Limited",
    "vehicleModelDate": "2021",
    "mileageFromOdometer": "37,412 mi.",
    "offers": {
      "@type": "Offer",
      "price": "$18,995",
      "seller": {"@type": "AutoDealer", "name": "Riverbend Chrysler"}
    },
    "dealRating": "Fair Price",
    "url": "https://www.cargurus.com/Cars/inventorylisting/vdp.action?listingId=1002"
  },
  {
    "@context": "https://schema.org",
    "@type": "Product",
    "name": "2020 Kia Soul LX",
    "offers": {"@type": "Offer", "price": "15400"},
    "url": "https://www.cargurus.com/Cars/inventorylisting/vdp.action?listingId=1003"
  }
]
</script>
</head><body>""" + PAGE_PADDING + """</body></html>
"""

EMBEDDED_JSON_FIXTURE = """
<html><head></head><body>
<div id="app"></div>
<script>
window.__INITIAL_STATE__ = {"searchResults": {"listings": [
  {"vin": "5UXCR6C0XL9123456", "year": 2020, "make": "BMW", "model": "X5", "trim": "xDrive40i",
   "mileage": "41,020", "price": "$32,500", "dealerName": "Premier BMW", "dealerCity": "Denver",
   "dealerState": "CO", "dealRating": "GOOD_DEAL", "dealDelta": "-820",
   "listingUrl": "https://www.cargurus.com/Cars/inventorylisting/vdp.action?listingId=2001"},
  {"vin": "2T3P1RFV8LC123456", "year": 2021, "make": "Toyota", "model": "RAV4", "trim": "XLE",
   "mileage": "29,880", "price": "19,700", "dealerName": "Foothills Toyota", "dealerCity": "Boulder",
   "dealerState": "CO", "dealRating": "HIGH_PRICE",
   "listingUrl": "https://www.cargurus.com/Cars/inventorylisting/vdp.action?listingId=2002"}
]}};
</script>
</body></html>
""" + PAGE_PADDING

HTML_CARD_FIXTURE = """
<html><body>
<div class="listing-tile" data-vin="5FNYF6H07KB123456">
  <a href="https://www.cargurus.com/Cars/inventorylisting/vdp.action?listingId=3001">
    <h3 class="title">2019 Honda Pilot EX-L</h3>
  </a>
  <span class="price">$21,995</span>
  <div class="mileage">52,300 mi.</div>
  <div class="dealer-name">Sunrise Honda</div>
  <div class="dealer-location">Franklin, TN</div>
  <span class="deal-rating">Good Deal</span>
  <div class="price-analysis">$620 below market average</div>
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
        scraper = CarGurusScraper(self.conn, limits=base.ScrapeLimits(max_pages_per_run=1))
        urls = scraper.search_urls(SEARCH)
        self.assertEqual(len(urls), 1)
        parsed = urlparse(urls[0])
        self.assertEqual(parsed.netloc, "www.cargurus.com")
        self.assertEqual(
            parsed.path, "/Cars/inventorylisting/viewDetailsFilterViewInventoryListing.action"
        )
        query = parse_qs(parsed.query)
        self.assertEqual(query["zip"], ["38464"])
        self.assertEqual(query["distance"], ["100"])
        self.assertEqual(query["maxPrice"], ["20000"])
        self.assertEqual(query["maxMileage"], ["60000"])
        self.assertEqual(query["startYear"], ["2021"])
        self.assertEqual(query["inventorySearchWidgetType"], ["AUTO"])
        self.assertEqual(query["sourceContext"], ["carGurusHomePageModel"])
        self.assertEqual(query["offset"], ["0"])

    def test_paging_produces_distinct_urls_capped_at_max_pages(self):
        scraper = CarGurusScraper(self.conn, limits=base.ScrapeLimits(max_pages_per_run=3))
        urls = scraper.search_urls(SEARCH)
        self.assertEqual(len(urls), 3)
        self.assertEqual(len(set(urls)), 3)  # distinct
        offsets = [parse_qs(urlparse(u).query)["offset"][0] for u in urls]
        self.assertEqual(offsets, ["0", "15", "30"])

    def test_search_urls_respects_lower_max_pages(self):
        scraper = CarGurusScraper(self.conn, limits=base.ScrapeLimits(max_pages_per_run=1))
        urls = scraper.search_urls(SEARCH)
        self.assertEqual(len(urls), 1)

    def test_no_zip_yields_no_urls(self):
        scraper = CarGurusScraper(self.conn, limits=base.ScrapeLimits(max_pages_per_run=2))
        self.assertEqual(scraper.search_urls({}), [])


class ParseTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.conn = make_conn(self._tmp.name)
        self.scraper = CarGurusScraper(self.conn, limits=base.ScrapeLimits())

    def tearDown(self):
        self.conn.close()
        self._tmp.cleanup()

    def test_parses_json_ld_vehicles_including_deal_rating(self):
        listings = self.scraper.parse(
            JSON_LD_FIXTURE, "https://www.cargurus.com/Cars/inventorylisting/..."
        )
        by_vin = {item.get("vin"): item for item in listings}

        self.assertIn("4T1G11AK1NU123456", by_vin)
        camry = by_vin["4T1G11AK1NU123456"]
        self.assertEqual(camry["year"], 2022)
        self.assertEqual(camry["make"], "Toyota")
        self.assertEqual(camry["model"], "Camry")
        self.assertEqual(camry["trim"], "SE")
        self.assertEqual(camry["price_current"], 23995)
        self.assertEqual(camry["mileage"], 22150)
        self.assertEqual(camry["dealer_name"], "Capital Toyota")
        self.assertEqual(camry["deal_rating"], "Great")
        self.assertEqual(camry["deal_delta"], -1450)

        self.assertIn("1C4RJFBG5MC123456", by_vin)
        jeep = by_vin["1C4RJFBG5MC123456"]
        self.assertEqual(jeep["year"], 2021)
        self.assertEqual(jeep["make"], "Jeep")
        self.assertEqual(jeep["model"], "Grand Cherokee")
        self.assertEqual(jeep["trim"], "Limited")
        self.assertEqual(jeep["price_current"], 18995)   # "$18,995" -> 18995
        self.assertEqual(jeep["mileage"], 37412)          # "37,412 mi." -> 37412
        self.assertEqual(jeep["dealer_name"], "Riverbend Chrysler")
        self.assertEqual(jeep["deal_rating"], "Fair")

        # The third vehicle has no VIN anywhere -- parse() may still return it; it is
        # ScraperBase.run() that drops it. Confirm no VIN was invented for it.
        no_vin_listings = [item for item in listings if not item.get("vin")]
        self.assertEqual(len(no_vin_listings), 1)
        self.assertEqual(no_vin_listings[0].get("price_current"), 15400)

    def test_parses_embedded_json_hydration_blob_including_deal_rating(self):
        listings = self.scraper.parse(
            EMBEDDED_JSON_FIXTURE, "https://www.cargurus.com/Cars/inventorylisting/..."
        )
        by_vin = {item.get("vin"): item for item in listings}
        self.assertEqual(len(listings), 2)

        bmw = by_vin["5UXCR6C0XL9123456"]
        self.assertEqual(bmw["year"], 2020)
        self.assertEqual(bmw["make"], "BMW")
        self.assertEqual(bmw["model"], "X5")
        self.assertEqual(bmw["trim"], "xDrive40i")
        self.assertEqual(bmw["mileage"], 41020)          # "41,020" -> 41020
        self.assertEqual(bmw["price_current"], 32500)     # "$32,500" -> 32500
        self.assertEqual(bmw["dealer_name"], "Premier BMW")
        self.assertEqual(bmw["dealer_city"], "Denver")
        self.assertEqual(bmw["dealer_state"], "CO")
        self.assertEqual(bmw["deal_rating"], "Good")
        self.assertEqual(bmw["deal_delta"], -820)

        rav4 = by_vin["2T3P1RFV8LC123456"]
        self.assertEqual(rav4["price_current"], 19700)    # "19,700" -> 19700
        self.assertEqual(rav4["deal_rating"], "High")
        self.assertNotIn("deal_delta", rav4)               # no delta was present for this one

    def test_parses_plain_html_cards_including_deal_rating(self):
        listings = self.scraper.parse(
            HTML_CARD_FIXTURE, "https://www.cargurus.com/Cars/inventorylisting/..."
        )
        self.assertEqual(len(listings), 1)
        listing = listings[0]
        self.assertEqual(listing["vin"], "5FNYF6H07KB123456")
        self.assertEqual(listing["year"], 2019)
        self.assertEqual(listing["make"], "Honda")
        self.assertEqual(listing["model"], "Pilot")
        self.assertEqual(listing["trim"], "EX-L")
        self.assertEqual(listing["price_current"], 21995)   # "$21,995" -> 21995
        self.assertEqual(listing["mileage"], 52300)          # "52,300 mi." -> 52300
        self.assertEqual(listing["dealer_name"], "Sunrise Honda")
        self.assertEqual(listing["dealer_city"], "Franklin")
        self.assertEqual(listing["dealer_state"], "TN")
        self.assertEqual(listing["deal_rating"], "Good")
        self.assertEqual(listing["deal_delta"], -620)

    def test_empty_or_garbage_page_returns_empty_list(self):
        self.assertEqual(
            self.scraper.parse(EMPTY_FIXTURE, "https://www.cargurus.com/Cars/inventorylisting/"),
            [],
        )
        self.assertEqual(self.scraper.parse("", "https://www.cargurus.com/Cars/inventorylisting/"), [])
        self.assertEqual(
            self.scraper.parse(
                "not even html {{{ ]] garbage", "https://www.cargurus.com/Cars/inventorylisting/"
            ),
            [],
        )

    def test_vinless_listing_is_dropped_by_run(self):
        opener = CountingOpener((200, JSON_LD_FIXTURE))
        limits = base.ScrapeLimits(max_pages_per_run=1, min_seconds_between_requests=0)
        fetcher = base.Fetcher(self.conn, self.scraper.key, limits, robots=FakeRobots(), opener=opener)
        scraper = CarGurusScraper(self.conn, limits=limits, fetcher=fetcher)

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
            offset = query.get("offset", ["0"])[0]
            return (200, CAP_PAGE_1 if offset == "0" else CAP_PAGE_2)

        opener = CountingOpener(respond)
        fetcher = base.Fetcher(self.conn, "cargurus", limits, robots=FakeRobots(), opener=opener)
        scraper = CarGurusScraper(self.conn, limits=limits, fetcher=fetcher)

        result = scraper.run(SEARCH)

        self.assertLessEqual(result.pages_fetched, 2)
        self.assertLessEqual(len(opener.calls), 2)
        self.assertLessEqual(len(result.listings), 5)
        self.assertEqual(len(result.listings), 5)  # exactly the cap, even though 7 were on offer

        usage = db.scrape_usage_today(self.conn, source="cargurus")
        self.assertEqual(usage["listings"], 5)
        self.assertEqual(usage["requests"], len(opener.calls))

    def test_fails_closed_when_robots_cannot_be_read(self):
        limits = base.ScrapeLimits(max_pages_per_run=2, min_seconds_between_requests=0)
        opener = CountingOpener((200, JSON_LD_FIXTURE))
        fetcher = base.Fetcher(self.conn, "cargurus", limits, robots=DisallowingRobots(), opener=opener)
        scraper = CarGurusScraper(self.conn, limits=limits, fetcher=fetcher)

        result = scraper.run(SEARCH)

        self.assertEqual(result.status, "disallowed")
        self.assertEqual(len(opener.calls), 0)
        self.assertEqual(result.listings, [])

    def test_challenge_response_is_blocked_without_retry(self):
        limits = base.ScrapeLimits(max_pages_per_run=2, min_seconds_between_requests=0)
        opener = CountingOpener((200, CHALLENGE_BODY))
        fetcher = base.Fetcher(self.conn, "cargurus", limits, robots=FakeRobots(), opener=opener)
        scraper = CarGurusScraper(self.conn, limits=limits, fetcher=fetcher)

        result = scraper.run(SEARCH)

        self.assertEqual(result.status, "blocked")
        self.assertEqual(len(opener.calls), 1)  # no retry
        self.assertEqual(result.listings, [])


if __name__ == "__main__":
    unittest.main()
