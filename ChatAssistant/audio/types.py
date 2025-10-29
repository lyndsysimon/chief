"""Audio data structures used across capture, STT, and TTS layers."""
from __future__ import annotations

from dataclasses import dataclass
import io
import wave


@dataclass(slots=True)
class AudioChunk:
    """Raw PCM audio along with metadata required for processing."""

    data: bytes
    sample_rate: int
    channels: int = 1
    sample_width: int = 2  # bytes per sample

    def to_wav_bytes(self) -> bytes:
        """Serialize the PCM payload to a WAV container."""

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(self.sample_width)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(self.data)
        return buffer.getvalue()

    @classmethod
    def from_wav_bytes(cls, payload: bytes) -> "AudioChunk":
        """Create an :class:`AudioChunk` instance from WAV bytes."""

        with wave.open(io.BytesIO(payload), "rb") as wav_file:
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            sample_rate = wav_file.getframerate()
            frames = wav_file.readframes(wav_file.getnframes())
        return cls(data=frames, sample_rate=sample_rate, channels=channels, sample_width=sample_width)

    def copy_with(self, **kwargs: int | bytes) -> "AudioChunk":
        """Return a modified copy of the audio chunk."""

        params = {
            "data": self.data,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "sample_width": self.sample_width,
        }
        params.update(kwargs)
        return AudioChunk(**params)
