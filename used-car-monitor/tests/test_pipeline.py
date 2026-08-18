"""Pipeline: normalization, client-side filtering, quota handling, upsert bookkeeping."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from carmon import db
from carmon.config import load_config
from carmon.marketcheck import MarketCheckClient, QuotaExceeded
from carmon.pipeline import filter_reason, normalize_listing, run_daily


def raw_listing(vin="1HGCV1F3XLA000001", **overrides):
    listing = {
        "vin": vin,
        "price": 17500,
        "miles": 32000,
        "is_certified": 0,
        "dist": 22.4,
        "inventory_type": "used",
        "vdp_url": "https://dealer.test/car/1",
        "dealer": {"name": "Test Motors", "city": "Columbia", "state": "TN"},
        "build": {
            "year": 2022, "make": "Honda", "model": "Civic", "trim": "LX",
            "body_type": "Sedan", "fuel_type": "Unleaded",
        },
    }
    listing.update(overrides)
    return listing


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


class FakeSession:
    """Stand-in for requests.Session that serves canned pages."""

    def __init__(self, pages):
        self.pages = list(pages)
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append(params)
        if self.pages:
            return FakeResponse(self.pages.pop(0))
        return FakeResponse({"num_found": 0, "listings": []})


class NormalizationTests(unittest.TestCase):
    def test_maps_marketcheck_fields(self):
        listing = normalize_listing(raw_listing())
        self.assertEqual(listing["vin"], "1HGCV1F3XLA000001")
        self.assertEqual(listing["make"], "Honda")
        self.assertEqual(listing["model"], "Civic")
        self.assertEqual(listing["mileage"], 32000)
        self.assertEqual(listing["price_current"], 17500)
        self.assertEqual(listing["dealer_city"], "Columbia")
        self.assertAlmostEqual(listing["distance_miles"], 22.4)
        self.assertFalse(listing["cpo"])

    def test_certified_flags_are_recognised(self):
        self.assertTrue(normalize_listing(raw_listing(is_certified=1))["cpo"])
        self.assertTrue(normalize_listing(raw_listing(inventory_type="certified"))["cpo"])

    def test_missing_vin_is_dropped(self):
        self.assertIsNone(normalize_listing(raw_listing(vin="")))

    def test_garbage_numbers_become_none(self):
        listing = normalize_listing(raw_listing(price="n/a", miles=None))
        self.assertIsNone(listing["price_current"])
        self.assertIsNone(listing["mileage"])


class FilterTests(unittest.TestCase):
    def setUp(self):
        self.search = load_config().search

    def _reason(self, **overrides):
        return filter_reason(normalize_listing(raw_listing(**overrides)), self.search)

    def test_matching_listing_is_kept(self):
        self.assertIsNone(self._reason())

    def test_truck_is_excluded(self):
        build = dict(raw_listing()["build"], body_type="Pickup", make="Ford", model="F-150")
        self.assertIn("body type", self._reason(build=build))

    def test_electric_excluded_by_default(self):
        build = dict(raw_listing()["build"], fuel_type="Electric")
        self.assertIn("fuel type", self._reason(build=build))

    def test_hybrid_toggle_can_allow_hybrids(self):
        build = dict(raw_listing()["build"], fuel_type="Hybrid")
        self.assertIsNotNone(self._reason(build=build))
        self.search = dict(self.search, include_electric_hybrid=True)
        self.assertIsNone(self._reason(build=build))

    def test_large_suv_model_excluded(self):
        build = dict(raw_listing()["build"], body_type="SUV", make="Chevrolet", model="Tahoe")
        self.assertIn("excluded model", self._reason(build=build))

    def test_over_budget_and_over_mileage_rejected(self):
        self.assertIn("price", self._reason(price=25000))
        self.assertIn("mileage", self._reason(miles=75000))

    def test_old_car_rejected(self):
        build = dict(raw_listing()["build"], year=2019)
        self.assertIn("year", self._reason(build=build))

    def test_new_car_rejected(self):
        self.assertIn("new car", self._reason(inventory_type="new", miles=12))


class RunDailyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.config = load_config()
        self.config.data["paths"]["db"] = str(self.tmp / "test.db")
        self.config.data["paths"]["digest_dir"] = str(self.tmp / "digests")
        self.config.data["search"]["include_certified_search"] = False
        self.config.data["search"]["max_pages"] = 1
        self.conn = db.init_db(self.config.db_path)

    def tearDown(self):
        self.conn.close()

    def _client(self, pages):
        return MarketCheckClient("test-key", self.conn, self.config.api, session=FakeSession(pages))

    def test_first_run_inserts_and_scores(self):
        pages = [{"num_found": 2, "listings": [raw_listing(), raw_listing(vin="2T1BURHE0JC000002")]}]
        result = run_daily(self.config, conn=self.conn, client=self._client(pages), run_date="2026-08-17")
        self.assertEqual(result.kept, 2)
        self.assertEqual(len(result.new_vins), 2)
        stored = db.get_listing(self.conn, "1HGCV1F3XLA000001")
        self.assertIsNotNone(stored["score"])
        self.assertTrue(stored["score_breakdown"], "score inputs must be stored, not hidden")

    def test_second_run_records_price_drop_history(self):
        run_daily(self.config, conn=self.conn, client=self._client(
            [{"num_found": 1, "listings": [raw_listing()]}]), run_date="2026-08-17")
        result = run_daily(self.config, conn=self.conn, client=self._client(
            [{"num_found": 1, "listings": [raw_listing(price=16000)]}]), run_date="2026-08-18")
        self.assertEqual(result.new_vins, [])
        self.assertEqual(result.price_change_vins, ["1HGCV1F3XLA000001"])
        history = db.get_price_history(self.conn, "1HGCV1F3XLA000001")
        self.assertEqual([h["price"] for h in history], [17500, 16000])
        drops = db.price_drops_since(self.conn, "2026-08-18")
        self.assertEqual(drops[0]["price_drop"], 1500)
        self.assertEqual(db.get_listing(self.conn, "1HGCV1F3XLA000001")["price_first_seen"], 17500)

    def test_disappeared_listing_marked_inactive(self):
        run_daily(self.config, conn=self.conn, client=self._client(
            [{"num_found": 2, "listings": [raw_listing(), raw_listing(vin="GONE0000000000001")]}]),
            run_date="2026-08-17")
        run_daily(self.config, conn=self.conn, client=self._client(
            [{"num_found": 1, "listings": [raw_listing()]}]), run_date="2026-08-18")
        self.assertFalse(db.get_listing(self.conn, "GONE0000000000001")["active"])
        self.assertEqual(db.count_listings(self.conn, active_only=True), 1)

    def test_api_calls_are_logged_against_the_monthly_cap(self):
        run_daily(self.config, conn=self.conn, client=self._client(
            [{"num_found": 1, "listings": [raw_listing()]}]), run_date="2026-08-17")
        self.assertEqual(db.calls_this_month(self.conn), 1)
        stats = db.stats(self.conn, 500)
        self.assertEqual(stats["api_calls_this_month"], 1)
        self.assertEqual(stats["api_calls_remaining"], 499)

    def test_monthly_cap_stops_further_calls(self):
        client = self._client([{"num_found": 1, "listings": [raw_listing()]}])
        client.monthly_cap = 1
        db.record_api_call(self.conn, "test", 200, "pre-existing")
        with self.assertRaises(QuotaExceeded):
            client._get({"start": 0})

    def test_dry_run_writes_nothing(self):
        result = run_daily(self.config, conn=self.conn, client=self._client(
            [{"num_found": 1, "listings": [raw_listing()]}]), run_date="2026-08-17", dry_run=True)
        self.assertEqual(result.kept, 1)
        self.assertEqual(db.count_listings(self.conn, active_only=False), 0)

    def test_run_is_recorded_even_on_error(self):
        class BoomSession:
            def get(self, *a, **k):
                return FakeResponse({"error": "bad key"}, status_code=401)

        client = MarketCheckClient("bad", self.conn, self.config.api, session=BoomSession())
        result = run_daily(self.config, conn=self.conn, client=client, run_date="2026-08-17")
        self.assertTrue(result.errors)
        runs = db.recent_runs(self.conn, 1)
        self.assertEqual(runs[0]["status"], "error")

    def test_radius_is_clamped_to_free_tier(self):
        self.config.data["search"]["radius_miles"] = 250
        client = self._client([{"num_found": 0, "listings": []}])
        self.assertEqual(client.build_params(self.config.search)["radius"], 100)


if __name__ == "__main__":
    unittest.main()
