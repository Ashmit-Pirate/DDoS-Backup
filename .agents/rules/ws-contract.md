---
trigger: glob
globs: api/routers/ws.py,api/schemas.py,api/routers/**
---

The WebSocket/REST contract with the frontend is FINALIZED and
asymmetric on purpose — backend was made to conform to the frontend's
existing types (sage.ts), not the reverse. If something conflicts, flag
it, don't silently resolve it either direction.

- Four WS event types only, envelope `{type, timestamp, data}`:
  telemetry, detection, mitigation, status_change. No separate
  risk_assessment event — risk is bundled into `detection`.
- `detection`: `{prediction, confidence, risk}` — no source_ip pushed to
  the client. `risk` must be a real computed value from the decision
  engine — never publish this event before the decision engine has run.
- `mitigation`: `{id, name, status, result, sourceIp}` — sourceIp powers
  the dashboard's derived blocked-IP list (frontend filters
  status === 'ACTIVE' client-side; no separate blocked-IP endpoint
  exists).
- `status_change`: the full 6-stage lifecycle string, not binary.
- REST: GET /api/v1/events returns `{incidents, logs}` split, not a
  generic feed. GET /api/v1/status returns the 6-stage string. GET
  /api/v1/mitigation/active includes sourceIp. GET/PUT /api/v1/config
  matches RuntimeSystemConfig. There is NO /api/v1/stats — dropped, the
  frontend builds graphs off the telemetry stream only.
- Every producer publishes through Redis `channel:events`, never directly
  into a WebSocket connection.