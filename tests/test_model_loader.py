import pytest
from detection.model_loader import load_models, get_model_bundle


def test_load_models_success():
    bundle = load_models()
    assert bundle is not None
    assert len(bundle.feature_columns) == 77
    assert len(bundle.index_to_class) == 8

    # Verify class inversion
    expected_classes = {"Benign", "LDAP", "MSSQL", "NetBIOS", "Portmap", "Syn", "UDP", "UDPLag"}
    assert set(bundle.index_to_class.values()) == expected_classes
    assert bundle.index_to_class[0] == "Benign"

    # Verify models expose predict and predict_proba
    assert hasattr(bundle.binary_model, "predict")
    assert hasattr(bundle.binary_model, "predict_proba")
    assert hasattr(bundle.multiclass_model, "predict")
    assert hasattr(bundle.multiclass_model, "predict_proba")


def test_get_model_bundle_singleton():
    bundle1 = get_model_bundle()
    bundle2 = get_model_bundle()
    assert bundle1 is bundle2
