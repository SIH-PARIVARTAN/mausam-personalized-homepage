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
#
# PATCH (2026-09-05, GAP-01 resolution):
#   Original table covered only 4 of 11 alertable cards. The following 6 entries
#   were added to ensure every alertable card can reach is_alert=True at an
#   appropriate, code-justified threshold. Thresholds are set at or below the
#   worst-case urgency_multiplier value returned by scoring.py for that card.
#   No urgency bands, persona weights, or scoring formulas were altered.

_HARD_ALERT_URGENCY: dict[str, float] = {
    # --- Original 4 entries (03_...md §6) -----------------------------------
    "aqi_health":               1.8,    # AQI ≥ 150 (Poor band)
    "uv_sun_exposure":          1.8,    # UV ≥ 8 (Very High band)
    "activity_window":          1.8,    # Composite bad conditions band
    "rain_commute":             2.0,    # Commute window + ≥60% precip

    # --- GAP-01 additions (2026-09-05) --------------------------------------
    # compound_heat_aqi_danger / compound_driving_hazard:
    #   scoring.py returns a flat 3.0 whenever the compound condition is true
    #   (Temp ≥ 38°C + AQI ≥ 150, or Precip ≥ 60% + Vis ≤ 1km).
    #   Threshold 2.5 is safely below 3.0, ensuring the compound card always
    #   alerts when its trigger condition is live.
    "compound_heat_aqi_danger": 2.5,
    "compound_driving_hazard":  2.5,

    # visibility_commute:
    #   scoring.py worst band = 2.5 (commute window + vis ≤ 1.5km).
    #   Threshold 2.0 means the card alerts only during the commute-window
    #   worst band (2.5 ≥ 2.0), not the off-peak worst band (1.6 < 2.0).
    "visibility_commute":       2.0,

    # destination_alert:
    #   scoring.py max urgency = 1.8 (≥ 2 destination active warnings).
    #   Threshold 1.8 means multi-warning destination scenarios alert.
    "destination_alert":        1.8,

    # agriculture_advisory:
    #   scoring.py frost_warning_active alone returns 2.0.
    #   Threshold 1.8 ensures the frost-warning path alerts.
    "agriculture_advisory":     1.8,

    # marine_conditions_alert:
    #   scoring.py wave_height_m > 1.5m returns 2.0.
    #   Threshold 1.8 ensures significant wave height scenarios alert.
    "marine_conditions_alert":  1.8,
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
