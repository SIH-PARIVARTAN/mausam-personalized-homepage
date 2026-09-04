# MAUSAM Phase B: Core Personas Execution Plan (Traveler & Commuter)

## 1. Purpose and Current Starting State
This document dictates the evidence-based execution plan for Phase B of the MAUSAM backend, targeting the **Traveler** and **Commuter** personas based on the actual repository architecture.

**Current Verified State:**
*   Phase A successfully scaffolded `health_flags` and `saved_locations` directly into the preference retrieval flow.
*   The read-only Multi-Persona Audit positively verified that the system flawlessly handles multiple personas by selecting the maximum relevant weight via `_best_persona_for_card`. 
*   The baseline engine achieves a strict 25/25 golden evaluation match and cleanly defaults to `default_general` when preferences are empty.
*   `engine/cards.py` has 8 functional cards. It currently lacks native `Traveler` and `Commuter` representations. 
*   `ContextFrame` does not yet contain visibility logic or travel-context representations.

## 2. Reconciled Findings from Roadmap & Actual Repository
*   **Obsolete Assumptions:** The old Master Roadmap assumed Travelers required live traffic inputs or complex route-mapping layers. We outright reject this. Traffic routing and ML are out of scope.
*   **P0 Current-Location Safety:** A firm boundary is codified: P0 overrides remain exclusively dedicated to the user's *current geo-location*. Warnings fetched for a Traveler's saved destinations will cap as P1 Alerts, ensuring local imminent danger is never visually overridden by a distant weather event.
*   **Multi-Persona Safety:** Because the `_best_persona_for_card` uses a geometric `max()`, we can map the new personas onto existing cards (like `rain_commute`) without inflating math or causing double-counting when mixed with other personas (e.g. Commuter + Family).

## 3. Key Product and Architectural Decision: Destination-Aware vs Route-Aware
**For Phase B, the Traveler persona is intentionally defined as destination-aware, not route-aware.**
The MVP will provide relevant current conditions, forecast/context, and warnings for selected travel destinations using the existing adapter architecture. Full route-aware weather intelligence is deliberately deferred to future scope because accurate route analysis requires route geometry, intermediate route points, and potentially a routing/maps provider. Do not treat route analysis as implemented or partially implemented. The extensible travel-context design allows future architectural extension to route-aware capabilities without re-writing the destination-oriented foundation.

## 4. Traveler Implementation Plan
**Features to Implement:**
1.  **Extensible Travel Context:** Instead of just a narrow `destination_warnings` list, `ContextFrame` will introduce a `destinations: list[DestinationContext]` array. Each `DestinationContext` will contain coordinates, basic weather/forecast data, and warnings, pulled by the existing `ForecastAdapter` and `WarningAdapter`.
2.  **Configurable Fetch Limit:** To prevent API latency/timeouts, a hard limit of `MAX_DESTINATIONS_FETCHED = 3` must be defined explicitly as a configurable constant. 
3.  **New Card (`destination_alert`):** 
    *   *Required signals:* Dynamic `_card_applies` checking if any active destination has notable weather or warnings.
    *   *Personas:* `["traveler"]`
    *   *Alert limits:* Allowed to hit P1 via urgency math, explicitly banned from P0 hard-rule assignment.
    *   *Explanation:* Grounded in both destination-specific weather and active warnings.

## 5. Commuter Implementation Plan
**Features to Implement:**
1.  **Reuse `rain_commute`:** Map the `commuter` persona to the existing `rain_commute` card with a high weight (e.g., 0.95). 
2.  **New Signal (`visibility_km`):** Extend `ContextFrame` to natively accept a `visibility_km: SignalValue`. `ForecastAdapter` must extract this from standard weather payloads.
3.  **New Card (`visibility_commute`):** 
    *   *Required signals:* `visibility_km`
    *   *Personas:* `["commuter"]`
    *   *Urgency:* Scales higher securely during the `is_commute_window` Boolean if visibility is low (e.g. < 2km).

## 6. Multi-Persona Compatibility & Safety Boundaries
*   No architectural changes needed for persona weighting. `_best_persona_for_card` securely determines overlap natively. 
*   **P0 Safeguard:** Local current warnings universally assert P0 priority immune to the traveler's P1 destination warnings.
*   **Graceful Degradation:** If network adapters timeout fetching destination weather, `destinations` defaults empty, gracefully bypassing the `destination_alert` card. Missing visibility data gracefully skips `visibility_commute`.

## 7. Data/Provider and Adapter Strategy
*   No provider hard-coding. The system remains hidden behind `WarningAdapter` and `ForecastAdapter`, ensuring flexibility to switch API sources (Open-Meteo, CPCB) without touching the personalization engine. 
*   Data origins must correctly preserve degraded (Stale, Unavailable) states dynamically.

## 8. Exact Implementation Sequence
*   **Step 1:** Define `MAX_DESTINATIONS_FETCHED = 3` constant. Update `ContextFrame` in `engine/models.py` with `destinations: list[DestinationContext]` and `visibility_km: SignalValue`.
*   **Step 2:** Update `backend/deps.py` and adapters to loop through (up to max 3) `saved_locations` passing coordinates into the adapter architecture.
*   **Step 3:** Update `engine/scoring.py` and `engine/cards.py` inserting the cards, weights, and `urgency_multipliers` matching visibility and destination warnings.
*   **Step 4:** Update `engine/explain.py` for new card explanations.
*   **Step 5:** Write unit/regression tests covering constraints (specifically testing the max 3 truncation logic limit) and multi-persona boundaries. Add scenarios to `golden_set.json`.

## 9. Test and Regression Plan
*   **New Tests Required:** `test_traveler_persona.py`, `test_commuter_persona.py`, and explicit test asserts on `MAX_DESTINATIONS_FETCHED = 3` bounds limit. 
*   **Regression Protections:** Assured 25/25 perfection must persist on historical sets.
*   **Golden Set Expansion:** Must expand evaluation to test Traveler destination logic and Commuter visibility behaviors.

## 10. Acceptance Gates
*  [ ] `MAX_DESTINATIONS_FETCHED = 3` constant limits outbound API loops. 
*  [ ] P0 local warnings universally override any P1 destination alert.
*  [ ] `visibility_km` integrated successfully without disrupting existing `ContextFrame` schemas.
*  [ ] Multi-persona arrays preserve maximum weights properly.
*  [ ] Golden set verification remains unbroken on expansion.

## 11. Explicit Out-of-Scope Items
*   Route-aware analysis, polyline data loading, intermediate weather checkpoints, or traffic routing integrations. 
*   Adding new ML features or external map dependencies.
*   Packing suggestion logic arrays (deferred to Phase C).

## 12. Documentation Requirements Post-Implementation
After implementation is functionally closed out, the following must be logged in `MAUSAM_BACKEND_IMPLEMENTATION_STATUS.md`:
*   Exact code changes made.
*   Exact tests and commands run.
*   Golden evaluation results and any acceptance-gate deviations. 
*   Explicit confirmation that the Phase B plan was fulfilled.
