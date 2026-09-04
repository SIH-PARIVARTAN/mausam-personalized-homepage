import os
import datetime
from adapters.forecast_adapter import ForecastAdapter
from adapters.warning_adapter import WarningAdapter
from adapters.sun_adapter import SunAdapter

def test_forecast_fixture():
    os.environ["FIXTURE_SCENARIO"] = "normal"
    now = datetime.datetime.now()
    adapter = ForecastAdapter()
    res = adapter.fetch(10.0, 10.0, datetime.datetime.now())
    # Should yield t, h, w, p, v, soil, ext = 7 items
    assert len(res) == 7
    assert res[0].confidence == 1.0
    assert res[1].confidence == 1.0
    assert res[2].confidence == 1.0
    assert res[3].confidence == 1.0
    assert res[4].confidence == 1.0
    assert res[5].confidence == 1.0
    assert isinstance(res[6], list)

    os.environ["FIXTURE_SCENARIO"] = "invalid_scenario_file"
    t, h, w, p, _v, _soil, _ext = adapter.fetch(18.5, 73.8, now)
    assert t.source == "unavailable"

def test_warning_fixture():
    os.environ["FIXTURE_SCENARIO"] = "severe_warning"
    now = datetime.datetime.now()
    adapter = WarningAdapter()
    data = adapter.fetch(18.5, 73.8, now)
    assert isinstance(data, list)
    assert len(data) > 0

def test_sun_fixture():
    # Requires absolute coordinates math which depends on location
    now = datetime.datetime.now()
    adapter = SunAdapter()
    sr, ss = adapter.fetch(18.5, 73.8, now)
    assert sr.source == "live"
    assert sr.confidence == 1.0
