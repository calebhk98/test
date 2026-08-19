"""Market appraisal endpoints and pages: /api/market, /api/appraise, /api/deals,
/market, /appraise, and the 'Versus the market' section on listing detail pages.

Split out of the former test_webapp.py -- see webapp_test_support.py for the shared
server scaffolding this and the other test_webapp_*.py modules use.
"""

from __future__ import annotations

import unittest

from carmon import db

from .webapp_test_support import LiveServerCase, make_listing, temp_db_config


class MarketFeaturesTestCase(LiveServerCase, unittest.TestCase):
    """Market appraisal endpoints and pages: /api/market, /api/appraise, /api/deals,
    /market, /appraise, and the 'Versus the market' section on listing detail pages."""

    def setUp(self) -> None:
        super().setUp()
        self.db_path = self.tmp_root / "carmon-market-test.db"
        config = temp_db_config(self.db_path)

        conn = db.init_db(self.db_path)

        # 15+ comparable Toyota Camry listings, spread across years/mileages, with a
        # roughly-linear price-vs-mileage relationship so a real regression fit happens
        # (model_summary needs >= MIN_ROWS_MILEAGE=6; this gives it 15).
        self.camry_vins = []
        for i in range(15):
            year = 2018 + (i % 5)
            mileage = 8000 + i * 6000
            price = round(31000 - mileage * 0.055 + (i % 3) * 150)
            vin = f"VINCAMRY{i:08d}"
            self.camry_vins.append(vin)
            db.upsert_listing(
                conn,
                make_listing(vin, make="Toyota", model="Camry", year=year, mileage=mileage, price_current=price),
                seen_date="2026-07-01",
            )
        # Re-seen a few of them a month later, with a couple of price cuts, so the trend
        # table has more than one month and price_cut_stats has something to report.
        for i in (0, 1, 2):
            vin = self.camry_vins[i]
            db.upsert_listing(
                conn,
                make_listing(vin, make="Toyota", model="Camry", year=2018 + (i % 5),
                             mileage=8000 + i * 6000 + 500, price_current=25000 - i * 100),
                seen_date="2026-08-10",
            )

        # A thin-data car: unique make/model, nothing else remotely like it in the DB, so
        # its appraisal must fall back to "every tracked listing" and say so.
        self.thin_vin = "VINYUGO000000001"
        db.upsert_listing(
            conn,
            make_listing(self.thin_vin, make="Yugo", model="GV", year=1985, mileage=90000, price_current=2000),
            seen_date="2026-08-01",
        )

        conn.close()

        self._start_server(config)

    # -- JSON API -------------------------------------------------------
    def test_api_market_report_shape(self):
        data = self._get_json("/api/market")
        self.assertIn("trend", data)
        self.assertIn("models", data)
        self.assertIn("best_deals", data)
        self.assertIn("data_note", data)
        self.assertGreaterEqual(len(data["trend"]), 1)
        self.assertTrue(any(m["make"] == "Toyota" and m["model"] == "Camry" for m in data["models"]))
        camry_summary = next(m for m in data["models"] if m["model"] == "Camry")
        self.assertGreaterEqual(camry_summary["sample_size"], 12)
        # 15 comparables is enough for a real mileage regression, not just a median.
        self.assertIsNotNone(camry_summary["r_squared"])
        self.assertIsNotNone(camry_summary["dollars_per_1k_miles"])

    def test_api_market_trend_endpoint(self):
        data = self._get_json("/api/market/trend?make=Toyota&model=Camry&months=6")
        self.assertEqual(data["make"], "Toyota")
        self.assertEqual(data["model"], "Camry")
        self.assertGreaterEqual(len(data["trend"]), 2)  # July + August seeded above

    def test_api_appraise_with_price_gives_grade(self):
        data = self._get_json("/api/appraise?make=Toyota&model=Camry&year=2020&mileage=30000&price=20000")
        self.assertIsNotNone(data["expected_price"])
        self.assertIsNotNone(data["grade"])
        self.assertGreater(data["sample_size"], 0)

    def test_api_appraise_without_price_has_no_grade(self):
        data = self._get_json("/api/appraise?make=Toyota&model=Camry&year=2020&mileage=30000")
        self.assertIsNotNone(data["expected_price"])
        self.assertIsNone(data["grade"])
        self.assertIsNone(data["actual_price"])

    def test_api_appraise_invalid_int_400(self):
        data = self._get_json("/api/appraise?make=Toyota&model=Camry&mileage=abc", expect_status=400)
        self.assertIn("error", data)

    def test_api_listing_detail_carries_appraisal(self):
        data = self._get_json(f"/api/listings/{self.camry_vins[5]}")
        self.assertIn("appraisal", data)
        self.assertIsNotNone(data["appraisal"])
        self.assertIn("expected_price", data["appraisal"])

    def test_api_deals_returns_list(self):
        data = self._get_json("/api/deals?limit=5")
        self.assertIn("deals", data)
        self.assertIsInstance(data["deals"], list)
        self.assertLessEqual(len(data["deals"]), 5)
        self.assertEqual(data["count"], len(data["deals"]))
        if data["deals"]:
            self.assertIn("appraisal", data["deals"][0])

    # -- HTML -------------------------------------------------------
    def test_market_page_shows_model_table_chart_and_data_note(self):
        status, body = self._get("/market")
        self.assertEqual(status, 200)
        text = body.decode("utf-8")
        self.assertIn("Camry", text)
        self.assertIn("<svg", text)
        self.assertIn('class="trend-chart"', text)
        self.assertIn("Best deals right now", text)
        # the market_report data_note caveat about cross-sectional vs longitudinal data
        self.assertIn("weeks of history", text)

    def test_appraise_page_renders_grade(self):
        status, body = self._get("/appraise?make=Toyota&model=Camry&year=2020&mileage=30000&price=20000")
        self.assertEqual(status, 200)
        text = body.decode("utf-8")
        self.assertIn("Expected price", text)
        self.assertIn("confidence", text)
        self.assertIn("Grade", text)

    def test_listing_page_shows_versus_the_market(self):
        status, body = self._get(f"/listing/{self.camry_vins[0]}")
        self.assertEqual(status, 200)
        text = body.decode("utf-8")
        self.assertIn("Versus the market", text)
        self.assertIn("Expected price", text)

    def test_thin_data_car_surfaces_caveat_note(self):
        status, body = self._get(f"/listing/{self.thin_vin}")
        self.assertEqual(status, 200)
        text = body.decode("utf-8")
        # No other Yugo listing exists at all, so the appraisal falls back to "every
        # tracked listing" and must say so, in plain sight -- never hidden.
        self.assertIn("No comparables for this make at all", text)

    def test_dashboard_has_vs_market_column(self):
        status, body = self._get("/")
        self.assertEqual(status, 200)
        text = body.decode("utf-8")
        self.assertIn("Vs market", text)

    def test_nav_links_to_market_and_appraise(self):
        status, body = self._get("/")
        text = body.decode("utf-8")
        self.assertIn('href="/market"', text)
        self.assertIn('href="/appraise"', text)


if __name__ == "__main__":
    unittest.main()
