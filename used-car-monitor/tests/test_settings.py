"""Editing config.json and .env safely — the rules behind the settings page."""

import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from carmon import settings
from carmon.config import Config, load_config


class WriteAuthorisationTests(unittest.TestCase):
    def test_loopback_may_write(self):
        for host in ("127.0.0.1", "localhost", "::1", "127.0.0.5"):
            allowed, _ = settings.writes_allowed(host, None)
            self.assertTrue(allowed, host)

    def test_public_bind_without_a_token_may_not_write(self):
        allowed, reason = settings.writes_allowed("0.0.0.0", None)
        self.assertFalse(allowed)
        self.assertIn("CARMON_API_TOKEN", reason)

    def test_public_bind_with_a_token_may_write(self):
        allowed, _ = settings.writes_allowed("192.168.1.20", "a-token")
        self.assertTrue(allowed)

    def test_unknown_host_is_treated_as_public(self):
        self.assertFalse(settings.writes_allowed("example.test", None)[0])


class EditableSettingsTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config()

    def test_common_sections_are_editable(self):
        fields = settings.editable_settings(self.config)
        for key in ("search.zip", "search.price_max", "scrapers.enabled",
                    "api.monthly_call_cap", "scoring.mode"):
            self.assertIn(key, fields)

    def test_paths_are_not_editable_over_http(self):
        fields = settings.editable_settings(self.config)
        self.assertFalse([key for key in fields if key.startswith("paths.")])

    def test_types_are_reported_for_form_rendering(self):
        fields = settings.editable_settings(self.config)
        self.assertEqual(fields["scrapers.enabled"]["type"], "bool")
        self.assertEqual(fields["search.price_max"]["type"], "number")
        self.assertEqual(fields["search.zip"]["type"], "string")
        self.assertEqual(fields["search.body_types"]["type"], "list")


class ApplyChangesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        source = json.loads((Path(__file__).resolve().parent.parent / "config.json").read_text())
        self.path = self.tmp / "config.json"
        self.path.write_text(json.dumps(source, indent=2), encoding="utf-8")
        self.config = Config(json.loads(self.path.read_text()), self.path)
        self._root = settings.PROJECT_ROOT
        settings.PROJECT_ROOT = self.tmp

    def tearDown(self):
        settings.PROJECT_ROOT = self._root

    def _reload(self):
        return json.loads(self.path.read_text())

    def test_a_valid_change_is_written_to_disk(self):
        result = settings.apply_changes(self.config, {"search.zip": "37211"})
        self.assertEqual(result["applied"]["search.zip"], "37211")
        self.assertEqual(self._reload()["search"]["zip"], "37211")
        self.assertEqual(self.config.data["search"]["zip"], "37211", "the live config must update too")

    def test_numbers_keep_their_type(self):
        settings.apply_changes(self.config, {"search.price_max": 15000})
        self.assertEqual(self._reload()["search"]["price_max"], 15000)
        settings.apply_changes(self.config, {"market.recency_half_life_days": 30})
        self.assertEqual(self._reload()["market"]["recency_half_life_days"], 30)

    def test_booleans_toggle(self):
        settings.apply_changes(self.config, {"scrapers.sources.repairpal": True})
        self.assertTrue(self._reload()["scrapers"]["sources"]["repairpal"])

    def test_a_type_change_is_rejected(self):
        with self.assertRaises(settings.SettingsError) as ctx:
            settings.apply_changes(self.config, {"search.radius_miles": "far"})
        self.assertIn("expects", str(ctx.exception))
        self.assertEqual(self._reload()["search"]["radius_miles"], 100)

    def test_a_boolean_cannot_be_set_from_a_number(self):
        with self.assertRaises(settings.SettingsError):
            settings.apply_changes(self.config, {"scrapers.enabled": 1})

    def test_unknown_keys_are_rejected(self):
        with self.assertRaises(settings.SettingsError):
            settings.apply_changes(self.config, {"search.nonsense": 1})
        with self.assertRaises(settings.SettingsError):
            settings.apply_changes(self.config, {"nonsense.thing": 1})

    def test_paths_cannot_be_changed_over_the_api(self):
        with self.assertRaises(settings.SettingsError) as ctx:
            settings.apply_changes(self.config, {"paths.db": "/etc/passwd"})
        self.assertIn("not editable", str(ctx.exception))

    def test_changes_are_all_or_nothing(self):
        with self.assertRaises(settings.SettingsError):
            settings.apply_changes(self.config, {"search.zip": "37211", "search.radius_miles": "far"})
        self.assertEqual(self._reload()["search"]["zip"], "38464", "a rejected batch must change nothing")

    def test_dry_run_changes_nothing(self):
        result = settings.apply_changes(self.config, {"search.zip": "90210"}, dry_run=True)
        self.assertTrue(result["dry_run"])
        self.assertEqual(self._reload()["search"]["zip"], "38464")

    def test_rapid_successive_edits_each_keep_their_own_backup(self):
        settings.apply_changes(self.config, {"search.zip": "37211"})
        settings.apply_changes(self.config, {"search.zip": "37212"})
        history = sorted((self.tmp / "data" / "config-history").glob("config-*.json"))
        self.assertEqual(len(history), 2, "same-second edits must not overwrite each other's archive")
        self.assertEqual(json.loads(history[0].read_text())["search"]["zip"], "38464")
        self.assertEqual(json.loads(history[1].read_text())["search"]["zip"], "37211")

    def test_a_backup_is_kept(self):
        settings.apply_changes(self.config, {"search.zip": "37211"})
        history = list((self.tmp / "data" / "config-history").glob("config-*.json"))
        self.assertTrue(history, "the previous config should be archived")
        self.assertEqual(json.loads(history[0].read_text())["search"]["zip"], "38464")

    def test_warnings_are_returned_but_do_not_block(self):
        result = settings.apply_changes(self.config, {"api.monthly_call_cap": 5000})
        self.assertTrue(any("free tier" in warning for warning in result["warnings"]))
        self.assertEqual(self._reload()["api"]["monthly_call_cap"], 5000)

    def test_auto_derived_weights_are_left_alone(self):
        result = settings.apply_changes(self.config, {"scoring.weights.price_no_bonus_at": "auto"})
        self.assertEqual(result["applied"], {})
        self.assertEqual(self._reload()["scoring"]["weights"]["price_no_bonus_at"], "auto")

    def test_empty_change_set_is_rejected(self):
        with self.assertRaises(settings.SettingsError):
            settings.apply_changes(self.config, {})

    def test_the_written_file_is_still_valid_json_and_loadable(self):
        settings.apply_changes(self.config, {"search.zip": "37211", "search.price_max": 18000})
        reloaded = Config(json.loads(self.path.read_text()), self.path)
        self.assertEqual(reloaded.search["zip"], "37211")
        self.assertEqual(reloaded.scoring["weights"]["price_no_bonus_at"], 18000.0,
                         "auto-derived weights must follow the edited budget")


class SecretsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self._root = settings.PROJECT_ROOT
        settings.PROJECT_ROOT = self.tmp
        self.env_path = self.tmp / ".env"
        self.env_path.write_text(
            "# Comment worth keeping\nMARKETCHECK_API_KEY=original-key-1234\nDISCORD_WEBHOOK_URL=\n",
            encoding="utf-8",
        )
        self._saved_env = {key: os.environ.pop(key, None) for key in settings.KNOWN_SECRETS}

    def tearDown(self):
        settings.PROJECT_ROOT = self._root
        for key, value in self._saved_env.items():
            if value is not None:
                os.environ[key] = value
            else:
                os.environ.pop(key, None)

    def test_masking_never_reveals_more_than_the_last_four(self):
        self.assertEqual(settings.mask("original-key-1234"), "•" * 13 + "1234")
        self.assertNotIn("original", settings.mask("original-key-1234"))
        self.assertEqual(settings.mask(""), "")
        self.assertEqual(settings.mask("abc"), "•••")

    def test_status_reports_which_secrets_are_set_without_their_values(self):
        os.environ["MARKETCHECK_API_KEY"] = "live-secret-9876"
        status = {entry["key"]: entry for entry in settings.secrets_status()}
        self.assertTrue(status["MARKETCHECK_API_KEY"]["set"])
        self.assertFalse(status["DISCORD_BOT_TOKEN"]["set"])
        blob = json.dumps(settings.secrets_status())
        self.assertNotIn("live-secret-9876", blob, "a secret value must never leave this module")
        self.assertIn("9876", status["MARKETCHECK_API_KEY"]["masked"])

    def test_setting_a_secret_rewrites_only_that_line(self):
        settings.update_secrets({"MARKETCHECK_API_KEY": "new-key-5678"})
        text = self.env_path.read_text()
        self.assertIn("MARKETCHECK_API_KEY=new-key-5678", text)
        self.assertIn("# Comment worth keeping", text, "comments must survive an edit")
        self.assertIn("DISCORD_WEBHOOK_URL=", text)

    def test_a_new_secret_is_appended(self):
        settings.update_secrets({"DISCORD_BOT_TOKEN": "bot-token-1111"})
        self.assertIn("DISCORD_BOT_TOKEN=bot-token-1111", self.env_path.read_text())

    def test_clearing_a_secret_empties_it(self):
        settings.update_secrets({"MARKETCHECK_API_KEY": ""})
        self.assertIn("MARKETCHECK_API_KEY=", self.env_path.read_text())
        self.assertNotIn("original-key-1234", self.env_path.read_text())

    def test_unknown_secrets_are_rejected(self):
        with self.assertRaises(settings.SettingsError) as ctx:
            settings.update_secrets({"AWS_SECRET_ACCESS_KEY": "nope"})
        self.assertIn("unknown secret", str(ctx.exception))
        self.assertNotIn("AWS_SECRET", self.env_path.read_text())

    def test_the_env_file_is_not_world_readable(self):
        settings.update_secrets({"MARKETCHECK_API_KEY": "new-key-5678"})
        mode = stat.S_IMODE(self.env_path.stat().st_mode)
        self.assertEqual(mode & (stat.S_IRWXG | stat.S_IRWXO), 0,
                         "credentials should not be readable by other users")

    def test_update_never_returns_the_value(self):
        result = settings.update_secrets({"MARKETCHECK_API_KEY": "top-secret-4321"})
        self.assertNotIn("top-secret-4321", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
