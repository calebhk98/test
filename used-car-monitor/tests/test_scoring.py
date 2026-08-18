"""Scoring rules: spec-literal `step` mode and continuous `smooth` mode."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from carmon.config import load_config
from carmon.scoring import normalize, score_listing


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.scoring = load_config().scoring

    def _score(self, **kwargs):
        listing = {"make": "Toyota", "model": "Corolla", "cpo": False}
        listing.update(kwargs)
        return score_listing(listing, self.scoring)

    # --- make/model preference ------------------------------------------
    def test_preferred_model_gets_bonus(self):
        result = self._score(make="Honda", model="Civic")
        values = {c.label: c.value for c in result.components}
        self.assertEqual(values["preferred model"], 2.0)

    def test_preferred_matches_model_variants(self):
        self.assertEqual(normalize("Mazda3"), normalize("Mazda 3"))
        result = self._score(make="Toyota", model="Corolla Hatchback")
        self.assertEqual({c.label for c in result.components} & {"preferred model"}, {"preferred model"})

    def test_caution_model_penalised_when_not_cpo(self):
        result = self._score(make="Nissan", model="Altima")
        values = {c.label: c.value for c in result.components}
        self.assertEqual(values["caution model"], -2.0)

    def test_caution_model_waived_when_cpo(self):
        result = self._score(make="Nissan", model="Altima", cpo=True)
        labels = {c.label: c.value for c in result.components}
        self.assertEqual(labels["caution model (waived)"], 0.0)
        self.assertEqual(labels["CPO"], 2.0)

    def test_neutral_model_scores_zero_for_preference(self):
        result = self._score(make="Subaru", model="Impreza")
        values = {c.label: c.value for c in result.components}
        self.assertEqual(values["model preference"], 0.0)

    # --- the continuity requirement --------------------------------------
    def test_mileage_is_continuous_near_40k(self):
        low = self._score(mileage=39950).score
        high = self._score(mileage=40050).score
        self.assertLess(abs(low - high), 0.02, "39,950 and 40,050 miles must score almost identically")

    def test_mileage_60k_is_clearly_worse_than_40k(self):
        at_40k = self._score(mileage=40000).score
        at_60k = self._score(mileage=60000).score
        self.assertLess(at_60k, at_40k - 0.9, "60,000 miles must be materially worse than 40,000")

    def test_mileage_anchor_matches_spec_at_40k(self):
        """The smooth ramp is calibrated so 40,000 miles still costs exactly -1."""
        component = next(c for c in self._score(mileage=40000).components if c.label == "mileage")
        self.assertAlmostEqual(component.value, -1.0, places=2)

    def test_step_mode_reproduces_the_spec_literally(self):
        scoring = dict(self.scoring, mode="step")
        below = score_listing({"make": "Toyota", "model": "Corolla", "mileage": 39950}, scoring)
        above = score_listing({"make": "Toyota", "model": "Corolla", "mileage": 40050}, scoring)
        self.assertEqual(below.score - above.score, 1.0, "step mode keeps the sharp 40k cliff on purpose")

    def test_distance_penalty_is_free_under_50_miles(self):
        component = next(c for c in self._score(distance_miles=45).components if c.label == "distance")
        self.assertEqual(component.value, 0.0)

    def test_distance_penalty_scales_beyond_50_miles(self):
        component = next(c for c in self._score(distance_miles=100).components if c.label == "distance")
        self.assertAlmostEqual(component.value, -2.0, places=2)

    def test_distance_penalty_has_a_floor(self):
        component = next(c for c in self._score(distance_miles=1000).components if c.label == "distance")
        self.assertGreaterEqual(component.value, -3.0)

    # --- price drop -------------------------------------------------------
    def test_price_drop_bonus(self):
        component = next(
            c for c in self._score(price_current=17000, price_first_seen=18000).components
            if c.label == "price drop"
        )
        self.assertGreater(component.value, 1.0)

    def test_no_bonus_when_price_rose(self):
        component = next(
            c for c in self._score(price_current=19000, price_first_seen=18000).components
            if c.label == "price drop"
        )
        self.assertEqual(component.value, 0.0)

    # --- transparency -----------------------------------------------------
    def test_every_component_is_explained(self):
        result = self._score(mileage=30000, distance_miles=70, cpo=True, price_current=16000,
                             year=2022, combined_mpg=34, complaint_count=95, recall_count=0)
        labels = [c.label for c in result.components]
        self.assertEqual(len(labels), 10, f"every scored dimension must be reported: {labels}")
        for expected in ("CPO", "price drop", "distance", "mileage", "price", "model year",
                         "fuel economy", "NHTSA complaints", "NHTSA recalls"):
            self.assertIn(expected, labels)
        for component in result.components:
            self.assertTrue(component.detail, f"component {component.label} has no explanation")
        self.assertAlmostEqual(result.score, sum(c.value for c in result.components), places=2)
        self.assertIn("score", result.explain())

    def test_missing_fields_do_not_crash(self):
        result = score_listing({}, self.scoring)
        self.assertIsInstance(result.score, float)

    def test_unresolved_auto_weight_falls_back_instead_of_crashing(self):
        scoring = dict(self.scoring)
        scoring["weights"] = dict(scoring["weights"], price_no_bonus_at="auto")
        result = score_listing({"make": "Kia", "model": "Forte", "price_current": 15000}, scoring)
        self.assertIsInstance(result.score, float)


class PriceYearMpgTests(unittest.TestCase):
    """Price, model year and MPG components."""

    def setUp(self):
        self.scoring = load_config().scoring

    def _component(self, label, **listing):
        result = score_listing({"make": "Kia", "model": "Forte", **listing}, self.scoring)
        return next(c for c in result.components if c.label == label)

    def test_cheaper_scores_better_up_to_the_full_bonus(self):
        dear = self._component("price", price_current=20000).value
        middling = self._component("price", price_current=16000).value
        cheap = self._component("price", price_current=12000).value
        self.assertEqual(dear, 0.0)
        self.assertAlmostEqual(cheap, 1.5, places=2)
        self.assertTrue(dear < middling < cheap)

    def test_price_bonus_is_capped_below_the_full_bonus_point(self):
        self.assertAlmostEqual(self._component("price", price_current=8000).value, 1.5, places=2)

    def test_price_is_continuous(self):
        low = self._component("price", price_current=15990).value
        high = self._component("price", price_current=16010).value
        self.assertLess(abs(low - high), 0.02)

    def test_price_ceiling_tracks_the_configured_budget(self):
        config = load_config()
        config.data["search"]["price_max"] = 15000
        component = next(
            c for c in score_listing({"make": "Kia", "model": "Forte", "price_current": 15000}, config.scoring).components
            if c.label == "price"
        )
        self.assertEqual(component.value, 0.0, "the price bonus must hit zero at the configured budget")

    def test_newer_model_years_score_better(self):
        self.assertEqual(self._component("model year", year=2021).value, 0.0)
        self.assertAlmostEqual(self._component("model year", year=2023).value, 0.5, places=2)
        self.assertAlmostEqual(self._component("model year", year=2025).value, 1.0, places=2)

    def test_year_bonus_does_not_run_away_for_very_new_cars(self):
        self.assertAlmostEqual(self._component("model year", year=2030).value, 1.0, places=2)

    def test_mpg_bonus_and_penalty(self):
        self.assertEqual(self._component("fuel economy", combined_mpg=28).value, 0.0)
        self.assertAlmostEqual(self._component("fuel economy", combined_mpg=40).value, 1.0, places=2)
        self.assertLess(self._component("fuel economy", combined_mpg=20).value, 0.0)

    def test_mpg_penalty_has_a_floor(self):
        self.assertAlmostEqual(self._component("fuel economy", combined_mpg=5).value, -0.5, places=2)

    def test_combined_mpg_is_derived_when_only_city_and_highway_are_known(self):
        component = self._component("fuel economy", city_mpg=30, highway_mpg=40)
        self.assertIn("34.5", component.detail)

    def test_unknown_values_score_zero_and_say_so(self):
        for label in ("price", "model year", "fuel economy"):
            component = self._component(label)
            self.assertEqual(component.value, 0.0)
            self.assertIn("unknown" if label != "fuel economy" else "no MPG data", component.detail)


class ReliabilityScoringTests(unittest.TestCase):
    """NHTSA complaint and recall components."""

    def setUp(self):
        self.scoring = load_config().scoring

    def _component(self, label, **listing):
        result = score_listing({"make": "Honda", "model": "Civic", **listing}, self.scoring)
        return next(c for c in result.components if c.label == label)

    def test_few_complaints_cost_nothing(self):
        self.assertEqual(self._component("NHTSA complaints", complaint_count=40).value, 0.0)

    def test_many_complaints_cost_the_full_penalty(self):
        self.assertAlmostEqual(self._component("NHTSA complaints", complaint_count=600).value, -1.5, places=2)
        self.assertAlmostEqual(self._component("NHTSA complaints", complaint_count=5000).value, -1.5, places=2)

    def test_complaint_penalty_is_continuous(self):
        low = self._component("NHTSA complaints", complaint_count=349).value
        high = self._component("NHTSA complaints", complaint_count=351).value
        self.assertLess(abs(low - high), 0.02)

    def test_top_component_is_named_in_the_explanation(self):
        component = self._component(
            "NHTSA complaints", complaint_count=878, top_complaint_components=[["STEERING", 729]]
        )
        self.assertIn("STEERING", component.detail)
        self.assertIn("not sales-volume adjusted", component.detail)

    def test_recalls_cost_a_little_each_with_a_floor(self):
        self.assertEqual(self._component("NHTSA recalls", recall_count=0).value, 0.0)
        self.assertAlmostEqual(self._component("NHTSA recalls", recall_count=4).value, -0.6, places=2)
        self.assertAlmostEqual(self._component("NHTSA recalls", recall_count=20).value, -0.75, places=2)

    def test_no_nhtsa_data_is_neutral_not_a_penalty(self):
        for label in ("NHTSA complaints", "NHTSA recalls"):
            component = self._component(label)
            self.assertEqual(component.value, 0.0)
            self.assertIn("no NHTSA data", component.detail)

    def test_a_clean_model_outscores_a_complaint_heavy_one(self):
        base = {"make": "Honda", "model": "Civic", "year": 2022, "price_current": 16500, "mileage": 30000}
        clean = score_listing({**base, "complaint_count": 95, "recall_count": 0}, self.scoring).score
        troubled = score_listing({**base, "complaint_count": 878, "recall_count": 4}, self.scoring).score
        self.assertGreater(clean - troubled, 1.5)

    def test_step_mode_thresholds(self):
        scoring = dict(self.scoring, mode="step")
        quiet = next(c for c in score_listing({"complaint_count": 100, "recall_count": 1}, scoring).components
                     if c.label == "NHTSA complaints")
        loud = next(c for c in score_listing({"complaint_count": 900, "recall_count": 5}, scoring).components
                    if c.label == "NHTSA complaints")
        self.assertEqual(quiet.value, 0.0)
        self.assertEqual(loud.value, -1.0)


if __name__ == "__main__":
    unittest.main()
