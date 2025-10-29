from __future__ import annotations

from ChatAssistant import main
from ChatAssistant.audio import AudioConfigurationError
from ChatAssistant.audio.types import AudioChunk


def test_example_flow_configures_elevenlabs(monkeypatch):
    original_backend = main.TTS_BACKEND
    called_kwargs: dict[str, bool] = {}

    def fake_configure(*, configure_stt: bool, configure_tts: bool) -> None:
        called_kwargs["configure_stt"] = configure_stt
        called_kwargs["configure_tts"] = configure_tts
        main.TTS_BACKEND = object()  # ensure example flow takes the call_tts branch

    monkeypatch.setattr(main, "configure_elevenlabs_from_env", fake_configure)

    reply = "Combat: 450 km/h, Landing: 350 km/h, Takeoff: 320 km/h"
    monkeypatch.setattr(main, "call_llm", lambda messages: reply)

    recorded: dict[str, AudioChunk] = {}

    def fake_call_tts(text: str) -> AudioChunk:
        recorded["text"] = text
        return AudioChunk(data=b"\x01\x02", sample_rate=16_000)

    monkeypatch.setattr(main, "call_tts", fake_call_tts)

    played: dict[str, AudioChunk] = {}
    monkeypatch.setattr(main, "play_audio", lambda chunk: played.setdefault("chunk", chunk))

    try:
        main.example_flow()
    finally:
        main.TTS_BACKEND = original_backend

    assert called_kwargs == {"configure_stt": False, "configure_tts": True}
    assert recorded["text"] == reply
    assert played["chunk"].data == b"\x01\x02"


def test_example_flow_falls_back_to_tone(monkeypatch):
    original_backend = main.TTS_BACKEND

    def fake_configure(**_: bool) -> None:
        raise AudioConfigurationError("missing env")

    monkeypatch.setattr(main, "configure_elevenlabs_from_env", fake_configure)

    reply = "Combat: 450 km/h, Landing: 350 km/h, Takeoff: 320 km/h"
    monkeypatch.setattr(main, "call_llm", lambda messages: reply)

    synthesized: dict[str, AudioChunk] = {}

    def fake_synthesize(text: str) -> AudioChunk:
        chunk = AudioChunk(data=b"\x10\x20", sample_rate=16_000)
        synthesized["text"] = text
        synthesized["chunk"] = chunk
        return chunk

    monkeypatch.setattr(main, "_synthesize_reference_tone", fake_synthesize)
    monkeypatch.setattr(main, "play_audio", lambda chunk: synthesized.setdefault("played", chunk))

    main.TTS_BACKEND = None

    try:
        main.example_flow()
    finally:
        main.TTS_BACKEND = original_backend

    assert synthesized["text"] == reply
    assert synthesized["played"].data == b"\x10\x20"
