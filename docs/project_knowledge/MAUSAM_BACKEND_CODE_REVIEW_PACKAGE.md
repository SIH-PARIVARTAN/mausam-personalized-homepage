# MAUSAM BACKEND CODE REVIEW PACKAGE
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

## SOURCE FILE: engine/models.py

### Exact Current Source

```python
"""
engine/models.py

Data models for the Mausam Personalized Homepage engine.

These dataclasses form the contract between the data adapter layer and the
personalization engine. They must NOT import anything from fastapi, requests,
sqlite3, adapters, backend, or cache — the engine is a pure function module.

Source of truth: 07_api_and_data_contracts.md §1, 14_implementation_blueprint.md §3.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal


# ---------------------------------------------------------------------------
# Signal provenance
# ---------------------------------------------------------------------------

Source = Literal["live", "cached", "simulated", "stale", "unavailable"]
"""
Provenance/freshness of a single environmental signal.

live       — fetched successfully from a real API right now.
cached     — fetched recently; served from cache because live fetch failed.
simulated  — fixture/demo data; always disclosed on the UI.
stale      — cached but beyond the freshness threshold; score is penalised.
unavailable— no value at all (no live data, no cache, no safe default).
"""


@dataclass
class SignalValue:
    """
    A single environmental measurement with provenance metadata.

    Every environmental field in ContextFrame uses this shape.
    The engine reads `.source` and `.confidence` to down-weight degraded data
    without ever hiding the degradation from the UI.
    """
    value: float | int | str | dict | list | None
    """
    Scalar measurement, or a small dict for composite signals (e.g. AQI
    carries {"aqi": 178, "dominant": "pm2.5"}).
    None when source == "unavailable".
    """
    source: Source
    """Provenance; always non-None (required by 07_...md §5 invariant)."""
    freshness_min: int | None
    """Age of the reading in minutes. None when source == "unavailable"."""
    confidence: float
    """
    0.0–1.0.  Derived from freshness + source type:
      live=1.0, cached≈0.9, simulated≈0.7, stale≈0.3, unavailable=0.0
    The engine multiplies this in as confidence_factor; the UI can display it
    as a badge.  06_...md §4 "confidence illustrative values" table.
    """

MAX_DESTINATIONS_FETCHED = 3

@dataclass
class DestinationContext:
    """
    Context for a saved travel destination.
    Provides a scalable foundation for destination-aware (not route-aware) components.
    """
    lat: float
    lon: float
    warnings: list[dict] = field(default_factory=list)
    temp_c: SignalValue = field(
        default_factory=lambda: SignalValue(None, "unavailable", None, 0.0)
    )

@dataclass
class DailyForecastSummary:
    """
    Lightweight forecast summary for extended horizons (e.g. event planning).
    Structurally isolated to prevent recursive/nested ContextFrame bloat.
    """
    date: str
    temp_min_c: float | None
    temp_max_c: float | None
    precip_prob_pct: float | None
    condition: str | None
    source: Source = "unavailable"
    confidence: float = 0.0

# ---------------------------------------------------------------------------
# Context frame — the single input to rank()
# ---------------------------------------------------------------------------

@dataclass
class ContextFrame:
    """
    Complete snapshot of user + temporal + environmental context for one
    homepage render.  Built by the backend's deps.py, passed into the engine
    as-is.  The engine must not make any I/O calls; all data lives here.

    Spec: 07_api_and_data_contracts.md §1, 03_...md §2.
    """

    # ---- User / persona context ----------------------------------------
    personas: list[str]
    """
    e.g. ["health"], ["fitness"], ["family"], or ["default_general"]
    for cold-start.  Multi-persona is supported per 09_...md §1 S4.
    Never empty — cold-start uses ["default_general"].
    """
    health_flags: list[str]
    """
    e.g. ["respiratory_sensitive", "heat_sensitive"].
    Empty list for no declared flags or cold-start.
    """
    has_declared_profile: bool
    """False for a cold-start / new-user session."""

    # ---- Temporal context -----------------------------------------------
    local_time: str            # ISO 8601, e.g. "2026-08-26T18:40:00+05:30"
    is_commute_window: bool    # derived by backend from time + saved active-hours
    is_daylight: bool          # derived from sunrise/sunset

    # ---- Location -------------------------------------------------------
    lat: float
    lon: float
    location_name: str = "Unknown"

    # ---- Environmental signals ------------------------------------------
    # Each carries {value, source, freshness_min, confidence}; the engine
    # never modifies these — it only reads them.

    temp_c: SignalValue = field(
        default_factory=lambda: SignalValue(None, "unavailable", None, 0.0)
    )
    feels_like_c: SignalValue = field(
        default_factory=lambda: SignalValue(None, "unavailable", None, 0.0)
    )
    humidity_pct: SignalValue = field(
        default_factory=lambda: SignalValue(None, "unavailable", None, 0.0)
    )
    wind_kmh: SignalValue = field(
        default_factory=lambda: SignalValue(None, "unavailable", None, 0.0)
    )
    precip_prob_pct: SignalValue = field(
        default_factory=lambda: SignalValue(None, "unavailable", None, 0.0)
    )
    warnings: list[dict] = field(default_factory=list)
    """
    List of active severe-weather warnings.
    Each entry: {"severity": "red/orange/yellow", "type": str, "text": str}.
    Empty list = no active warnings.
    """
    aqi: SignalValue = field(
        default_factory=lambda: SignalValue(None, "unavailable", None, 0.0)
    )
    """
    value is a dict {"aqi": int, "dominant": str} when available,
    or None when unavailable.
    """
    uv: SignalValue = field(
        default_factory=lambda: SignalValue(None, "unavailable", None, 0.0)
    )
    visibility_km: SignalValue = field(
        default_factory=lambda: SignalValue(None, "unavailable", None, 0.0)
    )

    # ---- Phase C: Specialized Personas Fields ---------------------------
    soil_moisture_pct: SignalValue = field(
        default_factory=lambda: SignalValue(None, "unavailable", None, 0.0)
    )
    frost_warning_active: bool = False
    planting_season_guidance: str = "unavailable"

    wave_height_m: SignalValue = field(
        default_factory=lambda: SignalValue(None, "unavailable", None, 0.0)
    )
    water_temp_c: SignalValue = field(
        default_factory=lambda: SignalValue(None, "unavailable", None, 0.0)
    )
    tide_status: str = "unavailable"

    comfort_index: float | None = None
    extended_forecast: list[DailyForecastSummary] = field(default_factory=list)
    pollen: SignalValue | None = None
    """
    None when pollen feature is entirely disabled.
    When present: SignalValue with source always "simulated".
    """
    sunrise: str = "06:00"    # HH:MM local time, locally computed (always "live")
    sunset: str = "18:30"     # HH:MM local time, locally computed (always "live")
    destinations: list[DestinationContext] = field(default_factory=list)

# ---------------------------------------------------------------------------
# Engine output
# ---------------------------------------------------------------------------

@dataclass
class RankedCard:
    """
    A single scored and ranked card, output by the engine.
    Maps directly onto 07_api_and_data_contracts.md §3.
    """
    card_id: str
    """Matches a key in CARD_DEFINITIONS (engine/cards.py)."""
    priority: Literal["P0", "P1", "P2", "P3"]
    is_alert: bool
    score: float
    """Raw numeric score: persona_weight × urgency_multiplier × confidence_factor."""
    score_components: dict
    """
    {"persona_weight": float, "urgency_multiplier": float, "confidence_factor": float}
    Preserved for explanation generation and inspector/test use.
    """
    explanation_text: str
    """
    Templated explanation grounded in signal_refs values.
    Never LLM-generated, never free-text.
    """
    signal_refs: list[dict]
    """
    [{"signal": "aqi", "value": 178, "source": "live"}, ...]
    The checkable evidence behind NFR-1 traceability.
    """


@dataclass
class EngineOutput:
    """
    Full output of engine.rank().
    ranked_cards excludes P0 overrides (those are in override_warnings).
    """
    ranked_cards: list[RankedCard]
    """
    P1–P3 cards, sorted descending by effective priority then score.
    Frontend renders these as the scrollable card list.
    """
    override_warnings: list[RankedCard]
    """
    P0 cards only.  Frontend renders these *above* ranked_cards with a
    visual break — they never scroll away.
    """


# ---------------------------------------------------------------------------
# ContextFrame validation (pure function, no I/O)
# ---------------------------------------------------------------------------

def validate_context_frame(cf: ContextFrame) -> list[str]:
    """
    Validate the ContextFrame before passing it to rank().

    Returns a list of human-readable error strings.
    An empty list means the frame is valid.

    Spec: 14_implementation_blueprint.md §3 (ContextFrame validation block).
    The backend calls this and returns a 4xx on non-empty errors.
    Missing/stale data is NOT a validation error — that is a designed-for
    state, not an API-misuse case (07_...md §4).
    """
    errors: list[str] = []

    if not cf.personas:
        errors.append("personas must be non-empty; use ['default_general'] for cold-start")

    if not (-90 <= cf.lat <= 90):
        errors.append(f"lat out of range: {cf.lat}")

    if not (-180 <= cf.lon <= 180):
        errors.append(f"lon out of range: {cf.lon}")

    for sig_name, sig in [("aqi", cf.aqi), ("uv", cf.uv)]:
        if not (0.0 <= sig.confidence <= 1.0):
            errors.append(f"{sig_name}.confidence out of 0–1 range: {sig.confidence}")

    return errors

```

## SOURCE FILE: engine/cards.py

### Exact Current Source

```python
"""
engine/cards.py

Registry of all 8 MVP homepage cards.

This is data, not logic — the engine reads this dictionary.
Adding a new card later only requires adding an entry here and the
corresponding weight, urgency, and explanation handlers in their modules.

Source of truth: 03_personalization_logic_and_decision_matrix.md §3,
                 14_implementation_blueprint.md §3 (cards.py block),
                 15_implementation_completion_and_handoff.md §0.3.
"""

# Each card definition:
#   personas         : list of persona tags this card is "relevant to",
#                      or ["*"] meaning all personas.
#   base_priority_floor : optional; "P0" for severe_warning bypasses scoring.
#   alertable        : if False, this card can NEVER become an alert even if
#                      urgency is high (pollen_illustrative is the only case).
#   required_signals : which ContextFrame fields must NOT be "unavailable" for
#                      this card to be a candidate.  Checked by _card_applies().
CARD_DEFINITIONS: dict[str, dict] = {
    "severe_warning": {
        "personas": ["*"],
        "base_priority_floor": "P0",
        "alertable": True,
        "required_signals": ["warnings"],   # non-empty list
        "description": "Severe weather warning — active override alert.",
    },
    "compound_heat_aqi_danger": {
        "personas": ["health", "fitness"],
        "alertable": True,
        "required_signals": [],  # Dynamic bounds verified natively by compound.py
        "description": "Composite physiological danger from extreme heat and dangerous AQI.",
    },
    "compound_driving_hazard": {
        "personas": ["commuter", "family"],
        "alertable": True,
        "required_signals": [],  # Dynamic bounds verified natively by compound.py
        "description": "Composite transit hazard heavily escalated by rain and low visibility.",
    },
    "aqi_health": {
        "personas": ["health", "fitness"],
        "alertable": True,
        "required_signals": ["aqi"],
        "description": "Air Quality Index and health guidance.",
    },
    "uv_sun_exposure": {
        "personas": ["health", "fitness"],
        "alertable": True,
        "required_signals": ["uv"],
        "description": "UV index and sun exposure guidance.",
    },
    "activity_window": {
        "personas": ["fitness"],
        "alertable": True,
        "required_signals": [],  # composite — at least one signal; handled in _card_applies
        "description": "Best outdoor activity window based on current conditions.",
    },
    "rain_commute": {
        "personas": ["family", "fitness", "commuter"],
        "alertable": True,
        "required_signals": ["precip_prob_pct"],
        "description": "Precipitation forecast and commute impact.",
    },
    "visibility_commute": {
        "personas": ["commuter"],
        "alertable": True,
        "required_signals": ["visibility_km"],
        "description": "Poor visibility alerts during commute windows.",
    },
    "destination_alert": {
        "personas": ["traveler"],
        "alertable": True,
        "required_signals": [], # Checked dynamically via _card_applies looking at destinations array natively
        "description": "Weather and safety insights for saved travel destinations.",
    },
    "agriculture_advisory": {
        "personas": ["agriculture"],
        "alertable": True,
        "required_signals": [], # Handled dynamically to combine frost + soil
        "description": "Farming and gardening guidance (soil moisture, frost).",
    },
    "marine_conditions_alert": {
        "personas": ["beachgoer"],
        "alertable": True,
        "required_signals": ["wave_height_m"], # Minimum required to consider marine viable
        "description": "Coastal safety indices and wave alerts.",
    },
    "event_outlook": {
        "personas": ["event_planner"],
        "alertable": False,
        "required_signals": [], # Evaluates comfort index or extended forecast
        "description": "Extended event horizons and comfort logic.",
    },
    "sunrise_sunset": {
        "personas": ["fitness", "default_general"],
        "alertable": False,
        "required_signals": [],   # always available (locally computed)
        "description": "Sunrise and sunset times; daylight information.",
    },
    "general_conditions": {
        "personas": ["*"],         # fallback/cold-start card for all personas
        "alertable": False,
        "required_signals": [],   # composite; handled in _card_applies
        "description": "Current temperature, humidity, and wind conditions.",
    },
    "pollen_illustrative": {
        # GATED: only ever shown when:
        #   1. user declared the "health" persona, AND
        #   2. "pollen_interest" is in health_flags, AND
        #   3. cf.pollen is not None.
        # This is an opt-in, not just a low-weight card.
        # Source: 15_...md §0.3, 13_final_mvp_specification.md pollen note.
        "personas": ["health"],
        "alertable": False,
        "required_signals": ["pollen"],
        "description": "Pollen level (illustrative / simulated, always disclosed).",
    },
}

# Stable ordering for conflict resolution tie-breaking (03_...md §8, rule 4).
# Earlier in this list = wins the tie.
CARD_DEFINITION_ORDER: list[str] = [
    "severe_warning",
    "compound_heat_aqi_danger",
    "compound_driving_hazard",
    "destination_alert",
    "visibility_commute",
    "marine_conditions_alert",
    "agriculture_advisory",
    "aqi_health",
    "rain_commute",
    "uv_sun_exposure",
    "activity_window",
    "event_outlook",
    "sunrise_sunset",
    "general_conditions",
    "pollen_illustrative",
]

assert set(CARD_DEFINITION_ORDER) == set(CARD_DEFINITIONS), (
    "CARD_DEFINITION_ORDER and CARD_DEFINITIONS must contain identical card IDs."
)

```

## SOURCE FILE: engine/scoring.py

### Exact Current Source

```python
"""
engine/scoring.py

Deterministic scoring pipeline for the Mausam personalization engine.

Pipeline per card:
    score = persona_weight × urgency_multiplier × confidence_factor

Each factor is computed by a dedicated, small, testable function.

Source of truth:
  - 03_personalization_logic_and_decision_matrix.md §4
  - 14_implementation_blueprint.md §3 (scoring.py block)
  - 15_implementation_completion_and_handoff.md §1 (all placeholders filled)

IMPORTANT: urgency_multiplier() must never read persona; it is purely a
function of environmental signals.  This independence is what proves the
engine is not just a persona lookup table (Risk R5 mitigation per 03_...md §4).
"""
from __future__ import annotations

from .models import ContextFrame, SignalValue

# ---------------------------------------------------------------------------
# Persona × Card weight table
# ---------------------------------------------------------------------------

# Full 8-card × 4-persona table.
# Values are design-quality placeholders consistent with 03_...md §3 scenario
# walkthrough and 15_...md §1.  Sanity-check against eval/run_spike.py before
# treating these as final/tuned.
#
# Interpretation: 0.0 = no relevance; 1.0 = maximum relevance.
# For cards where all personas have equal weight (e.g. severe_warning), the
# weight is 1.0 because P0 hard-rule bypasses scoring anyway — the weight
# is retained so explanation_text/score_components are never null.

PERSONA_WEIGHT: dict[tuple[str, str], float] = {
    # --- severe_warning ---------------------------------------------------
    # P0 hard-rule bypasses scoring; weights kept at 1.0 for all personas
    # so score_components are always populated (never null for explanations).
    ("severe_warning", "health"):          1.0,
    ("severe_warning", "fitness"):         1.0,
    ("severe_warning", "family"):          1.0,
    ("severe_warning", "default_general"): 1.0,

    # --- aqi_health -------------------------------------------------------
    # Most relevant to health (respiratory) › default_general › fitness › family
    ("aqi_health", "health"):          0.9,
    ("aqi_health", "fitness"):         0.5,
    ("aqi_health", "family"):          0.4,
    ("aqi_health", "default_general"): 0.6,

    # --- uv_sun_exposure --------------------------------------------------
    # Most relevant to fitness (outdoor activity) › health › default_general › family
    ("uv_sun_exposure", "health"):          0.6,
    ("uv_sun_exposure", "fitness"):         0.9,
    ("uv_sun_exposure", "family"):          0.3,
    ("uv_sun_exposure", "default_general"): 0.4,

    # --- activity_window --------------------------------------------------
    # Primarily fitness; others get a low-but-non-zero weight per §0.3 resolution.
    ("activity_window", "health"):          0.3,
    ("activity_window", "fitness"):         0.95,
    ("activity_window", "family"):          0.25,
    ("activity_window", "default_general"): 0.3,

    # --- rain_commute -----------------------------------------------------
    # Family (school run, commute importance) › fitness (affects outdoor plans) › general
    ("rain_commute", "health"):          0.3,
    ("rain_commute", "fitness"):         0.6,
    ("rain_commute", "family"):          0.95,
    ("rain_commute", "commuter"):        0.95,
    ("rain_commute", "default_general"): 0.4,

    # --- sunrise_sunset ---------------------------------------------------
    # Informational; fitness cares most, everyone else a little.
    ("sunrise_sunset", "health"):          0.3,
    ("sunrise_sunset", "fitness"):         0.5,
    ("sunrise_sunset", "family"):          0.3,
    ("sunrise_sunset", "default_general"): 0.3,

    # --- general_conditions -----------------------------------------------
    # The universal fallback/cold-start card; default_general weighted highest.
    ("general_conditions", "health"):          0.5,
    ("general_conditions", "fitness"):         0.5,
    ("general_conditions", "family"):          0.5,
    ("general_conditions", "default_general"): 0.7,

    # --- pollen_illustrative ----------------------------------------------
    # Health persona only (gated via opt-in flag in _card_applies).
    # Other persons receive 0.0 — they will never see this card because
    # _card_applies returns False for them before scoring starts.
    ("pollen_illustrative", "health"):          0.4,
    ("pollen_illustrative", "fitness"):         0.0,
    ("pollen_illustrative", "family"):          0.0,
    ("pollen_illustrative", "default_general"): 0.0,

    # --- visibility_commute -----------------------------------------------
    ("visibility_commute", "commuter"):        0.95,
    ("visibility_commute", "default_general"): 0.3,

    # --- Phase D Compound Personas ----------------------------------------
    ("compound_heat_aqi_danger", "health"):    1.0,
    ("compound_heat_aqi_danger", "fitness"):   1.0,
    ("compound_heat_aqi_danger", "default_general"): 0.8,

    ("compound_driving_hazard", "commuter"):   1.0,
    ("compound_driving_hazard", "family"):     1.0,
    ("compound_driving_hazard", "default_general"): 0.8,

    # --- destination_alert ------------------------------------------------
    # Strictly limits destination relevance only to Travelers to avoid overwhelming generic users
    ("destination_alert", "traveler"):         0.95,
    ("destination_alert", "default_general"):  0.0,

    # --- Phase C Specialized Personas -------------------------------------
    ("agriculture_advisory", "agriculture"):   0.95,
    ("agriculture_advisory", "default_general"): 0.0,
    
    ("marine_conditions_alert", "beachgoer"):  0.95,
    ("marine_conditions_alert", "default_general"): 0.0,
    
    ("event_outlook", "event_planner"):        0.95,
    ("event_outlook", "default_general"):      0.0,
}

# --- Cold-start ordering sanity check -------------------------------------
# With baseline urgency=1.0 and confidence=1.0, default_general weights give:
#   severe_warning P0 override (not scored)
#   general_conditions  0.70 → 0.70
#   aqi_health          0.60 → 0.60
#   uv_sun_exposure     0.40 → 0.40
#   rain_commute        0.40 → 0.40  (tie — resolved by CARD_DEFINITION_ORDER)
#   activity_window     0.30 → 0.30
#   sunrise_sunset      0.30 → 0.30  (tie)
# This matches 15_...md §1 cold-start ordering check.


# ---------------------------------------------------------------------------
# confidence_factor
# ---------------------------------------------------------------------------

CONFIDENCE_BY_SOURCE: dict[str, float] = {
    "live":        1.0,
    "cached":      0.9,
    "simulated":   0.7,
    "stale":       0.3,
    "unavailable": 0.0,
    "fixture":     1.0,
}


def confidence_factor(signal: SignalValue) -> float:
    """
    Convert a signal's source tag into a 0–1 confidence multiplier.

    Live data is fully trusted; stale/simulated data naturally sinks in
    ranking rather than being hidden or causing a crash.

    Spec: 03_...md §4, 06_...md §4 (confidence table).
    """
    return CONFIDENCE_BY_SOURCE.get(signal.source, 0.0)


# ---------------------------------------------------------------------------
# urgency_multiplier — purely environmental, never persona-dependent
# ---------------------------------------------------------------------------

def _aqi_value(cf: ContextFrame) -> int | None:
    """Extract the integer AQI from the composite SignalValue dict."""
    v = cf.aqi.value
    if v is None:
        return None
    if isinstance(v, dict):
        return v.get("aqi")
    # Fallback: if stored as a bare number (should not happen per contract)
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def urgency_multiplier(card_id: str, cf: ContextFrame) -> float:
    """
    Compute how urgent a card is based purely on environmental signal values.

    This function must NEVER read cf.personas or cf.health_flags — that
    independence is what prevents personalization from degenerating into
    a simple persona lookup table (03_...md §4, Risk R5 mitigation).

    Returns a multiplier ≥ 1.0.  Higher = more urgent.

    Spec: 14_implementation_blueprint.md §3, 15_...md §1 (all 8 branches).
    """

    if card_id == "severe_warning":
        # Bypasses scoring entirely via P0 hard-rule (03_...md §5).
        # Returning 1.0 ensures score_components is always populated.
        return 1.0

    if card_id == "aqi_health":
        v = _aqi_value(cf)
        if v is None:
            return 1.0
        if v >= 300:
            return 2.5   # Severe / Hazardous
        if v >= 150:
            return 1.8   # Poor
        if v >= 100:
            return 1.3   # Moderate
        return 1.0       # Satisfactory / Good

    if card_id == "uv_sun_exposure":
        v = cf.uv.value
        if v is None:
            return 1.0
        v = float(v)
        if v >= 11:
            return 2.2   # Extreme
        if v >= 8:
            return 1.8   # Very High
        if v >= 6:
            return 1.2   # High
        return 1.0       # Moderate / Low

    if card_id == "activity_window":
        # Composite urgency: any bad condition affecting outdoor activity pushes UP.
        aqi_v = _aqi_value(cf)
        uv_v  = cf.uv.value
        temp_v = cf.temp_c.value
        wind_v = cf.wind_kmh.value

        bad = (
            (aqi_v  is not None and aqi_v  >= 150)
            or (uv_v   is not None and float(uv_v)   >= 8)
            or (temp_v is not None and (float(temp_v) >= 38 or float(temp_v) <= 5))
            or (wind_v is not None and float(wind_v) >= 40)
        )
        moderate = (
            (aqi_v  is not None and aqi_v  >= 100)
            or (uv_v   is not None and float(uv_v)   >= 6)
        )
        if bad:
            return 1.8
        if moderate:
            return 1.3
        return 1.0

    if card_id == "rain_commute":
        p = cf.precip_prob_pct.value
        if p is None:
            return 1.0
        p = float(p)
        # Commute window raises urgency because timing matters for shelter / transit decisions.
        #
        # IMPLEMENTATION CALIBRATION (2026-08-26, Milestone 1 Audit F-01):
        #   The original value here was 2.0 (a design-quality placeholder per 15_...md §1).
        #   The audit demonstrated that 0.95 (family weight) × 2.0 × 0.7 (simulated conf.) = 1.33,
        #   which is below the P1 threshold of 1.5 defined in 03_...md §5.
        #   This contradicted 03_...md §88 which requires Family + commute + rain → P1.
        #   Resolution: raised to 2.35.  Chosen value: 0.95 × 2.35 × 0.7 = 1.56275 ≥ 1.5 → P1.
        #   Persona weights, confidence levels, and P1_THRESHOLD are all UNCHANGED.
        #   This is an implementation-level calibration of a placeholder, not a spec change.
        #   See docs/IMPL_CALIBRATION_DECISIONS.md for full audit rationale.
        if cf.is_commute_window and p >= 60:
            return 2.35  # calibrated from 2.0 — see comment above
        if cf.is_commute_window and p >= 30:
            return 1.5
        if p >= 60:
            return 1.3   # High precip even outside commute hours
        return 1.0

    if card_id == "visibility_commute":
        v = cf.visibility_km.value
        if v is None:
            return 1.0
        v = float(v)
        if cf.is_commute_window and v <= 1.5:
            return 2.5   # P1 boundary (0.95 * 2.5 * 0.7 = 1.66)
        if v <= 1.5:
            return 1.6   # High urgency anytime
        if cf.is_commute_window and v <= 5.0:
            return 1.4   # Moderate urgency
        return 1.0

    elif card_id == "destination_alert":
        if not cf.destinations:
            return 1.0
        warn_cnt = sum(len(d.warnings) for d in cf.destinations if d.warnings)
        if warn_cnt >= 2:
            return 1.8   # P1 boundary (0.95 * 1.8 * 1.0 = 1.71)
        if warn_cnt == 1:
            return 1.4   # P2 boundary
        return 1.0

    elif card_id == "agriculture_advisory":
        u = 1.0
        if getattr(cf, "frost_warning_active", False):
            u *= 2.0
        soil = getattr(cf, "soil_moisture_pct", None)
        if soil and soil.value is not None:
            if float(soil.value) < 30.0:  # Arbitrary threshold for dry soil
                u *= 1.5
        return u

    elif card_id == "marine_conditions_alert":
        u = 1.0
        wave = getattr(cf, "wave_height_m", None)
        if wave and wave.value is not None:
            if float(wave.value) > 1.5:
                u *= 2.0
        return u
        
    elif card_id == "event_outlook":
        u = 1.0
        comfort = getattr(cf, "comfort_index", None)
        if comfort is not None and comfort > 27.0: # Warm discomfort
            u *= 1.2
        return u

    if card_id == "sunrise_sunset":
        # Informational only in the MVP; urgency never changes independently.
        return 1.0

    if card_id == "general_conditions":
        v = cf.temp_c.value
        if v is not None and (float(v) >= 40 or float(v) <= 5):
            return 1.3   # Heatwave- or coldwave-adjacent conditions
        return 1.0

    if card_id == "pollen_illustrative":
        # Simulated/illustrative only (13_...md); never independently alerted.
        return 1.0

    if card_id == "compound_heat_aqi_danger":
        return 3.0
        
    if card_id == "compound_driving_hazard":
        return 3.0

    # Fallback for any unknown card_id (should never occur in prod).
    return 1.0


# ---------------------------------------------------------------------------
# score — the composite scoring function
# ---------------------------------------------------------------------------

def _resolve_persona_weight(card_id: str, persona: str, health_flags: list[str]) -> tuple[float, bool]:
    # If explicitly defined for the requested persona, use it.
    if (card_id, persona) in PERSONA_WEIGHT:
        base_pw = PERSONA_WEIGHT[(card_id, persona)]
    else:
        # Fallback to the default general weights properly instead of a flat 0.2.
        base_pw = PERSONA_WEIGHT.get((card_id, "default_general"), 0.2)
        
    modifier = 0.0
    flags_applied = False
    
    # Phase A: Map health flags directly to persona weight bumps.
    if card_id == "aqi_health" and "respiratory_sensitive" in health_flags:
        modifier = 0.1
        flags_applied = True
    elif card_id == "uv_sun_exposure" and "heat_sensitive" in health_flags:
        modifier = 0.1
        flags_applied = True
        
    final_pw = min(1.0, base_pw + modifier)
    return final_pw, flags_applied

def score(
    card_id: str,
    persona: str,
    cf: ContextFrame,
    primary_signal: SignalValue,
) -> tuple[float, dict]:
    """
    Compute the card's relevance score and return it alongside its components.

    Returns
    -------
    (score_value, score_components_dict)

    score_components_dict keys: "persona_weight", "urgency_multiplier",
                                "confidence_factor".
    Preserved so the explanation engine and tests can inspect each factor.

    Spec: 03_...md §4, 14_...md §3, 15_...md §1.
    """
    pw, flags_applied = _resolve_persona_weight(card_id, persona, cf.health_flags)
    um   = urgency_multiplier(card_id, cf)
    cfac = confidence_factor(primary_signal)
    raw  = pw * um * cfac
    return raw, {
        "persona_weight":       pw,
        "urgency_multiplier":   um,
        "confidence_factor":    cfac,
        "health_flags_applied": flags_applied,
    }

```

## SOURCE FILE: engine/priority.py

### Exact Current Source

```python
"""
engine/priority.py

Converts composite scores into documented priority levels (P0–P3)
and determines whether a card should trigger an alert treatment.

Source of truth:
  - 03_personalization_logic_and_decision_matrix.md §5, §6
  - 14_implementation_blueprint.md §3 (priority.py block)
"""
from __future__ import annotations

from .cards import CARD_DEFINITIONS
from .models import ContextFrame


# ---------------------------------------------------------------------------
# Priority classification
# ---------------------------------------------------------------------------

# Score thresholds from 03_...md §5.
P1_THRESHOLD = 1.5   # score ≥ 1.5 → P1 (High)
P2_THRESHOLD = 0.7   # score ≥ 0.7 → P2 (Normal);  < 0.7 → P3 (Low)

# NOTE: simulated data has confidence_factor = 0.7 (03_...md §4).  The raw
# score for a max-urgency simulated card can be <0.7 (e.g., stale AQI Poor:
# 0.9 × 1.8 × 0.3 = 0.486 → P3).  Per §6, such cards may still be is_alert;
# the apply_alert_priority_floor() function below ensures they are never
# completely collapsed/hidden (P3) while remaining an active alert.


def classify_priority(
    card_id: str,
    score_value: float,
    cf: ContextFrame,
) -> str:
    """
    Map a numeric score to a priority level string.

    P0 is a hard rule for severe_warning when warnings are present — it
    bypasses scoring entirely (03_...md §5).
    P1/P2/P3 derive from documented score thresholds.

    Returns "P0" | "P1" | "P2" | "P3".
    """
    # Hard rule: P0 always overrides if this is a warning card and warnings exist.
    if card_id == "severe_warning" and cf.warnings:
        return "P0"

    if score_value >= P1_THRESHOLD:
        return "P1"
    if score_value >= P2_THRESHOLD:
        return "P2"
    return "P3"


# ---------------------------------------------------------------------------
# Alert thresholds — urgency values that trigger alert treatment
# ---------------------------------------------------------------------------

# A card becomes an alert if it is P0, or if its urgency_multiplier crosses
# a documented hard threshold AND it is alertable (per CARD_DEFINITIONS).
# Thresholds match the urgency_multiplier bands in scoring.py.
# Source: 03_...md §6.

_HARD_ALERT_URGENCY: dict[str, float] = {
    "aqi_health":       1.8,    # AQI ≥ 150 (Poor band)
    "uv_sun_exposure":  1.8,    # UV ≥ 8 (Very High band)
    "activity_window":  1.8,    # Composite bad conditions band
    "rain_commute":     2.0,    # Commute window + ≥60% precip
}


def is_alert(
    card_id: str,
    priority: str,
    urgency: float,
    cf: ContextFrame,
) -> bool:
    """
    Decide whether this card deserves alert-level visual treatment.

    Per 03_...md §6:
    - P0 cards are always alerts.
    - Other cards become alerts if their urgency_multiplier crosses a hard
      threshold AND the card definition marks it as alertable.
    - Low-confidence alerts are shown WITH a disclosure badge — they are
      never suppressed (03_...md §6, last sentence).

    Returns True if the card should receive alert treatment.
    """
    if priority == "P0":
        return True

    alertable = CARD_DEFINITIONS.get(card_id, {}).get("alertable", True)
    if not alertable:
        return False

    threshold = _HARD_ALERT_URGENCY.get(card_id)
    if threshold is None:
        return False

    return urgency >= threshold


# ---------------------------------------------------------------------------
# Alert priority floor — F-02 resolution, Milestone 1 Audit
# ---------------------------------------------------------------------------

def apply_alert_priority_floor(priority: str, alert: bool) -> str:
    """
    Ensure that a card which is_alert=True is never ranked P3.

    03_...md §6 requires that alerts are "never hidden". §5 defines P3 as
    "shown lower on the page or collapsed". A P3-alert card violates both
    requirements simultaneously. This function applies the minimal floor:
    if a card is an alert but scored into P3 (due to low confidence_factor),
    elevate it to P2 so it is always visible with a degraded-data badge.

    IMPORTANT:
    - This changes only the DISPLAY priority tier, NOT the underlying score.
    - The score in RankedCard.score is always the raw formula result.
    - score_components['confidence_factor'] remains unchanged for traceability.
    - Only P3 → P2: do NOT promote alerts from P2 to P1.
    - Non-alert P3 cards remain P3.

    Call this AFTER both classify_priority() and is_alert() have been computed.
    """
    if alert and priority == "P3":
        return "P2"
    return priority

```

## SOURCE FILE: engine/compound.py

### Exact Current Source

```python
"""
engine/compound.py

Pure deterministic evaluation logic for Phase D compound insights.
These functions inspect ContextFrame directly and return boolean applicability natively.
They do not rank, explain, or interact with external services.
"""
from __future__ import annotations

from .models import ContextFrame


def is_compound_heat_aqi_danger(cf: ContextFrame) -> bool:
    """
    Evaluates if extreme heat and dangerous air quality occur simultaneously.
    Trigger: Temp >= 38 C AND AQI >= 150.
    Gracefully returns False if either signal is unavailable.
    """
    if cf.temp_c.source == "unavailable" or cf.aqi.source == "unavailable":
        return False
    
    if cf.temp_c.value is None or cf.aqi.value is None:
        return False
        
    try:
        temp = float(cf.temp_c.value)
        # cf.aqi.value is a dict: {"aqi": int, "dominant": str}
        aqi = int(cf.aqi.value.get("aqi", 0)) if isinstance(cf.aqi.value, dict) else int(cf.aqi.value)
        
        return temp >= 38.0 and aqi >= 150
    except (ValueError, TypeError, AttributeError):
        return False


def is_compound_driving_hazard(cf: ContextFrame) -> bool:
    """
    Evaluates if high precipitation and low visibility occur simultaneously.
    Trigger: Precip Probability >= 60% AND Visibility <= 1.0 km.
    Gracefully returns False if either signal is unavailable.
    """
    if cf.precip_prob_pct.source == "unavailable" or cf.visibility_km.source == "unavailable":
        return False
        
    if cf.precip_prob_pct.value is None or cf.visibility_km.value is None:
        return False
        
    try:
        precip = float(cf.precip_prob_pct.value)
        vis = float(cf.visibility_km.value)
        
        return precip >= 60.0 and vis <= 1.0
    except (ValueError, TypeError):
        return False

```

## SOURCE FILE: engine/conflict.py

### Exact Current Source

```python
"""
engine/conflict.py

Tie-break resolver for cards that land in the same priority bucket.

Resolution order (03_personalization_logic_and_decision_matrix.md §8):
  1. P0 always wins outright (separated from ranked list entirely in engine.py).
  2. Higher urgency_multiplier wins.
  3. If still tied, card tied to a DECLARED (not default) persona wins.
  4. If still tied, stable order by CARD_DEFINITION_ORDER.

The result is deterministic for any given input (required by 10_...md §1
"same input → same output, run twice").
"""
from __future__ import annotations

from .cards import CARD_DEFINITION_ORDER
from .models import RankedCard


_PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


def resolve_ties(
    cards: list[RankedCard],
    declared_persona_card_ids: set[str],
) -> list[RankedCard]:
    """
    Sort RankedCards by effective priority, breaking ties deterministically.

    Parameters
    ----------
    cards                    : list to sort (not mutated; returns new list).
    declared_persona_card_ids: card IDs that are tied to at least one of the
                               user's explicitly declared persona(s) — used for
                               tie-break rule 3.  Empty for cold-start users.

    Returns a new sorted list, highest priority first.
    """
    def sort_key(c: RankedCard) -> tuple:
        # Rule 1: priority level (P0 < P1 < P2 < P3 numerically).
        priority_rank = _PRIORITY_ORDER.get(c.priority, 99)

        # Rule 2: higher final calculated score wins (negate for ascending sort).
        raw_score = -c.score

        # Rule 3: declared-persona card beats a default one (0 < 1).
        not_declared = 0 if c.card_id in declared_persona_card_ids else 1

        # Rule 4: higher urgency_multiplier wins if raw score is tied.
        urgency = -c.score_components.get("urgency_multiplier", 1.0)

        # Rule 5: stable ordering from CARD_DEFINITION_ORDER.
        try:
            definition_pos = CARD_DEFINITION_ORDER.index(c.card_id)
        except ValueError:
            definition_pos = len(CARD_DEFINITION_ORDER)

        return (priority_rank, raw_score, not_declared, urgency, definition_pos)

    return sorted(cards, key=sort_key)

```

## SOURCE FILE: engine/derived.py

### Exact Current Source

```python
"""
engine/derived.py

Mathematical computations for derived environmental signals.
Ensures deterministic reasoning inside the Phase C domains without live ML/LLMs.
"""

def calculate_comfort_index(temp_c: float | int | None, humidity_pct: float | int | None) -> float | None:
    """
    Computes a simplified continuous comfort index based on Thom's Discomfort Index.
    Lower index = more comfortable (typically).
    
    Formula: DI = T - (0.55 - 0.0055 * RH) * (T - 14.5)
    If temp or humidity is unavailable, returns None.
    """
    if temp_c is None or humidity_pct is None:
        return None
        
    t = float(temp_c)
    h = float(humidity_pct)
    
    di = t - (0.55 - 0.0055 * h) * (t - 14.5)
    return round(di, 2)

def is_frost_warning(temp_c: float | int | None) -> bool:
    """
    Determines if frost conditions are actively viable (< 2.0C).
    Returns False if temp_c is unavailable.
    """
    if temp_c is None:
        return False
        
    return float(temp_c) < 2.0

```

## SOURCE FILE: engine/engine.py

### Exact Current Source

```python
"""
engine/engine.py

Public entrypoint for the Mausam Personalized Homepage engine.

The single public function is `rank(cf: ContextFrame) -> EngineOutput`.
This is a PURE function: same input always produces the same output.
There are NO network calls, NO database calls, NO filesystem reads here.

Source of truth:
  - 14_implementation_blueprint.md §3 (engine.py + all 5 helper names)
  - 15_implementation_completion_and_handoff.md §3 (all 5 helpers implemented)
  - 03_personalization_logic_and_decision_matrix.md §4–§13
  - 06_system_architecture.md §2 (module boundary rules)
"""
from __future__ import annotations

from .cards import CARD_DEFINITIONS, CARD_DEFINITION_ORDER
from .compound import is_compound_driving_hazard, is_compound_heat_aqi_danger
from .conflict import resolve_ties
from .explain import build_explanation
from .models import (
    ContextFrame,
    EngineOutput,
    RankedCard,
    SignalValue,
    validate_context_frame,
)
from .priority import apply_alert_priority_floor, classify_priority, is_alert
from .scoring import PERSONA_WEIGHT, score

# All persona tags the engine knows about.
_PERSONAS_ALL: frozenset[str] = frozenset(["health", "fitness", "family", "default_general"])


# ---------------------------------------------------------------------------
# Helper 1: _card_applies — missing-data + opt-in gating
# ---------------------------------------------------------------------------

def _card_applies(card_id: str, cf: ContextFrame) -> bool:
    """
    Determine whether a card is a candidate for this context.

    Returns False when:
    - the card's required signal is "unavailable" AND no safe default exists.
    - the card has special opt-in gating (pollen_illustrative).

    Source: 14_...md §3 (_card_applies) + 15_...md §3, 03_...md §10.
    """
    if card_id == "pollen_illustrative":
        # Gated: must have health persona + pollen_interest flag + pollen data.
        return (
            "health" in cf.personas
            and "pollen_interest" in cf.health_flags
            and cf.pollen is not None
            and cf.pollen.source != "unavailable"
        )

    if card_id == "severe_warning":
        return len(cf.warnings) > 0

    if card_id == "aqi_health":
        return cf.aqi.source != "unavailable"

    if card_id == "uv_sun_exposure":
        return cf.uv.source != "unavailable"

    if card_id == "rain_commute":
        return cf.precip_prob_pct.source != "unavailable"

    if card_id == "sunrise_sunset":
        # Locally computed; always available (08_...md §2).
        return True

    if card_id == "general_conditions":
        # Safe fallback — omit only if ALL of its inputs are unavailable.
        return not (
            cf.temp_c.source == "unavailable"
            and cf.humidity_pct.source == "unavailable"
            and cf.wind_kmh.source == "unavailable"
        )

    if card_id == "activity_window":
        # Composite — present if at least one input signal is available.
        return any(
            s.source != "unavailable"
            for s in [cf.temp_c, cf.wind_kmh, cf.aqi, cf.uv]
        )

    if card_id == "visibility_commute":
        return cf.visibility_km.source != "unavailable"

    if card_id == "destination_alert":
        return len(cf.destinations) > 0 and any(len(d.warnings) > 0 for d in cf.destinations)

    # Phase D Compounds:
    if card_id == "compound_heat_aqi_danger":
        return is_compound_heat_aqi_danger(cf)
    if card_id == "compound_driving_hazard":
        return is_compound_driving_hazard(cf)

    # Phase C Cards:
    if card_id == "agriculture_advisory":
        return cf.soil_moisture_pct.source != "unavailable" or getattr(cf, "frost_warning_active", False)

    if card_id == "marine_conditions_alert":
        return cf.wave_height_m.source != "unavailable"

    if card_id == "event_outlook":
        return getattr(cf, "extended_forecast", []) != [] or getattr(cf, "comfort_index", None) is not None

    return True   # Unknown card: allow (defensive default).


# ---------------------------------------------------------------------------
# Helper 2: _primary_signal_for — confidence gateway per card
# ---------------------------------------------------------------------------

def _primary_signal_for(card_id: str, cf: ContextFrame) -> SignalValue:
    """
    Return the SignalValue whose confidence gates this card's score.

    For composite cards (activity_window, general_conditions) the weakest
    available signal is used so that partial data degradation is visible in
    the score, not hidden.

    Source: 15_...md §3 (_primary_signal_for).
    """
    if card_id == "aqi_health":
        return cf.aqi

    if card_id == "uv_sun_exposure":
        return cf.uv

    if card_id == "rain_commute":
        return cf.precip_prob_pct

    if card_id == "pollen_illustrative":
        # cf.pollen is checked for not-None in _card_applies before reaching here.
        return cf.pollen  # type: ignore[return-value]

    if card_id == "sunrise_sunset":
        # Always live (locally computed).
        return SignalValue(
            value=f"{cf.sunrise}/{cf.sunset}",
            source="live",
            freshness_min=0,
            confidence=1.0,
        )

    if card_id == "severe_warning":
        # Warnings are simulated in the MVP (13_...md). Confidence is always
        # treated as 1.0 for P0 override cards — alerts are never suppressed by
        # low confidence (03_...md §6), though the source badge still shows.
        return SignalValue(
            value=cf.warnings,
            source="simulated",
            freshness_min=0,
            confidence=1.0,
        )

    if card_id in ("activity_window", "general_conditions"):
        if card_id == "activity_window":
            group = [cf.temp_c, cf.wind_kmh, cf.aqi, cf.uv]
        else:
            group = [cf.temp_c, cf.humidity_pct, cf.wind_kmh]
        valid = [s for s in group if s.source != "unavailable"]
        if valid:
            # Weakest confidence in the group drives the card's overall confidence.
            return min(valid, key=lambda s: s.confidence)
        return group[0]   # All unavailable — return temp_c (engine will skip anyway)

    if card_id == "visibility_commute":
        return cf.visibility_km

    if card_id == "compound_heat_aqi_danger":
        return min((cf.temp_c, cf.aqi), key=lambda s: s.confidence)

    if card_id == "compound_driving_hazard":
        return min((cf.precip_prob_pct, cf.visibility_km), key=lambda s: s.confidence)

    if card_id == "destination_alert":
        return SignalValue(
            value=cf.destinations,
            source="simulated",
            freshness_min=0,
            confidence=1.0,
        )

    if card_id == "agriculture_advisory":
        return cf.soil_moisture_pct

    if card_id == "marine_conditions_alert":
        return cf.wave_height_m
        
    if card_id == "event_outlook":
        if getattr(cf, "extended_forecast", []):
            ext = cf.extended_forecast[0]
            return SignalValue(value=None, source=ext.source, confidence=ext.confidence, freshness_min=0)
        valid = [s for s in (cf.temp_c, cf.humidity_pct) if s.source != "unavailable"]
        if valid:
            return min(valid, key=lambda s: s.confidence)
        return SignalValue(value=None, source="unavailable", confidence=0.0, freshness_min=0)

    # Fallback to temperature as a safe default.
    return cf.temp_c


# ---------------------------------------------------------------------------
# Helper 3: _signal_refs_for — build NFR-1 traceable evidence list
# ---------------------------------------------------------------------------

def _signal_refs_for(card_id: str, cf: ContextFrame) -> list[dict]:
    """
    Build the list of {signal, value, source} dicts that the explanation for
    this card is ALLOWED to reference.

    This list is the checkable evidence behind NFR-1: every number mentioned
    in explanation_text must appear here, and every value here comes directly
    from the ContextFrame — nothing invented.

    Source: 15_...md §3 (_signal_refs_for), 07_...md §5 invariant.
    """
    def _ref(name: str, sig: SignalValue, extract=None):
        val = sig.value
        if extract is not None:
            val = extract(val)
        return {"signal": name, "value": val, "source": sig.source}

    def _aqi_val(v):
        if isinstance(v, dict):
            return v.get("aqi")
        return v

    if card_id == "aqi_health":
        return [_ref("aqi", cf.aqi, _aqi_val)]

    if card_id == "uv_sun_exposure":
        return [_ref("uv", cf.uv)]

    if card_id == "activity_window":
        return [
            _ref("temp_c",   cf.temp_c),
            _ref("wind_kmh", cf.wind_kmh),
            _ref("aqi",      cf.aqi, _aqi_val),
            _ref("uv",       cf.uv),
        ]

    if card_id == "rain_commute":
        return [_ref("precip_prob_pct", cf.precip_prob_pct)]

    if card_id == "sunrise_sunset":
        return [
            {"signal": "sunrise", "value": cf.sunrise, "source": "live"},
            {"signal": "sunset",  "value": cf.sunset,  "source": "live"},
        ]

    if card_id == "general_conditions":
        return [
            _ref("temp_c",       cf.temp_c),
            _ref("humidity_pct", cf.humidity_pct),
            _ref("wind_kmh",     cf.wind_kmh),
        ]

    if card_id == "pollen_illustrative":
        return [_ref("pollen", cf.pollen)]  # type: ignore[arg-type]

    if card_id == "severe_warning":
        return [
            {"signal": "warning", "value": w, "source": "simulated"}
            for w in cf.warnings
        ]

    if card_id == "visibility_commute":
        return [_ref("visibility_km", cf.visibility_km)]

    if card_id == "compound_heat_aqi_danger":
        return [
            _ref("temp_c", cf.temp_c),
            _ref("aqi", cf.aqi, _aqi_val)
        ]

    if card_id == "compound_driving_hazard":
        return [
            _ref("precip_prob_pct", cf.precip_prob_pct),
            _ref("visibility_km", cf.visibility_km)
        ]

    if card_id == "destination_alert":
        return [
            {"signal": "warnings", "value": d.warnings, "source": "simulated"}
            for d in cf.destinations if getattr(d, "warnings", False)
        ]

    if card_id == "agriculture_advisory":
        return [_ref("soil_moisture_pct", cf.soil_moisture_pct)]

    if card_id == "marine_conditions_alert":
        return [
            _ref("wave_height_m", cf.wave_height_m),
            {"signal": "tide_status", "value": cf.tide_status, "source": cf.wave_height_m.source}
        ]

    if card_id == "event_outlook":
        return [{"signal": "comfort_index", "value": getattr(cf, "comfort_index", None), "source": "computed"}]

    return []


# ---------------------------------------------------------------------------
# Helper 4: _best_persona_for_card — multi-persona support
# ---------------------------------------------------------------------------

def _best_persona_for_card(card_id: str, personas: list[str]) -> str:
    """
    When the user has declared multiple personas (09_...md §1 S4 allows this),
    use whichever gives this specific card the HIGHEST weight.

    A health+fitness parent should see the AQI card at the health weight (0.9),
    not diluted by an average.

    Source: 15_...md §3 (_best_persona_for_card).
    """
    candidates = personas if personas else ["default_general"]
    return max(candidates, key=lambda p: PERSONA_WEIGHT.get((card_id, p), 0.2))


# ---------------------------------------------------------------------------
# Helper 5: _declared_ids — cards tied to the user's declared persona(s)
# ---------------------------------------------------------------------------

def _declared_ids(cf: ContextFrame) -> set[str]:
    """
    Return the set of card IDs that are directly tied to at least one of the
    user's explicitly declared (non-default) persona(s).

    Used only for conflict.py tie-break rule 3.
    Always empty for cold-start users (no declared profile).

    Source: 15_...md §3 (_declared_ids).
    """
    if not cf.has_declared_profile:
        return set()

    declared: set[str] = set()
    for card_id, definition in CARD_DEFINITIONS.items():
        relevant = definition.get("personas", [])
        if "*" in relevant:
            continue   # Universal card; not a distinguishing signal for tie-breaking.
        if any(p in relevant for p in cf.personas):
            declared.add(card_id)
    return declared


# ---------------------------------------------------------------------------
# Public API: rank()
# ---------------------------------------------------------------------------

def rank(cf: ContextFrame) -> EngineOutput:
    """
    The single public entrypoint of the personalization engine.

    Accepts a ContextFrame and returns a fully ranked EngineOutput.
    This is a PURE FUNCTION — no I/O, no side effects, deterministic.

    Algorithm:
    1. Validate the ContextFrame (raises ValueError on malformed input).
    2. For each card in CARD_DEFINITIONS:
       a. Check _card_applies (missing-data guard + opt-in gate).
       b. Select the best persona to score this card for.
       c. Compute score = persona_weight × urgency_multiplier × confidence_factor.
       d. Classify priority (P0 hard-rule overrides scoring).
       e. Determine alert status.
       f. Apply alert priority floor: if is_alert and priority==P3, raise to P2
          (03_...md §6 "never hidden"; see CAL-02 in docs/IMPL_CALIBRATION_DECISIONS.md).
       g. Build signal_refs and explanation_text.
    3. Resolve ties deterministically.
    4. Separate P0 override cards from the ranked list.
    5. Return EngineOutput.

    Raises
    ------
    ValueError
        If validate_context_frame() returns errors (malformed ContextFrame,
        not degraded data — 07_...md §4 distinguishes these explicitly).
    """
    errors = validate_context_frame(cf)
    if errors:
        raise ValueError(f"Invalid ContextFrame: {errors}")

    all_cards: list[RankedCard] = []

    for card_id in CARD_DEFINITIONS:
        # --- Gate check -------------------------------------------------------
        if not _card_applies(card_id, cf):
            continue

        # --- Scoring ----------------------------------------------------------
        best_persona   = _best_persona_for_card(card_id, cf.personas)
        primary_signal = _primary_signal_for(card_id, cf)
        score_val, components = score(card_id, best_persona, cf, primary_signal)

        # --- Priority + alert -------------------------------------------------
        priority  = classify_priority(card_id, score_val, cf)
        alert     = is_alert(card_id, priority, components["urgency_multiplier"], cf)
        # Apply F-02 alert visibility floor: never collapse an active alert to P3.
        # The raw score is preserved in score_val / components for full traceability.
        priority  = apply_alert_priority_floor(priority, alert)

        # --- Explanation tracing ----------------------------------------------
        refs        = _signal_refs_for(card_id, cf)
        explanation = build_explanation(card_id, priority, components, refs, cf)

        all_cards.append(RankedCard(
            card_id=card_id,
            priority=priority,
            is_alert=alert,
            score=round(score_val, 4),
            score_components=components,
            explanation_text=explanation,
            signal_refs=refs,
        ))

    # --- Tie-break sort -------------------------------------------------------
    sorted_cards = resolve_ties(all_cards, declared_persona_card_ids=_declared_ids(cf))

    # --- Separate P0 from ranked list ----------------------------------------
    override_warnings = [c for c in sorted_cards if c.priority == "P0"]
    ranked_cards       = [c for c in sorted_cards if c.priority != "P0"]

    # --- Targeted Redundancy Suppression (Phase D) ---------------------------
    # Executes after P0 splitting ensures severe_warnings are NEVER suppressed.
    suppress = set()
    active_ids = {c.card_id for c in ranked_cards}
    
    if "compound_heat_aqi_danger" in active_ids:
        suppress.update(["aqi_health", "general_conditions"])
    if "compound_driving_hazard" in active_ids:
        suppress.update(["visibility_commute", "rain_commute"])
        
    ranked_cards = [c for c in ranked_cards if c.card_id not in suppress]

    return EngineOutput(
        ranked_cards=ranked_cards,
        override_warnings=override_warnings,
    )

```

## SOURCE FILE: engine/explain.py

### Exact Current Source

```python
"""
engine/explain.py

Templated explanation generator for all 8 MVP cards.

Explanations are deterministic, grounded in actual signal_refs and
score_components values — never free-text, never LLM-generated.
This is the structural guarantee of NFR-1 (traceability) from
07_api_and_data_contracts.md §5.

Source of truth:
  - 03_personalization_logic_and_decision_matrix.md §13
  - 14_implementation_blueprint.md §3 (explain.py block)
  - 15_implementation_completion_and_handoff.md §2 (all 8 templates)
"""
from __future__ import annotations

from .models import ContextFrame

# ---------------------------------------------------------------------------
# Templates — one per card, total 8.
# Placeholders are filled with values from signal_refs and score_components;
# no value is ever invented outside those two sources.
# ---------------------------------------------------------------------------

EXPLANATION_TEMPLATES: dict[str, str] = {
    "severe_warning": (
        "{warning_text} — active {severity} warning → always shown first, "
        "regardless of your persona or preferences."
    ),
    "aqi_health": (
        "AQI {aqi_value} ({aqi_band}){persona_clause} — "
        "{urgency}× the normal urgency threshold → shown as {priority_label}."
    ),
    "uv_sun_exposure": (
        "UV index {uv_value} ({uv_band}){persona_clause} — "
        "{urgency}× the normal urgency threshold → shown as {priority_label}."
    ),
    "activity_window": (
        "Conditions: temp {temp_value}°C, wind {wind_value} km/h, "
        "AQI {aqi_value}, UV {uv_value}{persona_clause} → "
        "best outdoor window shifted, shown as {priority_label}."
    ),
    "rain_commute": (
        "{precip_value}% chance of rain{commute_clause} → shown as {priority_label}."
    ),
    "sunrise_sunset": (
        "Sunrise {sunrise_value}, sunset {sunset_value} → shown as {priority_label}."
    ),
    "visibility_commute": (
        "Visibility {visibility_value} km{commute_clause} → "
        "{urgency}× the normal urgency threshold → shown as {priority_label}."
    ),
    "destination_alert": (
        "{warnings_count} active warning(s) at {destinations_count} saved destination(s){delta_clause} → "
        "shown as {priority_label} for travelers."
    ),
    "compound_heat_aqi_danger": (
        "Combining extreme heat ({temp_value}°C) and dangerous air (AQI {aqi_value}) "
        "makes outdoor exposure uniquely hazardous → shown as {priority_label}."
    ),
    "compound_driving_hazard": (
        "High rain probability ({precip_value}%) coupled with dense fog ({visibility_value} km visibility) "
        "dictates extreme caution on roads today natively → shown as {priority_label}."
    ),
    "general_conditions": (
        "Currently {temp_value}°C, {humidity_value}% humidity, "
        "wind {wind_value} km/h{delta_clause} → shown as {priority_label}."
    ),
    "pollen_illustrative": (
        "Pollen level {pollen_value} [simulated for demo — illustrative only] "
        "→ shown as {priority_label}."
    ),
    "agriculture_advisory": (
        "Soil moisture {soil_value}%, frost risk {frost_status} → shown as {priority_label}."
    ),
    "marine_conditions_alert": (
        "Wave height {wave_value}m, tide {tide_value} → shown as {priority_label}."
    ),
    "event_outlook": (
        "Comfort index {comfort_value}, {forecast_horizon} day outlook → shown as {priority_label}."
    ),
}

PRIORITY_LABEL: dict[str, str] = {
    "P0": "an override warning",
    "P1": "a high-priority alert",
    "P2": "a normal-priority item",
    "P3": "a low-priority / background item",
}


# ---------------------------------------------------------------------------
# Band helpers — translate raw numeric values to human-readable bands
# ---------------------------------------------------------------------------

def _aqi_band(value: int | None) -> str:
    if value is None:
        return "unknown"
    if value >= 300:
        return "Severe"
    if value >= 150:
        return "Poor"
    if value >= 100:
        return "Moderate"
    return "Satisfactory"


def _uv_band(value: float | None) -> str:
    if value is None:
        return "unknown"
    v = float(value)
    if v >= 11:
        return "Extreme"
    if v >= 8:
        return "Very High"
    if v >= 6:
        return "High"
    return "Moderate/Low"


def _fmt(value, unit: str = "") -> str:
    """Format a possibly-None value for display in an explanation string."""
    if value is None:
        return "unavailable"
    return f"{value}{unit}"


# ---------------------------------------------------------------------------
# Persona clause builder
# ---------------------------------------------------------------------------

def _persona_clause(cf: ContextFrame, persona_weight: float) -> str:
    """
    Returns a short clause appended to explanations when the user's declared
    persona materially increased this card's relevance.
    Empty string for cold-start or low-weight cases.
    """
    if not cf.has_declared_profile:
        return ""
    if persona_weight >= 0.6:
        return ", and this is particularly relevant to your declared persona"
    return ""


# ---------------------------------------------------------------------------
# Destination Delta logic (Phase D)
# ---------------------------------------------------------------------------

def _build_traveler_delta(cf: ContextFrame) -> str:
    """
    Returns comparative temperature text for travelers explicitly comparing
    origins to destinations safely natively.
    """
    if "traveler" not in cf.personas and not cf.personas == ["default_general"]:
        return ""
        
    if not hasattr(cf, "destinations") or not cf.destinations:
        return ""
        
    dest = cf.destinations[0]
    
    if cf.temp_c.source == "unavailable" or dest.temp_c.source == "unavailable":
        return ""
    
    if cf.temp_c.value is None or getattr(dest.temp_c, "value", None) is None:
        return ""
        
    try:
        origin_t = float(cf.temp_c.value)
        dest_t = float(dest.temp_c.value)
        
        diff = dest_t - origin_t
        if abs(diff) < 1.0:
            return ". Destination temperature is similar to origin."
        
        diff_val = round(abs(diff), 1)
        comparative = "warmer" if diff > 0 else "cooler"
        return f". Destination is {diff_val}°C {comparative} than origin."
    except (ValueError, TypeError):
        return ""

# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------

def build_explanation(
    card_id: str,
    priority: str,
    score_components: dict,
    signal_refs: list[dict],
    cf: ContextFrame,
) -> str:
    """
    Build a deterministic, template-based explanation for one ranked card.

    Parameters
    ----------
    card_id         : one of the 8 documented card IDs.
    priority        : "P0" | "P1" | "P2" | "P3".
    score_components: {"persona_weight", "urgency_multiplier", "confidence_factor"}.
    signal_refs     : [{"signal": str, "value": any, "source": str}, ...].
    cf              : full ContextFrame (used for derived context like commute flag).

    Returns a human-readable string that references only values present in
    signal_refs or score_components — never invents or hallucinates numbers.
    """
    template = EXPLANATION_TEMPLATES.get(card_id)
    if template is None:
        return f"Shown as {PRIORITY_LABEL.get(priority, priority)}."

    priority_label  = PRIORITY_LABEL.get(priority, priority)
    urgency         = round(score_components.get("urgency_multiplier", 1.0), 2)
    persona_weight  = score_components.get("persona_weight", 0.0)
    health_applied  = score_components.get("health_flags_applied", False)
    
    p_clause = _persona_clause(cf, persona_weight)
    if health_applied:
        p_clause += " (priority elevated due to your health profile)"

    # Build a quick lookup from signal_refs for template substitution.
    refs = {r["signal"]: r["value"] for r in signal_refs}

    if card_id == "severe_warning":
        w = cf.warnings[0] if cf.warnings else {}
        return template.format(
            warning_text=w.get("text", "Severe weather warning"),
            severity=w.get("severity", "severe"),
        )

    if card_id == "aqi_health":
        raw_aqi = refs.get("aqi")
        return template.format(
            aqi_value=_fmt(raw_aqi),
            aqi_band=_aqi_band(raw_aqi),
            urgency=urgency,
            persona_clause=p_clause,
            priority_label=priority_label,
        )

    if card_id == "uv_sun_exposure":
        raw_uv = refs.get("uv")
        return template.format(
            uv_value=_fmt(raw_uv),
            uv_band=_uv_band(raw_uv),
            urgency=urgency,
            persona_clause=p_clause,
            priority_label=priority_label,
        )

    if card_id == "activity_window":
        raw_aqi = refs.get("aqi")
        return template.format(
            temp_value=_fmt(refs.get("temp_c")),
            wind_value=_fmt(refs.get("wind_kmh")),
            aqi_value=_fmt(raw_aqi),
            uv_value=_fmt(refs.get("uv")),
            persona_clause=p_clause,
            priority_label=priority_label,
        )

    if card_id == "rain_commute":
        commute_clause = " within your commute window" if cf.is_commute_window else ""
        return template.format(
            precip_value=_fmt(refs.get("precip_prob_pct")),
            commute_clause=commute_clause,
            priority_label=priority_label,
        )

    if card_id == "sunrise_sunset":
        return template.format(
            sunrise_value=refs.get("sunrise", cf.sunrise),
            sunset_value=refs.get("sunset", cf.sunset),
            priority_label=priority_label,
        )

    if card_id == "visibility_commute":
        commute_clause = " within your commute window" if cf.is_commute_window else ""
        return template.format(
            visibility_value=_fmt(refs.get("visibility_km")),
            commute_clause=commute_clause,
            urgency=urgency,
            priority_label=priority_label,
        )

    if card_id == "destination_alert":
        warn_cnt = sum(len(d.warnings) for d in cf.destinations if d.warnings)
        dest_cnt = sum(1 for d in cf.destinations if d.warnings)
        return template.format(
            warnings_count=warn_cnt,
            destinations_count=dest_cnt,
            delta_clause=_build_traveler_delta(cf),
            priority_label=priority_label,
        )

    if card_id == "compound_heat_aqi_danger":
        return template.format(
            temp_value=_fmt(refs.get("temp_c")),
            aqi_value=_fmt(refs.get("aqi")),
            priority_label=priority_label,
        )

    if card_id == "compound_driving_hazard":
        return template.format(
            precip_value=_fmt(refs.get("precip_prob_pct")),
            visibility_value=_fmt(refs.get("visibility_km")),
            priority_label=priority_label,
        )

    if card_id == "general_conditions":
        return template.format(
            temp_value=_fmt(refs.get("temp_c")),
            humidity_value=_fmt(refs.get("humidity_pct")),
            wind_value=_fmt(refs.get("wind_kmh")),
            delta_clause=_build_traveler_delta(cf),
            priority_label=priority_label,
        )

    if card_id == "pollen_illustrative":
        return template.format(
            pollen_value=_fmt(refs.get("pollen")),
            priority_label=priority_label,
        )

    if card_id == "agriculture_advisory":
        return template.format(
            soil_value=_fmt(refs.get("soil_moisture_pct")),
            frost_status="Active" if getattr(cf, "frost_warning_active", False) else "Inactive",
            priority_label=priority_label,
        )

    if card_id == "marine_conditions_alert":
        return template.format(
            wave_value=_fmt(refs.get("wave_height_m")),
            tide_value=_fmt(refs.get("tide_status")).title(),
            priority_label=priority_label,
        )

    if card_id == "event_outlook":
        horizon = len(getattr(cf, "extended_forecast", [])) if getattr(cf, "extended_forecast", []) else "no"
        return template.format(
            comfort_value=_fmt(getattr(cf, "comfort_index", None)),
            forecast_horizon=horizon,
            priority_label=priority_label,
        )

    # Fallback (should never be reached in a correctly configured system).
    return f"Shown as {priority_label}."

```

