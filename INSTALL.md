# Installation & Setup

This guide details how to set up and configure the Speech-MCP gateway.

## 🛠 Prerequisites

- **Python 3.12+**
- **Node.js & npm** (for the web dashboard)
- **uv** (recommended for Python dependency management)
- **just** (task runner for common operations)

---

## 🚀 Quick Start

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
    - **Frontend**: http://localhost:10917
    - **Backend**: http://localhost:10918

---

## 📡 Registry & Ports

| Service | Port | Protocol | Description |
| :--- | :--- | :--- | :--- |
| **MCP Server** | `10918` | stdio / SSE | Core tool definitions for AI agents |
| **Web API** | `10918` | HTTP/REST | Health and control endpoints |
| **Dashboard** | `10917` | HTTP | React/Vite user interface |
| **Telemetry** | `10918` | WebSocket | Real-time system logs (`/ws/logs`) |

---

## 🎙️ Hardware Setup

- **Microphone**: Required for Wake-Word detection and STT. Ensure your default OS microphone is correctly configured.
- **Speakers**: Required for TTS playback. The system uses the default Windows audio output.

---

## 🧪 Testing the Installation

Run these `just` recipes to verify specific components:

- `just demo-gemini-tags`: Test Gemini emotional synthesis.
- `just fix`: Run the automated diagnostic and linting suite.
- `just reindex`: Update the local RAG knowledge base.
