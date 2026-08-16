# Voice Command Bus (speech-mcp ingress)

Embodied / humanoid context: [HUMANOID_VOICE.md](HUMANOID_VOICE.md)

Canonical standard: **`D:\Dev\repos\mcp-central-docs\standards\VOICE_COMMAND_BUS.md`**

speech-mcp owns the microphone pipeline:

1. openWakeWord detects the wake word (`FLEET_VOICE_WAKE_KEYWORD`, default `hey_jarvis`; production target **`wakeywakey`** custom ONNX).
2. Records `FLEET_VOICE_COMMAND_SECONDS` (default 6) of audio on the same stream.
3. STT via FunASR when `FUNASR_ENABLED=true` (hook registered at server startup).
4. `POST` **SpeechIntent** to fleet-agent (`FLEET_VOICE_ROUTER_URL`, default `http://127.0.0.1:10996/api/voice/intent`).
5. **Speaks the routed result back** (default on; mute with `FLEET_VOICE_SPEAK_REPLY=0`).

## Enable delegation

```powershell
$env:FLEET_VOICE_DELEGATE = "1"
$env:FLEET_VOICE_ROUTER_URL = "http://127.0.0.1:10996/api/voice/intent"
$env:FUNASR_ENABLED = "true"
uv run speech-mcp  # or headless backend on 10909 via start.ps1 -Headless -BackendOnly
```

The listener **auto-starts at backend boot** when `FLEET_VOICE_DELEGATE=1`
(`FLEET_VOICE_AUTOSTART=0` to disable). Manual control:

```text
configure_local_wake_word(action="start", keyword="hey_jarvis")
configure_local_wake_word(action="status")
configure_local_wake_word(action="stop")
```

## Daily loop (practical usage)

```
wakeywakey                                  -> "Hello, mistress." (spoken ack)
"fritz gpu status"                          -> "OK. RTX 4090: 12% load, 9 of 24 GB VRAM"
"opencode assfix devices, run"              -> task sent to the open opencode session
"set timer twenty minutes, then play desguello" -> timer set + Plex music, spoken confirm
sleepsleep                                  -> "Going to sleep." (listener stops)
```

- **Wake word**: `FLEET_VOICE_WAKE_KEYWORD` (default `hey_jarvis`; production
  target is a custom `wakeywakey` ONNX — stock placeholder until trained).
- **Greeting**: `FLEET_VOICE_WAKE_GREETING` (default `Hello, mistress.`; empty = silent).
- **Sleep word**: `FLEET_VOICE_SLEEP_KEYWORD` (default `hey_mycroft` stock
  placeholder). Saying *"{wake word}, sleepsleep"* also stops the listener —
  true bare "sleepsleep" needs a custom ONNX like wakeywakey.
- **Bare commands** route to the default entity (fritz) — no prefix needed.
- **Spoken replies**: on by default, mute with `FLEET_VOICE_SPEAK_REPLY=0`.
- **Timers ring aloud**: speech-mcp announces expiry ("Timer done. <label>").

## NSSM

Register **speech-mcp backend (10909)** headless with `FLEET_VOICE_DELEGATE=1` and **fleet-agent-mcp (10996)**. See central standard §5.

## Example

> *hey jarvis* … *"boomy go on patrol and report what you found"*

fleet-agent routes to **yahboom-mcp** → `yahboom_agent_mission`.

## Dev-workflow commands

`fritz` is the dev-command entity (fleet-agent `dev_ops`, run in-process),
and the registry's `default_entity` — bare commands work without a prefix.
Full table + env: central standard §4b.

## Receivers

Every spoken command lands at one **receiver** (entity): fritz (universal
agent), opencode (dev IDE), boomy (Yahboom car), dreame (D20 Pro robovac),
calibre (ebook library), plexy (movie + audiobook player), alexa (Echo).
Full roster: central standard §4c.

> *hey jarvis* … *"fritz start webapp arxiv"*
> *hey jarvis* … *"fritz gpu status"*
> *hey jarvis* … *"fritz kick invokeai"*
> *hey jarvis* … *"opencode assfix devices, run"* → open opencode session
> *hey jarvis* … *"dreame clean the kitchen"* / *"dreame go home"*
> *hey jarvis* … *"calibre find neuromancer"* / *"calibre open dune"*
> *hey jarvis* … *"plexy play inception"* / *"plexy pause"*
> *hey jarvis* … *"set timer twenty minutes, then play desguello"* → timer + Plex

Replies are spoken back by default (e.g. *"OK. RTX 4090: 12% load, 9 of 24 GB VRAM, 52 C"*).
Set `FLEET_VOICE_SPEAK_REPLY=0` to mute.
