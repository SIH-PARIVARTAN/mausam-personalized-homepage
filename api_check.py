import httpx
try:
    url = "https://air-quality-api.open-meteo.com/v1/air-quality?latitude=19.55&longitude=75.25&current=us_aqi"
    r = httpx.get(url, timeout=3.0)
    print("STATUS:", r.status_code)
    try:
        data = r.json()
        print("JSON KEYS:", list(data.keys()))
        print("CURRENT KEY EXISTS:", "current" in data)
        print("CURRENT VALUE:", data.get("current"))
        
        # Simulating extraction
        aqi_val = data.get("current", {}).get("us_aqi")
        print("EXTRACTED_AQI:", aqi_val)
    except Exception as e:
        print("JSON ERROR:", str(e))
except Exception as e:
    print("HTTP ERROR:", str(e))
