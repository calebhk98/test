"""Market appraisal, trends, and the deal grading that hangs off them."""

import random
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from carmon import db, market
from carmon.config import load_config
from carmon.pipeline import refresh_market_values
from carmon.scoring import score_listing


def seed_market(conn, count=45, make="Toyota", model="Corolla", base=21000, slope=0.10,
                seen="2026-08-18", start=0, seed=7):
    """A synthetic market with a known truth: price = base - slope*miles + 800/model year."""
    rng = random.Random(seed)
    for index in range(count):
        year = rng.choice([2021, 2022, 2023])
        mileage = rng.randrange(15000, 58000, 500)
        price = int(base - slope * mileage + 800 * (year - 2021) + rng.gauss(0, 350))
        db.upsert_listing(conn, {
            "vin": f"{make[:2].upper()}{model[:2].upper()}{start + index:013d}",
            "make": make, "model": model, "year": year, "mileage": mileage,
            "price_current": price, "distance_miles": 25, "source": "marketcheck",
        }, seen)


class AppraisalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.config = load_config()
        self.config.data["paths"]["db"] = str(self.tmp / "m.db")
        self.conn = db.init_db(self.config.db_path)
        seed_market(self.conn)

    def tearDown(self):
        self.conn.close()

    def _appraise(self, **car):
        base = {"make": "Toyota", "model": "Corolla", "year": 2022, "mileage": 35000}
        base.update(car)
        return market.appraise(self.conn, base, self.config, today=date(2026, 8, 19))

    def test_recovers_the_true_depreciation_rate(self):
        """The generated market loses $100 per 1,000 miles; the fit should find that."""
        result = self._appraise(price_current=18000)
        self.assertAlmostEqual(result.dollars_per_1k_miles, 100, delta=15)
        self.assertGreater(result.r_squared, 0.8)

    def test_recovers_the_model_year_premium(self):
        result = self._appraise(price_current=18000)
        self.assertAlmostEqual(result.dollars_per_model_year, 800, delta=200)

    def test_a_cheap_car_grades_well_and_an_expensive_one_badly(self):
        expected = self._appraise(price_current=18000).expected_price
        cheap = self._appraise(price_current=int(expected * 0.85))
        dear = self._appraise(price_current=int(expected * 1.15))
        self.assertEqual(cheap.grade, "great deal")
        self.assertIn(dear.grade, ("above market", "well above market"))
        self.assertLess(cheap.delta, 0)
        self.assertGreater(dear.delta, 0)

    def test_a_market_priced_car_is_fair(self):
        expected = self._appraise(price_current=18000).expected_price
        result = self._appraise(price_current=int(expected))
        self.assertEqual(result.grade, "fair price")
        self.assertLess(abs(result.delta_pct), 5)

    def test_higher_mileage_lowers_the_expectation(self):
        low = self._appraise(mileage=20000, price_current=18000).expected_price
        high = self._appraise(mileage=55000, price_current=18000).expected_price
        self.assertGreater(low, high)
        self.assertAlmostEqual(low - high, 0.10 * 35000, delta=800)

    def test_percentile_positions_the_price_among_comparables(self):
        cheap = self._appraise(price_current=14000)
        dear = self._appraise(price_current=22000)
        self.assertLess(cheap.percentile, 15)
        self.assertGreater(dear.percentile, 85)

    def test_sample_size_and_confidence_are_always_reported(self):
        result = self._appraise(price_current=18000)
        self.assertGreater(result.sample_size, 20)
        self.assertEqual(result.confidence, "good")
        self.assertEqual(result.basis_level, "model_year")
        self.assertIn("comparable listings", result.summary())

    def test_thin_data_is_labelled_thin(self):
        conn = db.init_db(self.tmp / "thin.db")
        seed_market(conn, count=4)
        result = market.appraise(conn, {"make": "Toyota", "model": "Corolla", "year": 2022,
                                        "mileage": 35000, "price_current": 18000}, self.config)
        self.assertLessEqual(result.sample_size, 4)
        self.assertIn(result.confidence, ("very low", "low"))
        self.assertEqual(result.method, "median of comparables")
        self.assertTrue(result.notes)
        conn.close()

    def test_wrong_model_comparison_is_capped_to_very_low_confidence(self):
        """A big sample of the wrong cars is not confidence — this was a real trap."""
        result = self._appraise(make="Kia", model="Forte", price_current=15000)
        self.assertEqual(result.basis_level, "all")
        self.assertEqual(result.confidence, "very low")
        self.assertTrue(any("different mix of models" in note for note in result.notes))

    def test_no_data_at_all_returns_an_honest_empty_result(self):
        conn = db.init_db(self.tmp / "empty.db")
        result = market.appraise(conn, {"make": "Toyota", "model": "Corolla", "year": 2022,
                                        "mileage": 35000, "price_current": 18000}, self.config)
        self.assertIsNone(result.expected_price)
        self.assertEqual(result.sample_size, 0)
        self.assertIn("Not enough comparable data", result.summary())
        conn.close()

    def test_a_car_is_never_compared_against_itself(self):
        db.upsert_listing(self.conn, {"vin": "SELF00000000001", "make": "Toyota", "model": "Corolla",
                                      "year": 2022, "mileage": 35000, "price_current": 9999,
                                      "source": "marketcheck"}, "2026-08-18")
        result = market.appraise_vin(self.conn, "SELF00000000001", self.config)
        self.assertNotIn("SELF00000000001", [row["vin"] for row in
                                             market.comparables(self.conn, "Toyota", "Corolla",
                                                                exclude_vin="SELF00000000001")])
        self.assertLess(result.delta_pct, -20, "an absurdly cheap car should read as far below market")

    def test_estimates_stay_inside_a_sane_range(self):
        result = self._appraise(mileage=500000, price_current=5000)
        self.assertGreater(result.expected_price, 0)

    def test_missing_price_still_gives_an_expectation(self):
        result = self._appraise()
        self.assertIsNotNone(result.expected_price)
        self.assertIsNone(result.grade)
        self.assertIn("Expected about", result.summary())

    def test_sold_listings_count_as_market_evidence(self):
        self.conn.execute("UPDATE listings SET active = 0")
        self.conn.commit()
        result = self._appraise(price_current=18000)
        self.assertGreater(result.sample_size, 20, "sold cars are the best evidence of real prices")

    def test_demo_rows_never_pollute_the_market(self):
        db.upsert_listing(self.conn, {"vin": "DEMOMKT00000001", "make": "Toyota", "model": "Corolla",
                                      "year": 2022, "mileage": 35000, "price_current": 1,
                                      "source": "demo"}, "2026-08-18")
        vins = [row["vin"] for row in market.comparables(self.conn, "Toyota", "Corolla")]
        self.assertNotIn("DEMOMKT00000001", vins)


class TrendTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.config = load_config()
        self.config.data["paths"]["db"] = str(self.tmp / "t.db")
        self.conn = db.init_db(self.config.db_path)

    def tearDown(self):
        self.conn.close()

    def test_trend_tracks_a_falling_market(self):
        for offset, month in enumerate(("2026-06-15", "2026-07-15", "2026-08-15")):
            seed_market(self.conn, count=12, base=22000 - 500 * offset, seen=month,
                        start=offset * 100, seed=3)
        trend = market.price_trend(self.conn, months=6)
        self.assertEqual(len(trend), 3)
        self.assertGreater(trend[0]["median_price"], trend[-1]["median_price"])
        self.assertLess(trend[-1]["change_vs_previous"], 0)
        self.assertIsNotNone(trend[-1]["change_pct"])

    def test_trend_is_empty_before_any_history(self):
        self.assertEqual(market.price_trend(self.conn), [])

    def test_days_on_market_needs_vanished_listings(self):
        seed_market(self.conn, count=6, seen="2026-08-01")
        empty = market.days_on_market(self.conn)
        self.assertEqual(empty["sample_size"], 0)
        self.assertIn("fills in", empty["note"])

        self.conn.execute("UPDATE listings SET active = 0, last_seen = '2026-08-15'")
        self.conn.commit()
        measured = market.days_on_market(self.conn)
        self.assertEqual(measured["sample_size"], 6)
        self.assertAlmostEqual(measured["median_days"], 14, delta=1)

    def test_price_cut_stats(self):
        seed_market(self.conn, count=10, seen="2026-08-01")
        rows = self.conn.execute("SELECT vin, price_current FROM listings LIMIT 4").fetchall()
        for row in rows:
            db.upsert_listing(self.conn, {"vin": row["vin"], "price_current": row["price_current"] - 900},
                              "2026-08-10")
        cuts = market.price_cut_stats(self.conn)
        self.assertEqual(cuts["tracked"], 10)
        self.assertEqual(cuts["cut_count"], 4)
        self.assertEqual(cuts["cut_share_pct"], 40.0)
        self.assertAlmostEqual(cuts["median_cut"], 900, delta=1)

    def test_model_summary_reports_per_model_stats(self):
        seed_market(self.conn, count=20, make="Toyota", model="Corolla", seed=1)
        seed_market(self.conn, count=20, make="Honda", model="Civic", base=22500, start=500, seed=2)
        summaries = market.model_summary(self.conn)
        self.assertEqual({(row["make"], row["model"]) for row in summaries},
                         {("Toyota", "Corolla"), ("Honda", "Civic")})
        for row in summaries:
            self.assertGreater(row["sample_size"], 10)
            self.assertIsNotNone(row["dollars_per_1k_miles"])

    def test_market_report_has_everything_the_uis_need(self):
        seed_market(self.conn, count=20)
        report = market.market_report(self.conn, config=self.config)
        for key in ("listings_tracked", "trend", "models", "days_on_market",
                    "price_cuts", "best_deals", "data_note"):
            self.assertIn(key, report)
        self.assertIn("need weeks of history", report["data_note"])


class MarketScoringTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.config = load_config()
        self.config.data["paths"]["db"] = str(self.tmp / "s.db")
        self.conn = db.init_db(self.config.db_path)
        seed_market(self.conn, count=30)

    def tearDown(self):
        self.conn.close()

    def test_below_market_listings_score_higher(self):
        listing = {"make": "Toyota", "model": "Corolla", "year": 2022, "mileage": 35000,
                   "price_current": 17000, "market_sample_size": 30}
        cheap = score_listing({**listing, "market_delta_pct": -12}, self.config.scoring)
        dear = score_listing({**listing, "market_delta_pct": 12}, self.config.scoring)
        self.assertAlmostEqual(cheap.score - dear.score, 3.0, places=1)

    def test_thin_samples_do_not_move_the_score(self):
        component = next(
            c for c in score_listing(
                {"make": "Toyota", "model": "Corolla", "market_delta_pct": -20, "market_sample_size": 2},
                self.config.scoring).components
            if c.label == "vs market"
        )
        self.assertEqual(component.value, 0.0)
        self.assertIn("too thin to score", component.detail)

    def test_no_market_data_is_neutral(self):
        component = next(c for c in score_listing({"make": "Kia", "model": "Forte"},
                                                  self.config.scoring).components
                         if c.label == "vs market")
        self.assertEqual(component.value, 0.0)
        self.assertIn("no market comparison", component.detail)

    def test_refresh_stores_appraisals_and_rescores(self):
        summary = refresh_market_values(self.config, self.conn)
        self.assertEqual(summary["listings_appraised"], 30)
        row = self.conn.execute(
            "SELECT market_expected_price, market_delta_pct, market_grade, market_sample_size, "
            "score_breakdown FROM listings WHERE market_delta_pct IS NOT NULL LIMIT 1"
        ).fetchone()
        self.assertIsNotNone(row["market_expected_price"])
        self.assertIsNotNone(row["market_grade"])
        self.assertIn("vs market", row["score_breakdown"])

    def test_best_deals_are_ranked_by_how_far_below_expected(self):
        refresh_market_values(self.config, self.conn)
        deals = market.best_deals(self.conn, limit=5, config=self.config)
        self.assertTrue(deals)
        deltas = [item["appraisal"]["delta_pct"] for item in deals]
        self.assertEqual(deltas, sorted(deltas))
        self.assertLess(deltas[0], 0)


class LeastSquaresTests(unittest.TestCase):
    def test_fits_a_known_line(self):
        xs = [[float(x)] for x in range(20)]
        ys = [3.0 * x[0] + 7.0 for x in xs]
        fit = market.weighted_least_squares(xs, ys)
        self.assertAlmostEqual(fit["coefficients"][0], 7.0, places=4)
        self.assertAlmostEqual(fit["coefficients"][1], 3.0, places=4)
        self.assertAlmostEqual(fit["r_squared"], 1.0, places=4)

    def test_refuses_to_fit_too_few_points(self):
        self.assertIsNone(market.weighted_least_squares([[1.0], [2.0]], [1.0, 2.0]))

    def test_singular_input_returns_none(self):
        xs = [[1.0], [1.0], [1.0], [1.0]]
        self.assertIsNone(market.weighted_least_squares(xs, [1.0, 2.0, 3.0, 4.0]))

    def test_recency_weighting_favours_recent_observations(self):
        self.assertAlmostEqual(market.age_weight("2026-07-05", 45, date(2026, 8, 19)), 0.5, places=1)
        self.assertEqual(market.age_weight("2026-08-19", 45, date(2026, 8, 19)), 1.0)
        self.assertEqual(market.age_weight(None, 45), 1.0)


if __name__ == "__main__":
    unittest.main()
