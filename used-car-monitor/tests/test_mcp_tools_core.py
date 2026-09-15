"""Tests for the listings/stats/scoring/reliability/sources MCP tools: search_listings,
get_listing, get_price_history, top_listings, new_listings, price_drops, get_stats,
get_quota_pace, get_latest_digest, explain_score, score_hypothetical, list_sources,
get_reliability, refresh_reliability, list_reliability.

Split out of the former test_mcp_server.py; protocol-framing tests live in
test_mcp_protocol.py, market/appraisal tools in test_mcp_tools_market.py, and
scraper/settings tools in test_mcp_tools_scrapers.py -- see mcp_server_test_support.py
for the shared MCPServerTestCase base all of them use.
"""

from __future__ import annotations

import json
import unittest
from datetime import date
from unittest.mock import patch

from carmon import db
from carmon import nhtsa as nhtsamod
from carmon import quota as quotamod

from .mcp_server_test_support import RELIABLE_FACTS, MCPServerTestCase, make_listing


class FakeReliabilityResponse:
    """Mimics a requests.Response for the NHTSA endpoints."""

    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


class FakeReliabilitySession:
    """Stub session with a .get(url, params=, timeout=) matching requests.Session, no network."""

    def __init__(self):
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        if "complaints" in url:
            return FakeReliabilityResponse({
                "count": 2,
                "results": [
                    {"components": "ENGINE", "crash": False, "fire": False,
                     "numberOfInjuries": 0, "numberOfDeaths": 0},
                    {"components": "ENGINE,TRANSMISSION", "crash": False, "fire": False,
                     "numberOfInjuries": 0, "numberOfDeaths": 0},
                ],
            })
        if "recalls" in url:
            return FakeReliabilityResponse({
                "Count": 1,
                "results": [
                    {"NHTSACampaignNumber": "24V009000", "Component": "ENGINE",
                     "Summary": "stall risk", "Consequence": "loss of power",
                     "Remedy": "software update", "ReportReceivedDate": "05/06/2024",
                     "parkIt": False, "parkOutSide": False},
                ],
            })
        return FakeReliabilityResponse({})


class FailingSession:
    """Stub session that always fails, to prove refresh_reliability handles it without a crash."""

    def get(self, url, params=None, timeout=None):
        raise OSError("simulated network outage")


class TestToolsCall(MCPServerTestCase):
    def test_search_listings(self):
        resp = self.call_tool("search_listings", {"make": "Honda"})
        payload = self._tool_json(resp)
        self.assertGreaterEqual(payload["count"], 1)
        for listing in payload["listings"]:
            self.assertEqual(listing["make"], "Honda")

    def test_search_listings_sort_validation(self):
        resp = self.call_tool("search_listings", {"sort": "not-a-real-sort"})
        result = resp["result"]
        self.assertTrue(result["isError"])

    def test_search_listings_max_complaints_filters_and_keeps_unknown(self):
        # VIN0001 (Honda Civic, 5 complaints) and VIN0003 (Kia Forte, no cached NHTSA
        # data) should both survive a max_complaints=50 filter; VIN0002 (Toyota
        # Corolla, 500 complaints) should be dropped.
        resp = self.call_tool("search_listings", {"max_complaints": 50, "active_only": True})
        payload = self._tool_json(resp)
        vins = {row["vin"] for row in payload["listings"]}
        self.assertIn("VIN0001", vins)
        self.assertIn("VIN0003", vins, "listing with no cached NHTSA data must be kept, not excluded")
        self.assertNotIn("VIN0002", vins)

    def test_search_listings_max_recalls_filters(self):
        resp = self.call_tool("search_listings", {"max_recalls": 1, "active_only": True})
        payload = self._tool_json(resp)
        vins = {row["vin"] for row in payload["listings"]}
        self.assertIn("VIN0001", vins)  # 1 recall
        self.assertNotIn("VIN0002", vins)  # 4 recalls
        self.assertIn("VIN0003", vins)  # unknown, kept

    def test_search_listings_no_demo_data_has_no_warning_key(self):
        resp = self.call_tool("search_listings", {})
        payload = self._tool_json(resp)
        self.assertNotIn("warning", payload)

    def test_search_listings_flags_demo_data_with_warning(self):
        conn = db.connect(self.db_path)
        db.upsert_listing(
            conn,
            make_listing(vin="DEMOVIN0000000002", source="demo", make="Mazda", model="Mazda3"),
            seen_date="2026-08-17",
        )
        conn.close()
        resp = self.call_tool("search_listings", {"make": "Mazda"})
        result = resp["result"]
        self.assertFalse(result.get("isError"))
        payload = self._tool_json(resp)
        self.assertIn("warning", payload)
        self.assertIsInstance(payload["warning"], str)
        self.assertIn("DEMO", payload["warning"])

    def test_get_listing_found(self):
        resp = self.call_tool("get_listing", {"vin": "VIN0001"})
        payload = self._tool_json(resp)
        self.assertEqual(payload["listing"]["vin"], "VIN0001")
        self.assertIn("price_history", payload)
        self.assertIn("cross_shop_links", payload)
        self.assertGreaterEqual(len(payload["price_history"]), 1)

    def test_get_listing_includes_cached_nhtsa_data_and_urls(self):
        # VIN0001 is a Honda Civic 2022, seeded with RELIABLE_FACTS in setUp.
        resp = self.call_tool("get_listing", {"vin": "VIN0001"})
        payload = self._tool_json(resp)
        listing = payload["listing"]
        self.assertEqual(listing["complaint_count"], RELIABLE_FACTS["complaint_count"])
        self.assertEqual(listing["recall_count"], RELIABLE_FACTS["recall_count"])
        self.assertIn("nhtsa_vin_url", payload)
        self.assertIn("VIN0001", payload["nhtsa_vin_url"])
        self.assertIn("nhtsa_model_url", payload)
        self.assertIn("Honda", payload["nhtsa_model_url"])

    def test_get_listing_not_found(self):
        resp = self.call_tool("get_listing", {"vin": "DOES-NOT-EXIST"})
        result = resp["result"]
        self.assertTrue(result["isError"])
        self.assertIn("DOES-NOT-EXIST", result["content"][0]["text"])

    def test_get_listing_missing_vin_is_tool_error(self):
        resp = self.call_tool("get_listing", {})
        result = resp["result"]
        self.assertTrue(result["isError"])

    def test_get_listing_no_demo_data_has_no_warning_key(self):
        resp = self.call_tool("get_listing", {"vin": "VIN0001"})
        payload = self._tool_json(resp)
        self.assertNotIn("warning", payload)

    def test_get_listing_flags_demo_data_with_warning(self):
        conn = db.connect(self.db_path)
        db.upsert_listing(
            conn,
            make_listing(vin="DEMOVIN0000000003", source="demo", make="Kia", model="Seltos"),
            seen_date="2026-08-17",
        )
        conn.close()
        resp = self.call_tool("get_listing", {"vin": "DEMOVIN0000000003"})
        result = resp["result"]
        self.assertFalse(result.get("isError"))
        payload = self._tool_json(resp)
        self.assertIn("warning", payload)
        self.assertIsInstance(payload["warning"], str)
        self.assertIn("DEMO", payload["warning"])

    def test_get_price_history(self):
        resp = self.call_tool("get_price_history", {"vin": "VIN0001"})
        payload = self._tool_json(resp)
        self.assertEqual(payload["vin"], "VIN0001")
        self.assertGreaterEqual(len(payload["price_history"]), 2)

    def test_top_listings(self):
        resp = self.call_tool("top_listings", {"limit": 5})
        payload = self._tool_json(resp)
        self.assertIn("listings", payload)
        if len(payload["listings"]) >= 2:
            scores = [row["score"] for row in payload["listings"]]
            self.assertEqual(scores, sorted(scores, reverse=True))

    def test_new_listings(self):
        resp = self.call_tool("new_listings", {"days": 30, "limit": 10})
        payload = self._tool_json(resp)
        self.assertIn("listings", payload)
        self.assertGreaterEqual(payload["count"], 1)

    def test_price_drops(self):
        resp = self.call_tool("price_drops", {"days": 30, "limit": 10})
        payload = self._tool_json(resp)
        self.assertIn("listings", payload)
        vins = {row["vin"] for row in payload["listings"]}
        self.assertIn("VIN0001", vins)

    def test_get_stats(self):
        resp = self.call_tool("get_stats", {})
        payload = self._tool_json(resp)
        self.assertIn("listings_total", payload)
        self.assertIn("api_monthly_cap", payload)
        self.assertEqual(payload["api_monthly_cap"], self.config.api.get("monthly_call_cap"))
        # Pace context is embedded alongside the existing stats keys, not in place of them.
        self.assertIn("pace", payload)
        self.assertEqual(payload["pace"]["used"], payload["api_calls_this_month"])
        self.assertEqual(payload["pace"]["cap"], payload["api_monthly_cap"])
        self.assertIn("pace_ratio", payload["pace"])
        self.assertIn("pace_label", payload["pace"])
        # No demo data was seeded in setUp for this test class.
        self.assertEqual(payload["demo_listings"], 0)
        self.assertIsNone(payload["demo_warning"])

    def test_get_stats_reports_demo_listings(self):
        conn = db.connect(self.db_path)
        db.upsert_listing(
            conn,
            make_listing(vin="DEMOVIN0000000001", source="demo", make="Toyota", model="Corolla"),
            seen_date="2026-08-17",
        )
        conn.close()
        resp = self.call_tool("get_stats", {})
        payload = self._tool_json(resp)
        self.assertEqual(payload["demo_listings"], 1)
        self.assertIsNotNone(payload["demo_warning"])
        self.assertIn("DEMO", payload["demo_warning"])

    def test_get_quota_pace(self):
        cap = int(self.config.api.get("monthly_call_cap", 500))
        conn = db.connect(self.db_path)
        for _ in range(7):
            db.record_api_call(conn, "search", 200, "test call")
        used = db.calls_this_month(conn)
        conn.close()

        today = date.today()
        expected = quotamod.pace(used, cap, today)

        resp = self.call_tool("get_quota_pace", {})
        payload = self._tool_json(resp)

        self.assertEqual(payload["used"], expected["used"])
        self.assertEqual(payload["cap"], expected["cap"])
        self.assertEqual(payload["pace_ratio"], expected["pace_ratio"])
        self.assertEqual(payload["pace_label"], expected["pace_label"])
        self.assertEqual(payload["expected_by_now"], expected["expected_by_now"])
        self.assertIn("summary", payload)
        self.assertIn("bar", payload)
        self.assertIn(str(payload["used"]), payload["summary"])
        self.assertIn("month_end_sweep", payload)
        self.assertIn("should_sweep", payload["month_end_sweep"])
        self.assertIn("budget", payload["month_end_sweep"])
        self.assertIn("reserve", payload["month_end_sweep"])
        self.assertIn("reason", payload["month_end_sweep"])

    def test_get_quota_pace_width(self):
        resp = self.call_tool("get_quota_pace", {"width": 10})
        payload = self._tool_json(resp)
        self.assertEqual(len(payload["bar"]), 10)

    def test_get_latest_digest_no_digest_message(self):
        resp = self.call_tool("get_latest_digest", {})
        result = resp["result"]
        text = result["content"][0]["text"]
        # Should not be JSON-wrapped: plain text content.
        with self.assertRaises(json.JSONDecodeError):
            json.loads(text)
        self.assertIn("digest", text.lower())

    def test_explain_score(self):
        resp = self.call_tool("explain_score", {"vin": "VIN0001"})
        payload = self._tool_json(resp)
        self.assertEqual(payload["vin"], "VIN0001")
        self.assertIn("recomputed", payload)
        self.assertIn("score", payload["recomputed"])
        self.assertIn("explanation", payload)
        self.assertIsInstance(payload["explanation"], str)
        self.assertIn("stored_breakdown", payload)

    def test_explain_score_uses_cached_enrichment_and_mentions_nhtsa(self):
        # VIN0001's model/year has seeded reliability + MPG data, so the recomputed
        # explanation should reflect it instead of showing "no data".
        resp = self.call_tool("explain_score", {"vin": "VIN0001"})
        payload = self._tool_json(resp)
        labels = {c["label"] for c in payload["recomputed"]["components"]}
        self.assertIn("NHTSA complaints", labels)
        self.assertIn("NHTSA recalls", labels)
        self.assertIn("NHTSA", payload["explanation"])

    def test_explain_score_not_found(self):
        resp = self.call_tool("explain_score", {"vin": "NOPE"})
        result = resp["result"]
        self.assertTrue(result["isError"])

    def test_score_hypothetical(self):
        resp = self.call_tool("score_hypothetical", {
            "make": "Honda",
            "model": "Civic",
            "mileage": 45000,
            "distance_miles": 70,
            "price_current": 19000,
            "price_first_seen": 20000,
            "cpo": False,
        })
        payload = self._tool_json(resp)
        self.assertIn("result", payload)
        self.assertIn("score", payload["result"])
        self.assertIn("components", payload["result"])
        self.assertIn("explanation", payload)

    def test_score_hypothetical_defaults(self):
        resp = self.call_tool("score_hypothetical", {"make": "Kia", "model": "Forte"})
        payload = self._tool_json(resp)
        self.assertIn("result", payload)

    def test_score_hypothetical_with_mpg_and_complaints(self):
        resp = self.call_tool("score_hypothetical", {
            "make": "Mazda",
            "model": "3",
            "year": 2023,
            "mileage": 20000,
            "price_current": 17000,
            "combined_mpg": 36,
            "complaint_count": 20,
            "recall_count": 1,
        })
        payload = self._tool_json(resp)
        labels = {c["label"] for c in payload["result"]["components"]}
        self.assertIn("fuel economy", labels)
        self.assertIn("NHTSA complaints", labels)
        self.assertIn("NHTSA recalls", labels)
        self.assertIn("model year", labels)
        fuel = next(c for c in payload["result"]["components"] if c["label"] == "fuel economy")
        self.assertNotIn("no MPG data", fuel["detail"])

    def test_get_reliability_returns_counts_and_caveat(self):
        resp = self.call_tool("get_reliability", {"make": "Honda", "model": "Civic", "year": 2022})
        payload = self._tool_json(resp)
        self.assertEqual(payload["complaint_count"], RELIABLE_FACTS["complaint_count"])
        self.assertEqual(payload["recall_count"], RELIABLE_FACTS["recall_count"])
        self.assertIn("top_components", payload)
        self.assertIn("nhtsa_url", payload)
        self.assertIn("caveat", payload)
        self.assertIn("sold", payload["caveat"].lower())

    def test_get_reliability_unknown_model_is_error(self):
        resp = self.call_tool("get_reliability", {"make": "Yugo", "model": "GV", "year": 1988})
        result = resp["result"]
        self.assertTrue(result["isError"])
        text = result["content"][0]["text"]
        self.assertTrue("carmon enrich" in text or "refresh_reliability" in text)

    def test_get_reliability_missing_args_is_tool_error(self):
        resp = self.call_tool("get_reliability", {"make": "Honda"})
        result = resp["result"]
        self.assertTrue(result["isError"])

    def test_list_reliability_lists_cached_rows_sorted_by_complaints(self):
        resp = self.call_tool("list_reliability", {"limit": 10})
        payload = self._tool_json(resp)
        self.assertGreaterEqual(payload["count"], 2)
        models = payload["models"]
        counts = [row["complaint_count"] for row in models]
        self.assertEqual(counts, sorted(counts, reverse=True))
        makes = {(row["make"], row["model"]) for row in models}
        self.assertIn(("honda", "civic"), makes)
        self.assertIn(("toyota", "corolla"), makes)

    def test_refresh_reliability_uses_injected_fake_session_no_network(self):
        fake_session = FakeReliabilitySession()
        with patch.object(nhtsamod.requests, "Session", return_value=fake_session):
            resp = self.call_tool(
                "refresh_reliability", {"make": "Mazda", "model": "3", "year": 2023}
            )
        payload = self._tool_json(resp)
        self.assertEqual(payload["complaint_count"], 2)
        self.assertEqual(payload["recall_count"], 1)
        self.assertIn("nhtsa_url", payload)
        self.assertTrue(fake_session.calls, "the fake session should have been used, not the real network")
        # And it is now cached, retrievable through get_reliability without any session.
        cached_resp = self.call_tool("get_reliability", {"make": "Mazda", "model": "3", "year": 2023})
        cached = self._tool_json(cached_resp)
        self.assertEqual(cached["complaint_count"], 2)

    def test_refresh_reliability_failure_is_error_not_crash(self):
        # Speed up retries so the failure path doesn't sleep through backoff.
        self.config.data.setdefault("enrichment", {})["max_retries"] = 0
        with patch.object(nhtsamod.requests, "Session", return_value=FailingSession()):
            resp = self.call_tool(
                "refresh_reliability", {"make": "Ghost", "model": "Car", "year": 1999, "force": True}
            )
        result = resp["result"]
        self.assertTrue(result["isError"])

    def test_refresh_reliability_missing_args_is_tool_error(self):
        resp = self.call_tool("refresh_reliability", {"make": "Honda", "model": "Civic"})
        result = resp["result"]
        self.assertTrue(result["isError"])

    def test_list_sources(self):
        resp = self.call_tool("list_sources", {})
        payload = self._tool_json(resp)
        self.assertIn("sources", payload)
        self.assertIn("manufacturer_cpo", payload["sources"])
        self.assertIn("retailer", payload["sources"])
        self.assertIn("aggregator", payload["sources"])

    def test_unknown_tool_is_error_not_transport_error(self):
        resp = self.call_tool("not_a_real_tool", {})
        self.assertNotIn("error", resp)
        result = resp["result"]
        self.assertTrue(result["isError"])
        self.assertIn("Unknown tool", result["content"][0]["text"])

    def test_tools_call_missing_name_is_invalid_params(self):
        resp = self.call("tools/call", {"arguments": {}})
        self.assertIn("error", resp)
        self.assertEqual(resp["error"]["code"], -32602)


if __name__ == "__main__":
    unittest.main()
