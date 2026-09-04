import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.models_api import HomepageResponse
import uuid

client = TestClient(app)
valid_uuid = str(uuid.uuid4())

def test_homepage_contract_normal(monkeypatch):
    monkeypatch.setenv("FIXTURE_SCENARIO", "normal")
    response = client.get(f"/homepage?device_id={valid_uuid}&lat=12.9&lon=77.5")
    assert response.status_code == 200, response.json()
    data = response.json()
    HomepageResponse(**data)
    assert len(data["cards"]) > 0

def test_homepage_contract_severe(monkeypatch):
    monkeypatch.setenv("FIXTURE_SCENARIO", "severe_warning")
    response = client.get(f"/homepage?device_id={valid_uuid}&lat=12.9&lon=77.5")
    assert response.status_code == 200, response.json()
    data = response.json()
    HomepageResponse(**data)
    assert len(data["warnings_override"]) > 0

def test_homepage_contract_unavailable(monkeypatch):
    monkeypatch.setenv("FIXTURE_SCENARIO", "broken")
    from adapters.forecast_adapter import ForecastAdapter
    from adapters.aqi_adapter import AQIAdapter
    from adapters.uv_adapter import UVAdapter

    def fake_make_unav(*args, **kwargs):
        # By providing exactly the shape returning unavailable signals
        f = ForecastAdapter()
        return (f.make_unavailable_signal(), f.make_unavailable_signal(), f.make_unavailable_signal(), f.make_unavailable_signal(), f.make_unavailable_signal(), f.make_unavailable_signal(), [])

    monkeypatch.setattr(ForecastAdapter, "fetch", fake_make_unav)
    monkeypatch.setattr(AQIAdapter, "fetch", lambda *args, **kwargs: AQIAdapter().make_unavailable_signal())
    monkeypatch.setattr(UVAdapter, "fetch", lambda *args, **kwargs: UVAdapter().make_unavailable_signal())

    response = client.get(f"/homepage?device_id={valid_uuid}&lat=12.9&lon=77.5")
    assert response.status_code == 200, response.json()
    data = response.json()
    HomepageResponse(**data)
    assert data["system_notice"] is not None

def test_device_id_validation():
    response = client.get("/homepage?device_id=invalid&lat=12.9&lon=77.5")
    assert response.status_code == 422

def test_preferences_contract_enums():
    valid_payload = {
        "device_id": valid_uuid,
        "personas": ["health"],
        "health_flags": ["respiratory_sensitive"],
        "saved_locations": []
    }
    response = client.put("/preferences", json=valid_payload)
    assert response.status_code == 200, response.json()

    invalid_payload = {
        "device_id": valid_uuid,
        "personas": ["invalid_persona"],
        "health_flags": [],
        "saved_locations": []
    }
    response2 = client.put("/preferences", json=invalid_payload)
    assert response2.status_code == 422
