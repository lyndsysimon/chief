# Chat – War Thunder Local Assistant (Prototype Scaffold)

This repository contains a Windows-focused scaffold for a local War Thunder
voice copilot named **Chat**. The goal of the scaffold is to illustrate the
boundaries between audio capture, telemetry ingestion, prompt handling, and UI
configuration while leaving enough hooks for a Windows developer to plug in
hardware-specific implementations.

## Folder layout

```
ChatAssistant/
  core/        # Telemetry polling, state manager, reference data lookup
  audio/       # Wake word, hotkey, microphone, STT, TTS abstractions
  brain/       # Intent classification, prompt definitions, LLM client, responders
  ui/          # Tray application and settings window stubs
  data/        # Example reference JSON files
  main.py      # Bootstrap logic and example flow
```

## Running the example flow

The `example_flow()` function in `main.py` demonstrates a single end-to-end
interaction without real audio input. It primes the state with telemetry and
a reference dataset, runs the LLM stub, and prints the response. When no
text-to-speech backend has been configured it synthesizes a simple tone
sequence so you still hear a confirmation from the demo.

```bash
python -m ChatAssistant.main
```

Expected console output and audio:

```
Combat: 450 km/h, Landing: 350 km/h, Takeoff: 320 km/h
```

The TTS stub also logs the same line through the logger to emulate spoken
feedback.

## Wiring real dependencies

* **Wake word** – Replace `WakeWordListener` with a library such as Porcupine or
  Silero, or integrate Windows Speech SDK. Hook detection to `self._on_trigger()`.
* **Global hotkey** – Replace `GlobalHotkeyListener` with `keyboard` or
  `pywin32` registration. Call `self._on_trigger()` on activation.
* **STT** – `register_stt_backend()` in `audio/stt.py` now defaults to an
  ElevenLabs client when `ELEVENLABS_API_KEY` is provided. The helper converts
  PCM input to a WAV payload before calling the
  `https://api.elevenlabs.io/v1/speech-to-text` endpoint.
* **TTS** – `register_tts_backend()` in `audio/tts.py` uses ElevenLabs when
  both `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_ID` are set. Responses are
  downloaded as WAV and streamed to the default playback device.
* **LLM** – Implement `call_llm()` to call your preferred OpenAI-compatible
  endpoint. Remember to include the persona prompt provided in the
  requirements.
* **Telemetry** – `TelemetryReader` polls the local War Thunder telemetry API
  (`http://127.0.0.1:8111/state` by default) and normalizes frequently used
  values.
* **Reference data** – Place JSON files in `data/reference/`. The filename is a
  lower-case slug of the vehicle name, e.g. `f-16c_block_50.json`.

## Configuration persistence

`AssistantState` persists settings such as wake word and hotkey to
`ChatAssistant/config.json`. The settings window and tray app stubs demonstrate
how the state object can be reused across components.

## Audio configuration

`MicrophoneStream` and `play_audio` rely on the `sounddevice` package to
interface with the system's default input and output devices. Install it via:

```bash
pip install sounddevice
```

Set the following environment variables before launching the assistant so that
the ElevenLabs adapters can authenticate:

```bash
set ELEVENLABS_API_KEY=<your_api_key>
set ELEVENLABS_VOICE_ID=<voice_id_to_synthesize>
```

`ChatAssistant.audio.configure_elevenlabs_from_env()` reads these variables and
automatically wires the speech-to-text and text-to-speech backends.

## Example voice interaction

1. Wake word detector hears “chief”.
2. Microphone stream captures the user request.
3. STT returns “chief, what’s my flap rip speed?”.
4. Intent classifier flags the query as `IntentType.REFERENCE`.
5. `TelemetryResponder` collects telemetry (`get_current_state`) and reference
   data for the current vehicle.
6. `call_llm` receives the persona prompt, telemetry context, reference data,
   and the transcribed question.
7. LLM responds with “Combat: 450 km/h, Landing: 350 km/h, Takeoff: 320 km/h”.
8. `call_tts` synthesizes audio and `play_audio` sends it to the speakers.

At each step comments in code highlight where production integrations belong.
