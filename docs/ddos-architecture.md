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
  cascade (LightGBM gatekeeper → tuned XGBoost classifier, updated
  2026-08-25, replaced an earlier Random Forest) with rate-limiting/
  filtering mitigation only — no autoscaling, no honeypot, no
  unsupervised anomaly detector. See `ddos-project-context.md` for the
  full gap list — don't imply the deck's promises are already built.

## Finalized tech stack for backend

- **Framework**: FastAPI (Python). Chosen because the ML models are
  scikit-learn/LightGBM — an in-process call avoids a cross-language RPC
  hop — and FastAPI gives native async, a built-in WebSocket endpoint,
  and auto-generated OpenAPI docs the frontend can build against.
- **ML runtime**: `xgboost==2.1.4`, `lightgbm==4.6.0`, `scikit-learn==1.3.2`
  (updated 2026-08-25 after hyperparameter tuning — see ML model
  architecture below). scikit-learn remains required even though neither
  model is an `sklearn.ensemble` class — both use sklearn-API wrapper
  classes internally. `imbalanced-learn` is confirmed NOT required.
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
│   ├── models/                  # tuned_models/lightgbm_binary_tuned.pkl,
│   │                            #   tuned_models/xgboost_multiclass_tuned.pkl,
│   │                            #   tuned_models/feature_columns.pkl [single 77-list, shared],
│   │                            #   tuned_models/class_mapping.pkl [invert at load]
│   ├── model_loader.py          # THIS USER'S — loads both models once at startup
│   ├── feature_mapper.py        # THIS USER'S — reindexes to feature_columns.pkl's 77
│   │                            #   names for column-order safety (no subset-dropping
│   │                            #   needed as of the 2026-08-25 model update)
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

**Flow:** API layer receives the flow's 77-feature vector (single vector,
shared by both stages as of 2026-08-25) → calls the **binary LightGBM
gatekeeper** in-process (every flow, ~0.0022 ms) → if Benign, allow and
stop (see Benign-flow logging below); if Attack, escalate to the
**multiclass XGBoost investigator** with the SAME 77-vector (~0.0057 ms)
+ inverted `class_mapping.pkl` for the attack-type string and confidence
→ hands it to the **decision engine**, which pulls recent state from
Redis (rate, repeated-detection count) to compute a risk score/severity —
**the binary gatekeeper's `1` output is a trigger to escalate and log,
never a trigger to block**; blocking is decided solely by the decision
engine (see `ddos-build-plan.md`) → if risk warrants it, the mitigation
engine selects an attack-specific action (**simulation mode first**) →
the event is persisted to Postgres and published to a Redis pub/sub
channel → the WebSocket bridge forwards it to every connected dashboard
client.

## ML model architecture — two-stage cascade (tuned, updated 2026-08-25)

Hyperparameter tuning (`RandomizedSearchCV` + cross-validation across 6
candidate models) replaced the multiclass investigator and eliminated
the earlier two-vector feature split.

| Stage | Model | File | Metric | Latency/flow |
|---|---|---|---|---:|
| 1 — Gatekeeper | Binary LightGBM (tuned) | `lightgbm_binary_tuned.pkl` | 99.94% accuracy | 0.0022 ms |
| 2 — Investigator | Multiclass XGBoost (tuned, replaces Random Forest) | `xgboost_multiclass_tuned.pkl` | 83.49% macro F1 | 0.0057 ms |

Combined worst-case latency for a flagged flow: ~0.0079 ms.

**8 classes**: `Benign, LDAP, MSSQL, NetBIOS, Portmap, Syn, UDP, UDPLag`.

**Pre-tuning evaluation (historical, superseded):**

| Metric | Balanced RF (no longer used) | Normal RF (never used) |
|---|---:|---:|
| Accuracy | 98.55% | 98.66% |
| Macro Precision | 75.14% | 75.50% |
| Macro Recall | 78.46% | 74.52% |
| Macro F1 | 76.59% | 74.95% |

The tuned XGBoost's 83.49% macro F1 is a real improvement over the old
76.59% — macro F1/per-class recall (not raw accuracy) is what matters for
this imbalanced dataset (SYN/Benign/UDP/MSSQL well-represented;
NetBIOS/Portmap/UDPLag scarce). This ~83% precision picture is also *why*
the gatekeeper's `1` output must never be an automatic block.

**Two benchmarked, rejected alternatives from the pre-tuning round:**

| Model | Latency/flow | Why rejected |
|---|---:|---|
| Binary Balanced Random Forest | 0.0094 ms | ~4x slower than Binary LightGBM for no accuracy gain |
| Multiclass LightGBM | 0.0513 ms | Highest raw accuracy of the four at the time, but slowest |

## Feature contract — ONE shared 77-feature vector (updated 2026-08-25)

**History:** from 2026-08-22 to 2026-08-25, the two ML stages needed
different feature vectors (77 for the gatekeeper, a 65-name subset for
the pre-tuning Random Forest). **This is no longer true.** XGBoost
handles the previously-dropped zero-variance columns directly, so both
tuned models were trained on the identical 77-feature array — confirmed
via re-verification (`n_features_in_ == 77` checked for both, not
assumed).

- **Both models** expect the same **77 features**, exact names/order in
  `feature_columns.pkl` — confirmed byte-for-byte identical to the prior
  `binary_feature_columns.pkl`. The wire-format contract with the
  feature-extraction teammate is completely unchanged.
- **Wire format — CORRECTED 2026-08-26**: nested, not a flat 77-key
  object as earlier assumed. Confirmed directly by the ML/feature-
  extraction teammate and independently verified against a live
  Postgres/Redis/uvicorn stack:
  ```json
  { "metadata": { "source_ip": "...", "destination_ip": "...",
                  "source_port": <int>, "destination_port": <int> },
    "features": { /* all 77 named feature keys */ } }
  ```
  Reason given: the model must never see IP/port fields mixed into the
  feature vector. `destination_ip`/`source_port`/`destination_port` are
  accepted by the API but not yet persisted anywhere (only `source_ip`
  is stored, matching the existing `detections` schema). `/detect`
  rejects any other shape (including the old flat format) with a `422`.
- **Divide-by-zero handling** (unchanged): ratio-style features arrive
  already as `0` when the denominator is zero.
- **`class_mapping.pkl`** (renamed from `label_mapping.pkl`, same
  convention): name→index — must be inverted at load time. A first draft
  of the update assumed the opposite direction (would have caused a
  production `KeyError`); self-caught and fixed on re-verification.
- **Model output shape**: `.predict()` may return a bare scalar or
  1-element array — handle both defensively.
- **`predict_proba` confirmed available on both** tuned models.

**Practical implication**: `feature_mapper.py`'s subset-dropping logic is
now dead code — reduced to a single `reindex(columns=feature_columns)`
call kept for column-order safety only. `prediction.py`'s stage 2 call
now passes the exact same 77-length array used in stage 1.

**Verification (UPGRADED 2026-08-25)**: originally confirmed via the ML
teammate's self-report, then independently re-verified by directly
loading all four `tuned_models/*.pkl` files — every claim checked out
exactly (both `n_features_in_ == 77`, exact model classes,
`feature_columns.pkl` byte-for-byte identical to the old file,
`class_mapping.pkl` direction, `predict_proba` on both, exact version
match with zero warnings).

**Known quirk, harmless:** the LightGBM gatekeeper's internal
`feature_name_` uses underscores (`Flow_Duration`) — auto-sanitized at
training time — while `feature_columns.pkl` and the XGBoost model both
use spaces. Tested and confirmed this does not break prediction:
LightGBM's `predict()` matches by column position, not by name.

**Do not copy the ML teammate's illustrative API response shape** — her
example walkthroughs end with a simplified `{"status": "blocked",
"attack_type": "Syn"}`. That's explaining how the *models* chain
together, not a backend API spec. The real response must go through the
decision engine and match the finalized `mitigation` WS event shape (see
below) — never a bare `"blocked"` string assembled straight from the
multiclass output.

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
