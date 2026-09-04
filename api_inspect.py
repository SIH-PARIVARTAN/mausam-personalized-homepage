import httpx
import traceback

def test_aqi(lat, lon):
    try:
        url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=us_aqi"
        print(f"Requesting: {url}")
        with httpx.Client(timeout=1.5) as client:
            resp = client.get(url)
            resp.raise_for_status()
            payload = resp.json()
            aqi_val = payload.get("current", {}).get("us_aqi")
            print("Extracted:", aqi_val)
    except Exception as e:
        print("Caught exception:", type(e).__name__, str(e))
        traceback.print_exc()

test_aqi(19.55, 75.25)
test_aqi(18.5, 73.8)
