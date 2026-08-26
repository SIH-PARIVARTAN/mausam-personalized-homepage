import datetime
import os
import httpx
from adapters.base import Adapter
from engine.models import SignalValue
from cache.store import store

class AQIAdapter(Adapter):
    def fetch(self, lat: float, lon: float, when: datetime.datetime) -> SignalValue:
        mode = os.getenv("ADAPTER_MODE", "fixture")
        if mode == "fixture":
            filepath = os.path.join(os.path.dirname(__file__), "fixtures", "aqi_uv_recorded_samples.json")
            data = self.load_fixture(filepath)
            if data and "aqi_sample" in data:
                return SignalValue(value=data["aqi_sample"], source="simulated", confidence=0.7, freshness_min=0)
            return self.make_unavailable_signal()

        # Live path - scaffolded but defaults to returning logic based failures realistically for MVP
        try:
            # Fake HTTP for live path scaffold to simulate proper timeout semantics without hitting real API (MVP)
            return self.make_unavailable_signal()
        except httpx.TimeoutException:
            pass
        except Exception:
            pass

        return self.make_unavailable_signal()
