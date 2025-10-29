"""Microphone capture implementation backed by ``sounddevice``."""
from __future__ import annotations

import logging
import math
import queue
import time
from array import array
from contextlib import AbstractContextManager
from typing import Callable, Optional

from .types import AudioChunk

LOGGER = logging.getLogger(__name__)


def _compute_rms(chunk: bytes, sample_width: int) -> int:
    """Return the RMS value for ``chunk`` using a pure Python implementation."""

    if sample_width == 1:
        samples = array("b", chunk)
    elif sample_width == 2:
        samples = array("h")
        samples.frombytes(chunk)
    elif sample_width == 4:
        samples = array("i")
        samples.frombytes(chunk)
    else:  # pragma: no cover - defensive programming
        raise ValueError(f"Unsupported sample width: {sample_width}")

    if not samples:
        return 0

    total = 0
    for sample in samples:
        total += sample * sample

    return int(math.sqrt(total / len(samples)))

InputStreamFactory = Callable[[int, int, int, Callable[[bytes], None]], object]


class MicrophoneStream(AbstractContextManager):
    """Capture PCM audio from the default microphone until silence is detected."""

    def __init__(
        self,
        sample_rate: int = 16_000,
        channels: int = 1,
        chunk_duration: float = 0.25,
        silence_duration: float = 0.8,
        silence_threshold: int = 250,
        max_record_seconds: float = 15.0,
        input_stream_factory: Optional[InputStreamFactory] = None,
    ) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self.sample_width = 2
        self.chunk_duration = max(chunk_duration, 0.01)
        self.silence_duration = max(silence_duration, 0.1)
        self.silence_threshold = max(silence_threshold, 1)
        self.max_record_seconds = max(max_record_seconds, self.silence_duration)
        self._input_stream_factory = input_stream_factory
        self._input_stream: object | None = None
        self._queue: queue.Queue[bytes] = queue.Queue()

    def __enter__(self) -> "MicrophoneStream":
        LOGGER.debug(
            "Opening microphone stream (rate=%s, channels=%s)", self.sample_rate, self.channels
        )
        if self._input_stream_factory is None:
            self._input_stream_factory = self._build_sounddevice_stream
        try:
            blocksize = max(1, int(self.sample_rate * self.chunk_duration))
            self._input_stream = self._input_stream_factory(
                self.sample_rate, self.channels, blocksize, self._enqueue_chunk
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            LOGGER.warning("Failed to initialize microphone backend: %s", exc, exc_info=True)
            self._input_stream = None
        return self

    def __exit__(self, exc_type, exc, exc_tb) -> None:  # noqa: ANN001
        LOGGER.debug("Closing microphone stream")
        stream = self._input_stream
        self._input_stream = None
        if stream is not None:
            stop = getattr(stream, "stop", None)
            close = getattr(stream, "close", None)
            if callable(stop):
                try:
                    stop()
                except Exception:  # pragma: no cover - defensive logging
                    LOGGER.exception("Failed to stop microphone stream")
            if callable(close):
                try:
                    close()
                except Exception:  # pragma: no cover - defensive logging
                    LOGGER.exception("Failed to close microphone stream")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_sounddevice_stream(
        self, sample_rate: int, channels: int, blocksize: int, callback: Callable[[bytes], None]
    ) -> object:
        import sounddevice as sd

        def _callback(indata, frames, time_info, status):  # noqa: ARG001
            if status:  # pragma: no cover - status logging
                LOGGER.debug("Microphone status: %s", status)
            callback(bytes(indata))

        stream = sd.RawInputStream(
            samplerate=sample_rate,
            channels=channels,
            dtype="int16",
            blocksize=blocksize,
            callback=_callback,
        )
        stream.start()
        return stream

    def _enqueue_chunk(self, chunk: bytes) -> None:
        self._queue.put(chunk)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def capture_until_silence(self) -> AudioChunk:
        """Capture audio until silence is detected or the timeout elapses."""

        if self._input_stream is None:
            LOGGER.debug("Microphone backend unavailable; returning empty buffer")
            return AudioChunk(data=b"", sample_rate=self.sample_rate, channels=self.channels, sample_width=self.sample_width)

        frames: list[bytes] = []
        silence_start: float | None = None
        block_timeout = max(self.chunk_duration, 0.05)
        started = time.monotonic()
        deadline = started + self.max_record_seconds

        while time.monotonic() < deadline:
            try:
                chunk = self._queue.get(timeout=block_timeout)
            except queue.Empty:
                continue

            if not chunk:
                continue

            frames.append(chunk)
            rms = _compute_rms(chunk, self.sample_width)
            if rms < self.silence_threshold:
                if silence_start is None:
                    silence_start = time.monotonic()
                elif time.monotonic() - silence_start >= self.silence_duration:
                    break
            else:
                silence_start = None

        audio_bytes = b"".join(frames)
        return AudioChunk(
            data=audio_bytes,
            sample_rate=self.sample_rate,
            channels=self.channels,
            sample_width=self.sample_width,
        )
