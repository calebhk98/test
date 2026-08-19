"""/api/scrapers*, /api/settings*, /scrapers and /settings -- and the write-security
checks (auth, writes_allowed, intent marker, same-origin) shared by every write
endpoint.

Split out of the former test_webapp.py -- see webapp_test_support.py for the shared
server scaffolding this and the other test_webapp_*.py modules use.
"""

from __future__ import annotations

import json
import os
import unittest

from carmon import config as config_module
from carmon import db
from carmon import settings as settings_module

from .webapp_test_support import LiveServerCase, temp_db_config


class ScrapersAndSettingsTestCase(LiveServerCase, unittest.TestCase):
    """/api/scrapers*, /api/settings*, /scrapers and /settings -- and the write-security
    checks (auth, writes_allowed, intent marker, same-origin) shared by every write
    endpoint. Both carmon.settings.PROJECT_ROOT (config-history backups, .env writes) and
    carmon.config.DEFAULT_ENV_PATH (what a bare load_env() call reads) are patched to a
    tempdir for the lifetime of each test, so nothing here ever touches the real project's
    config.json, .env or data/config-history."""

    def setUp(self) -> None:
        super().setUp()
        self.db_path = self.tmp_root / "carmon-test.db"
        self.config_path = self.tmp_root / "config.json"

        config = temp_db_config(self.db_path)
        config.path = self.config_path
        self.config_path.write_text(json.dumps(config.data, indent=2) + "\n", encoding="utf-8")

        self._orig_settings_root = settings_module.PROJECT_ROOT
        self._orig_env_path = config_module.DEFAULT_ENV_PATH
        settings_module.PROJECT_ROOT = self.tmp_root
        config_module.DEFAULT_ENV_PATH = self.tmp_root / ".env"

        db.init_db(self.db_path).close()

        self._start_server(config)

    def tearDown(self) -> None:
        self._stop_server()
        settings_module.PROJECT_ROOT = self._orig_settings_root
        config_module.DEFAULT_ENV_PATH = self._orig_env_path
        self._tmpdir.cleanup()

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

    def test_settings_page_shows_secret_help_and_signup_link(self):
        status, body = self._get("/settings")
        self.assertEqual(status, 200)
        text = body.decode("utf-8")
        # The MarketCheck key is the one secret that is actually required, so its signup
        # link -- the whole point of "never open .env by hand" -- has to be right there.
        self.assertIn('href="https://www.marketcheck.com/apis"', text)
        self.assertIn('target="_blank"', text)
        self.assertIn('rel="noopener noreferrer"', text)
        # The one-line "how to get it" text should render too, not just the link.
        how_text = settings_module.SECRET_META["MARKETCHECK_API_KEY"]["how"]
        self.assertIn(how_text.split(".")[0], text)

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
