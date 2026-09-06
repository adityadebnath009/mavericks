import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


def dangerous_metrics(y_true, y_pred):
    actual = (np.asarray(y_true) >= 2).astype(int)
    predicted = (np.asarray(y_pred) >= 2).astype(int)

    precision = precision_score(actual, predicted, zero_division=0)
    recall = recall_score(actual, predicted, zero_division=0)
    f1 = f1_score(actual, predicted, zero_division=0)

    tn, fp, fn, tp = confusion_matrix(
        actual, predicted, labels=[0, 1]
    ).ravel()

    far = fp / max(fp + tn, 1)
    fnr = fn / max(fn + tp, 1)

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positive_rate": far,
        "false_negative_rate": fnr,
    }


def evaluate_predictions(pred, y_true):
    pred = np.asarray(pred)
    y_true = np.asarray(y_true)

    dangerous_true = (y_true >= 2).astype(int)
    dangerous_pred = (pred >= 2).astype(int)

    return {
        "accuracy": accuracy_score(y_true, pred),
        "macro_f1": f1_score(y_true, pred, average="macro", zero_division=0),
        "macro_precision": precision_score(y_true, pred, average="macro", zero_division=0),
        "macro_recall": recall_score(y_true, pred, average="macro", zero_division=0),
        "balanced_accuracy": balanced_accuracy_score(y_true, pred),
        "high_recall": recall_score(y_true, pred, labels=[2], average="macro", zero_division=0),
        "extreme_recall": recall_score(y_true, pred, labels=[3], average="macro", zero_division=0),
        "dangerous_recall": recall_score(dangerous_true, dangerous_pred, zero_division=0),
        "dangerous_precision": precision_score(dangerous_true, dangerous_pred, zero_division=0),
        "false_alarm_rate": (
            ((dangerous_pred == 1) & (dangerous_true == 0)).sum()
            / max((dangerous_true == 0).sum(), 1)
        ),
        "predictions": pred,
    }


def evaluate_model(model, X, y, name="evaluation"):
    pred = model.predict(X)
    result = evaluate_predictions(pred, y)
    result["name"] = name
    result["classification_report"] = classification_report(
        y,
        pred,
        labels=[0, 1, 2, 3],
        target_names=["LOW", "MODERATE", "HIGH", "EXTREME"],
        zero_division=0,
    )
    result["confusion_matrix"] = confusion_matrix(
        y, pred, labels=[0, 1, 2, 3]
    )
    return result


def scorecard_row(y_true, pred):
    metrics = evaluate_predictions(pred, y_true)
    return {
        "Accuracy": metrics["accuracy"],
        "Macro F1": metrics["macro_f1"],
        "Macro Precision": metrics["macro_precision"],
        "Macro Recall": metrics["macro_recall"],
        "Balanced Accuracy": metrics["balanced_accuracy"],
        "HIGH Recall": metrics["high_recall"],
        "EXTREME Recall": metrics["extreme_recall"],
        "Dangerous Recall": metrics["dangerous_recall"],
        "Dangerous Precision": metrics["dangerous_precision"],
        "False Alarm Rate": metrics["false_alarm_rate"],
    }
