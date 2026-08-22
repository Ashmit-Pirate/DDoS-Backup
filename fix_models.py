import os
import shutil
from pathlib import Path

test_models_dir = Path("test_models")
ml_models_dir = Path("ml_models")

multi_lgb_dir = ml_models_dir / "multiclass_lightgbm"
multi_brf_dir = ml_models_dir / "multiclass_random_forest"

# Remove the LightGBM one we mistakenly added
if multi_lgb_dir.exists():
    shutil.rmtree(multi_lgb_dir)

# Create the Random Forest one
multi_brf_dir.mkdir(parents=True, exist_ok=True)

# Copy and rename BRF files
shutil.copy(test_models_dir / "ddos_multiclass_brf.pkl", multi_brf_dir / "ddos_multiclass_random_forest.pkl")
shutil.copy(test_models_dir / "ddos_brf_feature_columns.pkl", multi_brf_dir / "ddos_feature_columns.pkl")
shutil.copy(test_models_dir / "ddos_brf_label_mapping.pkl", multi_brf_dir / "label_mapping.pkl")

with open(multi_brf_dir / "README.md", "w", encoding="utf-8") as f:
    f.write("# Multiclass Balanced Random Forest\n\n")
    f.write("This model classifies network traffic into 8 different types of attacks. It has an accuracy of ~99.00%.\n")

print("Successfully replaced multiclass_lightgbm with multiclass_random_forest!")
