from typing import Dict, Any, Optional
import numpy as np
from detection.model_loader import ModelBundle, get_model_bundle


def predict_flow(
    features_vector: np.ndarray,
    bundle: Optional[ModelBundle] = None,
) -> Dict[str, Any]:
    """
    Executes the two-stage ML cascade inference on a 77-feature vector:
    Stage 1: Binary LightGBM gatekeeper (always executed).
             - If Benign, returns immediately with Benign verdict and confidence.
    Stage 2: Multiclass XGBoost investigator (executed only when gatekeeper flags Attack).
             - Evaluates the flow using the SAME 77-feature vector.
             - Maps argmax prediction to attack class name via inverted class mapping.

    Returns a pure prediction dictionary (no mitigation or policy logic).
    """
    model_bundle = bundle or get_model_bundle()
    binary_model = model_bundle.binary_model
    multiclass_model = model_bundle.multiclass_model
    index_to_class = model_bundle.index_to_class

    # Stage 1: Binary LightGBM Gatekeeper
    bg_proba = binary_model.predict_proba(features_vector)
    benign_proba = float(bg_proba[0, 0])
    attack_proba = float(bg_proba[0, 1])

    # Defensive prediction check
    bg_pred = binary_model.predict(features_vector)
    # Handle scalar or 1D array
    bg_pred_val = int(bg_pred[0]) if hasattr(bg_pred, "__len__") else int(bg_pred)

    is_attack_gatekeeper = (bg_pred_val == 1) or (attack_proba >= 0.5)

    if not is_attack_gatekeeper:
        return {
            "predicted_class": "Benign",
            "confidence": round(benign_proba, 4),
            "gatekeeper_confidence": round(attack_proba, 4),
            "is_attack": False,
        }

    # Stage 2: Multiclass XGBoost Investigator
    mc_proba = multiclass_model.predict_proba(features_vector)[0]
    pred_idx = int(np.argmax(mc_proba))
    predicted_class = index_to_class.get(pred_idx, "Unknown")
    class_confidence = float(mc_proba[pred_idx])

    is_attack = predicted_class != "Benign"

    return {
        "predicted_class": predicted_class,
        "confidence": round(class_confidence, 4),
        "gatekeeper_confidence": round(attack_proba, 4),
        "is_attack": is_attack,
    }
