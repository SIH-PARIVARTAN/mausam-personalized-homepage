import datetime
import os
import json
import httpx
from adapters.base import Adapter
from engine.models import SignalValue, DailyForecastSummary
from cache.store import store
import logging

logger = logging.getLogger(__name__)

class ForecastAdapter(Adapter):
    def fetch(self, lat: float, lon: float, when: datetime.datetime) -> any:
        mode = os.getenv("ADAPTER_MODE", "fixture")
        if mode == "fixture":
            scenario = os.getenv("FIXTURE_SCENARIO", "normal")
            filepath = os.path.join(os.path.dirname(__file__), "fixtures", f"forecast_{scenario}.json")
            data = self.load_fixture(filepath)
            if not data:
                return (self.make_unavailable_signal(),) * 6 + ([],)
            
            return (
                SignalValue(value=data.get("temp_c"), source="fixture", confidence=1.0, freshness_min=0),
                SignalValue(value=data.get("humidity_pct"), source="fixture", confidence=1.0, freshness_min=0),
                SignalValue(value=data.get("wind_kmh"), source="fixture", confidence=1.0, freshness_min=0),
                SignalValue(value=data.get("precip_prob_pct"), source="fixture", confidence=1.0, freshness_min=0),
                SignalValue(value=data.get("visibility_km"), source="fixture", confidence=1.0, freshness_min=0),
                SignalValue(value=data.get("soil_moisture_pct"), source="fixture", confidence=1.0, freshness_min=0),
                [DailyForecastSummary(**day) for day in data.get("extended_forecast", [])]
            )

        cache_data = store.get("forecast", lat, lon)
        
        # 1. Fresh Cache
        if cache_data and not store.is_stale(cache_data["fetched_at"], max_age_min=60):
            logger.info("Serving fresh cache for Forecast")
            val = cache_data["value"]
            return (
                SignalValue(value=val.get("temp_c"), source="cache", confidence=0.7, freshness_min=cache_data.get("freshness_min", 0)) if val.get("temp_c") is not None else self.make_unavailable_signal(),
                SignalValue(value=val.get("humidity_pct"), source="cache", confidence=0.7, freshness_min=cache_data.get("freshness_min", 0)) if val.get("humidity_pct") is not None else self.make_unavailable_signal(),
                SignalValue(value=val.get("wind_kmh"), source="cache", confidence=0.7, freshness_min=cache_data.get("freshness_min", 0)) if val.get("wind_kmh") is not None else self.make_unavailable_signal(),
                SignalValue(value=val.get("precip_prob_pct"), source="cache", confidence=0.7, freshness_min=cache_data.get("freshness_min", 0)) if val.get("precip_prob_pct") is not None else self.make_unavailable_signal(),
                SignalValue(value=val.get("visibility_km"), source="cache", confidence=0.7, freshness_min=cache_data.get("freshness_min", 0)) if val.get("visibility_km") is not None else self.make_unavailable_signal(),
                self.make_unavailable_signal(),
                []
            )

        # 2. Attempt Live Fetch
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation_probability,visibility"
            with httpx.Client(timeout=1.5) as client:
                res = client.get(url)
                res.raise_for_status()
                payload = res.json()
                current = payload.get("current", {})
                
                vis_meters = current.get("visibility")
                live_vals = {
                    "temp_c": current.get("temperature_2m"),
                    "humidity_pct": current.get("relative_humidity_2m"),
                    "wind_kmh": current.get("wind_speed_10m"),
                    "precip_prob_pct": current.get("precipitation_probability"),
                    "visibility_km": vis_meters / 1000.0 if vis_meters is not None else None
                }
                
                if live_vals["temp_c"] is not None:
                    store.set("forecast", lat, lon, json.dumps(live_vals), "open-meteo", 0.9, freshness_min=0)
                    logger.info("Live fetch succeeded for Forecast")
                    return (
                        SignalValue(value=live_vals.get("temp_c"), source="open-meteo", confidence=0.9, freshness_min=0) if live_vals.get("temp_c") is not None else self.make_unavailable_signal(),
                        SignalValue(value=live_vals.get("humidity_pct"), source="open-meteo", confidence=0.9, freshness_min=0) if live_vals.get("humidity_pct") is not None else self.make_unavailable_signal(),
                        SignalValue(value=live_vals.get("wind_kmh"), source="open-meteo", confidence=0.9, freshness_min=0) if live_vals.get("wind_kmh") is not None else self.make_unavailable_signal(),
                        SignalValue(value=live_vals.get("precip_prob_pct"), source="open-meteo", confidence=0.9, freshness_min=0) if live_vals.get("precip_prob_pct") is not None else self.make_unavailable_signal(),
                        SignalValue(value=live_vals.get("visibility_km"), source="open-meteo", confidence=0.9, freshness_min=0) if live_vals.get("visibility_km") is not None else self.make_unavailable_signal(),
                        self.make_unavailable_signal(),
                        []
                    )
        except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as e:
            logger.warning(f"Live fetch failed for Forecast ({type(e).__name__}). Attempting fallback.")

        # 3. Soft Stale Fallback
        if cache_data and not store.is_stale(cache_data["fetched_at"], max_age_min=240):
            logger.info("Serving soft stale cache for Forecast after live failure")
            val = cache_data["value"]
            return (
                SignalValue(value=val.get("temp_c"), source="cache-stale", confidence=0.56, freshness_min=cache_data.get("freshness_min", 0)) if val.get("temp_c") is not None else self.make_unavailable_signal(),
                SignalValue(value=val.get("humidity_pct"), source="cache-stale", confidence=0.56, freshness_min=cache_data.get("freshness_min", 0)) if val.get("humidity_pct") is not None else self.make_unavailable_signal(),
                SignalValue(value=val.get("wind_kmh"), source="cache-stale", confidence=0.56, freshness_min=cache_data.get("freshness_min", 0)) if val.get("wind_kmh") is not None else self.make_unavailable_signal(),
                SignalValue(value=val.get("precip_prob_pct"), source="cache-stale", confidence=0.56, freshness_min=cache_data.get("freshness_min", 0)) if val.get("precip_prob_pct") is not None else self.make_unavailable_signal(),
                SignalValue(value=val.get("visibility_km"), source="cache-stale", confidence=0.56, freshness_min=cache_data.get("freshness_min", 0)) if val.get("visibility_km") is not None else self.make_unavailable_signal(),
                self.make_unavailable_signal(),
                []
            )

        # 4. Hard Stale Fatal
        logger.warning("Hard stale or empty cache for Forecast. Degrading to unavailable.")
        return (self.make_unavailable_signal(),) * 6 + ([],)
