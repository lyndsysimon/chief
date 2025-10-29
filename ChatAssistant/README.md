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
a reference dataset, runs the LLM stub, and prints the response.

```bash
python -m ChatAssistant.main
```

Expected console output:

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
* **STT** – Register an implementation with `register_stt_backend()` inside
  `audio/stt.py`. Faster Whisper or ElevenLabs works well on Windows.
* **TTS** – Register an implementation with `register_tts_backend()` inside
  `audio/tts.py`. Windows SAPI voices or ElevenLabs are both supported.
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
