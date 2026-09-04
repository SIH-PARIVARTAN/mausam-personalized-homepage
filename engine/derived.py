"""
engine/derived.py

Mathematical computations for derived environmental signals.
Ensures deterministic reasoning inside the Phase C domains without live ML/LLMs.
"""

def calculate_comfort_index(temp_c: float | int | None, humidity_pct: float | int | None) -> float | None:
    """
    Computes a simplified continuous comfort index based on Thom's Discomfort Index.
    Lower index = more comfortable (typically).
    
    Formula: DI = T - (0.55 - 0.0055 * RH) * (T - 14.5)
    If temp or humidity is unavailable, returns None.
    """
    if temp_c is None or humidity_pct is None:
        return None
        
    t = float(temp_c)
    h = float(humidity_pct)
    
    di = t - (0.55 - 0.0055 * h) * (t - 14.5)
    return round(di, 2)

def is_frost_warning(temp_c: float | int | None) -> bool:
    """
    Determines if frost conditions are actively viable (< 2.0C).
    Returns False if temp_c is unavailable.
    """
    if temp_c is None:
        return False
        
    return float(temp_c) < 2.0
