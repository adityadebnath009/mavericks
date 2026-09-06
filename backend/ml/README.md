# Modular ML version of `digha-hgbdt (1).ipynb`

This package separates the notebook into reusable Python modules while
preserving the notebook's terminology and main training/deployment flow.

## Folder placement

Copy the `src/` directory into:

    mavericks/backend/ml/src/

The expected project layout is:

    backend/
      ml/
        data/
        models/
        notebooks/
        src/
          __init__.py
          config.py
          data_loader.py
          diagnostics.py
          evaluation.py
          model.py
          preprocessing.py
          train.py

## Dataset

The notebook's local dataset filename is:

    new_indian_coastal_marine_dataset_2020_2025.csv

Place it in:

    backend/ml/data/

or set:

    MARINE_DATA_PATH=/absolute/path/to/file.csv

## Training

From `backend/ml`:

    python -m src.train

The script creates:

    models/model_hgbdt/sih_orca_risk_classifier.joblib
    models/model_hgbdt/feature_schema.json
    models/model_hgbdt/ood_ranges.json
    models/model_hgbdt/model_metadata.json
    models/model_hgbdt/metrics_report.json

## Deployment

The `.joblib` is the deployment artifact. It contains:

- the final 4-class HGBDT
- the selected N8 HIGH-vs-EXTREME specialist (when selected)
- severity threshold/alpha
- exact feature schema
- dangerous threshold
- class weights and deployment rule

Do not rebuild the model in the FastAPI request path. Load the saved package
once at application startup and call `predict()` / `predict_proba()` through
a predictor service.

## Important

2025 is kept as a final temporal holdout. N8 selection uses 2024 validation.
The operational dangerous score remains:

    P(HIGH) + P(EXTREME)

with its threshold selected from 2024 validation.
