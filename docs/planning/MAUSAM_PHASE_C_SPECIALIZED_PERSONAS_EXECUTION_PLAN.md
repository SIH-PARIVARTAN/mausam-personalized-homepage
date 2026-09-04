# MAUSAM Phase C: Specialized Personas Execution Plan

## 1. Purpose and Current Starting State
This document represents the final, authoritative, reconciled execution plan for Phase C, adding the Specialized Personas (**Agriculture/Gardener**, **Beachgoer/Surfer**, and **Event Planner**) while preserving SIH-grade backend integrity. 

**Current Verified State:**
*   **Engine Core:** Deterministic Engine operates perfectly (27/27 golden matches) and gracefully degrades external/missing inputs. Multi-persona overlaps are successfully mitigated using the `max()` geometric weight selection.
*   **Safety Limits & P0 Verification:** Local P0 overrides explicitly override any peripheral alerts. Fixtures themselves do not guarantee safety; P0 protection is strictly preserved and enforced through the existing `conflict.py` priority architecture. This must be explicitly proven with regression tests.
*   **Source vs Confidence Semantics:** The system separates source metadata from confidence. `fixture` data used for deterministic testing utilizes appropriate trusted confidence semantics (e.g. 1.0) and is not automatically treated as simulated. `simulated` data intentionally uses degraded (0.7) confidence logic.

## 2. Reconciled Phase C Scope (Live-Ready Architecture)
**CORRECTION:** Phase C will NOT permanently reduce complex SIH problems into single dummy strings (e.g. `sea_conditions_fair`). We will construct the exact provider-ready data models required for future API bindings (Phase D) using real, extensible properties.

*   **Data Flow:** Local JSON fixtures containing *realistically shaped data* will pass through standard adapters (`ForecastAdapter`, `MarineAdapter`).
*   **Phase C vs Phase D:** Phase C builds the Domain Models (`ContextFrame`), Adapters, and Engine Rules (`cards.py`) using `fixture` payloads. Phase D will replace the fixture file loads with active `httpx` logic (e.g. Open-Meteo).

## 3. Specialized Personas & Exact Data Implementations

### A. Agriculture / Gardener (`agriculture`)
*   **SIH Target:** Soil moisture, rainfall predictions, frost alerts, and seasonal planting guidance.
*   **Phase C Data Contract (`ContextFrame` extension):**
    *   `soil_moisture_pct` (SignalValue - parsing Open-Meteo `soil_moisture_0_to_1cm` via adapter).
    *   `frost_warning_active` (Computed logically offline if Temp < 2°C).
    *   `planting_season_guidance` (Architecturally defined, sourced as `"unavailable"` until backend DB logic is scaled).
*   **Implementation Map:** `ForecastAdapter` will be modified to parse these natively. A new card `agriculture_advisory` will be rated deterministically. 

### B. Beachgoer / Surfer (`beachgoer`)
*   **SIH Target:** Sea conditions, tide timings, wave height, and water temperature.
*   **Phase C Data Contract (`ContextFrame` extension):**
    *   `wave_height_m` (SignalValue)
    *   `water_temp_c` (SignalValue)
    *   `tide_status` (String/Enum payload)
*   **Implementation Map:** Because terrestrial weather APIs rarely mix marine attributes well, a dedicated `MarineAdapter` will be created targeting a realistic `fixtures/marine_sample.json`. For Phase C, we will evaluate `wave_height_m` directly into a `marine_conditions_alert` card. Existing temperature arrays can augment it. 

### C. Event Planner (`event_planner`)
*   **SIH Target:** Extended forecasts, probability of rain horizons, and comfort index.
*   **Phase C Data Contract (`ContextFrame` extension):**
    *   `comfort_index` (Computed dynamically using current `temp_c` and `humidity_pct`).
    *   `extended_forecast` (List of `DailyForecastSummary` objects, a production-grade lightweight model containing only genuinely required fields: date, temperature range, precipitation/rain probability, weather condition, and source/confidence metadata. ContextFrame avoids nested full ContextFrames). 
*   **Implementation Map:** Comfort index is completely deterministically constructed inside Phase C natively (`engine/derived.py`). The extended forecast array will securely yield an `event_outlook` card, but gracefully remain lightweight until true API multi-day HTTP arrays expand in Phase D.

## 4. Multi-Persona Compatibility & Constraints
*   **Behavioral Protection:** Existing algorithms natively handle multi-persona overlaps.
*   **P0 Guarantee:** No simulated marine or soil data will bypass the P0 local warning gate natively governed by `conflict.py`. 
*   **Missing Features:** If `MarineAdapter` returns `"unavailable"`, cards dynamically fail `_card_applies()`, hiding smoothly.

## 5. Explicit Implementation Sequence (Read-Only Plan)
*   **Step 1:** Build `adapters/marine_adapter.py` and exact fixture JSONs.
*   **Step 2:** Expand `ContextFrame` in `engine/models.py` with multi-field agricultural, marine, and extended-forecast structures.
*   **Step 3:** Hook parsing logic into adapters.
*   **Step 4:** Build `engine/derived.py` containing the `comfort_index` & `frost_warning` mathematical engines.
*   **Step 5:** Define the three domain cards (`agriculture_advisory`, `marine_conditions_alert`, `event_outlook`) in `engine/cards.py`. 
*   **Step 6:** Map exact Persona Weights in `engine/scoring.py` matching the multi-metric urgency parameters. 
*   **Step 7:** Add explicitly isolated tests (e.g., `test_event_planner_persona.py`) preventing logic regression on the existing 27/27 baseline. Extend `golden_set.json`.

## 6. Exact Files to be Modified
*   `adapters/marine_adapter.py` (New file)
*   `adapters/fixtures/marine_sample.json` (New file)
*   `adapters/forecast_adapter.py`
*   `engine/models.py`
*   `engine/cards.py`
*   `engine/scoring.py`
*   `engine/explain.py`
*   `engine/derived.py` (New file)

## 7. Execution Status
Phase C planning is **COMPLETED**.
Implementation code is **NOT YET STARTED**. 
The recommended first action is beginning Step 1 (MarineAdapter creation).
