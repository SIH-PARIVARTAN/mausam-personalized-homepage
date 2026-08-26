from fastapi import APIRouter
from backend.db import get_connection
import json, datetime
from backend.models_api import PreferencesBody

router = APIRouter()

@router.get("/preferences")
def read_preferences(device_id: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM preferences WHERE device_id=%s", (device_id,))
            row = cur.fetchone()
            if row is None:
                return {"device_id": device_id, "personas": ["default_general"], "health_flags": [], "saved_locations": []}
            return {
                "device_id": row[0],
                "personas": json.loads(row[1]),
                "health_flags": json.loads(row[2]),
                "saved_locations": json.loads(row[3] or "[]"),
            }

@router.put("/preferences")
def write_preferences(body: PreferencesBody):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO preferences (device_id, personas, health_flags, saved_locations, updated_at)
                   VALUES (%s, %s, %s, %s, %s)
                   ON CONFLICT(device_id) DO UPDATE SET
                     personas=EXCLUDED.personas, health_flags=EXCLUDED.health_flags,
                     saved_locations=EXCLUDED.saved_locations, updated_at=EXCLUDED.updated_at""",
                (body.device_id, json.dumps(body.personas), json.dumps(body.health_flags),
                 json.dumps(body.saved_locations), datetime.datetime.utcnow().isoformat()),
            )
        conn.commit()
    return {"status": "ok"}
