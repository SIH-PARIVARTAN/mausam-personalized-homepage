import datetime
import os
from adapters.base import Adapter
from engine.models import SignalValue

class MarineAdapter(Adapter):
    def fetch(self, lat: float, lon: float, when: datetime.datetime) -> any:
        scenario = os.getenv("FIXTURE_SCENARIO", "normal")
        filepath = os.path.join(os.path.dirname(__file__), "fixtures", f"marine_{scenario}.json")
        data = self.load_fixture(filepath)
        if not data:
            return (
                self.make_unavailable_signal(),
                self.make_unavailable_signal(),
                self.make_unavailable_signal()
            )

        # Using 'fixture' source and 1.0 confidence because deterministic tests fully trust local fixtures
        return (
            SignalValue(value=data.get("wave_height_m"), source="fixture", confidence=1.0, freshness_min=0),
            SignalValue(value=data.get("water_temp_c"), source="fixture", confidence=1.0, freshness_min=0),
            SignalValue(value=data.get("tide_status"), source="fixture", confidence=1.0, freshness_min=0)
        )
