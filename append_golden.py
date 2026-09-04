import json

with open("eval/golden_set.json", "r") as f:
    data = json.load(f)

# 1. Traveler Scenario
data.append({
    "id": "tr_destination_alert",
    "type": "persona_traveler",
    "persona": "traveler",
    "context": {
      "personas": ["traveler"],
      "health_flags": [],
      "has_declared_profile": True,
      "local_time": "2026-08-28T08:00:00Z",
      "is_commute_window": False,
      "is_daylight": True,
      "lat": 28.6,
      "lon": 77.2,
      "temp_c": {"value": 22, "source": "fixture", "confidence": 1.0, "freshness_min": 0},
      "aqi": {"value": 40, "source": "fixture", "confidence": 1.0, "freshness_min": 0},
      "precip_prob_pct": {"value": 0, "source": "fixture", "confidence": 1.0, "freshness_min": 0},
      "uv": {"value": 3, "source": "fixture", "confidence": 1.0, "freshness_min": 0},
      "wind_kmh": {"value": 10, "source": "fixture", "confidence": 1.0, "freshness_min": 0},
      "warnings": [],
      "destinations": [
        {
          "lat": 10, "lon": 10,
          "warnings": [{"severity": "red", "type": "flood", "text": "Flood Warning"}]
        },
        {
          "lat": 20, "lon": 20,
          "warnings": [{"severity": "yellow", "type": "wind", "text": "High Wind"}]
        }
      ]
    },
    "expected_top_card": "destination_alert",
    "rationale": "Traveler persona with 2+ destination warnings triggers P2 alert prioritized over general conditions"
})

# 2. Commuter Scenario
data.append({
    "id": "co_low_visibility",
    "type": "persona_commuter",
    "persona": "commuter",
    "context": {
      "personas": ["commuter"],
      "health_flags": [],
      "has_declared_profile": True,
      "local_time": "2026-08-28T08:00:00Z",
      "is_commute_window": True,
      "is_daylight": True,
      "lat": 28.6,
      "lon": 77.2,
      "temp_c": {"value": 22, "source": "fixture", "confidence": 1.0, "freshness_min": 0},
      "aqi": {"value": 40, "source": "fixture", "confidence": 1.0, "freshness_min": 0},
      "precip_prob_pct": {"value": 0, "source": "fixture", "confidence": 1.0, "freshness_min": 0},
      "uv": {"value": 3, "source": "fixture", "confidence": 1.0, "freshness_min": 0},
      "wind_kmh": {"value": 10, "source": "fixture", "confidence": 1.0, "freshness_min": 0},
      "warnings": [],
      "visibility_km": {"value": 0.5, "source": "fixture", "confidence": 1.0, "freshness_min": 0}
    },
    "expected_top_card": "visibility_commute",
    "rationale": "Commuter persona with <1.5km visibility during commute triggers P1 alert"
})

with open("eval/golden_set.json", "w") as f:
    json.dump(data, f, indent=2)
