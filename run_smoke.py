import os
import datetime
from dotenv import load_dotenv

# Instruct python-dotenv to read .env.local instead of the default .env
loaded = load_dotenv(".env.local")
print("Environment file .env.local loaded:", loaded)

os.environ["ADAPTER_MODE"] = "live"
print("ADAPTER_MODE explicitly set to:", os.environ["ADAPTER_MODE"])

from backend.db import init_pool, close_pool
from backend.deps import build_context_frame
import time

def run_tests():
    try:
        init_pool()
        print("\n--- FIRST FETCH (EXPECT LIVE CACHE MISS) ---")
        when = datetime.datetime.now(datetime.timezone.utc)
        cf = build_context_frame({'personas': ['default_general']}, 19.55, 75.25, when)
        
        print("AQI Value:", cf.aqi.value)
        print("AQI Source:", cf.aqi.source)
        print("Temp Value:", cf.temp_c.value)
        print("Temp Source:", cf.temp_c.source)
        print("Precip Prob:", cf.precip_prob_pct.value)
        print("Visibility (km):", cf.visibility_km.value)
        
        print("\n--- SECOND FETCH (EXPECT CACHE HIT) ---")
        cf2 = build_context_frame({'personas': ['default_general']}, 19.55, 75.25, when)
        print("AQI Source Retry:", cf2.aqi.source)
        print("Temp Source Retry:", cf2.temp_c.source)

    except Exception as e:
        print("ERROR:", str(e))
    finally:
        close_pool()

if __name__ == "__main__":
    run_tests()
