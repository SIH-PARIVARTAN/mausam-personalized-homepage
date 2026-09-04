import datetime
from backend.deps import build_context_frame
from engine.models import MAX_DESTINATIONS_FETCHED

def test_deps_destination_truncation(monkeypatch):
    prefs = {
        "personas": ["traveler"],
        "saved_locations": [{"lat": float(i), "lon": float(i)} for i in range(MAX_DESTINATIONS_FETCHED + 5)]
    }
    from adapters.forecast_adapter import ForecastAdapter
    from adapters.warning_adapter import WarningAdapter

    def fake_forecast(self, lat, lon, when):
        from engine.models import SignalValue
        return (
            SignalValue(20.0, "simulated", 0, 0.7), 
            SignalValue(50, "simulated", 0, 0.7), 
            SignalValue(10, "simulated", 0, 0.7), 
            SignalValue(10, "simulated", 0, 0.7), 
            SignalValue(8.0, "simulated", 0, 0.7),
            SignalValue(None, "unavailable", 0, 0.0),
            []
        )

    monkeypatch.setattr(ForecastAdapter, "fetch", fake_forecast)
    monkeypatch.setattr(WarningAdapter, "fetch", lambda *args, **kwargs: [])

    cf = build_context_frame(prefs, lat=0.0, lon=0.0, when=datetime.datetime.now())
    
    # Must enforce constraint
    assert len(cf.destinations) == MAX_DESTINATIONS_FETCHED
