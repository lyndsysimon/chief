"""Audio helpers for configuring speech capture, STT, and TTS backends."""
from __future__ import annotations

import logging
import os

from .stt import register_elevenlabs_stt
from .tts import register_elevenlabs_tts

LOGGER = logging.getLogger(__name__)


class AudioConfigurationError(RuntimeError):
    """Raised when automatic audio configuration cannot be completed."""


def configure_elevenlabs_from_env(*, configure_stt: bool = True, configure_tts: bool = True) -> None:
    """Configure ElevenLabs backends using environment variables if available."""

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise AudioConfigurationError("ELEVENLABS_API_KEY is not set")

    configured = False
    if configure_stt:
        register_elevenlabs_stt(api_key=api_key)
        configured = True

    if configure_tts:
        voice_id = os.getenv("ELEVENLABS_VOICE_ID")
        if not voice_id:
            raise AudioConfigurationError("ELEVENLABS_VOICE_ID is not set")
        register_elevenlabs_tts(api_key=api_key, voice_id=voice_id)
        configured = True

    if not configured:
        raise AudioConfigurationError("No ElevenLabs backends were configured")


__all__ = ["AudioConfigurationError", "configure_elevenlabs_from_env"]
