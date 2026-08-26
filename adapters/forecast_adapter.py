import datetime
import os
from adapters.base import Adapter
from engine.models import SignalValue

class ForecastAdapter(Adapter):
    def fetch(self, lat: float, lon: float, when: datetime.datetime) -> any:
        scenario = os.getenv("FIXTURE_SCENARIO", "normal")
        filepath = os.path.join(os.path.dirname(__file__), "fixtures", f"forecast_{scenario}.json")
        data = self.load_fixture(filepath)
        if not data:
            return (
                self.make_unavailable_signal(),
                self.make_unavailable_signal(),
                self.make_unavailable_signal(),
                self.make_unavailable_signal()
            )

        return (
            SignalValue(value=data.get("temp_c"), source="simulated", confidence=0.7, freshness_min=0),
            SignalValue(value=data.get("humidity_pct"), source="simulated", confidence=0.7, freshness_min=0),
            SignalValue(value=data.get("wind_kmh"), source="simulated", confidence=0.7, freshness_min=0),
            SignalValue(value=data.get("precip_prob_pct"), source="simulated", confidence=0.7, freshness_min=0)
        )
