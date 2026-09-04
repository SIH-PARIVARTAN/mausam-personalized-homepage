from engine.engine import rank
from engine.models import ContextFrame, SignalValue
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
r = rank(cf)
for c in r.ranked_cards:
    if c.card_id == "visibility_commute":
        print("CARD ID:", c.card_id)
        print("SCORE VAL (COMPUTED IN TEST): ", c.score_components['persona_weight']*c.score_components['urgency_multiplier']*c.score_components['confidence_factor'])
        print("PRIORITY:", c.priority)
        print("COMPONENTS:", c.score_components)
