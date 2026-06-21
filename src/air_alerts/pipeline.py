"""End-to-end project pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from air_alerts.constants import DEFAULT_DATA_URL, FOCUS_REGIONS
from air_alerts.dashboard import write_dashboard
from air_alerts.data import download_official_csv, load_alerts
from air_alerts.metrics import add_rolling_metrics, build_daily_metrics, complete_daily_grid, summarize_period
from air_alerts.model import backtest_baseline, predict_all_next_day
from air_alerts.report import write_report
from air_alerts.visuals import write_bar_png, write_heatmap_png, write_line_png, write_pipeline_png


@dataclass(frozen=True)
class ProjectArtifacts:
    dashboard_path: Path
    report_path: Path
    daily_metrics_path: Path
    summary_path: Path
    predictions_path: Path
    notebook_path: Path


def build_project(
    *,
    input_csv: Path | None = None,
    output_root: Path = Path("."),
    refresh: bool = False,
    data_url: str = DEFAULT_DATA_URL,
) -> ProjectArtifacts:
    """Build all project artifacts from a CSV or the public dataset."""
    output_root = Path(output_root)
    raw_path = input_csv or download_official_csv(output_root / "data" / "raw" / "vadimkin_alerts_en.csv", url=data_url, force=refresh)
    raw = load_alerts(raw_path)
    analysis = build_analysis(raw)

    processed_dir = output_root / "data" / "processed"
    docs_dir = output_root / "docs"
    reports_dir = output_root / "reports"
    notebooks_dir = output_root / "notebooks"
    assets_dir = docs_dir / "assets"
    for directory in (processed_dir, docs_dir, reports_dir, notebooks_dir, assets_dir):
        directory.mkdir(parents=True, exist_ok=True)

    daily_metrics_path = processed_dir / "daily_oblast_metrics.csv"
    summary_path = processed_dir / "last12_oblast_summary.csv"
    predictions_path = processed_dir / "next_day_baseline_predictions.csv"
    analysis["daily"].to_csv(daily_metrics_path, index=False)
    analysis["summary_last12"].to_csv(summary_path, index=False)
    analysis["predictions"].to_csv(predictions_path, index=False)

    chart_paths = _write_chart_assets(analysis, assets_dir)
    dashboard_path = write_dashboard(analysis, docs_dir / "index.html")
    report_path = write_report(analysis, reports_dir / "air_alerts_report.docx", chart_paths)
    notebook_path = write_notebook(notebooks_dir / "eda.ipynb")

    return ProjectArtifacts(
        dashboard_path=dashboard_path,
        report_path=report_path,
        daily_metrics_path=daily_metrics_path,
        summary_path=summary_path,
        predictions_path=predictions_path,
        notebook_path=notebook_path,
    )


def build_analysis(raw: pd.DataFrame, *, focus_regions: list[str] | None = None) -> dict[str, object]:
    focus_regions = focus_regions or FOCUS_REGIONS
    oblasts = sorted(raw["oblast"].dropna().unique())
    daily_active = build_daily_metrics(raw)
    if daily_active.empty:
        raise ValueError("no valid alert intervals found")

    complete = complete_daily_grid(
        daily_active,
        oblasts=oblasts,
        start_date=daily_active["date"].min(),
        end_date=daily_active["date"].max(),
    )
    daily = add_rolling_metrics(complete)
    latest = pd.to_datetime(daily["date"].max())
    last12_start = (latest - pd.DateOffset(months=12) + pd.Timedelta(days=1)).date().isoformat()

    summary_last12 = summarize_period(daily, start_date=last12_start)
    summary_history = summarize_period(daily)
    available_focus = [region for region in focus_regions if region in set(daily["oblast"])]
    focus_daily_last12 = daily[(daily["oblast"].isin(available_focus)) & (daily["date"] >= last12_start)].copy()
    focus_corr = _focus_correlation(focus_daily_last12)
    predictions = predict_all_next_day(daily)
    backtest = backtest_baseline(daily, min_train_days=min(30, max(2, daily["date"].nunique() // 3)))

    return {
        "daily": daily,
        "summary_last12": summary_last12,
        "summary_history": summary_history,
        "focus_daily_last12": focus_daily_last12,
        "focus_corr": focus_corr,
        "predictions": predictions,
        "backtest": backtest,
        "meta": {
            "latest_date": latest.date().isoformat(),
            "first_date": daily["date"].min(),
            "last12_start": last12_start,
            "focus_regions": available_focus,
            "oblast_count": len(oblasts),
            "raw_rows": len(raw),
        },
    }


def write_notebook(path: Path) -> Path:
    """Write a small transparent EDA notebook."""
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Air Alert Burden EDA\n",
                    "\n",
                    "This notebook reruns the core analysis and displays the main tables. "
                    "The full artifact build is available through the CLI.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "from pathlib import Path\n",
                    "import pandas as pd\n",
                    "from air_alerts.data import load_alerts\n",
                    "from air_alerts.pipeline import build_analysis\n",
                    "\n",
                    "raw = load_alerts(Path('../data/raw/official_data_en.csv'))\n",
                    "analysis = build_analysis(raw)\n",
                    "analysis['meta']\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "analysis['summary_last12'].head(10)\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "analysis['predictions'].head(10)\n",
                ],
            },
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(notebook, indent=2), encoding="utf-8")
    return path


def _write_chart_assets(analysis: dict[str, object], assets_dir: Path) -> dict[str, Path]:
    summary = analysis["summary_last12"]
    focus_daily = analysis["focus_daily_last12"]
    corr = analysis["focus_corr"]
    return {
        "burden": write_bar_png(
            summary,
            assets_dir / "top_oblast_burden.png",
            label_col="oblast",
            value_col="total_alert_hours",
            title="Top oblasts by alert burden",
        ),
        "focus": write_line_png(
            focus_daily,
            assets_dir / "focus_rolling_burden.png",
            title="Focus regions: rolling 30-day alert burden",
            y_col="rolling_30d_alert_hours",
        ),
        "corr": write_heatmap_png(corr, assets_dir / "focus_correlation.png", title="Co-alert similarity"),
        "pipeline": write_pipeline_png(assets_dir / "pipeline.png"),
    }


def _focus_correlation(focus_daily: pd.DataFrame) -> pd.DataFrame:
    if focus_daily.empty:
        return pd.DataFrame()
    pivot = focus_daily.pivot_table(index="date", columns="oblast", values="alert_hours", fill_value=0)
    if pivot.shape[1] < 2:
        return pd.DataFrame()
    return pivot.corr().fillna(0).round(3)
