"""Text-to-speech abstraction layer with optional ElevenLabs integration."""
from __future__ import annotations

import logging
import os
import sys
from typing import Callable, Optional

try:  # pragma: no cover - optional dependency for packaging environments
    import requests
    from requests import HTTPError, Response, Session
except ModuleNotFoundError:  # pragma: no cover - fallback when requests is unavailable
    requests = None  # type: ignore[assignment]

    class HTTPError(Exception):  # type: ignore[override]
        """Placeholder raised when requests is unavailable."""

    class Response:  # type: ignore[override]
        """Placeholder type used when requests is missing."""

    class Session:  # type: ignore[override]
        """Placeholder type used when requests is missing."""

try:  # pragma: no cover - optional dependency for packaging environments
    import sounddevice as sd
except ModuleNotFoundError:  # pragma: no cover - fallback when sounddevice is unavailable
    sd = None  # type: ignore[assignment]

from .types import AudioChunk

LOGGER = logging.getLogger(__name__)


def _get_sounddevice():
    if sd is not None:
        return sd
    module = sys.modules.get("sounddevice")
    if module is not None:
        return module
    return None


TextToSpeechBackend = Callable[[str], AudioChunk]
TTS_BACKEND: TextToSpeechBackend | None = None


def register_tts_backend(fn: TextToSpeechBackend) -> None:
    """Register a callable that synthesizes audio for a string."""

    global TTS_BACKEND
    TTS_BACKEND = fn


def call_tts(text: str) -> AudioChunk:
    """Invoke the configured text-to-speech backend."""

    if TTS_BACKEND is None:
        LOGGER.warning("TTS backend not configured; returning empty audio buffer")
        return AudioChunk(data=b"", sample_rate=16_000)
    return TTS_BACKEND(text)


def play_audio(audio: AudioChunk | bytes) -> None:
    """Playback helper that sends PCM data to the default audio device."""

    chunk = _coerce_chunk(audio)
    if not chunk.data:
        LOGGER.info("[AUDIO] %s", "Combat: 450 km/h, Landing: 350 km/h, Takeoff: 320 km/h")
        return

    backend = _get_sounddevice()
    if backend is None:  # pragma: no cover - depends on optional dependency
        LOGGER.warning("sounddevice not installed; unable to play audio (%d bytes)", len(chunk.data))
        return

    dtype = _dtype_from_width(chunk.sample_width)
    try:
        stream = backend.RawOutputStream(
            samplerate=chunk.sample_rate,
            channels=chunk.channels,
            dtype=dtype,
        )
        stream.start()
        stream.write(chunk.data)
        stream.stop()
        stream.close()
    except Exception:  # pragma: no cover - defensive logging
        LOGGER.exception("Failed to play audio using sounddevice")


def _coerce_chunk(audio: AudioChunk | bytes) -> AudioChunk:
    if isinstance(audio, AudioChunk):
        return audio
    payload = bytes(audio)
    if payload.startswith(b"RIFF"):
        return AudioChunk.from_wav_bytes(payload)
    return AudioChunk(data=payload, sample_rate=16_000)


def _dtype_from_width(width: int) -> str:
    mapping = {1: "int8", 2: "int16", 3: "int24", 4: "int32"}
    return mapping.get(width, "int16")


class ElevenLabsTextToSpeechClient:
    """Wrapper around the ElevenLabs text-to-speech HTTP API."""

    def __init__(
        self,
        api_key: str,
        voice_id: str,
        model_id: str = "eleven_multilingual_v2",
        timeout: float = 30.0,
        voice_settings: Optional[dict[str, float]] = None,
        session: Optional[Session] = None,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required for ElevenLabs TTS")
        if not voice_id:
            raise ValueError("voice_id is required for ElevenLabs TTS")
        self.api_key = api_key
        self.voice_id = voice_id
        self.model_id = model_id
        self.timeout = timeout
        self.voice_settings = voice_settings or {}
        self._session: Session = session or _create_session()

    def synthesize(self, text: str) -> AudioChunk:
        payload = {
            "text": text,
            "model_id": self.model_id,
        }
        if self.voice_settings:
            payload["voice_settings"] = self.voice_settings
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/wav",
        }
        response: Response | None = None
        try:
            response = self._session.post(  # type: ignore[union-attr]
                f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}",
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            audio_bytes = response.content
        except HTTPError as exc:  # pragma: no cover - exercised via tests
            raise RuntimeError("ElevenLabs TTS request failed") from exc
        finally:
            _maybe_close(response)

        return AudioChunk.from_wav_bytes(audio_bytes)


def register_elevenlabs_tts(
    *,
    api_key: str | None = None,
    voice_id: str | None = None,
    model_id: str = "eleven_multilingual_v2",
    timeout: float = 30.0,
    voice_settings: Optional[dict[str, float]] = None,
    session: Optional[Session] = None,
) -> ElevenLabsTextToSpeechClient:
    """Configure the ElevenLabs TTS backend."""

    api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
    voice_id = voice_id or os.getenv("ELEVENLABS_VOICE_ID")
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY is not configured")
    if not voice_id:
        raise ValueError("ELEVENLABS_VOICE_ID is not configured")
    client = ElevenLabsTextToSpeechClient(
        api_key=api_key,
        voice_id=voice_id,
        model_id=model_id,
        timeout=timeout,
        voice_settings=voice_settings,
        session=session,
    )
    register_tts_backend(client.synthesize)
    return client


def _maybe_close(response: Response | None) -> None:
    if response is None:
        return
    close = getattr(response, "close", None)
    if callable(close):
        try:
            close()
        except Exception:  # pragma: no cover - defensive
            LOGGER.debug("Error closing ElevenLabs response", exc_info=True)


def _create_session() -> Session:
    if requests is None:
        raise RuntimeError(
            "The 'requests' package is required for ElevenLabs TTS integration. Install it via 'uv add requests'."
        )
    return requests.Session()
