---
description: Diffs the current WebSocket/REST implementation and ML feature-vector handling against what's documented in ws-contract and ml-integration-boundaries — flags drift before it reaches a teammate.
---

Title: Contract check
Description: Diffs the current implementation against the shared
contracts with the frontend and ML teammates, flags any drift before it
ships.

Steps:
1. Read the current WS envelope implementation (api/schemas.py,
   api/routers/ws.py) and REST route response shapes.
2. Diff against ws-contract: exactly four event types (telemetry,
   detection, mitigation, status_change) with no risk_assessment event;
   detection has risk bundled in and never published null; mitigation
   includes sourceIp and uses only PLANNED/SIMULATED/ACTIVE/COMPLETED;
   status_change is the 6-stage string; /api/v1/events returns
   {incidents, logs} split; no /api/v1/stats exists.
3. Read the current feature-vector handling (detection/feature_mapper.py,
   detection/prediction.py, detection/model_loader.py).
4. Diff against ml-integration-boundaries: gatekeeper uses the full
   77-feature vector, multiclass uses the 65-feature subset derived from
   it (never hardcoded, always loaded from the .pkl column files),
   label_mapping is inverted at load time.
5. Report any drift found, each with the specific location and what it
   should be instead. This is a contract shared with the frontend and ML
   teammates — flag drift explicitly rather than silently resolving it in
   whichever direction seems convenient.
6. If no drift is found, state that explicitly rather than staying
   silent — a clean result should be reported, not just implied.