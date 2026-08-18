"""Single-source-of-truth guards: config.json is authoritative and nothing drifts from it."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from carmon.config import AUTO_DERIVED_WEIGHTS, PROJECT_ROOT, load_config, validate_config
from carmon.scoring import DEFAULT_WEIGHTS


class ConfigConsistencyTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config()
        self.raw = json.loads((PROJECT_ROOT / "config.json").read_text())

    def test_shipped_config_is_valid(self):
        self.assertEqual(validate_config(self.config), [])

    def test_every_scoring_weight_is_known(self):
        unknown = set(self.raw["scoring"]["weights"]) - set(DEFAULT_WEIGHTS)
        self.assertEqual(unknown, set(), "config.json declares weights the scorer does not read")

    def test_every_default_weight_is_declared_in_config(self):
        missing = set(DEFAULT_WEIGHTS) - set(self.raw["scoring"]["weights"])
        self.assertEqual(missing, set(), "a scorer weight is missing from config.json")

    def test_search_criteria_are_the_single_source_for_derived_weights(self):
        for weight_key in AUTO_DERIVED_WEIGHTS:
            self.assertEqual(
                str(self.raw["scoring"]["weights"][weight_key]).lower(), "auto",
                f"{weight_key} should be \"auto\" so it tracks the search criteria",
            )

    def test_changing_the_budget_moves_the_price_weight(self):
        self.config.data["search"]["price_max"] = 15000
        self.assertEqual(self.config.scoring["weights"]["price_no_bonus_at"], 15000.0)

    def test_changing_the_mileage_ceiling_moves_the_mileage_ramp(self):
        self.config.data["search"]["mileage_max"] = 45000
        self.assertEqual(self.config.scoring["weights"]["mileage_full_penalty_at"], 45000.0)

    def test_hardcoded_drift_is_reported(self):
        self.config.data["search"]["price_max"] = 15000
        self.config.data["scoring"]["weights"]["price_no_bonus_at"] = 20000
        warnings = validate_config(self.config)
        self.assertTrue(any("price_no_bonus_at" in warning for warning in warnings))

    def test_unknown_weight_key_is_reported(self):
        self.config.data["scoring"]["weights"]["mileage_pentalty"] = -1
        self.assertTrue(any("unknown key" in warning for warning in validate_config(self.config)))

    def test_over_cap_settings_are_reported(self):
        self.config.data["search"]["radius_miles"] = 250
        self.config.data["api"]["monthly_call_cap"] = 5000
        warnings = " ".join(validate_config(self.config))
        self.assertIn("free-tier limit of 100", warnings)
        self.assertIn("500 calls/month", warnings)

    def test_secrets_never_live_in_config_json(self):
        blob = json.dumps(self.raw).lower()
        for forbidden in ("api_key", "apikey", "webhook", "token", "secret", "password"):
            self.assertNotIn(forbidden, blob, "secrets belong in .env, never in config.json")

    def test_env_example_documents_every_secret_the_code_reads(self):
        example = (PROJECT_ROOT / ".env.example").read_text()
        for name in ("MARKETCHECK_API_KEY", "DISCORD_WEBHOOK_URL", "CARMON_API_TOKEN"):
            self.assertIn(name, example)

    def test_gitignore_protects_the_env_file(self):
        ignored = (PROJECT_ROOT / ".gitignore").read_text().splitlines()
        self.assertIn(".env", ignored)

    def test_search_criteria_flow_into_the_source_links(self):
        from carmon.sources import build_sources
        self.config.data["search"]["zip"] = "90210"
        self.assertTrue(any("90210" in source.url for source in build_sources(self.config.search)))


if __name__ == "__main__":
    unittest.main()
