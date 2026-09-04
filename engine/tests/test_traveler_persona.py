import pytest
from engine.models import ContextFrame, DestinationContext, SignalValue
from engine.engine import rank

def test_traveler_destination_alert_urgency():
    cf = ContextFrame(
        personas=["traveler"],
        health_flags=[],
        has_declared_profile=True,
        local_time="2026",
        is_commute_window=False,
        is_daylight=True,
        lat=0.0,
        lon=0.0,
        destinations=[
            DestinationContext(lat=10, lon=10, warnings=[{"text": "flood"}]),
            DestinationContext(lat=20, lon=20, warnings=[{"text": "storm"}])
        ]
    )
    ranked = rank(cf)
    dest = next(c for c in ranked.ranked_cards if c.card_id == "destination_alert")
    assert dest.priority == "P2"  # 2 warnings → 1.8 multiplier × 0.7 (simulated conf) = 1.197

    cf2 = ContextFrame(
        personas=["traveler"],
        health_flags=[],
        has_declared_profile=True,
        local_time="2026",
        is_commute_window=False,
        is_daylight=True,
        lat=0.0,
        lon=0.0,
        destinations=[
            DestinationContext(lat=10, lon=10, warnings=[{"text": "flood"}])
        ]
    )
    ranked2 = rank(cf2)
    dest2 = next(c for c in ranked2.ranked_cards if c.card_id == "destination_alert")
    assert dest2.priority == "P2" # 1 warning → 1.4 multiplier × 0.7 = 0.931 (P2 threshold is 0.7)


def test_local_p0_overrides_destination_alert():
    cf = ContextFrame(
        personas=["traveler"],
        health_flags=[],
        has_declared_profile=True,
        local_time="2026",
        is_commute_window=False,
        is_daylight=True,
        lat=0.0,
        lon=0.0,
        warnings=[{"severity": "red", "text": "local cyclone", "type": "cyclone"}],
        destinations=[
            DestinationContext(lat=10, lon=10, warnings=[{"severity": "red"}])
        ]
    )
    ranked = rank(cf)
    assert ranked.override_warnings[0].card_id == "severe_warning"
    assert ranked.override_warnings[0].priority == "P0"


def test_destination_alert_graceful_missing():
    cf = ContextFrame(
        personas=["traveler"],
        health_flags=[],
        has_declared_profile=True,
        local_time="2026",
        is_commute_window=False,
        is_daylight=True,
        lat=0.0,
        lon=0.0,
        destinations=[]
    )
    ranked = rank(cf)
    # destination_alert requires destinations with warnings
    assert not any(c.card_id == "destination_alert" for c in ranked.ranked_cards)
