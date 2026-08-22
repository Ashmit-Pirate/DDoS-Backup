# SAGE — Security Observatory

An ML-based adaptive DDoS protection system frontend, currently running with a sophisticated local simulation engine. 

SAGE visualizes real-time network telemetry, classifies incoming traffic using machine learning inference, and dynamically triggers automated mitigation policies in response to recognized threats.

## Tech Stack
- **Framework:** Next.js 15.2.0 (App Router)
- **Library:** React 19.0.0
- **Language:** TypeScript
- **Styling:** Tailwind CSS (Custom Design System)
- **Animation:** GSAP (`@gsap/react`)
- **Data Visualization:** Recharts
- **Icons:** Lucide React

## Running Locally
```bash
pnpm install
pnpm dev
```

## Routes
- `/` — Overview (Global Telemetry & Status)
- `/live-traffic` — Live Traffic Monitor
- `/detection` — Intelligence & ML Analytics
- `/mitigation` — Decision Engine & Active Policies
- `/incidents` — Historical Threat Incidents
- `/incidents/[id]` — Detailed Incident Analysis
- `/logs` — System Event Logs
- `/attack-lab` — Controlled Simulation Environment
- `/settings` — Configuration & Operations

## State Architecture (`store.tsx`)
The application relies on a strictly typed, globally available React Context (`SageContext`). This context acts as the single source of truth for the entire observatory. The pages themselves contain virtually no complex state, and simply render what the `SageContext` provides.

## Lifecycle
The application strictly enforces a finite state machine:
`NORMAL` → `ATTACK_DETECTED` → `CLASSIFIED` → `MITIGATING` → `RECOVERING` → `RECOVERED`

## Simulation Architecture
The Attack Lab (`/attack-lab`) allows operators to test the system by dispatching an intensity signal (`simulateAttack`). The simulation engine (`src/lib/simulation/engine.ts`) hooks into the `SageContext` and generates organic, mathematically-interpolated telemetry and state events over time, causing the entire frontend to automatically react to an unfolding threat lifecycle.

## Data Architecture
Data is strictly partitioned to enable smooth transition to a real backend API:
- **Static Configuration:** Found in `src/lib/config.ts`. Stores immutable values such as Model Metadata, training metrics, and feature schemas.
- **Runtime State:** Stored inside `SageContext`. Governs the current mitigation execution mode, real-time targets, server health, and traffic baselines.
- **Simulation Data:** The context orchestrates arrays of `TrafficPoint`, `Incident`, `LogEvent`, and `MitigationAction` structs.

## Backend Integration Path
The SAGE UI has been explicitly architected so that integrating a real backend requires **zero UI rewrites**.
1. The `SageContext` provides a generic `dispatchStateUpdate()` setter.
2. To connect real data, a developer simply replaces the `useEffect` block inside `store.tsx` (which currently drives the local simulation math) with a standard WebSocket client.
3. As the WebSocket streams JSON data, map it to the provided types (`PredictionResult`, `TrafficPoint`, `SystemState`) and pass it to `dispatchStateUpdate()`. The UI will flawlessly reflect the incoming real-world state.

## Important Files
- `src/lib/store.tsx` — The core global state context and FSM orchestrator.
- `src/lib/config.ts` — The static model and system constants.
- `src/types/sage.ts` — The centralized TypeScript model definitions.
- `src/components/ui/` — The reusable, abstract layout components (`SectionHeader`, `MetricReadout`, `StatusBadge`, `DataTable`).
- `src/app/globals.css` — Centralized CSS variables driving the entire Tailwind design system.
- `src/components/TrafficGraph.tsx` — The primary Recharts telemetry visualizer.
- `src/components/CustomCursor.tsx` — The hardware-accelerated global cursor Portal.
- `src/components/NavigationRail.tsx` — The primary sidebar layout.
