import datetime
import os
import httpx
from adapters.base import Adapter
from engine.models import SignalValue
from cache.store import store

class UVAdapter(Adapter):
    def fetch(self, lat: float, lon: float, when: datetime.datetime) -> SignalValue:
        mode = os.getenv("ADAPTER_MODE", "fixture")
        if mode == "fixture":
            scenario = os.getenv("FIXTURE_SCENARIO", "normal")
            filepath = os.path.join(os.path.dirname(__file__), "fixtures", f"aqi_uv_{scenario}.json")
            data = self.load_fixture(filepath)
            if data and "uv_index_sample" in data:
                return SignalValue(value=data["uv_index_sample"], source="simulated", confidence=0.7, freshness_min=0)
            return self.make_unavailable_signal()

        try:
            # Fake HTTP for live path scaffold to simulate proper timeout semantics without hitting real API
            return self.make_unavailable_signal()
        except httpx.TimeoutException:
            pass
        except Exception:
            pass

        return self.make_unavailable_signal()
