"""
Tests. Run with: PYTHONPATH=. python3 -m unittest discover tests -v

The statistics are the part of this model that would fail silently if it were
wrong, so that is where most of the coverage sits.
"""

import unittest

from gate import evals
from gate.intake import UseCase, score
from gate.requirements import Requirement, classify


BASE = {
    "volume": 3, "time_displaced": 3, "strategic_pull": 3,
    "consequence_of_error": 3, "ground_truth": 3,
    "verifiability": 3, "regulatory_scope": 3,
}


def uc(**overrides):
    scores = dict(BASE, **overrides)
    return UseCase(id="T", title="t", function="f", sponsor="s", scores=scores)


class TestWilson(unittest.TestCase):
    def test_perfect_small_sample_is_not_certainty(self):
        # 10 for 10 does not license a claim of 95%. This is the single most
        # common mistake in AI demos and the reason the bound is used at all.
        lb = evals.wilson_lower_bound(10, 10, 0.95)
        self.assertLess(lb, 0.95)
        self.assertGreater(lb, 0.70)

    def test_bound_tightens_with_n(self):
        a = evals.wilson_lower_bound(96, 100, 0.95)
        b = evals.wilson_lower_bound(960, 1000, 0.95)
        self.assertLess(a, b)

    def test_bound_never_exceeds_one_or_falls_below_zero(self):
        self.assertLessEqual(evals.wilson_lower_bound(50, 50, 0.99), 1.0)
        self.assertGreaterEqual(evals.wilson_lower_bound(0, 50, 0.99), 0.0)

    def test_higher_confidence_gives_lower_bound(self):
        self.assertLess(
            evals.wilson_lower_bound(96, 100, 0.99),
            evals.wilson_lower_bound(96, 100, 0.90),
        )


class TestSizing(unittest.TestCase):
    def test_no_headroom_is_unprovable(self):
        self.assertIsNone(evals.required_sample_size(0.95, 0.95))
        self.assertIsNone(evals.required_sample_size(0.99, 0.95))

    def test_more_headroom_needs_fewer_samples(self):
        tight = evals.required_sample_size(0.95, 0.96)
        loose = evals.required_sample_size(0.95, 0.99)
        self.assertGreater(tight, loose)

    def test_higher_confidence_needs_more_samples(self):
        self.assertGreater(
            evals.required_sample_size(0.95, 0.97, 0.99),
            evals.required_sample_size(0.95, 0.97, 0.90),
        )

    def test_sizing_actually_clears_the_threshold(self):
        for threshold, expected in [(0.90, 0.95), (0.95, 0.97), (0.80, 0.90)]:
            n = evals.required_sample_size(threshold, expected, 0.95)
            lb = evals.wilson_lower_bound(round(expected * n), n, 0.95)
            self.assertGreaterEqual(lb, threshold, f"{threshold}/{expected}")


class TestRelease(unittest.TestCase):
    def test_one_failure_blocks_release(self):
        good = evals.run_criterion("A", "accuracy", 0.90, 990, 1000)
        bad = evals.run_criterion("B", "accuracy", 0.90, 700, 1000)
        decision, _ = evals.release_decision([good, bad])
        self.assertEqual(decision, "HOLD")

    def test_underpowered_pass_does_not_release(self):
        # Observed above threshold, sample too small to support it.
        r = evals.run_criterion("A", "accuracy", 0.90, 19, 20)
        self.assertGreater(r.observed, r.threshold)
        self.assertFalse(r.passed)
        decision, _ = evals.release_decision([r])
        self.assertEqual(decision, "HOLD")

    def test_all_pass_releases(self):
        rs = [evals.run_criterion("A", "accuracy", 0.90, 990, 1000)]
        self.assertEqual(evals.release_decision(rs)[0], "RELEASE")


class TestIntakeGates(unittest.TestCase):
    def test_no_ground_truth_plus_no_check_is_gated_regardless_of_value(self):
        r = score(uc(volume=5, time_displaced=5, strategic_pull=5,
                     ground_truth=5, verifiability=5))
        self.assertEqual(r.disposition, "REFRAME")
        self.assertGreater(r.value, 90)

    def test_high_consequence_plus_no_check_is_gated(self):
        r = score(uc(volume=5, time_displaced=5, strategic_pull=5,
                     consequence_of_error=5, verifiability=5, ground_truth=1))
        self.assertEqual(r.disposition, "REFRAME")

    def test_clean_high_value_case_builds(self):
        r = score(uc(volume=5, time_displaced=5, strategic_pull=5,
                     consequence_of_error=1, ground_truth=1,
                     verifiability=1, regulatory_scope=1))
        self.assertEqual(r.disposition, "BUILD")

    def test_rejects_bad_scores(self):
        with self.assertRaises(ValueError):
            score(uc(volume=7))
        with self.assertRaises(ValueError):
            bad = uc()
            del bad.scores["volume"]
            score(bad)


class TestRequirements(unittest.TestCase):
    def _req(self, text, **kw):
        return Requirement(id="R", use_case_id="U", text=text, source="s", **kw)

    def test_adjective_without_metric_is_untestable(self):
        c = classify(self._req("The system shall produce accurate summaries."))
        self.assertEqual(c.kind, "UNTESTABLE")
        self.assertTrue(c.proposed_rewrite)

    def test_logging_requirement_is_deterministic(self):
        c = classify(self._req(
            "The system shall log the model version for every request."))
        self.assertEqual(c.kind, "DETERMINISTIC")

    def test_metric_forces_statistical_over_grammar(self):
        c = classify(self._req(
            "The system shall reject out-of-scope documents.",
            metric="refusal rate", threshold=0.98, expected=0.99))
        self.assertEqual(c.kind, "STATISTICAL")
        self.assertIn("override", c.reason)

    def test_metric_without_threshold_raises(self):
        with self.assertRaises(ValueError):
            classify(self._req("x", metric="accuracy"))

    def test_unknown_metric_raises(self):
        with self.assertRaises(ValueError):
            classify(self._req("x", metric="vibes", threshold=0.9, expected=0.95))


if __name__ == "__main__":
    unittest.main()
