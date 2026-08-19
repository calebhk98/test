"""Tests for carmon.mcp_server: JSON-RPC/MCP request handling over stdio."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from carmon import db
from carmon import demo as demomod
from carmon import market as marketmod
from carmon import nhtsa as nhtsamod
from carmon import pipeline as pipelinemod
from carmon import quota as quotamod
from carmon import settings as settingsmod
from carmon.config import Config, load_config
from carmon.mcp_server import MCPServer

PROJECT_ROOT = Path(__file__).resolve().parent.parent


RELIABLE_FACTS = {
    "complaint_count": 5,
    "recall_count": 1,
    "crash_complaints": 0,
    "fire_complaints": 0,
    "injuries": 0,
    "deaths": 0,
    "top_components": [["STEERING", 3], ["BRAKES", 2]],
    "recalls": [
        {
            "campaign": "24V001000",
            "component": "STEERING",
            "summary": "steering column may loosen",
            "consequence": "loss of control",
            "remedy": "inspect and replace",
            "report_date": "01/02/2024",
            "park_it": False,
            "park_outside": False,
        }
    ],
    "source": "nhtsa",
}

LOUD_FACTS = {
    "complaint_count": 500,
    "recall_count": 4,
    "crash_complaints": 10,
    "fire_complaints": 2,
    "injuries": 3,
    "deaths": 0,
    "top_components": [["ENGINE", 200], ["FUEL SYSTEM", 100]],
    "recalls": [],
    "source": "nhtsa",
}


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


def make_listing(vin="VIN0001", **overrides):
    listing = {
        "vin": vin,
        "year": 2022,
        "make": "Honda",
        "model": "Civic",
        "trim": "LX",
        "body_type": "Sedan",
        "fuel_type": "Gasoline",
        "mileage": 30000,
        "price_current": 18000,
        "price_first_seen": 19000,
        "dealer_name": "Example Honda",
        "dealer_city": "Springfield",
        "dealer_state": "TN",
        "distance_miles": 25.0,
        "cpo": True,
        "listing_url": "https://example.com/listing/vin0001",
        "score": 3.5,
        "score_breakdown": [{"label": "test", "value": 1.0, "detail": "detail"}],
        "source": "marketcheck",
    }
    listing.update(overrides)
    return listing


class MCPServerTestCase(unittest.TestCase):
    """Base class that builds a real MCPServer against a temp, seeded DB."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmpdir.name) / "carmon.db"

        conn = db.init_db(self.db_path)
        db.upsert_listing(conn, make_listing(vin="VIN0001", score=5.0), seen_date="2026-08-10")
        # Give VIN0001 a price drop on a later date.
        db.upsert_listing(
            conn,
            make_listing(vin="VIN0001", score=5.0, price_current=17000),
            seen_date="2026-08-17",
        )
        db.upsert_listing(
            conn,
            make_listing(vin="VIN0002", make="Toyota", model="Corolla", score=1.0, cpo=False),
            seen_date="2026-08-17",
        )
        # A third listing whose model/year has no cached NHTSA data at all, to prove
        # "unknown" is never treated as "bad" by the search filters.
        db.upsert_listing(
            conn,
            make_listing(vin="VIN0003", make="Kia", model="Forte", score=2.0, cpo=False),
            seen_date="2026-08-17",
        )
        # Seed cached NHTSA reliability: VIN0001 (Honda Civic 2022) is quiet, VIN0002
        # (Toyota Corolla 2022) is loud. VIN0003's model/year (Kia Forte 2022) is left
        # unseeded on purpose.
        db.save_reliability(conn, "Honda", "Civic", 2022, RELIABLE_FACTS)
        db.save_reliability(conn, "Toyota", "Corolla", 2022, LOUD_FACTS)
        db.save_mpg(conn, "Honda", "Civic", 2022, {"city_mpg": 33, "highway_mpg": 42, "combined_mpg": 36.5, "source": "fueleconomy.gov"})
        conn.close()

        config = load_config()  # real project config.json for search/scoring sections
        # Point paths.db at our temp DB using an ABSOLUTE path (relative paths
        # resolve against the project root, not the temp dir).
        config.data["paths"]["db"] = str(self.db_path.resolve())
        self.config = config
        self.server = MCPServer(config)

    def tearDown(self):
        self.server.close()
        self.tmpdir.cleanup()

    def call(self, method, params=None, request_id=1):
        message = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            message["params"] = params
        if request_id is not None:
            message["id"] = request_id
        return self.server.handle_request(message)

    def call_tool(self, name, arguments=None):
        return self.call("tools/call", {"name": name, "arguments": arguments or {}})


class TestInitializeAndProtocol(MCPServerTestCase):
    def test_initialize_shape(self):
        resp = self.call("initialize", {})
        self.assertEqual(resp["jsonrpc"], "2.0")
        self.assertEqual(resp["id"], 1)
        result = resp["result"]
        self.assertEqual(result["protocolVersion"], "2024-11-05")
        self.assertIn("tools", result["capabilities"])
        self.assertIn("resources", result["capabilities"])
        self.assertEqual(result["serverInfo"]["name"], "used-car-monitor")
        self.assertIn("version", result["serverInfo"])

    def test_notifications_initialized_returns_none(self):
        message = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
        self.assertIsNone(self.server.handle_request(message))

    def test_notification_without_id_generally_returns_none(self):
        message = {"jsonrpc": "2.0", "method": "ping"}
        self.assertIsNone(self.server.handle_request(message))

    def test_ping(self):
        resp = self.call("ping", {})
        self.assertEqual(resp["result"], {})

    def test_unknown_method_is_minus_32601(self):
        resp = self.call("totally/unknown", {})
        self.assertIn("error", resp)
        self.assertEqual(resp["error"]["code"], -32601)

    def test_shutdown(self):
        resp = self.call("shutdown", {})
        self.assertEqual(resp["result"], {})


class TestToolsList(MCPServerTestCase):
    def test_tools_list_has_all_twentyfive_with_schemas(self):
        resp = self.call("tools/list", {})
        tools = resp["result"]["tools"]
        names = {t["name"] for t in tools}
        expected = {
            "search_listings", "get_listing", "get_price_history", "top_listings",
            "new_listings", "price_drops", "get_stats", "get_quota_pace",
            "get_latest_digest", "explain_score", "score_hypothetical", "list_sources",
            "get_reliability", "refresh_reliability", "list_reliability",
            "appraise_car", "market_trend", "market_report", "best_deals", "list_comparables",
            "scraper_status", "scraper_events", "probe_scrapers", "run_scraper", "get_settings",
        }
        self.assertEqual(names, expected)
        self.assertEqual(len(tools), 25)
        for tool in tools:
            self.assertIn("inputSchema", tool, msg=tool["name"])
            self.assertEqual(tool["inputSchema"].get("type"), "object")
            self.assertIn("description", tool)
            self.assertTrue(tool["description"])


class TestResources(MCPServerTestCase):
    def test_resources_list(self):
        resp = self.call("resources/list", {})
        uris = {r["uri"] for r in resp["result"]["resources"]}
        self.assertIn("carmon://config", uris)
        self.assertIn("carmon://digest/latest", uris)

    def test_resources_read_config(self):
        resp = self.call("resources/read", {"uri": "carmon://config"})
        contents = resp["result"]["contents"]
        self.assertEqual(len(contents), 1)
        entry = contents[0]
        self.assertEqual(entry["uri"], "carmon://config")
        self.assertEqual(entry["mimeType"], "application/json")
        parsed = json.loads(entry["text"])
        self.assertIn("search", parsed)

    def test_resources_read_digest_latest_no_digest(self):
        resp = self.call("resources/read", {"uri": "carmon://digest/latest"})
        contents = resp["result"]["contents"]
        self.assertEqual(contents[0]["mimeType"], "text/markdown")
        # No digest module/data present in this fresh temp environment.
        self.assertIsInstance(contents[0]["text"], str)

    def test_resources_read_unknown_uri_is_invalid_params(self):
        resp = self.call("resources/read", {"uri": "carmon://nope"})
        self.assertIn("error", resp)
        self.assertEqual(resp["error"]["code"], -32602)


class TestToolsCall(MCPServerTestCase):
    def _tool_json(self, resp):
        self.assertNotIn("error", resp)
        result = resp["result"]
        self.assertFalse(result.get("isError"))
        text = result["content"][0]["text"]
        return json.loads(text)

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


class TestMalformedRequests(MCPServerTestCase):
    def test_missing_method_with_id_is_invalid_request(self):
        resp = self.server.handle_request({"jsonrpc": "2.0", "id": 1})
        self.assertIn("error", resp)
        self.assertEqual(resp["error"]["code"], -32600)

    def test_non_object_params_is_invalid_params(self):
        resp = self.server.handle_request(
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": "nope"}
        )
        self.assertIn("error", resp)
        self.assertEqual(resp["error"]["code"], -32602)


class TestEndToEndSubprocess(unittest.TestCase):
    """One real subprocess test: spawn the server, talk JSON-RPC over stdio."""

    def test_stdio_subprocess_initialize_and_tools_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "e2e.db"
            conn = db.init_db(db_path)
            conn.close()

            requests = [
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            ]
            input_data = "\n".join(json.dumps(r) for r in requests) + "\n"

            proc = subprocess.run(
                [sys.executable, "-m", "carmon.mcp_server", "--db", str(db_path)],
                input=input_data,
                capture_output=True,
                text=True,
                cwd=str(PROJECT_ROOT),
                timeout=30,
            )

            self.assertEqual(proc.returncode, 0, msg=f"stderr: {proc.stderr}")
            lines = [line for line in proc.stdout.splitlines() if line.strip()]
            self.assertEqual(len(lines), 2, msg=f"stdout was: {proc.stdout!r}")

            resp1 = json.loads(lines[0])
            resp2 = json.loads(lines[1])

            self.assertEqual(resp1["id"], 1)
            self.assertEqual(resp1["result"]["protocolVersion"], "2024-11-05")

            self.assertEqual(resp2["id"], 2)
            tool_names = {t["name"] for t in resp2["result"]["tools"]}
            self.assertEqual(len(tool_names), 25)


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

    def _tool_json(self, resp):
        self.assertNotIn("error", resp)
        result = resp["result"]
        self.assertFalse(result.get("isError"))
        text = result["content"][0]["text"]
        return json.loads(text)

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


class TestScraperAndSettingsTools(MCPServerTestCase):
    """scraper_status, scraper_events, probe_scrapers, run_scraper, get_settings.

    No test in this class may touch the network: scraper_status/scraper_events only ever
    read the local database, and probe_scrapers/run_scraper are exercised either against
    the disabled default config (which short-circuits before any adapter runs) or with
    carmon.pipeline.run_scrapers/probe_scrapers monkeypatched out.
    """

    def _tool_json(self, resp):
        self.assertNotIn("error", resp)
        result = resp["result"]
        self.assertFalse(result.get("isError"))
        text = result["content"][0]["text"]
        return json.loads(text)

    def test_scraper_status_shows_seeded_row_and_never_run_adapter(self):
        db.save_scraper_status(self.server.conn, "repairpal", {
            "status": "ok", "message": "fetched 2 model(s)",
            "pages_fetched": 2, "listings": 2,
        })
        resp = self.call_tool("scraper_status", {})
        payload = self._tool_json(resp)
        self.assertIn("scrapers_enabled", payload)
        self.assertIn("usage_today", payload)
        by_source = {row["source"]: row for row in payload["sources"]}
        self.assertIn("repairpal", by_source)
        self.assertEqual(by_source["repairpal"]["status"], "ok")
        self.assertEqual(by_source["repairpal"]["pages"], 2)
        self.assertEqual(by_source["repairpal"]["listings"], 2)
        # An adapter that has never run (no scraper_status row) must still appear.
        self.assertIn("carmax", by_source)
        self.assertEqual(by_source["carmax"]["status"], "never run")
        self.assertTrue(by_source["carmax"]["registered"])

    def test_scraper_status_filters_by_source(self):
        db.save_scraper_status(self.server.conn, "repairpal", {"status": "ok"})
        resp = self.call_tool("scraper_status", {"source": "repairpal"})
        payload = self._tool_json(resp)
        self.assertEqual([row["source"] for row in payload["sources"]], ["repairpal"])

    def test_scraper_status_unknown_source_is_tool_error(self):
        resp = self.call_tool("scraper_status", {"source": "not_a_real_source"})
        result = resp["result"]
        self.assertTrue(result["isError"])

    def test_scraper_events_returns_seeded_rows_and_respects_limit(self):
        conn = self.server.conn
        for i in range(3):
            db.record_scrape(conn, "repairpal", "page", f"https://repairpal.com/p{i}", 200, 1, "")
        db.record_scrape(conn, "carmax", "page", "https://carmax.com/p0", 200, 1, "")

        resp = self.call_tool("scraper_events", {"limit": 2, "source": "repairpal"})
        payload = self._tool_json(resp)
        self.assertEqual(payload["count"], 2)
        self.assertEqual(len(payload["events"]), 2)
        for row in payload["events"]:
            self.assertEqual(row["source"], "repairpal")

        resp_all = self.call_tool("scraper_events", {})
        payload_all = self._tool_json(resp_all)
        self.assertGreaterEqual(payload_all["count"], 4)

    def test_run_scraper_schema_defaults_dry_run_true(self):
        resp = self.call("tools/list", {})
        tools = {t["name"]: t for t in resp["result"]["tools"]}
        schema = tools["run_scraper"]["inputSchema"]
        self.assertIn("dry_run", schema["properties"])
        self.assertEqual(schema["properties"]["dry_run"]["default"], True)
        self.assertEqual(schema["properties"]["dry_run"]["type"], "boolean")

    def test_run_scraper_disabled_config_makes_no_network_calls(self):
        self.config.data.setdefault("scrapers", {})["enabled"] = False
        resp = self.call_tool("run_scraper", {})
        payload = self._tool_json(resp)
        self.assertFalse(payload["enabled"])
        self.assertIn("message", payload)

    def test_run_scraper_calls_pipeline_run_scrapers_with_args(self):
        called = {}

        def fake_run_scrapers(config, conn=None, sources=None, run_date=None, dry_run=False):
            called["sources"] = sources
            called["dry_run"] = dry_run
            return {"enabled": True, "sources": {}, "kept": 0, "new": 0, "skipped": []}

        with patch.object(pipelinemod, "run_scrapers", fake_run_scrapers):
            resp = self.call_tool("run_scraper", {"source": "repairpal", "dry_run": True})
        payload = self._tool_json(resp)
        self.assertEqual(called["sources"], ["repairpal"])
        self.assertTrue(called["dry_run"])
        self.assertTrue(payload["enabled"])

    def test_run_scraper_omitted_source_passes_none(self):
        called = {}

        def fake_run_scrapers(config, conn=None, sources=None, run_date=None, dry_run=False):
            called["sources"] = sources
            return {"enabled": True, "sources": {}, "kept": 0, "new": 0, "skipped": []}

        with patch.object(pipelinemod, "run_scrapers", fake_run_scrapers):
            self.call_tool("run_scraper", {})
        self.assertIsNone(called["sources"])

    def test_probe_scrapers_calls_pipeline_probe_scrapers(self):
        fake_results = [{"source": "repairpal", "name": "RepairPal", "status": "ok", "message": "ok"}]
        with patch.object(pipelinemod, "probe_scrapers", return_value=fake_results) as mock_probe:
            resp = self.call_tool("probe_scrapers", {})
        payload = self._tool_json(resp)
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["results"], fake_results)
        mock_probe.assert_called_once()

    def test_get_settings_returns_fields_and_masked_secrets_no_plaintext(self):
        fake_secret = "sUpErSecretVALUE998877"
        with patch.dict(os.environ, {"CARMON_API_TOKEN": fake_secret}):
            resp = self.call_tool("get_settings", {})
        payload = self._tool_json(resp)
        self.assertIn("fields", payload)
        self.assertIn("scrapers.enabled", payload["fields"])
        self.assertIn("secrets", payload)

        raw = json.dumps(payload)
        self.assertNotIn(fake_secret, raw)

        token_entry = next(s for s in payload["secrets"] if s["key"] == "CARMON_API_TOKEN")
        self.assertTrue(token_entry["set"])
        self.assertNotIn(fake_secret[:-4], token_entry["masked"])
        self.assertTrue(token_entry["masked"].endswith(fake_secret[-4:]))


if __name__ == "__main__":
    unittest.main()
