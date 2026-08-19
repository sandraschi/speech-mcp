# Speech-MCP Tools Reference

Full MCP tool surface (41 tools, version 0.6.5). Every tool sets an
`annotations=` hint (`READ_ONLY` = query only, `MUTATING` = changes state,
`DESTRUCTIVE` = can delete/overwrite) and documents a `## Return Format` +
`## Examples` block in its docstring.

Run `uv run python -m speech_mcp` (stdio) and call any tool from an MCP client
(Claude Desktop, Cursor, Windsurf). REST mirrors exist under `/api/v1/*`.

> Feature spec (2026-08-19): `docs/FEATURE_SPEC_2026.md`.

---

## Speech / TTS

### `text_to_speech`
`text_to_speech(text, provider, voice_id, description, ctx)` — `MUTATING`

Synthesize speech and play it immediately on the PC speaker.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `text` | str | required | Text to speak. Gemini supports inline audio tags: `[excited]`, `[whispers]`, `[laughs]`, `[sighs]`, `[fast]`, `[slow]` |
| `provider` | str | `"windows"` | `windows`, `hume`, `gemini`, `gemma`, `elevenlabs` |
| `voice_id` | str | `"default"` | Provider-specific voice name |
| `description` | str | None | **Hume only.** Prose style prompt (e.g. `"warm, slightly melancholic female voice"`) |

**Providers:**

| Provider | Key required | Voice options | Notes |
|---|---|---|---|
| `windows` | No | SAPI5 voices | Always available, instant |
| `hume` | `HUME_API_KEY` | `ITO`, `KORA`, or dynamic | Hume Octave; `description` drives prosody |
| `gemini` | `GOOGLE_API_KEY` | `Kore`, `Aoede`, `Charon`, `Fenrir`, `Orion`, `Puck`, `Leda`, `Zephyr` + more | Gemini 3.1 Flash TTS, inline audio tags |
| `gemma` | No | local | Gemma 4 local, SAPI5 fallback |
| `elevenlabs` | `ELEVENLABS_API_KEY` | account voices | High-fidelity synthesis |

**Returns:** `{"success": true, "provider": "...", "bytes_played": N, "status": "played"}`

**Examples:**
```
Say "Good evening" using the windows provider
Say "[cheerfully] Welcome! [whispers] This part is quiet." using gemini, voice Kore
Say "The reductionist universe..." using hume with description "warm, academic, slightly melancholic"
```

### `text_to_dialogue`
`text_to_dialogue(lines, ctx)` — `MUTATING`

Multi-voice dialogue via ElevenLabs (up to 10 voices), played on the PC speaker.
`lines` is a list of `{"text": str, "voice_id": str}` dicts.

**Returns:** `{"success": true, "provider": "ElevenLabs text_to_dialogue", "lines": N, "voices_used": N, "bytes_played": N, "status": "played"}`

### `play_audio_file`
`play_audio_file(path, ctx)` — `MUTATING` (diagnostics)

Play a `.wav` or `.mp3` file on the system speaker.

**Returns:** `{"success": true, "path": "..."}` or `{"success": false, "error": "..."}`

### `manage_voice_clones`
`manage_voice_clones(action, provider, name, audio_path, voice_id, language, ctx)` — `DESTRUCTIVE` (delete action)

| Parameter | Type | Default | Description |
|---|---|---|---|
| `action` | str | required | `"list"`, `"clone"`, `"delete"` |
| `provider` | str | `"elevenlabs"` | `"elevenlabs"` or `"hume"` |
| `name` | str | None | Display name for a new clone |
| `audio_path` | str | None | Absolute path to the audio sample (WAV/MP3/M4A, >= 5 s) |
| `voice_id` | str | None | Target voice for delete |
| `language` | str | `"en"` | IVC language code (`en`, `de`, `ja`, ...) |

**Returns:** `list` -> `{"voices": [...]}`; `clone` -> `{"voice_id": "..."}`; `delete` -> `{"deleted": true}`.

---

## Speech-to-Text (STT)

### `transcribe_audio_file`
`transcribe_audio_file(file_path, provider, language, ctx)` — `READ_ONLY`

Batch transcription of a local audio file. **FunASR** default (VAD + ASR +
punctuation + speaker diarization in one call), Gemini/Gemma fallbacks.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `file_path` | str | required | Absolute path to WAV/MP3/FLAC |
| `provider` | str | `"funasr"` | `funasr`, `gemini`, or `gemma` |
| `language` | str | `"auto"` | Language code or auto-detect |

**Returns:** `{"success": true, "text": "...", "segments": [...], "formatted": "..."}`

See [docs/providers/funasr.md](providers/funasr.md) for setup (`FUNASR_ENABLED`, sidecar mode on port 10914).

### `transcribe_stream_chunk`
`transcribe_stream_chunk(audio_base64, provider, language, sample_rate, mime_type, ctx)` — `READ_ONLY`

Stateless chunk transcription for stream bridges (base64 audio in, transcript out).

### `streaming_stt`
`streaming_stt(action, audio_b64, sample_rate, ctx)` — `MUTATING`

Streaming online ASR via **sherpa-onnx** (ja/en/de, CPU). Feed int16 PCM
(16 kHz mono) chunks; returns partial transcripts plus an endpoint flag.
Actions: `status`, `reset`, `feed`, `end`.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `action` | str | required | `status`, `reset`, `feed`, or `end` |
| `audio_b64` | str | `""` | Base64 int16 PCM (16 kHz mono), required for `feed` |
| `sample_rate` | int | `16000` | Only 16000 supported by sherpa-onnx |

Enable with `SHERPA_ASR_ENABLED=true` + `uv sync --extra sherpa`. Full guide:
[docs/STREAMING_ASR.md](STREAMING_ASR.md).

### `barge_in_feed`
`barge_in_feed(audio_b64, ctx)` — `MUTATING`

Feed mic audio for barge-in detection. A completed utterance in the return
means the user spoke - interrupt the assistant.

---

## Agentic (sampling)

### `start_evi_session`
`start_evi_session(ctx)` — `READ_ONLY`

Returns WebSocket connection parameters for a Hume EVI real-time session
(requires `HUME_API_KEY`; `HUME_CONFIG_ID` selects an EVI persona).

### `detect_wake_word`
`detect_wake_word(ctx, session_id)` — `MUTATING`

Arms Gemini Multimodal Live VAD for voice activity detection.

### `orchestrate_alexa_pattern`
`orchestrate_alexa_pattern(ctx, user_goal)` — `MUTATING`

Alexa 2.0-style proactive mission orchestration. Uses `ctx.sample()` to generate
a conversational strategy for the goal, interleaving listening + emotional
prosody + adaptive responding.

### `agentic_conversation_workflow`
`agentic_conversation_workflow(goal, ctx)` — `MUTATING`

SEP-1577 autonomous conversation mission. Elicits clarification when the goal is
vague, samples a strategy, and returns a structured mission plan. Requires a
sampling-capable MCP host (Claude Desktop).

---

## Utility

### `manage_domestic_utility`
`manage_domestic_utility(action, type, value, label, ctx)` — `MUTATING`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `action` | str | required | `"set"`, `"query"`, `"cancel"` |
| `type` | str | required | `"timer"`, `"weather"` |
| `value` | str\|int | None | Seconds for timers |
| `label` | str | `"Default"` | Timer label; city name for weather |

Weather fetches live from wttr.in; timers run as asyncio tasks and log on expiry.

### `trigger_action`
`trigger_action(action_type, params, ctx)` — `MUTATING`

Declared IoT bridge. Returns `pending_orchestration` with `requires_bridge` and
`next_steps` - no fake device state. Use with a wired devices-mcp bridge.

| Parameter | Type | Description |
|---|---|---|
| `action_type` | str | `light_on`, `light_off`, `notify` |
| `params` | dict | `{"room": "living_room"}` or `{"message": "..."}` |

---

## Runtime control

### `configure_runtime`
`configure_runtime(action, target, device, ctx)` — `MUTATING`

Switch a speech provider between CPU and GPU at runtime without restarting.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `action` | str | required | `status` or `set_device` |
| `target` | str | `"funasr"` | `funasr` or `sherpa` |
| `device` | str | `"cpu"` | `cpu`, `cuda:0` (funasr); `cpu`, `cuda` (sherpa) |

REST mirror: `GET/POST /api/v1/runtime`.

---

## RAG / Knowledge base

### `search_docs`
`search_docs(query, limit, ctx)` — `READ_ONLY`

Semantic vector search over the speech-mcp documentation corpus (LanceDB +
FastEmbed). Model downloads ~25 MB on first run.

**Returns:** list of `{"filename", "score", "content"}` chunks.

### `ask_docs`
`ask_docs(question, ctx)` — `READ_ONLY`

RAG + LLM sampling. Retrieves relevant chunks then uses `ctx.sample()` to
generate a grounded answer.

**Returns:** `{"answer": "...", "sources": [...]}`

---

## Safety

### `safety_validate_intent`
`safety_validate_intent(text)` — `READ_ONLY`

Pattern-matches text against social-engineering triggers (money transfers,
impersonation, credential phishing, accident-bail scenarios).

**Returns:** `{"safe": bool, "risk_level": "LOW"|"HIGH"|"CRITICAL", "reason": str, "recommendation": str}`

### `safety_log_audit`
`safety_log_audit(text, provider, emotional_intensity)` — `MUTATING`

Writes a forensic audit entry for high-intensity emotional speech. Returns a
confirmation string with a `forensic_trace_id`.

### `safety_verify_auth`
`safety_verify_auth(token)` — `READ_ONLY`

Validates a token against `SPEECH_MCP_AUTH_TOKEN`. Returns bool.

---

## Subtitle revision

### `revise_subtitles`
`revise_subtitles(srt_text, language, series, glossary, ctx)` — `MUTATING`

Homophone / jukugo disambiguation pass over SRT text via a local LLM
(Japanese-focused; `language="ja"`). Returns a change log (original/revised per
cue, applied + flagged counts) a human can review.

**Returns:** `{"success": bool, "revised_srt": str, "changes": [...], "applied_count": int, "flagged_count": int}`

REST mirror: `POST /api/v1/subtitles/revise`; depot endpoints under `/api/v1/transcripts`.

---

## Wake word

### `configure_local_wake_word`
`configure_local_wake_word(ctx, keyword, sleep_keyword, sensitivity, action)` — `MUTATING`

Configure the offline openWakeWord listener. No API key required.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `action` | str | required | `start`, `stop`, `status` |
| `keyword` | str | `"hey_jarvis"` | Wake word (`hey_jarvis`, `computer`, `alexa`, ...) |
| `sleep_keyword` | str | None | Separate stop keyword |
| `sensitivity` | float | `0.5` | Detection sensitivity 0.0-1.0 |

REST mirror: `POST /api/v1/wake_word`.

---

## UI (Prefab Apps)

These tools render interactive inline UIs in Claude Desktop (`@mcp.tool(app=True)`),
all backed by real data:

| Tool | Content |
|---|---|
| `prosody_dashboard` | Per-provider configured / missing-key status |
| `speech_activity_chart` | This session's TTS/STT interaction counts per provider |
| `fleet_health_overview` | Providers, RAG sources, active timers |
| `provider_capability_matrix` | TTS / STT / streaming / cloning / wake-word matrix |
| `latency_benchmark_view` | Honest card: latency is not measured by this server |

---

## Demos

### `run_speech_demo`
`run_speech_demo(demo, ctx)` — `MUTATING`

Execute a hardware-specific speech or capability demo script (e.g. `weather`,
`windows`, `shakespeare`, `price`). Runs the matching `scripts/demos/*.py`.

**Returns:** `{"success": bool, "demo": str, "exit_code": int, "output": str}`

---

## Voice memory (persistent episodic diary)

### `voice_memory_store`
`voice_memory_store(text, kind, speaker, topic, provider, ctx)` — `MUTATING`

Persist a voice episode (tts / stt / note / chat) to the SQLite diary at
`data/speech_mcp.db`. Survives restarts.

**Returns:** `{"success": bool, "episode": {id, ts, kind, text, ...}}`

REST: `GET/POST /api/v1/memory`, `GET /api/v1/memory/search?q=`,
`GET /api/v1/memory/stats`.

### `voice_memory_recall`
`voice_memory_recall(limit, kind, topic)` — `READ_ONLY`

Recent episodes, newest first, optional kind/topic filter.

### `voice_memory_search`
`voice_memory_search(query, limit)` — `READ_ONLY`

Keyword search over episode text/topic/speaker.

---

## Voice macros (phrase -> actions)

### `voice_macros`
`voice_macros(operation, phrase, label, actions, ctx)` — `MUTATING`

Bind spoken phrases to multi-step actions. `operation`: `list` | `create` |
`run` | `delete`. Actions: `{type: tts|timer|weather|memory, ...}`. Unknown
action types are reported, never silently skipped.

**Returns:** `list` -> `macros`; `create` -> stored macro; `run` -> per-action
`results` + `ok_all`; `delete` -> `deleted`.

REST: `GET/POST/DELETE /api/v1/macros`, `POST /api/v1/macros/run`.

---

## Translation bridge

### `translate_text`
`translate_text(text, target_language, provider, model, base_url)` — `READ_ONLY`

Translate via a local LLM (Ollama/LM Studio) - no cloud translation dependency.

**Returns:** `{"success": bool, "translation": str, "provider": str}`

### `translate_speech`
`translate_speech(file_path, target_language, speak, source_language, ...)` — `READ_ONLY`

FunASR transcribe -> local LLM translate -> optional TTS playback.

**Returns:** `{"success": bool, "transcript": str, "translation": str,
"spoken": {...}|null, "errors": [...]}`

REST: `POST /api/v1/translate`.

---

## Sound events

### `detect_sound_events`
`detect_sound_events(file_path, threshold_db, min_duration_s)` — `READ_ONLY`

Model-free energy-based segmentation of a 16-bit PCM WAV: RMS over 50 ms
windows, contiguous loud windows clustered into events. Labels:
`loud_event`, `speech_like` (high duty-cycle), plus silence gaps.

**Returns:** `{"success": bool, "duration_s": float, "duty_cycle": float,
"events": [{start_s, end_s, peak_db, label}], "count": int}`

REST: `POST /api/v1/sound/events` (wav bytes).

---

## Fleet readouts + reading mode

### `spoken_status_readout`
`spoken_status_readout(provider, voice_id)` — `MUTATING`

Speaks a live status readout: providers configured, RAG sources, active
timers, GPU. Real server state, spoken via TTS.

**Returns:** `{"success": bool, "text": str, "spoken": {...}}`

### `read_aloud`
`read_aloud(text, file_path, provider, voice_id)` — `MUTATING`

Reading mode: speak arbitrary text or a text file.

**Returns:** `{"success": bool, "spoken": {...}, "chars": int}`

REST: `POST /api/v1/readout`, `POST /api/v1/read`.

---

## Voice bank

### `manage_voice_bank`
`manage_voice_bank(operation, name, provider, voice_id, source, description)` — `MUTATING`

Named voice profiles routed to a provider + voice id. Register a profile, then
use its `name` directly as `voice_id` in `text_to_speech`. `source` marks the
origin (`elevenlabs`, `cosyvoice`, `gpt-sovits`, `custom`); local cloning needs
the optional model install and is never silently faked.

### `voice_bank_resolve`
`voice_bank_resolve(name)` — `READ_ONLY`

Resolve a profile to `{provider, voice_id}`.

REST: `GET/POST/DELETE /api/v1/voicebank`.

---

## Chat (skill-first)

### `chat_message`
`chat_message(message, personality, skill, provider, model, base_url, remember)` — `MUTATING`

Local LLM chat composed skill-first: loads the skill content (if given) as the
base system prompt, appends the persona framing (`sherlock`, `zen`,
`engineer`, `professor`, `custom`), generates, and optionally stores the
exchange in voice memory.

**Returns:** `{"success": bool, "reply": str, "personality": str, "skill": str}`

REST: `POST /api/v1/chat`, `GET /api/v1/personas`.

---

## Speech analytics

### `speech_analytics`
`speech_analytics(hours)` — `READ_ONLY`

Measured telemetry summary: per-provider calls, avg/p95 latency, success rate,
over the lookback window. Samples auto-recorded by TTS / readout / macro /
translate calls and the REST endpoints.

**Returns:** `{"success": bool, "window_hours": float, "total_calls": int,
"providers": {...}}`

REST: `GET /api/v1/analytics`. The `latency_benchmark_view` Prefab card renders
the same real numbers.
