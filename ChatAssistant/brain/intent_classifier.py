"""Very small heuristic intent classifier."""
from __future__ import annotations

from enum import Enum, auto


class IntentType(Enum):
    TELEMETRY = auto()
    REFERENCE = auto()
    MODE_SWITCH = auto()
    GENERAL = auto()


TELEMETRY_KEYWORDS = {"fuel", "g", "temperature", "damage", "status", "aoa", "speed"}
REFERENCE_KEYWORDS = {"flap", "gear", "rip", "limit", "wing"}
MODE_SWITCH_KEYWORDS = {"switch", "mode"}


def classify_intent(text: str) -> IntentType:
    lowered = text.lower()
    if any(word in lowered for word in MODE_SWITCH_KEYWORDS):
        return IntentType.MODE_SWITCH
    if any(word in lowered for word in REFERENCE_KEYWORDS):
        return IntentType.REFERENCE
    if any(word in lowered for word in TELEMETRY_KEYWORDS):
        return IntentType.TELEMETRY
    return IntentType.GENERAL
