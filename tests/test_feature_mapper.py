import numpy as np
import pytest
from detection.feature_mapper import map_features


def test_map_features_shape_and_defaults():
    cols = ["Protocol", "Flow Duration", "Total Fwd Packets", "Active Mean"]
    input_dict = {"Flow Duration": 12000, "Protocol": 6}

    mapped = map_features(input_dict, cols)
    assert isinstance(mapped, np.ndarray)
    assert mapped.shape == (1, 4)
    assert mapped[0, 0] == 6.0
    assert mapped[0, 1] == 12000.0
    assert mapped[0, 2] == 0.0  # missing feature defaults to 0
    assert mapped[0, 3] == 0.0  # missing feature defaults to 0


def test_map_features_handles_nan_and_inf():
    cols = ["Fwd Packet Length Mean", "Flow Bytes/s", "Down/Up Ratio"]
    input_dict = {
        "Fwd Packet Length Mean": float("nan"),
        "Flow Bytes/s": float("inf"),
        "Down/Up Ratio": 2.5,
    }

    mapped = map_features(input_dict, cols)
    assert mapped[0, 0] == 0.0
    assert mapped[0, 1] == 0.0
    assert mapped[0, 2] == 2.5


def test_map_features_exact_column_order():
    cols = ["B", "A", "C"]
    input_dict = {"A": 10, "B": 20, "C": 30}

    mapped = map_features(input_dict, cols)
    assert mapped[0, 0] == 20.0
    assert mapped[0, 1] == 10.0
    assert mapped[0, 2] == 30.0
