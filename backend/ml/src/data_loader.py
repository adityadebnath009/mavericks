from pathlib import Path
import pandas as pd

from .config import DATA_PATH, REQUIRED_COLUMNS


def load_dataset(path: Path | str = DATA_PATH) -> pd.DataFrame:
    """Load the CSV and parse datetime exactly as the notebook does."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}. "
            "Set MARINE_DATA_PATH or place the CSV in backend/ml/data/."
        )

    df = pd.read_csv(path, parse_dates=["datetime"])
    return df


def validate_required_columns(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def validate_duplicate_keys(df: pd.DataFrame) -> int:
    return int(df.duplicated(subset=["location_id", "datetime"]).sum())


def validate_hourly_continuity(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for location, group in df.groupby("location_id"):
        delta = group["datetime"].sort_values().diff().dropna()
        invalid = int((delta != pd.Timedelta(hours=1)).sum())
        rows.append(
            {
                "location_id": location,
                "rows": len(group),
                "invalid_intervals": invalid,
                "continuous": invalid == 0,
            }
        )
    return pd.DataFrame(rows)
