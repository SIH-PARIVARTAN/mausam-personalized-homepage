from engine.scoring import score
from engine.priority import classify_priority
from engine.models import ContextFrame, SignalValue
from engine.engine import _primary_signal_for

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
v, c = score("visibility_commute", cf, _primary_signal_for("visibility_commute", cf))
p = classify_priority("visibility_commute", v, cf)
with open("comp_out3.txt", "w") as f:
    f.write(f"SCORE: {v}\nCOMPONENTS: {c}\nPRIORITY: {p}")
