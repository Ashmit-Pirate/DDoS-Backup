---
trigger: always_on
---

Schema and data-lifecycle rules — load-bearing, not stylistic:

- Benign flows are NEVER written to the `detections` table. Increment
  Redis counters (`stats:total_count`, `stats:benign_count`) instead —
  the dashboard's benign% stat is computed from those, not from Postgres.
  Only flows the binary gatekeeper flags as Attack get a `detections` row.
- `mitigation_actions.status` uses exactly these four values: PLANNED,
  SIMULATED, ACTIVE, COMPLETED — matches the frontend's MitigationStatus
  type exactly. Don't introduce other values (e.g. EXPIRED).
- `system_status.status` is the 6-stage lifecycle string (NORMAL,
  ATTACK_DETECTED, CLASSIFIED, MITIGATING, RECOVERING, RECOVERED) — never
  a binary NORMAL/ATTACK.
- Redis TTL on `mitigation:{source_ip}` IS the cooldown auto-unblock
  mechanism. Never implement a separate cron job or polling loop for
  unblocking.
- Indexes on `detections(timestamp)` and `mitigation_actions(source_ip,
  status)` are load-bearing for dashboard query performance — don't drop
  or bypass them with ad hoc queries.
- Every producer of a WebSocket event writes to Postgres AND publishes to
  Redis `channel:events` via one shared `publish_event()` helper — never
  push directly into a WebSocket connection object from business logic.