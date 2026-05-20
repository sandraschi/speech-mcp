# Speech-MCP

<p align="center">
  <a href="https://github.com/casey/just"><img src="https://img.shields.io/badge/just-ready_to_go-7c5cfc?style=flat-square&logo=just&logoColor=white" alt="Just"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/PrefectHQ/fastmcp"><img src="https://img.shields.io/badge/FastMCP-3.2-7c5cfc?style=flat-square" alt="FastMCP"></a>
</p>

A modern multi-provider speech gateway featuring **Gemini Live real-time voice chat**, **Gemini 3.1 Flash TTS**, **Hume AI Octave**, and **ElevenLabs** voice cloning.

### The Dual-Core Experience

**MCP Server** — Advanced speech, RAG, and state management for agents and IDEs (Claude Desktop, Cursor, Windsurf).

**Modern Webapp** — A browser-based cockpit for real-time voice conversations, Creative Labs polyglot synthesis, voice clone management, and system monitoring.

---

## Providers

| Provider | Mode | Quality | Key |
|---|---|---|---|
| `gemini_live` | Real-time conversation | Very good | `GOOGLE_API_KEY` |
| `gemini` | Batch TTS | Highest | `GOOGLE_API_KEY` |
| `gemma` | Batch TTS/STT | SOTA Local | None |
| `hume` | Batch TTS (Octave) | High | `HUME_API_KEY` |
| `elevenlabs` | Batch TTS + voice cloning | High | `ELEVENLABS_API_KEY` |
| `windows` | Batch TTS (SAPI5) | Low | None |

---

## Key Features

**Gemma 4 Native Multimodal** — SOTA 2026 local engine integration. Features native audio/vision encoders for low-latency conversational reasoning. Supports prosody-aware interaction and local-first Zero-STT fallback. Optimized for A4B throughput (100+ t/s).

**Gemini 3.1 Flash TTS** — Highest-quality cloud synthesis (`gemini-3.1-flash-tts-preview`). 31 prebuilt voices, 100+ languages, expressive audio tags (`[whispers]`, `[excited]`, etc.).

**Creative Labs** — Polyglot synthesis demo with 19 languages (European, Slavic, Classical, Experimental, Global), literary samples, voice selection, prosody slider, and tongue-twister panel.

**Voice Cloning** — ElevenLabs Instant Voice Clone (IVC) via file upload. 5-second minimum audio sample. Cloned voices appear in the voice library immediately.

**Offline Wake-Word** — Privacy-first detection using openWakeWord (fully offline, Apache 2.0, no API key).

**RAG / Semantic Search** — LanceDB + FastEmbed knowledge base over project docs. `ask_docs` tool uses Claude sampling for grounded Q&A.

**Local AI** — Ollama and LM Studio model discovery and grounded generation.

---

## Documentation

- [Installation](INSTALL.md)
- [Configuration reference](docs/configuration.md)
- [Local voice alternatives](docs/local_voice_alternatives.md) ← kyutai-mcp / offline
- [Gemini Live voice chat](docs/gemini_live.md) ← new
- [Architecture](docs/architecture.md)
- [openWakeWord](docs/openwakeword.md)
- [Yahboom robot integration](docs/YAHBOOM_RASPBOT_VOICE.md)
- [RAG technical overview](docs/RAG_TECHNICAL_OVERVIEW.md)
- [Modern speech AI](docs/modern_speech_ai.md)

---

## Quick Start

```powershell
git clone https://github.com/sandraschi/speech-mcp
cd speech-mcp
just
```

This opens an interactive dashboard showing all available commands. Run `just bootstrap` to install dependencies, then `just serve` or `just dev` to start.

### Manual Setup

If you don't have `just` installed:
# Clone and install
git clone https://github.com/sandraschi/speech-mcp
cd speech-mcp
uv sync
# Configure keys
cp .env.example .env
# Edit .env — add GOOGLE_API_KEY at minimum
# Start backend
uv run python -m speech_mcp.webapp
# Start frontend (separate terminal)
cd web && npm install && npm run dev
Backend: `http://localhost:10909` — Frontend: `http://localhost:10908`
For Claude Desktop MCP integration see [docs/configuration.md](docs/configuration.md).

## License

MIT — see [LICENSE](LICENSE).

Contributors: @sandraschi. PRs welcome.
