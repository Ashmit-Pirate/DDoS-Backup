---
description: Run before moving to the next phase — verifies the current phase actually meets its DONE criteria, contract commitments, and relevant security items before declaring it finished.
---

Title: Phase gate check
Description: Run before moving to the next phase — verifies the current
phase actually meets its DONE criteria before declaring it finished.

Steps:
1. Identify which phase is being gated.
2. Run the full test suite for whatever was touched this phase.
3. Go through that phase's DONE/test criteria one by one and report
   pass/fail for each — don't summarize, enumerate.
4. Check the rule-set items actually relevant to this phase:
   - decision/ or mitigation/ touched: ml-integration-boundaries
     compliance — no direct prediction-to-block shortcut, mitigation
     defaults to SIMULATED.
   - api/ touched: run /contract-check — WS envelope and REST shapes
     must match ws-contract exactly.
   - detections/mitigation_actions/system_status touched: data-integrity
     — benign flows not persisted, correct status enum values, Redis TTL
     is the only cooldown mechanism.
   - anything touching secrets, the .pkl files, or network config: run
     /security-audit.
5. Report a clear go/no-go: only recommend moving to the next phase if
   every criterion and every relevant rule check passed.