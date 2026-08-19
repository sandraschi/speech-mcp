# Speech-MCP Voice Intelligence Features - SPEC 2026-08-19

Eight features, implemented as working MVP (honest, no stubs). Each ships MCP
tools + REST mirrors + webapp surface where useful, reusing the existing
provider/state/depot plumbing.

Scope note: local voice cloning (CosyVoice/GPT-SoVITS) and neural sound-event
classification require external models not bundled in this repo. They ship as a
fully functional **manager / pipeline** with an honest optional-model path
(declared extra, explicit "model not installed" errors) - consistent with how
sherpa-onnx and funasr extras already work.

---

## 1. Persistent voice memory (episodic voice diary)

**Goal**: stop forgetting. Every voice interaction (TTS spoken, STT heard) can
be persisted to a SQLite episodic store and recalled across sessions.

- **Data**: `data/speech_mcp.db` -> `memory_episodes` (id, ts, kind
  [tts|stt|note|chat], speaker, text, topic, provider, meta_json).
- **MCP tools**:
  - `voice_memory_store` (MUTATING) - persist an episode (text, kind,
    speaker, topic optional).
  - `voice_memory_recall` (READ_ONLY) - last N episodes, optional kind filter.
  - `voice_memory_search` (READ_ONLY) - LIKE keyword search over text/topic.
- **REST**: `GET /api/v1/memory`, `POST /api/v1/memory`,
  `GET /api/v1/memory/search?q=`.
- **Webapp**: History page gains a "Voice Memory" panel (list + search + add).

## 2. Real-time translation bridge ("Babel mode")

**Goal**: speak in one language, hear it in another - fully local when possible.

- **Pipeline**: FunASR STT (multilingual) -> local LLM translate (Ollama/LM
  Studio) -> TTS (gemini/gemma/windows).
- **MCP tools**:
  - `translate_text` (READ_ONLY) - translate text via local LLM.
  - `translate_speech` (READ_ONLY) - transcribe an audio file, translate, and
    optionally synthesize the translation to TTS.
- **REST**: `POST /api/v1/translate` (json: {text|file_base64, src, tgt, speak}).
- **Honest limits**: requires FunASR for audio; requires a local LLM reachable
  (errors otherwise). No cloud translation dependency.

## 3. Ambient audio intelligence (sound-event bus)

**Goal**: listen for things other than speech - alarm, clap, glass break, etc.

- **MVP**: energy-based event detection over PCM/WAV - RMS spike clustering,
  loud-event onset/offset, silence segmentation. Deterministic, real, honest.
- **MCP tool**: `detect_sound_events` (READ_ONLY) - analyze a WAV file, returns
  `[{start_s, end_s, peak_db, label: "loud_event"|"silence"|"speech_like"}]`.
- **REST**: `POST /api/v1/sound/events` (wav bytes).
- **Documented upgrade**: swap the heuristic scorer for a neural classifier
  (same return shape). Model download is the only blocker.

## 4. Voice bank + local voice cloning path

**Goal**: manage voice profiles across providers; enable offline cloning.

- **Data**: `voice_profiles` (id, name, provider, voice_id, source
  [elevenlabs|cosyvoice|gpt-sovits], meta_json).
- **MCP tool**: `manage_voice_bank` (MUTATING) - list / register / remove /
  describe profiles.
- **REST**: `GET/POST/DELETE /api/v1/voicebank`.
- **Synthesis routing**: `text_to_speech(voice_id=<bank profile>)` resolves
  registered profiles to their provider + voice_id.
- **Local cloning**: `docs/CLONING_GUARDRAILS.md` + optional `cosyvoice` extra
  declares the model dependency; a `cosyvoice_clone` tool raises a clear
  "install with uv sync --extra cosyvoice" error when the model is absent
  (same declared-extra pattern as funasr/sherpa). No silent fake clone.

## 5. Voice-first productivity (macros + reading mode)

**Goal**: bind spoken phrases to multi-step actions; turn text into speech on
demand.

- **Data**: `voice_macros` (id, phrase, label, actions_json, enabled).
- **MCP tool**: `voice_macros` (MUTATING) - list / create / run / delete.
  `run` executes the bound intent through existing handlers (timer, weather,
  TTS speak, memory note).
- **Reading mode**: `read_aloud` (MUTATING) - speak arbitrary text (or a file
  path) via TTS. Thin wrapper over `text_to_speech` + file read.
- **REST**: `GET/POST/DELETE /api/v1/macros`, `POST /api/v1/macros/run`,
  `POST /api/v1/read`.

## 6. Speech analytics (close the honest gap)

**Goal**: real latency/cost/emotion telemetry instead of "not measured".

- **Data**: `analytics_samples` (id, ts, provider, op, latency_ms, success,
  source, meta_json). TTS/STT tools auto-record a latency sample on each call.
- **MCP tool**: `speech_analytics` (READ_ONLY) - summary (per-provider calls,
  avg/p95 latency, success rate, est. cost).
- **REST**: `GET /api/v1/analytics`.
- **Prefab**: `latency_benchmark_view` card now renders real measured numbers.
- **Webapp**: Analytics strip on the dashboard (KPI: calls, p95 latency).

## 7. Fleet voice readouts

**Goal**: spoken status - "what's the fleet doing?"

- **MCP tool**: `spoken_status_readout` (MUTATING) - composes a status sentence
  from live server state (providers configured, RAG sources, active timers,
  GPU, analytics) and speaks it via TTS.
- **REST**: `POST /api/v1/readout`.
- **Hook**: wake word greeting can trigger a short readout
  (`FLEET_VOICE_READOUT=1`).

## 8. Webapp Chat page (fleet Chat standard + voice-aware)

**Goal**: text chat with personalities, skill-first system prompts, local LLM.

- **Page**: `web/src/components/ChatPage.tsx` - personality selector (4+
  incl. Custom), skill preprompt loaded from `GET /api/skills`, provider/model
  select, localStorage history (100 cap), export .txt, clear, data-testids
  (`chat-page`, `chat-controls`, `chat-messages`, `chat-input`, `chat-send`,
  `chat-export`, `chat-clear`, `personality-select`, `example-prompts`).
- **Backend**: `POST /api/v1/chat` (skill + personality system prompt
  composition, local LLM generation via `local_llm_provider`).
- **MCP tool**: `chat_message` (MUTATING) - same composition, returns reply.

---

## Cross-cutting

- All new tools: `annotations=`, `## Return Format`, `## Examples` docstrings.
- All stores in one SQLite DB `data/speech_mcp.db` (thread-locked, stdlib only).
- New REST routes registered in `server.py`; all return `{success, message, data}`.
- Webapp additions follow existing Tailwind dark theme + data-testid patterns.
- Optional deps (cosyvoice) declared as extras with explicit error messaging.
- Tests: unit tests for storage, macros, translate (mocked LLM), sound events,
  analytics; `-m "not live"` gating preserved.
