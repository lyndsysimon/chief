# Chief – Local War Thunder Assistant Scaffold

The `ChatAssistant` package contains a Windows-oriented prototype of a War
Thunder voice copilot called **Chat**. The scaffold wires together telemetry
polling, wake word & hotkey triggers, speech pipelines, persona prompts, and a
configuration UI shell so that the complete assistant can be finalized on a
Windows 11 gaming PC.

Refer to `ChatAssistant/README.md` for architecture details, wiring
instructions, and an example interaction that produces:

```
Combat: 450 km/h, Landing: 350 km/h, Takeoff: 320 km/h
```

This repository is structured to make it easy to replace the stubbed components
with real Windows integrations (Porcupine, faster-whisper, ElevenLabs, pywin32,
DirectSound, etc.).

## Implementation plan to reach a locally testable build

The table below tracks the end-to-end work required to replace the stubs with
production-ready integrations. Each milestone includes a goal, concrete tasks,
and the exit criteria that confirm the assistant is runnable on a Windows 11
machine. Tackle the milestones in order—later phases depend on the groundwork
from earlier ones.

| Milestone | Goal | Key tasks (ordered) | Exit criteria |
| --- | --- | --- | --- |
| **0. Environment bootstrap** | Confirm the scaffold runs unchanged on the target workstation. | 1. Install Python 3.11, Poetry/virtualenv, and the War Thunder HTTP telemetry plugin.<br>2. Clone this repository and run `python -m ChatAssistant.main --example` to validate the current stub pipeline.<br>3. Capture `pip list` / `python --version` for future troubleshooting notes. | Example flow prints the canned flap-speed response with no stack traces; dependency versions are documented. |
| **1. Speech capture & playback** | Replace audio stubs with real microphone and speaker I/O. | 1. Choose STT + TTS providers (e.g., faster-whisper GPU build + ElevenLabs).<br>2. Implement concrete adapters in `ChatAssistant/audio/stt.py` and `ChatAssistant/audio/tts.py`, registering them via `register_stt_backend` / `register_tts_backend`.<br>3. Flesh out `ChatAssistant/audio/io.py` to stream PCM from the default input device and play synthesized audio.<br>4. Add unit smoke tests in `tests/audio/` that mock hardware and assert bytes flow through the adapters. | Running `python -m ChatAssistant.main --example` produces spoken audio through the speakers, and new tests pass locally. |
| **2. Wake word & hotkey triggers** | Allow the assistant loop to start without code changes. | 1. Integrate Porcupine/Silero inside `ChatAssistant/audio/wake_word.py` and wire `_on_trigger` callbacks.<br>2. Implement a global hotkey listener in `ChatAssistant/audio/hotkey.py` using `keyboard` or `pywin32`.<br>3. Add logging and a `tests/audio/test_triggers.py` unit test that simulates trigger invocations. | Saying the wake word or pressing the configured hotkey starts the STT capture in a manual test; automated trigger tests pass. |
| **3. Telemetry + LLM integration** | Produce contextual answers sourced from live game data. | 1. Complete `TelemetryReader` in `ChatAssistant/core/telemetry.py` to poll `http://127.0.0.1:8111/state`, normalizing fields used by responders.<br>2. Populate `ChatAssistant/data/reference/` with JSON for the top aircraft you fly.<br>3. Implement `call_llm()` in `ChatAssistant/brain/llm.py` against your OpenAI-compatible endpoint, including persona prompt and grounding context.<br>4. Write integration tests (see `tests/integration/`) that mock HTTP + LLM responses to validate prompt assembly. | When triggered in War Thunder, the assistant reads telemetry, queries the LLM, and speaks an accurate flap-speed answer; integration tests succeed. |
| **4. Desktop UX polish** | Deliver a Windows tray experience with persistent settings. | 1. Build `ChatAssistant/ui/tray.py` with `pystray` or `pywin32` to expose quick actions (start/stop, mute mic, open settings).<br>2. Implement the settings window in `ChatAssistant/ui/settings.py` using `tkinter` or PySide, binding controls to `AssistantState`.<br>3. Promote `bootstrap_assistant()` as the default code path in `ChatAssistant/main.py` and add CLI flags for configuration.<br>4. Document installation/run steps for testers in this README. | Launching `python -m ChatAssistant.main` shows a tray icon and opens settings; state persists across restarts. |
| **5. Hardening & packaging** | Make the assistant reliable for daily use. | 1. Expand automated coverage across audio, telemetry, LLM, and UI layers (see `tests/`).<br>2. Add structured logging, retries, and exception handling around network/audio boundaries.<br>3. Create a packaged build (MSI/exe or installer script) and publish troubleshooting FAQs. | CI pipeline passes; packaged build installs and runs on a fresh Windows machine following documented steps. |

> Tip: Track progress with GitHub Issues that mirror each milestone row above so
> contributors can pick up discrete, testable tasks.
