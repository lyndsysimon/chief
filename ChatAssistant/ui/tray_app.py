"""System tray application shell."""
from __future__ import annotations

import logging
from typing import Optional

from ..brain.prompt_presets import PromptMode
from ..core.state_manager import AssistantState
from .settings_window import SettingsWindow

LOGGER = logging.getLogger(__name__)


class TrayApplication:
    """Placeholder implementation for a Windows tray icon."""

    def __init__(self, state: AssistantState) -> None:
        self._state = state
        self._window: Optional[SettingsWindow] = None

    def run(self) -> None:
        LOGGER.info("Tray application running (stub)")
        LOGGER.info("Current wake word: %s", self._state.get_wake_word())
        LOGGER.info("Current hotkey: %s", self._state.get_hotkey())
        LOGGER.info("Current mode: %s", self._state.get_prompt_mode())
        LOGGER.info("Invoke SettingsWindow.show() to open configuration UI")

    def open_settings(self) -> None:
        if self._window is None:
            self._window = SettingsWindow(state=self._state)
        self._window.show()

    def update_mode(self, mode: PromptMode) -> None:
        self._state.set_prompt_mode(mode)
