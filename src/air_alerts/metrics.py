"""Core time-series metrics for Ukrainian air raid alert burden."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pandas as pd


@dataclass(frozen=True)
class DailyInterval:
    date: date
    alert_minutes: float
    night_minutes: float
    alert_count: int = 0


def merge_intervals(intervals: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    """Merge overlapping or touching intervals."""
    valid = sorted((start, end) for start, end in intervals if pd.notna(start) and pd.notna(end) and end > start)
    if not valid:
        return []

    merged: list[tuple[datetime, datetime]] = [valid[0]]
    for start, end in valid[1:]:
        current_start, current_end = merged[-1]
        if start <= current_end:
            merged[-1] = (current_start, max(current_end, end))
        else:
            merged.append((start, end))
    return merged


def split_interval_daily(
    start: datetime,
    end: datetime,
    *,
    timezone_name: str = "Europe/Kyiv",
) -> list[DailyInterval]:
    """Split one alert interval into local-day alert and night-burden minutes."""
    tz = ZoneInfo(timezone_name)
    local_start = start.astimezone(tz)
    local_end = end.astimezone(tz)
    if local_end <= local_start:
        return []

    parts: list[DailyInterval] = []
    cursor = local_start
    first_part = True
    while cursor < local_end:
        next_midnight = datetime.combine(cursor.date() + timedelta(days=1), time.min, tzinfo=tz)
        segment_end = min(local_end, next_midnight)
        alert_minutes = _minutes_between(cursor, segment_end)
        night_minutes = _night_overlap_minutes(cursor, segment_end, tz)
        parts.append(
            DailyInterval(
                date=cursor.date(),
                alert_minutes=round(alert_minutes, 3),
                night_minutes=round(night_minutes, 3),
                alert_count=1 if first_part else 0,
            )
        )
        first_part = False
        cursor = segment_end

    return parts


def build_daily_metrics(
    raw: pd.DataFrame,
    *,
    timezone_name: str = "Europe/Kyiv",
) -> pd.DataFrame:
    """Aggregate raw alert rows into oblast-level daily burden metrics.

    All rows for the same oblast are unioned before daily splitting. This avoids
    double-counting overlaps when oblast, raion, and hromada records coexist.
    """
    required = {"oblast", "started_at", "finished_at"}
    missing = sorted(required - set(raw.columns))
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")

    frame = raw.copy()
    frame["started_at"] = pd.to_datetime(frame["started_at"], utc=True, errors="coerce")
    frame["finished_at"] = pd.to_datetime(frame["finished_at"], utc=True, errors="coerce")
    frame = frame.dropna(subset=["oblast", "started_at", "finished_at"])
    frame = frame[frame["finished_at"] > frame["started_at"]]

    rows: list[dict[str, object]] = []
    for oblast, group in frame.groupby("oblast", sort=True):
        intervals = [
            (row.started_at.to_pydatetime(), row.finished_at.to_pydatetime())
            for row in group.itertuples(index=False)
        ]
        for start, end in merge_intervals(intervals):
            for part in split_interval_daily(start, end, timezone_name=timezone_name):
                rows.append(
                    {
                        "date": part.date.isoformat(),
                        "oblast": oblast,
                        "alert_minutes": part.alert_minutes,
                        "night_minutes": part.night_minutes,
                        "alert_count": part.alert_count,
                    }
                )

    if not rows:
        return pd.DataFrame(columns=["date", "oblast", "alert_minutes", "night_minutes", "alert_count"])

    daily = pd.DataFrame(rows)
    daily = (
        daily.groupby(["date", "oblast"], as_index=False)
        .agg(
            alert_minutes=("alert_minutes", "sum"),
            night_minutes=("night_minutes", "sum"),
            alert_count=("alert_count", "sum"),
        )
        .sort_values(["date", "oblast"])
        .reset_index(drop=True)
    )
    daily["alert_hours"] = (daily["alert_minutes"] / 60).round(3)
    daily["night_hours"] = (daily["night_minutes"] / 60).round(3)
    return daily


def add_rolling_metrics(daily: pd.DataFrame) -> pd.DataFrame:
    """Add rolling 7-day and 30-day alert-burden metrics per oblast."""
    frame = daily.copy()
    frame["date_dt"] = pd.to_datetime(frame["date"])
    frame = frame.sort_values(["oblast", "date_dt"])
    for window in (7, 30):
        frame[f"rolling_{window}d_alert_hours"] = (
            frame.groupby("oblast")["alert_hours"]
            .transform(lambda s: s.rolling(window, min_periods=1).sum())
            .round(3)
        )
        frame[f"rolling_{window}d_night_hours"] = (
            frame.groupby("oblast")["night_hours"]
            .transform(lambda s: s.rolling(window, min_periods=1).sum())
            .round(3)
        )
    return frame.drop(columns=["date_dt"])


def complete_daily_grid(
    daily: pd.DataFrame,
    *,
    oblasts: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """Fill missing oblast-date rows with zero burden."""
    if daily.empty and not (oblasts and start_date and end_date):
        return daily.copy()

    frame = daily.copy()
    if "alert_hours" not in frame.columns:
        frame["alert_hours"] = frame["alert_minutes"] / 60
    if "night_hours" not in frame.columns:
        frame["night_hours"] = frame["night_minutes"] / 60

    oblast_values = oblasts or sorted(frame["oblast"].dropna().unique())
    start = pd.to_datetime(start_date or frame["date"].min())
    end = pd.to_datetime(end_date or frame["date"].max())
    all_dates = pd.date_range(start, end, freq="D").strftime("%Y-%m-%d")
    grid = pd.MultiIndex.from_product([all_dates, oblast_values], names=["date", "oblast"]).to_frame(index=False)
    complete = grid.merge(frame, on=["date", "oblast"], how="left")

    fill_columns = ["alert_minutes", "night_minutes", "alert_count", "alert_hours", "night_hours"]
    for column in fill_columns:
        complete[column] = complete[column].fillna(0)
    complete["alert_count"] = complete["alert_count"].astype(int)
    return complete.sort_values(["date", "oblast"]).reset_index(drop=True)


def summarize_period(daily: pd.DataFrame, *, start_date: str | None = None) -> pd.DataFrame:
    """Summarize burden metrics by oblast for a date window."""
    frame = daily.copy()
    if start_date:
        frame = frame[frame["date"] >= start_date]
    if frame.empty:
        return pd.DataFrame()

    summary = (
        frame.groupby("oblast", as_index=False)
        .agg(
            total_alert_hours=("alert_hours", "sum"),
            total_night_hours=("night_hours", "sum"),
            alert_count=("alert_count", "sum"),
            active_days=("date", "nunique"),
        )
        .sort_values("total_alert_hours", ascending=False)
        .reset_index(drop=True)
    )
    summary["night_share"] = (summary["total_night_hours"] / summary["total_alert_hours"]).fillna(0).round(3)
    summary["avg_alert_hours_per_active_day"] = (
        summary["total_alert_hours"] / summary["active_days"].replace(0, pd.NA)
    ).fillna(0).round(3)
    summary["total_alert_hours"] = summary["total_alert_hours"].round(3)
    summary["total_night_hours"] = summary["total_night_hours"].round(3)
    return summary


def _night_overlap_minutes(start: datetime, end: datetime, tz: ZoneInfo) -> float:
    current_day = start.date()
    windows = [
        (datetime.combine(current_day, time.min, tzinfo=tz), datetime.combine(current_day, time(7), tzinfo=tz)),
        (datetime.combine(current_day, time(22), tzinfo=tz), datetime.combine(current_day + timedelta(days=1), time.min, tzinfo=tz)),
    ]
    return sum(_overlap_minutes(start, end, win_start, win_end) for win_start, win_end in windows)


def _overlap_minutes(start: datetime, end: datetime, other_start: datetime, other_end: datetime) -> float:
    latest_start = max(start, other_start)
    earliest_end = min(end, other_end)
    if earliest_end <= latest_start:
        return 0.0
    return _minutes_between(latest_start, earliest_end)


def _minutes_between(start: datetime, end: datetime) -> float:
    return (end - start).total_seconds() / 60
