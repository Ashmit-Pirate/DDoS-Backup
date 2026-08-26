import os
import pathlib
import joblib
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
MODELS_DIR = pathlib.Path(os.getenv("MODELS_DIR", BASE_DIR / "tuned_models"))


@dataclass
class ModelBundle:
    binary_model: Any
    multiclass_model: Any
    feature_columns: List[str]
    index_to_class: Dict[int, str]
    class_to_index: Dict[str, int]


_model_bundle: Optional[ModelBundle] = None


def load_models(models_dir: Optional[pathlib.Path] = None) -> ModelBundle:
    """
    Loads both tuned ML models, feature columns, and inverted class mapping once.
    Ensures safe, in-memory caching for zero per-request loading overhead.
    """
    global _model_bundle
    target_dir = models_dir or MODELS_DIR
    if not target_dir.is_absolute():
        target_dir = BASE_DIR / target_dir

    binary_model_path = target_dir / "lightgbm_binary_tuned.pkl"
    multiclass_model_path = target_dir / "xgboost_multiclass_tuned.pkl"
    feature_cols_path = target_dir / "feature_columns.pkl"
    class_mapping_path = target_dir / "class_mapping.pkl"

    for path, name in [
        (binary_model_path, "Binary LightGBM model"),
        (multiclass_model_path, "Multiclass XGBoost model"),
        (feature_cols_path, "Feature columns"),
        (class_mapping_path, "Class mapping"),
    ]:
        if not path.exists():
            raise FileNotFoundError(f"{name} artifact not found at {path}")

    # Load artifacts via joblib
    binary_model = joblib.load(binary_model_path)
    multiclass_model = joblib.load(multiclass_model_path)
    feature_columns = list(joblib.load(feature_cols_path))
    raw_class_mapping = joblib.load(class_mapping_path)

    # Invert class mapping at load time: NAME -> INDEX becomes INDEX -> NAME
    index_to_class: Dict[int, str] = {int(v): str(k) for k, v in raw_class_mapping.items()}
    class_to_index: Dict[str, int] = {str(k): int(v) for k, v in raw_class_mapping.items()}

    # Verify input feature dimensions (both models trained on 77 features)
    bin_n_features = getattr(binary_model, "n_features_in_", None)
    mc_n_features = getattr(multiclass_model, "n_features_in_", None)

    if bin_n_features is not None and bin_n_features != len(feature_columns):
        raise ValueError(
            f"Binary model expects {bin_n_features} features but feature_columns has {len(feature_columns)}"
        )
    if mc_n_features is not None and mc_n_features != len(feature_columns):
        raise ValueError(
            f"Multiclass model expects {mc_n_features} features but feature_columns has {len(feature_columns)}"
        )

    _model_bundle = ModelBundle(
        binary_model=binary_model,
        multiclass_model=multiclass_model,
        feature_columns=feature_columns,
        index_to_class=index_to_class,
        class_to_index=class_to_index,
    )
    return _model_bundle


def get_model_bundle() -> ModelBundle:
    """Returns the loaded singleton ModelBundle. Raises RuntimeError if not loaded."""
    global _model_bundle
    if _model_bundle is None:
        raise RuntimeError("ML ModelBundle has not been loaded. Call load_models() during startup.")
    return _model_bundle
