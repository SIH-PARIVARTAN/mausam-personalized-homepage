# 01: FULL SYSTEM ARCHITECTURE

## 1. Current Architecture Diagram
```mermaid
graph TD
    UI[Next.js Frontend] -->|API Requests| BE((FastAPI Backend))
    
    subgraph BACKEND_LAYER
        BE --> DEP[deps.py\nBuilds ContextFrame]
        BE --> PREF[preferences.py\nUser Config]
        PREF <--> DB[(Neon PostgreSQL\nPrefs & Cache)]
    end
    
    subgraph ADAPTER_LAYER
        DEP --> AD_FORE[forecast_adapter.py]
        DEP --> AD_WARN[warning_adapter.py]
        DEP --> AD_AQI[aqi_adapter.py]
        DEP --> AD_UV[uv_adapter.py]
        DEP --> AD_SUN[sun_adapter.py]
        
        AD_FORE -.-> FIXTURES[Local JSON Fixtures]
        AD_AQI -.-> FIXTURES
        AD_UV -.-> FIXTURES
    end
    
    subgraph ENGINE_LAYER
        DEP -->|ContextFrame| ENG[engine.py\nrank()]
        ENG --> SC[scoring.py\nScores per Card/Persona]
        ENG --> CD[cards.py\nCard Registry]
        ENG --> EX[explain.py\nGenerates Text]
    end
    
    ENG -->|EngineOutput| BE
    BE -->|HomepageResponse| UI
```

## 2. Directory Structure and Purpose
- `engine/`: **Production-critical**. The pure, functional core. It consumes a `ContextFrame` and outputs a ranked, prioritized list of cards with explanations. 
- `backend/`: **Production-critical**. FastAPI application, routers (`homepage.py`, `preferences.py`), dependency injection (`deps.py`), and Neon Postgres initialization (`db.py`).
- `adapters/`: **Scaffolded**. Currently fetches data from `fixtures/` JSON files based on environmental variables. Fakes HTTP timeouts in some places.
- `frontend/`: (Next.js) **Client**. Reads from the backend.
- `tests/`: Covers engine and mock adapters thoroughly (137 passing tests).

## 3. The "Missing" Pieces
- Live integrations are actively bypassed.
- No ML infrastructure exists (no training, no inference, no tracking).
