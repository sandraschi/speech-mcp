# VoiceStudio — local TTS / voice cloning sidecar (optional)

> **Status:** optional provider, **disabled by default** (`VOICESTUDIO_ENABLED=false`).
> speech-mcp never embeds VoiceStudio code — it calls a running instance over
> HTTP/MCP. VoiceStudio is **AGPL-3.0-only** (commercial license available);
> speech-mcp stays MIT via this process boundary.

**Upstream:** https://github.com/debpalash/VoiceStudio

## Why this exists

speech-mcp's local story is STT-strong (FunASR default, sherpa-onnx streaming)
but TTS-weak without cloud keys (ElevenLabs/Gemini) or flat SAPI5.
VoiceStudio fills exactly the TTS/clone hole: local cloning, voice design,
and 17 engines (OmniVoice default, IndexTTS 2.5, CosyVoice 3, VoxCPM2, …)
behind one MCP + OpenAI-compatible surface.

## Architecture

```text
speech-mcp (10908/10909) ──HTTP/MCP──> VoiceStudio backend :3900 (/mcp, /v1/audio/*)
                          ──optional──> Rust sidecar :3902 (dictation toggle/insert)
```

| VoiceStudio piece | Port | speech-mcp uses it for |
|---|---|---|
| Python backend | 3900 | `generate_speech`, `clone_voice`, `list_voices`, `check_health`, `POST /v1/audio/transcriptions` |
| Rust control sidecar | 3902 | manual dictation (`toggle`), not wired into MCP tools |
| MCP Streamable HTTP | 3900/mcp | TTS + clone path (`X-VoiceStudio-Client-Id: speech-mcp`) |

No port conflicts with the fleet pair (10908/10909) or FunASR sidecar (10914).

## Quick enable

1. Start VoiceStudio: Electron app (Windows MSI), or Docker backend.
   Pre-install the OmniVoice model — the first `generate_speech` otherwise
   downloads ~2.3GB inside the request timeout.
2. `.env`:

```env
VOICESTUDIO_ENABLED=true
VOICESTUDIO_URL=http://127.0.0.1:3900
VOICESTUDIO_CLIENT_ID=speech-mcp
VOICESTUDIO_TIMEOUT_S=120
# Optional files-mode shared dir (keeps WAVs out of agent context):
# VOICESTUDIO_BASE_PATH=D:/Dev/repos/speech-mcp/data/voicestudio
```

3. Restart speech-mcp. `text_to_speech(provider="voicestudio")` now works;
   health shows under `/api/v1/health` → `voicestudio: {available: true}`.

## MCP tools

| Tool | Purpose |
|---|---|
| `text_to_speech(provider="voicestudio", voice_id="<profile|name>")` | Local synthesis, played on server speaker |
| `manage_voice_clones(action, provider="voicestudio", ...)` | `list` voices, `clone` from ref audio (consent only), `delete` is ElevenLabs-only |
| `manage_voice_bank(operation="register", provider="voicestudio", ...)` | Named profile → VoiceStudio `profile_id`; use name as `voice_id` in TTS |
| `transcribe_audio_file(provider="voicestudio")` | Fallback batch STT via OpenAI-compatible endpoint (FunASR stays default) |

Per-agent voices: `VOICESTUDIO_CLIENT_ID` binds this server's default voice.
Set it per deployment, or pass an explicit `profile_id` per call. Manage
bindings on the backend: `curl localhost:3900/api/mcp/bindings`.

## Configuration reference

| Variable | Default | Description |
|---|---|---|
| `VOICESTUDIO_ENABLED` | `false` | Opt-in switch for the sidecar provider |
| `VOICESTUDIO_URL` | `http://127.0.0.1:3900` | VoiceStudio backend base URL |
| `VOICESTUDIO_CLIENT_ID` | `speech-mcp` | Sent as `X-VoiceStudio-Client-Id` (per-agent voice binding) |
| `VOICESTUDIO_TIMEOUT_S` | `120` | MCP/HTTP timeout (min 10s; first model download needs more) |
| `VOICESTUDIO_BASE_PATH` | — | Shared dir for files-mode I/O; unset → base64 path args refused by backend |

## Security / privacy notes

- MCP transport is **unauthenticated, loopback-only**. Never expose :3900 to
  the open internet. Behind Tailscale/reverse proxy use HTTPS/WSS.
- Docker/remote agents: set `OMNIVOICE_MCP_ALLOWED_HOSTS` on the backend and
  mount one shared dir at the same path on both sides when using `BASE_PATH`.
- Clone only consent-verified voices. Keep the AI watermark on. Model weights
  carry their own licenses (default OmniVoice weights: CC-BY-NC) — review
  before commercial use.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `VoiceStudio not configured` | Set `VOICESTUDIO_ENABLED=true` and restart |
| `VoiceStudio backend not reachable` | Open the Electron app or `docker compose up`; check `VOICESTUDIO_URL` |
| First synthesis times out | Install the model via Model Catalogue first, or raise timeouts on both sides |
| `path arguments are refused` | Set `VOICESTUDIO_BASE_PATH` to a dir visible to both processes |
| Empty audio returned | Check backend GPU queue (`OMNIVOICE_GPU_QUEUE_TIMEOUT_S`); view backend logs |

## Declared doubles (tests)

`tests/test_voicestudio.py` mocks httpx at the network boundary (disabled-by-
default, unavailable-backend, and synthesized-WAV paths). No live VoiceStudio
needed for CI (`pytest -m "not live"`).
