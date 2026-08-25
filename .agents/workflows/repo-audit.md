---
description: Scans the actual repo state and reports what exists vs. what the plan says should exist — run when repo state is unclear or before trusting "phase X is done" without verification.
---

Title: Repo audit
Description: Produces a factual inventory of what's actually on disk,
cross-checked against the documented plan — this project has real
precedent for the two diverging, including one run of this exact check
that was accidentally pointed at an unrelated repo.

Steps:
1. Confirm the current folder is actually the DDoS-Mitigator monorepo —
   it should contain dashboard/ and ml_models/, not an unrelated app.
   Stop and flag if it doesn't look right rather than proceeding.
2. Produce a per-top-level-folder inventory (api/, db/, detection/,
   decision/, mitigation/, dashboard/, docker/, k8s/): what exists, what
   status (NOT FOUND / STUB / PARTIAL / COMPLETE), read files rather than
   guessing from filenames.
3. Explicitly confirm presence and exact path of all five ML artifact
   files, and whether feature_extractor.py / any flow-generation or
   packet-capture code exists.
4. Confirm whether env vars referenced in code (e.g. NEXT_PUBLIC_WS_URL,
   NEXT_PUBLIC_API_BASE_URL) are actually declared in any .env/.env.example
   file, not just assumed present.
5. Report drift explicitly: anywhere the plan (project-plan rule /
   ddos-backend-context) says something should exist and it doesn't, or
   vice versa. Don't soften or summarize away a gap — absence is
   information the next task needs.