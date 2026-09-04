"""
engine/tests/test_gap01_alert_regression.py

GAP-01 regression tests (2026-09-05).

Verifies that all six cards that were previously blocked from reaching
is_alert=True by the incomplete _HARD_ALERT_URGENCY table now correctly alert
at their documented worst-case urgency scenario.

These tests check the FINAL engine output (RankedCard.is_alert), not merely
the compound-condition boolean trigger. That distinction is the concrete
proof that the fix closes the real product risk.

Each test constructs a deterministic ContextFrame at maximum severity for the
card under test, runs engine.rank(), and asserts:
  1. The card is present in the output.
  2. is_alert is True.

The existing 4-card alert tests (test_priority_override.py, test_remediation.py)
remain unchanged and their assertions are not duplicated here.
"""
from __future__ import annotations

import pytest
from engine.engine import rank
from engine.models import ContextFrame, SignalValue, DestinationContext


# ---------------------------------------------------------------------------
# Shared fixture helpers
# ---------------------------------------------------------------------------

def _live(value) -> SignalValue:
    return SignalValue(value=value, source="live", freshness_min=0, confidence=1.0)


def _base_cf(**kwargs) -> ContextFrame:
    """Minimal valid ContextFrame with sensible defaults. Override via kwargs."""
    defaults = dict(
        personas=["default_general"],
        health_flags=[],
        has_declared_profile=False,
        local_time="2026-09-05T12:00:00+05:30",
        is_commute_window=False,
        is_daylight=True,
        lat=28.6,
        lon=77.2,
    )
    defaults.update(kwargs)
    return ContextFrame(**defaults)


def _find(output, card_id: str):
    """Return the first RankedCard with the given id from ranked or override lists."""
    all_cards = output.ranked_cards + output.override_warnings
    return next((c for c in all_cards if c.card_id == card_id), None)


# ---------------------------------------------------------------------------
# 1. compound_heat_aqi_danger
# ---------------------------------------------------------------------------

class TestCompoundHeatAqiDangerAlert:
    """
    Trigger: Temp >= 38°C AND AQI >= 150.
    urgency_multiplier returns flat 3.0 when compound fires.
    Threshold in _HARD_ALERT_URGENCY: 2.5.
    Expected: is_alert=True.
    """

    def test_compound_heat_aqi_danger_is_alert(self):
        cf = _base_cf(
            personas=["health"],
            has_declared_profile=True,
            temp_c=_live(40.0),
            aqi=_live({"aqi": 180, "dominant": "pm25"}),
        )
        output = rank(cf)
        card = _find(output, "compound_heat_aqi_danger")
        assert card is not None, "compound_heat_aqi_danger card must be present"
        assert card.is_alert is True, (
            f"compound_heat_aqi_danger must be is_alert=True at Temp=40°C + AQI=180 "
            f"(urgency=3.0 >= threshold 2.5). Got is_alert={card.is_alert}, "
            f"priority={card.priority}, score_components={card.score_components}"
        )

    def test_compound_heat_aqi_danger_alert_floor(self):
        """Low-confidence (simulated) compound scenario must still reach >= P2 via F-02 floor."""
        cf = _base_cf(
            personas=["health"],
            has_declared_profile=True,
            temp_c=SignalValue(value=40.0, source="simulated", freshness_min=300, confidence=0.7),
            aqi=SignalValue(value={"aqi": 180, "dominant": "pm25"}, source="simulated", freshness_min=300, confidence=0.7),
        )
        output = rank(cf)
        card = _find(output, "compound_heat_aqi_danger")
        assert card is not None
        assert card.is_alert is True
        assert card.priority in ("P0", "P1", "P2"), (
            f"Alert-floored compound card must not be P3. Got priority={card.priority}"
        )


# ---------------------------------------------------------------------------
# 2. compound_driving_hazard
# ---------------------------------------------------------------------------

class TestCompoundDrivingHazardAlert:
    """
    Trigger: Precip >= 60% AND Visibility <= 1.0 km (during commute window).
    urgency_multiplier returns flat 3.0 when compound fires.
    Threshold in _HARD_ALERT_URGENCY: 2.5.
    Expected: is_alert=True.
    """

    def test_compound_driving_hazard_is_alert(self):
        cf = _base_cf(
            personas=["commuter"],
            has_declared_profile=True,
            is_commute_window=True,
            precip_prob_pct=_live(80.0),
            visibility_km=_live(0.5),
        )
        output = rank(cf)
        card = _find(output, "compound_driving_hazard")
        assert card is not None, "compound_driving_hazard card must be present"
        assert card.is_alert is True, (
            f"compound_driving_hazard must be is_alert=True at Precip=80%+Vis=0.5km "
            f"(urgency=3.0 >= threshold 2.5). Got is_alert={card.is_alert}, "
            f"priority={card.priority}"
        )

    def test_compound_driving_hazard_alert_floor(self):
        """Low-confidence scenario must still floor to >= P2 via F-02."""
        cf = _base_cf(
            personas=["commuter"],
            has_declared_profile=True,
            is_commute_window=True,
            precip_prob_pct=SignalValue(value=80.0, source="simulated", freshness_min=300, confidence=0.7),
            visibility_km=SignalValue(value=0.5, source="simulated", freshness_min=300, confidence=0.7),
        )
        output = rank(cf)
        card = _find(output, "compound_driving_hazard")
        assert card is not None
        assert card.is_alert is True
        assert card.priority in ("P0", "P1", "P2"), (
            f"Alert-floored driving hazard card must not be P3. Got priority={card.priority}"
        )


# ---------------------------------------------------------------------------
# 3. visibility_commute
# ---------------------------------------------------------------------------

class TestVisibilityCommuteAlert:
    """
    Worst band: commute window + visibility <= 1.5km → urgency = 2.5.
    Threshold in _HARD_ALERT_URGENCY: 2.0.
    Expected: is_alert=True when urgency=2.5 >= 2.0.
    Off-peak worst band (urgency=1.6) must NOT alert (1.6 < 2.0).
    """

    def test_visibility_commute_during_commute_is_alert(self):
        cf = _base_cf(
            personas=["commuter"],
            has_declared_profile=True,
            is_commute_window=True,
            visibility_km=_live(0.8),   # <= 1.5km, commute window
        )
        output = rank(cf)
        card = _find(output, "visibility_commute")
        assert card is not None, "visibility_commute card must be present"
        assert card.is_alert is True, (
            f"visibility_commute must alert during commute window with vis=0.8km "
            f"(urgency=2.5 >= threshold 2.0). Got is_alert={card.is_alert}, "
            f"priority={card.priority}"
        )

    def test_visibility_commute_off_peak_does_not_alert(self):
        """Off-peak worst band (urgency=1.6) is below the alert threshold (2.0)."""
        cf = _base_cf(
            personas=["commuter"],
            has_declared_profile=True,
            is_commute_window=False,
            visibility_km=_live(0.8),   # <= 1.5km but NOT commute window → urgency=1.6
        )
        output = rank(cf)
        card = _find(output, "visibility_commute")
        assert card is not None
        assert card.is_alert is False, (
            f"visibility_commute must NOT alert off-peak with urgency=1.6 < threshold 2.0. "
            f"Got is_alert={card.is_alert}"
        )


# ---------------------------------------------------------------------------
# 4. destination_alert
# ---------------------------------------------------------------------------

class TestDestinationAlertAlert:
    """
    Trigger: >= 2 destination active warnings → urgency = 1.8.
    Threshold in _HARD_ALERT_URGENCY: 1.8.
    Expected: is_alert=True.
    Single-warning destination (urgency=1.4) must NOT alert (1.4 < 1.8).
    """

    def _make_warn(self) -> list[dict]:
        return [{"severity": "severe", "type": "storm", "text": "Heavy storm"}]

    def test_destination_alert_multi_warning_is_alert(self):
        dest1 = DestinationContext(
            lat=19.0, lon=72.8,
            warnings=self._make_warn(),
            temp_c=_live(32.0),
        )
        dest2 = DestinationContext(
            lat=23.0, lon=72.6,
            warnings=self._make_warn(),
            temp_c=_live(34.0),
        )
        cf = _base_cf(
            personas=["traveler"],
            has_declared_profile=True,
            destinations=[dest1, dest2],
        )
        output = rank(cf)
        card = _find(output, "destination_alert")
        assert card is not None, "destination_alert card must be present"
        assert card.is_alert is True, (
            f"destination_alert with >=2 destination warnings must be is_alert=True "
            f"(urgency=1.8 >= threshold 1.8). Got is_alert={card.is_alert}, "
            f"priority={card.priority}"
        )

    def test_destination_alert_single_warning_not_alert(self):
        """Single warning → urgency=1.4, which is below the threshold 1.8."""
        dest1 = DestinationContext(
            lat=19.0, lon=72.8,
            warnings=self._make_warn(),
            temp_c=_live(32.0),
        )
        cf = _base_cf(
            personas=["traveler"],
            has_declared_profile=True,
            destinations=[dest1],
        )
        output = rank(cf)
        card = _find(output, "destination_alert")
        assert card is not None
        assert card.is_alert is False, (
            f"destination_alert with 1 warning must NOT alert (urgency=1.4 < 1.8). "
            f"Got is_alert={card.is_alert}"
        )


# ---------------------------------------------------------------------------
# 5. agriculture_advisory
# ---------------------------------------------------------------------------

class TestAgricultureAdvisoryAlert:
    """
    Trigger: frost_warning_active=True → urgency = 2.0.
    Threshold in _HARD_ALERT_URGENCY: 1.8.
    Expected: is_alert=True.
    """

    def test_agriculture_advisory_frost_is_alert(self):
        cf = _base_cf(
            personas=["agriculture"],
            has_declared_profile=True,
            frost_warning_active=True,
            temp_c=_live(1.0),
        )
        output = rank(cf)
        card = _find(output, "agriculture_advisory")
        assert card is not None, "agriculture_advisory card must be present"
        assert card.is_alert is True, (
            f"agriculture_advisory with frost_warning_active=True must be is_alert=True "
            f"(urgency=2.0 >= threshold 1.8). Got is_alert={card.is_alert}, "
            f"priority={card.priority}"
        )

    def test_agriculture_advisory_no_stress_not_alert(self):
        """No frost, no dry soil → urgency=1.0, below any alert threshold.
        Card may or may not appear; if present it must not alert."""
        cf = _base_cf(
            personas=["agriculture"],
            has_declared_profile=True,
            frost_warning_active=False,
            temp_c=_live(22.0),
        )
        output = rank(cf)
        card = _find(output, "agriculture_advisory")
        # If the card doesn't appear at all, the no-alert property is trivially satisfied.
        if card is not None:
            assert card.is_alert is False, (
                f"agriculture_advisory with no frost/stress must NOT alert (urgency=1.0 < 1.8). "
                f"Got is_alert={card.is_alert}"
            )



# ---------------------------------------------------------------------------
# 6. marine_conditions_alert
# ---------------------------------------------------------------------------

class TestMarineConditionsAlert:
    """
    Trigger: wave_height_m > 1.5m → urgency = 2.0.
    Threshold in _HARD_ALERT_URGENCY: 1.8.
    Expected: is_alert=True.
    Small waves (wave <= 1.5m → urgency=1.0) must NOT alert.
    """

    def test_marine_conditions_high_wave_is_alert(self):
        cf = _base_cf(
            personas=["beachgoer"],
            has_declared_profile=True,
            wave_height_m=_live(2.5),
        )
        output = rank(cf)
        card = _find(output, "marine_conditions_alert")
        assert card is not None, "marine_conditions_alert card must be present"
        assert card.is_alert is True, (
            f"marine_conditions_alert with wave=2.5m must be is_alert=True "
            f"(urgency=2.0 >= threshold 1.8). Got is_alert={card.is_alert}, "
            f"priority={card.priority}"
        )

    def test_marine_conditions_calm_not_alert(self):
        """Calm seas (wave=0.5m → urgency=1.0) must not alert."""
        cf = _base_cf(
            personas=["beachgoer"],
            has_declared_profile=True,
            wave_height_m=_live(0.5),
        )
        output = rank(cf)
        card = _find(output, "marine_conditions_alert")
        assert card is not None
        assert card.is_alert is False, (
            f"marine_conditions_alert with calm wave=0.5m must NOT alert (urgency=1.0 < 1.8). "
            f"Got is_alert={card.is_alert}"
        )
