# Voice Command Bus (speech-mcp ingress)

Canonical standard: **`D:\Dev\repos\mcp-central-docs\standards\VOICE_COMMAND_BUS.md`**

speech-mcp owns the microphone pipeline:

1. openWakeWord detects the wake word (`FLEET_VOICE_WAKE_KEYWORD`, default `hey_jarvis`; production target **`wakeywakey`** custom ONNX).
2. Records `FLEET_VOICE_COMMAND_SECONDS` (default 6) of audio on the same stream.
3. STT via FunASR when `FUNASR_ENABLED=true` (hook registered at server startup).
4. `POST` **SpeechIntent** to fleet-agent (`FLEET_VOICE_ROUTER_URL`, default `http://127.0.0.1:10996/api/voice/intent`).

## Enable delegation

```powershell
$env:FLEET_VOICE_DELEGATE = "1"
$env:FLEET_VOICE_ROUTER_URL = "http://127.0.0.1:10996/api/voice/intent"
$env:FUNASR_ENABLED = "true"
uv run speech-mcp  # or headless backend on 10909 via start.ps1 -Headless -BackendOnly
```

Then start the listener:

```text
configure_local_wake_word(action="start", keyword="hey_jarvis")
```

## NSSM

Register **speech-mcp backend (10909)** headless with `FLEET_VOICE_DELEGATE=1` and **fleet-agent-mcp (10996)**. See central standard §5.

## Example

> *hey jarvis* … *"boomy go on patrol and report what you found"*

fleet-agent routes to **yahboom-mcp** → `yahboom_agent_mission`.
