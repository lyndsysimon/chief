"""Speech-to-text abstraction layer."""
from __future__ import annotations

import logging
from typing import Callable

LOGGER = logging.getLogger(__name__)

# Developers should assign this callback to point at their real STT
# implementation (e.g. faster-whisper or ElevenLabs).
STT_BACKEND: Callable[[bytes], str] | None = None


def register_stt_backend(fn: Callable[[bytes], str]) -> None:
    global STT_BACKEND
    STT_BACKEND = fn


def call_stt(audio_buffer: bytes) -> str:
    if STT_BACKEND is None:
        LOGGER.warning("STT backend not configured; returning canned text")
        return "chief, what's my flap rip speed?"
    return STT_BACKEND(audio_buffer)
