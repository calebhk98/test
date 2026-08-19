"""Tests for carmon.webapp: JSON API + HTML dashboard, exercised over real HTTP."""

from __future__ import annotations

import json
import os
import tempfile
import threading
import unittest
from datetime import date
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from carmon import config as config_module
from carmon import db
from carmon import quota
from carmon import settings as settings_module
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
        db.upsert_listing(
            conn,
            _make_listing("VIN000000000A001", city_mpg=31, highway_mpg=40, combined_mpg=34.8),
            seen_date="2026-08-10",
        )
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

        # -- cached NHTSA reliability + EPA MPG data (seeded directly, no network) --
        db.save_reliability(
            conn,
            "Toyota",
            "Corolla",
            2022,
            {
                "complaint_count": 42,
                "recall_count": 2,
                "crash_complaints": 3,
                "fire_complaints": 0,
                "injuries": 1,
                "deaths": 0,
                "top_components": [["ENGINE", 20], ["ELECTRICAL SYSTEM", 12]],
                "recalls": [
                    {
                        "campaign": "22V123000",
                        "component": "ENGINE",
                        "summary": "Engine may stall.",
                        "consequence": "Increases crash risk.",
                        "remedy": "Dealer will replace the engine control module.",
                        "report_date": "2022-05-01",
                        "park_it": False,
                        "park_outside": False,
                    }
                ],
                "source": "nhtsa",
            },
        )
        db.save_mpg(
            conn,
            "Toyota",
            "Corolla",
            2022,
            {"city_mpg": 31, "highway_mpg": 40, "combined_mpg": 34.8, "matched_name": "Corolla LE", "source": "fueleconomy.gov"},
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

    def test_reliability_detail_endpoint(self):
        data = self._get_json("/api/reliability/Toyota/Corolla/2022")
        self.assertEqual(data["complaint_count"], 42)
        self.assertEqual(data["recall_count"], 2)
        self.assertIn("nhtsa_url", data)
        self.assertIn("nhtsa.gov", data["nhtsa_url"])

    def test_reliability_detail_unknown_model_404(self):
        data = self._get_json("/api/reliability/Yugo/GV/1985", expect_status=404)
        self.assertIn("error", data)
        self.assertIn("carmon enrich", data["error"])

    def test_reliability_list_endpoint(self):
        data = self._get_json("/api/reliability")
        self.assertGreaterEqual(data["count"], 1)
        # model_reliability keys are stored lower-cased (see db._model_key); lookups by
        # /api/reliability/<make>/... are case-insensitive but this listing endpoint
        # reflects the table's own casing.
        makes = [m["make"] for m in data["models"]]
        self.assertIn("toyota", makes)

    def test_listing_detail_json_includes_nhtsa_fields(self):
        data = self._get_json("/api/listings/VIN000000000A001")
        self.assertEqual(data["complaint_count"], 42)
        self.assertEqual(data["recall_count"], 2)
        self.assertIn("nhtsa_vin_url", data)
        self.assertIn("nhtsa_model_url", data)

    def test_listings_max_complaints_filter(self):
        # Toyota Corolla has 42 cached complaints -- capping below that drops it, but the
        # Honda Civic (no cached NHTSA data at all) must survive since unknown != bad.
        data = self._get_json("/api/listings?max_complaints=10")
        vins = [item["vin"] for item in data["listings"]]
        self.assertNotIn("VIN000000000A001", vins)
        self.assertIn("VIN000000000B002", vins)
        self.assertEqual(data["filters"]["max_complaints"], 10)

    def test_listings_max_recalls_filter(self):
        data = self._get_json("/api/listings?max_recalls=0")
        vins = [item["vin"] for item in data["listings"]]
        self.assertNotIn("VIN000000000A001", vins)
        self.assertIn("VIN000000000B002", vins)

    def test_listings_max_complaints_invalid_400(self):
        data = self._get_json("/api/listings?max_complaints=abc", expect_status=400)
        self.assertIn("error", data)

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
        self.assertIn("<th>MPG</th>", text)
        self.assertIn("<th>NHTSA</th>", text)
        self.assertIn("34.8", text)  # combined_mpg for the Corolla row
        self.assertIn("42 / 2", text)  # complaints / recalls for the Corolla row
        self.assertIn("Model-years with NHTSA data", text)

    def test_listing_detail_html_has_score_breakdown(self):
        status, body = self._get("/listing/VIN000000000A001")
        self.assertEqual(status, 200)
        text = body.decode("utf-8")
        self.assertIn("Toyota Corolla is a preferred model", text)
        self.assertIn("Reliability (NHTSA)", text)
        self.assertIn("22V123000", text)  # recall campaign number
        self.assertIn("ENGINE", text)  # top complaint component
        self.assertIn("not adjusted for sales volume", text)  # volume caveat

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

    # -- quota pace -----------------------------------------------------
    def test_quota_endpoint_matches_pace_module(self):
        today = date.today()
        cap = int(self.config.api.get("monthly_call_cap", 500) or 500)
        conn = db.connect(self.config.db_path)
        for i in range(7):
            db.record_api_call(conn, "search", 200, note=f"call {i}")
        conn.close()

        expected = quota.pace(7, cap, today)

        data = self._get_json("/api/quota")
        self.assertEqual(data["used"], expected["used"])
        self.assertEqual(data["cap"], expected["cap"])
        self.assertEqual(data["pace_ratio"], expected["pace_ratio"])
        self.assertEqual(data["pace_label"], expected["pace_label"])
        self.assertEqual(data["expected_by_now"], expected["expected_by_now"])
        self.assertIn("summary", data)
        self.assertIn("bar", data)
        self.assertEqual(data["summary"], quota.summary_line(expected))
        self.assertEqual(data["bar"], quota.bar(expected))

    def test_stats_keeps_old_keys_and_gains_pace(self):
        today = date.today()
        cap = int(self.config.api.get("monthly_call_cap", 500) or 500)
        conn = db.connect(self.config.db_path)
        for i in range(3):
            db.record_api_call(conn, "search", 200, note=f"call {i}")
        conn.close()

        expected = quota.pace(3, cap, today)

        data = self._get_json("/api/stats")
        # old keys still present -- other tests/consumers depend on these
        for key in (
            "listings_total", "listings_active", "avg_price", "min_price", "best_score",
            "api_calls_this_month", "api_monthly_cap", "api_calls_remaining",
            "usage_by_month", "last_run",
        ):
            self.assertIn(key, data)
        self.assertIn("pace", data)
        self.assertEqual(data["pace"]["used"], expected["used"])
        self.assertEqual(data["pace"]["pace_ratio"], expected["pace_ratio"])
        self.assertEqual(data["pace"]["pace_label"], expected["pace_label"])

    def test_dashboard_shows_pace_tile(self):
        status, body = self._get("/")
        self.assertEqual(status, 200)
        text = body.decode("utf-8")
        self.assertIn("API pace", text)
        self.assertIn('class="tile pace', text)

    # -- demo data warnings -----------------------------------------------
    def test_no_demo_data_means_no_banner(self):
        health = self._get_json("/api/health")
        self.assertEqual(health["demo_listings"], 0)
        self.assertIsNone(health["demo_warning"])

        stats = self._get_json("/api/stats")
        self.assertEqual(stats["demo_listings"], 0)
        self.assertIsNone(stats["demo_warning"])

        status, body = self._get("/")
        self.assertEqual(status, 200)
        # the CSS rule for .demo-banner is always inlined -- check for the rendered
        # element itself, not the class name, which the stylesheet always contains.
        self.assertNotIn('<div class="demo-banner">', body.decode("utf-8"))

    # -- sort dropdown & caption --------------------------------------------
    def test_sort_dropdown_has_all_eight_options_including_last_seen(self):
        status, body = self._get("/")
        text = body.decode("utf-8")
        for key in (
            "score", "price", "price_desc", "mileage", "distance", "year",
            "first_seen", "last_seen",
        ):
            self.assertIn(f'value="{key}"', text)
        self.assertIn(">Last seen (newest first)<", text)

    def test_sort_caption_names_active_sort(self):
        status, body = self._get("/?sort=price_desc")
        text = body.decode("utf-8")
        self.assertIn("Sorted by price, high to low", text)

    def test_sort_caption_falls_back_to_score_for_bogus_sort(self):
        status, body = self._get("/?sort=bogus")
        self.assertEqual(status, 200)
        text = body.decode("utf-8")
        self.assertIn("Sorted by score, best first", text)
        self.assertNotIn(">bogus<", text)


class WebAppDemoDataTestCase(unittest.TestCase):
    """Demo listings (source='demo') must be impossible to mistake for real ones."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmpdir.name) / "carmon-demo-test.db"

        self.config = load_config()
        self.config.data["paths"] = dict(self.config.paths)
        self.config.data["paths"]["db"] = str(self.db_path)

        conn = db.init_db(self.config.db_path)
        db.upsert_listing(
            conn,
            _make_listing("DEMO0000000000A1", source="demo"),
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

    def _get(self, path: str):
        req = Request(self._url(path))
        with urlopen(req, timeout=5) as resp:
            return resp.status, resp.read()

    def _get_json(self, path: str):
        status, body = self._get(path)
        self.assertEqual(status, 200, msg=body)
        return json.loads(body)

    def test_health_reports_demo_listings(self):
        data = self._get_json("/api/health")
        self.assertEqual(data["demo_listings"], 1)
        self.assertIsNotNone(data["demo_warning"])
        self.assertIn("DEMO", data["demo_warning"])

    def test_stats_reports_demo_listings(self):
        data = self._get_json("/api/stats")
        self.assertEqual(data["demo_listings"], 1)
        self.assertIsNotNone(data["demo_warning"])

    def test_dashboard_shows_banner_and_badge(self):
        status, body = self._get("/")
        self.assertEqual(status, 200)
        text = body.decode("utf-8")
        self.assertIn("demo-banner", text)
        self.assertIn("DEMO DATA", text)
        self.assertIn('class="badge demo"', text)
        self.assertIn(">DEMO<", text)

    def test_listing_detail_shows_banner_and_badge(self):
        status, body = self._get("/listing/DEMO0000000000A1")
        self.assertEqual(status, 200)
        text = body.decode("utf-8")
        self.assertIn("demo-banner", text)
        self.assertIn('class="badge demo"', text)

    def test_sources_and_digest_pages_show_banner(self):
        for path in ("/sources", "/digest"):
            status, body = self._get(path)
            self.assertEqual(status, 200)
            self.assertIn("demo-banner", body.decode("utf-8"))


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


class MarketFeaturesTestCase(unittest.TestCase):
    """Market appraisal endpoints and pages: /api/market, /api/appraise, /api/deals,
    /market, /appraise, and the 'Versus the market' section on listing detail pages."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmpdir.name) / "carmon-market-test.db"

        self.config = load_config()
        self.config.data["paths"] = dict(self.config.paths)
        self.config.data["paths"]["db"] = str(self.db_path)

        conn = db.init_db(self.config.db_path)

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
                _make_listing(vin, make="Toyota", model="Camry", year=year, mileage=mileage, price_current=price),
                seen_date="2026-07-01",
            )
        # Re-seen a few of them a month later, with a couple of price cuts, so the trend
        # table has more than one month and price_cut_stats has something to report.
        for i in (0, 1, 2):
            vin = self.camry_vins[i]
            db.upsert_listing(
                conn,
                _make_listing(vin, make="Toyota", model="Camry", year=2018 + (i % 5),
                              mileage=8000 + i * 6000 + 500, price_current=25000 - i * 100),
                seen_date="2026-08-10",
            )

        # A thin-data car: unique make/model, nothing else remotely like it in the DB, so
        # its appraisal must fall back to "every tracked listing" and say so.
        self.thin_vin = "VINYUGO000000001"
        db.upsert_listing(
            conn,
            _make_listing(self.thin_vin, make="Yugo", model="GV", year=1985, mileage=90000, price_current=2000),
            seen_date="2026-08-01",
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

    def _get(self, path: str, expect_status: int = 200):
        req = Request(self._url(path))
        try:
            with urlopen(req, timeout=5) as resp:
                return resp.status, resp.read()
        except HTTPError as exc:
            return exc.code, exc.read()

    def _get_json(self, path: str, expect_status: int = 200):
        status, body = self._get(path, expect_status=expect_status)
        self.assertEqual(status, expect_status, msg=body)
        return json.loads(body)

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


class ScrapersAndSettingsTestCase(unittest.TestCase):
    """/api/scrapers*, /api/settings*, /scrapers and /settings -- and the write-security
    checks (auth, writes_allowed, intent marker, same-origin) shared by every write
    endpoint. Both carmon.settings.PROJECT_ROOT (config-history backups, .env writes) and
    carmon.config.DEFAULT_ENV_PATH (what a bare load_env() call reads) are patched to a
    tempdir for the lifetime of each test, so nothing here ever touches the real project's
    config.json, .env or data/config-history."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp_root = Path(self._tmpdir.name)
        self.db_path = self.tmp_root / "carmon-test.db"
        self.config_path = self.tmp_root / "config.json"

        self.config = load_config()
        self.config.data["paths"] = dict(self.config.paths)
        self.config.data["paths"]["db"] = str(self.db_path)
        self.config.path = self.config_path
        self.config_path.write_text(json.dumps(self.config.data, indent=2) + "\n", encoding="utf-8")

        self._orig_settings_root = settings_module.PROJECT_ROOT
        self._orig_env_path = config_module.DEFAULT_ENV_PATH
        settings_module.PROJECT_ROOT = self.tmp_root
        config_module.DEFAULT_ENV_PATH = self.tmp_root / ".env"

        db.init_db(self.config.db_path).close()

        self.server = webapp.create_server(self.config, host="127.0.0.1", port=0)
        self.host, self.port = self.server.server_address[:2]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        settings_module.PROJECT_ROOT = self._orig_settings_root
        config_module.DEFAULT_ENV_PATH = self._orig_env_path
        self._tmpdir.cleanup()

    def _url(self, path: str) -> str:
        return f"http://{self.host}:{self.port}{path}"

    def _get(self, path: str, headers=None):
        req = Request(self._url(path), headers=headers or {})
        try:
            with urlopen(req, timeout=5) as resp:
                return resp.status, resp.read()
        except HTTPError as exc:
            return exc.code, exc.read()

    def _get_json(self, path: str, expect_status: int = 200):
        status, body = self._get(path)
        self.assertEqual(status, expect_status, msg=body)
        return json.loads(body)

    def _post(self, path: str, json_body=None, headers=None, form=None):
        headers = dict(headers or {})
        if form is not None:
            data = urlencode(form).encode("utf-8")
            headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
        else:
            data = json.dumps(json_body if json_body is not None else {}).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")
        req = Request(self._url(path), data=data, headers=headers, method="POST")
        try:
            with urlopen(req, timeout=5) as resp:
                return resp.status, resp.read()
        except HTTPError as exc:
            return exc.code, exc.read()

    def _config_on_disk(self):
        return json.loads(self.config_path.read_text(encoding="utf-8"))

    # -- GET /api/scrapers --------------------------------------------------
    def test_api_scrapers_lists_adapters_including_no_history(self):
        data = self._get_json("/api/scrapers")
        self.assertIn("adapters", data)
        self.assertIn("usage_today", data)
        self.assertIn("by_source", data)
        self.assertIn("limits", data)
        keys = [a["key"] for a in data["adapters"]]
        self.assertIn("carmax", keys)  # registered adapter, never run -- must still appear
        carmax = next(a for a in data["adapters"] if a["key"] == "carmax")
        self.assertEqual(carmax["status"], "never run")
        self.assertFalse(carmax["enabled"])

    def test_api_scrapers_events_endpoint(self):
        data = self._get_json("/api/scrapers/events?limit=5")
        self.assertIn("count", data)
        self.assertIsInstance(data["events"], list)

    # -- POST /api/scrapers/toggle -------------------------------------------
    def test_scrapers_toggle_changes_config_get_does_not(self):
        before = self._config_on_disk()["scrapers"]["sources"]["carmax"]
        self.assertFalse(before)

        self._get("/api/scrapers")  # a GET must never mutate
        self.assertEqual(self._config_on_disk()["scrapers"]["sources"]["carmax"], before)

        status, body = self._post(
            "/api/scrapers/toggle", {"source": "carmax", "enabled": True},
            headers={"X-Carmon-Write": "1"},
        )
        self.assertEqual(status, 200, msg=body)
        self.assertTrue(self._config_on_disk()["scrapers"]["sources"]["carmax"])

    def test_scrapers_toggle_master_switch_with_no_source(self):
        status, body = self._post(
            "/api/scrapers/toggle", {"enabled": True}, headers={"X-Carmon-Write": "1"},
        )
        self.assertEqual(status, 200, msg=body)
        self.assertTrue(self._config_on_disk()["scrapers"]["enabled"])

    # -- POST /api/settings --------------------------------------------------
    def test_settings_post_applies_valid_change(self):
        status, body = self._post(
            "/api/settings", {"changes": {"search.zip": "37211"}}, headers={"X-Carmon-Write": "1"},
        )
        self.assertEqual(status, 200, msg=body)
        data = json.loads(body)
        self.assertEqual(data["applied"]["search.zip"], "37211")
        self.assertEqual(self._config_on_disk()["search"]["zip"], "37211")

    def test_settings_post_bad_type_400_and_unchanged(self):
        before = self._config_on_disk()["search"]["radius_miles"]
        status, body = self._post(
            "/api/settings", {"changes": {"search.radius_miles": "far"}}, headers={"X-Carmon-Write": "1"},
        )
        self.assertEqual(status, 400, msg=body)
        self.assertIn("error", json.loads(body))
        self.assertEqual(self._config_on_disk()["search"]["radius_miles"], before)

    def test_settings_post_unknown_key_400(self):
        status, body = self._post(
            "/api/settings", {"changes": {"totally.bogus": "x"}}, headers={"X-Carmon-Write": "1"},
        )
        self.assertEqual(status, 400, msg=body)

    def test_settings_post_paths_db_400(self):
        before = self._config_on_disk()["paths"]["db"]
        status, body = self._post(
            "/api/settings", {"changes": {"paths.db": "/somewhere/else.db"}}, headers={"X-Carmon-Write": "1"},
        )
        self.assertEqual(status, 400, msg=body)
        self.assertEqual(self._config_on_disk()["paths"]["db"], before)

    # -- POST /api/settings/secrets ------------------------------------------
    def test_settings_secrets_post_unknown_key_400(self):
        status, body = self._post(
            "/api/settings/secrets", {"changes": {"NOT_A_REAL_SECRET": "x"}}, headers={"X-Carmon-Write": "1"},
        )
        self.assertEqual(status, 400, msg=body)

    def test_settings_secrets_post_sets_and_never_echoes_value(self):
        status, body = self._post(
            "/api/settings/secrets",
            {"changes": {"MARKETCHECK_API_KEY": "supersecretvalue123"}},
            headers={"X-Carmon-Write": "1"},
        )
        self.assertEqual(status, 200, msg=body)
        self.assertNotIn(b"supersecretvalue123", body)
        env_text = (self.tmp_root / ".env").read_text(encoding="utf-8")
        self.assertIn("supersecretvalue123", env_text)  # really was written, just not echoed

    # -- security: write checks apply to every write endpoint ----------------
    def test_write_without_intent_marker_403(self):
        status, body = self._post("/api/scrapers/toggle", {"source": "carmax", "enabled": True})
        self.assertEqual(status, 403, msg=body)
        self.assertFalse(self._config_on_disk()["scrapers"]["sources"]["carmax"])

    def test_write_with_cross_origin_403(self):
        status, body = self._post(
            "/api/scrapers/toggle", {"source": "carmax", "enabled": True},
            headers={"X-Carmon-Write": "1", "Origin": "http://evil.example"},
        )
        self.assertEqual(status, 403, msg=body)
        self.assertFalse(self._config_on_disk()["scrapers"]["sources"]["carmax"])

    def test_write_same_origin_is_accepted(self):
        origin = f"http://{self.host}:{self.port}"
        status, body = self._post(
            "/api/scrapers/toggle", {"source": "carmax", "enabled": True},
            headers={"X-Carmon-Write": "1", "Origin": origin},
        )
        self.assertEqual(status, 200, msg=body)

    def test_write_without_token_401_when_token_configured(self):
        env_backup = os.environ.get("CARMON_API_TOKEN")
        os.environ["CARMON_API_TOKEN"] = "s3cr3t-write-token"
        try:
            status, body = self._post(
                "/api/scrapers/toggle", {"source": "carmax", "enabled": True},
                headers={"X-Carmon-Write": "1"},
            )
            self.assertEqual(status, 401, msg=body)
            self.assertFalse(self._config_on_disk()["scrapers"]["sources"]["carmax"])

            status, body = self._post(
                "/api/scrapers/toggle", {"source": "carmax", "enabled": True},
                headers={"X-Carmon-Write": "1", "Authorization": "Bearer s3cr3t-write-token"},
            )
            self.assertEqual(status, 200, msg=body)
        finally:
            if env_backup is None:
                os.environ.pop("CARMON_API_TOKEN", None)
            else:
                os.environ["CARMON_API_TOKEN"] = env_backup

    def test_get_settings_never_leaks_secret_value(self):
        status, body = self._post(
            "/api/settings/secrets",
            {"changes": {"MARKETCHECK_API_KEY": "supersecretvalue123"}},
            headers={"X-Carmon-Write": "1"},
        )
        self.assertEqual(status, 200, msg=body)

        data = self._get_json("/api/settings")
        secret = next(s for s in data["secrets"] if s["key"] == "MARKETCHECK_API_KEY")
        self.assertTrue(secret["set"])
        self.assertTrue(secret["masked"].endswith("e123"))
        self.assertNotIn("supersecretvalue123", json.dumps(data))
        self.assertIn("writable", data)
        self.assertIn("reason", data)

    def test_get_on_write_endpoint_404_never_mutates(self):
        before = self._config_on_disk()["scrapers"]["sources"]["carmax"]
        status, body = self._get("/api/scrapers/toggle")
        self.assertIn(status, (404, 405))
        self.assertEqual(self._config_on_disk()["scrapers"]["sources"]["carmax"], before)

        status, body = self._get("/api/settings", headers={})  # GET is the read endpoint, sanity check
        self.assertEqual(status, 200)

    def test_form_encoded_write_is_accepted(self):
        status, body = self._post(
            "/api/scrapers/toggle",
            form={"source": "carmax", "enabled": "1", "confirm": "1"},
        )
        self.assertEqual(status, 200, msg=body)
        self.assertTrue(self._config_on_disk()["scrapers"]["sources"]["carmax"])

    # -- HTML pages -----------------------------------------------------
    def test_scrapers_page_renders_status_badge_and_caveat(self):
        status, body = self._get("/scrapers")
        self.assertEqual(status, 200)
        text = body.decode("utf-8")
        self.assertIn("never run", text)
        self.assertIn('class="badge neutral"', text)
        self.assertIn("blocked", text.lower())
        self.assertIn("not a bug to fix", text)

    def test_settings_page_renders_and_shows_masked_secret(self):
        status, body = self._post(
            "/api/settings/secrets", {"changes": {"MARKETCHECK_API_KEY": "abcd987654"}},
            headers={"X-Carmon-Write": "1"},
        )
        self.assertEqual(status, 200, msg=body)

        status, body = self._get("/settings")
        self.assertEqual(status, 200)
        text = body.decode("utf-8")
        self.assertNotIn("abcd987654", text)
        self.assertIn("7654", text)
        self.assertIn("search", text)

    def test_settings_html_form_round_trip_bool_number_and_list(self):
        fields = self._get_json("/api/settings")["fields"]
        form_body = {"confirm": "1"}
        for dotted, info in fields.items():
            form_body[f"present.{dotted}"] = "1"
            if info["type"] == "bool":
                if dotted != "search.include_certified_search":  # leave this one unchecked
                    if info["value"]:
                        form_body[dotted] = "1"
            elif info["type"] == "list":
                if isinstance(info["value"], list) and all(
                    isinstance(v, (str, int, float, bool)) for v in info["value"]
                ):
                    form_body[dotted] = ", ".join(str(v) for v in info["value"])
                else:
                    del form_body[f"present.{dotted}"]  # complex list: not editable via form
            else:
                form_body[dotted] = str(info["value"])

        status, body = self._post("/settings", form=form_body)
        self.assertEqual(status, 200, msg=body)
        text = body.decode("utf-8")
        self.assertIn("Saved", text)

        after = self._config_on_disk()
        self.assertFalse(after["search"]["include_certified_search"])  # unchecked -> false
        self.assertEqual(after["search"]["radius_miles"], 100)  # number round-tripped
        self.assertEqual(
            after["search"]["exclude_body_types"],
            ["Pickup", "Truck", "Van", "Minivan", "Cargo Van", "Chassis", "Convertible"],
        )  # comma-joined list round-tripped back into a list

    def test_nav_links_to_scrapers_and_settings(self):
        status, body = self._get("/")
        text = body.decode("utf-8")
        self.assertIn('href="/scrapers"', text)
        self.assertIn('href="/settings"', text)


if __name__ == "__main__":
    unittest.main()
