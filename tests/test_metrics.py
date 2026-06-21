import unittest
from datetime import datetime, timezone

import pandas as pd

from air_alerts.metrics import build_daily_metrics, complete_daily_grid, merge_intervals, split_interval_daily


def utc(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


class MetricsTests(unittest.TestCase):
    def test_merge_intervals_merges_overlapping_and_touching_ranges(self) -> None:
        intervals = [
            (utc("2026-01-01T10:00:00"), utc("2026-01-01T11:00:00")),
            (utc("2026-01-01T10:30:00"), utc("2026-01-01T12:00:00")),
            (utc("2026-01-01T12:00:00"), utc("2026-01-01T12:30:00")),
            (utc("2026-01-01T13:00:00"), utc("2026-01-01T14:00:00")),
        ]

        merged = merge_intervals(intervals)

        self.assertEqual(
            merged,
            [
                (utc("2026-01-01T10:00:00"), utc("2026-01-01T12:30:00")),
                (utc("2026-01-01T13:00:00"), utc("2026-01-01T14:00:00")),
            ],
        )

    def test_split_interval_daily_counts_local_night_minutes(self) -> None:
        parts = split_interval_daily(
            utc("2026-01-01T20:00:00"),
            utc("2026-01-02T06:00:00"),
            timezone_name="Europe/Kyiv",
        )

        self.assertEqual(len(parts), 2)
        self.assertEqual(str(parts[0].date), "2026-01-01")
        self.assertEqual(parts[0].alert_minutes, 120.0)
        self.assertEqual(parts[0].night_minutes, 120.0)
        self.assertEqual(str(parts[1].date), "2026-01-02")
        self.assertEqual(parts[1].alert_minutes, 480.0)
        self.assertEqual(parts[1].night_minutes, 420.0)

    def test_build_daily_metrics_uses_unioned_oblast_intervals(self) -> None:
        raw = pd.DataFrame(
            [
                {
                    "oblast": "Kyiv City",
                    "started_at": "2026-01-01 10:00:00+00:00",
                    "finished_at": "2026-01-01 11:00:00+00:00",
                    "level": "oblast",
                    "source": "official",
                },
                {
                    "oblast": "Kyiv City",
                    "started_at": "2026-01-01 10:30:00+00:00",
                    "finished_at": "2026-01-01 12:00:00+00:00",
                    "level": "raion",
                    "source": "official",
                },
                {
                    "oblast": "Kyiv City",
                    "started_at": "2026-01-01 13:00:00+00:00",
                    "finished_at": "2026-01-01 13:30:00+00:00",
                    "level": "oblast",
                    "source": "official",
                },
            ]
        )

        daily = build_daily_metrics(raw)

        row = daily.loc[(daily["oblast"] == "Kyiv City") & (daily["date"] == "2026-01-01")].iloc[0]
        self.assertEqual(row["alert_count"], 2)
        self.assertEqual(row["alert_minutes"], 150.0)

    def test_complete_daily_grid_adds_zero_burden_days(self) -> None:
        daily = pd.DataFrame(
            {
                "date": ["2026-01-01", "2026-01-03"],
                "oblast": ["Kyiv City", "Kyiv City"],
                "alert_minutes": [60.0, 30.0],
                "night_minutes": [10.0, 0.0],
                "alert_count": [1, 1],
                "alert_hours": [1.0, 0.5],
                "night_hours": [0.167, 0.0],
            }
        )

        complete = complete_daily_grid(daily, start_date="2026-01-01", end_date="2026-01-03")

        self.assertEqual(len(complete), 3)
        middle = complete.loc[complete["date"] == "2026-01-02"].iloc[0]
        self.assertEqual(middle["alert_minutes"], 0.0)
        self.assertEqual(middle["alert_count"], 0)


if __name__ == "__main__":
    unittest.main()
