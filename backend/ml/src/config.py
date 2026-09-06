from pathlib import Path
import os

# backend/ml
ML_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ML_ROOT / "data"
MODEL_DIR = ML_ROOT / "models" / "model_hgbdt"

DEFAULT_DATA_FILENAME = "new_indian_coastal_marine_dataset_2020_2025.csv"
DATA_PATH = Path(
    os.getenv("MARINE_DATA_PATH", str(DATA_DIR / DEFAULT_DATA_FILENAME))
)

RANDOM_STATE = 42
PREDICTION_HORIZON_HOURS = 6

CLASS_LABELS = {
    0: "LOW",
    1: "MODERATE",
    2: "HIGH",
    3: "EXTREME",
}

SPATIAL_LOCATIONS = [
    "digha_wb",
    "cyclone_biparjoy_core",
]

BASE_FEATURE_COLUMNS = [
    "wind_speed_kts",
    "wind_gust_kts",
    "wave_height_m",
    "wave_period_s",
    "mean_wave_period_s",
    "swell_height_m",
    "swell_period_s",
    "air_pressure_hpa",
    "air_temp_c",
    "sst_c",
    "precipitation_mm",
    "latitude",
    "longitude",
    "wave_steepness",
    "gust_excess_kts",
    "gust_to_wind_ratio",
    "gust_above_gale",
    "wind_dir_sin",
    "wind_dir_cos",
    "wave_dir_sin",
    "wave_dir_cos",
    "swell_dir_sin",
    "swell_dir_cos",
    "cross_sea_angle",
    "month_sin",
    "month_cos",
    "hour_sin",
]

RISK_LAGS = [1, 2, 3, 6, 12, 24]
ROLLING_WINDOWS = [3, 6, 12, 24]

RISK_HISTORY_FEATURES = (
    [f"risk_class_lag_{x}" for x in RISK_LAGS]
    + [f"risk_class_roll_max_{x}" for x in ROLLING_WINDOWS]
    + [f"risk_class_roll_mean_{x}" for x in ROLLING_WINDOWS]
)

FEATURE_COLUMNS = BASE_FEATURE_COLUMNS + RISK_HISTORY_FEATURES

REQUIRED_COLUMNS = [
    "datetime",
    "location_id",
    "location_name",
    "latitude",
    "longitude",
    "risk_class",
]

# Original W3 safety weighting.
HIGH_WEIGHT_MULTIPLIER = 2.0
EXTREME_WEIGHT_MULTIPLIER = 3.0

# Existing operational rule.
DANGEROUS_RECALL_MINIMUM = 0.90

# N8 validation guardrails from the notebook.
N8_MIN_DANGEROUS_RECALL = 0.90
N8_MIN_HIGH_RECALL = 0.70
N8_MIN_MACRO_F1 = 0.55
