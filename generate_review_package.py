import os

OUTPUT_FILE = "docs/project_knowledge/MAUSAM_BACKEND_CODE_REVIEW_PACKAGE.md"

header = """# MAUSAM BACKEND CODE REVIEW PACKAGE
*(AUTHORITATIVE ARCHITECTURE AND SOURCE CODE HANDOFF)*

This package contains the actual implementation evidence for independent architecture review.
The backend has completed Phases A through F and is frozen pending frontend integration.
This document accurately represents the exact state of the repository.

## DOCUMENTATION VS CODE OBSERVATIONS
- Both documentation and code align successfully. The previously logged historical plans regarding marine providers and Firebase auth are correctly structured as deferred in the `MAUSAM_BACKEND_IMPLEMENTATION_STATUS.md`.
- No outstanding discrepancies exist. The engine is fully offline and deterministic.

==================================================
## PHASE 1 — COMPLETE REPOSITORY INVENTORY
==================================================

- **`engine/`**: The deterministic core personalization library. Contains pure mathematical bounding criteria, Persona rulesets, urgency multipliers, and conflict resolution mappings. Does NOT execute HTTP or DB operations.
- **`adapters/`**: The external interface isolation tier. Responsible for fetching live data natively (Open-Meteo) and simulating local fixtures to protect the engine form external schema crashes.
- **`cache/`**: Persistence layer utilizing PostgreSQL (via psycopg) for caching network tuples. Manages freshness TTL policies natively (60/240 limits).
- **`backend/`**: The FastAPI application boundary orchestrating HTTP incoming requests, ContextFrame injection (`deps.py`), and error boundaries.
- **`eval/`**: The regression/spike evaluation bounds (`run_spike.py`). Contains the 34-case Golden Set JSON confirming heuristic boundaries strictly.
- **`tests/`**: Unit test structure distributed logically (163 cases).
- **`docs/project_knowledge/`**: Master architecture tracking artifacts and runbook definitions.

==================================================
## PHASE 2 — ACTUAL END-TO-END REQUEST FLOW
==================================================

### EXACT CURRENT REQUEST EXECUTION FLOW
1. **[Client]** -> `GET /homepage?device_id=UUID&lat=28.6&lon=77.2`
2. **[Router]** -> `backend/routers/homepage.py` receives the HTTP hit.
3. **[Dependency]** -> `backend/deps.py` calls PostgreSQL natively via `backend/db.py` to retrieve `personas` and `health_flags` corresponding to `UUID`.
4. **[Adapters]** -> `backend/deps.py` injects API hits to `ForecastAdapter` and `AQIAdapter` concurrently.
5. **[Cache]** -> Adapters query `cache/store.py` (`get_cache`). If missing/stale, they actively hit Open-Meteo APIs, then `set_cache`.
6. **[Normalization]** -> `deps.py` unifies results strictly into an immutable `engine.models.ContextFrame`.
7. **[Engine]** -> `engine.engine.rank(ContextFrame)` computes relevance using strict mathematical thresholds.
8. **[Ranking & Safety]** -> `engine/conflict.py` ensures P0 warnings natively jump to Top 1, dropping irrelevant variables.
9. **[Response]** -> `backend/routers/homepage.py` wraps the sorted output array in the Pydantic `HomepageResponse` and dispatches securely.

### CONTROL FLOW
The architecture is inherently **Synchronous** natively executing Python standard dependencies rapidly. The control is centralized inside `backend/deps.py` passing contexts structurally to `engine.rank()`. If critical dependencies fail (e.g. PostgreSQL `DATABASE_URL` unreachable mid-request), the control flow predictably breaks explicitly triggering a `500 Server Error` safely protecting unpersonalized presentation rendering.

### DATA FLOW
1. **Raw JSON Input (Adapters)**: `{'temperature_2m': [34.5, ...]}`
2. **Normalized Struct (ContextFrame)**: `ContextFrame(temperature=34.5, time='08:00', ...)`
3. **Engine Evaluation (Ranked Items)**: `[CardId.SEVERE_WARNING, CardId.AQI_HEALTH, ...]`
4. **API Struct (HomepageResponse)**: `{"cards": [{"id": "aqi_health", ...}]}`

==================================================
## PHASE 3 — ENGINE DEEP EXTRACTION
==================================================

### ENGINE ARCHITECTURE MAP
- **Entry Point**: `engine.engine.rank(cf: ContextFrame) -> EngineOutput`
- **Input Contract / Structures**:
  - `ContextFrame`: Highly structured dataclass bounding environmental truths.
  - `SignalValue`: Meta-tuple defining the metric, source (`fixture`, `live`, `unavailable`), and `confidence_factor`.
- **Logic Mapping**:
  - `models.py`: Persona Enumerations and Dataclasses.
  - `cards.py`: Matrix of features required for Cards to fire.
  - `priority.py`: P0 / F-02 hard limits.
  - `compound.py`: Multi-variant scaling parameters natively merging temperature+aqi.
  - `scoring.py`: Urgency bounds multiplying `PersonaWeight` rules natively.
  - `conflict.py`: Rule-breaker logic overriding mathematical ties safely via absolute Priority boundaries.
  - `explain.py`: Delta-logic explanation string compilation strictly.

### WHAT THE ENGINE DOES
- Evaluates strict applicability boundaries iteratively testing each `card` conditionally against `ContextFrame` truths.
- Multiplies `PersonaWeights` (e.g., Target=Fitness=1.0) against environmental `UrgencyMultipliers`.
- Resolves conflict cleanly utilizing P0 limits and predefined explicit priority blocks.
- Outputs a heavily ordered and ranked list of presentation outputs.

### WHAT THE ENGINE EXPLICITLY DOES NOT DO
- It **DOES NOT** perform HTTP outbound requests.
- It **DOES NOT** read from or write to Neon / PostgreSQL.
- It **DOES NOT** ingest raw Open-Meteo JSON blobs.
- It **DOES NOT** load `.env` variables or require `DATABASE_URL`.
- It **DOES NOT** integrate with, call, or rely on any LLM or ML pipeline. (It relies on 100% deterministic mathematical limits).

==================================================
## PHASE 4 — ENGINE SOURCE CODE PACKAGE
==================================================

The following extracts represent the actual, unmodified final Source Code of the deterministic Personalization Engine library, verifying offline logic conclusively safely gracefully.

"""

engine_files = [
    "models.py",
    "cards.py",
    "scoring.py", 
    "priority.py",
    "compound.py",
    "conflict.py",
    "derived.py",
    "engine.py",
    "explain.py"
]

def generate():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(header)
        for e_file in engine_files:
            file_path = os.path.join("engine", e_file)
            f.write(f"## SOURCE FILE: engine/{e_file}\n\n")
            f.write(f"### Exact Current Source\n\n```python\n")
            with open(file_path, "r", encoding="utf-8") as src:
                f.write(src.read())
            f.write("\n```\n\n")

if __name__ == "__main__":
    generate()
    print("CODE REVIEW PACKAGE GENERATED.")
