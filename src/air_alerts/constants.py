"""Project constants and source notes."""

DEFAULT_DATA_URL = (
    "https://raw.githubusercontent.com/Vadimkin/"
    "ukrainian-air-raid-sirens-dataset/main/datasets/volunteer_data_en.csv"
)

PROJECT_TITLE = "Air Alert Burden & Fatigue Analyzer"

FOCUS_REGIONS = [
    "Kyiv City",
    "Kharkivska oblast",
    "Sumska oblast",
    "Donetska oblast",
    "Lvivska oblast",
]

DISCLAIMER = (
    "Analytical benchmark only; not for life-safety decisions. "
    "Always follow official alerts and local safety instructions."
)

SOURCE_LEDGER = [
    {
        "layer": "Alert history",
        "source": "Vadimkin Ukrainian air raid sirens dataset, volunteer_data_en.csv",
        "status": "reported public-warning events",
        "caveat": "Volunteer data is oblast-level and starts earlier, but some end times are imputed when marked naive.",
    },
    {
        "layer": "Regional aggregation",
        "source": "Derived by this project",
        "status": "calculated",
        "caveat": "Overlapping records inside the same oblast are unioned to avoid double counting.",
    },
    {
        "layer": "Night burden",
        "source": "Derived by this project",
        "status": "calculated",
        "caveat": "Night is defined as 22:00-07:00 Europe/Kyiv local time.",
    },
    {
        "layer": "Baseline forecast",
        "source": "Derived by this project",
        "status": "experimental benchmark",
        "caveat": "Not a safety recommendation and not a tactical prediction.",
    },
]
