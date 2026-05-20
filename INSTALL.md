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
| Dependencies out of sync | `uv sync --all-extras` |
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
    # Required for Wake-Word & Transcription
    GOOGLE_API_KEY=your_gemini_key

    # Optional Speech Providers
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
