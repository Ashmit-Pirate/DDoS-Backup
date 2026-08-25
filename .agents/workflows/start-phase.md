---
description: Kicks off work on a specific phase of the DDoS Protection System's 6-phase backend build plan, scoped correctly and test-gated.
---

Title: Start a DDoS backend build phase
Description: Kicks off work on a specific phase of the 6-phase backend
plan (scaffold, detection wrap, decision engine, mitigation, dashboard
API/WS bridge, deployment), scoped correctly and test-gated.

Steps:
1. Ask which phase number, if not already specified in the prompt.
2. Confirm which prior phases are already built AND tested — do not
   assume from the plan. Run /repo-audit first if repo state is unclear;
   this project has real precedent for "planned" and "actually on disk"
   diverging.
3. Restate the phase's task and DONE/test criteria (from
   ddos-backend-context) before writing any code, so scope is explicit
   up front.
4. Implement per tech-stack, scope-discipline, data-integrity, and — if
   this phase touches detection/, decision/, or mitigation/ —
   ml-integration-boundaries, and — if it touches api/ — ws-contract.
5. Write tests covering every DONE criterion for this phase, including
   simulated-attack/false-positive cases for decision/mitigation code and
   benign-flow non-persistence checks for detection code.
6. Run the test suite. Do not report the phase as complete until tests
   pass — report failures plainly instead of glossing over them.
7. If this phase touches api/ or detection/, run /contract-check before
   declaring it done — these are shared contracts with teammates.
8. Summarize what was built and explicitly list which DONE criteria
   passed and which didn't.