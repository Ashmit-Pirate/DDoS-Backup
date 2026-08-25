# Project Inventory Report

## Summary Table

| Component | Status | Note |
|---|---|---|
| frontend/dashboard | COMPLETE | Next.js dashboard exists, builds successfully, includes WebSocket client. |
| backend API | NOT FOUND | `api/` directory does not exist. |
| database layer | NOT FOUND | `db/` directory does not exist. |
| ML models | COMPLETE | Pickled model artifacts located in `ml_models/`. |
| feature extraction | NOT FOUND | No `feature_extractor.py` or flow generation code present. |
| traffic simulator | NOT FOUND | No `simulator.py` present. |
| decision engine | NOT FOUND | `decision/` directory does not exist. |
| mitigation engine | NOT FOUND | `mitigation/` directory does not exist. |
| Docker/infra | NOT FOUND | No Dockerfiles, compose files, or `k8s/` directories present. |

---

## 1. Full Directory Tree

```
DDoS-Mitigator/
    .gitignore
    AGENTS.md
    CLAUDE.md
    pnpm-lock.yaml
    pnpm-workspace.yaml
    dashboard/
        AGENTS.md
        CLAUDE.md
        eslint.config.mjs
        next-env.d.ts
        next.config.ts
        package.json
        postcss.config.mjs
        README.md
        tsconfig.json
        public/
            file.svg
            globe.svg
            next.svg
            vercel.svg
            window.svg
        src/
            app/
                favicon.ico
                globals.css
                layout.tsx
                page.tsx
                attack-lab/
                    page.tsx
                detection/
                    page.tsx
                incidents/
                    page.tsx
                incidents/[id]/
                    page.tsx
                live-traffic/
                    page.tsx
                logs/
                    page.tsx
                mitigation/
                    page.tsx
                settings/
                    page.tsx
            components/
                CustomCursor.tsx
                NavigationRail.tsx
                TrafficGraph.tsx
                ui/
                    DataTable.tsx
                    MetricReadout.tsx
                    SectionHeader.tsx
                    StatusBadge.tsx
            lib/
                config.ts
                store.tsx
                api/
                    wsClient.ts
                simulation/
                    engine.ts
            types/
                sage.ts
    docs/
        ml_model_contract.md
    ml_models/
        binary_lightgbm/
            binary_feature_columns.pkl
            binary_lightgbm.pkl
            README.md
        multiclass_random_forest/
            ddos_feature_columns.pkl
            ddos_multiclass_random_forest.pkl
            label_mapping.pkl
            README.md
    scripts/
        inspect_models.py
```

---

## 2. Per Top-Level Folder

### `dashboard/`
Status: **COMPLETE**
*   `AGENTS.md`, `CLAUDE.md`, `README.md`: Documentation for the dashboard frontend.
*   `package.json`, `tsconfig.json`, `next.config.ts`, `eslint.config.mjs`, `postcss.config.mjs`: Configuration files for the Next.js React application.
*   `next-env.d.ts`: TypeScript declarations for Next.js.
*   `public/`: Static SVG assets (`file.svg`, `globe.svg`, `next.svg`, `vercel.svg`, `window.svg`).
*   `src/app/`: Next.js App Router pages for various dashboard views (`attack-lab`, `detection`, `incidents`, `live-traffic`, `logs`, `mitigation`, `settings`).
*   `src/components/`: Reusable UI components (`CustomCursor.tsx`, `NavigationRail.tsx`, `TrafficGraph.tsx`, `ui/` elements).
*   `src/lib/`: Application logic, including `store.tsx` (state), `config.ts`, `api/wsClient.ts` (WebSocket client), and `simulation/engine.ts`.
*   `src/types/`: TypeScript type definitions (`sage.ts`).

### `docs/`
Status: **COMPLETE**
*   `ml_model_contract.md`: Markdown document detailing ML model specifications, required features, and artifacts paths.

### `ml_models/`
Status: **COMPLETE**
*   `binary_lightgbm/binary_lightgbm.pkl`: The compiled LightGBM model for binary DDoS classification.
*   `binary_lightgbm/binary_feature_columns.pkl`: The exact feature columns required for the binary model.
*   `binary_lightgbm/README.md`: Readme for the binary model.
*   `multiclass_random_forest/ddos_multiclass_random_forest.pkl`: The compiled Random Forest model for multiclass DDoS type classification.
*   `multiclass_random_forest/ddos_feature_columns.pkl`: The exact feature columns required for the multiclass model.
*   `multiclass_random_forest/label_mapping.pkl`: Python dictionary mapping predicted index to attack class name.
*   `multiclass_random_forest/README.md`: Readme for the multiclass model.

### `scripts/`
Status: **COMPLETE**
*   `inspect_models.py`: A Python script to verify, load, and inspect the shapes and details of the ML `.pkl` models.

### `api/`, `db/`, `detection/`, `decision/`, `mitigation/`, `docker/`, `k8s/`
Status: **NOT FOUND**

---

## 3. Feature Extraction

*   **`feature_extractor.py`**: **NOT FOUND**. Explicitly absent from the repository. No feature extraction logic currently exists on disk.
*   **Traffic monitoring/flow generation code (raw packets → flow records / PCAP handling)**: **NOT FOUND**.
*   **`simulator.py` (DDoS traffic simulator)**: **NOT FOUND**. 

---

## 4. ML Artifacts

The current location of the required ML artifacts are as follows:

*   `binary_lightgbm.pkl`: Found at `ml_models/binary_lightgbm/binary_lightgbm.pkl`
*   `binary_feature_columns.pkl`: Found at `ml_models/binary_lightgbm/binary_feature_columns.pkl`
*   `ddos_multiclass_random_forest.pkl`: Found at `ml_models/multiclass_random_forest/ddos_multiclass_random_forest.pkl`
*   `ddos_feature_columns.pkl`: Found at `ml_models/multiclass_random_forest/ddos_feature_columns.pkl`
*   `label_mapping.pkl`: Found at `ml_models/multiclass_random_forest/label_mapping.pkl`

---

## 5. Dependency Manifests

### `dashboard/package.json`

```json
{
  "name": "sage",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint"
  },
  "dependencies": {
    "@gsap/react": "^2.1.2",
    "clsx": "^2.1.1",
    "date-fns": "^4.4.0",
    "gsap": "^3.15.0",
    "lucide-react": "^1.33.0",
    "next": "16.3.1",
    "react": "19.2.8",
    "react-dom": "19.2.8",
    "recharts": "^3.10.1",
    "tailwind-merge": "^3.6.0"
  },
  "devDependencies": {
    "@tailwindcss/postcss": "^4",
    "@types/node": "^20",
    "@types/react": "^19",
    "@types/react-dom": "^19",
    "eslint": "^9",
    "eslint-config-next": "16.3.1",
    "tailwindcss": "^4",
    "typescript": "^5"
  },
  "packageManager": "pnpm@10.32.1"
}
```
**Flag:** Almost all dependencies in `package.json` (except `next`, `react`, `react-dom`, and `eslint-config-next`) are listed without a strictly pinned version, using the `^` carat prefix (e.g., `^2.1.2`). 

**Python Manifests (`requirements.txt`, `pyproject.toml`, `Pipfile`)**: **NOT FOUND**.

---

## 6. Docker

**`Dockerfile`, `docker-compose.yml`, `.dockerignore`**: **NOT FOUND**. 
No Docker configuration currently exists in the repository.

---

## 7. ENV Config

**`.env` / `.env.example`**: **NOT FOUND**.
There are no `.env` files present anywhere in the repository. The application `wsClient.ts` references `NEXT_PUBLIC_WS_URL` and `NEXT_PUBLIC_API_BASE_URL`, but these variables are not defined in any checked-in environment files.

---

## 8. Dashboard State

*   **`dashboard/` presence**: Confirmed. It exists at the monorepo root.
*   **WebSocket implementation**: `dashboard/src/lib/api/wsClient.ts` exists. It exports the custom hook `useLiveConnection`, which handles REST hydration and WebSocket lifecycle updates.
*   **Build Status**: **PASS**.
    The application successfully compiles with `pnpm run build` (triggering `next build`). 

**Build Output:**
```text
$ next build
▲ Next.js 16.3.1 (Turbopack)
✓ Running next.config.ts took 175ms

  Creating an optimized production build ...
✓ Compiled successfully in 12.3s
  Running TypeScript ...
  Finished TypeScript in 5.7s ...
  Collecting page data using 13 workers ...
  Generating static pages using 13 workers (0/11) ...
  Generating static pages using 13 workers (2/11) 
  Generating static pages using 13 workers (5/11) 
  Generating static pages using 13 workers (8/11) 
✓ Generating static pages using 13 workers (11/11) in 2.2s
  Finalizing page optimization ...

Route (app)
┌ ○ /
├ ○ /_not-found
├ ○ /attack-lab
├ ○ /detection
├ ○ /incidents
├ ƒ /incidents/[id]
├ ○ /live-traffic
├ ○ /logs
├ ○ /mitigation
└ ○ /settings


○  (Static)   prerendered as static content
ƒ  (Dynamic)  server-rendered on demand
```

---

## 9. Backend State

**`api/`, `db/`, `decision/`, `mitigation/` Phase 1 scaffold**: **NOT FOUND**.
These folders are completely missing from the monorepo root. No Phase 1 backend code (FastAPI app, `/health` endpoint, etc.) has been scaffolded or committed yet.

---

## 10. Tests

**Test files**: **NOT FOUND**. 
No test suites, `__tests__` directories, or `*.test.ts` / `test_*.py` files exist in the current project structure.
