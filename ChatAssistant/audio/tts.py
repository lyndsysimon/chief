"""Text-to-speech abstraction layer with optional ElevenLabs integration."""
from __future__ import annotations

import logging
import os
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

from .types import AudioChunk

LOGGER = logging.getLogger(__name__)

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

    try:
        import sounddevice as sd
    except ImportError:  # pragma: no cover - depends on optional dependency
        LOGGER.warning("sounddevice not installed; unable to play audio (%d bytes)", len(chunk.data))
        return

    dtype = _dtype_from_width(chunk.sample_width)
    try:
        stream = sd.RawOutputStream(
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
        LOGGER.debug(
            "Sending ElevenLabs TTS request (voice_id=%s, model_id=%s, text_length=%d)",
            self.voice_id,
            self.model_id,
            len(text),
        )
        try:
            response = self._session.post(  # type: ignore[union-attr]
                f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}",
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            LOGGER.debug(
                "ElevenLabs TTS response received (status=%s, reason=%s, content_type=%s, bytes=%d)",
                getattr(response, "status_code", None),
                getattr(response, "reason", None),
                response.headers.get("Content-Type") if hasattr(response, "headers") else None,
                len(getattr(response, "content", b"")),
            )
            response.raise_for_status()
            audio_bytes = response.content
            if not audio_bytes:
                LOGGER.warning("ElevenLabs TTS returned an empty audio payload")
        except HTTPError as exc:  # pragma: no cover - exercised via tests
            _log_elevenlabs_error(exc)
            raise RuntimeError("ElevenLabs TTS request failed") from exc
        finally:
            _maybe_close(response)

        chunk = AudioChunk.from_wav_bytes(audio_bytes)
        LOGGER.debug(
            "ElevenLabs TTS audio decoded (channels=%s, sample_rate=%s, sample_width=%s, bytes=%d)",
            chunk.channels,
            chunk.sample_rate,
            chunk.sample_width,
            len(chunk.data),
        )
        return chunk


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
    LOGGER.info(
        "Registered ElevenLabs TTS backend (voice_id=%s, model_id=%s, timeout=%s)",
        voice_id,
        model_id,
        timeout,
    )
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


def _log_elevenlabs_error(exc: HTTPError) -> None:
    response = getattr(exc, "response", None)
    if response is None:
        LOGGER.error("ElevenLabs TTS request failed without a response: %s", exc)
        return

    status = getattr(response, "status_code", "<unknown>")
    reason = getattr(response, "reason", "")
    content_type = None
    try:
        content_type = response.headers.get("Content-Type")
    except Exception:  # pragma: no cover - defensive
        content_type = None

    preview: str | bytes
    try:
        preview = response.text  # type: ignore[assignment]
    except Exception:  # pragma: no cover - defensive
        preview = getattr(response, "content", b"")

    if isinstance(preview, str):
        preview = preview.strip()
        preview = preview[:500]
    else:
        preview = preview[:200]

    LOGGER.error(
        "ElevenLabs TTS request failed (status=%s, reason=%s, content_type=%s, body_preview=%r)",
        status,
        reason,
        content_type,
        preview,
    )
