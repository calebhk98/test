"""Tests for the JSON-RPC/MCP framing itself: initialize/ping/shutdown, tools/list and
resources/* shape, malformed requests, and one real stdio subprocess round-trip.

Split out of the former test_mcp_server.py; tool-behavior tests live in
test_mcp_tools_core.py / test_mcp_tools_market.py / test_mcp_tools_scrapers.py -- see
mcp_server_test_support.py for the shared MCPServerTestCase base all of them use.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from carmon import db

from .mcp_server_test_support import MCPServerTestCase

PROJECT_ROOT = Path(__file__).resolve().parent.parent


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


if __name__ == "__main__":
    unittest.main()
