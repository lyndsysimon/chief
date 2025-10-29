import logging

import pytest

from chief.audio import stt as stt_module
from chief.audio import tts as tts_module
from chief.audio.hotkey_listener import GlobalHotkeyListener
from chief.audio.mic_capture import MicrophoneStream
from chief.audio.stt import call_stt, register_stt_backend
from chief.audio.tts import call_tts, play_audio, register_tts_backend
from chief.audio.wake_word_listener import WakeWordListener
from chief.audio.types import AudioChunk


@pytest.fixture(autouse=True)
def reset_backends():
    stt_module.STT_BACKEND = None
    tts_module.TTS_BACKEND = None
    yield
    stt_module.STT_BACKEND = None
    tts_module.TTS_BACKEND = None


def test_call_stt_uses_registered_backend():
    register_stt_backend(lambda chunk: f"processed:{chunk.sample_rate}:{len(chunk.data)}")

    audio = AudioChunk(data=b"1234", sample_rate=16_000)
    assert call_stt(audio) == "processed:16000:4"


def test_call_stt_returns_placeholder_when_missing(caplog):
    caplog.set_level(logging.WARNING)

    result = call_stt(AudioChunk(data=b"1234", sample_rate=16_000))

    assert result == "chief, what's my flap rip speed?"
    assert "STT backend not configured" in caplog.text


def test_call_tts_uses_registered_backend():
    register_tts_backend(lambda text: AudioChunk(data=text.encode("utf-8"), sample_rate=22_050))

    result = call_tts("hello")
    assert isinstance(result, AudioChunk)
    assert result.data == b"hello"
    assert result.sample_rate == 22_050


def test_call_tts_returns_empty_buffer_when_missing(caplog):
    caplog.set_level(logging.WARNING)

    result = call_tts("hi")

    assert isinstance(result, AudioChunk)
    assert result.data == b""
    assert "TTS backend not configured" in caplog.text


def test_play_audio_logs_expected_message(caplog):
    caplog.set_level(logging.INFO)

    play_audio(AudioChunk(data=b"", sample_rate=16_000))

    assert "Combat: 450 km/h" in caplog.text


def test_hotkey_listener_simulate_trigger_invokes_callback():
    triggered = []
    listener = GlobalHotkeyListener(lambda: "ctrl+shift+x", lambda: triggered.append(True))

    listener.simulate_trigger()

    assert triggered == [True]


def test_wake_word_listener_simulate_detection_invokes_callback():
    triggered = []
    listener = WakeWordListener(lambda: "chief", lambda: triggered.append(True))

    listener.simulate_detection()

    assert triggered == [True]


def test_microphone_stream_context_manager_logs(caplog):
    caplog.set_level(logging.DEBUG)

    with MicrophoneStream() as stream:
        chunk = stream.capture_until_silence()
        assert isinstance(chunk, AudioChunk)
        assert chunk.data == b""

    assert "Opening microphone stream" in caplog.text
    assert "Closing microphone stream" in caplog.text
