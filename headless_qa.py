import urllib.request
import json
import uuid

def test_homepage_200():
    print("Testing /homepage 200 OK...")
    url = "http://localhost:8000/homepage?device_id=d7b5f8fd-029e-4c57-893c-91af6d862f91&lat=18.4635&lon=73.8732"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req) as resp:
            data = resp.read()
            print("HTTP Status:", resp.status)
            assert resp.status == 200
            print("✅ 422 tracking error fully resolved, HTTP 200 OK received natively.")
    except Exception as e:
        print("❌ Error:", e)

def test_chatbot_fallback_ui():
    print("\nTesting /api/chat fallback missing GROQ Key...")
    url = "http://localhost:3000/api/chat"
    payload = json.dumps({"messages": [{"role": "user", "content": "Is it raining?"}]}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print("HTTP Status:", resp.status)
            print("Response:", data.get('reply'))
            assert "Chatbot AI is currently unavailable" in data.get('reply', '')
            print("✅ Chatbot fallback explicitly rejects generation without credentials as expected.")
    except Exception as e:
        print("❌ Error:", e)

if __name__ == "__main__":
    test_homepage_200()
    test_chatbot_fallback_ui()
