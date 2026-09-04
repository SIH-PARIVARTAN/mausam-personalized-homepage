# MAUSAM SIH26076: Demo Runbook

## 1. Pre-Demo Checklist
Before beginning any SIH evaluation demonstration, verify the environment:
- [ ] `.env.local` is present in the repository root containing `DATABASE_URL`.
- [ ] `DATABASE_URL` is correct and the PostgreSQL database (Neon) is reachable.
- [ ] The terminal does not explicitly print or expose `DATABASE_URL` anywhere.
- [ ] Port `8000` is free.
- [ ] Internet connection is active.

## 2. Startup Procedure
Start the backend API using Uvicorn with the local environment file.

```bash
uvicorn backend.main:app --env-file .env.local
```
*Note: The `--env-file .env.local` flag is required because `load_dotenv()` defaults to `.env`.*

## 3. Normal Live Demonstration
Once the server is running, trigger a query against the API (e.g., using a browser or `curl`):
`http://localhost:8000/homepage?device_id=sihtest1234&lat=28.6&lon=77.2`

Watch the console for normal operation resolution timings.
```text
INFO:backend.routers.homepage:Resolved /homepage in 240ms (is_alert=False)
```

## 4. Cache Demonstration
Reload the exact same URL within 60 minutes.
Observe the terminal logs indicating cache hit:
```text
INFO:adapters.forecast_adapter:Serving fresh cache for Forecast
INFO:adapters.aqi_adapter:Serving fresh cache for AQI
```
The response time should drop significantly (e.g., `<50ms`).

## 5. Provider Failure Demonstration (Graceful Degradation)
To prove the architecture safely handles unavailable providers without crashing:
1. **Disable your Wi-Fi interface** (or disconnect the network route).
2. Wait for the `timeout=1.5` bounds on Open-Meteo to expire for a new coordinate (e.g. `lat=22.6&lon=88.3`).

## 6. Soft-Stale Fallback Demonstration
If the cache for a coordinate is older than 60 minutes but newer than 4 hours, and the live provider fails (as simulated above), the system falls back to the soft-stale cache.
```text
WARNING:adapters.aqi_adapter:Live fetch failed for AQI (ConnectTimeout). Attempting fallback.
INFO:adapters.aqi_adapter:Serving soft stale cache for AQI after live failure
```

## 7. Empty-Cache / Hard-Stale Degradation Demonstration
If the Wi-Fi is disabled and you query a completely new coordinate without cache history, the system degrades to "unavailable" natively.
```text
WARNING:adapters.forecast_adapter:Hard stale or empty cache for Forecast. Degrading to unavailable.
WARNING:backend.routers.homepage:Resolved /homepage in 21ms WITH DEGRADATION (all sources unavailable)
```
The UI response natively drops dependent cards and defaults to `General Conditions` correctly.

## 8. Regression Demonstration
Run the test suite to prove that all underlying deterministic rules are intact.
```bash
$env:PYTHONPATH="."
pytest engine/tests/ adapters/tests/
```
**Expected Result:** `175 passed` (or functionally equivalent perfect pass-rate).

## 9. Golden Evaluation Demonstration
Run the 34-scenario Golden Spike limits.
```bash
$env:PYTHONPATH="."
python eval/run_spike.py
```
**Expected Result:** `34/34 passing successfully`.

## 10. Recovery Checklist
*   **Database connection fails on startup:** Verify `DATABASE_URL` and internet connection to Neon.
*   **500 Internal Server Error during requests:** The database is unreachable mid-request. Ensure the DB is online. (The backend is critically dependent on PostgreSQL).
*   **Port is occupied:** Kill existing processes on port 8000 or use `--port 8001`.
*   **Environment file missing:** The app will crash with `ValueError: DATABASE_URL must be configured.`

## 11. Safety Rules
*   **NEVER** expose the `DATABASE_URL` credential string during a live code review or demonstration.
*   **NEVER** commit `.env.local` to version control.
*   If terminal logs output exceptions related to DB connection drop, ensure the DSN does not leak the password.
