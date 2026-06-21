# Product Requirements Document

## Problem Statement

Regional analysts need a reproducible way to understand how the time burden of air raid alerts in Ukraine changes across regions and over time. The project should emphasize alert burden and fatigue rather than tactical prediction: which oblasts experience the highest duration and frequency, how much of the burden happens at night, how the last 12 months compare with historical context, and whether a cautious baseline indicator can summarize likely alert burden tomorrow.

## Solution

Build a small Python project that downloads public air raid alert history, normalizes timestamps to Kyiv local time, aggregates alerts to oblast-level daily metrics, and generates reproducible artifacts: a CLI, a static HTML dashboard, a DOCX report, a transparent EDA notebook, and tests. The project will include a baseline benchmark model for next-day alert burden with a visible disclaimer that it is not suitable for life-safety decisions.

## User Stories

1. As a regional analyst, I want daily alert-duration metrics by oblast, so that I can compare burden across Ukraine.
2. As a regional analyst, I want alert frequency by oblast, so that I can distinguish many short alerts from fewer long alerts.
3. As a researcher, I want nighttime alert burden, so that I can study likely sleep disruption.
4. As a researcher, I want rolling 7-day and 30-day burden, so that I can see sustained fatigue rather than only isolated spikes.
5. As a reviewer, I want a clear caveat about data limitations, so that I can judge whether the analysis is responsible.
6. As a reviewer, I want a public GitHub repository with reproducible commands, so that I can rerun the project.
7. As a user, I want a static HTML dashboard, so that I can open the visualization through GitHub Pages without running Python.
8. As a user, I want a DOCX report, so that I can read the findings in a familiar document format.
9. As a researcher, I want focus-region views for Kyiv City, Kharkivska, Sumska, Donetska, and Lvivska oblasts, so that the national picture has concrete examples.
10. As a developer, I want tests for interval merging and night-hour calculations, so that the most error-prone time-series logic is protected.
11. As a reviewer, I want a baseline model and backtest metrics, so that I can see a careful analytical benchmark without unsafe claims.

## Implementation Decisions

- Primary dataset: Vadimkin Ukrainian air raid sirens dataset, volunteer English CSV, because it remains oblast-level across the analysis period.
- Official CSV caveat: after late 2025, official records become more granular, so naive oblast union can overstate region-wide civilian burden.
- Time basis: raw data is UTC; analytical metrics are computed in Europe/Kyiv local time.
- Geographic basis: aggregate to oblast-level using interval union per oblast to avoid double-counting overlapping local records.
- Main scope: last 12 months as the primary analytical window, with all available history used for context.
- Focus regions: Kyiv City, Kharkivska oblast, Sumska oblast, Donetska oblast, and Lvivska oblast.
- Baseline model: weighted blend of recent 7-day mean, 30-day mean, and same-weekday historical mean; reported as a benchmark only.
- Artifacts: Python package, CLI, static HTML dashboard, DOCX report, EDA notebook, README, and tests.
- Visualization style: direct labels, source notes, caveats near the charts, no sensational conflict imagery.

## Testing Decisions

- Tests should verify public behavior through public functions and CLI-level generation where practical.
- Time interval tests cover overlapping interval union, daily splitting, and night-window overlap.
- Aggregation tests cover oblast-level metrics from sample alert records.
- Model tests cover non-negative predictions and backtest output shape.
- Report-generation smoke tests can be lightweight because the main risk is analytical correctness rather than DOCX styling.

## Out of Scope

- Tactical prediction of attacks or safety recommendations.
- Real-time alerting.
- Individual shelter advice.
- Military target, weapon, or frontline analysis.
- A complex machine-learning model requiring heavy dependencies.
- Perfect reconstruction of local risk after the December 2025 district-level alert methodology change.

## Further Notes

The analysis must repeatedly state that alerts are public-warning events, not direct attack events. The baseline indicator is an analytical experiment for burden planning and model validation, not a tool for deciding whether to ignore or respond to an alert.
