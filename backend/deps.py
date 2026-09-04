import datetime
from fastapi import HTTPException
from engine.models import ContextFrame, SignalValue
from adapters.forecast_adapter import ForecastAdapter
from adapters.warning_adapter import WarningAdapter
from adapters.sun_adapter import SunAdapter
from adapters.aqi_adapter import AQIAdapter
from adapters.uv_adapter import UVAdapter
from adapters.marine_adapter import MarineAdapter

def build_context_frame(prefs: dict, lat: float, lon: float, when: datetime.datetime) -> ContextFrame:
    # 1. Compute time context
    # is_commute_window: 07:00–09:30 or 17:30–20:00 local time
    hour = when.hour
    minute = when.minute
    time_float = hour + (minute / 60.0)

    is_commute_window = (7.0 <= time_float <= 9.5) or (17.5 <= time_float <= 20.0)

    # 2-6. Call adapters
    t, h, w, p, v, soil_pct, ext_fc = ForecastAdapter().fetch(lat, lon, when)
    warnings = WarningAdapter().fetch(lat, lon, when)
    sr, ss = SunAdapter().fetch(lat, lon, when)
    aqi = AQIAdapter().fetch(lat, lon, when)
    uv = UVAdapter().fetch(lat, lon, when)
    wave_ht, water_t, tide_st = MarineAdapter().fetch(lat, lon, when)

    # is_daylight
    is_daylight = True
    if sr.value and ss.value:
        try:
            # simple comparison assuming sr and ss are "HH:MM"
            srh, srm = map(int, sr.value.split(":"))
            ssh, ssm = map(int, ss.value.split(":"))
            sr_f = srh + srm / 60.0
            ss_f = ssh + ssm / 60.0
            is_daylight = (sr_f <= time_float <= ss_f)
        except Exception:
            pass
    personas = prefs.get("personas", ["default_general"])
    if not personas:
        personas = ["default_general"]
    has_declared_profile = "default_general" not in personas
    
    # Phase B: Loop destinations safely up to MAX limit
    from engine.models import MAX_DESTINATIONS_FETCHED, DestinationContext
    from engine.derived import calculate_comfort_index, is_frost_warning

    saved_locations = prefs.get("saved_locations", [])
    destinations = []
    
    for loc in saved_locations[:MAX_DESTINATIONS_FETCHED]:
        d_lat = loc.get("lat")
        d_lon = loc.get("lon")
        if d_lat is not None and d_lon is not None:
            # Use deterministic adapter structure to avoid code-smell
            dw = WarningAdapter().fetch(float(d_lat), float(d_lon), when)
            dt, _h, _w, _p, _v, _soil, _ext = ForecastAdapter().fetch(float(d_lat), float(d_lon), when)
            destinations.append(
                DestinationContext(lat=float(d_lat), lon=float(d_lon), warnings=dw, temp_c=dt)
            )

    return ContextFrame(
        personas=personas,
        health_flags=prefs.get("health_flags", []),
        has_declared_profile=has_declared_profile,
        local_time=when.isoformat(),
        is_commute_window=is_commute_window,
        is_daylight=is_daylight,
        lat=lat,
        lon=lon,
        location_name="Unknown",
        temp_c=t,
        humidity_pct=h,
        wind_kmh=w,
        precip_prob_pct=p,
        visibility_km=v,
        warnings=warnings,
        aqi=aqi,
        uv=uv,
        destinations=destinations,
        soil_moisture_pct=soil_pct,
        frost_warning_active=is_frost_warning(t.value),
        planting_season_guidance="unavailable",
        wave_height_m=wave_ht,
        water_temp_c=water_t,
        tide_status=tide_st.value if tide_st.value else "unavailable",
        comfort_index=calculate_comfort_index(t.value, h.value),
        extended_forecast=ext_fc
    )
