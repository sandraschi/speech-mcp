---
name: speech-expert
description: Expert guide for speech-mcp - TTS, local/streaming STT, barge-in, wake word, voice command bus, and provider selection.
---

# Speech-MCP Expert

speech-mcp is a multi-provider speech gateway: text-to-speech (TTS), speech-to-text (STT),
realtime voice, wake word, and a fleet voice command bus. It runs as an MCP server (stdio or
HTTP) with a React webapp.

## When to use which STT

| Need | Use | Why |
|------|-----|-----|
| Batch/file transcription | `transcribe_audio_file` (provider `funasr`) | FunASR MLT-Nano: offline, multilingual, VAD+punctuation+diarization |
| Live streaming with partials | `streaming_stt` (sherpa-onnx) | ja/en/de, CPU, emits partials + endpoint |
| Barge-in / interruption | `barge_in_feed` | Completed utterance = interrupt signal |
| Cloud quality, realtime conversation | `start_evi_session` / Gemini Live | Hume EVI or `gemini_live` |
| Tiny chunks / stateless | `transcribe_stream_chunk` | base64 PCM per fragment |

Guidance: default to `funasr` for accuracy + offline; use `streaming_stt` when you need
text as it is spoken (voice agents, live captions); use `barge_in_feed` to let the user
interrupt the assistant (no echo cancellation - gate mic feeding while it speaks).

## TTS providers

`text_to_speech(provider=...)` - `windows` (SAPI5, always works), `gemini` (highest
cloud quality, voice=`Kore` etc.), `hume` (emotional/expressive), `elevenlabs` (needs
`voice_id` from `manage_voice_clones`), `gemma` (local, SAPI fallback).
`text_to_dialogue` = multi-voice ElevenLabs conversation.

## Wake word + voice command bus

- `configure_local_wake_word(action="start|stop|status")` - openWakeWord, offline.
- With `FLEET_VOICE_DELEGATE=1` the listener routes wake -> STT -> `POST fleet-agent
  /api/voice/intent`. `SHERPA_ASR_ENABLED=1` switches capture to streaming (no fixed
  window) with a follow-up turn.

## REST surface

`/api/v1/health` (provider booleans), `/api/v1/diagnostics`, `/api/tools`,
`/api/skills`, `/api/v1/tts`, `/api/v1/voices`, `/api/v1/transcribe`,
`/api/v1/wake_word`, `/api/v1/utility`, `/api/v1/stop`, `/api/v1/shutdown`.

## Config essentials

- FunASR: `FUNASR_ENABLED=true`, `FUNASR_MODEL=FunAudioLLM/Fun-ASR-MLT-Nano-2512`
  (31 langs incl. en/ja/de), `FUNASR_DEVICE=cuda:0|cpu`. Requires `uv sync --extra funasr`.
- Streaming: `SHERPA_ASR_ENABLED=true`, `SHERPA_ASR_LANG=en|ja|de`, `SHERPA_BARGE_IN=true`.
  Requires `uv sync --extra sherpa` + `just sherpa-download`.
- Cloud keys: `GOOGLE_API_KEY`, `HUME_API_KEY`, `ELEVENLABS_API_KEY`.

## Troubleshooting quick hits

- Health `funasr:false` -> funasr extra not installed (`uv sync --extra funasr`) or model
  needs `trust_remote_code` (already set). Device `cpu` vs `cuda:0` mismatch.
- `streaming_stt` unavailable -> `SHERPA_ASR_ENABLED` off or model not downloaded.
- No sound -> providers map in `/api/v1/health`; try `windows` provider first.
- REST auth -> `SPEECH_MCP_AUTH_TOKEN` must be sent as `X-Speech-MCP-Auth`.

Full docs: `docs/STREAMING_ASR.md`, `docs/providers/funasr.md`, `docs/TROUBLESHOOTING.md`.
