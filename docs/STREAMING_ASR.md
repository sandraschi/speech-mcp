# Streaming ASR & Barge-in (sherpa-onnx)

**Established**: 2026-08-17

speech-mcp ships a **streaming, CPU, local** STT path via
[sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) (k2-fsa) focused on the
languages this fleet cares about: **Japanese, English, German**. It adds
VAD-segmented live transcription and **barge-in** (interrupt while the
assistant is speaking) for the wake -> STT -> reply loop.

## Why sherpa-onnx for barge-in

FunASR is batch/chunk STT - great accuracy, but it transcribes a finished
audio window. Barge-in needs an **online recognizer** that keeps emitting
partials as speech streams in, plus a way to know when the user started
talking again. sherpa-onnx gives the streaming part: online transducer models
with partial results + rule-based **endpoint detection** (trailing-silence),
all on ONNX/CPU (no GPU needed).

> Note: the sherpa-onnx Windows wheel's `VoiceActivityDetector` segfaults
> (access violation in `pop()`), so barge-in here uses the streaming
> recognizer's endpoint detection instead. There is no echo cancellation:
> if the assistant's own TTS reaches the mic it looks like the user - use a
> headset/beamforming in production, or gate mic feeding while the assistant
> speaks (the fleet voice listener does the latter).

## Models (ja / en / de)

| Lang | Model | Notes |
|------|-------|-------|
| en | `csukuangfj/sherpa-onnx-streaming-zipformer-en-2023-06-26` | English streaming transducer |
| ja | `csukuangfj/sherpa-onnx-streaming-zipformer-ar_en_id_ja_ru_th_vi_zh-2025-02-10` | Multilingual (ar/en/id/ja/ru/th/vi/zh); Japanese covered |
| de | `csukuangfj/sherpa-onnx-streaming-zipformer-de-kroko-2025-08-06` | German streaming transducer (Kroko-ASR) |

All three are **transducer** models (`encoder`/`decoder`/`joiner`). Files are
auto-discovered by glob, so per-release filenames don't matter.

## Setup

```powershell
uv sync --extra sherpa
uv run python scripts/download_sherpa_models.py   # en, ja, de
# .env:
# SHERPA_ASR_ENABLED=true
# SHERPA_ASR_LANG=en        # en | ja | de
# SHERPA_BARGE_IN=true
```

Models download into `models/sherpa-onnx/{lang}/` (override with
`SHERPA_MODEL_DIR`).

**Windows note:** if a stray `onnxruntime.dll` exists in `C:\WINDOWS\system32`
(installed by some other app), sherpa-onnx loads it instead of the venv copy
and fails with `requested API version [N] not available`. The provider forces
the venv DLL via `os.add_dll_directory()` - no action needed.

## MCP tools

- `streaming_stt(action="status|reset|feed|end", audio_b64=..., sample_rate=16000)`
  — feed live int16 PCM chunks; returns `{partial, endpoint}`. `end` flushes
  the utterance.
- `barge_in_feed(audio_b64=...)` — feed mic audio; returns a list of
  completed utterance transcripts. A non-empty list means the user spoke
  (interrupt the assistant).

## Fleet voice bus integration

When `SHERPA_ASR_ENABLED` + `SHERPA_BARGE_IN=1`, the fleet voice listener
(`voice_listener.py`) switches from the fixed `command_seconds` capture window
to **streaming endpoint-based capture** after the wake word:

1. Wake word fires -> greeting spoken.
2. The listener streams the mic through the online recognizer, accumulating
   partials, until the user finishes one utterance (trailing-silence endpoint).
3. The transcript is routed via `post_speech_intent` (voice command bus).
4. After the spoken reply, the listener opens a follow-up window (6s) and
   routes the next utterance - a natural turn-taking loop.

For mid-reply interruption (cutting TTS the instant the user starts speaking),
use `barge_in_feed` from the agent or the cloud `gemini_live` path, which
already emits `interrupted` events.

## Health & capabilities

`GET /api/v1/health` reports `providers.sherpa_streaming` and
`features.barge_in`. `GET /api/capabilities` lists `sherpa_streaming` under
`stt` and `streaming`.
