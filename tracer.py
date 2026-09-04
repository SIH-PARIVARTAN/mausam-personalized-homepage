from engine.engine import rank
from engine.models import ContextFrame, DestinationContext
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
r = rank(cf)
d = next(c for c in r.ranked_cards if c.card_id == "destination_alert")
with open("comp_out.txt", "w") as f:
    f.write(str(d.score_components))
