from chief.core.state_manager import AssistantState
from chief.core.telemetry_reader import TelemetryReader


class DummyState(AssistantState):
    def __init__(self) -> None:
        super().__init__("/nonexistent/config.json")

    def _persist_config(self) -> None:  # type: ignore[override]
        pass


def test_normalize_snapshot_handles_multiple_fields() -> None:
    state = DummyState()
    reader = TelemetryReader(state)

    raw = {
        "name": "F-16A",
        "fuel": 0.5,
        "speed": {"kmh": 900},
        "pitch": 10,
        "roll": -2,
        "aoa": 12,
        "altitude": 4500,
        "g_force": 5.2,
        "ammo": 120,
        "gear": "up",
        "flaps": "combat",
        "damage": {"left_wing": "yellow"},
        "temperatures": {"oil": 80},
    }

    normalized = reader._normalize_snapshot(raw)

    assert normalized == {
        "vehicle": "F-16A",
        "fuel_percent": 50.0,
        "ias_kmh": 900,
        "pitch_deg": 10,
        "roll_deg": -2,
        "aoa_deg": 12,
        "altitude_m": 4500,
        "g_load": 5.2,
        "ammo": 120,
        "gear_state": "up",
        "flap_state": "combat",
        "damage": {"left_wing": "yellow"},
        "temperatures_c": {"oil": 80},
    }


def test_normalize_snapshot_handles_alternate_fields() -> None:
    state = DummyState()
    reader = TelemetryReader(state)

    raw = {
        "plane_name": "F-4E",
        "fuel": 87,
        "ias": 750,
        "g_force": None,
    }

    normalized = reader._normalize_snapshot(raw)

    assert normalized["vehicle"] == "F-4E"
    assert normalized["fuel_percent"] == 87
    assert normalized["ias_kmh"] == 750
    assert normalized["g_load"] is None
