from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Dict, Any
import datetime
import uuid
import pytz

from backend.db import get_connection
from backend.deps import build_context_frame
from engine.engine import rank
from backend.models_api import HomepageResponse, CardResponse, WarningResponse
import json
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter()

# Simple global dict for explain references in single process runtime
explain_db = {}

def get_preferences(device_id: str) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT personas, health_flags, saved_locations FROM preferences WHERE device_id = %s
            """, (device_id,))
            row = cur.fetchone()
            if row:
                return {
                    "personas": json.loads(row[0]),
                    "health_flags": json.loads(row[1]),
                    "saved_locations": json.loads(row[2] or "[]")
                }
            return {
                "personas": ["default_general"],
                "health_flags": [],
                "saved_locations": []
            }

@router.get("/homepage", response_model=HomepageResponse)
async def homepage(
    device_id: str = Query(..., pattern=r"^[a-zA-Z0-9_-]{28}$|^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"),
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180)
):
    if not device_id.strip():
        raise HTTPException(status_code=422, detail="device_id required")

    start_time = time.time()
    prefs = get_preferences(device_id)
    now_ist = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))

    # Assemble context via adapters
    cf = build_context_frame(prefs, lat, lon, now_ist)

    # Run the engine
    engine_output = rank(cf)

    ctx_id = uuid.uuid4().hex[:8]
    context_snapshot_id = f"ctx_{ctx_id}"

    # Format cards
    display_titles = {
        # Original 8 entries
        "severe_warning":           "Severe Weather Warning",
        "aqi_health":               "Air Quality",
        "uv_sun_exposure":          "UV Index",
        "activity_window":          "Activity Window",
        "rain_commute":             "Rain & Commute",
        "sunrise_sunset":           "Daylight Hours",
        "general_conditions":       "General Conditions",
        "pollen_illustrative":      "Pollen Levels",
        # GAP-01 / display patch (2026-09-05): 7 missing persona-specific cards
        "compound_heat_aqi_danger": "Extreme Heat & Air Quality Danger",
        "compound_driving_hazard":  "Driving Hazard Alert",
        "visibility_commute":       "Low Visibility Commute",
        "destination_alert":        "Destination Weather Alert",
        "agriculture_advisory":     "Agriculture Advisory",
        "marine_conditions_alert":  "Marine Conditions Alert",
        "event_outlook":            "Event Weather Outlook",
    }

    cards = []
    for rc in engine_output.ranked_cards:
        exp_id = f"exp_{rc.card_id}_{ctx_id}"

        # Populate explanation DB
        explain_db[exp_id] = {
            "text": rc.explanation_text,
            "signal_refs": [{"signal": sr.get("signal", ""), "value": sr.get("value"), "source": sr.get("source", "simulated")} for sr in rc.signal_refs],
            "score_components": {
                "persona_weight": rc.score_components.get("persona_weight", 1.0),
                "urgency_multiplier": rc.score_components.get("urgency_multiplier", 1.0),
                "confidence_factor": rc.score_components.get("confidence_factor", 1.0)
            }
        }

        val_summary = rc.explanation_text.split(" — ")[0] if " — " in rc.explanation_text else rc.explanation_text

        c_res = CardResponse(
            card_id=rc.card_id,
            title=display_titles.get(rc.card_id, "Mausam Info"),
            priority=rc.priority,
            is_alert=rc.is_alert,
            value_summary=val_summary,
            source=rc.signal_refs[0].get("source", "simulated") if rc.signal_refs else "simulated",
            freshness_badge=None,
            explanation_ref=exp_id
        )
        cards.append(c_res)

    warnings_override = []
    for w_card in engine_output.override_warnings:
        w = w_card.signal_refs[0].get("value", {}) if w_card.signal_refs else {}
        if w:
            warnings_override.append(WarningResponse(
                severity=w.get("severity", "severe"),
                type=w.get("type", "Unknown"),
                text=w.get("text", "")
            ))

    # Identify if everything is unavailable
    # The engine guarantees at least one card (general_conditions) for fallback,
    # so we must check if all output sources are unavailable.
    all_unavailable = True
    if engine_output.override_warnings:
        all_unavailable = False
    else:
        for rc in engine_output.ranked_cards:
            if rc.card_id in ["sunrise_sunset", "general_conditions"]:
                continue
            if rc.signal_refs:
                for sr in rc.signal_refs:
                    if sr.get("source") != "unavailable":
                        all_unavailable = False
                        break

    system_notice = "All data sources unavailable. Displaying degraded view." if all_unavailable else None

    elapsed = time.time() - start_time
    if all_unavailable:
        logger.warning(f"Resolved /homepage in {elapsed*1000:.0f}ms WITH DEGRADATION (all sources unavailable)")
    else:
        logger.info(f"Resolved /homepage in {elapsed*1000:.0f}ms (is_alert={any(c.is_alert for c in cards)})")

    return HomepageResponse(
        context_snapshot_id=context_snapshot_id,
        generated_at=now_ist.isoformat(),
        cards=cards,
        warnings_override=warnings_override,
        system_notice=system_notice
    )
