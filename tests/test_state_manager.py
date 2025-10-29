import json
from pathlib import Path

import pytest

from ChatAssistant.brain.prompt_presets import PromptMode
from ChatAssistant.core.state_manager import AssistantState


@pytest.fixture()
def config_path(tmp_path: Path) -> Path:
    return tmp_path / "config.json"


def test_initializes_with_defaults_when_config_missing(config_path: Path) -> None:
    state = AssistantState(str(config_path))

    assert state.get_wake_word() == "chief"
    assert state.get_hotkey() == "capslock+q"
    assert state.get_prompt_mode() == PromptMode.CREW_CHIEF
    assert state.get_stt_backend() == "whisper"
    assert state.get_tts_backend() == "windows_sapi"


def test_updates_and_returns_copy_of_snapshot(config_path: Path) -> None:
    state = AssistantState(str(config_path))
    payload = {"fuel_percent": 42}

    state.update_telemetry_snapshot(payload)
    returned = state.get_telemetry_snapshot()

    assert returned == payload

    payload["fuel_percent"] = 1
    assert state.get_telemetry_snapshot()["fuel_percent"] == 42


def test_persists_changes_to_config_file(config_path: Path) -> None:
    state = AssistantState(str(config_path))

    state.set_wake_word("raven")
    state.set_hotkey("ctrl+alt+s")
    state.set_prompt_mode(PromptMode.INSTRUCTOR)
    state.set_stt_backend("test_stt")
    state.set_tts_backend("test_tts")

    data = json.loads(config_path.read_text(encoding="utf-8"))
    assert data == {
        "wake_word": "raven",
        "hotkey": "ctrl+alt+s",
        "prompt_mode": PromptMode.INSTRUCTOR.value,
        "stt_backend": "test_stt",
        "tts_backend": "test_tts",
    }


def test_loads_defaults_when_config_invalid(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text("{invalid json]", encoding="utf-8")

    state = AssistantState(str(config_path))

    assert state.get_wake_word() == "chief"
    assert state.get_prompt_mode() == PromptMode.CREW_CHIEF


def test_toggle_mode_from_command_switches_modes(config_path: Path) -> None:
    state = AssistantState(str(config_path))

    mode = state.toggle_mode_from_command("Please switch to instructor mode")
    assert mode == PromptMode.INSTRUCTOR
    assert state.get_prompt_mode() == PromptMode.INSTRUCTOR

    mode = state.toggle_mode_from_command("back to crew chief")
    assert mode == PromptMode.CREW_CHIEF
    assert state.get_prompt_mode() == PromptMode.CREW_CHIEF
