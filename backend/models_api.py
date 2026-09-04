from pydantic import BaseModel, Field, StringConstraints
from typing import Annotated

from enum import Enum

class PersonaEnum(str, Enum):
    health = "health"
    fitness = "fitness"
    family = "family"
    traveler = "traveler"
    commuter = "commuter"
    agriculture = "agriculture"
    beachgoer = "beachgoer"
    event_planner = "event_planner"
    default_general = "default_general"

class HealthFlagEnum(str, Enum):
    respiratory_sensitive = "respiratory_sensitive"
    heat_sensitive = "heat_sensitive"
    pollen_interest = "pollen_interest"

class PreferencesBody(BaseModel):
    # Regex accepts UUIDv4 OR legacy 28-char alphanumeric Firebase UID to gracefully support both test and UI contracts.
    device_id: Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_-]{28}$|^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")]
    personas: list[PersonaEnum] = Field(default=[], max_length=20)
    health_flags: list[HealthFlagEnum] = Field(default=[], max_length=20)
    saved_locations: list[dict] = Field(default=[], max_length=20)

class SignalRef(BaseModel):
    signal: str
    value: int | float | str | None
    source: str

class WarningResponse(BaseModel):
    severity: str
    type: str
    text: str

class CardResponse(BaseModel):
    card_id: str
    title: str
    priority: str
    is_alert: bool
    value_summary: str
    source: str
    freshness_badge: str | None = None
    explanation_ref: str

class HomepageResponse(BaseModel):
    context_snapshot_id: str
    generated_at: str
    cards: list[CardResponse]
    warnings_override: list[WarningResponse] = []
    system_notice: str | None = None

class ScoreComponentsRef(BaseModel):
    persona_weight: float
    urgency_multiplier: float
    confidence_factor: float

class ExplainResponse(BaseModel):
    explanation_ref: str
    text: str
    signal_refs: list[SignalRef]
    score_components: ScoreComponentsRef
