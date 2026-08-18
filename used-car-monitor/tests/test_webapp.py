"""Tests for carmon.webapp: JSON API + HTML dashboard, exercised over real HTTP."""

from __future__ import annotations

import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from carmon import db
from carmon import webapp
from carmon.config import load_config


def _make_listing(vin: str, **overrides):
    listing = {
        "vin": vin,
        "year": 2022,
        "make": "Toyota",
        "model": "Corolla",
        "trim": "LE",
        "mileage": 25000,
        "price_current": 18500,
        "dealer_name": "Test Toyota",
        "dealer_city": "Nashville",
        "dealer_state": "TN",
        "distance_miles": 42.0,
        "cpo": True,
        "listing_url": "https://example.com/listing/" + vin,
        "score": 3.5,
        "score_breakdown": [
            {"label": "preferred_model", "value": 2.0, "detail": "Toyota Corolla is a preferred model"},
            {"label": "cpo", "value": 2.0, "detail": "Certified pre-owned"},
            {"label": "distance", "value": -0.5, "detail": "42.0 miles (50 free)"},
        ],
        "body_type": "Sedan",
        "fuel_type": "Gasoline",
    }
    listing.update(overrides)
    return listing


class WebAppTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmpdir.name) / "carmon-test.db"

        self.config = load_config()
        # Point paths.db at an ABSOLUTE temp path -- Config.db_path resolves
        # relative paths against the project root, so a bare filename would
        # not land in our tempdir.
        self.config.data["paths"] = dict(self.config.paths)
        self.config.data["paths"]["db"] = str(self.db_path)
        self.assertTrue(self.config.db_path.is_absolute())
        self.assertEqual(self.config.db_path, self.db_path)

        conn = db.init_db(self.config.db_path)
        db.upsert_listing(conn, _make_listing("VIN000000000A001"), seen_date="2026-08-10")
        db.upsert_listing(conn, _make_listing("VIN000000000A001", price_current=17999), seen_date="2026-08-17")
        db.upsert_listing(
            conn,
            _make_listing(
                "VIN000000000B002",
                make="Honda",
                model="Civic",
                score=1.0,
                score_breakdown=[{"label": "preferred_model", "value": 2.0, "detail": "Honda Civic"}],
            ),
            seen_date="2026-08-18",
        )
        conn.close()

        self.server = webapp.create_server(self.config, host="127.0.0.1", port=0)
        self.host, self.port = self.server.server_address[:2]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self._tmpdir.cleanup()

    def _url(self, path: str) -> str:
        return f"http://{self.host}:{self.port}{path}"

    def _get(self, path: str, headers=None, expect_status: int = 200):
        req = Request(self._url(path), headers=headers or {})
        try:
            with urlopen(req, timeout=5) as resp:
                body = resp.read()
                return resp.status, body
        except HTTPError as exc:
            return exc.code, exc.read()

    def _get_json(self, path: str, headers=None, expect_status: int = 200):
        status, body = self._get(path, headers=headers)
        self.assertEqual(status, expect_status, msg=body)
        return json.loads(body)

    # -- JSON API -----------------------------------------------------
    def test_health(self):
        data = self._get_json("/api/health")
        self.assertEqual(data["status"], "ok")
        self.assertIn("version", data)
        self.assertEqual(data["listings"], 2)

    def test_stats(self):
        data = self._get_json("/api/stats")
        self.assertEqual(data["listings_active"], 2)
        self.assertIn("api_calls_this_month", data)
        self.assertIn("api_monthly_cap", data)

    def test_listings_filtering_and_limit(self):
        data = self._get_json("/api/listings?make=Toyota")
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["listings"][0]["vin"], "VIN000000000A001")

        data_all = self._get_json("/api/listings?limit=1")
        self.assertEqual(len(data_all["listings"]), 1)
        self.assertEqual(data_all["limit"], 1)

    def test_listing_detail_includes_history_and_cross_shop(self):
        data = self._get_json("/api/listings/VIN000000000A001")
        self.assertEqual(data["vin"], "VIN000000000A001")
        self.assertIn("price_history", data)
        self.assertGreaterEqual(len(data["price_history"]), 2)
        self.assertIn("cross_shop", data)
        self.assertTrue(len(data["cross_shop"]) > 0)

    def test_listing_history_endpoint(self):
        data = self._get_json("/api/listings/VIN000000000A001/history")
        self.assertEqual(data["vin"], "VIN000000000A001")
        self.assertGreaterEqual(len(data["history"]), 2)

    def test_unknown_vin_404(self):
        data = self._get_json("/api/listings/NOSUCHVIN", expect_status=404)
        self.assertIn("error", data)

    def test_invalid_limit_400(self):
        data = self._get_json("/api/listings?limit=abc", expect_status=400)
        self.assertIn("error", data)

    def test_new_and_price_drops_and_top(self):
        new_data = self._get_json("/api/new?days=1&limit=25")
        self.assertIsInstance(new_data["listings"], list)
        self.assertEqual(new_data["count"], len(new_data["listings"]))

        drops = self._get_json("/api/price-drops?days=30&limit=25")
        self.assertTrue(any(item["vin"] == "VIN000000000A001" for item in drops["listings"]))

        top = self._get_json("/api/top?limit=5")
        self.assertEqual(top["listings"][0]["vin"], "VIN000000000A001")
        self.assertEqual(top["count"], len(top["listings"]))

    def test_sources_and_config_and_runs(self):
        sources = self._get_json("/api/sources")
        self.assertIn("categories", sources)

        cfg = self._get_json("/api/config")
        self.assertIn("search", cfg)

        runs = self._get_json("/api/runs?limit=10")
        self.assertIsInstance(runs["runs"], list)

    def test_digest_latest_when_absent(self):
        data = self._get_json("/api/digest/latest")
        self.assertIn("path", data)
        self.assertIn("markdown", data)

    def test_cors_and_options_preflight(self):
        status, body = self._get("/api/health")
        self.assertEqual(status, 200)
        req = Request(self._url("/api/health"), method="OPTIONS")
        with urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 204)
            self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), "*")

    def test_unknown_api_path_404_json(self):
        status, body = self._get("/api/does-not-exist")
        self.assertEqual(status, 404)
        data = json.loads(body)
        self.assertIn("error", data)

    # -- HTML pages -----------------------------------------------------
    def test_dashboard_html(self):
        status, body = self._get("/")
        self.assertEqual(status, 200)
        text = body.decode("utf-8")
        self.assertIn("VIN000000000A001", text)
        self.assertIn("Toyota", text)

    def test_listing_detail_html_has_score_breakdown(self):
        status, body = self._get("/listing/VIN000000000A001")
        self.assertEqual(status, 200)
        text = body.decode("utf-8")
        self.assertIn("Toyota Corolla is a preferred model", text)

    def test_listing_detail_html_unknown_vin_404(self):
        status, body = self._get("/listing/NOSUCHVIN")
        self.assertEqual(status, 404)

    def test_sources_page(self):
        status, body = self._get("/sources")
        self.assertEqual(status, 200)
        text = body.decode("utf-8")
        self.assertIn("manual", text.lower())

    def test_digest_page(self):
        status, body = self._get("/digest")
        self.assertEqual(status, 200)

    def test_unknown_html_path_404(self):
        status, body = self._get("/no-such-page")
        self.assertEqual(status, 404)


class WebAppAuthTestCase(unittest.TestCase):
    """Bearer-token enforcement when CARMON_API_TOKEN is configured."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmpdir.name) / "carmon-auth-test.db"

        self.config = load_config()
        self.config.data["paths"] = dict(self.config.paths)
        self.config.data["paths"]["db"] = str(self.db_path)

        db.init_db(self.config.db_path).close()

        self.token = "s3cr3t-token"
        self._env_patch = os.environ.get("CARMON_API_TOKEN")
        os.environ["CARMON_API_TOKEN"] = self.token

        self.server = webapp.create_server(self.config, host="127.0.0.1", port=0)
        self.host, self.port = self.server.server_address[:2]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self._tmpdir.cleanup()
        if self._env_patch is None:
            os.environ.pop("CARMON_API_TOKEN", None)
        else:
            os.environ["CARMON_API_TOKEN"] = self._env_patch

    def _url(self, path: str) -> str:
        return f"http://{self.host}:{self.port}{path}"

    def test_health_stays_public(self):
        with urlopen(self._url("/api/health"), timeout=5) as resp:
            self.assertEqual(resp.status, 200)

    def test_unauthenticated_request_rejected(self):
        with self.assertRaises(HTTPError) as ctx:
            urlopen(self._url("/api/listings"), timeout=5)
        self.assertEqual(ctx.exception.code, 401)

    def test_wrong_token_rejected(self):
        req = Request(self._url("/api/listings"), headers={"Authorization": "Bearer wrong"})
        with self.assertRaises(HTTPError) as ctx:
            urlopen(req, timeout=5)
        self.assertEqual(ctx.exception.code, 401)

    def test_correct_token_accepted(self):
        req = Request(self._url("/api/listings"), headers={"Authorization": f"Bearer {self.token}"})
        with urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)


if __name__ == "__main__":
    unittest.main()
