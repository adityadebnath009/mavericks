# backend/ml/src/config.py

from pathlib import Path


# ==========================================
# Project Paths
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "marine_risk_processed.csv"
)

MODEL_DIR = (
    PROJECT_ROOT
    / "backend"
    / "models"
)

MODEL_PATH = (
    MODEL_DIR
    / "orca_xgb_model.json"
)

METADATA_PATH = (
    MODEL_DIR
    / "orca_xgb_metadata.json"
)


# ==========================================
# Dataset Configuration
# ==========================================

TARGET_COLUMN = "risk_class"

SPLIT_DATE = "2024-01-01"

FEATURES = [
    "wind_speed_kts",
    "wind_direction_deg",
    "wave_height_m",
    "wave_period_s",
    "air_temperature_c",
    "water_temperature_c",
    "relative_humidity_pct",
    "air_pressure_hpa",
    "latitude",
    "longitude",
    "month",
    "hour"
]


# ==========================================
# XGBoost Configuration
# ==========================================

XGB_PARAMS = {
    "objective": "multi:softprob",
    "num_class": 4,
    "n_estimators": 300,
    "learning_rate": 0.05,
    "max_depth": 5,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "reg_alpha": 0.1,
    "reg_lambda": 1.5,
    "eval_metric": "mlogloss",
    "random_state": 42,
    "n_jobs": -1
}


# ==========================================
# Risk Class Mapping
# ==========================================

CLASS_NAMES = {
    0: "LOW",
    1: "MODERATE",
    2: "HIGH",
    3: "EXTREME"
}