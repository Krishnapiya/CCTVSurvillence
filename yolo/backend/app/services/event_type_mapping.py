"""
Map surveillance event `type` values to CCTV Master `event_code` values.

Master codes are defined in the CCTV Master project config.yaml under event_types.
Surveillance-only types with no master equivalent are mapped to None (skip sync or extend master later).
"""

from __future__ import annotations

# surveillance type (lowercase) -> master event_code
SURVEILLANCE_TO_MASTER_EVENT_CODE: dict[str, str | None] = {
    # Direct / close matches
    "fainting": "FAINTING",
    "smoke": "SMOKE_DET",
    "projectile": "PROJECTILE",
    "intrusion": "INTRUSION",
    "human_detection": "INTRUSION",
    "uniform_violation": "GROUP_NO_UNIFORM",
    # Surveillance types without a dedicated master code yet
    "fire": "SMOKE_DET",  # nearest master category; add FIRE_DET on master if needed
    "fight": None,
    "suicide_risk": None,
    "smoking": None,
    "mobile_usage": None,
    "bag": None,
    "bench": None,
}

# Human-readable labels for surveillance UI (optional reference)
SURVEILLANCE_EVENT_LABELS: dict[str, str] = {
    "fire": "Fire Detection",
    "smoke": "Smoke Detection",
    "intrusion": "Intrusion",
    "human_detection": "Human Detection",
    "mobile_usage": "Mobile Phone Detection",
    "bag": "Bag Detection",
    "bench": "Bench Detection",
    "fainting": "Fainting Detection",
    "fight": "Fight Detection",
    "suicide_risk": "Suicide Risk",
    "projectile": "Projectile",
    "uniform_violation": "Uniform Violation",
    "smoking": "Smoking Detection",
}


def map_to_master_event_code(surveillance_type: str) -> str | None:
    """Return master event_code for a surveillance event type, or None if not syncable."""
    if not surveillance_type:
        return None
    return SURVEILLANCE_TO_MASTER_EVENT_CODE.get(surveillance_type.lower().strip())


def is_syncable_event_type(surveillance_type: str) -> bool:
    return map_to_master_event_code(surveillance_type) is not None
