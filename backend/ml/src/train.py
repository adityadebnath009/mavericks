"""
End-to-end training/evaluation entry point derived from digha-hgbdt (1).ipynb.

Run from backend/ml:
    python -m src.train

The notebook remains the experiment record. This script is the modular
training/deployment implementation of the same pipeline.
"""

import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .config import (
    CLASS_LABELS,
    DANGEROUS_RECALL_MINIMUM,
    FEATURE_COLUMNS,
    HIGH_WEIGHT_MULTIPLIER,
    EXTREME_WEIGHT_MULTIPLIER,
    MODEL_DIR,
    PREDICTION_HORIZON_HOURS,
    RANDOM_STATE,
    SPATIAL_LOCATIONS,
)
from .data_loader import (
    load_dataset,
    validate_duplicate_keys,
    validate_hourly_continuity,
    validate_required_columns,
)
from .diagnostics import (
    class_distribution,
    extreme_support_report,
    high_extreme_confusion,
    permutation_importance_report,
)
from .evaluation import dangerous_metrics, evaluate_model, scorecard_row
from .model import (
    N6_EXPERIMENTS,
    N8_SPECIALIST_CONFIGS,
    apply_n8,
    train_extreme_weight_experiments,
    optimize_dangerous_threshold,
    retrain_final_base,
    retrain_final_specialist,
    select_base_model,
    train_hgbdt_candidates,
    train_n8_specialists,
)
from .preprocessing import (
    calculate_inverse_frequency_weights,
    create_splits,
    make_matrices,
    make_safety_weights,
    prepare_dataframe,
)


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------
    # Load + validation
    # ---------------------------------------------------------
    df_raw = load_dataset()
    validate_required_columns(df_raw)

    duplicate_keys = validate_duplicate_keys(df_raw)
    print("Rows:", len(df_raw))
    print("Columns:", len(df_raw.columns))
    print("Duplicate location-time records:", duplicate_keys)

    continuity = validate_hourly_continuity(
        df_raw.sort_values(["location_id", "datetime"])
    )
    if not continuity["continuous"].all():
        print("WARNING: non-hourly gaps detected.")

    # ---------------------------------------------------------
    # Target + features
    # ---------------------------------------------------------
    df = prepare_dataframe(df_raw)

    # ---------------------------------------------------------
    # Official splits
    # ---------------------------------------------------------
    splits = create_splits(df, SPATIAL_LOCATIONS)
    mats = make_matrices(splits)

    X_dev = mats["X_dev"]
    y_dev = mats["y_dev"]
    X_val = mats["X_val"]
    y_val = mats["y_val"]
    X_2025 = mats["X_2025"]
    y_2025 = mats["y_2025"]
    X_digha = mats["X_digha"]
    y_digha = mats["y_digha"]

    print("\nSplit sizes:")
    for key in ["dev_train", "validation", "temporal_test", "spatial_test"]:
        print(f"{key}: {len(splits[key])}")

    print("\nEXTREME support:")
    print(extreme_support_report({
        "Training 2020-2023": y_dev,
        "Validation 2024": y_val,
        "Temporal Test 2025": y_2025,
        "Spatial Test": y_digha,
    }))

    print("\nTraining class distribution:")
    print(class_distribution(y_dev, CLASS_LABELS))

    # ---------------------------------------------------------
    # W3 safety weighting
    # ---------------------------------------------------------
    safety_weights, sample_weight = make_safety_weights(
        y_dev,
        HIGH_WEIGHT_MULTIPLIER,
        EXTREME_WEIGHT_MULTIPLIER,
    )

    print("\nSafety weights:", safety_weights)

    # ---------------------------------------------------------
    # N2 diagnostic (kept separate from final selection)
    # ---------------------------------------------------------
    n2_df, _ = train_extreme_weight_experiments(
        X_dev, y_dev, X_val, y_val,
        calculate_inverse_frequency_weights(y_dev),
    )
    print("\nN2 EXTREME weight diagnostic:")
    print(n2_df.to_string(index=False))

    # ---------------------------------------------------------
    # Base + N6 candidates
    # ---------------------------------------------------------
    experiments, candidate_models, _ = train_hgbdt_candidates(
        X_dev, y_dev, sample_weight
    )

    tuning_results = []
    for name, model in candidate_models.items():
        result = evaluate_model(model, X_val, y_val, name)
        tuning_results.append({
            "name": name,
            "accuracy": result["accuracy"],
            "macro_f1": result["macro_f1"],
            "macro_precision": result["macro_precision"],
            "macro_recall": result["macro_recall"],
            "balanced_accuracy": result["balanced_accuracy"],
            "high_recall": result["high_recall"],
            "extreme_recall": result["extreme_recall"],
            "dangerous_recall": result["dangerous_recall"],
            "dangerous_precision": result["dangerous_precision"],
        })

    tuning_results_df = pd.DataFrame(tuning_results)

    best_name, best_model = select_base_model(
        tuning_results_df, candidate_models
    )
    print("\nPreliminary selected base:", best_name)

    # ---------------------------------------------------------
    # N8 severity refinement
    # ---------------------------------------------------------
    n8_specialists, n8_results_df, n8_best = train_n8_specialists(
        X_dev,
        y_dev,
        X_val,
        y_val,
        candidate_models,
        base_results=tuning_results_df,
    )

    n8_method = str(n8_best["method"])
    n8_base_name = str(n8_best["base_model"])
    n8_specialist_name = str(n8_best["specialist"])
    n8_threshold = float(n8_best["threshold"])
    n8_alpha = float(n8_best["alpha"])

    best_name = n8_base_name
    best_model = candidate_models[best_name]

    print("\nN8 selected:")
    print(n8_best)

    # Dangerous threshold remains based on the base model and
    # the original P(HIGH)+P(EXTREME) rule, selected on 2024 only.
    dangerous_threshold, threshold_df = optimize_dangerous_threshold(
        best_model, X_val, y_val
    )

    # Validate N8 safety invariant.
    val_severity_model = (
        n8_specialists[n8_specialist_name]
        if n8_method == "specialist_blend"
        else None
    )
    val_pred = apply_n8(
        best_model,
        val_severity_model,
        X_val,
        n8_method,
        n8_threshold,
        n8_alpha,
    )
    base_val_pred = best_model.predict(X_val)
    assert np.array_equal(
        base_val_pred >= 2,
        val_pred >= 2,
    )

    print("\nN8 validation score:")
    print(scorecard_row(y_val, val_pred))

    # ---------------------------------------------------------
    # Final retraining on 2020-2024 non-spatial data
    # ---------------------------------------------------------
    final_train = splits["dev_train"].copy()
    # Match notebook: train_mask means all pre-2025 non-spatial data.
    final_train = df[
        (df["datetime"] < "2025-01-01")
        & (~df["location_id"].isin(SPATIAL_LOCATIONS))
    ].copy()

    X_final = final_train[FEATURE_COLUMNS].astype("float32")
    y_final = final_train["target_risk_class"].astype("int8")

    final_weights, final_sample_weight = make_safety_weights(
        y_final,
        HIGH_WEIGHT_MULTIPLIER,
        EXTREME_WEIGHT_MULTIPLIER,
    )

    selected_params = next(
        p for p in experiments if p["name"] == best_name
    )

    start = time.perf_counter()
    final_model = retrain_final_base(
        selected_params,
        X_final,
        y_final,
        final_sample_weight,
    )
    print(f"\nFinal base training time: {time.perf_counter() - start:.2f}s")

    final_specialist = None
    if n8_method == "specialist_blend":
        cfg = next(
            c for c in N8_SPECIALIST_CONFIGS
            if c["name"] == n8_specialist_name
        )
        final_specialist = retrain_final_specialist(
            cfg, X_final, y_final
        )

    # ---------------------------------------------------------
    # Final 2025 + spatial evaluation
    # ---------------------------------------------------------
    pred_2025 = apply_n8(
        final_model,
        final_specialist,
        X_2025,
        n8_method,
        n8_threshold,
        n8_alpha,
    )
    pred_digha = apply_n8(
        final_model,
        final_specialist,
        X_digha,
        n8_method,
        n8_threshold,
        n8_alpha,
    )

    eval_2025 = evaluate_model(final_model, X_2025, y_2025, "2025 base")
    eval_digha = evaluate_model(final_model, X_digha, y_digha, "Digha base")

    danger_2025 = dangerous_metrics(y_2025, pred_2025)
    danger_digha = dangerous_metrics(y_digha, pred_digha)

    scorecard = pd.DataFrame({
        "Metric": [
            "Accuracy",
            "Macro F1",
            "Macro Precision",
            "Macro Recall",
            "Balanced Accuracy",
            "HIGH Recall",
            "EXTREME Recall",
            "Standard Dangerous Recall",
            "Threshold Dangerous Recall",
            "Threshold Dangerous Precision",
            "Threshold False Alarm Rate",
        ],
        "2025 Temporal": [
            scorecard_row(y_2025, pred_2025)["Accuracy"],
            scorecard_row(y_2025, pred_2025)["Macro F1"],
            scorecard_row(y_2025, pred_2025)["Macro Precision"],
            scorecard_row(y_2025, pred_2025)["Macro Recall"],
            scorecard_row(y_2025, pred_2025)["Balanced Accuracy"],
            scorecard_row(y_2025, pred_2025)["HIGH Recall"],
            scorecard_row(y_2025, pred_2025)["EXTREME Recall"],
            danger_2025["recall"],
            None,
            None,
            None,
        ],
        "Digha Spatial": [
            scorecard_row(y_digha, pred_digha)["Accuracy"],
            scorecard_row(y_digha, pred_digha)["Macro F1"],
            scorecard_row(y_digha, pred_digha)["Macro Precision"],
            scorecard_row(y_digha, pred_digha)["Macro Recall"],
            scorecard_row(y_digha, pred_digha)["Balanced Accuracy"],
            scorecard_row(y_digha, pred_digha)["HIGH Recall"],
            scorecard_row(y_digha, pred_digha)["EXTREME Recall"],
            danger_digha["recall"],
            None,
            None,
            None,
        ],
    })

    # Operational dangerous threshold is evaluated from base probabilities.
    for X, y, col in [
        (X_2025, y_2025, "2025 Temporal"),
        (X_digha, y_digha, "Digha Spatial"),
    ]:
        proba = final_model.predict_proba(X)
        p_danger = proba[:, 2] + proba[:, 3]
        actual = (np.asarray(y) >= 2).astype(int)
        pred_danger = (p_danger >= dangerous_threshold).astype(int)

        dr = (
            ((pred_danger == 1) & (actual == 1)).sum()
            / max((actual == 1).sum(), 1)
        )
        dp = (
            ((pred_danger == 1) & (actual == 1)).sum()
            / max((pred_danger == 1).sum(), 1)
        )
        far = (
            ((pred_danger == 1) & (actual == 0)).sum()
            / max((actual == 0).sum(), 1)
        )

        scorecard.loc[
            scorecard["Metric"] == "Threshold Dangerous Recall", col
        ] = dr
        scorecard.loc[
            scorecard["Metric"] == "Threshold Dangerous Precision", col
        ] = dp
        scorecard.loc[
            scorecard["Metric"] == "Threshold False Alarm Rate", col
        ] = far

    print("\nFINAL SCORECARD")
    print(scorecard.to_string(index=False))

    print("\n2025 HIGH/EXTREME confusion:")
    print(high_extreme_confusion(y_2025, pred_2025))

    print("\nDigha HIGH/EXTREME confusion:")
    print(high_extreme_confusion(y_digha, pred_digha))

    # ---------------------------------------------------------
    # Save deployment artifacts
    # ---------------------------------------------------------
    model_package = {
        "model": final_model,
        "severity_model": final_specialist,
        "severity_method": n8_method,
        "severity_threshold": n8_threshold,
        "severity_alpha": n8_alpha,
        "severity_base_model": n8_base_name,
        "severity_specialist_name": n8_specialist_name,
        "features": FEATURE_COLUMNS,
        "class_weights": final_weights,
        "prediction_horizon_hours": PREDICTION_HORIZON_HOURS,
        "risk_labels": CLASS_LABELS,
        "dangerous_threshold": dangerous_threshold,
        "dangerous_definition": "HIGH + EXTREME",
        "model_selection": best_name,
        "deployment_rule": (
            "Base HGBDT predicts LOW/MODERATE/HIGH/EXTREME. "
            "N8 may convert HIGH to EXTREME only. "
            "LOW/MODERATE are never promoted. "
            "Existing EXTREME predictions remain EXTREME. "
            "Dangerous warning uses P(HIGH)+P(EXTREME) "
            "against the validation-selected threshold."
        ),
    }

    model_path = MODEL_DIR / "sih_orca_risk_classifier.joblib"
    joblib.dump(model_package, model_path)

    feature_schema = {
        "feature_count": len(FEATURE_COLUMNS),
        "features": FEATURE_COLUMNS,
        "target": "target_risk_class",
        "prediction_horizon_hours": PREDICTION_HORIZON_HOURS,
        "classes": CLASS_LABELS,
        "dangerous_definition": "HIGH + EXTREME",
        "dangerous_threshold": dangerous_threshold,
    }
    (MODEL_DIR / "feature_schema.json").write_text(
        json.dumps(feature_schema, indent=4)
    )

    ood_ranges = {
        f: {
            "min": float(X_final[f].min()),
            "max": float(X_final[f].max()),
        }
        for f in FEATURE_COLUMNS
    }
    (MODEL_DIR / "ood_ranges.json").write_text(
        json.dumps(ood_ranges, indent=4)
    )

    metadata = {
        "model_version": "v5-extreme-severity-recovery-modular",
        "prediction_horizon_hours": PREDICTION_HORIZON_HOURS,
        "feature_count": len(FEATURE_COLUMNS),
        "classes": list(CLASS_LABELS.values()),
        "development_training_period": "2020-2024 non-spatial",
        "validation_period": "2024",
        "temporal_test_period": "2025",
        "spatial_holdout": SPATIAL_LOCATIONS,
        "random_state": RANDOM_STATE,
        "algorithm": "Histogram Gradient Boosting Decision Tree",
        "selected_model": best_name,
        "hyperparameters": selected_params,
        "class_weighting": "safety_oriented",
        "HIGH_weight_multiplier": HIGH_WEIGHT_MULTIPLIER,
        "EXTREME_weight_multiplier": EXTREME_WEIGHT_MULTIPLIER,
        "n8_extreme_severity_refinement": True,
        "n8_severity_method": n8_method,
        "n8_severity_threshold": n8_threshold,
        "n8_severity_alpha": n8_alpha,
        "n8_severity_base_model": n8_base_name,
        "n8_severity_specialist": n8_specialist_name,
        "dangerous_definition": "HIGH + EXTREME",
        "dangerous_threshold": dangerous_threshold,
        "threshold_selection": "2024 validation only",
    }
    (MODEL_DIR / "model_metadata.json").write_text(
        json.dumps(metadata, indent=4)
    )

    report = {
        "model": {
            "selected_model": best_name,
            "dangerous_threshold": dangerous_threshold,
            "dangerous_definition": "HIGH + EXTREME",
            "n8_severity_method": n8_method,
            "n8_severity_threshold": n8_threshold,
            "n8_severity_alpha": n8_alpha,
            "n8_severity_specialist": n8_specialist_name,
        },
        "temporal_2025": scorecard_row(y_2025, pred_2025),
        "spatial": scorecard_row(y_digha, pred_digha),
    }
    (MODEL_DIR / "metrics_report.json").write_text(
        json.dumps(report, indent=4, default=float)
    )

    print("\nSaved:", model_path)


if __name__ == "__main__":
    main()
