# Speech-MCP

<p align="center">
  <a href="https://github.com/sandraschi/speech-mcp/actions/workflows/ci.yml"><img src="https://github.com/sandraschi/speech-mcp/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/sandraschi/speech-mcp/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="MIT License"></a>
  <a href="https://github.com/casey/just"><img src="https://img.shields.io/badge/just-ready_to_go-7c5cfc?style=flat-square&logo=just&logoColor=white" alt="Just"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://biomejs.dev"><img src="https://img.shields.io/badge/Biome-2.4-60a5fa?style=flat-square" alt="Biome"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/PrefectHQ/fastmcp"><img src="https://img.shields.io/badge/FastMCP-3.2-7c5cfc?style=flat-square" alt="FastMCP"></a>
  <a href="docs/providers/funasr.md"><img src="https://img.shields.io/badge/FunASR-local_STT-orange?style=flat-square" alt="FunASR"></a>
</p>

A modern multi-provider speech gateway featuring **Alibaba FunASR local STT**, **Gemini Live real-time voice chat**, **Gemini 3.1 Flash TTS**, **Hume AI Octave**, and **ElevenLabs** voice cloning.

### The Dual-Core Experience

**MCP Server** — Advanced speech, RAG, and state management for agents and IDEs (Claude Desktop, Cursor, Windsurf).

**Modern Webapp** — A browser-based cockpit for real-time voice conversations, Creative Labs polyglot synthesis, voice clone management, and system monitoring.

---

## FunASR — local STT, no subscription tax

Chinese open-weight speech AI is the breakout story of 2025–2026: industrial ASR with **open weights**, **arxiv-backed benchmarks**, ModelScope/HuggingFace hubs, and edge variants from **234M to 7.7B** — all without per-minute cloud billing.

speech-mcp integrates **[Alibaba FunASR](docs/providers/funasr.md)** as the default STT backend:

| What you get | Detail |
|---|---|
| **Speed** | Up to 170× realtime on GPU, ~17× on CPU (vs ~13× for Whisper-large-v3) |
| **One pipeline** | VAD + ASR + punctuation + speaker diarization in a single call |
| **Structured output** | Timestamps, speaker labels, emotion tags (SenseVoice) |
| **Edge options** | PyTorch GPU/CPU, ONNX INT8, Windows SDK, `funasr-server` sidecar |
| **Agent tools** | `transcribe_audio_file`, `transcribe_stream_chunk` |
| **Papers** | [Fun-ASR (2509.12508)](https://arxiv.org/abs/2509.12508), [FunAudioLLM (2407.04051)](https://arxiv.org/abs/2407.04051) |

```powershell
uv sync --extra funasr
# .env: FUNASR_ENABLED=true
```

Full research write-up, model zoo, benchmarks, and deployment matrix: **[docs/providers/funasr.md](docs/providers/funasr.md)**

---

## Providers

| Provider | Mode | Quality | Key |
|---|---|---|---|
| **`funasr`** | **Batch + chunk STT (local)** | **Highest local speed** | **`FUNASR_ENABLED`** |
| `gemini_live` | Real-time conversation | Very good | `GOOGLE_API_KEY` |
| `gemini` | Batch TTS | Highest | `GOOGLE_API_KEY` |
| `gemma` | Batch TTS/STT | SOTA Local | None |
| `hume` | Batch TTS (Octave) | High | `HUME_API_KEY` |
| `elevenlabs` | Batch TTS + voice cloning | High | `ELEVENLABS_API_KEY` |
| `windows` | Batch TTS (SAPI5) | Low | None |

---

## Key Features

**FunASR Local STT** — Alibaba Tongyi Fun-ASR-Nano / SenseVoice integrated natively. Structured transcripts with speakers and timestamps. OpenAI-compatible sidecar on port 10910. See [FunASR guide](docs/providers/funasr.md).

**Gemma 4 Native Multimodal** — SOTA 2026 local engine integration. Features native audio/vision encoders for low-latency conversational reasoning. Supports prosody-aware interaction and local-first Zero-STT fallback. Optimized for A4B throughput (100+ t/s).

**Gemini 3.1 Flash TTS** — Highest-quality cloud synthesis (`gemini-3.1-flash-tts-preview`). 31 prebuilt voices, 100+ languages, expressive audio tags (`[whispers]`, `[excited]`, etc.).

**Creative Labs** — Polyglot synthesis demo with 19 languages (European, Slavic, Classical, Experimental, Global), literary samples, voice selection, prosody slider, and tongue-twister panel.

**Voice Cloning** — ElevenLabs Instant Voice Clone (IVC) via file upload. 5-second minimum audio sample. Cloned voices appear in the voice library immediately.

**Offline Wake-Word** — Privacy-first detection using openWakeWord (fully offline, Apache 2.0, no API key).

**RAG / Semantic Search** — LanceDB + FastEmbed knowledge base over project docs. `ask_docs` tool uses Claude sampling for grounded Q&A.

**Local AI** — Ollama and LM Studio model discovery and grounded generation.

---

## Documentation

- [**FunASR local STT (full guide)**](docs/providers/funasr.md) ← **open-weight Chinese ASR, benchmarks, edge deploy**
- [Installation](INSTALL.md)
- [Configuration reference](docs/configuration.md)
- [Local voice alternatives](docs/local_voice_alternatives.md) ← kyutai-mcp / offline
- [Chinese AI speech research](docs/CHINESE_AI_RESEARCH.md)
- [Gemini Live voice chat](docs/gemini_live.md)
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

```powershell
git clone https://github.com/sandraschi/speech-mcp
cd speech-mcp
uv sync
cp .env.example .env
# Edit .env — add GOOGLE_API_KEY for cloud TTS; FUNASR_ENABLED=true for local STT
uv run python -m speech_mcp.webapp
cd web
npm install
npm run dev
```

Backend: `http://localhost:10909` — Frontend: `http://localhost:10908`

For Claude Desktop MCP integration see [docs/configuration.md](docs/configuration.md).

## License

MIT — see [LICENSE](LICENSE).

Contributors: @sandraschi. PRs welcome.
