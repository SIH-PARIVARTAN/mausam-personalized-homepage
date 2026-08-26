# Project Status — Mausam Personalized Homepage

> **Last updated:** 2026-08-26 (post Phase 2B commit `128d1aa`)
> **Branch:** `milestone-2-adapters-backend`
> **Purpose:** Quick-read current state for any new team member. Read this before reading the planning docs.

---

## What This Project Is

An **intelligent personalization layer** for the Mausam mobile app (IMD / MoES).

It answers the question: *given this user's persona and the current environment, what should appear at the top of their weather homepage right now?*

Core mechanics:
- Collect weather/environment signals (AQI, UV, forecast, warnings, sunrise/sunset)
- Assemble a `ContextFrame` per user request
- Score candidate homepage cards: `score = persona_weight × urgency_multiplier × confidence_factor`
- Return a ranked, explained card list via a REST API
- Frontend renders the returned order — no re-ranking in the UI

This is not a replacement weather app. It is a personalization layer.

---

## Completed Work

### Architecture Baseline · `9d471ba`

- Repository structure established
- All planning documents written (`docs/planning/`)
- Adapter interface defined
- Engine contract defined
- API contract defined (`07_api_and_data_contracts.md`)
- No code yet

### Phase 2A · `512a580`

- FastAPI backend scaffolded
- `/preferences` endpoint (GET + PUT)
- PostgreSQL persistence via `psycopg` v3 native driver + connection pool
- Neon-compatible schema (`preferences`, `signal_cache` tables)
- `backend/db.py`, `backend/settings.py`
- CORS configured

### Phase 2B · `128d1aa` — **Current HEAD**

All of the following are implemented and tested:

**Engine (`engine/`) — frozen, unmodified by Phase 2A/2B:**
- 8 card definitions (`cards.py`)
- Scoring function: `persona_weight × urgency × confidence` (`scoring.py`)
- P0–P3 priority classifier + alert-floor rule (`priority.py`)
- Conflict resolver + ranking loop (`engine.py`)
- Templated explanation generator — 8 templates, grounded in real signal values (`explain.py`)
- Data models: `ContextFrame`, `RankedCard`, `EngineOutput` (`models.py`)
- **134 unit + scenario tests** — all passing

**Adapters (`adapters/`):**
- `BaseAdapter` with `make_unavailable_signal()` contract
- `ForecastAdapter` — fixture-mode (temp, humidity, wind, precip)
- `WarningAdapter` — IMD-shaped fixture (includes severe-warning scenario)
- `AQIAdapter` — fixture-mode (live API scaffold present for future activation)
- `UVAdapter` — fixture-mode (live API scaffold present)
- `SunAdapter` — live computed via `astral` library (no external API)
- Fixture scenarios: `normal`, `rain_commute`, `heat_uv_spike`, `severe_warning`

**Backend API (`backend/`):**
- `GET /homepage` — returns ranked `HomepageResponse` with `cards[]` + `warnings_override[]`
- `GET /explain` — returns `ExplainResponse` with text + signal_refs + score_components
- `GET /preferences` and `PUT /preferences`
- `GET /health`
- `build_context_frame()` (`backend/deps.py`) — full ContextFrame assembly
- Degraded response handling: `system_notice` for full-layer failure; `source: "unavailable"` on per-card basis
- **13 backend API tests** — all passing

**Infrastructure:**
- Production boundary checker (`check_boundaries.py`) — confirms no secrets in production files
- `requirements.txt` pinned

---

## Current Architecture State

```
COMPLETE                     PENDING
────────                     ───────
engine/          ✅          frontend/src/app/page.tsx (scaffold only)
adapters/        ✅          frontend preferences screen
backend/         ✅          frontend explanation sheet
cache/store.py   ✅          live AQI/UV adapters (fixture-mode now)
backend tests    ✅
engine tests     ✅
```

---

## Current Supported Personas

| Persona | Supported | Key Cards |
|---|---|---|
| Health-conscious | ✅ | `aqi_health`, `uv_sun_exposure`, `pollen_illustrative`* |
| Outdoor fitness | ✅ | `activity_window`, `uv_sun_exposure`, `sunrise_sunset` |
| Parents & families | ✅ | `rain_commute`, `severe_warning` P0 |
| Default / cold-start | ✅ | `severe_warning` > `general_conditions` > `aqi_health` |

*`pollen_illustrative`: card definition and scoring exist; fixture/adapter not yet implemented — card always omitted in current build due to null pollen signal.

---

## Intentionally Deferred

These items were explicitly excluded from the Phase 2B MVP scope (see `docs/planning/00_project_decision_log.md` Decision D4 and `docs/planning/13_final_mvp_specification.md §52`):

- **Beachgoer / marine persona** — no public INCOIS developer API available; fixture card possible for demo
- **Traveler persona** — saved_locations field present in schema, but no multi-destination routing
- **Agriculture persona** — no accessible agromet / soil-moisture data source for students
- **Commuter (traffic)** — weather + traffic integration requires external traffic API (outside IMD scope)
- **Event planner** — multi-day forecast + comfort index not implemented
- **Pollen adapter** — no validated Indian pollen data source; card gated/illustrative
- **Live adapter hardening** — timeouts, retries, parse guards for AQI/UV live mode (see `docs/planning/16_production_architecture_reassessment.md §3`)

---

## Known Gaps

| Gap | Severity for Demo | Notes |
|---|---|---|
| Frontend not built | **Critical** | No UI = nothing to demo to judges |
| Pollen fixture missing | Moderate | Health persona feels incomplete without it |
| Live AQI/UV adapters always return `unavailable` | Moderate | Demo runs on fixture data; live data claim cannot be made |
| Comfort index not implemented | Low | Addresses event-planner PS persona |
| Marine/beachgoer card absent | Low | Addresses beachgoer PS persona with minimal effort |

---

## Immediate Next Milestone — Frontend

Implement in this order:

1. **S2 — Personalized Homepage** — `GET /homepage` → render ranked card list
2. **S4 — Preferences Editor** — `GET/PUT /preferences` → persona selector + health flags + live reorder trigger
3. **S3 — Explanation Sheet** — `GET /explain` → tap-to-reveal card explanation
4. **S5 — Loading / Degraded states** — skeleton cards, `system_notice` banner, per-card source badge

See [docs/frontend_handoff.md](frontend_handoff.md) for the full frontend developer guide.

---

## Git Milestone References

| Commit | Description |
|---|---|
| `9d471ba` | Architecture baseline |
| `512a580` | Phase 2A — PostgreSQL foundation + preferences API |
| `128d1aa` | Phase 2B — fixture adapters + personalized homepage API (current HEAD) |

---

## Test Commands (Verification Gate)

```bash
# 134 engine tests
python -m pytest engine/tests -q

# 13 backend API tests
python -m pytest backend/tests -v

# Production boundary check
python check_boundaries.py

# Git cleanliness
git diff --check
git status --short engine    # should return nothing (engine frozen)
```
