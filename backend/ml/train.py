# ml/train.py

import json
import os

from src.data_loader import load_dataset

from src.preprocessing import (
    prepare_features,
    temporal_split,
    calculate_class_weights
)

from src.model import (
    create_model,
    train_model
)

from src.evaluation import evaluate_model

from src.config import (
    MODEL_DIR,
    MODEL_PATH,
    METADATA_PATH,
    FEATURES,
    SPLIT_DATE,
    CLASS_NAMES,
    XGB_PARAMS
)


def main():

    # --------------------------------
    # 1. Load dataset
    # --------------------------------

    df = load_dataset()


    # --------------------------------
    # 2. Prepare features
    # --------------------------------

    df, X, y = prepare_features(df)


    # --------------------------------
    # 3. Temporal split
    # --------------------------------

    X_train, X_test, y_train, y_test = (
        temporal_split(
            df,
            X,
            y
        )
    )


    print(f"Training samples: {len(X_train)}")
    print(f"Testing samples : {len(X_test)}")


    # --------------------------------
    # 4. Class weights
    # --------------------------------

    class_weight_dict, sample_weights = (
        calculate_class_weights(y_train)
    )


    # --------------------------------
    # 5. Create model
    # --------------------------------

    model = create_model()


    # --------------------------------
    # 6. Train
    # --------------------------------

    model = train_model(
        model,
        X_train,
        y_train,
        sample_weights
    )


    # --------------------------------
    # 7. Evaluate
    # --------------------------------

    train_metrics = evaluate_model(
        model,
        X_train,
        y_train,
        "TRAINING RESULTS"
    )

    test_metrics = evaluate_model(
        model,
        X_test,
        y_test,
        "TEMPORAL HOLDOUT RESULTS"
    )


    # --------------------------------
    # 8. Save model
    # --------------------------------

    os.makedirs(
        MODEL_DIR,
        exist_ok=True
    )

    model.save_model(
        MODEL_PATH
    )


    # --------------------------------
    # 9. Save metadata
    # --------------------------------

    metadata = {

        "model_name":
            "ORCA Marine Risk XGBoost",

        "target":
            "risk_class",

        "features":
            FEATURES,

        "class_mapping":
            CLASS_NAMES,

        "split_date":
            SPLIT_DATE,

        "model_parameters":
            XGB_PARAMS,

        "class_weights":
            {
                str(k): float(v)
                for k, v
                in class_weight_dict.items()
            },

        "train_metrics":
            train_metrics,

        "test_metrics":
            test_metrics
    }

    with open(
        METADATA_PATH,
        "w"
    ) as file:

        json.dump(
            metadata,
            file,
            indent=4
        )


    print("\nModel saved to:")
    print(MODEL_PATH)

    print("\nMetadata saved to:")
    print(METADATA_PATH)


if __name__ == "__main__":
    main()