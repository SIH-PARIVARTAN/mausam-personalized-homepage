import pytest
from engine.models import ContextFrame, SignalValue
from engine.engine import rank

def test_commuter_visibility_p1():
    cf = ContextFrame(
        personas=["commuter"],
        health_flags=[],
        has_declared_profile=True,
        local_time="2026",
        is_daylight=True,
        lat=0.0,
        lon=0.0,
        is_commute_window=True,
        visibility_km=SignalValue(value=1.0, source="live", freshness_min=0, confidence=1.0)
    )
    ranked = rank(cf)
    vis = next(c for c in ranked.ranked_cards if c.card_id == "visibility_commute")
    assert vis.priority == "P1" # < 1.5km during commute -> 2.5 multiplier * 0.95 -> 2.375 -> P1

def test_commuter_graceful_missing_visibility():
    cf = ContextFrame(
        personas=["commuter"],
        health_flags=[],
        has_declared_profile=True,
        local_time="2026",
        is_daylight=True,
        lat=0.0,
        lon=0.0,
        is_commute_window=True,
        visibility_km=SignalValue(value=None, source="unavailable", freshness_min=None, confidence=0.0)
    )
    ranked = rank(cf)
    # The _card_applies specifically looks for valid required signals. If unavailable, card drops
    assert not any(c.card_id == "visibility_commute" for c in ranked.ranked_cards)
