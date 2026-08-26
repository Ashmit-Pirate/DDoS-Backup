# DDoS Mitigation System: Option 1 Demo Runbook

This runbook guides you through a fully verified, dataset-driven demonstration of the DDoS Protection System (Option 1). **Note:** This demonstration does not use a real target website, does not capture live local network traffic, and does not perform actual firewall block enforcement. The mitigation system operates safely in `SIMULATED` mode.

### About the Demo Data (Provenance)
Because the official raw CICDDoS2019 dataset CSVs are extremely large (gigabytes) and distributed primarily through gated academic portals (like Kaggle or Mendeley) rather than raw public URLs, this demo uses **fully synthetic but structurally realistic 77-feature payload vectors**. These vectors were computationally crafted to mimic genuine flow properties (e.g., maintaining consistent packet-to-byte ratios and flow durations) while ensuring they cleanly trigger the exact >0.95 confidence thresholds required by both the ML gatekeeper and multiclass models to properly execute the demo beats below.

## 0. Pre-Flight Verification & Setup

Before the demo begins, ensure the environment is pristine and fully operational. 

1. **Start the Backend:**
   ```bash
   docker compose up -d
   ```
2. **Apply Database Migrations:**
   ```bash
   docker exec -it ddos-backend alembic upgrade head
   ```
3. **Verify Backend Health:**
   Ensure the backend is online and models are loaded:
   ```bash
   curl -s http://localhost:8000/health
   ```
   *Expected Output: `{"status":"ok","database":"connected","redis":"connected","models_loaded":true}`*

4. **Start the Dashboard:**
   Open a new terminal window:
   ```bash
   cd dashboard
   npm run dev
   ```
   Navigate to `http://localhost:3000` in your browser.
   *Crucial Check:* Verify that the amber "Simulation Mode" badge (bottom right) **disappears** shortly after loading. This confirms the WebSocket has successfully authenticated the CORS origin and is actively streaming.

---

## 1. Demo Beat: Benign Traffic Flow
**Dashboard Page:** `Live Traffic` & `Detection`

Explain that regular traffic flows smoothly through the multi-stage machine learning pipeline. The gatekeeper evaluates it in milliseconds and permits it without wasting extensive compute.

**Command:**
```bash
curl -s -X POST http://localhost:8000/api/v1/detect -H "Content-Type: application/json" -d @docs/payload_benign.json
```
* **What to point out:** 
  - On the `Live Traffic` dashboard, incoming traffic registers but nothing turns red. 
  - The API response explicitly shows `gatekeeper_confidence` extremely low (e.g. `0.009`), `predicted_class` as `Benign`, and `action` as `ALLOW`.

---

## 2. Demo Beat: Single Attack Flow (No Direct Block)
**Dashboard Page:** `Detection` & `Logs`

Explain that the system avoids false-positive drops. An isolated anomaly might look like an attack, but the decision engine requires context (rate and repetition) before applying a harsh mitigation.

**Command:**
```bash
curl -s -X POST http://localhost:8000/api/v1/detect -H "Content-Type: application/json" -d @docs/payload_syn.json
```
* **What to point out:**
  - The model recognizes the attack with high confidence (e.g. `0.98`), correctly labeling it `Syn`.
  - However, the decision engine only escalates the severity to `MEDIUM` and the action to `MONITOR`. 
  - The `Logs` page will show a new entry: `MONITOR — traffic flagged, no mitigation triggered`. **No block occurred.**

---

## 3. Demo Beat: Sustained Attack (Triggering Mitigation)
**Dashboard Page:** `Mitigation` & `Incidents`

Explain that as the same IP continues to assault the network, the repeated-detection counter dynamically increases the risk score until it crosses the threshold.

**Command:** (Run this exact command two times in a row)
```bash
curl -s -X POST http://localhost:8000/api/v1/detect -H "Content-Type: application/json" -d @docs/payload_syn.json
curl -s -X POST http://localhost:8000/api/v1/detect -H "Content-Type: application/json" -d @docs/payload_syn.json
```
* **What to point out:**
  - Upon the final call, the `risk_score` exceeds the threshold (e.g., jumps to ~94), escalating the severity to `HIGH`.
  - The `Mitigation` page instantly updates with a new active rule for `3.3.3.3` with the policy `RATE_LIMIT`.
  - Emphasize that the status is explicitly `SIMULATED`—the system has formulated and logged the exact required response without breaking local network connectivity.

---

## 4. Demo Beat: Diverse Threat Vectors
**Dashboard Page:** `Mitigation`

Demonstrate that the mitigation engine isn't static; it applies different firewall strategies tailored precisely to the specific type of attack identified by the ML investigator.

**Command:** (Run this exact command 3 times in a row)
```bash
curl -s -X POST http://localhost:8000/api/v1/detect -H "Content-Type: application/json" -d @docs/payload_udp.json
curl -s -X POST http://localhost:8000/api/v1/detect -H "Content-Type: application/json" -d @docs/payload_udp.json
curl -s -X POST http://localhost:8000/api/v1/detect -H "Content-Type: application/json" -d @docs/payload_udp.json
```
* **What to point out:**
  - A new mitigation rule appears for `4.4.4.4`.
  - Unlike the Syn attack which resulted in `RATE_LIMIT`, this UDP attack correctly prompts a `RATE_LIMIT_AND_FILTER` policy, proving the dynamic nature of the mitigation engine.

---

## Troubleshooting Guide

- **Badge Stuck on "Simulation Mode"**: 
  - **Check:** Ensure the backend is actually running on port `8000` (`curl http://localhost:8000/health`).
  - **Check:** Ensure `dashboard/.env.local` uses `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` and `NEXT_PUBLIC_WS_URL=ws://localhost:8000`.
  - **Check:** Verify you are accessing the dashboard via `http://localhost:3000`. Accessing it via `127.0.0.1` or an IP address will violate the CORS `ALLOWED_ORIGINS` and silently drop the WebSocket upgrade.

- **No Events Appearing on Dashboard**:
  - Verify that the Docker containers (specifically `ddos-redis`) are healthy. The WebSocket strictly relies on Redis PubSub to broadcast events across the microservices.
