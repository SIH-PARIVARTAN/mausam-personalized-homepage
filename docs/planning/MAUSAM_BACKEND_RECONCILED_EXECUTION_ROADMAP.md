# MAUSAM BACKEND RECONCILED EXECUTION ROADMAP

## 1. Executive Summary
This document serves as the authoritative, reconciled execution plan for the remainder of the SIH26076 MAUSAM Personalized Homepage backend development. 

*   **Current Starting State:** The deterministic engine foundation is fully verified and stable. The evaluation framework, testing patterns, API contracts, and core engine algorithms (`priority`, `scoring`, `conflict` resolution) have been rigorously audited. The dynamic engine correctly calculates optimal rankings against a 25-scenario golden set (scoring 25/25 100%) when given deterministic fixture inputs. The previously hypothesized need for a "calibration bound" has been rejected on evidence. 
*   **What has been completed:** Phase 0 (Foundation Stabilization), Phase 1 (Evaluation Baseline), and Intermediate Phase 2 (Foundation Correction). 
*   **What remains:** Expanding the context model, implementing remaining personas, building out dynamic provider-swappable live data adapters, adding deterministic compound insights, and final system hardening.

## 2. Reconciliation of Historical Roadmap
The previous master roadmap (`23_mausam_master_backend_implementation_roadmap.md`) mapped 10 phases (0-9). Based on the verified implementation status and constraints against over-engineering (specifically removing ML without empirical data requirements), the roadmap is reconciled as follows:

| Historical Phase | Current Status | Action | Reason |
| :--- | :--- | :--- | :--- |
| **Phase 0 (Foundation)** | **Complete** | **Remove** | Baseline stabilized, formats verified. |
| **Phase 1 (Evaluation)** | **Complete** | **Remove** | Golden set execution and methodology built. |
| **Phase 1.5 (Correction)** | **Complete** | **Remove** | Implementation defects mapped and patched. |
| **Phase 2 (Context Model)** | **Complete** | **Keep** (New Phase A) | `health_flags` and `saved_locations` are required prerequisites for subsequent personas. |
| **Phase 3 (Persona Tier 1)** | Not Started | **Keep** (New Phase B) | Traveler and Commuter rely on core logic. |
| **Phase 4 (Persona Tier 2)** | Not Started | **Keep** (New Phase C) | Agriculture, Beachgoer, Event Planner introduce novel domain models requiring careful fake/fallback handling. |
| **Phase 5 (Live Data)** | Not Started | **Modify** (New Phase D) | Adapter architecture must remain strictly provider-swappable (e.g., Open-Meteo as a candidate, not a lock). |
| **Phase 6 (Novelty)** | Not Started | **Keep** (New Phase E) | Cross-signal reasoning remains the strongest deterministic novelty constraint. |
| **Phase 7 (Telemetry)** | Not Started | **Remove** | Logging user inputs purely to feed ML is out of scope for a deterministic final SIH product unless UI interaction requires it. |
| **Phase 8 (ML Hybrid)** | Not Started | **Remove** | The current deterministic engine is a verified strength. ML introduces extreme risk and architecture bloat without defensible SIH product value. |
| **Phase 9 (Hardening)** | Not Started | **Modify** (New Phase F) | Merged into the mandatory final integration/evaluation phase. |

---

## 3. Corrected Remaining Phase Sequence
The remaining development will progress linearly through the following 6 phases:
*   **Phase A:** Context Model Completion (`health_flags`, `saved_locations`)
*   **Phase B:** Core Personas Expansion (Traveler & Commuter)
*   **Phase C:** Specialized Personas Expansion (Agriculture, Beachgoer, Event Planner)
*   **Phase D:** Dynamic Provider Integrations (Live Data Adapters & Graceful Degradation)
*   **Phase E:** Deterministic Insight Enrichment (Compound Conditions & Deltas)
*   **Phase F:** Final Integration, Evaluation, and Release Hardening

*(Note: Alpha naming is used here to permanently sever confusion from the historical numeric phases 1-9)*

---

## 4. Detailed Execution Plan

### **Phase A: Context Model Completion (`health_flags`, `saved_locations`)**
*   **Purpose:** To make the `health_flags` and `saved_locations` fields materially impactful on engine scoring and contextual logic, enabling subsequent domain personas to hook onto this capability.
*   **Exact Scope:** Add `saved_locations` array to `ContextFrame`. Introduce an explicit, targeted `health_flag_multiplier()` within `engine/scoring.py` for health-related flags (e.g., respiratory sensitivity influencing AQI card urgency). Update explanation templates to cite the health flag if it swung the priority.
*   **Files Involved:** `engine/models.py`, `engine/scoring.py`, `backend/deps.py`, `engine/explain.py`, `engine/engine.py`.
*   **Dependencies:** None. (Completed)
*   **Explicit Non-Goals:** Do NOT build the Traveler destination alert card yet; just wire the data passing. Do NOT rewrite the base multiplicative scoring logic.
*   **Acceptance Criteria:** A health-profile user with a defined health flag receives elevated priority for the targeted card compared to a profile without the flag. `ContextFrame` successfully reads `saved_locations`. 
*   **Required Automated Tests:** Unit tests for `health_flag_multiplier(...)`. Contract tests proving API endpoints safely retrieve/ignore preferences.
*   **Documentation:** Update data contracts reflecting health modifier logic.
*   **Definition of Done:** Verification tests pass without breaking existing engine performance limits.

### **Phase B: Core Personas Expansion (Traveler & Commuter)**
*   **Purpose:** Extend the persona scope to address the Traveler and Commuter SIH bullet points natively natively relying on the newly-inserted `saved_locations` architecture.
*   **Exact Scope:** Add Traveler/Commuter to `PERSONA_WEIGHTs`. Build `destination_alert` card mapped to `saved_locations` iterating via existing `WarningAdapter`. Build `packing_suggestion` mapped to deterministic lookup arrays. Add `visibility_commute` card for commuters dependent on a new `visibility` metric. 
*   **Files Involved:** `engine/cards.py`, `engine/scoring.py`, `engine/priority.py`, `adapters/fixtures/*`.
*   **Dependencies:** Phase A.
*   **Explicit Non-Goals:** Do not attempt to process live traffic density arrays or routing logic.
*   **Acceptance Criteria:** `destination_alert` triggers appropriately when a warning overlaps a `saved_location`. A Commuter persona effectively escalates visibility-related issues to P1/P2. 
*   **Required Automated Tests:** `test_traveler_persona.py`, `test_commuter_persona.py`. Assert complete coverage mapping in `test_all_32_combinations_present.py`.
*   **Documentation:** Update persona matrix coverage.
*   **Definition of Done:** Both Traveler and Commuter safely yield distinct demoable cards relying on deterministic fixture states.

### **Phase C: Specialized Personas Expansion (Agriculture, Beachgoer, Event Planner)**
*   **Purpose:** Cement the 8/8 persona SIH requirement without falsifying or exposing the system to complex unreliable data sourcing.
*   **Exact Scope:** Integrate `extended_forecast` models for Event Planners producing an `extended_outlook` card. Compute a pure mathematical `comfort_index` natively inside the engine. Create simulated `soil_moisture_advisory` and `sea_conditions` cards natively labeled as illustrative.
*   **Files Involved:** `engine/models.py`, `engine/cards.py`, `engine/derived.py`.
*   **Dependencies:** Phase B.
*   **Explicit Non-Goals:** Do not hook up live INCOIS tidal APIs or active soil sensors. These specialized signals remain safely as "simulated" illustrative metrics conforming strictly to the original safety limitations. 
*   **Acceptance Criteria:** All 8 default SIH personas possess fully operational fallback behaviors, unique card types, and distinct priority weighting tables. 
*   **Required Automated Tests:** Persona tests validating illustrative signal behavior and the mathematical correctness of `comfort_index`. 
*   **Documentation:** Update persona matrix affirming 8/8 completion.
*   **Definition of Done:** `PERSONA_WEIGHT` scales to 8 total entities; no unhandled cold-start exceptions occur.

### **Phase D: Dynamic Provider Integrations**
*   **Purpose:** Finalize the adapter abstraction, routing actual network-aware live data into the engine safely alongside cached implementations and fixture setups.
*   **Exact Scope:** Implement active `httpx` HTTP data integration within `AQIAdapter`, `UVAdapter`, and basic weather structures. Keep providers generic (e.g. Open-Meteo, CPCB) but swap-ready. Leverage `cache.store` for timeout/rate-limiting degradation. 
*   **Files Involved:** `adapters/aqi_adapter.py`, `adapters/uv_adapter.py`, `adapters/weather_adapter.py`, `cache/store.py`.
*   **Dependencies:** Phase C.
*   **Explicit Non-Goals:** Do not tightly couple JSON schemas of an API to the interior `Engine` code. Do not implement complex load balancing. 
*   **Acceptance Criteria:** The system correctly gracefully degrades from `live` -> `cached` -> `stale` -> `unavailable` dynamically based on simulated connection timeouts. 
*   **Required Automated Tests:** Adapter integration tests intercepting mock HTTP errors (timeouts, 404s, malformed 200s).
*   **Documentation:** Clear guide on how an operations team rotates out an API key or shifts weather providers from Open-Meteo to OpenWeatherMap.
*   **Definition of Done:** Complete API response capability under poor network simulated parameters.

### **Phase E: Deterministic Insight Enrichment**
*   **Purpose:** Distinguish the personalization functionality with high-leverage "why now?" features, bypassing LLM gimmicks entirely. 
*   **Exact Scope:** Implement compound detection arrays (e.g., "High Heat + Low AQI") elevating card priorities deterministically. Feed prior `ContextSnapshot` values into `engine.explain()` to append change-over-time delta messaging (e.g., "AQI has risen by 40 since yesterday."). 
*   **Files Involved:** `engine/compound.py`, `engine/explain.py`, `backend/routers/homepage.py`.
*   **Dependencies:** Phase D.
*   **Explicit Non-Goals:** Do not feed natural language generators.
*   **Acceptance Criteria:** Cross-signal conditions safely evaluate logically above standard isolated variables, maintaining P0 boundaries. 
*   **Required Automated Tests:** `test_compound_conditions.py`, `test_delta_explanation.py`. Ensure P0 overrides supersede compound conditions always.
*   **Definition of Done:** "Why now" deltas appear clearly and accurately in API explanation fields.

### **Phase F: Final Integration, Evaluation, and Release Hardening**
*   **Purpose:** Perform an overarching end-to-end integration and evaluate against an expanded array of dynamic states. 
*   **Exact Scope:** Produce a final `DEMO_RUNBOOK`. Run an expanded set of golden evaluation scenarios (now requiring representation across all 8 personas). Assure all deployment configurations map correctly without missing environment variable crashes. 
*   **Dependencies:** All previous phases.
*   **Acceptance Criteria:** Expanded 40+ element Golden Set successfully proves engine behavior without degradation. P0 critical flags route effortlessly to the top slot of a homepage API return. 
*   **Documentation:** Complete API schemas, architecture diagrams, and Final Demo Readme. 
*   **Definition of Done:** Application can be safely handed off for frontend ingestion or SIH review panel live demonstration. 

---

## 5. Provider / Data Strategy
**Flexibility Standard:** Under no circumstances should the logic of `engine/` reference an external endpoint (e.g., `open-meteo`). All external APIs are handled solely within the `/adapters/` module, which standardizes divergent payloads into an internal typed `SignalValue`.
*   **Production State (`live`):** Connects to the active API provider, passing a `.env` configured key and enforcing strict connection timeouts. 
*   **Degraded State (`cached/stale`):** Should the network drop, the adapter pulls from a local fast-store memory buffer (`cache/store.py`). 
*   **Failure State (`unavailable`):** Fails gracefully, appending an `unavailable` tag natively instructing the engine to suppress certain environmental cards.
*   **Evaluation Mode (`fixture`):** Bypasses all HTTP layers, loading fixed static dictionaries from `/adapters/fixtures/`. *Treated as functionally perfect (`confidence=1.0`) during isolated test and spike contexts.*

## 6. Testing Strategy
Future developers deploying these phases must provide verification mirroring the current repository standards:
1.  **Focused Unit Tests:** All logic additions (like `heat_multiplier`) must receive dedicated isolated unit assertions inside `engine/tests/`.
2.  **Regression Tests:** Deterministic behaviors such as Tie-breakers, Confidence assignments, and standard Priority band assignments cannot be shifted or broken. 
3.  **API/Contract Tests:** Endpoints must guarantee typed inputs and return safe error schemas (e.g. HTTP 422 Unprocessable Entity) on bad `device_id`s, not throw a 500 server exception. 
4.  **Graceful Degradation Tests:** Mandatory assertion tests forcing HTTP 408 Timeouts to prove the UI still receives an organized subset of remaining context cards.
5.  **Evaluation Exapnsion:** The `golden_set.json` must be manually expanded beyond the current 25 scenarios to integrate tests encompassing Traveler logic, Commuter logic, and specific compound delta states.

## 7. Risk Register
*   **Risk:** `health_flag_multiplier` scaling aggressively resulting in artificial inflation. 
    *   *Mitigation:* Restrict multipliers tightly within bounds (e.g., `1.2x`) instead of additive sums. Unit test boundary outcomes.
*   **Risk:** Unavailable Provider access (e.g., CPCB APIs are suddenly unreachable).
    *   *Mitigation:* Enforce `unavailable` state logic strictly preventing application crashes. 
*   **Risk:** Overpromising complex domain features (Soil moisture).
    *   *Mitigation:* Pre-label niche telemetry inputs as simulated `illustrative` signals transparently ensuring SIH judges recognize the product is demonstrating logic pipelines, not hardware sensors.

## 8. Immediate Next Action
All verification criteria has passed. Development is cleared to proceed sequentially. 
**The single recommended next implementation phase is Phase B: Core Personas Expansion (Traveler & Commuter).**
