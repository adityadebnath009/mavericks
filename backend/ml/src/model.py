# ml/src/model.py

from xgboost import XGBClassifier

from .config import XGB_PARAMS


def create_model():
    """Create the ORCA XGBoost classifier."""

    model = XGBClassifier(
        **XGB_PARAMS
    )

    return model


def train_model(model, X_train, y_train, sample_weights):
    """Train the XGBoost model."""

    print("Training ORCA XGBoost model...")

    model.fit(
        X_train,
        y_train,
        sample_weight=sample_weights
    )

    print("Training completed.")

    return model