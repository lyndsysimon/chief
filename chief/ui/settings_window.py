"""Settings UI stub."""
from __future__ import annotations

import logging

from ..brain.prompt_presets import PromptMode
from ..core.state_manager import AssistantState

LOGGER = logging.getLogger(__name__)


class SettingsWindow:
    """Represents the configuration window shown from the tray icon."""

    def __init__(self, state: AssistantState) -> None:
        self._state = state

    def show(self) -> None:
        LOGGER.info("Settings window (stub)")
        LOGGER.info("Wake word: %s", self._state.get_wake_word())
        LOGGER.info("Hotkey: %s", self._state.get_hotkey())
        LOGGER.info("Prompt mode: %s", self._state.get_prompt_mode())
        LOGGER.info("STT backend: %s", self._state.get_stt_backend())
        LOGGER.info("TTS backend: %s", self._state.get_tts_backend())

    def update_wake_word(self, wake_word: str) -> None:
        self._state.set_wake_word(wake_word)

    def update_hotkey(self, hotkey: str) -> None:
        self._state.set_hotkey(hotkey)

    def update_mode(self, mode: PromptMode) -> None:
        self._state.set_prompt_mode(mode)

    def update_stt_backend(self, backend: str) -> None:
        self._state.set_stt_backend(backend)

    def update_tts_backend(self, backend: str) -> None:
        self._state.set_tts_backend(backend)
