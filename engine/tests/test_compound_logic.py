import pytest
from engine.models import ContextFrame, SignalValue
from engine.compound import is_compound_heat_aqi_danger, is_compound_driving_hazard

def test_compound_heat_aqi_danger():
    # Base CF
    cf = ContextFrame(
        personas=["health"],
        health_flags=[],
        has_declared_profile=True,
        local_time="2026-08-26T12:00:00Z",
        is_commute_window=False,
        is_daylight=True,
        lat=0.0,
        lon=0.0,
    )
    
    # Missing / default -> False
    assert not is_compound_heat_aqi_danger(cf)
    
    # Below thresholds -> False
    cf.temp_c = SignalValue(value=35.0, source="live", freshness_min=0, confidence=1.0)
    cf.aqi = SignalValue(value={"aqi": 100, "dominant": "pm25"}, source="live", freshness_min=0, confidence=1.0)
    assert not is_compound_heat_aqi_danger(cf)
    
    # Temp hits, AQI misses -> False
    cf.temp_c.value = 39.0
    assert not is_compound_heat_aqi_danger(cf)
    
    # Both hit -> True
    cf.aqi.value = {"aqi": 155, "dominant": "pm25"} # Dictionary format
    assert is_compound_heat_aqi_danger(cf)
    
    # Integer fallback format hits -> True
    cf.aqi.value = 160
    assert is_compound_heat_aqi_danger(cf)
    
    # Temp missing -> False
    cf.temp_c.source = "unavailable"
    assert not is_compound_heat_aqi_danger(cf)

def test_compound_driving_hazard():
    cf = ContextFrame(
        personas=["commuter"],
        health_flags=[],
        has_declared_profile=True,
        local_time="2026-08-26T12:00:00Z",
        is_commute_window=True,
        is_daylight=True,
        lat=0.0,
        lon=0.0,
    )
    
    assert not is_compound_driving_hazard(cf)
    
    cf.precip_prob_pct = SignalValue(value=50.0, source="live", freshness_min=0, confidence=1.0)
    cf.visibility_km = SignalValue(value=2.0, source="live", freshness_min=0, confidence=1.0)
    assert not is_compound_driving_hazard(cf)
    
    # Rain hits, vis misses
    cf.precip_prob_pct.value = 70.0
    assert not is_compound_driving_hazard(cf)
    
    # Both hit
    cf.visibility_km.value = 0.5
    assert is_compound_driving_hazard(cf)
    
    # Vis unavailable
    cf.visibility_km.source = "unavailable"
    assert not is_compound_driving_hazard(cf)

