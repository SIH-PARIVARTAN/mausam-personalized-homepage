import pytest
import datetime
import httpx
from unittest.mock import patch, MagicMock
import os
from engine.models import SignalValue
from cache.store import store
from adapters.aqi_adapter import AQIAdapter
from adapters.forecast_adapter import ForecastAdapter

@pytest.fixture(autouse=True)
def set_live_mode():
    os.environ["ADAPTER_MODE"] = "live"
    yield
    os.environ["ADAPTER_MODE"] = "fixture"

def test_aqi_live_timeout_fallback():
    # Setup cache for soft-stale fallback
    store.get = MagicMock(return_value={"fetched_at": "old", "value": 110, "confidence": 0.8, "freshness_min": 0})
    store.is_stale = MagicMock(side_effect=[True, False]) # Fresh=True (stale), Soft-Stale=False (valid)
    
    adapter = AQIAdapter()
    when = datetime.datetime.now()
    
    with patch("httpx.Client.get", side_effect=httpx.TimeoutException("mocked timeout")):
        result = adapter.fetch(0.0, 0.0, when)
    
    assert result.value == 110
    assert result.source == "cache-stale"

def test_aqi_live_success_cache_miss():
    store.get = MagicMock(return_value=None)
    store.set = MagicMock()
    
    adapter = AQIAdapter()
    when = datetime.datetime.now()
    
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"current": {"us_aqi": 42}}
    
    with patch("httpx.Client.get", return_value=mock_resp):
        result = adapter.fetch(0.0, 0.0, when)
    
    assert result.value == 42
    assert result.source == "open-meteo"
    store.set.assert_called_once()

def test_forecast_live_timeout_hard_stale_fallback():
    # Setup cache: Too old (soft-stale check fails)
    store.get = MagicMock(return_value={"fetched_at": "very_old", "value": {"temp_c": 10}, "confidence": 0.8, "freshness_min": 0})
    store.is_stale = MagicMock(side_effect=[True, True]) 
    
    adapter = ForecastAdapter()
    when = datetime.datetime.now()
    
    with patch("httpx.Client.get", side_effect=httpx.TimeoutException("mock")):
        res = adapter.fetch(0.0, 0.0, when)
    
    # 7-tuple contract verification
    assert len(res) == 7
    # Since it failed hard-stale, should all be unavailable
    assert res[0].source == "unavailable"
    assert res[5].source == "unavailable"
    assert res[6] == [] 

def test_forecast_live_success_schema():
    store.get = MagicMock(return_value=None)
    store.set = MagicMock()
    
    adapter = ForecastAdapter()
    when = datetime.datetime.now()
    
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "current": {
            "temperature_2m": 25.5,
            "relative_humidity_2m": 60,
            "precipitation_probability": 0,
            "wind_speed_10m": 12,
            "visibility": 10000
        }
    }
    
    with patch("httpx.Client.get", return_value=mock_resp):
        res = adapter.fetch(0.0, 0.0, when)
    
    assert len(res) == 7
    assert res[0].value == 25.5
    assert res[1].value == 60
    assert res[4].value == 10.0 # 10000 / 1000.0 mapped perfectly natively
    assert res[5].source == "unavailable" # unsupported parameter
