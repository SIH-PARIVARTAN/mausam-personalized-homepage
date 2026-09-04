"""
engine/compound.py

Pure deterministic evaluation logic for Phase D compound insights.
These functions inspect ContextFrame directly and return boolean applicability natively.
They do not rank, explain, or interact with external services.
"""
from __future__ import annotations

from .models import ContextFrame


def is_compound_heat_aqi_danger(cf: ContextFrame) -> bool:
    """
    Evaluates if extreme heat and dangerous air quality occur simultaneously.
    Trigger: Temp >= 38 C AND AQI >= 150.
    Gracefully returns False if either signal is unavailable.
    """
    if cf.temp_c.source == "unavailable" or cf.aqi.source == "unavailable":
        return False
    
    if cf.temp_c.value is None or cf.aqi.value is None:
        return False
        
    try:
        temp = float(cf.temp_c.value)
        # cf.aqi.value is a dict: {"aqi": int, "dominant": str}
        aqi = int(cf.aqi.value.get("aqi", 0)) if isinstance(cf.aqi.value, dict) else int(cf.aqi.value)
        
        return temp >= 38.0 and aqi >= 150
    except (ValueError, TypeError, AttributeError):
        return False


def is_compound_driving_hazard(cf: ContextFrame) -> bool:
    """
    Evaluates if high precipitation and low visibility occur simultaneously.
    Trigger: Precip Probability >= 60% AND Visibility <= 1.0 km.
    Gracefully returns False if either signal is unavailable.
    """
    if cf.precip_prob_pct.source == "unavailable" or cf.visibility_km.source == "unavailable":
        return False
        
    if cf.precip_prob_pct.value is None or cf.visibility_km.value is None:
        return False
        
    try:
        precip = float(cf.precip_prob_pct.value)
        vis = float(cf.visibility_km.value)
        
        return precip >= 60.0 and vis <= 1.0
    except (ValueError, TypeError):
        return False
