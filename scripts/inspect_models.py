import sys
import os
import pathlib
import pprint
import traceback
import numpy as np

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent

# 1. Expected vs Actual paths
EXPECTED_PATHS = {
    "binary_model": BASE_DIR / "ml_models" / "binary_lightgbm" / "binary_lightgbm.pkl",
    "multiclass_model": BASE_DIR / "ml_models" / "multiclass_random_forest" / "ddos_multiclass_random_forest.pkl",
    "feature_columns_documented": BASE_DIR / "ddos_feature_columns.pkl",
    "label_mapping_documented": BASE_DIR / "label_mapping.pkl",
}

ACTUAL_PATHS = {
    "binary_model": BASE_DIR / "ml_models" / "binary_lightgbm" / "binary_lightgbm.pkl",
    "binary_feature_columns": BASE_DIR / "ml_models" / "binary_lightgbm" / "binary_feature_columns.pkl",
    "multiclass_model": BASE_DIR / "ml_models" / "multiclass_random_forest" / "ddos_multiclass_random_forest.pkl",
    "multiclass_feature_columns": BASE_DIR / "ml_models" / "multiclass_random_forest" / "ddos_feature_columns.pkl",
    "label_mapping": BASE_DIR / "ml_models" / "multiclass_random_forest" / "label_mapping.pkl",
}

def print_section(title):
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def try_load(file_path):
    print(f"\n--- Loading: {file_path.relative_to(BASE_DIR) if file_path.is_relative_to(BASE_DIR) else file_path} ---")
    if not file_path.exists():
        print(f"  [ERROR] File does NOT exist at path: {file_path}")
        return None, None, None, FileNotFoundError(f"File not found: {file_path}")
    
    obj = None
    method_used = None
    err_joblib = None
    err_pickle = None

    try:
        import joblib
        obj = joblib.load(file_path)
        method_used = "joblib"
        print("  [SUCCESS] Loaded via joblib.load()")
        return obj, method_used, None, None
    except Exception as e:
        err_joblib = e
        print(f"  [WARN] joblib.load() failed: {e}")

    try:
        import pickle
        with open(file_path, "rb") as f:
            obj = pickle.load(f)
        method_used = "pickle"
        print("  [SUCCESS] Loaded via pickle.load()")
        return obj, method_used, None, None
    except Exception as e:
        err_pickle = e
        print(f"  [ERROR] pickle.load() failed: {e}")

    return None, None, err_joblib, err_pickle

def main():
    print_section("ML MODEL ARTIFACT INSPECTION REPORT")

    # Check dependency versions
    print("\n--- Environment Package Versions ---")
    for pkg in ["joblib", "scikit-learn", "lightgbm", "imbalanced-learn", "sklearn", "imblearn", "pandas", "numpy"]:
        try:
            mod = __import__(pkg.replace("-", "_"))
            ver = getattr(mod, "__version__", "unknown")
            print(f"  {pkg}: {ver}")
        except ImportError as e:
            print(f"  {pkg}: NOT INSTALLED ({e})")

    # 1. Path Locations & Discrepancies
    print_section("1. ARTIFACT FILE LOCATIONS & DISCREPANCIES")
    for key, path in ACTUAL_PATHS.items():
        exists = path.exists()
        print(f"  Actual {key:30s}: {path.relative_to(BASE_DIR)} -> {'EXISTS' if exists else 'MISSING'}")

    print("\nChecking documented vs actual discrepancies:")
    if not EXPECTED_PATHS["feature_columns_documented"].exists():
        print(f"  [FLAG] Documented root path 'ddos_feature_columns.pkl' does NOT exist.")
        print(f"         Multiclass feature columns found at: {ACTUAL_PATHS['multiclass_feature_columns'].relative_to(BASE_DIR)}")
        print(f"         Binary feature columns found at:     {ACTUAL_PATHS['binary_feature_columns'].relative_to(BASE_DIR)}")
    if not EXPECTED_PATHS["label_mapping_documented"].exists():
        print(f"  [FLAG] Documented root path 'label_mapping.pkl' does NOT exist.")
        print(f"         Found at: {ACTUAL_PATHS['label_mapping'].relative_to(BASE_DIR)}")

    # 2. Label Mapping Inspection
    print_section("2. LABEL MAPPING INSPECTION (label_mapping.pkl)")
    label_obj, label_loader, _, _ = try_load(ACTUAL_PATHS["label_mapping"])
    if label_obj is not None:
        print(f"  Type: {type(label_obj)}")
        print(f"  Exact Contents:")
        pprint.pprint(label_obj, indent=4)
        
        # Analyze direction
        if isinstance(label_obj, dict):
            keys = list(label_obj.keys())
            vals = list(label_obj.values())
            print(f"\n  Key Types: {set(type(k) for k in keys)}")
            print(f"  Value Types: {set(type(v) for v in vals)}")
            
            is_index_to_name = all(isinstance(k, (int, np.integer)) for k in keys)
            is_name_to_index = all(isinstance(k, str) for k in keys)
            
            if is_index_to_name:
                print("  Direction: INDEX -> NAME (0-7 -> Attack Name)")
            elif is_name_to_index:
                print("  Direction: NAME -> INDEX (Attack Name -> 0-7)")
            else:
                print("  Direction: MIXED / OTHER")

            documented_classes = {"Benign", "LDAP", "MSSQL", "NetBIOS", "Portmap", "Syn", "UDP", "UDPLag"}
            found_classes = set(vals) if is_index_to_name else set(keys)
            print(f"  Class Count: {len(found_classes)}")
            print(f"  Matches 8 Documented Classes ({documented_classes}): {found_classes == documented_classes}")
            if found_classes != documented_classes:
                print(f"  [WARN] Discrepancy! Found: {found_classes}, Difference: {found_classes ^ documented_classes}")

    # 3. Feature Columns Inspection
    print_section("3. FEATURE COLUMNS INSPECTION")
    mc_cols, _, _, _ = try_load(ACTUAL_PATHS["multiclass_feature_columns"])
    bin_cols, _, _, _ = try_load(ACTUAL_PATHS["binary_feature_columns"])

    if mc_cols is not None:
        print(f"\n--- Multiclass Feature Columns ({ACTUAL_PATHS['multiclass_feature_columns'].relative_to(BASE_DIR)}) ---")
        print(f"  Type: {type(mc_cols)}")
        print(f"  Count: {len(mc_cols)}")
        print("  Full Ordered Feature List (Multiclass 65 features):")
        for idx, col in enumerate(mc_cols, 1):
            print(f"    {idx:2d}. {col}")

    if bin_cols is not None:
        print(f"\n--- Binary Feature Columns ({ACTUAL_PATHS['binary_feature_columns'].relative_to(BASE_DIR)}) ---")
        print(f"  Type: {type(bin_cols)}")
        print(f"  Count: {len(bin_cols)}")
        print("  Full Ordered Feature List (Binary 77 features):")
        for idx, col in enumerate(bin_cols, 1):
            print(f"    {idx:2d}. {col}")

    if mc_cols is not None and bin_cols is not None:
        are_equal = list(mc_cols) == list(bin_cols)
        print(f"\n  Binary (77) vs Multiclass (65) Feature Columns Identical: {are_equal}")
        print(f"  Difference count: {len(bin_cols)} vs {len(mc_cols)}")
        bin_set = set(bin_cols)
        mc_set = set(mc_cols)
        only_bin = bin_set - mc_set
        only_mc = mc_set - bin_set
        print(f"  Features in Binary (77) but omitted in Multiclass (65): {len(only_bin)}")
        for col in sorted(only_bin):
            print(f"    - {col}")
        if only_mc:
            print(f"  Features in Multiclass but omitted in Binary: {only_mc}")

    # 4. Binary LightGBM Gatekeeper Inspection
    print_section("4. BINARY LIGHTGBM GATEKEEPER INSPECTION")
    bin_model, bin_loader, bin_err_j, bin_err_p = try_load(ACTUAL_PATHS["binary_model"])
    if bin_model is not None:
        mod_name = type(bin_model).__module__
        cls_name = type(bin_model).__name__
        print(f"  Class Name & Module: {mod_name}.{cls_name}")
        
        # Pipeline vs Bare Estimator
        is_pipeline = "Pipeline" in cls_name or hasattr(bin_model, "steps")
        print(f"  Is Preprocessing Pipeline Wrapped: {is_pipeline}")
        if is_pipeline:
            print("  Pipeline steps:")
            for name, step in bin_model.steps:
                print(f"    - {name}: {type(step).__module__}.{type(step).__name__}")
        
        # Expected feature count
        n_feat = getattr(bin_model, "n_features_in_", None)
        if n_feat is None and hasattr(bin_model, "booster_"):
            n_feat = bin_model.booster_.num_feature()
        print(f"  Expected Input Feature Count (n_features_in_): {n_feat}")

        # Predict vs Predict_Proba
        has_predict = hasattr(bin_model, "predict")
        has_predict_proba = hasattr(bin_model, "predict_proba")
        print(f"  Exposes predict(): {has_predict}")
        print(f"  Exposes predict_proba(): {has_predict_proba}")

        if hasattr(bin_model, "classes_"):
            print(f"  Model classes_: {bin_model.classes_}")

        # Test inference with dummy input matching binary features (77)
        if has_predict_proba and bin_cols is not None:
            try:
                import pandas as pd
                dummy_df = pd.DataFrame(np.zeros((1, len(bin_cols))), columns=list(bin_cols))
                proba = bin_model.predict_proba(dummy_df)
                pred = bin_model.predict(dummy_df)
                print(f"  Dummy Inference Test (with {len(bin_cols)} features):")
                print(f"    predict() output: {pred} (type: {type(pred)}, shape: {getattr(pred, 'shape', None)})")
                print(f"    predict_proba() output shape: {proba.shape}")
                print(f"    predict_proba() values: {proba}")
                print("  [CONFIRMED] Binary LightGBM gatekeeper predict_proba succeeds with 77 features.")
            except Exception as e:
                print(f"  [ERROR] Dummy inference failed: {e}")
                traceback.print_exc()
    else:
        print(f"  Failed to load binary model artifact!")

    # 5. Multiclass Random Forest Inspection
    print_section("5. MULTICLASS RANDOM FOREST INSPECTION")
    mc_model, mc_loader, mc_err_j, mc_err_p = try_load(ACTUAL_PATHS["multiclass_model"])
    if mc_model is not None:
        mod_name = type(mc_model).__module__
        cls_name = type(mc_model).__name__
        print(f"  Class Name & Module: {mod_name}.{cls_name}")
        
        # Pipeline vs Bare Estimator
        is_pipeline = "Pipeline" in cls_name or hasattr(mc_model, "steps")
        print(f"  Is Preprocessing Pipeline Wrapped: {is_pipeline}")
        if is_pipeline:
            print("  Pipeline steps:")
            for name, step in mc_model.steps:
                print(f"    - {name}: {type(step).__module__}.{type(step).__name__}")

        # Expected feature count
        n_feat = getattr(mc_model, "n_features_in_", None)
        print(f"  Expected Input Feature Count (n_features_in_): {n_feat}")

        # Predict vs Predict_Proba
        has_predict = hasattr(mc_model, "predict")
        has_predict_proba = hasattr(mc_model, "predict_proba")
        print(f"  Exposes predict(): {has_predict}")
        print(f"  Exposes predict_proba(): {has_predict_proba}")

        if hasattr(mc_model, "classes_"):
            print(f"  Model classes_: {mc_model.classes_}")

        # Test inference with dummy input matching multiclass features (65)
        if has_predict_proba and mc_cols is not None:
            try:
                import pandas as pd
                dummy_df = pd.DataFrame(np.zeros((1, len(mc_cols))), columns=list(mc_cols))
                proba = mc_model.predict_proba(dummy_df)
                pred = mc_model.predict(dummy_df)
                print(f"  Dummy Inference Test (with {len(mc_cols)} features):")
                print(f"    predict() output: {pred} (type: {type(pred)}, shape: {getattr(pred, 'shape', None)})")
                print(f"    predict_proba() output shape: {proba.shape}")
                print(f"    predict_proba() values: {proba}")
                
                # Check class count
                if proba.shape[1] == 8:
                    print("  [CONFIRMED] predict_proba returns exactly 8 probabilities.")
                else:
                    print(f"  [WARN] predict_proba returns {proba.shape[1]} probabilities, expected 8!")
            except Exception as e:
                print(f"  [ERROR] Dummy inference failed: {e}")
                traceback.print_exc()
    else:
        print(f"  Failed to load multiclass model artifact!")

    print_section("END OF REPORT")

if __name__ == "__main__":
    main()
