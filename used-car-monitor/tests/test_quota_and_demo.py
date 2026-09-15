"""Quota pacing, the month-end sweep, and demo-data safety."""

import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from carmon import db, demo, quota
from carmon.config import load_config


class PaceTests(unittest.TestCase):
    """100 calls on the 15th should read as relaxed; 100 on the 5th should not."""

    def test_the_motivating_example(self):
        relaxed = quota.pace(100, 500, date(2026, 8, 15))
        tense = quota.pace(100, 500, date(2026, 8, 5))
        self.assertLess(relaxed["pace_ratio"], 1.0)
        self.assertGreater(tense["pace_ratio"], 1.0)
        self.assertEqual(relaxed["pace_label"], "well under pace")
        self.assertEqual(tense["pace_label"], "running hot")
        self.assertLess(relaxed["projected_month_total"], 500)
        self.assertGreater(tense["projected_month_total"], 500)

    def test_expected_by_now_tracks_the_calendar(self):
        metrics = quota.pace(0, 500, date(2026, 8, 15))
        self.assertAlmostEqual(metrics["expected_by_now"], 500 * 15 / 31, places=1)
        self.assertEqual(metrics["days_in_month"], 31)
        self.assertEqual(metrics["days_remaining"], 16)

    def test_difference_says_how_far_off_pace(self):
        metrics = quota.pace(100, 500, date(2026, 8, 15))
        self.assertLess(metrics["difference"], 0, "under pace should read as a negative difference")
        self.assertAlmostEqual(metrics["difference"], 100 - metrics["expected_by_now"], places=1)

    def test_pace_is_a_metric_not_a_limit(self):
        """Even wildly over pace, nothing here reports a block — the cap alone stops calls."""
        metrics = quota.pace(490, 500, date(2026, 8, 2))
        self.assertEqual(metrics["pace_label"], "far ahead of pace")
        self.assertEqual(metrics["remaining"], 10)
        self.assertNotIn("blocked", metrics)

    def test_affordable_per_day_spreads_what_is_left(self):
        metrics = quota.pace(200, 500, date(2026, 8, 21))
        self.assertAlmostEqual(metrics["affordable_per_day"], 300 / 10, places=1)

    def test_february_is_handled(self):
        self.assertEqual(quota.pace(0, 500, date(2026, 2, 14))["days_in_month"], 28)
        self.assertEqual(quota.pace(0, 500, date(2024, 2, 14))["days_in_month"], 29)

    def test_last_day_is_flagged(self):
        self.assertTrue(quota.pace(0, 500, date(2026, 8, 31))["is_last_day"])
        self.assertFalse(quota.pace(0, 500, date(2026, 8, 30))["is_last_day"])

    def test_zero_usage_does_not_divide_by_zero(self):
        metrics = quota.pace(0, 500, date(2026, 8, 1))
        self.assertEqual(metrics["pace_ratio"], 0.0)
        self.assertEqual(metrics["used"], 0)

    def test_summary_line_and_bar(self):
        metrics = quota.pace(100, 500, date(2026, 8, 15))
        summary = quota.summary_line(metrics)
        self.assertIn("100/500", summary)
        self.assertIn("day 15/31", summary)
        self.assertIn("well under pace", summary)
        gauge = quota.bar(metrics, 20)
        self.assertEqual(len(gauge), 20)
        self.assertIn("|", gauge)

    def test_pace_from_db_counts_only_this_month(self):
        conn = db.init_db(Path(tempfile.mkdtemp()) / "t.db")
        for _ in range(7):
            db.record_api_call(conn, "test", 200, "")
        metrics = quota.pace_from_db(conn, 500)
        self.assertEqual(metrics["used"], 7)
        conn.close()


class SweepBudgetTests(unittest.TestCase):
    def test_sweeps_on_the_last_day_with_calls_to_spare(self):
        plan = quota.sweep_budget(210, 500, {}, date(2026, 8, 31))
        self.assertTrue(plan["should_sweep"])
        self.assertEqual(plan["budget"], 500 - 210 - 20)
        self.assertIn("expire", plan["reason"])

    def test_does_not_sweep_mid_month(self):
        plan = quota.sweep_budget(210, 500, {}, date(2026, 8, 15))
        self.assertFalse(plan["should_sweep"])
        self.assertIn("not the sweep window", plan["reason"])

    def test_keeps_a_reserve(self):
        plan = quota.sweep_budget(495, 500, {}, date(2026, 8, 31))
        self.assertFalse(plan["should_sweep"])
        self.assertIn("reserve", plan["reason"])

    def test_respects_the_configured_ceiling(self):
        plan = quota.sweep_budget(0, 500, {"max_extra_calls": 50}, date(2026, 8, 31))
        self.assertEqual(plan["budget"], 50)

    def test_can_be_disabled(self):
        plan = quota.sweep_budget(0, 500, {"enabled": False}, date(2026, 8, 31))
        self.assertFalse(plan["should_sweep"])
        self.assertIn("disabled", plan["reason"])

    def test_trigger_window_can_cover_more_days(self):
        plan = quota.sweep_budget(100, 500, {"trigger_last_days": 3}, date(2026, 8, 30))
        self.assertTrue(plan["should_sweep"])


class DemoSafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.config = load_config()
        self.config.data["paths"]["db"] = str(self.tmp / "t.db")
        self.conn = db.init_db(self.config.db_path)

    def tearDown(self):
        self.conn.close()

    def _age_demo(self, hours: float) -> None:
        stamp = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat(timespec="seconds")
        self.conn.execute("UPDATE listings SET updated_at = ? WHERE source = 'demo'", (stamp,))
        self.conn.commit()

    def test_seeded_demo_is_counted_and_flagged(self):
        demo.seed(self.config, self.conn, count=5)
        self.assertEqual(demo.demo_count(self.conn), 5)
        banner = demo.demo_banner(self.conn)
        self.assertIn("DEMO DATA", banner)
        self.assertIn("not real cars", banner)

    def test_fresh_demo_data_is_kept(self):
        demo.seed(self.config, self.conn, count=3)
        self.assertEqual(demo.maybe_expire(self.conn, self.config), 0)
        self.assertEqual(demo.demo_count(self.conn), 3)

    def test_stale_demo_data_clears_itself(self):
        demo.seed(self.config, self.conn, count=3)
        self._age_demo(13)  # config default is 12 hours
        self.assertEqual(demo.maybe_expire(self.conn, self.config), 3)
        self.assertEqual(demo.demo_count(self.conn), 0)
        self.assertIsNone(demo.demo_banner(self.conn))

    def test_expiry_window_is_configurable(self):
        demo.seed(self.config, self.conn, count=2)
        self._age_demo(3)
        self.config.data["demo"]["auto_clear_hours"] = 2
        self.assertEqual(demo.maybe_expire(self.conn, self.config), 2)

    def test_expiry_can_be_switched_off(self):
        demo.seed(self.config, self.conn, count=2)
        self._age_demo(500)
        self.config.data["demo"]["auto_clear_hours"] = 0
        self.assertEqual(demo.maybe_expire(self.conn, self.config), 0)

    def test_force_clears_regardless_of_age(self):
        demo.seed(self.config, self.conn, count=4)
        self.assertEqual(demo.maybe_expire(self.conn, self.config, force=True), 4)

    def test_a_real_run_clears_demo_data_first(self):
        """The important guarantee: real listings never sit alongside fake ones."""
        from carmon.marketcheck import MarketCheckClient
        from carmon.pipeline import run_daily
        import json as _json

        class Response:
            status_code = 200

            def __init__(self, payload):
                self._payload = payload
                self.text = _json.dumps(payload)

            def json(self):
                return self._payload

        class Session:
            def get(self, url, params=None, timeout=None):
                return Response({"num_found": 1, "listings": [{
                    "vin": "REAL0000000000001", "price": 16000, "miles": 30000, "is_certified": 0,
                    "dist": 20, "inventory_type": "used", "vdp_url": "u",
                    "dealer": {"name": "d", "city": "c", "state": "TN"},
                    "build": {"year": 2022, "make": "Toyota", "model": "Corolla", "trim": "LE",
                              "body_type": "Sedan", "fuel_type": "Unleaded"}}]})

        self.config.data["search"]["include_certified_search"] = False
        self.config.data["search"]["max_pages"] = 1
        self.config.data["enrichment"]["nhtsa_enabled"] = False
        self.config.data["enrichment"]["epa_mpg_enabled"] = False
        demo.seed(self.config, self.conn, count=5)
        client = MarketCheckClient("k", self.conn, self.config.api, session=Session())

        run_daily(self.config, conn=self.conn, client=client, run_date="2026-08-15")

        self.assertEqual(demo.demo_count(self.conn), 0, "a real run must not leave demo rows behind")
        self.assertEqual(db.count_listings(self.conn, active_only=False), 1)

    def test_a_dry_run_leaves_demo_data_alone(self):
        from carmon.pipeline import run_daily
        demo.seed(self.config, self.conn, count=3)
        self.config.data["enrichment"]["nhtsa_enabled"] = False
        self.config.data["enrichment"]["epa_mpg_enabled"] = False
        try:
            run_daily(self.config, conn=self.conn, api_key="k", run_date="2026-08-15", dry_run=True)
        except Exception:
            pass
        self.assertEqual(demo.demo_count(self.conn), 3)

    def test_demo_helpers_are_safe_on_an_empty_database(self):
        self.assertEqual(demo.demo_count(self.conn), 0)
        self.assertIsNone(demo.demo_age_hours(self.conn))
        self.assertIsNone(demo.demo_banner(self.conn))
        self.assertEqual(demo.maybe_expire(self.conn, self.config), 0)


if __name__ == "__main__":
    unittest.main()
