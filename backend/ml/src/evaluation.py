# ml/src/evaluation.py

from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix
)

from .config import CLASS_NAMES


def evaluate_model(
    model,
    X,
    y,
    dataset_name
):
    """Evaluate the model."""

    predictions = model.predict(X)

    accuracy = accuracy_score(
        y,
        predictions
    )

    macro_f1 = f1_score(
        y,
        predictions,
        average="macro",
        zero_division=0
    )

    print("\n" + "=" * 60)
    print(dataset_name)
    print("=" * 60)

    print(f"Accuracy : {accuracy:.4f}")
    print(f"Macro F1 : {macro_f1:.4f}")

    print("\nClassification Report:")

    print(
        classification_report(
            y,
            predictions,
            labels=list(CLASS_NAMES.keys()),
            target_names=list(CLASS_NAMES.values()),
            zero_division=0
        )
    )

    print("\nConfusion Matrix:")

    matrix = confusion_matrix(
        y,
        predictions,
        labels=list(CLASS_NAMES.keys())
    )

    print(matrix)

    return {
        "accuracy": float(accuracy),
        "macro_f1": float(macro_f1),
        "confusion_matrix": matrix.tolist()
    }