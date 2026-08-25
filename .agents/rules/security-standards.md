---
trigger: always_on
---

Hackathon-appropriate security checklist — not production-grade, but
still load-bearing for a safe live demo:

- Only load .pkl/.joblib files the team itself trained — joblib.load()
  can execute arbitrary code on load. Fine for our own artifacts, never
  load an untrusted .pkl.
- Secrets (DB credentials, API keys) via environment variables only —
  never commit them, never hardcode them, even in test fixtures.
- Attack simulation traffic (Locust/Scapy) must NEVER be pointed at
  anything except our own isolated Docker network / local target app.
  Never run against shared Wi-Fi, venue networks, or infrastructure we
  don't own — this is a documented pitfall from the project's own
  planning docs, not a hypothetical.
- API authentication is not yet decided (likely skipped for the demo) —
  don't assume this is fine to leave open without flagging it if a task
  touches anything resembling multi-user access; ask first.
- CORS should be locked to the actual dashboard origin for the demo
  environment, not left wildcard, even though this isn't a production
  deployment.
- If a task seems to require weakening any of the above (e.g. "just
  disable CORS for testing"), flag it and ask rather than doing it
  silently.