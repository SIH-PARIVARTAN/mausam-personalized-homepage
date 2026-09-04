# MAUSAM PHASE E: LIVE PROVIDER INTEGRATION & RESILIENT DATA ACQUISITION

## 1. Document Context
This document serves as the repository-grounded blueprint for **Phase E: Live Provider Integration**, developed following the successful strict read-only architectural closure audit.

## 2. Verified Backend Starting State
*   **Phase D** is definitively closed natively.
*   **pytest engine/tests/** returns `156 passed in 0.66s`.
*   **run_spike.py** returns `34/34 (100.0%)` precision.
*   **Architecture Flow:** The backend utilizes fully synchronous pipeline boundaries natively loading via `deps.py` dependencies.

## 3. Master Roadmap Reconciliation
*   **Original Intention:** Expand the data pipeline to handle live inputs, ML structures, telemetry layers. 
*   **Reconciled Decision:** ML is entirely removed and rejected from Phase E. Telemetry is removed. The deterministic algorithm scales reliably up to 8 personas natively and generates sufficient precision avoiding expensive LLM hallucination risks. The phase is officially scoped solely bound to **Resilient Data Acquisition via HTTPS**. 

## 4. Actual Request and Data Flow
1. **API Endpoint Route:** (e.g. `backend/routers/homepage.py`) captures standard HTTP request metrics sync.
2. **Dependency Injection:** `Depends(build_context_frame)` triggers inside `backend/deps.py` calling synchronous loops natively. 
3. **Adapter Invocation:** Synchronous endpoints `ForecastAdapter().fetch(...)` initialize native class interfaces safely processing parameters natively.
4. **ContextFrame Assembly:** The tuple attributes output strictly directly into the `models.ContextFrame(...)` constructor natively.
5. **Engine Evaluation:** Passes synchronously to `engine.py`.

## 5. Adapter Contract Audit
*   **ForecastAdapter:** `return (temp_c, humidity, wind_kmh, precip_prob_pct, vis_km, soil_pct, extended_forecast)`. A rigid 7-tuple.
*   **AQIAdapter:** `return aqi`. Single `SignalValue`.
*   **MarineAdapter:** `return (wave, water_t, tide)`. A rigid 3-tuple.
*   **Unavailable Safeties:** All return layers possess concrete `self.make_unavailable_signal()` defaults natively ensuring zero tuple schema breakages.

## 6. Cache / PostgreSQL Audit
*   **Integration Truth:** `backend/db.py` implements a persistent `psycopg` connection pool. Schema natively enforces `signal_cache` creation possessing (`cache_key, value_json, source, fetched_at, confidence, freshness_min`).
*   **Verdict:** VERIFIED AND USABLE NOW. PostgreSQL is already perfectly prepared caching SignalValues natively avoiding Redis deployment overheads organically.

## 7. Live Signal and Provider Matrix
| CURRENT SIGNAL | CURRENT ADAPTER | REQUIRED NATIVELY? | PROPOSED PROVIDER | PHASE E DECISION |
| :--- | :--- | :--- | :--- | :--- |
| `temp_c` | ForecastAdapter | YES | Open-Meteo Weather | IMPLEMENT NOW — REQUIRED |
| `precip_prob_pct` | ForecastAdapter | YES | Open-Meteo Weather | IMPLEMENT NOW — REQUIRED |
| `visibility_km` | ForecastAdapter | YES | Open-Meteo Weather | IMPLEMENT NOW — REQUIRED |
| `aqi` | AQIAdapter | YES | Open-Meteo AQI | IMPLEMENT NOW — REQUIRED |
| `soil_moisture_pct` | ForecastAdapter | ILLUSTRATIVE | N/A | FIXTURE ONLY / UNAVAILABLE |
| `extended_forecast` | ForecastAdapter | ILLUSTRATIVE | N/A | FIXTURE ONLY / UNAVAILABLE |
| `wave_height_m` | MarineAdapter | ILLUSTRATIVE | N/A | FIXTURE ONLY / UNAVAILABLE |
| `warnings` | WarningAdapter | ILLUSTRATIVE | N/A | FIXTURE ONLY / UNAVAILABLE |

## 8. Sync vs Async Architecture Decision
*   **Decision:** STRICTLY SYNCHRONOUS. 
*   **Reasoning:** The entire `backend/deps.py` and `db.py` layer operates synchronously natively using `psycopg.connect`. Converting adapters to `async` would fracture the entire `ContextFrame` construction block. Adapters will use synchronous `httpx.Client()` wrapped natively within strict limits ensuring parallel threading safely executes within acceptable MS boundaries natively.

## 9. Final Failure / Cache / Degradation Model
**Architecture Selected:** `Live on miss/stale -> Cache update -> fallback -> Unavailable`
*   If `freshness_min` evaluates > 60 inside `cache/store.py`, it forces a Live Httpx fetch natively against Open-Meteo.
*   If HTTP triggers `40x`, `50x`, or `TimeoutException` (`> 1500 MS`), the fetch excepts gracefully.
*   The system then safely pulls the Stale cache as a fallback to avoid UI blocking.
*   If cache evaluates completely empty, falls backwards to `self.make_unavailable_signal()` gracefully protecting ContextFrame evaluations natively.

## 10. Fixture Mode and Test Isolation Guarantee
*   `ADAPTER_MODE="fixture"` explicitly exists actively mapping arrays immediately bypassing live blocks natively.
*   The Pytest suite and `run_spike.py` scripts execute natively bounded protecting outbound pings completely safely.

## 11. Final Reconciled Phase E Scope
**A. Implement Now — Required:**
*   Live Open-Meteo queries inside `ForecastAdapter` returning `temp_c, precip, visibility`.
*   Live Open-Meteo queries inside `AQIAdapter` extracting AQI indices properly.
*   Graceful mapping mapping un-fetchable signals (`soil_moisture`) to `unavailable`.

**E. Deferred:**
*   LLM chatbots.
*   Agricultural API keys.

## 12. Regression-Safe Implementation Sequence
1.  **Step E1:** Setup `httpx` timeouts securely handling outbound exceptions. 
2.  **Step E2:** Integrate `AQIAdapter` fetching live metrics persisting seamlessly to `cache.store`. 
3.  **Step E3:** Integrate `ForecastAdapter` retaining strictly the exact 7-element Tuple signature ensuring graceful degradation mappings natively.
4.  **Step E4:** Assure tests successfully run bounding outputs ensuring fixtures securely block integration bleeding natively.

## 13. Acceptance Gates
*   **GATE 1:** Existing deterministic regression suite remains fully passing manually.
*   **GATE 2:** Golden evaluation remains 100% deterministic in fixture mode securely.
*   **GATE 3:** No outbound HTTP calls escape the pytest architecture native boundaries.
*   **GATE 4:** `httpx` Timeout parameters do not block UI execution globally returning gracefully evaluated degraded lists.
*   **GATE 5:** Native PostgreSQL Cache effectively updates freshness_min securely retaining persistent queries organically.
