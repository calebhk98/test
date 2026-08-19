"""Tests for the Autotrader scraper adapter.

Everything here runs against synthetic, hand-written fixture HTML/JSON via an injected
`opener` callable — no network access, and no real Autotrader page source is stored in
this repo. See `carmon/scrapers/autotrader.py` for why: from the machine this was written
on, real search requests are answered with a bot-challenge shell, so the parser could not
be validated against live HTML and is instead tested against markup shaped like what
schema.org / Next.js-style state / card-based listing pages are documented to look like.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from urllib.parse import parse_qs, urlparse

from carmon import db
from carmon.scrapers import autotrader
from carmon.scrapers.base import REGISTRY, Fetcher, ScrapeLimits


class _PermissiveRobots:
    """A robots.txt stand-in that allows everything and sets no crawl-delay."""

    def check(self, url: str) -> None:
        return None

    def crawl_delay(self, url: str) -> None:
        return None


def _pad_page(html: str) -> str:
    """Pad a fixture past base.looks_like_challenge()'s 'tiny + script-heavy' heuristic.

    That heuristic (correctly) treats a short, script-heavy 200 response as a bot-challenge
    shell rather than a real page. Our synthetic fixtures are deliberately tiny, so anything
    routed through Fetcher.get() (i.e. through ScraperBase.run()) needs padding to read as a
    real page instead of a challenge. Fixtures parsed directly via scraper.parse() skip
    Fetcher entirely and don't need this.
    """
    filler = "<!-- fixture padding, not real content " + ("x" * 3000) + " -->"
    return html + filler


def _make_search() -> dict:
    return {
        "zip": "38464",
        "radius_miles": 100,
        "year_min": 2021,
        "price_max": 20000,
        "mileage_max": 60000,
    }


# --- fixtures ----------------------------------------------------------------------

JSON_LD_FIXTURE = """
<html><head>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Vehicle",
      "vehicleIdentificationNumber": "1HGCV1F34LA000001",
      "name": "2022 Honda Accord Sport",
      "brand": {"@type": "Brand", "name": "Honda"},
      "model": "Accord",
      "vehicleModelDate": "2022",
      "bodyType": "Sedan",
      "fuelType": "Gasoline",
      "mileageFromOdometer": {"@type": "QuantitativeValue", "value": "37,412 miles"},
      "offers": {
        "@type": "Offer",
        "price": "$18,995",
        "priceCurrency": "USD",
        "url": "https://www.autotrader.com/cars-for-sale/vehicledetails/1HGCV1F34LA000001",
        "seller": {
          "@type": "AutoDealer",
          "name": "Acme Motors",
          "address": {"addressLocality": "Springfield", "addressRegion": "TN"}
        }
      }
    },
    {
      "@type": "Car",
      "vehicleIdentificationNumber": "5YJ3E1EA7KF000002",
      "name": "Certified 2021 Toyota Camry LE",
      "brand": "Toyota",
      "model": {"name": "Camry"},
      "vehicleModelDate": 2021,
      "mileageFromOdometer": 22150,
      "offers": {"price": 19995, "seller": {"name": "Metro Toyota"}}
    },
    {
      "@type": "Product",
      "name": "2023 Kia Forte LXS",
      "sku": "1FA6P8TH0J5000003",
      "offers": {"price": 17500}
    }
  ]
}
</script>
</head><body></body></html>
"""

# A JSON-LD fixture with one listing missing a VIN entirely, to exercise the base
# class's own VIN-based drop in ScraperBase.run() (not adapter-side filtering).
DROP_NO_VIN_FIXTURE = """
<html><head>
<script type="application/ld+json">
{"@context": "https://schema.org", "@graph": [
  {"@type": "Vehicle", "vehicleIdentificationNumber": "1FTEW1EP0JK000030",
   "name": "2019 Ford F-150 XLT", "offers": {"price": 21000}},
  {"@type": "Vehicle", "name": "2020 Jeep Wrangler Sahara", "offers": {"price": 28000}},
  {"@type": "Vehicle", "vehicleIdentificationNumber": "4T1BF1FK0HU000031",
   "name": "2018 Subaru Outback Premium", "offers": {"price": 17500}}
]}
</script>
</head><body></body></html>
"""

STATE_FIXTURE = """
<html><body>
<script id="__NEXT_DATA__" type="application/json">
{"props": {"pageProps": {"searchResults": {"listings": [
  {"vin": "JN1AZ4EH0FM000010", "year": 2020, "make": "Nissan", "model": "Altima", "trim": "SV",
   "mileage": "41,000 mi", "price": "$14,500", "bodyType": "Sedan", "fuelType": "Gasoline",
   "dealer": {"name": "Riverside Auto", "city": "Nashville", "state": "TN"},
   "vdpUrl": "/cars-for-sale/vehicledetails/JN1AZ4EH0FM000010"},
  {"vin": "1G1ZD5ST9JF000011", "year": 2019, "make": "Chevrolet", "model": "Malibu",
   "mileage": 28900, "price": 13200, "certified": true,
   "dealer": {"name": "Metro Chevy", "city": "Knoxville", "state": "TN"}}
]}}}}
</script>
</body></html>
"""

HTML_CARD_FIXTURE = """
<html><body>
<div class="results-list">
  <div class="inventory-listing" data-vin="3FA6P0H79JR000020">
    <a href="/cars-for-sale/vehicledetails/3FA6P0H79JR000020">
      <h3 class="title">2021 Ford Fusion SE</h3>
    </a>
    <span class="price">$16,750</span>
    <span class="mileage">33,120 miles</span>
    <span class="dealer-name">Sunbelt Ford</span>
    <span class="dealer-location">Chattanooga, TN</span>
  </div>
  <div class="inventory-listing" data-vin="2T1BURHE0JC000021">
    <a href="/cars-for-sale/vehicledetails/2T1BURHE0JC000021">
      <h3 class="title">Certified 2022 Toyota Corolla LE</h3>
    </a>
    <span class="price">$19,300</span>
    <span class="mileage">15,890 miles</span>
    <span class="dealer-name">Toyota of Murfreesboro</span>
    <span class="dealer-location">Murfreesboro, TN</span>
    <span class="badge">Certified Pre-Owned</span>
  </div>
  <div class="inventory-listing" data-no-vin="true">
    <h3 class="title">2020 Kia Soul LX</h3>
    <span class="price">$12,000</span>
  </div>
</div>
</body></html>
"""


def _state_fixture_page(prefix: str, count: int) -> str:
    """A __NEXT_DATA__ style fixture with `count` uniquely-VIN'd listings."""
    listings = [
        {
            "vin": f"{prefix}{i:03d}",
            "year": 2021,
            "make": "Test",
            "model": "Car",
            "mileage": 10000 + i,
            "price": 15000 + i,
        }
        for i in range(count)
    ]
    payload = {"props": {"pageProps": {"searchResults": {"listings": listings}}}}
    return _pad_page(
        '<html><body><script id="__NEXT_DATA__" type="application/json">'
        + json.dumps(payload)
        + "</script></body></html>"
    )


class AutotraderScraperTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self._tmpdir, "test.db")
        self.conn = db.init_db(self.db_path)

    def tearDown(self) -> None:
        self.conn.close()

    def _scraper(self, limits: ScrapeLimits, opener) -> autotrader.AutotraderScraper:
        fetcher = Fetcher(self.conn, "autotrader", limits, robots=_PermissiveRobots(), opener=opener)
        return autotrader.AutotraderScraper(self.conn, limits, fetcher)

    # --- registration --------------------------------------------------------------
    def test_registered_under_expected_key(self) -> None:
        self.assertEqual(autotrader.AutotraderScraper.key, "autotrader")
        self.assertIn("autotrader", REGISTRY)
        self.assertIs(REGISTRY["autotrader"], autotrader.AutotraderScraper)

    # --- search_urls -----------------------------------------------------------------
    def test_search_urls_contain_configured_params_and_avoid_disallowed_paths(self) -> None:
        limits = ScrapeLimits(max_pages_per_run=3, min_seconds_between_requests=0)
        scraper = self._scraper(limits, opener=lambda *a, **k: (200, ""))
        urls = scraper.search_urls(_make_search())

        self.assertEqual(len(urls), 3)
        self.assertLessEqual(len(urls), limits.max_pages_per_run)
        self.assertEqual(len(urls), len(set(urls)))  # paging produces distinct URLs

        for url in urls:
            self.assertTrue(url.startswith("https://www.autotrader.com/cars-for-sale/all-cars?"))
            query = parse_qs(urlparse(url).query)
            self.assertEqual(query["zip"], ["38464"])
            self.assertEqual(query["searchRadius"], ["100"])
            self.assertEqual(query["startYear"], ["2021"])
            self.assertEqual(query["maxPrice"], ["20000"])
            self.assertEqual(query["maxMileage"], ["60000"])
            for frag in autotrader.DISALLOWED_PATH_FRAGMENTS:
                self.assertNotIn(frag, url)

        first_records = [parse_qs(urlparse(u).query)["firstRecord"][0] for u in urls]
        self.assertEqual(first_records, sorted(set(first_records), key=int))  # advancing pages

    def test_search_urls_capped_at_max_pages_per_run(self) -> None:
        limits = ScrapeLimits(max_pages_per_run=1, min_seconds_between_requests=0)
        scraper = self._scraper(limits, opener=lambda *a, **k: (200, ""))
        urls = scraper.search_urls(_make_search())
        self.assertEqual(len(urls), 1)

    def test_search_urls_empty_without_zip(self) -> None:
        limits = ScrapeLimits(max_pages_per_run=2, min_seconds_between_requests=0)
        scraper = self._scraper(limits, opener=lambda *a, **k: (200, ""))
        self.assertEqual(scraper.search_urls({}), [])

    # --- parse: JSON-LD --------------------------------------------------------------
    def test_parse_json_ld_fixture(self) -> None:
        limits = ScrapeLimits(min_seconds_between_requests=0)
        scraper = self._scraper(limits, opener=lambda *a, **k: (200, ""))
        listings = scraper.parse(JSON_LD_FIXTURE, "https://www.autotrader.com/cars-for-sale/all-cars?zip=38464")

        self.assertEqual(len(listings), 3)
        by_vin = {listing["vin"]: listing for listing in listings}

        accord = by_vin["1HGCV1F34LA000001"]
        self.assertEqual(accord["year"], 2022)
        self.assertEqual(accord["make"], "Honda")
        self.assertEqual(accord["model"], "Accord")
        self.assertEqual(accord["price_current"], 18995)  # "$18,995" -> int
        self.assertEqual(accord["mileage"], 37412)  # "37,412 miles" -> int
        self.assertEqual(accord["dealer_name"], "Acme Motors")
        self.assertEqual(accord["dealer_city"], "Springfield")
        self.assertEqual(accord["dealer_state"], "TN")
        self.assertNotIn("cpo", accord)

        camry = by_vin["5YJ3E1EA7KF000002"]
        self.assertEqual(camry["year"], 2021)
        self.assertEqual(camry["make"], "Toyota")
        self.assertEqual(camry["model"], "Camry")
        self.assertEqual(camry["price_current"], 19995)
        self.assertEqual(camry["mileage"], 22150)
        self.assertTrue(camry.get("cpo") is True)  # "Certified ..." in name

        kia = by_vin["1FA6P8TH0J5000003"]  # derived purely from the title fallback
        self.assertEqual(kia["year"], 2023)
        self.assertEqual(kia["make"], "Kia")
        self.assertEqual(kia["model"], "Forte")
        self.assertEqual(kia["trim"], "LXS")
        self.assertEqual(kia["price_current"], 17500)

    def test_run_drops_listing_missing_vin(self) -> None:
        limits = ScrapeLimits(max_pages_per_run=1, min_seconds_between_requests=0)
        scraper = self._scraper(limits, opener=lambda *a, **k: (200, _pad_page(DROP_NO_VIN_FIXTURE)))

        # The adapter itself does not filter VIN-less listings out of JSON-LD results...
        raw = scraper.parse(DROP_NO_VIN_FIXTURE, "https://www.autotrader.com/cars-for-sale/all-cars?zip=1")
        self.assertEqual(len(raw), 3)
        self.assertTrue(any("vin" not in listing for listing in raw))

        # ...ScraperBase.run() is what drops it.
        result = scraper.run(_make_search())
        self.assertEqual(result.status, "ok")
        self.assertEqual(len(result.listings), 2)
        self.assertEqual(
            {listing["vin"] for listing in result.listings},
            {"1FTEW1EP0JK000030", "4T1BF1FK0HU000031"},
        )

    # --- parse: embedded JSON state ---------------------------------------------------
    def test_parse_embedded_state_fixture(self) -> None:
        limits = ScrapeLimits(min_seconds_between_requests=0)
        scraper = self._scraper(limits, opener=lambda *a, **k: (200, ""))
        listings = scraper.parse(STATE_FIXTURE, "https://www.autotrader.com/cars-for-sale/all-cars?zip=38464")

        self.assertEqual(len(listings), 2)
        by_vin = {listing["vin"]: listing for listing in listings}

        altima = by_vin["JN1AZ4EH0FM000010"]
        self.assertEqual(altima["year"], 2020)
        self.assertEqual(altima["make"], "Nissan")
        self.assertEqual(altima["model"], "Altima")
        self.assertEqual(altima["trim"], "SV")
        self.assertEqual(altima["price_current"], 14500)  # "$14,500" -> int
        self.assertEqual(altima["mileage"], 41000)  # "41,000 mi" -> int
        self.assertEqual(altima["dealer_name"], "Riverside Auto")
        self.assertEqual(altima["dealer_city"], "Nashville")
        self.assertEqual(altima["dealer_state"], "TN")
        self.assertTrue(altima["listing_url"].endswith("/cars-for-sale/vehicledetails/JN1AZ4EH0FM000010"))

        malibu = by_vin["1G1ZD5ST9JF000011"]
        self.assertEqual(malibu["price_current"], 13200)
        self.assertEqual(malibu["mileage"], 28900)
        self.assertTrue(malibu.get("cpo") is True)

    # --- parse: HTML card fallback -----------------------------------------------------
    def test_parse_html_card_fixture(self) -> None:
        limits = ScrapeLimits(min_seconds_between_requests=0)
        scraper = self._scraper(limits, opener=lambda *a, **k: (200, ""))
        listings = scraper.parse(HTML_CARD_FIXTURE, "https://www.autotrader.com/cars-for-sale/all-cars?zip=38464")

        # the third card has no data-vin and must not appear
        self.assertEqual(len(listings), 2)
        by_vin = {listing["vin"]: listing for listing in listings}

        fusion = by_vin["3FA6P0H79JR000020"]
        self.assertEqual(fusion["year"], 2021)
        self.assertEqual(fusion["make"], "Ford")
        self.assertEqual(fusion["model"], "Fusion")
        self.assertEqual(fusion["trim"], "SE")
        self.assertEqual(fusion["price_current"], 16750)
        self.assertEqual(fusion["mileage"], 33120)
        self.assertEqual(fusion["dealer_name"], "Sunbelt Ford")
        self.assertEqual(fusion["dealer_city"], "Chattanooga")
        self.assertEqual(fusion["dealer_state"], "TN")
        self.assertNotIn("cpo", fusion)
        self.assertTrue(fusion["listing_url"].endswith("/cars-for-sale/vehicledetails/3FA6P0H79JR000020"))

        corolla = by_vin["2T1BURHE0JC000021"]
        self.assertEqual(corolla["year"], 2022)
        self.assertEqual(corolla["make"], "Toyota")
        self.assertEqual(corolla["model"], "Corolla")
        self.assertEqual(corolla["trim"], "LE")
        self.assertEqual(corolla["price_current"], 19300)
        self.assertEqual(corolla["mileage"], 15890)
        self.assertEqual(corolla["dealer_name"], "Toyota of Murfreesboro")
        self.assertTrue(corolla.get("cpo") is True)

    # --- parse: garbage / empty input --------------------------------------------------
    def test_parse_garbage_or_empty_returns_empty_list(self) -> None:
        limits = ScrapeLimits(min_seconds_between_requests=0)
        scraper = self._scraper(limits, opener=lambda *a, **k: (200, ""))
        url = "https://www.autotrader.com/cars-for-sale/all-cars?zip=1"

        self.assertEqual(scraper.parse("", url), [])
        self.assertEqual(scraper.parse("   ", url), [])
        self.assertEqual(scraper.parse("<html><body>Nothing to see here.</body></html>", url), [])
        self.assertEqual(scraper.parse("{not even valid json <<< ???", url), [])
        self.assertEqual(
            scraper.parse(
                '<script type="application/ld+json">{"broken": [1, 2,}</script>', url
            ),
            [],
        )

    # --- caps hold end to end ----------------------------------------------------------
    def test_caps_hold_end_to_end(self) -> None:
        limits = ScrapeLimits(max_pages_per_run=2, max_listings_per_day=5, min_seconds_between_requests=0)
        calls = {"n": 0}

        def fake_opener(url, headers, timeout):
            calls["n"] += 1
            first_record = parse_qs(urlparse(url).query).get("firstRecord", ["0"])[0]
            return 200, _state_fixture_page(prefix=f"CAP{first_record}", count=4)

        scraper = self._scraper(limits, opener=fake_opener)
        result = scraper.run(_make_search())

        self.assertLessEqual(calls["n"], 2)
        self.assertEqual(result.pages_fetched, calls["n"])
        self.assertLessEqual(len(result.listings), 5)
        self.assertEqual(len(result.listings), len({l["vin"] for l in result.listings}))  # no dup VINs

        usage = db.scrape_usage_today(self.conn)
        self.assertEqual(usage["listings"], len(result.listings))
        self.assertLessEqual(usage["listings"], limits.max_listings_per_day)

        # sanity: the fixture had more listings available than the cap allows
        self.assertEqual(calls["n"], 2)
        self.assertEqual(len(result.listings), 5)

    # --- blocked: challenge body, no retry ----------------------------------------------
    def test_challenge_body_yields_blocked_with_no_retry(self) -> None:
        limits = ScrapeLimits(max_pages_per_run=2, min_seconds_between_requests=0)
        calls = {"n": 0}

        def fake_opener(url, headers, timeout):
            calls["n"] += 1
            return 200, "<html><body>Just a moment... enable javascript and cookies to continue.</body></html>"

        scraper = self._scraper(limits, opener=fake_opener)
        result = scraper.run(_make_search())

        self.assertEqual(result.status, "blocked")
        self.assertEqual(calls["n"], 1)
        self.assertEqual(result.listings, [])


if __name__ == "__main__":
    unittest.main()
