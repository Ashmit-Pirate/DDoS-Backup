---
trigger: always_on
---

This user owns: api/, db/, decision/, mitigation/, and — corrected
2026-08-22 from an earlier misattribution — model_loader.py,
feature_mapper.py, and prediction.py inside detection/. Backend loads and
calls the ML models in-process, so that code is backend's, not the ML
teammate's.

NOT this user's scope — flag rather than build silently:
- feature_extractor.py inside detection/ (raw traffic → feature vector)
  — ML/feature-extraction teammate's.
- Training, retraining, or modifying any .pkl model — ML teammate's.
- dashboard/ (Next.js app) — frontend teammate's, already built and
  reorganized into this monorepo; don't edit its internals from a backend
  task.
- docker/, k8s/ manifests — infra scope, unless explicitly asked to
  scaffold a docker-compose.yml for local Postgres/Redis as part of
  Phase 1.

If something looks like a useful addition beyond the current phase's
scope, flag it as a scope-creep tradeoff and ask, rather than building it
silently. Don't start work that depends on a later phase's deliverable —
that's a sign the phase boundary needs revisiting, not a reason to jump
ahead.