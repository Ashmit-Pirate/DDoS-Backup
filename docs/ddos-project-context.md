# DDoS Protection System — Whole-Project Context

**Status: finalized reference for whole-project background** — the
pitch, team, and non-backend picture. For backend/database implementation
detail, see `ddos-architecture.md` and `ddos-build-plan.md`; this doc is
the broader context those two don't repeat.

## Problem statement

**DDoS Protection System for Cloud: Architecture and Tool** — PS05, DJSCE
SIH 2026 internal hackathon. Team ID **SIH26_206**, team name **Bit by
Bit**. Domain: Cybersecurity / Cloud Infrastructure. Category: Software.

**The problem:** cloud-hosted services face DDoS floods that closely
mimic legitimate traffic spikes; static thresholds and manual monitoring
can't keep pace with adaptive, multi-vector floods. Affects cloud-hosted
businesses/SaaS, end-users relying on uptime, DevOps/SRE/security teams,
and SMEs without enterprise WAF budgets. Current pain points: slow manual
triage, false positives blocking genuine users, costly/opaque commercial
tools, and self-hosted setups lacking auto-recovery.

## Team composition

| Member | Role |
|---|---|
| 1 | Cloud Infrastructure & DevOps (Docker, Kubernetes, Nginx) |
| 2 | ML / Detection Engineering (Anomaly Detection, Python) |
| 3 | **Backend & Mitigation Controller** (API Automation, Scripting) — owns the scope in `ddos-architecture.md`/`ddos-build-plan.md` |
| 4 | Frontend & Dashboard (Next.js, Visualization) |
| 5 | Security Testing & Attack Simulation (Red-teaming, QA) |
| 6 | Research, Documentation & Presentation (Literature, Pitch) |

## Proposed solution — four-layer architecture (as pitched)

1. **Sensing layer** — extracts traffic features in short time windows:
   requests/sec per IP, unique-IP entropy, per-endpoint hit distribution,
   TCP flag ratios, User-Agent/device fingerprint diversity, geolocation
   skew, inter-arrival time periodicity.
2. **Detection layer (hybrid, as pitched)** — rule-based fast path
   (instant thresholds, catches obvious volumetric floods in under a
   second) + ML-based path (Isolation Forest/One-Class SVM or an
   LSTM-Autoencoder, catches stealthy low-and-slow application-layer
   attacks). **See "Pitch vs. actual build" below — this is NOT what's
   actually built.**
3. **Mitigation & self-healing layer (as pitched)** — dynamic
   firewall/rate-limit updates, Kubernetes HPA to absorb volumetric
   spikes, honeypot/decoy rerouting, automatic cooldown-based unblocking.
   **See gaps below — HPA and honeypot are not in the actual plan.**
4. **Explainability dashboard** — live traffic graph, status indicator,
   blocked-IP list, time-to-detect/time-to-mitigate metrics, and a "why
   was this flagged" feature panel.

## ⚠️ Pitch vs. actual build — known gaps (don't paper over these)

1. **Detection method.** Deck's headline claim is hybrid rule-engine +
   unsupervised anomaly detection, explicitly pitched as not needing
   labeled signatures. What's actually built is a **two-stage supervised
   cascade** — Binary LightGBM gatekeeper → Multiclass Random Forest — the
   opposite paradigm. The gatekeeper does give a genuine "fast first
   line of defense" in practice (0.0026 ms/flow), closer in *spirit* to
   the deck's framing than a single multiclass model — but it's still a
   trained ML classifier, not a threshold rule engine, and there's no
   unsupervised anomaly detector anywhere in the build. Lead with
   "two-stage ML cascade for speed + accuracy" when this comes up, not
   the rule-engine/anomaly-detector framing.
2. **Mitigation scope.** Deck promises Kubernetes autoscaling and
   honeypot rerouting. The actual mitigation policy only covers rate
   limiting, filtering, and exposure restriction — no autoscaling or
   honeypot logic is planned or built.
3. **Dashboard tech — resolved.** Deck listed Grafana OR React+WebSocket
   as options; team has confirmed **Next.js + WebSocket push**, no
   polling. Settled, not a gap.
4. **Attack simulation tooling.** Deck names Scapy (volumetric) + Locust
   (L7) specifically; carry the specific tools into the actual
   `simulator.py` rather than a generic description.
5. **Explainability metrics.** The deck's "why flagged" panel and
   time-to-detect/time-to-mitigate metrics are a headline feature — make
   sure they're explicit in the dashboard build, not just a pitch
   promise. The backend's `risk_assessments.factors` payload is designed
   to feed this panel.

## Literature survey & innovation positioning (from the pitch deck)

**Identified gap** (deck's own framing): no open, self-hostable system
combines fast rule-based response, ML-based anomaly detection, automatic
mitigation, and explainability in one architecture. Compared against:
rule-based rate limiting, statistical/entropy anomaly detection, ML
classifiers (SVM/RF), deep learning sequence models (LSTM/CNN), and
commercial WAF/scrubbing (Cloudflare-style).

**Innovation table (as pitched):**

| Dimension | Existing approaches | This system (as pitched) |
|---|---|---|
| Detection method | Rules OR ML alone | Hybrid rule + ML with escalation/voting |
| Response | Manual/static rules | Automatic mitigation, self-healing (autoscale + honeypot) |
| Transparency | Black-box | Explainable "why flagged" panel |
| Deployment | Proprietary/commercial | Open, self-hostable |

**References cited**: Mirkovic & Reiher (2004, DDoS taxonomy, ACM SIGCOMM
CCR); Zargar, Joshi & Tipper (2013, DDoS defense survey, IEEE Comm.
Surveys); Yuan, Li & Li (2017, DeepDefense, IEEE SMARTCOMP); Sharafaldin,
Lashkari, Hakak & Ghorbani (2019, CICDDoS2019 dataset/taxonomy, IEEE
ICCST); Cloudflare DDoS Threat Report (Cloudflare Radar).

## Whole-project roadmap

**Original pitch-level roadmap** (6 phases, superseded in practice by the
backend's own 6-phase plan in `ddos-build-plan.md` for phases 3-4):
1. Target Infrastructure — Dockerize, Nginx, K8s cluster,
   Prometheus/Grafana.
2. Attack Simulation Tool — Scapy/hping3 (volumetric) + Locust (L7).
3. Detection Engine — feature pipeline, rule fast-path, ML anomaly
   detector, escalation logic.
4. Mitigation & Recovery — controller, K8s HPA, honeypot, cooldown
   unblock.
5. Dashboard & Explainability.
6. Rehearse the demo end-to-end.

**ML-side roadmap** (from the technical context doc):
- ✅ **Completed**: dataset obtained/cleaned, train/test split, binary +
  multiclass experiments, Random Forest, Balanced Random Forest, model
  evaluation, model saved + reload-validated.
- **Inference**: `prediction.py`, load both models + feature columns +
  label mapping, accept the correct feature vector per model, return
  class + confidence. *(Backend's scope — see `ddos-build-plan.md`.)*
- **Traffic/feature extraction**: controlled traffic input, flow
  extraction, generate BOTH the 77-feature and 65-feature vectors per
  flow. *(ML/feature-extraction teammate's scope.)*
- **Decision & Mitigation**: backend's scope, see `ddos-build-plan.md`.
- **Dashboard**: live traffic graph, attack stats, confidence,
  risk/severity, mitigation status, event logs. *(Frontend teammate's —
  already built against the finalized WS contract.)*
- **Deployment**: Dockerize, local prototype, K8s deploy, connect
  protected app, controlled DDoS simulation.
- **Validation**: benign/attack-type tests, false-positive/negative
  evaluation, detection & mitigation latency, server availability,
  end-to-end demo.

## Testing strategy (whole project)

Staged, in an isolated Docker/K8s lab only — never against public or
venue infrastructure:
1. Normal traffic only — establish baseline, verify no false positives.
2. Low-intensity simulated attack — mitigation stays in simulation mode.
3. Higher-intensity attack — measure detection accuracy/latency,
   confidence, false pos/neg, mitigation latency, server availability.
4. All 7 attack classes individually.

Recommended to combine three traffic sources: a legitimate-traffic
generator (false-positive measurement), the controlled Python attack
simulator (reproducible attack traffic), and PCAP/dataset replay
(validates the feature pipeline matches training-data behavior — catches
feature bugs a synthetic simulator wouldn't reveal). **Chosen approach for
this project: replay CICDDoS2019 test-set rows as "live" flows**, with
the live attack simulator controlling *which* labeled rows get streamed
(Benign when idle, matching-attack-class when an attack is launched) —
this guarantees feature correctness (real dataset values, zero
feature-engineering translation risk) while keeping the demo's
attack-button-to-dashboard-reaction causality real.

## Live demo script (4-5 min, as planned)

Dashboard under normal traffic (healthy/green) → launch the attack tool
live from a separate machine → dashboard shows latency spike, detector
flags within seconds, open the "why" panel → show automatic mitigation
(blocked-IP counter, latency recovering — *autoscaling is a pending gap,
don't claim it live*) → close on a metrics card ("Detected in X sec,
mitigated in Y sec, near-zero downtime") → end on the architecture
diagram slide.

## Pitfalls to watch out for (team-wide, revisit before demo day)

- **False positives blocking your own demo** — tune thresholds on your
  exact test traffic beforehand.
- **ML overfitting to the team's own attack tool** — validate on
  CICDDoS2019, not just the synthetic demo pattern.
- **Network/legal safety** — Scapy/hping3 need elevated privileges and
  can trip campus network security; run only inside an isolated Docker
  network, isolated VM, or NAT'd VirtualBox, never against a shared or
  venue network.
- **Unconvincing recovery time** — pre-warm pods, use fast-triggering
  thresholds so recovery is visibly quick.
- **"How is this different from Cloudflare/AWS Shield?"** — lead with
  hybrid detection + auto-recovery *(mind the honeypot/autoscaling gaps
  above when answering this live)*.
- **Hackathon Wi-Fi is unreliable** — run the whole demo locally, never
  dependent on venue internet.
- **Always keep a recorded backup video** of a successful full run.

## Safety & isolation (non-negotiable, whole team)

All attack simulation stays limited to infrastructure the team owns or is
explicitly authorized to test. The Docker/Kubernetes environment is the
lab boundary — the simulator is never pointed at public websites,
third-party infrastructure, or any network without explicit
authorization.
