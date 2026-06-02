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
  <a href="docs/HUMANOID_VOICE.md"><img src="https://img.shields.io/badge/Humanoid_voice-thesis-8b5cf6?style=flat-square" alt="Humanoid voice thesis"></a>
</p>

A modern multi-provider speech gateway featuring **Alibaba FunASR local STT**, **Gemini Live real-time voice chat**, **Gemini 3.1 Flash TTS**, **Hume AI Octave**, and **ElevenLabs** voice cloning — built for **embodied agents and humanoid-scale voice** (wake → understand → fleet act → speak).

### Why this repo matters — humanoids and open speech

Good **speech perception and reply** are load-bearing for humanoids: hands-free commands, noisy environments, structured transcripts for planners, and local STT without per-minute cloud tax. **Chinese open-weight industrial speech** (FunASR, SenseVoice, CosyVoice, and related stacks) is shipping as deployable tooling — ModelScope/HuggingFace weights, ONNX edge, `funasr-server` — aligned with robotics and agent fleets at scale.

**speech-mcp** is the fleet voice layer: **FunASR** default STT, **Voice Command Bus** to fleet-agent (robot missions), optional cloud TTS/live for social quality.

**Read the full thesis and architecture:** [**docs/HUMANOID_VOICE.md**](docs/HUMANOID_VOICE.md)

### The Dual-Core Experience

**MCP Server** — Advanced speech, RAG, and state management for agents and IDEs (Claude Desktop, Cursor, Windsurf).

**Modern Webapp** — A browser-based cockpit for real-time voice conversations, Creative Labs polyglot synthesis, voice clone management, and system monitoring.

---

## FunASR — default local STT (why this repo leads with it)

Chinese open-weight speech stacks are ahead on **industrial ASR**: open weights on ModelScope/HuggingFace, published RTF benchmarks, and deploy paths from **234M ONNX** to **7.7B** GPU — without per-minute cloud STT billing. Among them, **[Alibaba FunASR](docs/providers/funasr.md)** is the integrated default in speech-mcp because it unifies **VAD + ASR + punctuation + diarization** in one `AutoModel()` call and ships a production toolkit (`funasr-server`, ONNX, Docker, native MCP in upstream v1.3.3+).

| What you get | Detail |
|---|---|
| **Speed** | Up to ~170× realtime on GPU, ~17× on CPU (vs ~13× for Whisper-large-v3 in published tables) |
| **Models** | [Fun-ASR-Nano-2512](https://huggingface.co/FunAudioLLM/Fun-ASR-Nano-2512), [SenseVoiceSmall](https://github.com/FunAudioLLM/SenseVoice), Paraformer family |
| **Structured output** | Timestamps, speaker labels; emotion/event tags via SenseVoice |
| **Edge** | PyTorch (`cuda`/`cpu`/`mps`), ONNX INT8, Windows runtime SDK, OpenAI-compatible sidecar on **10910** |
| **MCP tools** | `transcribe_audio_file`, `transcribe_stream_chunk` (default `provider=funasr`) |
| **REST** | `POST /api/v1/transcribe?provider=funasr` |
| **Fleet voice bus** | Post-wake utterance STT when `FLEET_VOICE_DELEGATE=1` ([VOICE_COMMAND_BUS.md](docs/VOICE_COMMAND_BUS.md)) |
| **Papers** | [Fun-ASR (2509.12508)](https://arxiv.org/abs/2509.12508), [FunAudioLLM (2407.04051)](https://arxiv.org/abs/2407.04051), [SenseVoice (2401.04251)](https://arxiv.org/abs/2401.04251) |
| **Upstream** | [modelscope/FunASR](https://github.com/modelscope/FunASR) |

### Quick enable

```powershell
uv sync --extra funasr
Copy-Item .env.example .env
# In .env:
# FUNASR_ENABLED=true
# FUNASR_MODEL=FunAudioLLM/Fun-ASR-Nano-2512
# FUNASR_DEVICE=cuda:0
```

**Sidecar (no torch in speech-mcp process):**

```powershell
uv sync --extra funasr
uv run python scripts/start_funasr_sidecar.py
# .env: FUNASR_OPENAI_URL=http://127.0.0.1:10910/v1
```

**Full guide (env matrix, benchmarks, licensing, sidecar API):** [**docs/providers/funasr.md**](docs/providers/funasr.md)

---

## Chinese FOSS speech — landscape (FunASR first, others linked)

speech-mcp is a **gateway**: cloud TTS/live voice plus **local STT via FunASR**. Other Chinese open models are documented for comparison and future providers — see [**docs/CHINESE_AI_RESEARCH.md**](docs/CHINESE_AI_RESEARCH.md).

| Project | Family | Primary role | speech-mcp | Learn more |
|---|---|---|---|---|
| **[FunASR](docs/providers/funasr.md)** | Alibaba / Tongyi | **Industrial STT** (VAD+punc+diarization) | **Integrated (default STT)** | [funasr.md](docs/providers/funasr.md) |
| **[SenseVoice](https://github.com/FunAudioLLM/SenseVoice)** | FunAudioLLM | Fast multilingual STT + emotion/events | Via FunASR hub models | [CHINESE_AI_RESEARCH.md](docs/CHINESE_AI_RESEARCH.md) |
| **[Fun-ASR](https://github.com/FunAudioLLM/Fun-ASR)** | FunAudioLLM | Nano ASR (2512), low-latency | Via `FUNASR_MODEL` | [funasr.md](docs/providers/funasr.md) |
| **[CosyVoice 2/3](https://github.com/FunAudioLLM/CosyVoice)** | FunAudioLLM | Zero-shot multilingual **TTS**, cloning | Future candidate | [CHINESE_AI_RESEARCH.md](docs/CHINESE_AI_RESEARCH.md) |
| **[ChatTTS](https://github.com/2noise/ChatTTS)** | 2noise | Conversational **TTS** (pauses, laughter) | Future candidate | [CHINESE_AI_RESEARCH.md](docs/CHINESE_AI_RESEARCH.md) |
| **[GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)** | Community | Few-shot **voice cloning** (ZH/JP strong) | Future candidate | [local_voice_alternatives.md](docs/local_voice_alternatives.md) |
| **[Fish Speech](https://github.com/fishaudio/fish-speech)** | Fish Audio | Open TTS / voice clone | Not integrated | [CHINESE_AI_RESEARCH.md](docs/CHINESE_AI_RESEARCH.md) |
| **[WeNet](https://github.com/wenet-e2e/wenet)** | Community | End-to-end ASR toolkit | Not integrated (FunASR preferred here) | [CHINESE_AI_RESEARCH.md](docs/CHINESE_AI_RESEARCH.md) |
| **[FireRedASR](https://github.com/FireRedTeam/FireRedASR)** | Xiaohongshu | Industrial Mandarin/English ASR | Not integrated | [CHINESE_AI_RESEARCH.md](docs/CHINESE_AI_RESEARCH.md) |

**Why FunASR over “just run Whisper”:** one pipeline for agents (segments + speakers + punctuation), faster published RTF on Chinese/multilingual industrial sets, first-class **MCP + OpenAI sidecar** in this repo, and alignment with the FunAudioLLM model line (SenseVoice, CosyVoice) if you add local TTS later.

**Offline duplex conversation** (not batch STT): use [**kyutai-mcp**](https://github.com/sandraschi/kyutai-mcp) (Moshi) alongside speech-mcp — see [local_voice_alternatives.md](docs/local_voice_alternatives.md).

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

**Fleet Voice Command Bus** — With `FLEET_VOICE_DELEGATE=1`, wake → utterance STT → `POST` fleet-agent `/api/voice/intent` (e.g. *"boomy go on patrol…"*). Humanoid-scale pattern: [docs/HUMANOID_VOICE.md](docs/HUMANOID_VOICE.md). Ops: [docs/VOICE_COMMAND_BUS.md](docs/VOICE_COMMAND_BUS.md).

**RAG / Semantic Search** — LanceDB + FastEmbed knowledge base over project docs. `ask_docs` tool uses Claude sampling for grounded Q&A.

**Local AI** — Ollama and LM Studio model discovery and grounded generation.

---

## Documentation

- [**Humanoid voice — thesis & fleet architecture**](docs/HUMANOID_VOICE.md) ← **why speech-mcp / FunASR / China open speech**
- [**FunASR local STT (full guide)**](docs/providers/funasr.md) ← **start here for STT**
- [**Chinese FOSS speech landscape**](docs/CHINESE_AI_RESEARCH.md) ← SenseVoice, CosyVoice, ChatTTS, GPT-SoVITS, …
- [Installation](INSTALL.md) — includes `uv sync --extra funasr`
- [Configuration reference](docs/configuration.md)
- [Tools reference](docs/tools-reference.md) — `transcribe_*` MCP tools
- [Local voice alternatives](docs/local_voice_alternatives.md) ← kyutai-mcp / offline duplex
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

## Distribution (MCPB + Tauri)

| Channel | Command / artifact |
|---------|-------------------|
| **Claude Desktop** | Release `.mcpb` or `just mcpb-pack` |
| **Windows app** | Release NSIS/MSI or `just build-native` |
| **Developers** | `just start` (backend **10909** + Vite **10908**) |

Fleet pattern: [mcp-central-docs/standards/rules/tauri_godot_sota.md](https://github.com/sandraschi/mcp-central-docs/blob/main/standards/rules/tauri_godot_sota.md). Details: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## License

MIT — see [LICENSE](LICENSE).

Contributors: @sandraschi. PRs welcome.
