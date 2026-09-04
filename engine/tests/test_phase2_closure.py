"""
engine/tests/test_phase2_closure.py

Focused regression tests for Phase 2 Engine Foundation Correction.
Ensures that the fixture confidence collapse and the raw-score tie-breaking 
defects do not regress.
"""
import pytest
from engine.scoring import confidence_factor, CONFIDENCE_BY_SOURCE
from engine.models import SignalValue, RankedCard
from engine.conflict import resolve_ties

def test_phase2_fixture_confidence_is_fully_trusted():
    """
    Regression test for the Phase 2 '0.0 confidence collapse' bug.
    Ensures that evaluating cards using 'fixture' data from the golden evaluation
    set gives a confidence factor of 1.0 rather than defaulting to 0.0.
    """
    assert "fixture" in CONFIDENCE_BY_SOURCE, "'fixture' must be explicitly mapped in CONFIDENCE_BY_SOURCE"
    
    # Create a dummy fixture signal
    sv = SignalValue(value=25.0, source="fixture", freshness_min=0, confidence=1.0)
    
    cf_val = confidence_factor(sv)
    assert cf_val == 1.0, f"Expected confidence factor for 'fixture' source to be 1.0, got {cf_val}"

def test_phase2_tie_breaking_respects_raw_score_before_urgency_and_static_order():
    """
    Regression test for Phase 2 tie-breaking bug.
    Ensures that when two cards belong to the same priority bucket, the resolver
    prefers the card with the higher final calculated score BEFORE using
    urgency_multiplier or the static CARD_DEFINITION_ORDER.
    """
    # Create two dummy cards in the same priority bucket (P2)
    # Card A: Lower static rank, lower urgency, but higher raw score.
    card_a = RankedCard(
        card_id="sunrise_sunset", # Static rank index 5 (lower)
        priority="P2",
        is_alert=False,
        score=0.9, # Higher raw score
        score_components={"urgency_multiplier": 1.0}, # Lower urgency
        explanation_text="",
        signal_refs=[]
    )
    
    # Card B: Higher static rank, higher urgency, but lower raw score.
    card_b = RankedCard(
        card_id="aqi_health", # Static rank index 1 (higher)
        priority="P2",
        is_alert=False,
        score=0.8, # Lower raw score
        score_components={"urgency_multiplier": 1.5}, # Higher urgency
        explanation_text="",
        signal_refs=[]
    )
    
    # Resolve the tie
    sorted_cards = resolve_ties([card_a, card_b], declared_persona_card_ids=set())
    
    # Since card A has the higher overall raw score (0.9 > 0.8), it must win
    # despite having lower urgency and being lower in the static order.
    assert sorted_cards[0].card_id == "sunrise_sunset", (
        "Tie-breaker failed to prioritize the higher calculated score (0.9 vs 0.8). "
        "It incorrectly fell back to urgency_multiplier or static order."
    )
    assert sorted_cards[1].card_id == "aqi_health"

def test_phase2_tie_breaking_respects_urgency_if_raw_score_ties():
    """
    Ensure that urgency_multiplier is used correctly as a fallback if the raw score
    itself is identical.
    """
    card_a = RankedCard(
        card_id="sunrise_sunset", 
        priority="P2",
        is_alert=False,
        score=0.8, # Tied raw score
        score_components={"urgency_multiplier": 1.0}, # Lower urgency
        explanation_text="",
        signal_refs=[]
    )
    
    card_b = RankedCard(
        card_id="aqi_health", 
        priority="P2",
        is_alert=False,
        score=0.8, # Tied raw score
        score_components={"urgency_multiplier": 1.5}, # Higher urgency
        explanation_text="",
        signal_refs=[]
    )
    
    sorted_cards = resolve_ties([card_a, card_b], declared_persona_card_ids=set())
    assert sorted_cards[0].card_id == "aqi_health", "Must fall back to urgency if raw scores are tied"
