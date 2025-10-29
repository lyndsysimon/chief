import json
from pathlib import Path

from chief.brain.responder import TelemetryResponder
from chief.core.reference_data import ReferenceDataRegistry
from chief.core.state_manager import AssistantState


def make_state(tmp_path: Path) -> AssistantState:
    return AssistantState(str(tmp_path / "config.json"))


def test_generate_telemetry_only_response_formats_values(tmp_path: Path) -> None:
    state = make_state(tmp_path)
    state.update_telemetry_snapshot(
        {
            "fuel_percent": 34,
            "ias_kmh": 820,
            "aoa_deg": 12,
            "g_load": 7.2,
            "g_status": "HIGH",
            "damage": {"left_wing": "yellow"},
        }
    )
    responder = TelemetryResponder(state, ReferenceDataRegistry(str(tmp_path)))

    response = responder.generate_telemetry_only_response()

    assert "Fuel: 34%" in response
    assert "IAS: 820 km/h" in response
    assert "AoA: 12°" in response
    assert "G-load: 7.2 (HIGH)" in response
    assert "Left Wing: yellow" in response


def test_generate_telemetry_only_response_handles_missing_data(tmp_path: Path) -> None:
    state = make_state(tmp_path)
    responder = TelemetryResponder(state, ReferenceDataRegistry(str(tmp_path)))

    assert responder.generate_telemetry_only_response() == "No data"


def test_build_context_messages_combines_telemetry_and_reference(tmp_path: Path) -> None:
    state = make_state(tmp_path)
    state.update_telemetry_snapshot({"vehicle": "F-16A", "fuel_percent": 55})

    ref_dir = tmp_path / "ref"
    ref_dir.mkdir()
    (ref_dir / "f-16a.json").write_text(json.dumps({"flaps": "450 km/h"}), encoding="utf-8")

    responder = TelemetryResponder(state, ReferenceDataRegistry(str(ref_dir)))

    messages = responder.build_context_messages()

    assert messages == [
        {"role": "assistant", "content": "Telemetry: vehicle: F-16A, fuel_percent: 55"},
        {"role": "assistant", "content": "Reference: flaps: 450 km/h"},
    ]
