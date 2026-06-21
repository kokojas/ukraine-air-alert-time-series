# Air Alert Burden & Fatigue Analyzer

This project analyzes the time burden of air raid alerts in Ukraine at the oblast level. It focuses on alert duration, alert frequency, nighttime burden, rolling fatigue indicators, regional differences, co-alert similarity, and a cautious next-day burden benchmark.

The project does **not** predict attacks and does **not** provide safety advice. The baseline model is an analytical benchmark only; it is not for life-safety decisions. Always follow official alerts and local safety instructions.

## Why This Matters

Air raid alerts are not only discrete events. They create a time burden: interrupted sleep, disrupted study and work, repeated context switching, and alert fatigue. A regional analyst needs a reproducible way to compare that burden across regions and time without overstating what the data can prove.

## What The Project Builds

- `src/air_alerts/`: tested Python package
- `tests/`: unittest-based TDD and validation tests
- `notebooks/eda.ipynb`: transparent EDA notebook
- `docs/index.html`: static dashboard for GitHub Pages
- `reports/air_alerts_report.docx`: readable DOCX report with charts and a method diagram
- `data/processed/`: generated daily metrics, summaries, and baseline predictions

## Demo Outputs

- [Live static dashboard](https://kokojas.github.io/ukraine-air-alert-time-series/) generated from `docs/index.html`
- [Dashboard HTML source](https://github.com/kokojas/ukraine-air-alert-time-series/blob/main/docs/index.html)
- [DOCX report](https://github.com/kokojas/ukraine-air-alert-time-series/blob/main/reports/air_alerts_report.docx) with charts, key findings, method notes, and limitations
- [Daily oblast metrics CSV](https://github.com/kokojas/ukraine-air-alert-time-series/blob/main/data/processed/daily_oblast_metrics.csv)
- [Last-12-month summary CSV](https://github.com/kokojas/ukraine-air-alert-time-series/blob/main/data/processed/last12_oblast_summary.csv)
- [Next-day baseline predictions CSV](https://github.com/kokojas/ukraine-air-alert-time-series/blob/main/data/processed/next_day_baseline_predictions.csv)

## Data Source

Primary source: Vadimkin Ukrainian air raid sirens dataset, `volunteer_data_en.csv`.

I use the volunteer CSV for the main view because it stays at oblast level across the analysis period. The official CSV is more authoritative but becomes more granular in late 2025; directly unioning raion/hromada records into oblasts can overstate region-wide civilian burden.

Important caveats:

- Alert records are public-warning events, not direct attack records.
- Raw timestamps are UTC; this project computes metrics in Europe/Kyiv local time.
- Some volunteer records have imputed end times when the source marks them as `naive`.
- Overlapping alert records inside the same oblast are unioned before aggregation.
- From late 2025, official records become more granular in some places, so oblast aggregation is conservative.
- The baseline model is a benchmark, not a tactical or safety forecast.

## Method

1. Download or load the official alert CSV.
2. Parse alert intervals and convert them to Europe/Kyiv local time.
3. Union overlapping intervals inside each oblast to reduce double counting.
4. Split intervals into local calendar days.
5. Compute daily alert minutes, nighttime minutes, alert counts, and rolling 7-day/30-day burden.
6. Summarize the last 12 months as the main analytical window.
7. Produce focus-region views for Kyiv City, Kharkivska, Sumska, Donetska, and Lvivska oblasts.
8. Build a simple weighted baseline for next-day alert burden.
9. Generate a static dashboard, DOCX report, and processed CSVs.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m air_alerts.cli --refresh
python -m unittest discover -s tests
```

If the CSV is already available locally:

```bash
python -m air_alerts.cli --input-csv data/raw/vadimkin_alerts_en.csv
```

Open the dashboard:

```bash
open docs/index.html
```

## Baseline Model

The baseline predicts next-day alert minutes using a weighted blend of:

- recent 7-day mean,
- recent 30-day mean,
- same-weekday historical mean.

This is intentionally simple. The point is to create a transparent benchmark and backtest it, not to claim reliable defense prediction.

## Tests

The tests focus on behavior that can easily go wrong:

- merging overlapping alert intervals,
- splitting UTC intervals into Kyiv local days,
- counting nighttime burden,
- filling zero-alert days,
- creating end-to-end artifacts from a small sample CSV,
- keeping the baseline prediction labeled as a non-safety benchmark.

Run:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```
