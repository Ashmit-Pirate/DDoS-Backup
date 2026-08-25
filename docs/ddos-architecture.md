# DDoS Protection System — Architecture & Schema

**Status: planning finalized for the backend/database scope.** Treat
everything below as settled — do not re-derive it or re-ask scoping
questions already answered here. Only change something here if explicitly
told a decision was revised, or if it conflicts with what a teammate
actually built (flag it, don't silently resolve it).

Companion doc: `ddos-build-plan.md` (phases, decision-engine logic,
mitigation policy, security checklist). Whole-project/non-backend
background (pitch deck, team, demo script, safety): `ddos-project-context.md`.

## Project summary

**DDoS Protection System for Cloud: Architecture and Tool** — SIH26_206,
Team "Bit by Bit", problem statement PS05, DJSCE SIH 2026 internal
hackathon. An ML-based DDoS detection, classification, and adaptive
mitigation system: monitors traffic, classifies legitimate vs. malicious
flows, identifies attack type, selects an attack-specific mitigation
strategy, protects legitimate users, and shows everything on a real-time
dashboard.

This doc covers the **backend + database** portion specifically — FastAPI
service, PostgreSQL, Redis, the ML inference wrapper, decision engine, and
mitigation engine. Frontend (Next.js dashboard), ML model training, and
infra (Docker/K8s edge) are teammates' scope — this backend integrates
with all three but doesn't own them.

## Product scope (decided)

- **Standard**: hackathon-timeline build with production-correct
  decisions made once, not a throwaway prototype — security, staged
  rollout (simulation before real enforcement), and test-gating are
  first-class, not afterthoughts.
- **Scope discipline**: planning is done for this backend scope. Stay
  inside it — flag rather than silently build into ML training, feature
  extraction internals, frontend components, or K8s manifests.
- **Known gap between the pitch deck and what's actually built**: the
  deck promises a hybrid rule-engine + unsupervised anomaly detector
  (Isolation Forest/LSTM) with Kubernetes autoscaling and honeypot
  rerouting. What's actually built is a two-stage **supervised** ML
  cascade (LightGBM gatekeeper → Random Forest classifier) with
  rate-limiting/filtering mitigation only — no autoscaling, no honeypot,
  no unsupervised anomaly detector. See `ddos-project-context.md` for the
  full gap list — don't imply the deck's promises are already built.

## Finalized tech stack for backend

- **Framework**: FastAPI (Python). Chosen because the ML models are
  scikit-learn/LightGBM — an in-process call avoids a cross-language RPC
  hop — and FastAPI gives native async, a built-in WebSocket endpoint,
  and auto-generated OpenAPI docs the frontend can build against.
- **ML runtime**: `lightgbm` (binary gatekeeper) + `scikit-learn`
  (multiclass Random Forest), pin **`scikit-learn==1.3.2`** specifically
  — the models were trained on that version and unpickling on a newer one
  (tested: 1.8.0) throws `InconsistentVersionWarning`; don't assume a
  newer version reproduces identical tree behavior. **`imbalanced-learn`
  is confirmed NOT required** — despite the "Balanced Random Forest"
  name, direct `.pkl` inspection confirmed it's a plain
  `sklearn.ensemble.RandomForestClassifier` with `class_weight='balanced'`,
  not `imblearn`'s specialized ensemble class.
- **Database**: PostgreSQL — durable event log, mitigation history,
  dashboard queries, tunable config.
- **Cache/state**: Redis — hot-path state (rate counters,
  repeated-detection counts, active-mitigation TTLs) and pub/sub fan-out
  to WebSocket clients.
- **ORM**: SQLAlchemy + Alembic for migrations (recommended default, not
  yet explicitly reconfirmed with the team — flag if it comes up).
- **Schemas**: Pydantic (native to FastAPI) for request/response/WS
  payload validation.
- **Frontend** (teammate's, already built): Next.js dashboard, confirmed
  **push/live updates via WebSocket only** — no polling anywhere in the
  frontend. Backend must never assume a REST-polling fallback is
  acceptable.
- Do not introduce alternative libraries for something already decided
  here (no swapping FastAPI, no alternate ORM, no imbalanced-learn)
  without asking first.

## Repo structure (do not deviate)

```
DDoS-Mitigator/
├── api/                       # this user's — FastAPI app, routers, schemas, WS bridge
│   ├── main.py                 # FastAPI app, startup loads both ML models
│   ├── routers/
│   │   ├── detect.py            # POST /api/v1/detect
│   │   ├── events.py            # GET /api/v1/events
│   │   ├── status.py            # GET /api/v1/status
│   │   ├── config.py            # GET/PUT /api/v1/config
│   │   ├── mitigation.py        # GET /api/v1/mitigation/active
│   │   └── ws.py                # WebSocket /ws/live, Redis pub/sub bridge
│   └── schemas.py               # Pydantic models incl. the WS envelope
├── db/                        # this user's — SQLAlchemy models, Alembic, Redis client
│   ├── models.py
│   ├── database.py
│   ├── redis_client.py
│   └── migrations/
├── detection/                  # SPLIT ownership — see note below
│   ├── models/                  # the .pkl artifacts: binary_lightgbm.pkl,
│   │                            #   binary_feature_columns.pkl [77],
│   │                            #   ddos_multiclass_random_forest.pkl,
│   │                            #   ddos_feature_columns.pkl [65-subset],
│   │                            #   label_mapping.pkl [invert at load]
│   ├── model_loader.py          # THIS USER'S — loads both models once at startup
│   ├── feature_mapper.py        # THIS USER'S — derives the 65-vector from the 77-vector
│   ├── prediction.py            # THIS USER'S — two-stage inference, prediction ONLY,
│   │                            #   never decides mitigation
│   └── feature_extractor.py     # ML/feature-extraction teammate's — raw traffic → 77-vector
├── decision/                   # this user's — decision_engine.py, risk_score.py, mitigation_policy.py
├── mitigation/                  # this user's — mitigation_engine.py, rate_limiter.py, firewall.py, simulator.py
├── dashboard/                   # frontend teammate's — Next.js app, already built
├── docker/                      # infra
└── k8s/                         # infra
```

**Detection/ ownership note (corrected 2026-08-22 from an earlier
misattribution):** backend loads and calls both ML models in-process, so
`model_loader.py`, `feature_mapper.py`, and `prediction.py` are this
user's files. Only `feature_extractor.py` (raw traffic → feature vector)
belongs to the ML/feature-extraction teammate.

## System architecture

```
Traffic / flow events (from monitor or simulator)
              │
              ▼
   ┌─────────────────────────────────────────┐
   │        Backend service (FastAPI)         │
   │                                           │
   │   API layer → Decision engine → Mitigation│
   │   (ingest &      (risk          (select & │
   │    route)         scoring)       respond) │
   └─────────────────────────────────────────┘
              │                          │
              ▼                          ▼
   Dashboard (Next.js, via WS)   Data layer (PostgreSQL + Redis)
```

**Flow:** API layer receives the flow's 77-feature vector → derives the
65-feature subset (see Feature contract) → calls the **binary LightGBM
gatekeeper** in-process with the 77-vector (every flow, ~0.0026 ms) → if
Benign, allow and stop (see Benign-flow logging below); if Attack,
escalate to the **multiclass Random Forest** with the 65-vector
(~0.0140 ms) + inverted `label_mapping.pkl` for the attack-type string
and confidence → hands it to the **decision engine**, which pulls recent
state from Redis (rate, repeated-detection count) to compute a risk
score/severity — **the binary gatekeeper's `1` output is a trigger to
escalate and log, never a trigger to block**; blocking is decided solely
by the decision engine (see `ddos-build-plan.md`) → if risk warrants it,
the mitigation engine selects an attack-specific action (**simulation
mode first**) → the event is persisted to Postgres and published to a
Redis pub/sub channel → the WebSocket bridge forwards it to every
connected dashboard client.

## ML model architecture — two-stage cascade

Confirmed by **two independent sources**: direct inspection of the actual
`.pkl` files, and the ML teammate's own description of her pipeline — not
just one or the other.

| Stage | Model | File | Latency/flow | Role |
|---|---|---|---|---|
| 1 — Gatekeeper | Binary LightGBM (`lightgbm.sklearn.LGBMClassifier`) | `binary_lightgbm.pkl` | 0.0026 ms | Runs on **every** flow; outputs `0` (Benign) / `1` (Attack); has `predict_proba` |
| 2 — Investigator | Multiclass Random Forest (`sklearn.ensemble.RandomForestClassifier`, `class_weight='balanced'`) | `ddos_multiclass_random_forest.pkl` | 0.0140 ms | Runs **only** on flows stage 1 flags as Attack; classifies which of 7 attack types; has `predict_proba` |

Combined worst-case latency for a flagged flow: ~0.0166 ms.

**8 classes**: `Benign, LDAP, MSSQL, NetBIOS, Portmap, Syn, UDP, UDPLag`.

**Multiclass model evaluation:**

| Metric | Balanced RF (selected) | Normal RF (not used) |
|---|---:|---:|
| Accuracy | 98.55% | 98.66% |
| Macro Precision | 75.14% | 75.50% |
| Macro Recall | 78.46% | 74.52% |
| Macro F1 | 76.59% | 74.95% |

Balanced RF was chosen over the marginally-more-accurate normal RF
because its macro recall/F1 are higher — more meaningful for this
imbalanced dataset (SYN/Benign/UDP/MSSQL well-represented;
NetBIOS/Portmap/UDPLag scarce). **98.55% accuracy is not the whole
story** — report macro F1 and per-class recall honestly. This ~75% macro
precision is also *why* the gatekeeper's `1` output must never be an
automatic block (see decision engine logic in `ddos-build-plan.md`).

**Two benchmarked, rejected alternatives — know they exist, don't build
against them:**

| Model | Latency/flow | Why rejected |
|---|---:|---|
| Binary Balanced Random Forest | 0.0094 ms | ~4x slower than Binary LightGBM for no accuracy gain |
| Multiclass LightGBM | 0.0513 ms | Highest raw accuracy of the four, but slowest at 8-class inference |

No XGBoost model is integrated (a teammate may build one separately for
comparison — not part of the current system).

## Feature contract — two vectors, not one (CONFIRMED)

Confirmed by both direct `.pkl` inspection **and** the ML teammate
independently — not a working assumption.

- **Gatekeeper vector**: 77 features, exact names/order in
  `binary_feature_columns.pkl`.
- **Multiclass vector**: 65 features, exact names/order in
  `ddos_feature_columns.pkl` — a strict subset of the 77, same relative
  order, with these 12 dropped (constant/all-zero in training data, per
  the ML teammate): `Bwd PSH Flags, Bwd URG Flags, Fwd URG Flags,
  FIN Flag Count, ECE Flag Count, PSH Flag Count, Fwd Avg Bytes/Bulk,
  Fwd Avg Packets/Bulk, Fwd Avg Bulk Rate, Bwd Avg Bytes/Bulk,
  Bwd Avg Packets/Bulk, Bwd Avg Bulk Rate`.

**Vector-splitting responsibility (CONFIRMED):** the feature-extraction
teammate sends **one 77-feature vector per flow**; backend derives the
65-subset itself in `feature_mapper.py` via
`reindex(columns=multiclass_feature_columns)`.

**Wire format (CONFIRMED):** a **named JSON object**, not a bare array —
e.g. `{"Flow Duration": 1500, "Total Fwd Packets": 3, ...}` for all 77
keys. Verified byte-for-byte against the real `binary_feature_columns.pkl`
contents (exact spacing/capitalization match).

**Divide-by-zero handling (CONFIRMED):** for ratio-style features (e.g.
`Flow Bytes/s`) where the denominator is zero, the extractor sends **0**,
not `NaN`/`Infinity`/`null`. Backend can trust incoming values are
already clean — keep a defensive check anyway.

**`label_mapping.pkl` is name→index** (`{'Benign': 0, 'LDAP': 1, ...}`) —
must be **inverted** at load time to decode model output into a string.

**Model output shape**: `predict()` may return a bare scalar or a
1-element array depending on library/input shape — handle both, don't
assume `result[0]` always works.

**Do not copy the ML teammate's illustrative API response** — her example
walkthrough ends with a simplified `{"status": "blocked", "attack_type":
"Syn"}`. That's her explaining how the *models* chain together, not a
backend API spec. The real response must go through the decision engine
and match the finalized `mitigation` WS event shape (see below) — never
a bare `"blocked"` string assembled straight from the multiclass output.

## Benign-flow logging — design decision

The binary gatekeeper runs on every flow, but writing a full Postgres row
for every single benign flow would be wasteful at line rate.

**Decision:** don't write a `detections` row for Benign flows. Instead,
increment two Redis counters on every flow regardless of outcome —
`stats:total_count` and `stats:benign_count` — and only write a
`detections` row (and continue to the multiclass stage) when the
gatekeeper flags Attack. The dashboard's "Benign traffic %" stat is
computed from the two Redis counters, not from scanning Postgres.

## Database schema (PostgreSQL)

```sql
CREATE TABLE detections (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
  source_ip TEXT NOT NULL,
  -- the binary LightGBM's own output confidence, kept for audit/tuning
  -- even though it doesn't drive the block decision by itself
  gatekeeper_confidence NUMERIC(5,4),
  predicted_class TEXT NOT NULL CHECK (predicted_class IN
    ('Benign','LDAP','MSSQL','NetBIOS','Portmap','Syn','UDP','UDPLag')),
  confidence NUMERIC(5,4) NOT NULL CHECK (confidence BETWEEN 0 AND 1)
);
CREATE INDEX idx_detections_time ON detections (timestamp);

CREATE TABLE risk_assessments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  detection_id UUID NOT NULL REFERENCES detections(id) ON DELETE CASCADE,
  risk_score INT NOT NULL CHECK (risk_score BETWEEN 0 AND 100),
  severity TEXT NOT NULL CHECK (severity IN ('LOW','MEDIUM','HIGH')),
  factors JSONB NOT NULL,  -- e.g. {"confidence":0.994,"traffic_rate":"extremely_high","repeated_detection":true}
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE mitigation_actions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  risk_assessment_id UUID NOT NULL REFERENCES risk_assessments(id) ON DELETE CASCADE,
  attack_type TEXT NOT NULL,
  action_type TEXT NOT NULL,  -- RATE_LIMIT, FILTER, BLOCK, RESTRICT_EXPOSURE, ALLOW
  -- matches the frontend's MitigationStatus type exactly:
  status TEXT NOT NULL CHECK (status IN ('PLANNED','SIMULATED','ACTIVE','COMPLETED')),
  source_ip TEXT NOT NULL,  -- pushed to the client as `sourceIp` — powers the blocked-IP list
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ  -- cooldown-based auto-unblock target (internal only;
                           -- surfaces to the client as a human-readable `result` string)
);
CREATE INDEX idx_mitigation_source ON mitigation_actions (source_ip, status);

CREATE TABLE events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
  attack_type TEXT NOT NULL,
  severity TEXT NOT NULL,
  confidence NUMERIC(5,4),
  action TEXT,
  status TEXT
);
-- Unified log feed matching the dashboard's log format:
-- 12:35:21 | SYN | HIGH | 99.4% | RATE_LIMIT | ACTIVE
CREATE INDEX idx_events_time ON events (timestamp);
CREATE INDEX idx_events_attack_type ON events (attack_type);

CREATE TABLE system_status (
  id INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),  -- singleton row
  -- 6-stage lifecycle matching the frontend's SystemState type:
  status TEXT NOT NULL CHECK (status IN
    ('NORMAL','ATTACK_DETECTED','CLASSIFIED','MITIGATING','RECOVERING','RECOVERED')),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE config (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now()
);
-- e.g. confidence_threshold, rate_threshold, repeated_detection_window_sec,
-- cooldown_seconds — tunable live during the demo without redeploying.
```

`timestamp`/`attack_type` are indexed on `events` specifically so a
Grafana fallback can query it directly if that path is ever needed
alongside the React/Next.js dashboard.

## Redis keys

| Key pattern | Type | Purpose |
|---|---|---|
| `rate:{source_ip}` | counter + TTL | Sliding-window request rate per source |
| `detect:{source_ip}:{attack_type}` | counter + TTL | Repeated-detection escalation |
| `mitigation:{source_ip}` | string + TTL | Active mitigation — **TTL expiry is the cooldown-based auto-unblock**, no cron job needed |
| `channel:events` | pub/sub | Fan-out from event producers to every WebSocket connection |
| `stats:total_count` | counter | Incremented on every flow, gatekeeper stage, regardless of verdict |
| `stats:benign_count` | counter | Incremented only when the gatekeeper outputs Benign; `benign_count / total_count` feeds the dashboard's benign% |

## REST API surface

**Reconciled with the actual frontend contract** — the frontend (Next.js
dashboard, `SageContext`/`src/types/sage.ts`) was already built against a
specific shape before backend existed. Since the frontend had zero real
network calls at that point (pure client-side mock simulation), the
decision was to make the **backend conform to the frontend's existing
types**, not the reverse.

| Endpoint | Method | Consumer | Shape |
|---|---|---|---|
| `/api/v1/detect` | POST | Traffic monitor/simulator — feature vector in, prediction+confidence out | see Feature contract |
| `/api/v1/events` | GET | Dashboard — initial-hydration snapshot on WS connect | `{ incidents: Incident[], logs: LogEvent[] }` — split, not a generic feed |
| `/api/v1/status` | GET | Dashboard — status + initial-hydration on WS connect | the 6-stage lifecycle string |
| `/api/v1/mitigation/active` | GET | Dashboard — current rate limits/blocks, and the blocked-IP list's hydration source | `MitigationAction[]` including `sourceIp` |
| `/api/v1/config` | GET/PUT | Team — tune decision-engine thresholds live | `RuntimeSystemConfig` shape (`targetApplication`, `environment`, `mitigationMode`, `telemetryRefreshRateMs`, `serverAvailability`, `baselineRequestRate`, `baselineEntropy`) |
| `/api/v1/stats` | — | **Dropped.** Frontend builds its graphs off the continuous `telemetry` WS stream. |
| `/ws/live` | WebSocket | Dashboard — real-time push (see contract below) | |

## Blocked-IP list — design decision

No new endpoint or event type. Derived from the existing `mitigation`
event/`MitigationAction` data:

- `mitigation_actions.source_ip` (Postgres) and `mitigation:{source_ip}`
  (Redis) already carry everything needed — one added field on the
  pushed/returned payload: **`sourceIp`**.
- Dashboard derives "currently blocked IPs" by filtering
  `status === 'ACTIVE'` client-side off the live WS stream; the Redis TTL
  naturally produces a follow-up `status: 'COMPLETED'` event when a block
  lifts.
- `GET /api/v1/mitigation/active` is the hydration-on-load version of the
  same shape.
- **Production/scale note**: cap what's sent for a sustained attack with
  many source IPs (most-recent-N or pagination) so payload/render size
  stays bounded. Status transitions must be idempotent — a duplicate
  `ACTIVE` event for an IP already in the list is a no-op, not a
  duplicate row.

## WebSocket event contract (`/ws/live`) — FINALIZED

Typed envelope so the client routes each message without guessing:

```json
{ "type": "detection" | "mitigation" | "status_change" | "telemetry",
  "timestamp": "2026-08-22T14:35:21.123Z",
  "data": { ... } }
```

**Four event types only.** No standalone `risk_assessment` event — risk
is bundled directly into `detection`.

- **`telemetry`** (frequent, ~1s, driven by `config.telemetryRefreshRateMs`):
  `{ time: "HH:MM:SS", timestamp: <epoch ms>, incoming: <num>, origin: <num>, baseline: <num>, event?: string }`
- **`detection`** (no `source_ip` pushed to the client — keep it in the DB
  row / decision-engine logic only):
  `{ prediction: AttackClass, confidence: <num>, risk: "LOW"|"MEDIUM"|"HIGH" }`
  — `risk` must be a real computed value from the decision engine. **Never
  publish this event before the decision engine has run** — there's no
  separate `risk_assessment` event to fill it in later.
- **`mitigation`**: `{ id: string, name: string, status: "PLANNED"|"SIMULATED"|"ACTIVE"|"COMPLETED", result: string, sourceIp: string }`
  — `result` is a human-readable string (e.g. `"Blocked 1,204 malicious requests"`).
- **`status_change`**: `{ status: "NORMAL"|"ATTACK_DETECTED"|"CLASSIFIED"|"MITIGATING"|"RECOVERING"|"RECOVERED" }`

**Delivery pattern:** every producer (detection/decision/mitigation code)
calls one `publish_event(type, data)` helper, which (1) writes to the
`events` table and (2) publishes to Redis `channel:events`. The `/ws/live`
endpoint subscribes to that channel and forwards messages verbatim — never
push directly from business logic into a WebSocket connection object.

```python
async def publish_event(event_type: str, data: dict):
    envelope = {"type": event_type, "timestamp": utcnow_iso(), "data": data}
    await redis.publish("channel:events", json.dumps(envelope))
    # persist the same envelope to the `events` table here too

@app.websocket("/ws/live")
async def ws_live(websocket: WebSocket):
    await websocket.accept()
    pubsub = redis.pubsub()
    await pubsub.subscribe("channel:events")
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_text(message["data"])
    except WebSocketDisconnect:
        await pubsub.unsubscribe("channel:events")
```

On connect, the frontend also calls `GET /api/v1/status` +
`GET /api/v1/events?limit=50` to hydrate before live events start
flowing — otherwise the dashboard is blank on load.
