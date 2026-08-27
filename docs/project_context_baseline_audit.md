# Project Context & Baseline Understanding Audit

**Date:** 2026-08-27
**Target Project:** Mausam Personalized Homepage (SIH26076)

## 1. Executive Project Understanding
- **The True Objective:** Building a contextual relevance and personalization layer for the existing Mausam mobile application, NOT replacing the weather app with a full-featured alternative.
- **What We Are Building:** An intelligent engine that ranks weather cards based on user personas and environmental signals (AQI, UV, Rain, Warnings, Sun), applying math (score = weight × urgency × confidence) to generate an explainable, personalized homepage layout.
- **What We Are Explicitly NOT Building:** We are not building ML black-box personalization. We are not building generic dashboard features without context logic. We are not blindly adding all personas without underlying data adapters.

## 2. Current Implementation Map
- **Engine (`engine/`):** **Frozen and Stable**. Contains 8 card definitions, scoring logic (weight × urgency × confidence), alert classification, and explanation templating.
- **Backend (`backend/`):** FastAPI app with 3 primary endpoints (`/homepage`, `/explain`, `/preferences`). Implements ContextFrame assembly dynamically from adapter sources. Uses a PostgreSQL database (Neon-compatible) for preference persistence and cache.
- **Adapters (`adapters/`):** Standardized interface (`fetch()`) currently largely relying on JSON local fixtures (`ForecastAdapter`, `WarningAdapter`, `AQIAdapter`, `UVAdapter`), barring `SunAdapter` which runs live computation (`astral`). Live AQI and UV scaffolds exist but run fixture data gracefully right now.
- **Database/Cache (`cache/`, `backend/db.py`):** PostgreSQL for user preferences (`personas`, `health_flags`) and cache, preventing DB failure when scaling/restarting.
- **Frontend (`frontend/`):** Just an empty Next.js 16 App Router scaffold without UI implementation.
- **Documentation (`docs/`):** Contains historical planning docs (which are un-remediated but contextually useful) and authoritative final state docs (such as `project_status.md`, `frontend_handoff.md`, `IMPL_CALIBRATION_DECISIONS.md`).

## 3. Exact Architecture and Data Flow
The data flow is deterministic and centralized within the backend components:
1. **Request:** Frontend issues `GET /homepage?device_id=X&lat=Y&lon=Z`.
2. **Preference Resolution:** Backend queries Postgres for the user's `personas` and `health_flags`. Defaults to bare minimum settings for cold-starters.
3. **Data Fetching:** Backend leverages `build_context_frame()` which calls all `Adapters` for data (forecast, warnings, sun, etc.). The adapters provide normalized payloads or safe unavailable flags.
4. **Engine Scoring:** The frozen pure function `rank(ContextFrame)` computes the score for each candidate card (Score = persona_weight × urgency_multiplier × confidence_factor).
5. **Alert Mapping:** Any active severity warnings bypass scoring as P0 hard overrides (`warnings_override`). P3 alerts are automatically elevated to P2.
6. **Response Formulation:** Results are validated as Pydantic models (ranked `cards[]` and `warnings_override[]`). Explanation strings and metadata mapped and cached in memory.
7. **Frontend Consumption:** The UI blindly renders the list, top to bottom without altering or resorting the order.

## 4. Current API Contract Summary
Extracted directly from `backend/routers/homepage.py` & `models_api.py`:
- **`GET /homepage`**: requires `device_id` (str), `lat` (float, -90 to 90), `lon` (float, -180 to 180). Returns `HomepageResponse` (snapshot ID, generation time, sorted `cards`, `warnings_override`, optional `system_notice`).
- **`GET /preferences`**: requires `device_id`. Returns user string array payloads (`personas`, `health_flags`, `saved_locations`).
- **`PUT /preferences`**: accepts `PreferencesBody` (`device_id` string, `personas` list, `health_flags` list, `saved_locations` list). Returns `{"status": "ok"}`.
- **`GET /explain`**: requires `explanation_ref`. Returns `ExplainResponse` (text, `signal_refs`, `score_components`).
- **`GET /health`**: health-check endpoint.

## 5. Persona Inventory
- **Currently Implemented (Deeply Supported):**
  - Health-conscious (`health`): tied to AQI, UV, Pollen (simulated), etc.
  - Outdoor fitness enthusiasts (`fitness`): tied to Activity Window, Sunrise/Sunset, Wind.
  - Parents & families (`family`): tied to Rain Commute, Severe warnings.
  - Cold-start Default (`default_general`): fallback handling.
- **Partially Represented (Implemented as gated UI definitions but data null/stubbed):**
  - Pollen sensitivity (under health, via `pollen_interest` flag/`pollen_illustrative` card).
- **Deferred / Unimplemented:**
  - Beachgoers / Surfers (requires marine API).
  - Travelers (multi-destination routing not in scope).
  - Agriculture / Gardeners (agromet APIs inaccessible).
  - Commuters (traffic API out of scope).
  - Event Planners (comfort index deferred).

## 6. Data-Source Matrix
| Signal | Consuming Feature/Persona | Adapter / Source | Current Status |
|--------|---------------------------|------------------|----------------|
| Temperature/Humidity/Wind/Precip | Fitness, Family, Default | `ForecastAdapter` | Fixture (`forecast_adapter.py`) |
| Severe Warnings | All Personas (P0 override) | `WarningAdapter` | Fixture (`warning_adapter.py`) |
| AQI (Air Quality) | Health, Fitness | `AQIAdapter` | Fixture (Live Scaffold present) |
| UV Index | Health, Fitness | `UVAdapter` | Fixture (Live Scaffold present) |
| Sunrise / Sunset (Daylight) | Fitness, General | `SunAdapter` | **Live** (via `astral` lib locally calc'd) |
| Pollen Level | Health (Pollen Interest) | (None) | Scaffolded as missing/unavailable |

## 7. What is Stable/Frozen
- **The Personalization Engine (`engine/`)**: This block is frozen. It is a dependency-free pure function. No API calls or database logic exist here. Modifying this breaks the test suite of 134 units.
- **Backend Architecture Principles**: FastAPI architecture, dependency injections (`ContextFrame` assembly), and Pydantic models. Adapters enforce standardized interfaces masking whether data is live or simulated.

## 8. What is Incomplete
- **Frontend Layer**: The `frontend/` directory is essentially an empty scaffold for Next.js. The UI layer needs to be implemented to consume the `/homepage`, `/explain`, and `/preferences` logic accurately.
- **Live APIs**: AQI and UV rely entirely on fixtures. Timeouts and live fallbacks are unimplemented.
- **Coverage Extrapolations**: Pollen adapter absent. Deferred personas are completely unbuilt on the backend/adapter side.
- **Frontend / Backend E2E Contract Test**: No automated end-to-end user-flow validation driving Next.js rendering against FastAPI responses.

## 9. Documentation Authority Map
- **Current Authoritative Docs**: `project_status.md`, `frontend_handoff.md`, `IMPL_CALIBRATION_DECISIONS.md`, `frontend_product_spec.md`, `ui_screen_specification.md`, `technical_architecture.md`.
- **Historical Decisions (Preserved but do not treat as raw truth)**: Files housed in `docs/planning/` (e.g., `03_personalization_logic_and_decision_matrix.md`).
- **Contradiction Resolutions**: Outlined entirely matching `IMPL_CALIBRATION_DECISIONS.md` correcting old calculations where (e.g., family + rain required an elevated coefficient score factor which older files lacked).

## 10. Risks and Constraints
- **Fake UI AI Claims Risk**: The project clearly enforces an explainable UI. The frontend must not claim ML/AI when rendering explanation cards.
- **Sorting Contradiction Risk**: If the frontend attempts to do client-side ranking, it overrides the engine output, invalidating the personalization audit trail.
- **Fixture vs Live Transparency Risks**: We must ensure "simulated" tags are aggressively presented anywhere live data hasn't yet been securely introduced.

## 11. Understanding of the Next Decision Point
The upcoming issue concerns a frontend integration dilemma. A teammate has apparently created a frontend UI in a separate repository utilizing a different architecture stack. The objective will be conducting a rigorous architectural reconciliation, figuring out how to safely import the visual UI layouts/assets into this primary Next.js+FastAPI stack, while strictly preserving backend rendering priorities and ignoring their architectural/logic differences that conflict with our authoritative personalization engine boundaries.
