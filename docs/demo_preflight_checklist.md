# Option 1 Demo: 5-Minute Pre-Flight Checklist

Run this checklist immediately before the presentation begins to ensure a smooth demo.

- [ ] **Docker Containers Running**: 
  - Run `docker compose up -d`
  - Run `docker ps` to verify `ddos-backend`, `ddos-postgres`, and `ddos-redis` are healthy.
- [ ] **Database Migrated**: 
  - Run `docker exec -it ddos-backend alembic upgrade head` to ensure the schema is intact.
- [ ] **Backend Responding**: 
  - Run `curl -s http://localhost:8000/health`. Ensure `models_loaded: true`.
- [ ] **Frontend Started**: 
  - In the `dashboard` directory, run `npm run dev`.
- [ ] **Browser Prepared**: 
  - Open `http://localhost:3000`. (Do **NOT** use `127.0.0.1` or network IP to avoid CORS errors).
- [ ] **Simulation Badge Gone**: 
  - Ensure the amber "Simulation Mode" badge has disappeared from the bottom right, confirming active WebSocket connections.
- [ ] **Terminals Ready**: 
  - Have a terminal window open and ready to paste the exact `curl` commands from `docs/demo_runbook_option1.md`.
- [ ] **Payload Files Exist**:
  - Verify `docs/payload_benign.json`, `docs/payload_syn.json`, and `docs/payload_udp.json` exist.

**REMINDER**: Do not click or interact with the "Config" / threshold settings on the dashboard during the live demo; they are not fully wired to the backend decision engine yet. Mitigation actions will display as `SIMULATED`, demonstrating the decision-making process without enacting actual firewall rules.
