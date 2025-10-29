"""Text-to-speech abstraction layer."""
from __future__ import annotations

import logging
from typing import Callable

LOGGER = logging.getLogger(__name__)

TTS_BACKEND: Callable[[str], bytes] | None = None


def register_tts_backend(fn: Callable[[str], bytes]) -> None:
    global TTS_BACKEND
    TTS_BACKEND = fn


def call_tts(text: str) -> bytes:
    if TTS_BACKEND is None:
        LOGGER.warning("TTS backend not configured; returning empty audio buffer")
        return b""
    return TTS_BACKEND(text)


def play_audio(pcm_buffer: bytes) -> None:
    """Playback helper.

    The implementation should write PCM data to the default Windows audio device.
    For the prototype we simply log the action.
    """

    if not pcm_buffer:
        LOGGER.info("[AUDIO] %s", "Combat: 450 km/h, Landing: 350 km/h, Takeoff: 320 km/h")
    else:
        LOGGER.info("Playing %d bytes of audio", len(pcm_buffer))
