# Muse Voice Transcribe — Meta's Real-Time Diarized ASR

> **Why this matters:** Meta Superintelligence Labs released Muse Voice Transcribe on
> 2026-09-01 — one model doing streaming ASR, speaker diarization (20+ speakers), and
> end-of-turn detection, at $0.18/hour. speech-mcp integrates it as a cloud STT provider
> alongside local FunASR: use FunASR for offline/no-subscription transcription, use Muse
> when you specifically need live, continuously-diarized transcription (e.g. a call in
> progress) rather than a batch upload.

---

## API surface (confirmed against Meta's own client recipe)

Source: [meta-models/meta-model-cookbook](https://github.com/meta-models/meta-model-cookbook),
`06_muse_voice/01_voice_api_fundamentals/` (`utils.py`, `transcribe_stream.py`, `transcribe_file.py`).

| Endpoint | Protocol | Notes |
|---|---|---|
| `https://api.meta.ai/v1/asr/transcribe` | HTTP POST, multipart, `Authorization: Bearer <key>` | One-shot file transcription. Caps: 32MB body / 10 minutes of audio. |
| `wss://api.meta.ai/v1/asr/realtime` | WebSocket | Credential rides inside the JSON handshake (`authorization.accessToken`), not a header. Audio as raw binary PCM frames (mono 16-bit, 16kHz or 24kHz). Ends with `{"type":"endStream"}`. |

Realtime events are tagged by `type`: `session` (handshake ack), `transcript` (partial/final,
cumulative), `speaker`, `speechComplete` (correlate turns by `turnId`), `error`.

Modes: `PUSH_TO_TALK`, `ENDPOINTING`, `DIARIZATION` (speech-mcp always requests `DIARIZATION`).

---

## speech-mcp integration

### Enable

`.env`:

```env
MUSE_ENABLED=true
MUSE_API_KEY=your-meta-model-api-key
MUSE_MODEL=muse-voice-transcribe-1.0
```

No new dependency or `uv sync --extra` needed — `websockets` and an HTTP client are already
core dependencies of this repo (used the same way by `providers/gemini.py` and
`providers/funasr.py`'s sidecar mode).

### MCP tools

| Tool | Purpose |
|---|---|
| `transcribe_audio_file(file_path, provider="muse")` | Batch — one file, diarized turns, same return shape as FunASR |
| `transcribe_stream_chunk(audio_base64, provider="muse")` | Stateless single chunk (writes a temp file, calls the file endpoint) |
| `muse_transcribe_stream(action, audio_b64)` | Realtime — `start`/`feed`/`end`/`status` over one continuous diarized session, so speaker identity stays consistent across a whole call instead of resetting per chunk |

**Structured return (batch):**

```json
{
  "success": true,
  "provider": "muse",
  "model": "muse-voice-transcribe-1.0",
  "text": "full transcript",
  "segments": [
    {"speaker": "A", "start_s": 0.12, "end_s": 3.45, "text": "..."}
  ],
  "formatted": "[00.12s -> 03.45s] [Speaker A]: ..."
}
```

**Realtime event stream (`muse_transcribe_stream`):**

```json
{"success": true, "action": "feed", "events": [
  {"type": "speaker", "label": "A"},
  {"type": "speechComplete", "turnId": 3, "speaker": "A", "transcript": "..."}
]}
```

### REST

```http
POST /api/v1/transcribe/file?provider=muse&language=auto
POST /api/v1/transcribe/batch?provider=muse&language=auto
```

Both default to `provider=funasr` when the query param is omitted, so existing callers are
unaffected.

### Webapp

- **Batch Transcription page** — provider dropdown (funasr / gemini / gemma / muse) next to
  the language selector; export to SRT/VTT/TXT works unchanged since Muse's turns are
  normalized into the same `segments` shape FunASR already produces.
- **Live Transcribe page** — captures mic (`getUserMedia`) plus, optionally, the other side
  of a call via `getDisplayMedia({audio:true})` (tab or full-system audio), mixes both
  client-side, and streams PCM to `wss://<backend>/ws/stream?provider=muse`. Renders a
  live-scrolling, speaker-labeled transcript as `speechComplete` events arrive.

---

## Compliance note

Neither the MCP tool nor the webapp live page triggers a call platform's own recording
indicator (e.g. Teams' recording banner), since capture happens outside that platform. In
Austria/EU, transcribing a call generally needs the same consent as recording it — make sure
other participants know before using this on a call they haven't agreed to.

---

## Configuration reference

| Variable | Default | Description |
|---|---|---|
| `MUSE_ENABLED` | `false` | Enables the Muse provider |
| `MUSE_API_KEY` | — | Meta Model API key (`dev.meta.ai`) |
| `MUSE_MODEL` | `muse-voice-transcribe-1.0` | Model id |

---

## Comparison with FunASR (fleet neighbor)

| | Muse Voice Transcribe | FunASR |
|---|---|---|
| Hosting | Cloud (Meta Model API) | Local (GPU/CPU) or sidecar |
| Cost | $0.18/hour | Hardware only |
| Continuous diarization across a live session | Yes (`muse_transcribe_stream`) | No — batch/chunk only |
| Privacy | Audio leaves the device | Fully offline |
| Languages | 70+ (25 verified at launch) | 31 (Fun-ASR-MLT-Nano) |

Use FunASR for offline/no-subscription batch work; use Muse for live, speaker-tracked
transcription of an in-progress call.
