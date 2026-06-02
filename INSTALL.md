# Installation

## 🚀 Quick Start (recommended)

```powershell
# Install just if you don't have it
winget install Casey.Just    # Windows
# scoop install just          # Windows (alternative)
# brew install just           # macOS
# sudo apt install just       # Debian/Ubuntu
# cargo install just          # Linux (Rust)

git clone https://github.com/sandraschi/speech-mcp
cd speech-mcp
just
```

The interactive recipe dashboard opens in your browser. From there:

```powershell
just bootstrap   # install all dependencies
just serve       # start the server
just web         # start the frontend (if applicable)
```

> **Why not `pip install`?** MCP servers bundle webapps, configs, project scaffolding, and tooling that a flat Python package can't deliver. PyPI offers no safety advantage — it doesn't audit packages either. `just` gives you the complete, ready-to-run stack.

### Claude Desktop (MCPB — Option A)

1. Download `speech-mcp-*.mcpb` from [GitHub Releases](https://github.com/sandraschi/speech-mcp/releases/latest)
2. Drag the file into Claude Desktop (Extensions)
3. Configure API keys in the extension settings (Google, Hume, ElevenLabs as needed)

Build locally: `just mcpb-pack` (requires Node.js for `npx @anthropic-ai/mcpb`).

### Windows desktop (Tauri — full installer)

1. Download **Speech MCP** `*_x64-setup.exe` (NSIS) or `.msi` from [Releases](https://github.com/sandraschi/speech-mcp/releases/latest)
2. Run the installer — launches the cockpit and starts the backend sidecar on **10909**
3. Optional: set API keys via `.env` next to the install or extension docs

Build locally: `just build-native` (Rust, Node 22+, Python 3.12+, PyInstaller). Installers appear under `native/target/release/bundle/`.

FunASR weights are **not** inside the Tauri bundle; use `uv sync --extra funasr` in a dev clone for local STT.

### FunASR local STT (recommended for agents)

speech-mcp uses **[FunASR](docs/providers/funasr.md)** as the default speech-to-text backend (open-weight, no per-minute STT billing).

```powershell
uv sync --extra funasr
Copy-Item .env.example .env
# Edit .env:
# FUNASR_ENABLED=true
# FUNASR_MODEL=FunAudioLLM/Fun-ASR-Nano-2512
# FUNASR_DEVICE=cuda:0
```

Optional **sidecar** (keeps torch out of the main MCP process):

```powershell
uv run python scripts/start_funasr_sidecar.py
# .env: FUNASR_OPENAI_URL=http://127.0.0.1:10910/v1
```

MCP tools: `transcribe_audio_file`, `transcribe_stream_chunk`. Full guide: [docs/providers/funasr.md](docs/providers/funasr.md). Chinese FOSS landscape: [docs/CHINESE_AI_RESEARCH.md](docs/CHINESE_AI_RESEARCH.md). **Humanoid / fleet thesis:** [docs/HUMANOID_VOICE.md](docs/HUMANOID_VOICE.md).

---

## 🐌 Traditional Setup

If you prefer not to use `just`:

1. Install [Python 3.13+](https://python.org) and [uv](https://docs.astral.sh/uv/)
2. Clone and enter the repo:
   ```powershell
   git clone https://github.com/sandraschi/speech-mcp
   cd speech-mcp
   ```
3. Install dependencies:
   ```powershell
   uv sync --all-extras
   ```
   For **FunASR STT only** (lighter than `--all-extras`): `uv sync --extra funasr`
4. Start the server:
   ```powershell
   # stdio mode (for MCP clients like Claude Desktop)
   uv run python -m speech_mcp.server

   # HTTP mode (for web dashboard)
   uv run uvicorn speech_mcp.server:app --port 10909
   ```
5. Open `http://localhost:10909` or the frontend URL.

---

## ❓ Troubleshooting

| Issue | Fix |
|---|---|
| `just` not found | Install via `winget install Casey.Just`, `scoop install just`, or `brew install just` |
| Port conflict | Run `just kill-all` to clear fleet ports (10700–11000) |
| Dependencies out of sync | `uv sync --all-extras` or `uv sync --extra funasr` |
| FunASR `ImportError` | Run `uv sync --extra funasr`; GPU drivers for `FUNASR_DEVICE=cuda:0` |
| STT tools say not configured | Set `FUNASR_ENABLED=true` or `FUNASR_OPENAI_URL` in `.env` |
| Something else | [Open a GitHub issue](https://github.com/sandraschi/speech-mcp/issues) |

---

*See the main [README](README.md) for feature overview and documentation.

---

## Legacy Documentation

_This INSTALL.md was updated with the standard fleet Quick Start template. The original instructions are preserved below._

# Installation & Setup

This guide details how to set up and configure the Speech-MCP gateway.

## ­ƒøá Prerequisites

- **Python 3.12+**
- **Node.js & npm** (for the web dashboard)
- **uv** (recommended for Python dependency management)
- **just** (task runner for common operations)

---

## ­ƒÜÇ Quick Start

1.  **Clone the Repository**:
    ```powershell
    git clone https://github.com/sandraschi/speech-mcp.git
    cd speech-mcp
    ```

2.  **Environment Setup**:
    Initialize the virtual environment and install dependencies:
    ```powershell
    uv sync
    just install
    ```

3.  **Configuration**:
    Create a `.env` file in the root directory:
    ```env
    # Local STT (recommended) — see docs/providers/funasr.md
    FUNASR_ENABLED=true
    FUNASR_MODEL=FunAudioLLM/Fun-ASR-Nano-2512
    FUNASR_DEVICE=cuda:0

    # Cloud TTS / live (optional)
    GOOGLE_API_KEY=your_gemini_key
    HUME_API_KEY=your_hume_key
    ELEVENLABS_API_KEY=your_eleven_key
    ```

4.  **Launch**:
    ```powershell
    just start
    ```
    - **Frontend**: http://localhost:10908
    - **Backend**: http://localhost:10909

---

## ­ƒôí Registry & Ports

| Service | Port | Protocol | Description |
| :--- | :--- | :--- | :--- |
| **Backend** | `10909` | HTTP/REST | FastAPI + MCP SSE + WebSocket |
| **Dashboard** | `10908` | HTTP | React/Vite user interface |

---

## ­ƒÄÖ´©Å Hardware Setup

- **Microphone**: Required for Wake-Word detection and STT. Ensure your default OS microphone is correctly configured.
- **Speakers**: Required for TTS playback. The system uses the default Windows audio output.

---

## ­ƒº¬ Testing the Installation

Run these `just` recipes to verify specific components:

- `just demo-gemini-tags`: Test Gemini emotional synthesis.
- `just fix`: Run the automated diagnostic and linting suite.
- `just reindex`: Update the local RAG knowledge base.
