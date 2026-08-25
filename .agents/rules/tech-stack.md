---
trigger: always_on
---

DDoS Protection System (SIH26_206, PS05) — backend + database portion.

Backend: FastAPI (Python) — native async, built-in WebSocket support, and
in-process calls to the ML models avoid a cross-language RPC hop.

ML runtime: scikit-learn (pin ==1.3.2 — models were trained on this
version; a newer one throws InconsistentVersionWarning on load) +
lightgbm. imbalanced-learn is NOT required despite the "Balanced Random
Forest" name — confirmed by direct .pkl inspection to be a plain
sklearn.ensemble.RandomForestClassifier with class_weight='balanced'.

Database: PostgreSQL (detections, risk_assessments, mitigation_actions,
events, system_status, config tables) + Redis (rate limiting,
repeated-detection counters, mitigation TTL/cooldown, pub/sub event
fan-out, benign/total traffic counters).

Repo layout (do not deviate):
DDoS-Mitigator/
  api/          # this user's — FastAPI app, routers, schemas, WS bridge
  db/           # this user's — SQLAlchemy models, Alembic, Redis client
  detection/    # SPLIT ownership — model_loader.py, feature_mapper.py,
                #   prediction.py are THIS USER'S (backend loads/calls
                #   models in-process); feature_extractor.py is the
                #   ML/feature-extraction teammate's
  decision/     # this user's — decision_engine.py, risk_score.py
  mitigation/   # this user's — mitigation_engine.py, policy, simulator.py
  dashboard/    # frontend teammate's — Next.js app, already built
  docker/, k8s/ # infra

Do not introduce alternative libraries for something already decided here
(no swapping FastAPI, no alternate ORM, no imbalanced-learn) without
asking first.