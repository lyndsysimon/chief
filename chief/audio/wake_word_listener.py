"""Wake word listener stub.

In production this module would wrap Porcupine, Silero VAD+keyword spotting, or
any preferred detector. The class only exposes the interface expected by the
rest of the application so developers can plug in the actual engine.
"""
from __future__ import annotations

import logging
import time
from typing import Callable

LOGGER = logging.getLogger(__name__)


class WakeWordListener:
    """Continuously listens to the microphone and fires an event on detection."""

    def __init__(self, wake_word_provider: Callable[[], str], on_trigger: Callable[[], None]) -> None:
        self._wake_word_provider = wake_word_provider
        self._on_trigger = on_trigger

    def run_forever(self) -> None:
        LOGGER.info("Wake word listener running (stub mode)")
        while True:
            time.sleep(1.0)
            # In stub mode we simply log the configured wake word.
            LOGGER.debug("Waiting for wake word: %s", self._wake_word_provider())

    def simulate_detection(self) -> None:
        """Helper used in tests or demos to trigger the callback manually."""

        LOGGER.info("Wake word manually triggered")
        self._on_trigger()
