
## [Unreleased] — 2026-06-14

### Added
- Tauri CORS: 	auri://localhost, http://tauri.localhost, https://tauri.localhost in CORS origins
- Tauri CORS: _TAURI env var toggle with llow_origin_regex for secure WebView access
- build.ps1: auto-copy NSIS installer to dist/ on build
- CUA-NSIS: config-driven smoke test (`scripts/cua-smoke.py`, `scripts/cua-nsis-config.json`)
- CUA-NSIS: `just build-native` + `just cua-nsis-test` recipes
- CUA-NSIS: 11-phase smoke (install, launch, WebView OCR, feature route, diagnostics, uninstall)
- CUA-NSIS: local certification — all 11 phases pass locally (2026-06-14)

### Changed
- CORS: llow_origins=["*"] → explicit origins list for Tauri webview compatibility
# Changelog — Speech-MCP

All notable changes to this project will be documented in this file.

## [0.6.3] - 2026-05-31 (beta)

### Added — Tauri native + MCPB distribution

- **`native/`** — Tauri 2.0 desktop shell (WebView2) + PyInstaller sidecar `speech-mcp-backend` on port **10909**
- **`just build-native`** — full pipeline: Vite (`VITE_API_BASE`) → sidecar → NSIS/MSI under `native/target/release/bundle/`
- **`just mcpb-pack`** — Claude Desktop `.mcpb` from root `manifest.json`
- **Release CI** — tag builds upload wheel, `.mcpb`, and Windows installers together

### Fixed

- Web `HealthPage` TypeScript build (optional health provider/token fields)

## [0.6.2] - 2026-05-31 (beta)

### Added — Humanoid voice thesis & documentation

- **[docs/HUMANOID_VOICE.md](docs/HUMANOID_VOICE.md)** — product thesis: speech as load-bearing HRI for humanoids, Chinese open-weight industrial speech (FunASR default), fleet architecture (mermaid), deployment topologies, operator checklist, safety, roadmap
- README hero + badge linking humanoid doc; expanded FunASR and Chinese FOSS tables
- [docs/CHINESE_AI_RESEARCH.md](docs/CHINESE_AI_RESEARCH.md) rewrite with fleet map
- Cross-links from FunASR guide, Voice Command Bus, Yahboom bridge, INSTALL, integration guide, `llms.txt` / `llms-full.txt`

### Changed — Web visibility

- Dashboard banner: humanoid/fleet voice + links to thesis doc, Help, STT
- Help page: default-open Humanoid section + expanded FunASR / API / FAQ

### Fixed

- Health/MCP metadata version aligned to package version (`0.6.2`)

**Status:** pre-1.0 beta — no Tauri desktop shell in this repo; release ships Python sdist/wheel + GitHub notes. Webapp remains Vite (10908) + FastAPI backend (10909).

## [0.6.1] - 2026-05-31 (beta)

### Added — Fleet Voice Command Bus

- Optional wake → record → FunASR STT → `POST` fleet-agent `/api/voice/intent` when `FLEET_VOICE_DELEGATE=1`
- `voice_bus.py` / `voice_listener.py`; wake-word tool reports `fleet_delegate` and router URL
- Guide: [docs/VOICE_COMMAND_BUS.md](docs/VOICE_COMMAND_BUS.md)

### Changed

- Biome formatter: `lineEnding: lf` for stable web CI on Windows

**Status:** pre-1.0 beta — env names and router contract may change.

## [0.6.0] - 2026-05-31 (beta)

### Added — FunASR local STT

- `FunASRProvider` (native ModelScope + OpenAI-compatible sidecar)
- MCP tools `transcribe_audio_file`, `transcribe_stream_chunk`; REST `POST /api/v1/transcribe?provider=funasr`
- [docs/providers/funasr.md](docs/providers/funasr.md)

### Changed

- CI: Biome web lint, Ruff on `src`/`tests`, Python 3.12, PortAudio for pytest
- GitHub description and topics refreshed

### Added — Gemma 4 Native Multimodal (April 2026)

- `GemmaProvider` local-first STT/TTS prototype; hybrid fallback to cloud Gemini
- Health checks and voice discovery prioritize local engines

**Status:** pre-1.0 beta.

## [0.5.1] - 2026-04-20

### Fixed — Infrastructure Hardening
- Added `src/speech_mcp/__init__.py` to ensure the directory is recognized as a valid Python package in all environments.
- Hardened startup configuration: disabled FastMCP banners and update checks to avoid handshake timeouts in restricted fleet environments.
- Explicitly defined `stdio` transport as the default for MCP communication.
- Synchronized repository dependencies via `uv sync`.

## [0.5.0] - 2026-04-19

### Added — Gemini Live real-time voice chat

- New `VoiceChat` webapp page — full-duplex voice conversation with `gemini-3.1-flash-live-preview`
  - Mic capture via `ScriptProcessor` → downsample 48kHz float32 → 16kHz int16 PCM → binary WS frames
  - Gapless audio playback via `AudioContext` with sequential chunk scheduling
  - Barge-in support: browser sends `{ type: "interrupt" }`, server sends `{ type: "interrupted" }` to flush buffer
  - Input and output transcript overlay in real time
  - Voice selector (9 prebuilt voices) and system prompt/persona config before session start
  - Text injection mid-session (for robot bridge use case)
  - Session state machine: idle → connecting → ready → idle
- New `_handle_gemini_live()` in `streaming.py`
  - Secure proxy: `browser ↔ speech-mcp backend ↔ Gemini Live API` (API key stays server-side)
  - Uses `google-genai` SDK `client.aio.live.connect()` with `LiveConnectConfig`
  - Model: `gemini-3.1-flash-live-preview` with `thinkingLevel="minimal"` for lowest latency
  - Output PCM chunks wrapped in WAV headers per-chunk before forwarding (browser `decodeAudioData` compatibility)
  - Concurrent coroutines: `browser_to_gemini` (audio + control) and `gemini_to_browser` (audio + transcripts)
  - Handles `server_content.interrupted`, `turn_complete`, `output_transcription`, `input_transcription`
  - System prompt and voice passed as WebSocket URL params
- `docs/gemini_live.md` — full documentation: architecture diagram, audio pipeline, message protocol, browser/backend message tables, voice comparison table, robot integration pattern, known limitations

### Added — ElevenLabs voice cloning (VoicesPage now functional)

- `/api/v1/voices` now calls `eleven_client.voices.get_all()` — returns real voice list instead of empty array
- `/api/v1/voices/clone` — new POST endpoint accepting multipart `name` + audio `file`, calls `eleven_client.voices.ivc.create()`
- `/api/v1/tts/wav` extended to support `elevenlabs` provider (returns MP3) and `gemini` provider; accepts `voice_id` param
- Windows SAPI5 voices now enumerated via `pyttsx3.getProperty("voices")` instead of hardcoded `["default"]`
- `VoicesPage.tsx` — clone panel now has real `<input type="file">` wired to `FormData` POST; voice list refreshes after successful clone; preview URL passes `voice_id`; success/error shown in separate styled banners

### Fixed — Gemini streaming (CreativeLabs / Prosody Lab buttons)

- `_handle_gemini` in `streaming.py` replaced: was attempting to use Gemini Multimodal Live WS API which returns raw PCM incompatible with browser `decodeAudioData`; now uses `GeminiProvider.synthesize_wav()` — full WAV sent as single binary frame
- `StreamPlayback.tsx`: added `playKey` to `useEffect` dependency array — re-clicking same text now re-triggers synthesis

### Fixed — Webapp sidebar not showing on startup

- `AppLayout.tsx` fully rewritten using inline styles instead of Tailwind utility classes for layout skeleton
- Root cause: Tailwind v4 Vite plugin was not reliably generating `lg:relative`, `-translate-x-full`, `lg:translate-x-0` classes from dynamic string interpolations; sidebar rendered as `fixed` overlay with zero visible area
- Sidebar is now always in the flex document flow on desktop (not `fixed`); separate `position: fixed` overlay for mobile with CSS media query
- `index.css`: added `html, body, #root { height: 100%; width: 100%; margin: 0; padding: 0 }` — flex layout had nothing to stretch into
- `App.css`: cleared leftover Vite scaffold (`max-width: 1280px; margin: 0 auto; padding: 2rem`) which was constraining `#root`
- Sidebar collapsed state no longer persists across page loads (was silently collapsing sidebar to icon-strip)

### Added — Sidebar nav items

- **Voice Chat** nav item (🗣️) — routes to new `VoiceChat` page
- **Creative Labs** nav item (🧪) — was missing despite page existing



### Fixed — Server startup (breaking bugs)
- `tools/ui.py` imported `fastmcp.ui` which does not exist — replaced with correct
  `prefab_ui` component API (`@mcp.tool(app=True)`, `PrefabApp`, `Metric`, `BarChart`, etc.)
- `server.py` had no `main()` entry point; `pyproject.toml` declared
  `speech-mcp = "speech_mcp.server:main"` causing an `AttributeError` crash on every
  Claude Desktop startup
- Missing `@app.get("/api/v1/voices")` decorator on `api_voices()` — route was silently dropped
- `state.py` eagerly imported `lancedb` + `fastembed` at module level, causing 10–20 s
  startup delay and Claude Desktop timeout; import moved inside `get_store()` (lazy)
- Added `src/speech_mcp/__main__.py` so `python -m speech_mcp.server` works correctly

### Added — Gemini 2.5 Flash TTS
- `providers/gemini.py` rewritten from scratch using `google-genai` SDK
  (replaces deprecated `google-generativeai`)
- Correct model ID: `gemini-2.5-flash-preview-tts`
- Raw PCM output (24kHz 16-bit mono) wrapped in WAV headers via stdlib `wave`
- 31 prebuilt voices documented; audio tag support (`[excited]`, `[whispers]`, etc.)
- `GOOGLE_API_KEY` wired into `.env` and Claude Desktop config env block
- `pyproject.toml`: `google-generativeai` → `google-genai>=1.0.0`

### Added — Real audio playback on PC speaker
- `text_to_speech` tool now **actually plays audio** via `winsound.PlaySound` (stdlib WAV)
  instead of returning a dead `stream_url`
- Three working providers: `windows` (SAPI5), `hume` (Octave REST), `gemini` (2.5 Flash TTS)
- Hume uses `client.tts.synthesize_file()` with `FormatWav()` — correct SDK path
- All synthesis runs in `anyio.to_thread.run_sync` so the async event loop is never blocked
- Temp WAV files are created, played, then deleted — no file accumulation

### Added — Prefab UI tools (real implementation)
- `prosody_dashboard` — `@mcp.tool(app=True)` renders inline dashboard with `Metric`,
  `Badge`, `Row`, `Separator`, `Heading` components
- `speech_activity_chart` — inline `BarChart` of per-session token usage with `Sparkline`-style metrics
- `docs/prefab_ui_reference.md` — source-verified reference for `prefab_ui 0.19.x`
  covering all components, charts, actions, reactive state (`Rx`), and gotchas

### Changed
- `text_to_speech` default provider changed from `gemini` to `windows` (gemini requires API key)
- `manage_voice_clones` Hume path now calls `hume_client.tts.voices.list()` (real API)
  instead of returning a hardcoded stub
- `tools/speech.py` docstring updated to cover all three providers and `voice_id` options

## [0.3.2] - 2026-04-17

### Added
- Grounded generation: RAG retrieval wired into local LLM prompt via Ollama / LM Studio
- Context-aware synthesis: semantic fragments injected directly into the generation prompt
- Provider parity: Ollama and LM Studio both support the new pipeline

## [0.3.1] - 2026-04-17

### Added
- Local LLM elicitation: proactive model discovery for Ollama and LM Studio
- Dynamic model selection in Settings UI dropdown
- Grounded Chat: "Ask AI" mode in Semantic Search with local model awareness

### Fixed
- Ruff linting violations across the codebase
- Biome accessibility issues in Settings and Semantic Search
- Backend host binding hardened to 127.0.0.1; WebSocket error handling improved

## [0.3.0] - 2026-04-17

### Added
- Hume AI EVI & Octave integration
- RAG layer: LanceDB + FastEmbed for semantic documentation search
- SEP-1577 sampling for agentic workflows
- `agentic_conversation_workflow`, `orchestrate_alexa_pattern` tools
- `search_docs`, `ask_docs` (RAG + grounded Q&A)
- `safety_validate_intent` for vocal intent risk analysis
- Live weather via `manage_domestic_utility` + wttr.in

## [0.2.0-alpha] - 2026-02-27

### Added
- ElevenLabs roadmap integration
- Multi-provider gateway architecture
- SOTA UI for Tools and Voices pages
- Service Linkage Hub for central fleet discovery
- Alexa-style domestic utility logic (timers, weather, IoT)

## [0.1.0] - 2026-02-27

### Added
- Initial Hume AI integration (Octave v1, EVI v2/v3)
- FastMCP server with `text_to_speech`, `start_evi_session`, `manage_voice_clones`
- Webapp baseline
- Git repository and GitHub remote setup

