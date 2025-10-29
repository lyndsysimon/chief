from ChatAssistant.brain.intent_classifier import (
    IntentType,
    classify_intent,
)


def test_detects_mode_switch_keywords() -> None:
    assert classify_intent("Please switch mode") is IntentType.MODE_SWITCH


def test_detects_reference_keywords() -> None:
    assert classify_intent("What's my flap rip speed?") is IntentType.REFERENCE


def test_detects_telemetry_keywords() -> None:
    assert classify_intent("fuel status") is IntentType.TELEMETRY


def test_defaults_to_general() -> None:
    assert classify_intent("hello") is IntentType.GENERAL
