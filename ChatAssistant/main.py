"""Entry point for the Chat assistant prototype.

The goal of this scaffold is to show how the components described in the
requirements can be wired together. The concrete audio, wake-word, hotkey and
LLM implementations are intentionally left as pluggable stubs so that the
assistant can be completed on a real Windows 11 workstation.
"""
from __future__ import annotations

import logging
import math
import re
import struct
import threading
from typing import Dict, List

from .audio import AudioConfigurationError, configure_elevenlabs_from_env
from .audio.hotkey_listener import GlobalHotkeyListener
from .audio.mic_capture import MicrophoneStream
from .audio.stt import call_stt
from .audio.tts import TTS_BACKEND, call_tts, play_audio
from .audio.types import AudioChunk
from .audio.wake_word_listener import WakeWordListener
from .brain.intent_classifier import IntentType, classify_intent
from .brain.llm_client import call_llm
from .brain.prompt_presets import PromptMode, get_prompt
from .brain.responder import TelemetryResponder
from .core.reference_data import ReferenceDataRegistry
from .core.state_manager import AssistantState
from .core.telemetry_reader import TelemetryReader
from .ui.tray_app import TrayApplication

LOGGER = logging.getLogger(__name__)


def bootstrap_assistant() -> None:
    """Wire together the assistant and start background services."""

    try:
        configure_elevenlabs_from_env()
    except AudioConfigurationError as exc:
        LOGGER.info("Audio backends not fully configured: %s", exc)

    state = AssistantState()
    telemetry_reader = TelemetryReader(state)
    telemetry_thread = threading.Thread(
        target=telemetry_reader.run_forever, name="TelemetryReader", daemon=True
    )
    telemetry_thread.start()

    reference_registry = ReferenceDataRegistry(base_path="./ChatAssistant/data/reference")

    responder = TelemetryResponder(state=state, reference_data=reference_registry)

    wake_word_listener = WakeWordListener(
        wake_word_provider=state.get_wake_word,
        on_trigger=lambda: handle_interaction(state, responder, PromptMode.CREW_CHIEF),
    )
    wake_word_thread = threading.Thread(
        target=wake_word_listener.run_forever, name="WakeWordListener", daemon=True
    )
    wake_word_thread.start()

    hotkey_listener = GlobalHotkeyListener(
        hotkey_provider=state.get_hotkey,
        on_trigger=lambda: handle_interaction(state, responder, PromptMode.CREW_CHIEF),
    )
    hotkey_thread = threading.Thread(
        target=hotkey_listener.run_forever, name="HotkeyListener", daemon=True
    )
    hotkey_thread.start()

    tray_app = TrayApplication(state=state)
    tray_app.run()


def handle_interaction(state: AssistantState, responder: TelemetryResponder, default_mode: PromptMode) -> None:
    """Main interaction loop executed whenever we are triggered."""

    LOGGER.info("Trigger received, capturing audio")
    mode = state.get_prompt_mode()
    if mode is None:
        mode = default_mode

    with MicrophoneStream() as stream:
        audio_buffer = stream.capture_until_silence()

    query_text = call_stt(audio_buffer)
    LOGGER.info("Recognized query: %s", query_text)
    if not query_text:
        return

    intent = classify_intent(query_text)
    LOGGER.debug("Intent: %s", intent)

    if intent == IntentType.MODE_SWITCH:
        mode = state.toggle_mode_from_command(query_text)
        response_text = f"Mode: {mode.value}"
    elif intent == IntentType.TELEMETRY:
        response_text = responder.generate_telemetry_only_response()
    else:
        messages: List[Dict[str, str]] = []
        messages.append({"role": "system", "content": get_prompt(mode)})
        messages.extend(responder.build_context_messages())
        messages.append({"role": "user", "content": query_text})
        response_text = call_llm(messages)

    LOGGER.info("Response: %s", response_text)
    audio_out = call_tts(response_text)
    play_audio(audio_out)


def example_flow() -> None:
    """Demonstrate an example interaction using stubbed values."""

    state = AssistantState()
    state.set_wake_word("chief")
    state.set_prompt_mode(PromptMode.CREW_CHIEF)

    # Populate telemetry snapshot manually for the example
    state.update_telemetry_snapshot(
        {
            "vehicle": "F-16C Block 50",
            "fuel_percent": 34,
            "ias_kmh": 820,
            "aoa_deg": 12,
            "g_load": 7.2,
            "g_status": "HIGH",
            "damage": {"left_wing": "Yellow"},
        }
    )

    reference_registry = ReferenceDataRegistry(base_path="./ChatAssistant/data/reference")
    responder = TelemetryResponder(state=state, reference_data=reference_registry)

    question = "chief, what's my flap rip speed?"
    intent = classify_intent(question)
    assert intent == IntentType.REFERENCE

    messages: List[Dict[str, str]] = []
    messages.append({"role": "system", "content": get_prompt(PromptMode.CREW_CHIEF)})
    messages.extend(responder.build_context_messages())
    messages.append({"role": "user", "content": question})

    llm_reply = call_llm(messages)
    print(llm_reply)

    audio_chunk = call_tts(llm_reply) if TTS_BACKEND is not None else AudioChunk(data=b"", sample_rate=16_000)
    if not audio_chunk.data:
        audio_chunk = _synthesize_reference_tone(llm_reply)
    play_audio(audio_chunk)


def _synthesize_reference_tone(response_text: str) -> AudioChunk:
    """Generate a simple confirmation tone for the example flow."""

    sample_rate = 16_000
    amplitude = int(0.35 * (2 ** 15 - 1))
    tone_duration = 0.35
    spacer_duration = 0.1

    label_frequency = {
        "combat": 880.0,
        "landing": 660.0,
        "takeoff": 550.0,
    }

    matches = re.findall(r"(Combat|Landing|Takeoff):\s*([0-9]+)", response_text, re.IGNORECASE)
    if not matches:
        matches = [("status", "0")]

    frames = bytearray()

    def _append_silence(duration: float) -> None:
        frame_count = int(duration * sample_rate)
        frames.extend(b"\x00\x00" * frame_count)

    def _append_tone(frequency: float, duration: float) -> None:
        frame_count = int(duration * sample_rate)
        two_pi_over_rate = 2.0 * math.pi * frequency / sample_rate
        for n in range(frame_count):
            sample = math.sin(two_pi_over_rate * n)
            frames.extend(struct.pack("<h", int(sample * amplitude)))

    for label, value in matches:
        base_freq = label_frequency.get(label.lower(), 440.0)
        _append_tone(base_freq, tone_duration)
        _append_silence(spacer_duration)
        for digit in value:
            digit_freq = 440.0 + (int(digit) * 18.0)
            _append_tone(digit_freq, tone_duration / 3)
            _append_silence(spacer_duration / 2)
        _append_silence(spacer_duration * 2)

    return AudioChunk(data=bytes(frames), sample_rate=sample_rate)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    example_flow()
