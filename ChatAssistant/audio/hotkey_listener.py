"""Global hotkey listener stub."""
from __future__ import annotations

import logging
import time
from typing import Callable

LOGGER = logging.getLogger(__name__)


class GlobalHotkeyListener:
    """Listens for a configurable keyboard shortcut to trigger the assistant."""

    def __init__(self, hotkey_provider: Callable[[], str], on_trigger: Callable[[], None]) -> None:
        self._hotkey_provider = hotkey_provider
        self._on_trigger = on_trigger

    def run_forever(self) -> None:
        LOGGER.info("Hotkey listener running (stub mode)")
        while True:
            time.sleep(1.0)
            LOGGER.debug("Waiting for hotkey: %s", self._hotkey_provider())

    def simulate_trigger(self) -> None:
        LOGGER.info("Hotkey manually triggered")
        self._on_trigger()
