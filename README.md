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
