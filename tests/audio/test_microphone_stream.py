from ChatAssistant.audio.mic_capture import MicrophoneStream
from ChatAssistant.audio.types import AudioChunk


class DummyStream:
    def stop(self):
        pass

    def close(self):
        pass


def test_microphone_stream_collects_until_silence():
    def factory(sample_rate, channels, blocksize, callback):  # noqa: ARG001
        loud_frame = (b"\x10\x00" * blocksize)
        silent_frame = (b"\x00\x00" * blocksize)
        callback(loud_frame)
        for _ in range(6):
            callback(silent_frame)
        return DummyStream()

    stream = MicrophoneStream(
        sample_rate=8_000,
        chunk_duration=0.01,
        silence_duration=0.05,
        silence_threshold=20,
        max_record_seconds=0.2,
        input_stream_factory=factory,
    )

    with stream as s:
        chunk = s.capture_until_silence()

    assert isinstance(chunk, AudioChunk)
    assert chunk.data.startswith(b"\x10\x00")
    assert chunk.sample_rate == 8_000
