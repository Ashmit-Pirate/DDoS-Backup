# DDoS Protection System — Build Plan & Standards

**Status: planning finalized.** Companion to `ddos-architecture.md`. This
is the sequential, build-and-test-gated phase plan — do not skip ahead or
start a phase whose prerequisites aren't built AND tested yet. Check repo
state rather than assuming a phase is done (see "Verifying repo state"
at the end) — this project has real precedent for "planned" and
"actually on disk" diverging.

## 6-phase build plan (sequential, test-gated)

1. **Scaffold** — FastAPI app + `docker-compose.yml` bringing up Postgres
   + Redis, `/health` endpoint. Test: all three containers start, health
   check returns 200.
2. **Detection wrap** — `POST /api/v1/detect` calls the binary LightGBM
   gatekeeper in-process first, using the 77-feature vector (every
   request); if Benign, increments `stats:total_count`/`stats:benign_count`
   and stops (no `detections` row). If Attack, escalates to the
   multiclass Random Forest using the 65-feature vector (derived from the
   77 in `feature_mapper.py`) + inverted `label_mapping.pkl` for the
   attack-type string, then writes a `detections` row. Can start before
   feature extraction is finished using stub vectors of the correct
   lengths (77 and 65). Test: known benign input → counters increment, no
   row written; known attack input → correct class + confidence, matches
   the ML teammate's own evaluation, `detections` row written.
3. **Decision engine** — risk scoring backed by the Redis counters
   (`rate:{source_ip}`, `detect:{source_ip}:{attack_type}`,
   `mitigation:{source_ip}`), thresholds pulled from `config`. Test:
   high-confidence sustained SYN → HIGH severity; single low-confidence
   flag → LOW/no action.
4. **Mitigation engine, simulation mode** — attack-specific policy table,
   writes `mitigation_actions`, Redis TTL implements cooldown
   auto-expiry. Test: simulated SYN attack produces a logged RATE_LIMIT
   action that auto-expires after the cooldown window.
5. **Dashboard-facing API + WebSocket bridge** — `events`/`status`/
   `mitigation/active`/`config` endpoints (no `/stats`), `/ws/live` with
   the Redis pub/sub bridge. Test: trigger a detection → connected WS
   client receives all four event types (`telemetry`, `detection`,
   `mitigation`, `status_change`) in the finalized frontend-matching
   shape, within the demo's target latency.
6. **Containerize** — Dockerfile for the backend service, wired into
   `docker-compose.yml` and the `k8s/` manifests. Test: full stack up via
   `docker-compose up`, end-to-end flow works with no manual steps.

## Model routing per phase (Antigravity)

| Phase | What it is | Model | Why |
|---|---|---|---|
| 1 — Scaffold | FastAPI skeleton, docker-compose, health check | Gemini 3.6 Flash (high) | Mechanical, well-specified boilerplate |
| 2 — Detection wrap | `/api/v1/detect`, in-process `.pkl` calls, `detections` row | Gemini 3.6 Flash (high) — switch to Opus if the feature contract with the ML teammate turns out ambiguous mid-build | Mostly mechanical, one precision-sensitive integration point |
| 3 — Decision engine | Risk scoring, Redis rate/repeat counters, threshold logic | **Opus 4.6 (thinking)** | A subtle bug here causes a false negative or false positive — the core claim of the whole project |
| 4 — Mitigation engine (simulation mode) | Attack-specific policy, `mitigation_actions` writes, Redis TTL cooldown | **Opus 4.6 (thinking)** | Same reasoning as phase 3 — cooldown/TTL timing mistakes are load-bearing |
| 5 — Dashboard API + WS bridge | REST endpoints, Redis pub/sub → WS forwarding, typed envelope | Gemini 3.6 Flash (high) for plumbing; Opus if connection-state/concurrency bugs show up | Mostly mechanical, with one concurrency-sensitive area |
| 6 — Containerize | Dockerfile, compose wiring, k8s manifest hookup | Gemini 3.6 Flash (high) | Mechanical config |

**Rule of thumb:** if a subtle bug would cause a false negative, false
positive, or a cooldown/TTL timing mistake → Opus. If it's mechanical,
well-specified boilerplate → Flash. Phases 3 and 4 are load-bearing for
this project specifically — don't downgrade those two to save time.

Skip Gemini 3.1 Pro for fresh-build phases; its value is a large context
window for reasoning across an already-large existing codebase, which
doesn't apply while building from scratch. Reconsider if the repo grows
large enough that reconciling backend code against teammates' code late
in integration becomes the task itself.

## Decision engine logic

**Never** `if prediction != "Benign": block()` — applies to **both** ML
stages, including the binary gatekeeper. The ML teammate's own
integration guide described the gatekeeper's `1` output as a direct block
trigger — **that instruction is not followed as written.** The
gatekeeper's `1` is treated purely as an **escalation trigger** (run the
multiclass model, log a `detections` row, feed the decision engine) —
never a block trigger by itself. The actual block/mitigate decision is
made exclusively by the decision engine, using the multiclass model's
predicted class + confidence, not the gatekeeper's raw verdict. This
preserves the gatekeeper's real value (a ~5x-cheaper triage filter that
lets the multiclass model skip most legitimate traffic) without
reintroducing a direct ML→block path.

The decision engine sits between prediction and enforcement and weighs:
predicted class + confidence (multiclass stage), traffic rate
(`rate:{source_ip}`), repeated detections
(`detect:{source_ip}:{attack_type}`), and current mitigation state
(`mitigation:{source_ip}`) — producing a risk score → severity
(LOW/MEDIUM/HIGH) → mitigation decision. A middle "suspicious" tier
(monitor → rate-limit → re-evaluate → escalate) exists specifically to
protect legitimate users, since the model's macro precision (~75%) means
some false positives are expected, concentrated in the minority classes
(NetBIOS, Portmap, UDPLag).

**Starting-point placeholder thresholds** (illustrative, NOT tuned — MUST
be validated against real CICDDoS2019-style test traffic before demo
day): confidence > 0.95 AND repeat_count >= 3 → HIGH; confidence > 0.80 →
MEDIUM; below that → LOW/suspicious tier (monitor, don't mitigate yet).
Exact numbers should ultimately live in the `config` table, not be
hardcoded.

**Event-publish ordering rule:** the `detection` WS event's `risk` field
must carry the actual computed severity from the decision engine — never
publish the `detection` event before the decision engine has run and
produced a real risk value. Compute prediction → run the decision engine
→ THEN publish, with `risk` filled in from that result.

## Mitigation policy — attack-specific, staged

| Traffic/attack | Action |
|---|---|
| Benign | Allow, no mitigation |
| SYN | Connection rate limiting |
| UDP | UDP rate limiting + filtering |
| MSSQL | Restrict exposure + rate controls |
| LDAP | LDAP-specific filtering + rate limiting |
| NetBIOS | Restrict unnecessary NetBIOS traffic |
| Portmap | Restrict portmapper/RPC exposure |
| UDPLag | Rate limiting + suspicious-flow filtering |
| Repeated high-confidence attack | Escalate, temporary source block |

**Staged rollout, not optional:**
1. **Simulation mode** (default, built first) — decision + mitigation
   logic runs fully, writes to `mitigation_actions` with
   `status='SIMULATED'`, nothing touches a real firewall.
2. **Controlled enforcement** — only after simulation-mode logic is
   tested; real enforcement (nftables / NGINX rate limiting / WAF rules)
   is the infra teammate's integration point, called from
   `mitigation_engine.py`.

## Key design decisions (reference — don't re-litigate)

- **No direct ML → block.** Decision engine is mandatory, not a
  passthrough, at both ML stages.
- **Two data stores, deliberately.** Redis for anything needing a TTL or
  sub-second reads; Postgres for anything that must survive a restart or
  get queried historically.
- **Staged mitigation** — simulation mode is the default; real
  enforcement is a separate, later step.
- **Typed WebSocket envelope, routed through Redis pub/sub** — never push
  from business logic straight into a socket; keeps this horizontally
  scalable.
- **Attack-specific mitigation, not a generic block-everything action.**
- **Backend conforms to the frontend's contract, not the reverse** —
  frontend's types were treated as source of truth once found to be more
  dashboard-ready than the original backend draft.
- **Blocked-IP list is derived, not a new feature** — rides on the
  existing `mitigation` event/table via one added field (`sourceIp`).
- **Two-stage ML cascade, gatekeeper never blocks directly** — an
  explicit override of the ML teammate's own suggested shortcut.
- **Benign flows aren't persisted to Postgres** — Redis counters feed the
  dashboard's benign% stat instead.
- **Two different feature vectors** (77 vs. 65) — not one shared vector,
  confirmed by direct `.pkl` inspection and the ML teammate independently.

## Security checklist (hackathon-appropriate, still load-bearing)

- Only load `.pkl`/`.joblib` files the team itself trained —
  `joblib.load()` can execute arbitrary code on load. Fine for our own
  artifacts, never load an untrusted `.pkl`.
- Secrets (DB credentials, API keys) via environment variables only —
  never commit them, never hardcode them, even in test fixtures.
- Attack simulation traffic (Locust/Scapy) must NEVER be pointed at
  anything except our own isolated Docker network / local target app.
  Never run against shared Wi-Fi, venue networks, or infrastructure we
  don't own.
- API authentication is not yet decided (likely skipped for the demo) —
  don't assume this is fine to leave open without flagging it if a task
  touches anything resembling multi-user access; ask first.
- CORS should be locked to the actual dashboard origin for the demo
  environment, not left wildcard, even though this isn't a production
  deployment.
- If a task seems to require weakening any of the above (e.g. "just
  disable CORS for testing"), flag it and ask rather than doing it
  silently.

## Not yet decided (flag rather than invent if it comes up)

- API authentication (none discussed yet).
- Exact ORM (SQLAlchemy assumed as the default, not yet explicitly
  reconfirmed with the team).
- Whether raw per-flow feature vectors get persisted anywhere (current
  schema deliberately does NOT store them, to keep storage light).
- Decision-engine thresholds are placeholders — need real validation
  against test traffic before demo day, not tuned yet.

## Verifying repo state before starting a phase

Don't trust this document's phase list alone to know what's actually
built — check the real repo. This project has hit real drift between
"planned" and "on disk" more than once, including one inventory scan that
was accidentally run against an unrelated repository entirely. Before
starting or resuming a phase:
1. Confirm you're actually in the DDoS-Mitigator monorepo (should contain
   `dashboard/` and `ml_models/`, not an unrelated app).
2. Check which top-level folders (`api/`, `db/`, `decision/`,
   `mitigation/`) actually have content, and whether existing code passes
   its own tests, rather than assuming a phase is "done" because this doc
   lists it in sequence.
