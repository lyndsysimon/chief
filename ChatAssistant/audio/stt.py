"""Speech-to-text abstraction layer with ElevenLabs integration."""
from __future__ import annotations

import logging
import os
from typing import Callable, Optional

import requests
from requests import HTTPError, Response, Session

from .types import AudioChunk

LOGGER = logging.getLogger(__name__)

SpeechToTextBackend = Callable[[AudioChunk], str]
STT_BACKEND: SpeechToTextBackend | None = None


def register_stt_backend(fn: SpeechToTextBackend) -> None:
    """Register a callable that converts audio into text."""

    global STT_BACKEND
    STT_BACKEND = fn


def _ensure_chunk(audio: AudioChunk | bytes) -> AudioChunk:
    if isinstance(audio, AudioChunk):
        return audio
    return AudioChunk(data=bytes(audio), sample_rate=16_000)


def call_stt(audio_buffer: AudioChunk | bytes) -> str:
    """Invoke the configured speech-to-text backend."""

    chunk = _ensure_chunk(audio_buffer)
    if STT_BACKEND is None:
        LOGGER.warning("STT backend not configured; returning canned text")
        return "chief, what's my flap rip speed?"
    return STT_BACKEND(chunk)


class ElevenLabsSpeechToTextClient:
    """Thin wrapper around ElevenLabs' speech-to-text HTTP API."""

    def __init__(
        self,
        api_key: str,
        model_id: str = "eleven_monolingual_v1",
        language: str | None = None,
        timeout: float = 30.0,
        session: Optional[Session] = None,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required for ElevenLabs STT")
        self.api_key = api_key
        self.model_id = model_id
        self.language = language
        self.timeout = timeout
        self._session: Session = session or _create_session()

    def transcribe(self, audio: AudioChunk) -> str:
        headers = {
            "Accept": "application/json",
            "xi-api-key": self.api_key,
        }
        data: dict[str, str] = {"model_id": self.model_id}
        if self.language:
            data["language"] = self.language
        files = {
            "file": ("audio.wav", audio.to_wav_bytes(), "audio/wav"),
        }

        response: Response | None = None
        try:
            response = self._session.post(  # type: ignore[union-attr]
                "https://api.elevenlabs.io/v1/speech-to-text",
                headers=headers,
                data=data,
                files=files,
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except HTTPError as exc:  # pragma: no cover - exercised via tests
            raise RuntimeError("ElevenLabs STT request failed") from exc
        finally:
            _maybe_close(response)

        text = payload.get("text") or payload.get("transcription")
        if not isinstance(text, str):
            raise RuntimeError("ElevenLabs STT returned an unexpected payload")
        return text


def register_elevenlabs_stt(
    *,
    api_key: str | None = None,
    model_id: str = "eleven_monolingual_v1",
    language: str | None = None,
    timeout: float = 30.0,
    session: Optional[Session] = None,
) -> ElevenLabsSpeechToTextClient:
    """Configure the ElevenLabs STT backend."""

    api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY is not configured")
    client = ElevenLabsSpeechToTextClient(
        api_key=api_key,
        model_id=model_id,
        language=language,
        timeout=timeout,
        session=session,
    )
    register_stt_backend(client.transcribe)
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
    return requests.Session()
