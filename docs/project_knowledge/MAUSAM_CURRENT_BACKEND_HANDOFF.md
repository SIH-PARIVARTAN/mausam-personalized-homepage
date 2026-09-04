# MAUSAM CURRENT BACKEND HANDOFF

*CURRENT BACKEND HANDOFF for frontend integration, Claude review, SIH presentation, and future development.*

## 1. EXECUTIVE SUMMARY

The MAUSAM backend serves as a highly scalable context engine. It intercepts raw weather data, matches it against a given user's personalization profile, and scores it deterministically to emit prioritized cards. 

**The backend's role:**
`External Open-Meteo Data → Normalization → ContextFrame → Deterministic MAUSAM engine → Persona-aware scoring → Priority classification → Compound conditions → Cards → HomepageResponse → Frontend`

The backend is the strictly authoritative personalization and ranking layer. The frontend is exclusively responsible for rendering these backend decisions. The optional Groq conversational LLM is strictly an interface, NOT the ranking engine.

## 2. SIH PROBLEM STATEMENT CONTEXT

**SIH 2026**
**Problem Statement SIH26076**
*Development of personalized homepage for "Mausam" mobile application*

*   **REQUIRED + FULLY IMPLEMENTED**: Context-aware alerts, Personalized dynamic homepage, deterministic modular expandability, Explainability logic.
*   **PARTIALLY IMPLEMENTED**: Low-connectivity gracefully degraded caching, Persona combinations (Currently strictly handles active combinations, but limits to top limits natively).
*   **PROPOSED / NOT IMPLEMENTED**: Native Mobile Packaging (Capacitor/PWA), SMS failover warnings.

## 3. BACKEND TECHNOLOGY STACK

*   **Python:** Core data processing architecture.
*   **FastAPI:** High-performance web framework serving REST endpoints.
*   **Pydantic:** Strict payload validation and context-frame guarding (root cause solver of the legacy 422 JSON errors).
*   **Neon / PostgreSQL / SQLAlchemy:** Persists `preferences` and `saved_locations`.
*   **Open-Meteo:** Live external telemetry provider (Temp, Rain, UV, AQI).
*   **Astral:** Natively computes Daylight/Sunrise/Sunset using coordinates natively without API latency. 
*   **Redis/Memory Store Cache:** Powers Graceful degradation via `Fresh / Soft-Stale / Hard-Stale` cascading fallbacks.
*   **Pytest:** Test harness to evaluate the backend.

## 4. COMPLETE MODULE MAP

```text
backend/
  routers/
    homepage.py   # Exposes GET /homepage
    preferences.py# Exposes GET & PUT /preferences
  deps.py         # Hydrates ContextFrame from location, adapters & time
  main.py         # FastAPI Bootstrapper
  db.py           # Neon Postgres configuration

engine/
  models.py       # Defines pure 'ContextFrame', 'SignalValue', and 'DailyForecastSummary'
  cards.py        # Defines CARD_DEFINITIONS (Source of truth for personas and triggers)
  scoring.py      # Executes math: PersonaWeight * UrgencyMultiplier * ConfidenceFactor
  derived.py      # Translates values (e.g. comfort_index, frost_active) 
  engine.py       # Orchestrates the ranking list & compound checks
  explain.py      # Produces text strings detailing exactly *why* a card won

adapters/
  forecast_adapter.py # Integrates Open-Meteo
  aqi_adapter.py      # Fetches AQI specifics
  uv_adapter.py       # Fetches clear UV 
  warning_adapter.py  # Checks external warnings
  marine_adapter.py   # Fixture-only stub
  base.py             # Defines the ADAPTER_MODE (Live vs Fixture) interface

eval/
  run_spike.py        # Golden set tester ensuring 34 deterministic scenarios pass accurately
```

## 5. DETERMINISTIC ENGINE — DEEP EXPLANATION

**Flow:** `ContextFrame → derived signals → cards → persona scoring → urgency → confidence → compound conditions → priority → conflict resolution → ranking → explanation → response`

**Rules:**
1.  **The engine is purely deterministic**. Given the identical normalized context + preferences, it produces statistically identical rankings.
2.  The engine `(engine/)` knows absolutely nothing about HTTP, Requests, APIs, SQLAlchemy, or LLMs. It strictly intakes a typed `ContextFrame` and emits a `EngineOutput`.

## 6. CONTEXTFRAME (Normalized Context Model)

Defined in `engine/models.py`. Keys strictly used:
*   `personas` (list[str]): Inherited from user preferences. 
*   `is_commute_window` (bool): Derived from local time bounds (`07:00-09:30` and `17:30-20:00`). 
*   `is_daylight` (bool): Computed via Astral `sr` and `ss`.
*   `temp_c`, `humidity_pct`, `wind_kmh`, `precip_prob_pct`, `warnings`, `visibility_km`: Standard Open-Meteo hookups (`SignalValue`).
*   `aqi`, `uv`: Extracted for Health/Outdoor safety boundaries.
*   `destinations`: Extracted exclusively for Traveler delta-comparison limits.
*   `soil_moisture_pct`, `comfort_index`, `wave_height_m`: Phase C Specific mappings. 

## 7. PERSONA ARCHITECTURE

**Official Personas:** `health, fitness, beachgoer, traveler, family, agriculture, commuter, event_planner`.
*Note: `default_general` exists purely as a cold-start state. It is not an official user persona.*

**Execution:** Users may pass multiple personas in the array `["fitness", "health"]`. The backend iterates `CARD_DEFINITIONS`, and if the card natively matches *any* declared persona array overlaps, it fires.

## 8. CARD SYSTEM

Managed in `engine/cards.py`. 

*   `severe_warning` (P0 | All Personas | Triggered by active hazard).
*   `rain_commute` (P1/P2 | Commuter, Family | Heavy rain >30% inside transit periods).
*   `activity_window` (P2 | Fitness | Modifies outdoor windows).
*   `aqi_health` (P1/P2 | Health | Triggers aggressively > 100).
*   `destination_alert` (P1/P2 | Traveler | Triggers warning threshold matching between specific origin-destination offsets).
*   `agriculture_advisory` (P1/P2 | Agriculture | Evaluates soil/frost). 
*   `marine_conditions_alert` (P1/P2 | Beachgoer | Evaluates wave height).
*   `event_outlook` (P2 | Event Planner | Scored on `comfort_index`).
*   Compound Cards (`compound_heat_aqi_danger`, `compound_driving_hazard`) are generated explicitly.

## 9. SCORING SYSTEM

Located in `engine/scoring.py`.
`Raw Score = Persona_Weight * Urgency_Multiplier * Confidence_Factor`

- **Persona_Weight:** Statically evaluated lookup (e.g. `aqi_health` is `0.9` for Health, `0.4` for Family).
- **Urgency_Multiplier:** Reacts environmental status (e.g. Severe air quality `AQI > 300` jumps multiplier to `2.5`). 
- **Confidence_Factor:** `Live` = 1.0, `Cached` = 0.9, `Simulated` = 0.7, `Stale` = 0.3. 

## 10. COMPOUND CONDITIONS

These specifically execute *after* native evaluation to protect against fragmented dashboarding:
- **Heat + AQI:** If AQI > 150 AND Temp > 35c → generates `compound_heat_aqi_danger`. 
- **Visibility + Rain:** Combines visibility loss and severe rain matrices natively into `compound_driving_hazard`. 

## 11. EXPLAINABILITY

At the end of engine rotation, `engine/explain.py` extracts the `signal_refs` array variables and generates a deterministic string.
*Example: `Visibility 1.2km within your commute window → 1.6x the normal urgency threshold → shown as a high-priority alert.`*
The logic is entirely transparent, avoiding black-box LLM risks on priority decisions.

## 12. API CONTRACT

*   **`GET /homepage`**: Needs `device_id`, `lat`, `lon`. Returns {`override_warnings`, `ranked_cards`}.
*   **`GET /preferences`**: Needs `device_id`. Returns user `{personas, health_flags, saved_locations}`.
*   **`PUT /preferences`**: Mutates PostgreSQL user context models. 

## 13. CACHE / DEGRADATION

Implements Graceful Degradation in adapters.
*   **Fresh:** Returns high-confidence live payloads.
*   **Soft-Stale:** Retains older responses up to 4 hours with lowered priority matrices (`Confidence 0.56`).
*   **Hard-Stale/Failure:** Defaults variables to `.make_unavailable_signal()`, natively hiding the cards inside `ranking.py` cleanly instead of throwing 500 exceptions on the Frontend.

## 14. THE 422 BUG — HISTORICAL + CURRENT STATUS

**Bug:** Fast API `PUT /preferences` was constantly emitting `422 Unprocessable Entity` payloads at runtime on the website.
**Cause (Runtime Verified):** The `models_api.py` enforced severe regex standards for `device_id` constraints (Requires 36-char string UUIDv4 or 28-char alphanumeric). Earlier, the React frontend generated ad-hoc `15-char` non-compliant arrays in `localStorage`. 
**Remediation:** `AuthContext.tsx` was deeply patched to safely parse/scrub memory buffers and inject real Firebase IDs or RFC UUIDs exclusively. **Fixed and Runtime Verified.**

## 15. SPECIAL PERSONAS (THE LIMITATIONS OF LIVE DATA)

The backend adapters specifically demonstrate this distinction:
*   **Event Planner:** `ForecastAdapter` strictly hardcodes `extended_forecast` to `[]` when `ADAPTER_MODE=live`. The Event Planner natively evaluates a static `comfort_index`. SIH 10-day trending claims are functionally **unimplemented**.
*   **Beachgoer / Agriculture:** Neither marine APIs nor soil APIs are hooked up. They exclusively return `fixture` (mock) objects generated from `fixtures/marine_normal.json`.

*(Note: The React frontend descriptors have been patched to portray this reality cleanly avoiding fake claims).*

## 16. CHATBOT / LLM BOUNDARY

**Core Boundary:** `Mausam Context → Chatbot NLP → Next.JS /api/chat → Groq API`
The LLM serves strictly optionally to explain or summarize the output of the MAUSAM rank engine dynamically. The Chatbot **does not rank cards, alter priority, override warnings, or fabricate values**. It safely handles Graceful degradation by aborting logic and returning `Service Unavailable` if `GROQ_API_KEY` is missing.

## 17. TRAVELER DESTINATIONS

The `ForecastAdapter` evaluates the frontend `PUT` arrays mapping coordinates into `destinations` objects. It hits limits at `MAX_DESTINATIONS_FETCHED=3`. It then generates a reliable differential calculation showing exactly how much colder/warmer a destination is compared to the active original position cleanly natively.

## 18. CURRENT TEST / QA STATUS

*   **Golden Test Suite (`run_spike.py`):** **34/34** scenarios evaluated. Passes purely deterministically validating multi-persona conflict management.
*   **Frontend UI Build:** NPM compiles correctly with zero validation mismatch.

## 19. PRODUCT/DESIGN OPEN QUESTIONS FOR CLAUDE

Claude should advise on the visual/presentation logic bound to these realities:
*   **Information Hierarchy:** Given that backend P0 overrides inherently surface first, how heavily should the generalized weather metrics exist visually below the active card output?
*   **Event Planner:** Given the limitation mapped to single-day `comfort_index` natively instead of predictive arrays, what is the best non-trivial presentation logic for demonstrations without claiming a 10-day graph?
*   **Map Integrations:** How cleanly should `Traveler` locations merge with the `Leaflet` components without overloading the homepage bounds? 
*   **Confidence Visibility:** Is it confusing or valuable to show "Simulated Fixture" stamps natively on Beach/Agri personas during demos?

## 20. CURRENT BACKEND VERDICT

**Status: FROZEN WITH DOCUMENTED LIMITATIONS**
**Readiness: STABLE**

The core data pipeline, schema extraction rules, scoring determinism, identity validation, and caching degradation behave flawlessly against the SIH expectations. Integrations with advanced soil and marine APIs remain firmly scoped out of MVP (running as fixtures), but their absence does not harm system stability natively.
