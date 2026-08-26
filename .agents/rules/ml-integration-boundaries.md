---
trigger: glob
globs: detection/**,decision/**,mitigation/**
---

Rules specific to the ML inference → decision → mitigation pipeline:

- prediction.py returns a prediction ONLY (class + confidence for both
  the gatekeeper and multiclass stages). It never decides mitigation. The
  binary gatekeeper's `1` output is an escalation trigger, never a block
  trigger — this was an explicit override of the ML teammate's own
  integration guide, which suggested blocking directly on it; don't
  revert to that shortcut.
- The decision engine is mandatory between prediction and enforcement.
  Never `if prediction != "Benign": block()` at any stage, including the
  multiclass stage. Risk score comes from prediction + confidence + Redis
  state (rate, repeated-detection count, current mitigation) — never from
  the model's raw output alone.
- Feature contract (UPDATED 2026-08-25 — hyperparameter tuning changed
  this): both models now share ONE 77-feature vector, loaded from
  `feature_columns.pkl`. The earlier 77-vs-65 split (gatekeeper needing
  all 77, multiclass needing a 65-name subset) is superseded — the tuned
  XGBoost investigator (replaced an earlier Random Forest) handles the
  full 77 directly. `feature_mapper.py`'s job is now just a
  `reindex(columns=feature_columns)` call for column-order safety, not
  subset-dropping. Never hardcode the feature list — always load from
  `feature_columns.pkl`, it's the single source of truth.
- `class_mapping.pkl` (renamed from `label_mapping.pkl`, same
  convention) is name→index — must be inverted at load time to decode
  model output into an attack-name string. This has been a recurring
  bug source (caught twice now, including once by the ML teammate
  self-correcting) — always verify the direction explicitly rather than
  assuming a renamed file kept the same orientation.
- Divide-by-zero features arrive from the extractor already as 0, not
  NaN/Infinity — don't assume this holds without a defensive check anyway.
- model_loader.py loads both models ONCE at startup, never per-request.
  Current files: `lightgbm_binary_tuned.pkl` (gatekeeper) and
  `xgboost_multiclass_tuned.pkl` (investigator) — both require
  `scikit-learn` installed even though neither is an `sklearn.ensemble`
  class, since both use sklearn-API wrapper classes internally. Pin
  `xgboost==2.1.4`, `lightgbm==4.6.0`, `scikit-learn==1.3.2`.
- Mitigation defaults to SIMULATED status. Real enforcement only when
  explicitly told the team has moved to Stage 2 controlled enforcement.
- Known harmless quirk: the LightGBM gatekeeper's internal feature_name_
  uses underscores (auto-sanitized at training time) while
  feature_columns.pkl and the XGBoost model use spaces. Confirmed this
  does not affect prediction — LightGBM matches by column position, not
  name. Don't "fix" this if you notice it while debugging.