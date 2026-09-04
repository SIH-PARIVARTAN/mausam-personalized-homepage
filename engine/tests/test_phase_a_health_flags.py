import pytest
from engine.models import ContextFrame, SignalValue
from engine.scoring import score, PERSONA_WEIGHT

@pytest.fixture
def base_context():
    return ContextFrame(
        personas=["health"],
        health_flags=[],
        has_declared_profile=True,
        local_time="2026-08-26T12:00:00+05:30",
        is_commute_window=False,
        is_daylight=True,
        lat=28.6,
        lon=77.2,
        aqi=SignalValue(value={"aqi": 110, "dominant": "pm2.5"}, source="live", freshness_min=5, confidence=1.0)
    )

def test_health_flag_modifies_persona_weight_for_aqi(base_context):
    cf_no_flags = base_context
    cf_with_flags = ContextFrame(
        **{**base_context.__dict__, "health_flags": ["respiratory_sensitive"]}
    )

    # Calculate for user without profile vs user with profile
    base_pw = PERSONA_WEIGHT[("aqi_health", "health")]
    assert base_pw == 0.9

    primary_signal = cf_no_flags.aqi
    score_no, components_no = score("aqi_health", "health", cf_no_flags, primary_signal)
    
    score_yes, components_yes = score("aqi_health", "health", cf_with_flags, primary_signal)

    # Verify original weight is preserved without flags
    assert components_no["persona_weight"] == 0.9
    assert components_no["health_flags_applied"] is False
    
    # Verify exact +0.1 lift with flags
    assert components_yes["persona_weight"] == 1.0
    assert components_yes["health_flags_applied"] is True

    # Raw score should mathematically be higher because weight is 1.0 vs 0.9.
    # Urgency multiplier for aqi 110 is 1.3.
    # Confidence is 1.0.
    # score_no = 0.9 * 1.3 * 1.0 = 1.17
    # score_yes = 1.0 * 1.3 * 1.0 = 1.3
    assert score_yes > score_no
    assert abs(score_yes - 1.3) < 0.001

def test_health_flag_leaves_unrelated_cards_alone(base_context):
    # A respiratory flag should not bump the weight of rain commute.
    cf_with_flags = ContextFrame(
        **{**base_context.__dict__, "health_flags": ["respiratory_sensitive"]}
    )
    
    # Needs some precip probability to be scorable
    cf_with_flags.precip_prob_pct = SignalValue(value=80, source="live", freshness_min=5, confidence=1.0)
    primary_signal = cf_with_flags.precip_prob_pct
    
    _raw, components = score("rain_commute", "health", cf_with_flags, primary_signal)
    
    assert components["health_flags_applied"] is False
    assert components["persona_weight"] == PERSONA_WEIGHT[("rain_commute", "health")]
