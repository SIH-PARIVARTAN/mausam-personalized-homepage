# 08: FINAL BACKEND COMPLETION ROADMAP

## Phase 1: Security & Identity (MUST DO FIRST)
*Do not expand personas or add live data until the app is secure.*
- **Step 1:** Add Firebase Admin SDK to `backend/deps.py`.
- **Step 2:** Refactor `GET /homepage` to require a `Bearer <Firebase ID Token>`.
- **Step 3:** Change `device_id` primary key in Neon DB to `firebase_uid`.

## Phase 2: Complete the 8 Personas
*Extend the deterministic engine before pursuing ML.*
- **Step 1:** Modify `backend/routers/preferences.py` schemas to accept `agriculture`, `commuter`, `travel`, `event_planner`, `beachgoer`.
- **Step 2:** Update `engine/cards.py` to register new cards (e.g. `soil_moisture`, `traffic_commute`).
- **Step 3:** Add logic to `engine/scoring.py` specifically targeting new personas (e.g., if agriculture and temp drops, alert frost).

## Phase 3: Connect Live IMD / OpenWeather Adapters
*The adapter architecture is already perfect for this.*
- **Step 1:** Inject secret keys into `.env`.
- **Step 2:** Modify `adapters/aqi_adapter.py` and `forecast_adapter.py` to hit actual endpoints if `ADAPTER_MODE=live`.
- **Step 3:** Cache responses in PostgreSQL `signal_cache` to stay under API rate limits.

## Phase 4: Foundational ML Logging
*Prepare for the future context-aware ML model.*
- **Step 1:** Build an analytics endpoint `POST /api/telemetry/interaction`.
- **Step 2:** Save telemetry events (impressions vs. clicks) anonymously in Neon Postgres. 

## What should NOT be rewritten?
- **DO NOT** rewrite `engine/engine.py`. Its pure functional design (input: `ContextFrame`, output: `EngineOutput`) makes testing flawless. 
- **DO NOT** rewrite conflict resolution.
- **DO NOT** attempt to make the engine an AI LLM prompt. Deterministic rules are much safer for severe weather warnings.
