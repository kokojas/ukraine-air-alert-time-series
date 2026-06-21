"""Cautious baseline benchmark for next-day alert burden."""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd


MODEL_NOTE = "Analytical benchmark only; not for life-safety decisions."


def predict_next_day(daily: pd.DataFrame, oblast: str) -> dict[str, object]:
    """Predict next-day alert minutes for one oblast using a simple benchmark."""
    region = _prepare_region(daily, oblast)
    if region.empty:
        raise ValueError(f"no daily metrics for oblast: {oblast}")

    next_date = region["date_dt"].max() + timedelta(days=1)
    predicted = _predict_from_history(region, next_date)
    return {
        "oblast": oblast,
        "target_date": next_date.date().isoformat(),
        "predicted_alert_minutes": round(float(max(predicted, 0.0)), 2),
        "predicted_alert_hours": round(float(max(predicted, 0.0)) / 60, 2),
        "model": "weighted_recent_weekday_baseline",
        "model_note": MODEL_NOTE,
    }


def predict_all_next_day(daily: pd.DataFrame) -> pd.DataFrame:
    """Predict next-day alert burden for every oblast in the frame."""
    rows = [predict_next_day(daily, oblast) for oblast in sorted(daily["oblast"].dropna().unique())]
    return pd.DataFrame(rows).sort_values("predicted_alert_minutes", ascending=False).reset_index(drop=True)


def backtest_baseline(daily: pd.DataFrame, *, min_train_days: int = 30) -> pd.DataFrame:
    """Backtest the baseline and return mean absolute error per oblast."""
    results: list[dict[str, object]] = []
    for oblast in sorted(daily["oblast"].dropna().unique()):
        region = _prepare_region(daily, oblast)
        errors: list[float] = []
        actuals: list[float] = []
        for index in range(min_train_days, len(region)):
            train = region.iloc[:index]
            target = region.iloc[index]
            pred = _predict_from_history(train, target["date_dt"])
            actual = float(target["alert_minutes"])
            errors.append(abs(pred - actual))
            actuals.append(actual)
        if errors:
            results.append(
                {
                    "oblast": oblast,
                    "mae_minutes": round(float(np.mean(errors)), 2),
                    "mae_hours": round(float(np.mean(errors)) / 60, 2),
                    "mean_actual_minutes": round(float(np.mean(actuals)), 2),
                    "n_test_days": len(errors),
                    "model_note": MODEL_NOTE,
                }
            )
    columns = ["oblast", "mae_minutes", "mae_hours", "mean_actual_minutes", "n_test_days", "model_note"]
    if not results:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(results, columns=columns).sort_values("mae_minutes").reset_index(drop=True)


def _prepare_region(daily: pd.DataFrame, oblast: str) -> pd.DataFrame:
    frame = daily[daily["oblast"] == oblast].copy()
    if frame.empty:
        return frame
    frame["date_dt"] = pd.to_datetime(frame["date"])
    frame = frame.sort_values("date_dt").reset_index(drop=True)
    return frame


def _predict_from_history(history: pd.DataFrame, target_date: pd.Timestamp) -> float:
    if history.empty:
        return 0.0

    recent_7 = history.tail(7)["alert_minutes"].mean()
    recent_30 = history.tail(30)["alert_minutes"].mean()
    same_weekday = history[history["date_dt"].dt.dayofweek == target_date.dayofweek]["alert_minutes"]
    weekday_mean = same_weekday.tail(12).mean() if not same_weekday.empty else recent_30

    values = np.array([recent_7, recent_30, weekday_mean], dtype=float)
    weights = np.array([0.45, 0.35, 0.20], dtype=float)
    mask = ~np.isnan(values)
    if not mask.any():
        return 0.0
    return float(np.average(values[mask], weights=weights[mask]))
