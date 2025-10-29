import io
import sys
import wave

import pytest

from chief.audio.stt import call_stt, register_elevenlabs_stt
from chief.audio.tts import call_tts, play_audio, register_elevenlabs_tts
from chief.audio.types import AudioChunk


class DummyResponse:
    def __init__(self, *, json_payload=None, content: bytes = b"", status_code: int = 200):
        self._json_payload = json_payload
        self._content = content
        self.status_code = status_code

    def json(self):
        return self._json_payload

    @property
    def content(self):
        return self._content

    def raise_for_status(self):
        if self.status_code >= 400:
            from requests import HTTPError

            raise HTTPError(response=self)

    def close(self):
        pass


class DummySession:
    def __init__(self):
        self.calls: list[dict] = []

    def post(self, url, *, headers=None, data=None, files=None, json=None, timeout=None):
        call = {
            "url": url,
            "headers": headers or {},
            "data": data,
            "files": files,
            "json": json,
            "timeout": timeout,
        }
        self.calls.append(call)
        if "speech-to-text" in url:
            payload = {"text": "transcribed"}
            return DummyResponse(json_payload=payload)
        if "text-to-speech" in url:
            return DummyResponse(content=b"WAVE")
        raise AssertionError("Unexpected URL: " + url)


@pytest.fixture(autouse=True)
def reset_backends():
    from chief.audio import stt as stt_module
    from chief.audio import tts as tts_module

    stt_module.STT_BACKEND = None
    tts_module.TTS_BACKEND = None
    yield
    stt_module.STT_BACKEND = None
    tts_module.TTS_BACKEND = None


def test_elevenlabs_stt_registration():
    session = DummySession()

    register_elevenlabs_stt(api_key="token", session=session)

    result = call_stt(AudioChunk(data=b"\x00\x01" * 10, sample_rate=16_000))
    assert result == "transcribed"
    assert session.calls, "Expected ElevenLabs STT call to be made"
    call = session.calls[0]
    assert call["headers"]["xi-api-key"] == "token"
    assert call["data"]["model_id"] == "eleven_monolingual_v1"
    assert call["files"]["file"][0] == "audio.wav"


def _build_wav(sample_rate=22_050, channels=1, sample_width=2, frames=b"\x01\x00" * 10):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(frames)
    return buffer.getvalue()


def test_elevenlabs_tts_registration():
    wav_bytes = _build_wav(frames=b"\x01\x00" * 5)
    session = DummySession()

    def post(url, **kwargs):  # noqa: ANN001
        if "text-to-speech" in url:
            headers = kwargs["headers"]
            assert headers["xi-api-key"] == "token"
            assert headers["Accept"] == "audio/wav"
            payload = kwargs["json"]
            assert payload["text"] == "hello"
            return DummyResponse(content=wav_bytes)
        return DummyResponse()

    session.post = post  # type: ignore[assignment]

    register_elevenlabs_tts(api_key="token", voice_id="test-voice", session=session)

    audio = call_tts("hello")
    assert isinstance(audio, AudioChunk)
    assert audio.data != b""
    assert audio.sample_rate == 22_050


def test_play_audio_with_sounddevice(monkeypatch):
    class DummyStream:
        def __init__(self):
            self.written = b""
            self.started = False
            self.stopped = False

        def start(self):
            self.started = True

        def write(self, data):
            self.written += data

        def stop(self):
            self.stopped = True

        def close(self):
            pass

    class DummySoundDevice:
        def __init__(self):
            self.streams: list[DummyStream] = []

        def RawOutputStream(self, **kwargs):  # noqa: N803
            stream = DummyStream()
            stream.kwargs = kwargs
            self.streams.append(stream)
            return stream

    dummy = DummySoundDevice()
    monkeypatch.setitem(sys.modules, "sounddevice", dummy)

    chunk = AudioChunk(data=b"\x01\x00" * 5, sample_rate=16_000)
    play_audio(chunk)
    assert dummy.streams, "Expected RawOutputStream to be invoked"
    created = dummy.streams[0]
    assert created.started is True
    assert created.stopped is True
    assert created.written == chunk.data


if __name__ == "__main__":
    pytest.main([__file__])
