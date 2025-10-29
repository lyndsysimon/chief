"""Microphone capture stub."""
from __future__ import annotations

import logging
from contextlib import AbstractContextManager

LOGGER = logging.getLogger(__name__)


class MicrophoneStream(AbstractContextManager):
    """Placeholder context manager for microphone capture."""

    def __enter__(self) -> "MicrophoneStream":
        LOGGER.debug("Opening microphone stream (stub)")
        return self

    def __exit__(self, exc_type, exc, exc_tb) -> None:  # noqa: ANN001
        LOGGER.debug("Closing microphone stream (stub)")

    def capture_until_silence(self) -> bytes:
        """Return raw PCM bytes for the captured speech.

        The actual implementation should capture audio in a background buffer and
        stop when speech ends. For the prototype we just return an empty buffer.
        """

        LOGGER.debug("Capturing audio (stub)")
        return b""
