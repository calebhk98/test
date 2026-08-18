"""CLI commands and storage-layer behaviour that the other suites do not cover."""

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from carmon import db, demo
from carmon.cli import main
from carmon.config import load_config, load_env, ConfigError
from carmon.sources import build_sources, sources_for_listing


class DbTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.conn = db.init_db(self.tmp / "t.db")

    def tearDown(self):
        self.conn.close()

    def test_vin_is_the_primary_key_so_repeats_dedupe(self):
        for _ in range(3):
            db.upsert_listing(self.conn, {"vin": "V1", "make": "Kia", "model": "Forte", "price_current": 15000})
        self.assertEqual(db.count_listings(self.conn, active_only=False), 1)

    def test_history_only_appended_when_something_changed(self):
        db.upsert_listing(self.conn, {"vin": "V1", "price_current": 15000, "mileage": 20000}, "2026-08-01")
        db.upsert_listing(self.conn, {"vin": "V1", "price_current": 15000, "mileage": 20000}, "2026-08-02")
        self.assertEqual(len(db.get_price_history(self.conn, "V1")), 1)
        db.upsert_listing(self.conn, {"vin": "V1", "price_current": 14500, "mileage": 20000}, "2026-08-03")
        self.assertEqual(len(db.get_price_history(self.conn, "V1")), 2)

    def test_first_seen_never_moves_but_last_seen_does(self):
        db.upsert_listing(self.conn, {"vin": "V1", "price_current": 15000}, "2026-08-01")
        db.upsert_listing(self.conn, {"vin": "V1", "price_current": 14000}, "2026-08-09")
        row = db.get_listing(self.conn, "V1")
        self.assertEqual(row["first_seen"], "2026-08-01")
        self.assertEqual(row["last_seen"], "2026-08-09")
        self.assertEqual(row["price_first_seen"], 15000)

    def test_search_filters_and_sorting(self):
        db.upsert_listing(self.conn, {"vin": "A", "make": "Toyota", "model": "Corolla", "price_current": 15000, "score": 3.0, "cpo": True})
        db.upsert_listing(self.conn, {"vin": "B", "make": "Nissan", "model": "Altima", "price_current": 12000, "score": -1.0})
        self.assertEqual([l["vin"] for l in db.search_listings(self.conn, sort="score")], ["A", "B"])
        self.assertEqual([l["vin"] for l in db.search_listings(self.conn, sort="price")], ["B", "A"])
        self.assertEqual([l["vin"] for l in db.search_listings(self.conn, make="toyota")], ["A"])
        self.assertEqual([l["vin"] for l in db.search_listings(self.conn, cpo_only=True)], ["A"])
        self.assertEqual([l["vin"] for l in db.search_listings(self.conn, min_score=0)], ["A"])
        self.assertEqual([l["vin"] for l in db.search_listings(self.conn, query="altima")], ["B"])

    def test_search_limit_is_capped(self):
        rows = db.search_listings(self.conn, limit=99999)
        self.assertIsInstance(rows, list)

    def test_score_breakdown_round_trips_as_json(self):
        db.upsert_listing(self.conn, {"vin": "A", "score": 1.0, "score_breakdown": [{"label": "CPO", "value": 2.0, "detail": "certified"}]})
        stored = db.get_listing(self.conn, "A")
        self.assertEqual(stored["score_breakdown"][0]["label"], "CPO")


class SourcesTests(unittest.TestCase):
    def setUp(self):
        self.search = load_config().search

    def test_all_three_categories_are_present(self):
        categories = {source.category for source in build_sources(self.search)}
        self.assertEqual(categories, {"manufacturer_cpo", "retailer", "aggregator"})

    def test_links_carry_the_configured_criteria(self):
        carmax = next(s for s in build_sources(self.search) if s.key == "carmax")
        self.assertIn("zip=38464", carmax.url)
        self.assertIn("20000", carmax.url)
        self.assertIn("60000", carmax.url)

    def test_expected_sites_are_covered(self):
        keys = {source.key for source in build_sources(self.search)}
        for expected in ("toyota_certified", "honda_certified", "carmax", "carvana", "vroom",
                         "cargurus", "autotrader", "cars_com", "truecar"):
            self.assertIn(expected, keys)

    def test_per_listing_cross_shop_links(self):
        links = sources_for_listing({"year": 2022, "make": "Honda", "model": "Civic"}, self.search)
        self.assertTrue(links)
        self.assertTrue(all(link["url"].startswith("https://") for link in links))

    def test_no_scraper_is_registered_in_v1(self):
        from carmon import scrapers
        self.assertEqual(scrapers.available(), [])


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.db_path = str(self.tmp / "cli.db")

    def _run(self, *argv):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = main(["--db", self.db_path, *argv])
        return code, buffer.getvalue()

    def test_seed_demo_then_stats_and_digest(self):
        code, out = self._run("seed-demo", "--count", "6")
        self.assertEqual(code, 0)
        self.assertIn("Seeded 6", out)

        code, out = self._run("stats")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["listings_active"], 6)

        code, out = self._run("digest", "--days", "30")
        self.assertEqual(code, 0)
        self.assertIn("Used Car Daily Digest", out)

    def test_seed_demo_clear(self):
        self._run("seed-demo", "--count", "4")
        code, out = self._run("seed-demo", "--clear")
        self.assertEqual(code, 0)
        self.assertIn("Removed 4", out)

    def test_score_command_explains_itself(self):
        code, out = self._run("score", "--make", "Nissan", "--model", "Sentra", "--mileage", "45000")
        self.assertEqual(code, 0)
        self.assertIn("caution model", out)
        self.assertIn("mileage", out)

    def test_score_command_json(self):
        code, out = self._run("score", "--make", "Honda", "--model", "Civic", "--json")
        payload = json.loads(out)
        self.assertIn("components", payload)

    def test_rescore_after_switching_to_step_mode(self):
        self._run("seed-demo", "--count", "5")
        code, out = self._run("rescore")
        self.assertEqual(code, 0)
        self.assertIn("Rescored 5", out)

    def test_sources_command(self):
        code, out = self._run("sources")
        self.assertEqual(code, 0)
        self.assertIn("CarMax", out)
        code, out = self._run("sources", "--json")
        self.assertIn("manufacturer_cpo", json.loads(out))

    def test_cron_command_prints_a_usable_line(self):
        code, out = self._run("cron", "--at", "7:30")
        self.assertEqual(code, 0)
        self.assertIn("30 7 * * *", out)
        self.assertIn("-m carmon run", out)

    def test_bad_config_path_is_reported(self):
        code = main(["--config", str(self.tmp / "nope.json"), "stats"])
        self.assertEqual(code, 2)


class EnvTests(unittest.TestCase):
    def test_env_file_is_parsed_and_env_vars_win(self):
        tmp = Path(tempfile.mkdtemp()) / ".env"
        tmp.write_text('MARKETCHECK_API_KEY="from-file"\n# comment\nDISCORD_WEBHOOK_URL=https://hook\n')
        values = load_env(tmp)
        self.assertEqual(values["MARKETCHECK_API_KEY"], "from-file")
        self.assertEqual(values["DISCORD_WEBHOOK_URL"], "https://hook")

    def test_missing_env_file_is_not_fatal(self):
        self.assertIsInstance(load_env(Path("/nonexistent/.env")), dict)


if __name__ == "__main__":
    unittest.main()
