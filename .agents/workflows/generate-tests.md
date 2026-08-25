---
description: Generates tests for a specified backend module against its phase's DONE criteria, including attack-simulation and false-positive cases.
---

Title: Generate tests for a module
Description: Generates tests for a specified module against its phase's
DONE criteria.

Steps:
1. Identify the module and which phase's DONE criteria it corresponds to
   (ask if unclear).
2. pytest, covering each DONE criterion, plus module-specific cases:
   - detection/: benign flow → no detections row written, both Redis
     counters increment; attack flow of each of the 7 classes → correct
     label after inversion; scalar-vs-array model output both handled.
   - decision/: false-positive/suspicious-tier case (low confidence
     never mitigates); repeated-detection escalation to HIGH; no
     direct-block shortcut anywhere in the code path.
   - mitigation/: every action defaults to SIMULATED status; correct
     attack-specific policy selected per class.
   - api/ or ws.py: event shape conformance — each of the four event
     types matches ws-contract exactly, detection's risk field is never
     null.
3. Name test files with the project's existing convention.
4. Run the generated tests and report pass/fail — fix failures that stem
   from the test itself being wrong; report failures that reveal a real
   bug rather than papering over them.