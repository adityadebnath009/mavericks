import time
import numpy as np
import pandas as pd

from sklearn.ensemble import HistGradientBoostingClassifier

from .config import (
    DANGEROUS_RECALL_MINIMUM,
    EXTREME_WEIGHT_MULTIPLIER,
    HIGH_WEIGHT_MULTIPLIER,
    N8_MIN_DANGEROUS_RECALL,
    N8_MIN_HIGH_RECALL,
    N8_MIN_MACRO_F1,
    RANDOM_STATE,
)
from .evaluation import evaluate_predictions


BASE_EXPERIMENTS = [
    {"name": "risk_history_baseline", "learning_rate": 0.03, "max_iter": 400, "max_depth": 8, "min_samples_leaf": 20, "l2_regularization": 1.0},
    {"name": "risk_history_lr_002", "learning_rate": 0.02, "max_iter": 600, "max_depth": 8, "min_samples_leaf": 20, "l2_regularization": 1.0},
    {"name": "risk_history_lr_003_600", "learning_rate": 0.03, "max_iter": 600, "max_depth": 8, "min_samples_leaf": 20, "l2_regularization": 1.0},
    {"name": "risk_history_depth_6", "learning_rate": 0.03, "max_iter": 400, "max_depth": 6, "min_samples_leaf": 20, "l2_regularization": 1.0},
    {"name": "risk_history_depth_10", "learning_rate": 0.03, "max_iter": 400, "max_depth": 10, "min_samples_leaf": 20, "l2_regularization": 1.0},
    {"name": "risk_history_leaf_30", "learning_rate": 0.03, "max_iter": 400, "max_depth": 8, "min_samples_leaf": 30, "l2_regularization": 1.0},
    {"name": "risk_history_leaf_50", "learning_rate": 0.03, "max_iter": 400, "max_depth": 8, "min_samples_leaf": 50, "l2_regularization": 1.0},
    {"name": "risk_history_l2_3", "learning_rate": 0.03, "max_iter": 400, "max_depth": 8, "min_samples_leaf": 30, "l2_regularization": 3.0},
    {"name": "risk_history_deep_safety", "learning_rate": 0.03, "max_iter": 400, "max_depth": 8, "min_samples_leaf": 15, "l2_regularization": 1.0},
    {"name": "risk_history_generalization", "learning_rate": 0.02, "max_iter": 600, "max_depth": 7, "min_samples_leaf": 40, "l2_regularization": 3.0},
]

N6_EXPERIMENTS = [
    {"name": "refine_baseline", "learning_rate": 0.03, "max_iter": 400, "max_depth": 10, "min_samples_leaf": 20, "l2_regularization": 1.0},
    {"name": "refine_depth_12", "learning_rate": 0.03, "max_iter": 400, "max_depth": 12, "min_samples_leaf": 20, "l2_regularization": 1.0},
    {"name": "refine_leaf_10", "learning_rate": 0.03, "max_iter": 400, "max_depth": 10, "min_samples_leaf": 10, "l2_regularization": 1.0},
    {"name": "refine_leaf_30", "learning_rate": 0.03, "max_iter": 400, "max_depth": 10, "min_samples_leaf": 30, "l2_regularization": 1.0},
    {"name": "refine_l2_3", "learning_rate": 0.03, "max_iter": 400, "max_depth": 10, "min_samples_leaf": 20, "l2_regularization": 3.0},
    {"name": "refine_lr_002", "learning_rate": 0.02, "max_iter": 600, "max_depth": 10, "min_samples_leaf": 20, "l2_regularization": 1.0},
]

N8_SPECIALIST_CONFIGS = [
    {"name": "n8_d6_leaf5_x6", "learning_rate": 0.03, "max_iter": 600, "max_depth": 6, "min_samples_leaf": 5, "l2_regularization": 1.0, "extreme_multiplier": 6.0},
    {"name": "n8_d8_leaf5_x8", "learning_rate": 0.03, "max_iter": 600, "max_depth": 8, "min_samples_leaf": 5, "l2_regularization": 1.0, "extreme_multiplier": 8.0},
    {"name": "n8_d8_leaf10_x10", "learning_rate": 0.02, "max_iter": 800, "max_depth": 8, "min_samples_leaf": 10, "l2_regularization": 1.0, "extreme_multiplier": 10.0},
    {"name": "n8_d10_leaf5_x10", "learning_rate": 0.02, "max_iter": 800, "max_depth": 10, "min_samples_leaf": 5, "l2_regularization": 1.0, "extreme_multiplier": 10.0},
    {"name": "n8_d10_leaf10_x15", "learning_rate": 0.02, "max_iter": 800, "max_depth": 10, "min_samples_leaf": 10, "l2_regularization": 3.0, "extreme_multiplier": 15.0},
    {"name": "n8_d12_leaf5_x15", "learning_rate": 0.02, "max_iter": 800, "max_depth": 12, "min_samples_leaf": 5, "l2_regularization": 3.0, "extreme_multiplier": 15.0},
    {"name": "n8_d8_leaf5_x20", "learning_rate": 0.015, "max_iter": 900, "max_depth": 8, "min_samples_leaf": 5, "l2_regularization": 3.0, "extreme_multiplier": 20.0},
    {"name": "n8_d10_leaf5_x20", "learning_rate": 0.015, "max_iter": 900, "max_depth": 10, "min_samples_leaf": 5, "l2_regularization": 3.0, "extreme_multiplier": 20.0},
]


def build_hgbdt(params):
    return HistGradientBoostingClassifier(
        loss="log_loss",
        learning_rate=params["learning_rate"],
        max_iter=params["max_iter"],
        max_depth=params["max_depth"],
        min_samples_leaf=params["min_samples_leaf"],
        l2_regularization=params["l2_regularization"],
        max_bins=255,
        early_stopping=False,
        random_state=RANDOM_STATE,
    )


def train_hgbdt_candidates(X_dev, y_dev, sample_weight):
    experiments = BASE_EXPERIMENTS + N6_EXPERIMENTS
    models = {}
    rows = []

    for params in experiments:
        model = build_hgbdt(params)
        start = time.perf_counter()
        model.fit(X_dev, y_dev, sample_weight=sample_weight)
        elapsed = time.perf_counter() - start

        pred = model.predict(X_dev)  # replaced below by caller for validation
        models[params["name"]] = model
        rows.append({
            "name": params["name"],
            "training_time_sec": elapsed,
        })

    return experiments, models, pd.DataFrame(rows)


def evaluate_candidates(models, X_val, y_val):
    rows = []
    for name, model in models.items():
        result = evaluate_predictions(model.predict(X_val), y_val)
        rows.append({
            "name": name,
            **{k: v for k, v in result.items() if k != "predictions"},
        })
    return pd.DataFrame(rows)


def select_base_model(results_df, models):
    eligible = results_df[
        results_df["dangerous_recall"] >= DANGEROUS_RECALL_MINIMUM
    ].copy()

    if eligible.empty:
        eligible = results_df.copy()

    selected = (
        eligible.sort_values(
            ["macro_f1", "dangerous_recall", "dangerous_precision", "balanced_accuracy"],
            ascending=False,
        ).iloc[0]
    )
    name = str(selected["name"])
    return name, models[name]


def optimize_dangerous_threshold(model, X_val, y_val):
    proba = model.predict_proba(X_val)
    p_dangerous = proba[:, 2] + proba[:, 3]
    actual = (y_val >= 2).astype(int)

    rows = []
    for threshold in np.arange(0.01, 0.51, 0.01):
        pred = (p_dangerous >= threshold).astype(int)
        tp = ((pred == 1) & (actual == 1)).sum()
        fp = ((pred == 1) & (actual == 0)).sum()
        fn = ((pred == 0) & (actual == 1)).sum()
        tn = ((pred == 0) & (actual == 0)).sum()
        recall = tp / max(tp + fn, 1)
        precision = tp / max(tp + fp, 1)
        far = fp / max(fp + tn, 1)
        rows.append({
            "threshold": float(threshold),
            "dangerous_recall": recall,
            "dangerous_precision": precision,
            "false_alarm_rate": far,
        })

    df = pd.DataFrame(rows)
    eligible = df[df["dangerous_recall"] >= DANGEROUS_RECALL_MINIMUM]
    if not eligible.empty:
        best = eligible.sort_values(
            ["dangerous_precision", "false_alarm_rate"],
            ascending=[False, True],
        ).iloc[0]
    else:
        best = df.sort_values(
            ["dangerous_recall", "dangerous_precision"],
            ascending=False,
        ).iloc[0]

    return float(best["threshold"]), df



def train_extreme_weight_experiments(X_dev, y_dev, X_val, y_val, base_weights):
    """Notebook N2: evaluate EXTREME class multipliers [2, 3, 4, 5]."""
    multipliers = [2.0, 3.0, 4.0, 5.0]
    models = {}
    rows = []

    for multiplier in multipliers:
        weights_dict = base_weights.copy()
        weights_dict[2] = weights_dict.get(2, 1.0) * HIGH_WEIGHT_MULTIPLIER
        weights_dict[3] = weights_dict.get(3, 1.0) * multiplier
        sample_weight = y_dev.map(weights_dict).to_numpy(dtype="float32")

        params = {
            "name": f"extreme_weight_x{multiplier:g}",
            "learning_rate": 0.03,
            "max_iter": 400,
            "max_depth": 10,
            "min_samples_leaf": 20,
            "l2_regularization": 1.0,
        }
        model = build_hgbdt(params)
        model.fit(X_dev, y_dev, sample_weight=sample_weight)
        models[multiplier] = model

        metrics = evaluate_predictions(model.predict(X_val), y_val)
        rows.append({
            "extreme_multiplier": multiplier,
            **{k: v for k, v in metrics.items() if k != "predictions"},
        })

    return pd.DataFrame(rows).sort_values(
        "extreme_recall", ascending=False
    ).reset_index(drop=True), models

def train_n8_specialists(X_dev, y_dev, X_val, y_val, base_models, base_results=None):
    danger_mask = y_dev >= 2
    X_danger = X_dev.loc[danger_mask]
    y_danger = y_dev.loc[danger_mask]
    y_severity = (y_danger == 3).astype("int8")

    specialists = {}
    rows = []

    if base_results is not None and not base_results.empty:
        base_pool = (
            base_results
            .sort_values(
                ["macro_f1", "dangerous_recall", "balanced_accuracy"],
                ascending=False,
            )
            .drop_duplicates("name")
            .head(8)["name"]
            .tolist()
        )
        base_pool = [name for name in base_pool if name in base_models]
    else:
        base_pool = list(base_models.keys())[:8]

    for cfg in N8_SPECIALIST_CONFIGS:
        weights = np.where(
            y_severity.to_numpy() == 1,
            cfg["extreme_multiplier"],
            1.0,
        ).astype("float32")

        specialist = build_hgbdt(cfg)
        specialist.fit(X_danger, y_severity, sample_weight=weights)
        specialists[cfg["name"]] = specialist

        specialist_p = specialist.predict_proba(X_val)[:, 1]

        for base_name in base_pool:
            base_model = base_models[base_name]
            base_pred = base_model.predict(X_val)
            base_proba = base_model.predict_proba(X_val)

            pair = base_proba[:, 2] + base_proba[:, 3] + 1e-9
            base_relative = base_proba[:, 3] / pair
            high_gate = base_pred == 2

            for alpha in np.arange(0.0, 1.01, 0.25):
                score = alpha * specialist_p + (1.0 - alpha) * base_relative

                for threshold in np.arange(0.10, 0.901, 0.01):
                    pred = base_pred.copy()
                    pred[high_gate & (score >= threshold)] = 3
                    metrics = evaluate_predictions(pred, y_val)

                    rows.append({
                        "method": "specialist_blend",
                        "base_model": base_name,
                        "specialist": cfg["name"],
                        "threshold": float(threshold),
                        "alpha": float(alpha),
                        **{k: v for k, v in metrics.items() if k != "predictions"},
                    })

    for base_name in base_pool:
        base_model = base_models[base_name]
        base_pred = base_model.predict(X_val)
        base_proba = base_model.predict_proba(X_val)
        pair = base_proba[:, 2] + base_proba[:, 3] + 1e-9
        relative = base_proba[:, 3] / pair
        high_gate = base_pred == 2

        for threshold in np.arange(0.05, 0.901, 0.01):
            pred = base_pred.copy()
            pred[high_gate & (relative >= threshold)] = 3
            metrics = evaluate_predictions(pred, y_val)
            rows.append({
                "method": "base_relative_extreme",
                "base_model": base_name,
                "specialist": "none",
                "threshold": float(threshold),
                "alpha": 0.0,
                **{k: v for k, v in metrics.items() if k != "predictions"},
            })

    results = pd.DataFrame(rows)

    eligible = results[
        (results["dangerous_recall"] >= N8_MIN_DANGEROUS_RECALL)
        & (results["high_recall"] >= N8_MIN_HIGH_RECALL)
        & (results["macro_f1"] >= N8_MIN_MACRO_F1)
    ].copy()

    if eligible.empty:
        eligible = results[
            (results["dangerous_recall"] >= 0.90)
            & (results["high_recall"] >= 0.60)
            & (results["macro_f1"] >= 0.50)
        ].copy()

    if eligible.empty:
        eligible = results[
            results["dangerous_recall"] >= 0.90
        ].copy()

    if eligible.empty:
        raise RuntimeError("N8 produced no eligible severity candidate.")

    best = (
        eligible.sort_values(
            ["extreme_recall", "macro_f1", "high_recall", "balanced_accuracy", "dangerous_precision"],
            ascending=False,
        ).iloc[0]
    )

    return specialists, results, best


def apply_n8(
    base_model,
    severity_model,
    X,
    method,
    threshold,
    alpha,
):
    base_pred = base_model.predict(X)
    base_proba = base_model.predict_proba(X)
    pair = base_proba[:, 2] + base_proba[:, 3] + 1e-9
    base_relative = base_proba[:, 3] / pair

    if method == "base_relative_extreme":
        score = base_relative
    elif method == "specialist_blend":
        if severity_model is None:
            raise RuntimeError("N8 specialist is required.")
        specialist_p = severity_model.predict_proba(X)[:, 1]
        score = alpha * specialist_p + (1.0 - alpha) * base_relative
    else:
        raise ValueError(f"Unknown N8 method: {method}")

    refined = base_pred.copy()
    refined[(base_pred == 2) & (score >= threshold)] = 3

    # Safety invariant from the notebook.
    assert np.array_equal(base_pred >= 2, refined >= 2)
    return refined


def retrain_final_base(params, X_train, y_train, sample_weight):
    model = build_hgbdt(params)
    model.fit(X_train, y_train, sample_weight=sample_weight)
    return model


def retrain_final_specialist(cfg, X_train, y_train):
    mask = y_train >= 2
    X_danger = X_train.loc[mask]
    y_danger = (y_train.loc[mask] == 3).astype("int8")
    weights = np.where(
        y_danger.to_numpy() == 1,
        cfg["extreme_multiplier"],
        1.0,
    ).astype("float32")

    model = build_hgbdt(cfg)
    model.fit(X_danger, y_danger, sample_weight=weights)
    return model
