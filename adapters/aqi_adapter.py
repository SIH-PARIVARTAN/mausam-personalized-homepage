import datetime
import os
import httpx
from adapters.base import Adapter
from engine.models import SignalValue
from cache.store import store
import logging

logger = logging.getLogger(__name__)

class AQIAdapter(Adapter):
    def fetch(self, lat: float, lon: float, when: datetime.datetime) -> SignalValue:
        mode = os.getenv("ADAPTER_MODE", "fixture")
        if mode == "fixture":
            scenario = os.getenv("FIXTURE_SCENARIO", "normal")
            filepath = os.path.join(os.path.dirname(__file__), "fixtures", f"aqi_uv_{scenario}.json")
            data = self.load_fixture(filepath)
            if data and "aqi_sample" in data:
                return SignalValue(value=data["aqi_sample"], source="simulated", confidence=0.7, freshness_min=0)
            return self.make_unavailable_signal()

        cache_data = store.get("aqi", lat, lon)
        
        # 1. Fresh Cache
        if cache_data and not store.is_stale(cache_data["fetched_at"], max_age_min=60):
            logger.info("Serving fresh cache for AQI")
            return SignalValue(
                value=cache_data["value"], 
                source="cache", 
                confidence=cache_data.get("confidence", 0.7), 
                freshness_min=cache_data.get("freshness_min", 0)
            )

        # 2. Attempt Live Provider Fetch
        try:
            url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=us_aqi"
            with httpx.Client(timeout=1.5) as client:
                resp = client.get(url)
                resp.raise_for_status()
                payload = resp.json()
                
                aqi_val = payload.get("current", {}).get("us_aqi")
                if aqi_val is not None:
                    # Update Cache
                    store.set("aqi", lat, lon, str(aqi_val), "open-meteo", 0.9, freshness_min=0)
                    logger.info("Live fetch succeeded for AQI")
                    return SignalValue(value=aqi_val, source="open-meteo", confidence=0.9, freshness_min=0)
        
        except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as e:
            logger.warning(f"Live fetch failed for AQI ({type(e).__name__}). Attempting fallback.")

        # 3. Soft-Stale Fallback (Up to 4 hours)
        if cache_data and not store.is_stale(cache_data["fetched_at"], max_age_min=240):
            logger.info("Serving soft stale cache for AQI after live failure")
            return SignalValue(
                value=cache_data["value"], 
                source="cache-stale", 
                confidence=cache_data.get("confidence", 0.7) * 0.8, 
                freshness_min=cache_data.get("freshness_min", 0)
            )
            
        # 4. Hard-Stale / Fatal Failure Fallback
        logger.warning("Hard stale or empty cache for AQI. Degrading to unavailable.")
        return self.make_unavailable_signal()
