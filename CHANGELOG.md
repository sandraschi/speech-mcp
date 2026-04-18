# Changelog — Speech-MCP

All notable changes to this project will be documented in this file.

## [0.4.0] - 2026-04-17

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
