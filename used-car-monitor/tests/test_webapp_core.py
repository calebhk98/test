"""Core carmon.webapp tests: the JSON API + HTML dashboard's everyday paths, demo-data
warnings, and bearer-token auth. Split out of the former test_webapp.py; market/appraise
tests live in test_webapp_market.py and scrapers/settings tests in
test_webapp_scrapers_settings.py -- see webapp_test_support.py for the shared server
scaffolding all three modules use.
"""

from __future__ import annotations

import json
import os
import unittest
from datetime import date
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from carmon import db
from carmon import quota

from .webapp_test_support import LiveServerCase, make_listing, temp_db_config


class WebAppTestCase(LiveServerCase, unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.db_path = self.tmp_root / "carmon-test.db"
        config = temp_db_config(self.db_path)
        # Point paths.db at an ABSOLUTE temp path -- Config.db_path resolves
        # relative paths against the project root, so a bare filename would
        # not land in our tempdir.
        self.assertTrue(config.db_path.is_absolute())
        self.assertEqual(config.db_path, self.db_path)

        conn = db.init_db(self.db_path)
        db.upsert_listing(
            conn,
            make_listing("VIN000000000A001", city_mpg=31, highway_mpg=40, combined_mpg=34.8),
            seen_date="2026-08-10",
        )
        db.upsert_listing(conn, make_listing("VIN000000000A001", price_current=17999), seen_date="2026-08-17")
        db.upsert_listing(
            conn,
            make_listing(
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

        self._start_server(config)

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


class WebAppDemoDataTestCase(LiveServerCase, unittest.TestCase):
    """Demo listings (source='demo') must be impossible to mistake for real ones."""

    def setUp(self) -> None:
        super().setUp()
        self.db_path = self.tmp_root / "carmon-demo-test.db"
        config = temp_db_config(self.db_path)

        conn = db.init_db(self.db_path)
        db.upsert_listing(
            conn,
            make_listing("DEMO0000000000A1", source="demo"),
            seen_date="2026-08-18",
        )
        conn.close()

        self._start_server(config)

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


class WebAppAuthTestCase(LiveServerCase, unittest.TestCase):
    """Bearer-token enforcement when CARMON_API_TOKEN is configured."""

    def setUp(self) -> None:
        super().setUp()
        self.db_path = self.tmp_root / "carmon-auth-test.db"
        config = temp_db_config(self.db_path)
        db.init_db(self.db_path).close()

        self.token = "s3cr3t-token"
        self._env_patch = os.environ.get("CARMON_API_TOKEN")
        os.environ["CARMON_API_TOKEN"] = self.token

        self._start_server(config)

    def tearDown(self) -> None:
        self._stop_server()
        self._tmpdir.cleanup()
        if self._env_patch is None:
            os.environ.pop("CARMON_API_TOKEN", None)
        else:
            os.environ["CARMON_API_TOKEN"] = self._env_patch

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
