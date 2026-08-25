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
- Feature contract (confirmed 2026-08-24, both by direct .pkl inspection
  AND the ML teammate independently): binary gatekeeper needs 77 features
  (binary_feature_columns.pkl); multiclass model needs a 65-feature
  SUBSET (ddos_feature_columns.pkl) — NOT the same vector. ML teammate
  sends one 77-feature named JSON object per flow; backend derives the
  65-subset itself via reindex against ddos_feature_columns.pkl. Never
  hardcode either feature list — always load from the .pkl files, they're
  the single source of truth.
- label_mapping.pkl is name→index — must be inverted at load time to
  decode model output into an attack-name string.
- Divide-by-zero features arrive from the extractor already as 0, not
  NaN/Infinity — don't assume this holds without a defensive check anyway.
- model_loader.py loads both models ONCE at startup, never per-request.
- Mitigation defaults to SIMULATED status. Real enforcement only when
  explicitly told the team has moved to Stage 2 controlled enforcement.