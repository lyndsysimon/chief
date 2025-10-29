"""State container shared across background services."""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from ..brain.prompt_presets import PromptMode


class AssistantState:
    """Thread-safe state container.

    The state manager is responsible for holding the most recent telemetry
    snapshot, cached reference data, and user configuration such as wake word,
    hotkey, and prompt mode.
    """

    _DEFAULT_CONFIG = {
        "wake_word": "chief",
        "hotkey": "capslock+q",
        "prompt_mode": PromptMode.CREW_CHIEF.value,
        "stt_backend": "whisper",
        "tts_backend": "windows_sapi",
    }

    def __init__(self, config_path: str = "./chief/config.json") -> None:
        self._lock = threading.RLock()
        self._config_path = Path(config_path)
        self._config = self._load_config()
        self._telemetry_snapshot: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Telemetry snapshot
    # ------------------------------------------------------------------
    def update_telemetry_snapshot(self, snapshot: Dict[str, Any]) -> None:
        with self._lock:
            self._telemetry_snapshot = dict(snapshot)

    def get_telemetry_snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._telemetry_snapshot)

    # ------------------------------------------------------------------
    # Wake word configuration
    # ------------------------------------------------------------------
    def get_wake_word(self) -> str:
        with self._lock:
            return self._config.get("wake_word", "chief")

    def set_wake_word(self, value: str) -> None:
        with self._lock:
            self._config["wake_word"] = value
            self._persist_config()

    # ------------------------------------------------------------------
    # Hotkey configuration
    # ------------------------------------------------------------------
    def get_hotkey(self) -> str:
        with self._lock:
            return self._config.get("hotkey", "capslock+q")

    def set_hotkey(self, value: str) -> None:
        with self._lock:
            self._config["hotkey"] = value
            self._persist_config()

    # ------------------------------------------------------------------
    # Prompt mode configuration
    # ------------------------------------------------------------------
    def get_prompt_mode(self) -> Optional[PromptMode]:
        with self._lock:
            mode_value = self._config.get("prompt_mode")
        return PromptMode(mode_value) if mode_value else None

    def set_prompt_mode(self, mode: PromptMode) -> None:
        with self._lock:
            self._config["prompt_mode"] = mode.value
            self._persist_config()

    def toggle_mode_from_command(self, command_text: str) -> PromptMode:
        lowered = command_text.lower()
        if "instructor" in lowered:
            mode = PromptMode.INSTRUCTOR
        else:
            mode = PromptMode.CREW_CHIEF
        self.set_prompt_mode(mode)
        return mode

    # ------------------------------------------------------------------
    # Backend selection
    # ------------------------------------------------------------------
    def get_stt_backend(self) -> str:
        with self._lock:
            return self._config.get("stt_backend", "whisper")

    def set_stt_backend(self, backend: str) -> None:
        with self._lock:
            self._config["stt_backend"] = backend
            self._persist_config()

    def get_tts_backend(self) -> str:
        with self._lock:
            return self._config.get("tts_backend", "windows_sapi")

    def set_tts_backend(self, backend: str) -> None:
        with self._lock:
            self._config["tts_backend"] = backend
            self._persist_config()

    # ------------------------------------------------------------------
    # Config persistence
    # ------------------------------------------------------------------
    def _load_config(self) -> Dict[str, Any]:
        if not self._config_path.exists():
            return dict(self._DEFAULT_CONFIG)
        try:
            return json.loads(self._config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return dict(self._DEFAULT_CONFIG)

    def _persist_config(self) -> None:
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        self._config_path.write_text(json.dumps(self._config, indent=2), encoding="utf-8")
