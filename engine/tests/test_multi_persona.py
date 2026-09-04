import pytest
from engine.engine import _best_persona_for_card, _declared_ids, rank
from engine.models import ContextFrame, SignalValue
from engine.scoring import PERSONA_WEIGHT

@pytest.fixture
def multi_persona_cf():
    return ContextFrame(
        personas=["health", "fitness", "family"],
        health_flags=[],
        has_declared_profile=True,
        local_time="2026-08-26T12:00:00+05:30",
        is_commute_window=True,
        is_daylight=True,
        lat=28.6,
        lon=77.2,
        aqi=SignalValue(value={"aqi": 180, "dominant": "pm2.5"}, source="live", freshness_min=5, confidence=1.0),
        uv=SignalValue(value=9.0, source="live", freshness_min=5, confidence=1.0),
        precip_prob_pct=SignalValue(value=85, source="live", freshness_min=5, confidence=1.0)
    )

def test_best_persona_combines_max_weights():
    # health has highest weight for aqi_health (0.9)
    best_aqi = _best_persona_for_card("aqi_health", ["health", "fitness", "family"])
    assert best_aqi == "health"
    
    # fitness has highest weight for uv_sun_exposure (0.9)
    best_uv = _best_persona_for_card("uv_sun_exposure", ["health", "fitness", "family"])
    assert best_uv == "fitness"
    
    # family has highest weight for rain_commute (0.95)
    best_rain = _best_persona_for_card("rain_commute", ["health", "fitness", "family"])
    assert best_rain == "family"

def test_multi_persona_scoring_does_not_dilute_results(multi_persona_cf):
    output = rank(multi_persona_cf)
    cards = {c.card_id: c for c in output.ranked_cards}
    
    assert cards["aqi_health"].score_components["persona_weight"] == 0.9
    assert cards["uv_sun_exposure"].score_components["persona_weight"] == 0.9
    assert cards["rain_commute"].score_components["persona_weight"] == 0.95

def test_empty_persona_fallback():
    best_empty = _best_persona_for_card("aqi_health", [])
    assert best_empty == "default_general"

def test_p0_safety_ignores_multi_persona_weightings(multi_persona_cf):
    # Setup severe warning
    multi_persona_cf.warnings = [{"severity": "red", "type": "Flood", "text": "Evacuate"}]
    output = rank(multi_persona_cf)
    
    assert len(output.override_warnings) == 1
    assert output.override_warnings[0].card_id == "severe_warning"
    assert output.override_warnings[0].score_components["persona_weight"] == 1.0

def test_declared_ids_aggregates_multiple_profiles(multi_persona_cf):
    # Ensure all cards relevant to health, fitness, or family are captured
    declared = _declared_ids(multi_persona_cf)
    assert "aqi_health" in declared
    assert "uv_sun_exposure" in declared
    assert "rain_commute" in declared
