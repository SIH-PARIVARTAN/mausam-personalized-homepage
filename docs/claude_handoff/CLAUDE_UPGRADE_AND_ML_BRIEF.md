# CLAUDE UPGRADE AND ML BRIEF

## 1. Verified Current Facts
- The backend is a standard FastAPI + Neon Postgres stack.
- The personalization engine is 100% deterministic, rule-based, and heavily tested (137 passing tests).
- There is ZERO Machine Learning code in the repository.
- There is ZERO live data fetching currently working (all mock fixtures).
- Only 3 out of 8 personas exist.
- Authentication is completely missing on the backend.

## 2. The Missing Functionality (Backend Completion Roadmap)
Before attempting ML, the backend *must* be completed:
1. **Security:** Implement Firebase Auth verification in FastAPI dependency injection to replace raw `device_id` lookups.
2. **Missing Personas:** Add the 5 remaining personas (`agriculture`, `commuter`, `traveler`, `beachgoer`, `event_planner`). Update the UI schemas, the `PERSONA_WEIGHT` dict, and `cards.py` to support new cards corresponding to these personas.
3. **Live Data:** Inject real API keys and replace the fixture-loading in `adapters/` with actual `httpx` calls to OpenWeather or IMD. Implement safe caching using the existing `signal_cache` PostgreSQL table.

## 3. ML and AI Readiness Audit
**Is ML Justified?** Right now, NO. The deterministic engine handles the hackathon MVP flawlessly and is much safer for Severe Weather warnings. 

**Is the codebase ready for ML?** NO. There is no historical dataset. You cannot train an ML personalization system without user interaction data (impressions, clicks, time spent). 

## 4. Proposed Future ML Evolution
If you want to evolve this to a hybrid ML platform:
- **Step 1: Collect Data.** Build `POST /api/telemetry` to log `ContextFrame` snapshots + user actions (clicked cards, dismissed cards).
- **Step 2: Generate Offline Dataset.** Wait until thousands of telemetry rows are stored in a Warehouse.
- **Step 3: Train an XGBoost/LightGBM model.** Train the model to predict the Probability of Click for a specific `(Card, Persona, Environment_State)`.
- **Step 4: Hybrid Inference Service.** The deterministic engine keeps P0 Overrides (Severe Warnings), but the ML model dynamically replaces the `persona_weight` table inside `engine/scoring.py` with real-time predictions. 

*Until Step 1 and Step 2 happen, do not attempt to write ML model training code in this repository.*
