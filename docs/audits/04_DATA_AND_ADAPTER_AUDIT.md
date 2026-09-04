# 04: DATA AND ADAPTER AUDIT

## 1. External Data Sources & Adapters Status
The backend architecture is clean and adapter-based (`adapters/base.py` and implementers), meaning swapping a mock for a live API requires zero changes to the engine.

| Adapter | Intended Provider | Current Status | Mocked? | Real Network Calls? |
|---|---|---|---|---|
| AQI (`aqi_adapter.py`) | Air Quality API | MOCKED | Yes via `fixtures/` | No |
| Weather (`forecast_adapter.py`) | IMD / OpenWeather | MOCKED | Yes via `fixtures/` | No |
| Sun (`sun_adapter.py`) | Astronomical API | MOCKED | Yes via `fixtures/` | No |
| UV (`uv_adapter.py`) | UV Index API | MOCKED | Yes via `fixtures/` | No |
| Warnings (`warning_adapter.py`) | IMD Severe Alerts | MOCKED | Yes via `fixtures/` | No |

**Evidence (`aqi_adapter.py`):**
```python
mode = os.getenv("ADAPTER_MODE", "fixture")
if mode == "fixture":
    filepath = os.path.join(os.path.dirname(__file__), "fixtures", "aqi_uv_recorded_samples.json")
```

**Verdict:** The Live Data integration is currently **0% complete**. The HTTP path inside the adapters catches `httpx.TimeoutException` but then immediately returns standard `unavailable_signal()`.

## 2. Database and Persistence Audit
**Current Implementation:**
`backend/db.py` initialize Neon Postgres with `psycopg_pool`.

**Tables:**
1. `preferences`: Stores `device_id`, `personas` (JSON string), `health_flags` (JSON string), `saved_locations`.
2. `signal_cache`: Stores transient API responses so the UI loads instantly. Columns: `cache_key`, `value_json`, `source`, `confidence`, `freshness_min`.

**Data Ownership Flaws:**
- `device_id` is passed blindly via the `GET /homepage?device_id=X` query string.
- No secure session or token signature authentication is implemented in the DB layer. Firebase Auth tokens from the frontend are entirely ignored on the backend right now. 
- *Consequence:* You cannot store sensitive ML training logs yet until auth is locked down.
