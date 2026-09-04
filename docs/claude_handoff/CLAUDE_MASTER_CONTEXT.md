# CLAUDE MASTER CONTEXT

## 1. Project Background
**Project:** Mausam Personalized Homepage (SIH 2026, Problem Statement 26076)
**Problem:** Standard weather apps are generic. Users (Parents, Athletes, Agriculture) need highly contextual insights.
**Core Principle:** This codebase implements a deterministic, rule-based personalization engine. It is NOT a machine learning project yet.

## 2. Full System Architecture (Current State)
The system is divided into clear boundaries ensuring the engine never touches I/O.
- **Frontend:** Next.js (Retrieves data, handles UI).
- **Backend:** FastAPI (`backend/`). Exposes `/homepage` and `/preferences`.
- **Adapters:** Standardized fetchers (`adapters/`). Currently 100% mocked via JSON fixtures.
- **Database:** Neon PostgreSQL. Stores `device_id`, `personas` (JSON array of strings), `health_flags`, and a `signal_cache`.
- **Engine:** Pure functions (`engine/`). Takes a `ContextFrame`, applies hardcoded scoring logic, and returns a prioritized list of cards.

**Request Flow:**
`GET /homepage` -> `deps.py` fetches DB preferences & fires Adapters -> Assembles `ContextFrame` -> `engine.rank()` -> Resolves P0 overrides, scores cards, runs tie-breakers, generates explanations -> Returns `EngineOutput`.

## 3. Engine and Personalization (The Single Source of Truth)
The Engine (`engine/engine.py` & `engine/scoring.py`) is beautifully architected. 
- **Determinism:** `Score = Persona Weight × Urgency Multiplier × Confidence Factor`.
- **Persona Weights:** Hardcoded in `PERSONA_WEIGHT` dict.
- **Urgency Multiplier:** Purely environmental logic (e.g. `If AQI > 150, Urgency = 2.5`). It *never* reads the user's persona, preventing hardcoded persona shortcuts.
- **P0 Overrides:** Alerts like `severe_warning` bypass scoring entirely and are forcibly pinned to the top.

## 4. Persona Implementation Status
The SIH project targets **8 personas**. The repository currently implements **3**:
- Health (Done)
- Fitness (Done)
- Family (Done)
- Default General (Fallback - Done)
- *Agriculture, Commuter, Traveler, Beachgoer, Event Planner* = **MISSING**.

## 5. Adapters and Data (Important)
- **Current State:** 0% Live Data. All adapters (`aqi_adapter.py`, `forecast_adapter.py`) read from `adapters/fixtures/*.json` when `ADAPTER_MODE=fixture`.
- The live HTTP scaffold exists but simply catches exceptions and returns degraded data.
- **Implication:** Extending to OpenWeather / IMD APIs requires modifying the `fetch()` method in the adapters.

## 6. API and Contracts
- `/homepage` accepts `device_id`, `lat`, `lon`. **CRITICAL GAP:** There is NO real authentication (e.g., Firebase Token verification) happening in the backend. 
- `/preferences` reads/writes string arrays directly to Postgres without auth.

## 7. What MUST Be Preserved
- The pure functionality of `engine.rank()`. Do not add database calls or API requests into the `engine/` directory.
- The P0 priority override system.
- The fallback logic where degraded/unavailable data gracefully drops a card's score rather than crashing the system.
