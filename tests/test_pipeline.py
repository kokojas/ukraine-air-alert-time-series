import tempfile
import unittest
from pathlib import Path

import pandas as pd

from air_alerts.pipeline import build_project


class PipelineTests(unittest.TestCase):
    def test_build_project_creates_submission_artifacts_from_sample_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample = root / "sample.csv"
            pd.DataFrame(
                [
                    {
                        "oblast": "Kyiv City",
                        "raion": "",
                        "hromada": "",
                        "level": "oblast",
                        "started_at": "2026-01-01 20:00:00+00:00",
                        "finished_at": "2026-01-01 21:00:00+00:00",
                        "source": "official",
                    },
                    {
                        "oblast": "Kharkivska oblast",
                        "raion": "",
                        "hromada": "",
                        "level": "oblast",
                        "started_at": "2026-01-02 01:00:00+00:00",
                        "finished_at": "2026-01-02 03:00:00+00:00",
                        "source": "official",
                    },
                ]
            ).to_csv(sample, index=False)

            artifacts = build_project(input_csv=sample, output_root=root)

            self.assertTrue(artifacts.dashboard_path.exists())
            self.assertTrue(artifacts.report_path.exists())
            self.assertTrue(artifacts.daily_metrics_path.exists())
            self.assertIn("not for life-safety decisions", artifacts.dashboard_path.read_text().lower())


if __name__ == "__main__":
    unittest.main()
