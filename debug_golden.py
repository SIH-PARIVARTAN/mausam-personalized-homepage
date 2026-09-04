import json
from engine.models import ContextFrame, SignalValue, DestinationContext
from engine.compound import is_compound_heat_aqi_danger
from engine.engine import rank

with open('eval/golden_set.json', 'r') as f:
    scenarios = json.load(f)

s = next(x for x in scenarios if x["id"] == "pd_compound_heat_aqi")
data = s['context']
data['temp_c'] = SignalValue(**data['temp_c'])
data['aqi'] = SignalValue(**data['aqi'])
data['precip_prob_pct'] = SignalValue(**data['precip_prob_pct'])
data['uv'] = SignalValue(**data['uv'])
data['wind_kmh'] = SignalValue(**data['wind_kmh'])

cf = ContextFrame(**data)
print("is_compound:", is_compound_heat_aqi_danger(cf))
out = rank(cf)
for c in out.ranked_cards:
    print(c.card_id, c.score, c.priority)
