import numpy as np
import pandas as pd

from .config import (
    BASE_FEATURE_COLUMNS,
    CLASS_LABELS,
    FEATURE_COLUMNS,
    PREDICTION_HORIZON_HOURS,
    RISK_HISTORY_FEATURES,
    RISK_LAGS,
    ROLLING_WINDOWS,
    SPATIAL_LOCATIONS,
)


def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reproduce the notebook's target and risk-history construction.

    Target:
        risk_class(t + 6h)

    Risk-history features use only past risk_class values.
    """
    df = df.sort_values(
        ["location_id", "datetime"]
    ).reset_index(drop=True).copy()

    df["target_risk_class"] = (
        df.groupby("location_id")["risk_class"]
        .shift(-PREDICTION_HORIZON_HOURS)
    )

    df = df.dropna(subset=["target_risk_class"]).copy()
    df["target_risk_class"] = df["target_risk_class"].astype(int)

    for lag in RISK_LAGS:
        df[f"risk_class_lag_{lag}"] = (
            df.groupby("location_id")["risk_class"].shift(lag)
        )

    for window in ROLLING_WINDOWS:
        df[f"risk_class_roll_max_{window}"] = (
            df.groupby("location_id")["risk_class"]
            .transform(
                lambda s: s.shift(1)
                .rolling(window=window, min_periods=1)
                .max()
            )
        )

        df[f"risk_class_roll_mean_{window}"] = (
            df.groupby("location_id")["risk_class"]
            .transform(
                lambda s: s.shift(1)
                .rolling(window=window, min_periods=1)
                .mean()
            )
        )

    missing_features = [
        f for f in FEATURE_COLUMNS if f not in df.columns
    ]
    if missing_features:
        raise ValueError(f"Missing features: {missing_features}")

    history_complete_mask = (
        df[RISK_HISTORY_FEATURES].notna().all(axis=1)
    )
    df = df.loc[history_complete_mask].copy()

    return df


def create_splits(
    df: pd.DataFrame,
    spatial_locations=SPATIAL_LOCATIONS,
):
    """
    Match the notebook's official split:
      development: < 2024 and not spatial holdout
      validation: 2024 and not spatial holdout
      temporal test: 2025 and not spatial holdout
      spatial test: selected spatial locations
    """
    spatial_locations = list(spatial_locations)

    train_mask = (
        (df["datetime"] < "2025-01-01")
        & (~df["location_id"].isin(spatial_locations))
    )

    temporal_mask = (
        (df["datetime"] >= "2025-01-01")
        & (~df["location_id"].isin(spatial_locations))
    )

    spatial_mask = df["location_id"].isin(spatial_locations)

    dev_train_mask = (
        (df["datetime"] < "2024-01-01")
        & (~df["location_id"].isin(spatial_locations))
    )

    validation_mask = (
        (df["datetime"] >= "2024-01-01")
        & (df["datetime"] < "2025-01-01")
        & (~df["location_id"].isin(spatial_locations))
    )

    return {
        "train_mask": train_mask,
        "dev_train_mask": dev_train_mask,
        "validation_mask": validation_mask,
        "temporal_mask": temporal_mask,
        "spatial_mask": spatial_mask,
        "dev_train": df.loc[dev_train_mask].copy(),
        "validation": df.loc[validation_mask].copy(),
        "temporal_test": df.loc[temporal_mask].copy(),
        "spatial_test": df.loc[spatial_mask].copy(),
    }


def make_matrices(splits):
    def xy(frame):
        return (
            frame[FEATURE_COLUMNS].astype("float32"),
            frame["target_risk_class"].astype("int8"),
        )

    X_dev, y_dev = xy(splits["dev_train"])
    X_val, y_val = xy(splits["validation"])
    X_2025, y_2025 = xy(splits["temporal_test"])
    X_spatial, y_spatial = xy(splits["spatial_test"])

    return {
        "X_dev": X_dev,
        "y_dev": y_dev,
        "X_val": X_val,
        "y_val": y_val,
        "X_2025": X_2025,
        "y_2025": y_2025,
        "X_digha": X_spatial,
        "y_digha": y_spatial,
    }


def calculate_inverse_frequency_weights(y, k=4):
    counts = y.value_counts().sort_index()
    n = len(y)
    return {
        int(cls): n / (k * count)
        for cls, count in counts.items()
    }


def make_safety_weights(
    y,
    high_multiplier=2.0,
    extreme_multiplier=3.0,
):
    weights = calculate_inverse_frequency_weights(y)
    if 2 in weights:
        weights[2] *= high_multiplier
    if 3 in weights:
        weights[3] *= extreme_multiplier

    sample_weight = y.map(weights).to_numpy(dtype="float32")
    return weights, sample_weight
