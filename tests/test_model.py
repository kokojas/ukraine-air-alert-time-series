import unittest

import pandas as pd

from air_alerts.model import backtest_baseline, predict_next_day


class ModelTests(unittest.TestCase):
    def test_baseline_prediction_is_non_negative_and_labeled_as_benchmark(self) -> None:
        daily = pd.DataFrame(
            {
                "date": pd.date_range("2026-01-01", periods=45, freq="D").strftime("%Y-%m-%d"),
                "oblast": ["Kyiv City"] * 45,
                "alert_minutes": [0, 30, 60, 90, 45, 0, 120] * 6 + [30, 60, 0],
                "alert_count": [0, 1, 1, 2, 1, 0, 3] * 6 + [1, 1, 0],
                "night_minutes": [0, 10, 20, 30, 5, 0, 60] * 6 + [10, 20, 0],
            }
        )

        prediction = predict_next_day(daily, "Kyiv City")

        self.assertEqual(prediction["oblast"], "Kyiv City")
        self.assertGreaterEqual(prediction["predicted_alert_minutes"], 0)
        self.assertIn("benchmark", prediction["model_note"].lower())
        self.assertIn("not for life-safety", prediction["model_note"].lower())

    def test_backtest_returns_mae_for_each_region(self) -> None:
        daily = pd.DataFrame(
            {
                "date": pd.date_range("2026-01-01", periods=45, freq="D").strftime("%Y-%m-%d"),
                "oblast": ["Kyiv City"] * 45,
                "alert_minutes": [0, 30, 60, 90, 45, 0, 120] * 6 + [30, 60, 0],
                "alert_count": [0, 1, 1, 2, 1, 0, 3] * 6 + [1, 1, 0],
                "night_minutes": [0, 10, 20, 30, 5, 0, 60] * 6 + [10, 20, 0],
            }
        )

        result = backtest_baseline(daily, min_train_days=21)

        self.assertEqual(result.loc[0, "oblast"], "Kyiv City")
        self.assertGreaterEqual(result.loc[0, "mae_minutes"], 0)
        self.assertGreater(result.loc[0, "n_test_days"], 0)


if __name__ == "__main__":
    unittest.main()
