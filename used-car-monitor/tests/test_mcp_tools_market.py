"""Market/appraisal MCP tools: appraise_car, market_trend, market_report, best_deals,
list_comparables, plus get_listing's 'appraisal' key.

Split out of the former test_mcp_server.py -- see mcp_server_test_support.py for the
shared MCPServerTestCase base this and the other test_mcp_*.py modules use.
"""

from __future__ import annotations

import unittest

from carmon import db

from .mcp_server_test_support import MCPServerTestCase, make_listing


class TestMarketTools(MCPServerTestCase):
    """Market/appraisal tools: appraise_car, market_trend, market_report, best_deals,
    list_comparables, plus get_listing's new 'appraisal' key. These need a real
    comparable population, so this class seeds a healthy batch of Honda Civic
    listings across several model years and mileages on top of the base setUp."""

    def setUp(self):
        super().setUp()
        conn = db.connect(self.db_path)
        # 15 additional Honda Civic comparables across 2021-2023, mileage decreasing
        # with newer model year, so a real weighted-least-squares fit is possible
        # (MIN_ROWS_FULL == 12) and pins down a believable price/mileage relationship.
        specs = [
            (2021, 55000, 15500), (2021, 60000, 15000), (2021, 50000, 16000),
            (2021, 65000, 14500), (2021, 58000, 15200),
            (2022, 40000, 17500), (2022, 35000, 18000), (2022, 45000, 17000),
            (2022, 38000, 17700), (2022, 32000, 18300),
            (2023, 20000, 20500), (2023, 15000, 21000), (2023, 25000, 20000),
            (2023, 18000, 20700), (2023, 22000, 20200),
        ]
        for i, (year, mileage, price) in enumerate(specs, start=100):
            db.upsert_listing(
                conn,
                make_listing(
                    vin=f"CIVCOMP{i:04d}", year=year, mileage=mileage,
                    price_current=price, price_first_seen=price,
                ),
                seen_date="2026-08-17",
            )
        conn.close()

    def test_appraise_car_priced_returns_expected_price_grade_and_sample_size(self):
        resp = self.call_tool("appraise_car", {
            "make": "Honda", "model": "Civic", "year": 2022, "mileage": 37000, "price": 15000,
        })
        payload = self._tool_json(resp)
        self.assertIsNotNone(payload["expected_price"])
        self.assertIsNotNone(payload["grade"])
        self.assertGreaterEqual(payload["sample_size"], 12)
        self.assertIn(payload["basis_level"], ("model_year", "model"))
        self.assertIn("confidence", payload)
        self.assertIn("summary", payload)

    def test_appraise_car_without_price_has_no_grade(self):
        resp = self.call_tool("appraise_car", {
            "make": "Honda", "model": "Civic", "year": 2022, "mileage": 37000,
        })
        payload = self._tool_json(resp)
        self.assertIsNotNone(payload["expected_price"])
        self.assertIsNone(payload["grade"])
        self.assertIsNone(payload["delta"])
        self.assertIsNone(payload["actual_price"])

    def test_appraise_car_by_vin_appraises_stored_listing(self):
        resp = self.call_tool("appraise_car", {"vin": "VIN0001"})
        payload = self._tool_json(resp)
        self.assertIsNotNone(payload["expected_price"])
        self.assertEqual(payload["actual_price"], 17000)  # VIN0001's later price_current

    def test_appraise_car_vin_not_found(self):
        resp = self.call_tool("appraise_car", {"vin": "DOES-NOT-EXIST"})
        result = resp["result"]
        self.assertTrue(result["isError"])

    def test_appraise_car_no_comparables_falls_back_with_notes(self):
        resp = self.call_tool("appraise_car", {
            "make": "Zzyzx", "model": "Rareone", "year": 2022, "mileage": 30000, "price": 20000,
        })
        payload = self._tool_json(resp)
        self.assertIn(payload["basis_level"], ("make", "all"))
        self.assertTrue(payload["notes"], "fallback appraisal must carry caveats in notes")

    def test_market_trend_returns_trend_days_and_cuts(self):
        resp = self.call_tool("market_trend", {"make": "Honda", "model": "Civic", "months": 6})
        payload = self._tool_json(resp)
        self.assertIn("trend", payload)
        self.assertIsInstance(payload["trend"], list)
        self.assertIn("days_on_market", payload)
        self.assertIn("sample_size", payload["days_on_market"])
        self.assertIn("price_cuts", payload)
        self.assertIn("tracked", payload["price_cuts"])

    def test_market_trend_defaults_to_whole_market(self):
        resp = self.call_tool("market_trend", {})
        payload = self._tool_json(resp)
        self.assertIsNone(payload["make"])
        self.assertIsNone(payload["model"])
        self.assertIn("trend", payload)

    def test_market_report_has_all_keys(self):
        resp = self.call_tool("market_report", {"months": 6})
        payload = self._tool_json(resp)
        for key in ("listings_tracked", "trend", "models", "days_on_market", "price_cuts",
                    "best_deals", "data_note"):
            self.assertIn(key, payload, msg=key)
        self.assertGreaterEqual(payload["listings_tracked"], 15)

    def test_best_deals_entries_carry_appraisal(self):
        resp = self.call_tool("best_deals", {"limit": 10, "min_sample": 3})
        payload = self._tool_json(resp)
        self.assertIn("listings", payload)
        self.assertGreater(len(payload["listings"]), 0)
        for row in payload["listings"]:
            self.assertIn("appraisal", row)
            self.assertIn("delta_pct", row["appraisal"])
            self.assertIn("sample_size", row["appraisal"])

    def test_list_comparables_returns_rows(self):
        resp = self.call_tool("list_comparables", {
            "make": "Honda", "model": "Civic", "year": 2022, "year_window": 1,
        })
        payload = self._tool_json(resp)
        self.assertIn("listings", payload)
        self.assertGreaterEqual(payload["count"], 10)
        for row in payload["listings"]:
            self.assertEqual(row["make"], "Honda")

    def test_list_comparables_requires_make_and_model(self):
        resp = self.call_tool("list_comparables", {"make": "Honda"})
        result = resp["result"]
        self.assertTrue(result["isError"])

    def test_get_listing_carries_appraisal(self):
        resp = self.call_tool("get_listing", {"vin": "VIN0001"})
        payload = self._tool_json(resp)
        self.assertIn("appraisal", payload)
        self.assertIsNotNone(payload["appraisal"])
        self.assertIn("sample_size", payload["appraisal"])
        self.assertIn("basis_level", payload["appraisal"])


if __name__ == "__main__":
    unittest.main()
