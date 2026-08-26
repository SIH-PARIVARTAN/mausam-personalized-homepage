# Project Roadmap

This roadmap reflects the actual repository state.

## 🟩 COMPLETED: Foundation & Backend MVP

**Objective:** Build a robust, scalable backend that handles personalization mathematically.
- **Architecture Baseline:** Project structure, comprehensive markdown planning specs.
- **Personalization Engine:** Pure python scoring models, urgency mapping, conflict resolution, explainability templates. (130+ passing tests).
- **PostgreSQL Foundation:** Neon DB integration via psycopg3 for preference and cache storage.
- **Data Adapters (Phase 1):** Configured standardized interfaces for Forecasts, Warnings, AQI, UV, and Sunlight. Implemented robust simulated fixtures mirroring real-world IMD structures.
- **Backend APIs:** `/homepage`, `/preferences`, `/explain` endpoints running on FastAPI.

## 🟨 NEXT MILESTONE (CURRENT): Frontend UI Integration

**Objective:** Build a responsive, presentation-only Next.js client that consumes the FastAPI endpoints and proves the personalization logic visually.
- **S2 Personalized Homepage:** React components to render the `cards[]` array exactly as sorted by the backend.
- **S4 Preferences Modal:** UI to select between the 3 MVP personas and toggle health flags. Instantly triggers a homepage re-render.
- **S3 Explanation Sheet:** Tap interaction to reveal technical explanations based on backend refs.
- **Warning & Degradation UI:** Distinct visual treatments for P0 Severe Warnings and honest badging for "stale" or "simulated" data.
- **Demo Rehearsal:** Execute the end-to-end "change persona -> see cards reorder" flow.

## ⬜ FUTURE.1: Persona Expansion

**Objective:** Achieve 100% compliance with SIH26076's recommended 8 personas.
- **Pollen Data Adapter:** Source a reliable Indian pollen index API to finalize the Health persona.
- **Comfort Index:** Mathematical formula combining temp/humidity to support Event Planners.
- **Marine Adapter:** INCOIS integration (or fixtures) for Beachgoers/Surfers.
- **Traveler Logic:** Expand `/preferences` schema to support multi-destination routing.

## ⬜ FUTURE.2: Production & Live Data

**Objective:** Transition from Hackathon MVP to a live, scalable production environment.
- **IMD API Whitelisting:** Replace `ForecastAdapter` and `WarningAdapter` fixtures with live HTTPS polling.
- **AQI / UV Hardening:** Activate live HTTP endpoints with 5s timeout, 1-retry fallback limits to prevent thread hangups.
- **Deployment:** Render (Backend API), Vercel (Next.js Frontend).
- **Traffic API Exploratory:** Assess non-MoES API dependencies to satisfy commuter traffic requirements without violating project scope.
