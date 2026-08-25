---
trigger: always_on
---

Full backend specification lives in this repo's docs — read
@/docs/ddos-architecture.md, @/docs/ddos-build-plan.md, and
@/docs/ddos-project-context.md before starting any task that isn't
purely mechanical.

These cover: finalized architecture, full database schema, the
WebSocket/REST contract (reconciled with the frontend's existing types —
backend conforms to them, not the reverse), the ML feature contract
(confirmed with the ML teammate, not just assumed), the 6-phase build
plan with model routing, and the whole-project pitch/team/demo context.

Treat all of it as settled. Do not re-derive architecture, schema, or
scope from scratch. Do not start a phase whose prerequisites aren't built
AND tested yet — check the actual repo state rather than assuming from
the docs alone; this project has real precedent for "planned" and
"actually on disk" drift.