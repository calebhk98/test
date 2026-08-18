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
        result = self._score(mileage=30000, distance_miles=70, cpo=True)
        self.assertEqual(len(result.components), 5)
        for component in result.components:
            self.assertTrue(component.detail, f"component {component.label} has no explanation")
        self.assertAlmostEqual(result.score, sum(c.value for c in result.components), places=2)
        self.assertIn("score", result.explain())

    def test_missing_fields_do_not_crash(self):
        result = score_listing({}, self.scoring)
        self.assertIsInstance(result.score, float)


if __name__ == "__main__":
    unittest.main()
