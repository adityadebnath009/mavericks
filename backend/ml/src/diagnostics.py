import numpy as np
import pandas as pd

from sklearn.inspection import permutation_importance

from .evaluation import dangerous_metrics


def class_distribution(y, labels):
    counts = pd.Series(y).value_counts().sort_index()
    return pd.DataFrame({
        "Class": counts.index,
        "Label": [labels[int(c)] for c in counts.index],
        "Count": counts.values,
        "Percentage": counts.values / len(y) * 100,
    })


def extreme_support_report(y_sets):
    return pd.DataFrame([
        {
            "dataset": name,
            "EXTREME_support": int((np.asarray(y) == 3).sum()),
            "HIGH_support": int((np.asarray(y) == 2).sum()),
        }
        for name, y in y_sets.items()
    ])


def confusion_table(y_true, y_pred):
    cm = pd.DataFrame(
        pd.crosstab(
            pd.Series(y_true, name="Actual"),
            pd.Series(y_pred, name="Predicted"),
        )
    )
    return cm


def high_extreme_confusion(y_true, y_pred):
    mask = np.asarray(y_true) >= 2
    return pd.crosstab(
        pd.Series(np.asarray(y_true)[mask], name="Actual"),
        pd.Series(np.asarray(y_pred)[mask], name="Predicted"),
    ).reindex(index=[2, 3], columns=[2, 3], fill_value=0)


def permutation_importance_report(model, X_val, y_val, feature_columns):
    result = permutation_importance(
        model,
        X_val,
        y_val,
        scoring="f1_macro",
        n_repeats=5,
        random_state=42,
        n_jobs=-1,
    )
    return (
        pd.DataFrame({
            "Feature": feature_columns,
            "Importance Mean": result.importances_mean,
            "Importance Std": result.importances_std,
        })
        .sort_values("Importance Mean", ascending=False)
        .reset_index(drop=True)
    )


def create_events(timestamps, dangerous_mask):
    temp = pd.DataFrame({
        "datetime": pd.to_datetime(timestamps),
        "dangerous": np.asarray(dangerous_mask),
    }).sort_values("datetime").reset_index(drop=True)

    events = []
    start_time = None
    previous_time = None

    for _, row in temp.iterrows():
        current_time = row["datetime"]

        if row["dangerous"]:
            if (
                start_time is None
                or previous_time is None
                or current_time - previous_time > pd.Timedelta(hours=1)
            ):
                if start_time is not None:
                    events.append({"start": start_time, "end": previous_time})
                start_time = current_time
        else:
            if start_time is not None:
                events.append({"start": start_time, "end": previous_time})
                start_time = None

        previous_time = current_time

    if start_time is not None:
        events.append({"start": start_time, "end": previous_time})

    return events


def event_level_metrics_by_location(
    df_eval,
    actual_dangerous,
    predicted_dangerous,
):
    temp = df_eval[["location_id", "datetime"]].copy()
    temp["actual"] = np.asarray(actual_dangerous).astype(bool)
    temp["predicted"] = np.asarray(predicted_dangerous).astype(bool)

    results = []

    for location, group in temp.groupby("location_id"):
        group = group.sort_values("datetime").reset_index(drop=True)
        actual_events = create_events(group["datetime"], group["actual"])
        predicted_events = create_events(group["datetime"], group["predicted"])

        detected = 0
        for actual_event in actual_events:
            if any(
                predicted_event["start"] <= actual_event["end"]
                and predicted_event["end"] >= actual_event["start"]
                for predicted_event in predicted_events
            ):
                detected += 1

        results.append({
            "location_id": location,
            "actual_events": len(actual_events),
            "predicted_events": len(predicted_events),
            "detected_events": detected,
            "event_recall": (
                detected / len(actual_events)
                if actual_events else np.nan
            ),
        })

    return pd.DataFrame(results)
