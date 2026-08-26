import pytest
import os
os.environ["DATABASE_URL"] = "postgresql://dummy"

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_db():
    with patch("backend.main.get_connection") as mock_get_conn, \
         patch("backend.routers.preferences.get_connection") as mock_pref_conn, \
         patch("cache.store.get_connection") as mock_cache_conn, \
         patch("backend.main.init_pool"), \
         patch("backend.main.init_db"), \
         patch("backend.main.close_pool"):

        # Setup a mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        # Make the connection context manager yield the mock_conn
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        mock_pref_conn.return_value.__enter__.return_value = mock_conn
        mock_cache_conn.return_value.__enter__.return_value = mock_conn

        # Make the cursor context manager yield the mock_cursor
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        yield mock_cursor

def test_health_endpoint(mock_db):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "db": "connected"}

def test_health_endpoint_degraded(mock_db):
    mock_db.execute.side_effect = Exception("DB Down")
    resp = client.get("/health")
    assert resp.status_code == 503
    assert resp.json() == {"status": "degraded", "db": "unavailable"}

def test_preferences_cold_start(mock_db):
    mock_db.fetchone.return_value = None
    resp = client.get("/preferences?device_id=cold_starter_123")
    assert resp.status_code == 200
    data = resp.json()
    assert data["personas"] == ["default_general"]
    assert data["device_id"] == "cold_starter_123"

def test_preferences_put_and_get(mock_db):
    import json
    # Mocking PUT
    device_id = "testbench_device"
    payload = {
        "device_id": device_id,
        "personas": ["health", "fitness"],
        "health_flags": ["asthma"],
        "saved_locations": []
    }
    put_resp = client.put("/preferences", json=payload)
    assert put_resp.status_code == 200
    assert put_resp.json() == {"status": "ok"}

    # Mocking GET where it returns the saved row
    mock_db.fetchone.return_value = (
        device_id,
        json.dumps(["health", "fitness"]),
        json.dumps(["asthma"]),
        json.dumps([])
    )
    get_resp = client.get(f"/preferences?device_id={device_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["personas"] == ["health", "fitness"]
    assert data["health_flags"] == ["asthma"]

def test_cache_store(mock_db):
    from cache.store import store
    import json

    import datetime

    # Mock GET returning a row
    fetched_at = (datetime.datetime.utcnow() - datetime.timedelta(hours=2)).isoformat()
    mock_db.fetchone.return_value = (
        json.dumps({"test": 123}),
        "simulated",
        fetched_at,
        0.9,
        10
    )

    data = store.get("pytest", 18.23, 73.11)
    assert data is not None
    assert data["source"] == "simulated"
    assert data["value"] == {"test": 123}

    # Staleness check
    assert store.is_stale(fetched_at, max_age_min=-1) == True
