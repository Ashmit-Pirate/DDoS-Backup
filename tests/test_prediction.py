import numpy as np
import pytest
from detection.model_loader import load_models
from detection.prediction import predict_flow
from detection.feature_mapper import map_features


@pytest.fixture(scope="module")
def bundle():
    return load_models()


def test_predict_benign_flow(bundle):
    # Standard benign flow with 0.0 features
    features = {col: 0.0 for col in bundle.feature_columns}
    features_vector = map_features(features, bundle.feature_columns)

    result = predict_flow(features_vector, bundle)
    assert "predicted_class" in result
    assert "confidence" in result
    assert "gatekeeper_confidence" in result
    assert "is_attack" in result
    assert isinstance(result["confidence"], float)
    assert isinstance(result["gatekeeper_confidence"], float)
    assert 0.0 <= result["confidence"] <= 1.0
    assert 0.0 <= result["gatekeeper_confidence"] <= 1.0


def test_predict_attack_escalation(bundle):
    # Simulated high-frequency SYN flood vector
    features = {col: 0.0 for col in bundle.feature_columns}
    features["Protocol"] = 6.0
    features["SYN Flag Count"] = 1.0
    features["ACK Flag Count"] = 0.0
    features["Flow Packets/s"] = 100000.0
    features["Flow Bytes/s"] = 5000000.0
    features["Fwd Packets/s"] = 100000.0
    features["Total Fwd Packets"] = 1000.0
    features["Fwd Header Length"] = 20.0
    features["Init Fwd Win Bytes"] = 65535.0

    features_vector = map_features(features, bundle.feature_columns)
    result = predict_flow(features_vector, bundle)

    assert result["predicted_class"] in bundle.index_to_class.values()
    assert 0.0 <= result["confidence"] <= 1.0
    assert 0.0 <= result["gatekeeper_confidence"] <= 1.0
