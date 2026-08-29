# ml/src/diagnostics.py

import pandas as pd

from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report
)


def wave_height_diagnostic(
    df,
    split_date="2024-01-01"
):
    """Evaluate how strongly wave height predicts risk."""

    train_mask = (
        df["datetime"] <
        pd.Timestamp(split_date)
    )

    test_mask = (
        df["datetime"] >=
        pd.Timestamp(split_date)
    )

    X_train = df.loc[
        train_mask,
        ["wave_height_m"]
    ]

    X_test = df.loc[
        test_mask,
        ["wave_height_m"]
    ]

    y_train = df.loc[
        train_mask,
        "risk_class"
    ]

    y_test = df.loc[
        test_mask,
        "risk_class"
    ]

    model = DecisionTreeClassifier(
        max_depth=4,
        random_state=42
    )

    model.fit(
        X_train,
        y_train
    )

    predictions = model.predict(X_test)

    accuracy = accuracy_score(
        y_test,
        predictions
    )

    print(
        f"Wave-height-only accuracy: "
        f"{accuracy:.4f}"
    )

    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0
        )
    )