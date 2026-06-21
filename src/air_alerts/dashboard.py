"""Static HTML dashboard renderer."""

from __future__ import annotations

from html import escape
from pathlib import Path

import pandas as pd

from air_alerts.constants import DISCLAIMER, PROJECT_TITLE, SOURCE_LEDGER
from air_alerts.visuals import bar_chart_svg, heatmap_svg, line_chart_svg


def write_dashboard(analysis: dict[str, object], output_path: Path) -> Path:
    summary = analysis["summary_last12"]
    focus_daily = analysis["focus_daily_last12"]
    corr = analysis["focus_corr"]
    predictions = analysis["predictions"]
    backtest = analysis["backtest"]
    meta = analysis["meta"]

    top_region = _top_value(summary, "oblast", default="No data")
    top_hours = _top_value(summary, "total_alert_hours", default=0.0)
    night_region = _top_by(summary, "total_night_hours")

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(PROJECT_TITLE)}</title>
  <style>
    :root {{ --text:#111827; --muted:#6b7280; --line:#e5e7eb; --bg:#f8fafc; --accent:#2563eb; }}
    body {{ margin:0; font-family: Arial, Helvetica, sans-serif; color:var(--text); background:#fff; line-height:1.5; }}
    header {{ padding:36px 28px 24px; border-bottom:1px solid var(--line); background:var(--bg); }}
    main {{ max-width:1120px; margin:0 auto; padding:24px; }}
    h1 {{ margin:0 0 8px; font-size:34px; letter-spacing:0; }}
    h2 {{ margin:30px 0 12px; font-size:24px; }}
    .subtitle {{ max-width:880px; color:var(--muted); font-size:16px; }}
    .disclaimer {{ margin-top:16px; padding:12px 14px; border-left:4px solid #dc2626; background:#fff7ed; font-weight:700; }}
    .kpis {{ display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); gap:12px; margin:22px 0; }}
    .kpi {{ border:1px solid var(--line); border-radius:8px; padding:14px; background:#fff; }}
    .kpi span {{ display:block; color:var(--muted); font-size:12px; text-transform:uppercase; }}
    .kpi strong {{ display:block; margin-top:6px; font-size:20px; }}
    .panel {{ border:1px solid var(--line); border-radius:8px; padding:16px; margin:16px 0; overflow-x:auto; }}
    table {{ width:100%; border-collapse:collapse; font-size:14px; }}
    th, td {{ border-bottom:1px solid var(--line); padding:8px; text-align:left; }}
    th {{ background:#f9fafb; }}
    .note {{ color:var(--muted); font-size:13px; }}
    @media (max-width:800px) {{ .kpis {{ grid-template-columns:1fr 1fr; }} h1 {{ font-size:28px; }} }}
    @media (max-width:560px) {{ main {{ padding:16px; }} .kpis {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
<header>
  <h1>{escape(PROJECT_TITLE)}</h1>
  <p class="subtitle">Time-series analysis of air raid alert burden in Ukraine: duration, frequency, nighttime burden, regional differences, co-alert correlations, and a cautious baseline benchmark.</p>
  <p class="disclaimer">{escape(DISCLAIMER)}</p>
</header>
<main>
  <section class="kpis">
    <div class="kpi"><span>Latest data date</span><strong>{escape(meta["latest_date"])}</strong></div>
    <div class="kpi"><span>Main window</span><strong>{escape(meta["last12_start"])} to {escape(meta["latest_date"])}</strong></div>
    <div class="kpi"><span>Highest burden</span><strong>{escape(str(top_region))}</strong></div>
    <div class="kpi"><span>Top-region hours</span><strong>{float(top_hours):.1f}h</strong></div>
  </section>

  <section class="panel">
    {bar_chart_svg(summary, label_col="oblast", value_col="total_alert_hours", title="Top oblasts by alert burden in the last 12 months", suffix="h")}
    <p class="note">Intervals inside each oblast are unioned before aggregation to reduce overlap double-counting.</p>
  </section>

  <section class="panel">
    {line_chart_svg(focus_daily, title="Focus regions: rolling 30-day alert burden", y_col="rolling_30d_alert_hours")}
    <p class="note">Focus regions: {escape(', '.join(meta["focus_regions"]))}.</p>
  </section>

  <section class="panel">
    {bar_chart_svg(summary.sort_values("night_share", ascending=False), label_col="oblast", value_col="night_share", title="Night burden share by oblast", suffix="")}
    <p class="note">Night is defined as 22:00-07:00 Europe/Kyiv local time.</p>
  </section>

  <section class="panel">
    {heatmap_svg(corr, title="Co-alert similarity among focus regions")}
    <p class="note">Correlation uses daily alert hours in the main analysis window.</p>
  </section>

  <h2>Baseline benchmark</h2>
  <p class="note">{escape(DISCLAIMER)}</p>
  {_table(predictions.head(10), ["oblast", "target_date", "predicted_alert_hours", "model"])}
  <h2>Backtest summary</h2>
  {_table(backtest.head(10), ["oblast", "mae_hours", "n_test_days"])}

  <h2>Source and method ledger</h2>
  {_source_table()}
</main>
</body>
</html>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path


def _table(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return '<p class="note">No data available.</p>'
    visible = frame[[column for column in columns if column in frame.columns]].copy()
    head = "".join(f"<th>{escape(column)}</th>" for column in visible.columns)
    rows = []
    for row in visible.itertuples(index=False):
        cells = "".join(f"<td>{escape(str(value))}</td>" for value in row)
        rows.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def _source_table() -> str:
    rows = []
    for item in SOURCE_LEDGER:
        rows.append(
            "<tr>"
            f"<td>{escape(item['layer'])}</td>"
            f"<td>{escape(item['source'])}</td>"
            f"<td>{escape(item['status'])}</td>"
            f"<td>{escape(item['caveat'])}</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr><th>Layer</th><th>Source</th><th>Status</th><th>Caveat</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def _top_value(frame: pd.DataFrame, column: str, *, default: object) -> object:
    if frame.empty or column not in frame.columns:
        return default
    return frame.iloc[0][column]


def _top_by(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame.columns:
        return "No data"
    return str(frame.sort_values(column, ascending=False).iloc[0]["oblast"])
