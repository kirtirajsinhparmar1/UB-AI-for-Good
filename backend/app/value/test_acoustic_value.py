import unittest

from app.value import compute_acoustic_value_delta, load_default_demo_policy


class AcousticValueTests(unittest.TestCase):
    def test_rejects_invalid_base_values(self) -> None:
        for value in (0, -1, float("nan"), float("inf")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                compute_acoustic_value_delta(value, 20)

    def test_rejects_scores_outside_range(self) -> None:
        for score in (-1, 101):
            with self.subTest(score=score), self.assertRaises(ValueError):
                compute_acoustic_value_delta(15_000, score)

    def test_score_zero_and_one_hundred_work(self) -> None:
        low = compute_acoustic_value_delta(15_000, 0)
        high = compute_acoustic_value_delta(15_000, 100)
        self.assertEqual(low.delta_pct, 1.0)
        self.assertEqual(low.risk_band, "low")
        self.assertEqual(high.delta_pct, -15.0)
        self.assertEqual(high.risk_band, "high")

    def test_adjusted_value_is_never_negative(self) -> None:
        result = compute_acoustic_value_delta(0.01, 100)
        self.assertGreaterEqual(result.adjusted_wholesale_value, 0)

    def test_value_never_increases_as_risk_increases(self) -> None:
        values = [compute_acoustic_value_delta(15_000, score).adjusted_wholesale_value for score in range(101)]
        self.assertTrue(all(later <= earlier for earlier, later in zip(values, values[1:])))

    def test_results_are_deterministic(self) -> None:
        first = compute_acoustic_value_delta(15_000, 82)
        second = compute_acoustic_value_delta(15_000, 82)
        self.assertEqual(first, second)

    def test_default_policy_loads_with_prototype_metadata(self) -> None:
        policy = load_default_demo_policy()
        self.assertEqual(policy.version, "demo-v1")
        self.assertEqual(policy.policy_type, "prototype_demo_policy")
        self.assertIn("Illustrative hackathon policy", policy.note)
        self.assertEqual(len(policy.breakpoints), 6)

    def test_delta_arithmetic_and_example_calculation(self) -> None:
        result = compute_acoustic_value_delta(15_000, 82)
        self.assertEqual(result.delta_pct, -8.7)
        self.assertEqual(result.delta_amount, -1_305.0)
        self.assertEqual(result.adjusted_wholesale_value, 13_695.0)
        self.assertEqual(
            result.adjusted_wholesale_value,
            round(result.base_wholesale_value + result.delta_amount, 2),
        )
        self.assertEqual(result.policy_type, "prototype_demo_policy")
        self.assertIn("discount", result.rationale)


if __name__ == "__main__":
    unittest.main()
