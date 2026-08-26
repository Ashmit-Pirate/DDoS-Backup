from typing import Dict, List, Any
import numpy as np


def map_features(input_features: Dict[str, Any], feature_columns: List[str]) -> np.ndarray:
    """
    Reindexes an incoming JSON dictionary of features into a 2D numpy float array (1, 77)
    matching the exact column order in feature_columns.pkl.
    Defensively cleans missing, NaN, or Inf values (replaced with 0.0).
    """
    row_values = []
    for col in feature_columns:
        val = input_features.get(col, 0.0)
        try:
            float_val = float(val) if val is not None else 0.0
            if np.isnan(float_val) or np.isinf(float_val):
                float_val = 0.0
        except (ValueError, TypeError):
            float_val = 0.0

        row_values.append(float_val)

    return np.array([row_values], dtype=np.float32)
