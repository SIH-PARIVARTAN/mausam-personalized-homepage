import json, os

os.makedirs('eval', exist_ok=True)

def mkw(persona, temp, aqi, prec, uv=2, wind=10, commute=False, missing=False, warn=None):
    w = []
    if warn:
        w.append({"type": warn["t"], "severity": warn["s"], "title": warn["tit"], "description": "...", "onset": "2026-08-28T00:00:00Z", "expires": "2026-08-29T00:00:00Z", "source": "fixture"})

    # Missing vectors
    if missing == "aqi": aqi = None
    elif missing == "all": aqi, uv, prec, temp, wind = None, None, None, None, None

    aqiv = {"value": aqi, "source": "fixture", "confidence": 1.0, "freshness_min": 0} if aqi is not None else {"value": None, "source": "unavailable", "confidence": 0.0, "freshness_min": None}
    uvv = {"value": uv, "source": "fixture", "confidence": 1.0, "freshness_min": 0} if uv is not None else {"value": None, "source": "unavailable", "confidence": 0.0, "freshness_min": None}
    precv = {"value": prec, "source": "fixture", "confidence": 1.0, "freshness_min": 0} if prec is not None else {"value": None, "source": "unavailable", "confidence": 0.0, "freshness_min": None}
    tempv = {"value": temp, "source": "fixture", "confidence": 1.0, "freshness_min": 0} if temp is not None else {"value": None, "source": "unavailable", "confidence": 0.0, "freshness_min": None}
    windv = {"value": wind, "source": "fixture", "confidence": 1.0, "freshness_min": 0} if wind is not None else {"value": None, "source": "unavailable", "confidence": 0.0, "freshness_min": None}

    return {
        "personas": [persona],
        "health_flags": [],
        "has_declared_profile": persona != "default_general",
        "local_time": "2026-08-28T08:00:00Z",
        "is_commute_window": commute,
        "is_daylight": True,
        "lat": 28.6, "lon": 77.2,
        "temp_c": tempv,
        "aqi": aqiv,
        "precip_prob_pct": precv,
        "uv": uvv,
        "wind_kmh": windv,
        "warnings": w
    }

scenarios = [
    # --- C1: Cold Starts ---
    {"id": "cs_nice",       "type": "cold_start", "persona": "default_general", "context": mkw("default_general", 22, 40, 0, 3, 10, False), "expected_top_card": "general_conditions", "rationale": "Base weight 0.7 wins over AQI 0.6 on mild weather"},
    {"id": "cs_rain",       "type": "cold_start", "persona": "default_general", "context": mkw("default_general", 22, 40, 80, 3, 10, False), "expected_top_card": "general_conditions", "rationale": "Outside commute, rain threshold 1.3x0.4 = 0.52 < 0.7"},
    {"id": "cs_commute",    "type": "cold_start", "persona": "default_general", "context": mkw("default_general", 18, 40, 80, 2, 10, True),  "expected_top_card": "rain_commute", "rationale": "Commute + Rain = 2.35x0.4 = 0.94 wins over general 0.7"},
    {"id": "cs_heat",       "type": "cold_start", "persona": "default_general", "context": mkw("default_general", 42, 40, 0, 5, 10, False),  "expected_top_card": "general_conditions", "rationale": "Heat boosts general to 1.3"},
    {"id": "cs_missing",    "type": "missing_data","persona": "default_general", "context": mkw("default_general", 20, 50, 0, missing="all"), "expected_top_card": "general_conditions", "rationale": "Universal fallback card"},

    # --- C2: P0 Overrides ---
    {"id": "p0_flood_health", "type": "p0_override", "persona": "health", "context": mkw("health", 25, 40, 90, warn={"t": "flood", "s": "severe", "tit": "Flood"}), "expected_top_card": "severe_warning"},
    {"id": "p0_cyc_fit",      "type": "p0_override", "persona": "fitness", "context": mkw("fitness", 25, 40, 90, warn={"t": "cyclone", "s": "severe", "tit": "Cyc"}), "expected_top_card": "severe_warning"},
    {"id": "p0_heat_fam",     "type": "p0_override", "persona": "family", "context": mkw("family", 45, 40, 0, warn={"t": "heat", "s": "severe", "tit": "Heat"}), "expected_top_card": "severe_warning"},

    # --- C3: Mild / Normal Differentiation ---
    {"id": "mild_health",   "type": "normal", "persona": "health", "context": mkw("health", 22, 50, 0, 3), "expected_top_card": "aqi_health", "rationale": "Highest base weight (0.9)"},
    {"id": "mild_fitness",  "type": "normal", "persona": "fitness", "context": mkw("fitness", 22, 50, 0, 3), "expected_top_card": "activity_window", "rationale": "Highest base weight (0.95) over UV(0.9)"},
    {"id": "mild_family",   "type": "normal", "persona": "family", "context": mkw("family", 22, 50, 0, 3), "expected_top_card": "rain_commute", "rationale": "Highest base weight (0.95)"},
    {"id": "mild_sun_gen",  "type": "normal", "persona": "default_general", "context": mkw("default_general", 22, 40, 0, 3), "expected_top_card": "general_conditions"},

    # --- C4: Missing/Degraded Data ---
    {"id": "miss_aqi_hlt",  "type": "missing_data", "persona": "health", "context": mkw("health", 25, 50, 0, 3, missing="aqi"), "expected_top_card": "uv_sun_exposure", "rationale": "AQI drops, UV becomes highest available"},
    {"id": "miss_all_fit",  "type": "missing_data", "persona": "fitness", "context": mkw("fitness", 25, 50, 0, missing="all"), "expected_top_card": "sunrise_sunset", "rationale": "Sunrise (0.5) beats General (0.5), tiebreaker order"},

    # --- C5: Severe Environmental Floors ---
    {"id": "sev_aqi_hlt",   "type": "thresholds", "persona": "health",  "context": mkw("health", 25, 350, 0), "expected_top_card": "aqi_health"},
    {"id": "sev_aqi_fam",   "type": "thresholds", "persona": "family",  "context": mkw("family", 25, 350, 0), "expected_top_card": "aqi_health", "rationale": "Urgency (2.5) pushes AQI over family's baseline Rain preference"},
    {"id": "ext_uv_fit",    "type": "thresholds", "persona": "fitness", "context": mkw("fitness", 25, 50, 0, 12), "expected_top_card": "uv_sun_exposure", "rationale": "UV (2.2 * 0.9 = 1.98) beats ActWindow (1.8 * 0.95 = 1.71)"},
    {"id": "mod_dry_fam",   "type": "thresholds", "persona": "family",  "context": mkw("family", 22, 50, 10, commute=True), "expected_top_card": "rain_commute"},

    # --- C6: Conflicting Multipliers ---
    {"id": "con_fit_aqi_uv","type": "conflict", "persona": "fitness", "context": mkw("fitness", 25, 160, 0, 9), "expected_top_card": "activity_window", "rationale": "Activity Window (1.8 * 0.95 = 1.71) beats UV (1.8 * 0.9 = 1.62)"},
    {"id": "con_hlt_aqi_rn","type": "conflict", "persona": "health",  "context": mkw("health", 25, 160, 90, commute=True), "expected_top_card": "aqi_health", "rationale": "AQI (1.8*0.9 = 1.62) beats Rain (2.35*0.3 = 0.70)"},
    {"id": "con_fam_aqi_rn","type": "conflict", "persona": "family",  "context": mkw("family", 25, 160, 90, commute=True), "expected_top_card": "rain_commute", "rationale": "Rain (2.35*0.95 = 2.23) beats AQI (1.8*0.4 = 0.72)"},
    {"id": "con_hlt_heat",  "type": "conflict", "persona": "health",  "context": mkw("health", 41, 50, 0), "expected_top_card": "aqi_health", "rationale": "General Heat (1.3*0.5 = 0.65) still loses to base AQI (0.9)"},
    {"id": "con_fit_heat",  "type": "conflict", "persona": "fitness", "context": mkw("fitness", 41, 50, 0), "expected_top_card": "activity_window", "rationale": "Heat makes window 'bad' -> 1.8 * 0.95 = 1.71"},

    # --- C7: Boundaries ---
    {"id": "bnd_aqi_149",   "type": "boundary", "persona": "default_general", "context": mkw("default_general", 22, 149, 0), "expected_top_card": "aqi_health", "rationale": "1.3 * 0.6 = 0.78 > 0.7"},
    {"id": "bnd_mod_wthr",  "type": "boundary", "persona": "fitness", "context": mkw("fitness", 22, 110, 0, 6), "expected_top_card": "activity_window", "rationale": "Moderate boosts window"}
]

with open('eval/golden_set.json', 'w') as f:
    json.dump(scenarios, f, indent=2)

print(f"Golden set built with {len(scenarios)} scenarios.")
