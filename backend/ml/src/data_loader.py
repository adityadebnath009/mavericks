# ml/src/data_loader.py

import pandas as pd

from .config import DATA_PATH


def load_dataset():
    """Load the marine risk dataset."""

    df = pd.read_csv(DATA_PATH)

    print(f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")

    return df