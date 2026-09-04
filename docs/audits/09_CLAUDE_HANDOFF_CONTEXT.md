# 09: CLAUDE HANDOFF CONTEXT

Dear Future Claude Agent, 
You are receiving this project to finalize the backend expansion. This repository contains a deterministic personalization engine for weather (Mausam). IT DOES NOT CONTAIN MACHINE LEARNING. 

**FILES TO PROVIDE TO THE NEXT CLAUDE AGENT**

### TIER 1 — MUST PROVIDE
*These files are the absolute core of the backend architecture.*
1. `docs/audits/*` (You are reading this now. Essential to understand the state of the project.)
2. `engine/engine.py` 
   - *Why:* It's the central ranking entry point. Shows how deterministic decisions are assembled.
3. `engine/scoring.py` 
   - *Why:* Contains the hardcoded math for personalization weighting.
4. `engine/cards.py` 
   - *Why:* Defines the physical cards and the personas capable of seeing them.
5. `engine/models.py` 
   - *Why:* The contract types. Exposes `ContextFrame` which is exactly how data flows into the engine.

### TIER 2 — STRONGLY RECOMMENDED
*Important implementation details for routing and external data.*
1. `backend/deps.py`
   - *Why:* Shows how the `ContextFrame` is constructed using dummy adapters.
2. `backend/routers/homepage.py`
   - *Why:* Demonstrates the main FastAPI endpoint and how it resolves device preferences.
3. `adapters/base.py` & `adapters/aqi_adapter.py`
   - *Why:* Confirms that adapters are currently returning JSON fixtures. Shows exactly where to place live HTTP requests (like OpenWeather/IMD API).
4. `backend/db.py`
   - *Why:* Explains how Neon Postgres is configured.

### TIER 3 — ONLY IF NEEDED
*Peripheral or secondary.*
1. `engine/tests/*` 
   - *Why:* If you change logic, review tests to ensure you don't break expected P0 overrides.

## "READ THIS FIRST" ORDER
1. `docs/audits/00_EXECUTIVE_PROJECT_OVERVIEW.md`
2. `docs/audits/03_ENGINE_AND_PERSONALIZATION_AUDIT.md`
3. `engine/scoring.py`
4. `engine/engine.py`

## Final Instructions for the Next Agent:
1. Do not recommend a rewrite. The deterministic engine is excellent.
2. Wait for explicit approval before changing `engine/`. Your primary goal should be implementing the missing 5 personas, moving from `device_id` to Firebase Auth, and hooking up live IMD/OpenWeather adapters in `adapters/`. Only pursue ML when data logging is fully established over hundreds of sessions.
