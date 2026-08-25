# ML Model Contract & Pre-Phase 2 Specifications

## Overview
This document defines the exact contracts, specifications, and assumptions for the four machine learning artifacts added to the project. It serves as the authoritative technical reference for Phase 2 implementation (`/api/v1/detect` endpoint and decision engine integration).

---

## 1. Artifact File Locations & Path Discrepancies

### Actual vs Documented Paths
| Artifact Description | Documented Expected Path | Actual Found Path | File Size | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Binary Gatekeeper Model** | `ml_models/binary_lightgbm/binary_lightgbm.pkl` | `ml_models/binary_lightgbm/binary_lightgbm.pkl` | ~2.1 MB | Verified |
| **Multiclass Model** | `ml_models/multiclass_random_forest/ddos_multiclass_random_forest.pkl` | `ml_models/multiclass_random_forest/ddos_multiclass_random_forest.pkl` | ~4.8 MB | Verified |
| **Binary Feature Columns** | (Not documented separately) | `ml_models/binary_lightgbm/binary_feature_columns.pkl` | ~2.1 KB | Verified |
| **Multiclass Feature Columns**| `ddos_feature_columns.pkl` (at root) | `ml_models/multiclass_random_forest/ddos_feature_columns.pkl` | ~1.8 KB | Path Discrepancy |
| **Label Mapping** | `label_mapping.pkl` (at root) | `ml_models/multiclass_random_forest/label_mapping.pkl` | ~200 B | Path Discrepancy |

> [!WARNING]
> **Path Discrepancy Flag**: `ddos_feature_columns.pkl` and `label_mapping.pkl` do not exist in the root folder. They are located inside `ml_models/multiclass_random_forest/`. Furthermore, a separate `binary_feature_columns.pkl` exists in `ml_models/binary_lightgbm/`.

---

## 2. Required Python Dependencies & Versions

To unpickle and run inference without errors, the following packages are required in `requirements.txt`:

```text
lightgbm>=4.0.0
scikit-learn>=1.3.0
joblib>=1.3.0
pandas>=2.0.0
numpy>=1.24.0
```

### Unpickling Notes:
- **Binary Model**: `lightgbm.sklearn.LGBMClassifier`. Loaded via `joblib.load()`.
- **Multiclass Model**: `sklearn.ensemble._forest.RandomForestClassifier`. Loaded via `joblib.load()`.
  - *Note on `imbalanced-learn`*: Although referred to as a "Balanced Random Forest", the actual unpickled class is standard scikit-learn `RandomForestClassifier` (trained with scikit-learn 1.3.2). `imbalanced-learn` is **not** required to load or run this artifact.

---

## 3. Feature Vectors & Preprocessing Contract

### Preprocessing Bundling
- Neither model is wrapped in a `sklearn.pipeline.Pipeline`.
- Both models are bare estimators (`LGBMClassifier` and `RandomForestClassifier`).
- **Phase 2 Assumption**: The backend must handle feature extraction, clean numerical conversion, and column ordering before passing dataframes/arrays to model inference.

### Feature Count & Discrepancy Between Pipeline Stages

> [!IMPORTANT]
> **Critical Feature Count Contract**:
> - **Stage 1 (Binary Gatekeeper)**: Expects **77 features** (`n_features_in_ = 77`).
> - **Stage 2 (Multiclass RF)**: Expects **65 features** (`n_features_in_ = 65`).

#### Omitted 12 Features in Stage 2 (Multiclass Model):
The multiclass Random Forest omits 12 features present in the 77-feature binary dataset:
1. `Bwd Avg Bulk Rate`
2. `Bwd Avg Bytes/Bulk`
3. `Bwd Avg Packets/Bulk`
4. `Bwd PSH Flags`
5. `Bwd URG Flags`
6. `ECE Flag Count`
7. `FIN Flag Count`
8. `Fwd Avg Bulk Rate`
9. `Fwd Avg Bytes/Bulk`
10. `Fwd Avg Packets/Bulk`
11. `Fwd URG Flags`
12. `PSH Flag Count`

### Full Feature Column Specifications

#### Stage 1: Binary Gatekeeper Feature Order (77 Features)
```text
 1. Protocol                  27. Bwd IAT Mean             53. Avg Packet Size
 2. Flow Duration             28. Bwd IAT Std              54. Avg Fwd Segment Size
 3. Total Fwd Packets         29. Bwd IAT Max              55. Avg Bwd Segment Size
 4. Total Backward Packets    30. Bwd IAT Min              56. Fwd Avg Bytes/Bulk
 5. Fwd Packets Length Total  31. Fwd PSH Flags            57. Fwd Avg Packets/Bulk
 6. Bwd Packets Length Total  32. Bwd PSH Flags            58. Fwd Avg Bulk Rate
 7. Fwd Packet Length Max     33. Fwd URG Flags            59. Bwd Avg Bytes/Bulk
 8. Fwd Packet Length Min     34. Bwd URG Flags            60. Bwd Avg Packets/Bulk
 9. Fwd Packet Length Mean    35. Fwd Header Length        61. Bwd Avg Bulk Rate
10. Fwd Packet Length Std     36. Bwd Header Length        62. Subflow Fwd Packets
11. Bwd Packet Length Max     37. Fwd Packets/s            63. Subflow Fwd Bytes
12. Bwd Packet Length Min     38. Bwd Packets/s            64. Subflow Bwd Packets
13. Bwd Packet Length Mean    39. Packet Length Min        65. Subflow Bwd Bytes
14. Bwd Packet Length Std     40. Packet Length Max        66. Init Fwd Win Bytes
15. Flow Bytes/s              41. Packet Length Mean       67. Init Bwd Win Bytes
16. Flow Packets/s            42. Packet Length Std        68. Fwd Act Data Packets
17. Flow IAT Mean             43. Packet Length Variance   69. Fwd Seg Size Min
18. Flow IAT Std              44. FIN Flag Count           70. Active Mean
19. Flow IAT Max              45. SYN Flag Count           71. Active Std
20. Flow IAT Min              46. RST Flag Count           72. Active Max
21. Fwd IAT Total             47. PSH Flag Count           73. Active Min
22. Fwd IAT Mean              48. ACK Flag Count           74. Idle Mean
23. Fwd IAT Std               49. URG Flag Count           75. Idle Std
24. Fwd IAT Max               50. CWE Flag Count           76. Idle Max
25. Fwd IAT Min               51. ECE Flag Count           77. Idle Min
26. Bwd IAT Total             52. Down/Up Ratio
```

#### Stage 2: Multiclass Model Feature Order (65 Features)
```text
 1. Protocol                  23. Fwd IAT Std              45. CWE Flag Count
 2. Flow Duration             24. Fwd IAT Max              46. Down/Up Ratio
 3. Total Fwd Packets         25. Fwd IAT Min              47. Avg Packet Size
 4. Total Backward Packets    26. Bwd IAT Total            48. Avg Fwd Segment Size
 5. Fwd Packets Length Total  27. Bwd IAT Mean             49. Avg Bwd Segment Size
 6. Bwd Packets Length Total  28. Bwd IAT Std              50. Subflow Fwd Packets
 7. Fwd Packet Length Max     29. Bwd IAT Max              51. Subflow Fwd Bytes
 8. Fwd Packet Length Min     30. Bwd IAT Min              52. Subflow Bwd Packets
 9. Fwd Packet Length Mean    31. Fwd PSH Flags            53. Subflow Bwd Bytes
10. Fwd Packet Length Std     32. Fwd Header Length        54. Init Fwd Win Bytes
11. Bwd Packet Length Max     33. Bwd Header Length        55. Init Bwd Win Bytes
12. Bwd Packet Length Min     34. Fwd Packets/s            56. Fwd Act Data Packets
13. Bwd Packet Length Mean    35. Bwd Packets/s            57. Fwd Seg Size Min
14. Bwd Packet Length Std     36. Packet Length Min        58. Active Mean
15. Flow Bytes/s              37. Packet Length Max        59. Active Std
16. Flow Packets/s            38. Packet Length Mean       60. Active Max
17. Flow IAT Mean             39. Packet Length Std        61. Active Min
18. Flow IAT Std              40. Packet Length Variance   62. Idle Mean
19. Flow IAT Max              41. SYN Flag Count           63. Idle Std
20. Flow IAT Min              42. RST Flag Count           64. Idle Max
21. Fwd IAT Total             43. ACK Flag Count           65. Idle Min
22. Fwd IAT Mean              44. URG Flag Count
```

---

## 4. Label Mapping Contract (`label_mapping.pkl`)

### File Format & Direction
`label_mapping.pkl` contains a Python `dict`:
```python
{
    'Benign': 0,
    'LDAP': 1,
    'MSSQL': 2,
    'NetBIOS': 3,
    'Portmap': 4,
    'Syn': 5,
    'UDP': 6,
    'UDPLag': 7
}
```

- **Direction**: **NAME -> INDEX** (`str` attack class name -> `int` index `0..7`).
- **Class Coverage**: Exactly matches the 8 documented classes (`Benign`, `LDAP`, `MSSQL`, `NetBIOS`, `Portmap`, `Syn`, `UDP`, `UDPLag`).

### Phase 2 Conversion Formula
To map predicted class indices (`0..7`) back to human-readable attack names in Phase 2 inference:
```python
INDEX_TO_LABEL = {v: k for k, v in label_mapping.items()}
# Result: {0: 'Benign', 1: 'LDAP', 2: 'MSSQL', 3: 'NetBIOS', 4: 'Portmap', 5: 'Syn', 6: 'UDP', 7: 'UDPLag'}
```

---

## 5. Binary Gatekeeper Contract (`binary_lightgbm.pkl`)

- **Model Class**: `lightgbm.sklearn.LGBMClassifier`
- **Supported Methods**: Both `predict()` and `predict_proba()` are exposed.
- **Classes Attribute**: `[0, 1]` (0 = Benign, 1 = Flagged/DDoS).
- **Confidence Extraction**:
  - Calling `predict_proba(X_77)` returns an array of shape `(N, 2)`.
  - Column 0 (`proba[:, 0]`): Benign probability.
  - Column 1 (`proba[:, 1]`): Attack probability (to populate `gatekeeper_confidence` in `detections` table).

---

## 6. Multiclass Model Contract (`ddos_multiclass_random_forest.pkl`)

- **Model Class**: `sklearn.ensemble._forest.RandomForestClassifier`
- **Supported Methods**: Both `predict()` and `predict_proba()` are exposed.
- **Classes Attribute**: `[0, 1, 2, 3, 4, 5, 6, 7]`.
- **Probabilities & Class Alignment**:
  - Calling `predict_proba(X_65)` returns an array of shape `(N, 8)`.
  - Column index `i` (0 to 7) corresponds directly to index `i` in `INDEX_TO_LABEL`.
  - The sum of probabilities across all 8 classes equals 1.0.

---

## 7. Architectural & Pipeline Requirements for Phase 2

1. **Two-Stage Pipeline Flow**:
   - **Stage 1 (Binary Gatekeeper)**: Construct 77-feature vector `X_77`. Run `binary_model.predict_proba(X_77)`.
   - **Gatekeeper Confidence**: Store `proba[:, 1]` as `gatekeeper_confidence`.
   - **If Flagged (Class 1)**: Filter `X_77` down to the 65 features required for Stage 2.
   - **Stage 2 (Multiclass Model)**: Run `multiclass_model.predict_proba(X_65)`. Map argmax index via `INDEX_TO_LABEL[idx]`.

2. **No Data Re-saving/Modification**:
   - Model `.pkl` files remain untouched read-only artifacts.
