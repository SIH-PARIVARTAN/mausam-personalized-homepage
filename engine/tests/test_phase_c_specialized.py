import pytest
from engine.models import ContextFrame, SignalValue, DailyForecastSummary
from engine.engine import rank

@pytest.fixture
def empty_context():
    return ContextFrame(
        personas=["default_general"],
        health_flags=[],
        has_declared_profile=False,
        local_time="2026-08-30T10:00:00+05:30",
        is_commute_window=False,
        is_daylight=True,
        lat=10.0,
        lon=10.0
    )

def test_agriculture_persona_soil_dryness(empty_context):
    empty_context.personas = ["agriculture"]
    empty_context.has_declared_profile = True
    empty_context.temp_c = SignalValue(25.0, "live", 0, 1.0)
    empty_context.soil_moisture_pct = SignalValue(15.0, "fixture", 0, 1.0)
    
    res = rank(empty_context)
    
    top = res.ranked_cards[0]
    # Agriculture should easily win since dry soil (15%) boosts urgency by 1.5x (0.95 * 1.5 * 1.0 = 1.425)
    assert top.card_id == "agriculture_advisory"

def test_beachgoer_persona_high_waves(empty_context):
    empty_context.personas = ["beachgoer"]
    empty_context.has_declared_profile = True
    empty_context.wave_height_m = SignalValue(2.0, "fixture", 0, 1.0)
    empty_context.tide_status = "rising"

    res = rank(empty_context)
    
    top = res.ranked_cards[0]
    # Beachgoer score: 0.95 (weight) * 2.0 (urgency for >1.5 waves) = 1.9
    assert top.card_id == "marine_conditions_alert"

def test_event_planner_persona_discomfort(empty_context):
    empty_context.personas = ["event_planner"]
    empty_context.has_declared_profile = True
    empty_context.temp_c = SignalValue(35.0, "live", 0, 1.0)
    empty_context.humidity_pct = SignalValue(80.0, "live", 0, 1.0)
    # Comfort index will be high (discomfort).
    empty_context.comfort_index = 32.0 
    empty_context.extended_forecast = [DailyForecastSummary("2026-08-31", 20.0, 30.0, 10.0, "sunny", "fixture", 1.0)]

    res = rank(empty_context)
    
    top = res.ranked_cards[0]
    assert top.card_id == "event_outlook"

def test_p0_override_protects_against_phase_c_marine(empty_context):
    # Tests that localized severe weather suppresses high waves
    empty_context.personas = ["beachgoer"]
    empty_context.wave_height_m = SignalValue(2.5, "fixture", 0, 1.0) # High wave
    empty_context.warnings = [{"severity": "red", "type": "Tornado", "text": "Tornado Warning"}]

    res = rank(empty_context)
    # Severe warning guarantees rank 1 position P0 override
    assert res.override_warnings[0].card_id == "severe_warning"

def test_multi_persona_maximum_weight():
    # Agriculture and Beachgoer overlaps
    cf = ContextFrame(
        personas=["beachgoer", "agriculture"],
        health_flags=[],
        has_declared_profile=True,
        local_time="2026-08-30T10:00:00",
        is_commute_window=False,
        is_daylight=True,
        lat=10.0,
        lon=10.0
    )
    # Both active, but wave is highly dangerous (2.0) vs normal soil (50%)
    cf.wave_height_m = SignalValue(2.5, "fixture", 0, 1.0)
    cf.soil_moisture_pct = SignalValue(50.0, "fixture", 0, 1.0)
    
    res = rank(cf)
    
    # marine_conditions_alert score is 0.95 * 2.0 = 1.9 
    # agriculture_advisory score is 0.95 * 1.0 = 0.95
    assert res.ranked_cards[0].card_id == "marine_conditions_alert"
