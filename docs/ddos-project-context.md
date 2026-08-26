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
   cascade** — Binary LightGBM gatekeeper → tuned Multiclass XGBoost
   (updated 2026-08-25, replaced an earlier Random Forest) — the
   opposite paradigm. The gatekeeper does give a genuine "fast first
   line of defense" in practice (0.0022 ms/flow, tuned), closer in
   *spirit* to the deck's framing than a single multiclass model — but
   it's still a trained ML classifier, not a threshold rule engine, and
   there's no unsupervised anomaly detector anywhere in the build. Lead
   with "two-stage tuned ML cascade for speed + accuracy" when this comes
   up, not the rule-engine/anomaly-detector framing.
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
  evaluation, model saved + reload-validated, and (2026-08-25)
  hyperparameter tuning via RandomizedSearchCV + cross-validation across
  6 candidate models — replaced the multiclass investigator with a tuned
  XGBoost classifier and eliminated the earlier 77-vs-65 feature split.
- **Inference**: `prediction.py`, load both tuned models + the single
  shared feature-columns list + class mapping, accept the flow's
  77-feature vector, return class + confidence. *(Backend's scope — see
  `ddos-build-plan.md`.)*
- **Traffic/feature extraction**: controlled traffic input, flow
  extraction, generate the 77-feature vector per flow (single vector,
  shared by both stages as of 2026-08-25). *(ML/feature-extraction
  teammate's scope.)*
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

## Demo strategy (SUPERSEDES the demo script below) — added 2026-08-26

**Status: team decision pending.** A PDF was sent to the team with three
concrete options — check which one was actually chosen before assuming.

DoIT (the team's own Express/MongoDB task-manager app, previously the
target of a real attack-impact test — see `ddos_impact_report.md`) is
the confirmed, authorized demo target if a real attack is used.

**Three options:**
1. **Option 1 — dataset-driven, no target.** BUILT AND VERIFIED,
   2026-08-26 (`docs/demo_runbook_option1.md`,
   `docs/demo_preflight_checklist.md`, 4 demo beats). Safe baseline
   regardless of what else is attempted. Proves detection/decision/
   mitigation intelligence; doesn't claim to protect a website.
2. **Option 2 — real attack on DoIT, fake/simulated protection.**
   AVOID — DoIT would genuinely degrade while the dashboard falsely
   narrates success. Worse than not attempting a live target if noticed.
3. **Option 3 — real attack, real detection, real enforcement.** The
   only option where "we protect a website" is literally true. Needs
   Session 4 (real traffic capture) + Session 5 (real enforcement) — see
   `ddos-build-plan.md`'s Session 4/5 section for the technical plan.
   Real engineering risk if rushed — stretch goal, not a replacement for
   Option 1.

**Recommendation given to the team**: lock in Option 1, treat Option 3
as a stretch goal, avoid Option 2 entirely.

## Original pitch-deck demo script (SUPERSEDED, kept for history)

Dashboard under normal traffic (healthy/green) → launch the attack tool
live from a separate machine → dashboard shows latency spike, detector
flags within seconds, open the "why" panel → show automatic mitigation
(blocked-IP counter, latency recovering — *autoscaling is a pending gap,
don't claim it live*) → close on a metrics card ("Detected in X sec,
mitigated in Y sec, near-zero downtime") → end on the architecture
diagram slide.

**Why superseded**: assumed the deck's pitched architecture (pods
autoscaling, an always-real live attack target) — the "Demo strategy"
section above reflects what's actually been built and decided.

## Pitfalls to watch out for (team-wide, revisit before demo day)

**Real pitfalls discovered during actual build, most load-bearing:**
- **Demo data optimized to guarantee a confidence score is a credibility
  risk, not a win** — already caught once (an early attempt walked the
  trained models' own decision paths; rejected and rebuilt as honest
  synthetic data instead).
- **Option 2 is the riskiest combination available** — see "Demo
  strategy" above.
- **Commit early** — the repo went uncommitted through three full build
  sessions before this was caught and fixed.
- **Windows/OneDrive file-attribute issues can silently break Docker
  builds** — check for reparse-point/sparse-file attributes before
  assuming a code problem if `docker compose up --build` can't read
  `api/` files.

**Original pitch-deck-era pitfalls (partially superseded, kept for reference):**
- **False positives blocking your own demo** — tune thresholds on your
  exact test traffic beforehand. *(Still relevant — thresholds remain
  unvalidated placeholders.)*
- **ML overfitting to the team's own attack tool** — validate on
  CICDDoS2019, not just the synthetic demo pattern. *(Partially moot for
  Option 1 — no real CICDDoS2019 rows were available; still relevant for
  Option 3.)*
- **Network/legal safety** — Scapy/hping3 need elevated privileges and
  can trip campus network security; run only inside an isolated Docker
  network, isolated VM, or NAT'd VirtualBox, never against a shared or
  venue network. *(Only relevant if Option 3 is pursued.)*
- **Unconvincing recovery time** — the real story is the Redis TTL
  cooldown auto-lifting a mitigation, already verified working — not
  the deck's pods-autoscaling framing.
- **"How is this different from Cloudflare/AWS Shield?"** — lead with
  the two-stage tuned ML cascade + explicit no-direct-block decision
  engine, not the deck's honeypot/autoscaling framing.
- **Hackathon Wi-Fi is unreliable** — run the whole demo locally, never
  dependent on venue internet.
- **Always keep a recorded backup video** of a successful full run.

## Safety & isolation (non-negotiable, whole team)

All attack simulation stays limited to infrastructure the team owns or is
explicitly authorized to test. The Docker/Kubernetes environment is the
lab boundary — the simulator is never pointed at public websites,
third-party infrastructure, or any network without explicit
authorization. DoIT is confirmed authorized (the team's own project).


