"""NHTSA complaints/recalls and EPA fuel-economy enrichment (all offline, fake sessions)."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from carmon import db, fueleconomy, nhtsa
from carmon.config import load_config
from carmon.fueleconomy import FuelEconomyClient, combined_from_city_highway
from carmon.nhtsa import NHTSAClient, recall_lookup_url, vin_recall_url
from carmon.pipeline import attach_cached_enrichment, enrich_listings
from carmon.scoring import score_listing

COMPLAINTS = {
    "count": 3,
    "results": [
        {"odiNumber": 1, "components": "STEERING,SUSPENSION", "crash": False, "fire": False,
         "numberOfInjuries": 0, "numberOfDeaths": 0, "summary": "sticky steering"},
        {"odiNumber": 2, "components": "STEERING", "crash": True, "fire": False,
         "numberOfInjuries": 1, "numberOfDeaths": 0, "summary": "lost control"},
        {"odiNumber": 3, "components": "UNKNOWN OR OTHER", "crash": False, "fire": True,
         "numberOfInjuries": 0, "numberOfDeaths": 0, "summary": "smoke"},
    ],
}
RECALLS = {
    "Count": 2,
    "results": [
        {"NHTSACampaignNumber": "23V704000", "Component": "STEERING:RACK AND PINION",
         "Summary": "steering rack may be incorrectly assembled", "Consequence": "tire damage",
         "Remedy": "inspect and replace", "ReportReceivedDate": "19/10/2023", "parkIt": False,
         "parkOutSide": False},
        {"NHTSACampaignNumber": "24V123000", "Component": "FUEL SYSTEM", "Summary": "leak",
         "Consequence": "fire risk", "Remedy": "replace pump", "ReportReceivedDate": "01/02/2024",
         "parkIt": True, "parkOutSide": True},
    ],
}


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


class FakeNHTSASession:
    def __init__(self, fail_with=None, recalls_status=200, recalls_payload=None):
        self.calls = []
        self.fail_with = fail_with
        self.recalls_status = recalls_status
        self.recalls_payload = recalls_payload if recalls_payload is not None else RECALLS

    def get(self, url, params=None, timeout=None, headers=None):
        self.calls.append((url, params))
        if self.fail_with:
            raise self.fail_with
        if "complaints" in url:
            return FakeResponse(COMPLAINTS)
        if "recalls" in url:
            return FakeResponse(self.recalls_payload, status_code=self.recalls_status)
        return FakeResponse({})


class FakeEPASession:
    """Mimics fueleconomy.gov, including its EPA-specific model naming."""

    def __init__(self):
        self.calls = []

    def get(self, url, params=None, timeout=None, headers=None):
        self.calls.append((url, params))
        if url.endswith("/menu/model"):
            return FakeResponse({"menuItem": [
                {"text": "Civic 4Dr", "value": "Civic 4Dr"},
                {"text": "Civic Type R", "value": "Civic Type R"},
                {"text": "Accord", "value": "Accord"},
            ]})
        if url.endswith("/menu/options"):
            return FakeResponse({"menuItem": [{"text": "auto", "value": "45678"}]})
        return FakeResponse({"city08": "31", "highway08": "40", "comb08": "35"})


class NHTSATests(unittest.TestCase):
    def setUp(self):
        self.conn = db.init_db(Path(tempfile.mkdtemp()) / "t.db")
        self.session = FakeNHTSASession()
        self.client = NHTSAClient(self.conn, {"cache_days": 30}, session=self.session)

    def tearDown(self):
        self.conn.close()

    def test_counts_and_component_rollup(self):
        facts = self.client.facts_for("Honda", "Civic", 2022)
        self.assertEqual(facts["complaint_count"], 3)
        self.assertEqual(facts["recall_count"], 2)
        self.assertEqual(facts["crash_complaints"], 1)
        self.assertEqual(facts["fire_complaints"], 1)
        self.assertEqual(facts["injuries"], 1)
        self.assertEqual(facts["top_components"][0], ["STEERING", 2])

    def test_placeholder_component_is_ignored(self):
        facts = self.client.facts_for("Honda", "Civic", 2022)
        self.assertNotIn("UNKNOWN OR OTHER", [component for component, _ in facts["top_components"]])

    def test_recall_details_are_kept(self):
        facts = self.client.facts_for("Honda", "Civic", 2022)
        campaigns = {recall["campaign"] for recall in facts["recalls"]}
        self.assertEqual(campaigns, {"23V704000", "24V123000"})
        park_it = next(r for r in facts["recalls"] if r["campaign"] == "24V123000")
        self.assertTrue(park_it["park_it"])

    def test_results_are_cached_so_repeat_lookups_are_free(self):
        self.client.facts_for("Honda", "Civic", 2022)
        calls_after_first = len(self.session.calls)
        self.client.facts_for("honda", "civic", 2022)
        self.assertEqual(len(self.session.calls), calls_after_first, "second lookup must hit the cache")

    def test_case_insensitive_cache_key(self):
        self.client.facts_for("HONDA", "CIVIC", 2022)
        self.assertIsNotNone(db.get_reliability(self.conn, "honda", "civic", 2022))

    def test_network_failure_is_not_fatal(self):
        client = NHTSAClient(self.conn, {"max_retries": 0}, session=FakeNHTSASession(fail_with=OSError("boom")))
        self.assertIsNone(client.facts_for("Kia", "Forte", 2022))

    def test_network_failure_falls_back_to_stale_cache(self):
        self.client.facts_for("Honda", "Civic", 2022)
        broken = NHTSAClient(self.conn, {"max_retries": 0, "cache_days": 0},
                             session=FakeNHTSASession(fail_with=OSError("boom")))
        self.assertEqual(broken.facts_for("Honda", "Civic", 2022)["complaint_count"], 3)

    def test_http_400_with_zero_results_means_no_recalls_not_an_error(self):
        """NHTSA answers 400 with a valid 'Count: 0' body when a model-year has no recalls."""
        session = FakeNHTSASession(
            recalls_status=400,
            recalls_payload={"Count": 0, "Message": "Results returned successfully", "results": []},
        )
        client = NHTSAClient(self.conn, {"max_retries": 0}, session=session)
        facts = client.facts_for("Toyota", "Corolla", 2022)
        self.assertIsNotNone(facts, "a zero-recall model must still get its complaint data stored")
        self.assertEqual(facts["recall_count"], 0)
        self.assertEqual(facts["complaint_count"], 3)

    def test_a_real_400_still_fails(self):
        session = FakeNHTSASession(recalls_status=400, recalls_payload={"error": "bad request"})
        client = NHTSAClient(self.conn, {"max_retries": 0}, session=session)
        facts = client.facts_for("Toyota", "Corolla", 2022)
        self.assertEqual(facts["complaint_count"], 3, "complaints survive a recalls-side failure")
        self.assertEqual(facts["recall_count"], 0)
        self.assertTrue(facts["partial"], "a partial fetch is flagged as such")

    def test_incomplete_vehicle_returns_none(self):
        self.assertIsNone(self.client.facts_for("", "Civic", 2022))
        self.assertIsNone(self.client.facts_for("Honda", "Civic", None))

    def test_human_lookup_urls(self):
        self.assertIn("vehicleMake=Honda", recall_lookup_url("Honda", "Civic", 2022))
        self.assertIn("vin=ABC", vin_recall_url("ABC"))


class FuelEconomyTests(unittest.TestCase):
    def setUp(self):
        self.conn = db.init_db(Path(tempfile.mkdtemp()) / "t.db")
        self.session = FakeEPASession()
        self.client = FuelEconomyClient(self.conn, {}, session=self.session)

    def tearDown(self):
        self.conn.close()

    def test_combined_uses_epa_weighting(self):
        self.assertEqual(combined_from_city_highway(30, 40), 34.5)
        self.assertEqual(combined_from_city_highway(30, None), 30.0)
        self.assertIsNone(combined_from_city_highway(None, None))

    def test_epa_model_name_is_matched_fuzzily(self):
        self.assertEqual(self.client.best_model_name(2022, "Honda", "Civic"), "Civic 4Dr")

    def test_lookup_stores_mpg(self):
        record = self.client.lookup(2022, "Honda", "Civic")
        self.assertEqual(record["city_mpg"], 31.0)
        self.assertEqual(record["highway_mpg"], 40.0)
        self.assertEqual(record["matched_name"], "Civic 4Dr")

    def test_lookup_is_cached(self):
        self.client.lookup(2022, "Honda", "Civic")
        calls = len(self.session.calls)
        self.client.lookup(2022, "Honda", "Civic")
        self.assertEqual(len(self.session.calls), calls)

    def test_unmatched_model_returns_none(self):
        self.assertIsNone(self.client.lookup(2022, "Honda", "Tractor"))


class EnrichIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.conn = db.init_db(Path(tempfile.mkdtemp()) / "t.db")
        self.config = load_config()

    def tearDown(self):
        self.conn.close()

    def test_enrichment_feeds_the_score(self):
        listings = [{"vin": "V1", "make": "Honda", "model": "Civic", "year": 2022,
                     "price_current": 16500, "mileage": 35000, "distance_miles": 30}]
        enrich_listings(
            self.config, self.conn, listings,
            nhtsa_client=NHTSAClient(self.conn, {}, session=FakeNHTSASession()),
            mpg_client=FuelEconomyClient(self.conn, {}, session=FakeEPASession()),
        )
        listing = listings[0]
        self.assertEqual(listing["complaint_count"], 3)
        self.assertEqual(listing["recall_count"], 2)
        self.assertAlmostEqual(listing["combined_mpg"], 35.0, places=1)

        result = score_listing(listing, self.config.scoring)
        labels = {c.label for c in result.components}
        self.assertIn("NHTSA complaints", labels)
        self.assertIn("NHTSA recalls", labels)
        self.assertIn("fuel economy", labels)
        recalls = next(c for c in result.components if c.label == "NHTSA recalls")
        self.assertAlmostEqual(recalls.value, -0.30, places=2)

    def test_one_lookup_serves_many_listings_of_the_same_model(self):
        session = FakeNHTSASession()
        listings = [
            {"vin": f"V{i}", "make": "Honda", "model": "Civic", "year": 2022, "price_current": 16000}
            for i in range(5)
        ]
        enrich_listings(self.config, self.conn, listings,
                        nhtsa_client=NHTSAClient(self.conn, {}, session=session),
                        mpg_client=FuelEconomyClient(self.conn, {}, session=FakeEPASession()))
        self.assertEqual(len(session.calls), 2, "5 listings of one model-year cost 2 NHTSA calls, not 10")
        self.assertTrue(all(l["complaint_count"] == 3 for l in listings))

    def test_marketcheck_mpg_wins_over_an_epa_lookup(self):
        session = FakeEPASession()
        listings = [{"vin": "V1", "make": "Honda", "model": "Civic", "year": 2022,
                     "city_mpg": 33, "highway_mpg": 42, "combined_mpg": 37.1}]
        enrich_listings(self.config, self.conn, listings,
                        nhtsa_client=NHTSAClient(self.conn, {}, session=FakeNHTSASession()),
                        mpg_client=FuelEconomyClient(self.conn, {}, session=session))
        self.assertEqual(listings[0]["combined_mpg"], 37.1)
        self.assertEqual(session.calls, [], "no EPA call when MarketCheck already supplied MPG")

    def test_disabled_enrichment_makes_no_calls(self):
        config = load_config()
        config.data["enrichment"]["nhtsa_enabled"] = False
        config.data["enrichment"]["epa_mpg_enabled"] = False
        session = FakeNHTSASession()
        listings = [{"vin": "V1", "make": "Honda", "model": "Civic", "year": 2022}]
        summary = enrich_listings(config, self.conn, listings,
                                  nhtsa_client=NHTSAClient(self.conn, {}, session=session))
        self.assertEqual(session.calls, [])
        self.assertIsNone(summary["nhtsa"])

    def test_cached_enrichment_attaches_without_network(self):
        db.save_reliability(self.conn, "Kia", "Forte", 2023,
                            {"complaint_count": 12, "recall_count": 1, "top_components": [["ENGINE", 4]]})
        listing = attach_cached_enrichment(self.conn, {"make": "Kia", "model": "Forte", "year": 2023})
        self.assertEqual(listing["complaint_count"], 12)
        self.assertEqual(listing["top_complaint_components"][0], ["ENGINE", 4])


if __name__ == "__main__":
    unittest.main()
