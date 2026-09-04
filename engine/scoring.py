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
