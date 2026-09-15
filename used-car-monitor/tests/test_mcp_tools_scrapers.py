"""Scraper and settings MCP tools: scraper_status, scraper_events, probe_scrapers,
run_scraper, get_settings.

Split out of the former test_mcp_server.py -- see mcp_server_test_support.py for the
shared MCPServerTestCase base this and the other test_mcp_*.py modules use.
"""

from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

from carmon import db
from carmon import pipeline as pipelinemod

from .mcp_server_test_support import MCPServerTestCase


class TestScraperAndSettingsTools(MCPServerTestCase):
    """scraper_status, scraper_events, probe_scrapers, run_scraper, get_settings.

    No test in this class may touch the network: scraper_status/scraper_events only ever
    read the local database, and probe_scrapers/run_scraper are exercised either against
    the disabled default config (which short-circuits before any adapter runs) or with
    carmon.pipeline.run_scrapers/probe_scrapers monkeypatched out.
    """

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
