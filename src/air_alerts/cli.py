"""Command-line interface for building the project artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from air_alerts.pipeline import build_project


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Ukraine air alert burden analysis artifacts.")
    parser.add_argument("--input-csv", type=Path, default=None, help="Optional local official_data_en.csv path.")
    parser.add_argument("--output-root", type=Path, default=Path("."), help="Project root for generated artifacts.")
    parser.add_argument("--refresh", action="store_true", help="Download the public CSV even if cached.")
    args = parser.parse_args(argv)

    artifacts = build_project(input_csv=args.input_csv, output_root=args.output_root, refresh=args.refresh)
    print(f"Dashboard: {artifacts.dashboard_path}")
    print(f"Report: {artifacts.report_path}")
    print(f"Daily metrics: {artifacts.daily_metrics_path}")
    print(f"Summary: {artifacts.summary_path}")
    print(f"Predictions: {artifacts.predictions_path}")
    print(f"Notebook: {artifacts.notebook_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
