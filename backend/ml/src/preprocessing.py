# ml/src/preprocessing.py

import pandas as pd

from .config import FEATURES, TARGET_COLUMN, SPLIT_DATE


def prepare_features(df):
    """Prepare datetime features and return X and y."""

    df = df.copy()

    df["datetime"] = pd.to_datetime(df["datetime"])

    # Required temporal features
    df["month"] = df["datetime"].dt.month
    df["hour"] = df["datetime"].dt.hour

    X = df[FEATURES]
    y = df[TARGET_COLUMN]

    return df, X, y


def temporal_split(df, X, y):
    """Split data chronologically."""

    split_date = pd.Timestamp(SPLIT_DATE)

    train_mask = df["datetime"] < split_date
    test_mask = df["datetime"] >= split_date

    X_train = X.loc[train_mask]
    X_test = X.loc[test_mask]

    y_train = y.loc[train_mask]
    y_test = y.loc[test_mask]

    return X_train, X_test, y_train, y_test


def calculate_class_weights(y_train):
    """Calculate balanced sample weights."""

    from sklearn.utils.class_weight import compute_class_weight
    import numpy as np

    classes = np.unique(y_train)

    weights = compute_class_weight(
        class_weight="balanced",
        classes=classes,
        y=y_train
    )

    class_weight_dict = dict(
        zip(classes, weights)
    )

    sample_weights = y_train.map(
        class_weight_dict
    ).to_numpy()

    return class_weight_dict, sample_weights