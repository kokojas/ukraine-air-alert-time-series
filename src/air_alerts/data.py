"""Dataset loading utilities."""

from __future__ import annotations

from pathlib import Path
from urllib.request import urlretrieve

import pandas as pd

from air_alerts.constants import DEFAULT_DATA_URL


def download_official_csv(
    destination: Path,
    *,
    url: str = DEFAULT_DATA_URL,
    force: bool = False,
) -> Path:
    """Download the official alert CSV if needed."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not force:
        return destination
    urlretrieve(url, destination)
    return destination


def load_alerts(path_or_url: str | Path) -> pd.DataFrame:
    """Load the alert CSV and keep the columns required by the analysis."""
    frame = pd.read_csv(path_or_url)
    if "region" in frame.columns and "oblast" not in frame.columns:
        frame = frame.rename(columns={"region": "oblast"})
    if "source" not in frame.columns:
        frame["source"] = "volunteer"
    if "level" not in frame.columns:
        frame["level"] = "oblast"
    required = ["oblast", "started_at", "finished_at"]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")
    return frame
