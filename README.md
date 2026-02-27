# Speech-MCP (Multi-Provider Speech Gateway)

![Status: Beta](https://img.shields.io/badge/Status-Beta-orange?style=for-the-badge)
![FastMCP: 2.14.5](https://img.shields.io/badge/FastMCP-2.14.5-blue?style=for-the-badge)
![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

SOTA-grade MCP server and web application for industrial voice orchestration, supporting Hume AI (EVI/Octave) and ElevenLabs.

> [!IMPORTANT]
> **Status: Beta (v0.1.0)**. This project is in active development. Features are stable but subject to optimization in upcoming 0.x releases.

## 🚀 Overview

Speech-MCP is a federated gateway for advanced voice AI. It provides a unified MCP interface for text-to-speech, real-time empathic voice sessions, and high-fidelity voice cloning.

## 🛠️ Key Capabilities

- **Hume AI Integration**:
    - **EVI 2/3**: Real-time empathic voice interface with prosody-driven responses.
    - **Octave TTS**: Emotionally aware text-to-speech.
- **ElevenLabs Integration** (Roadmap/Alpha):
    - **Professional Voice Cloning (PVC)**: State-of-the-art neural cloning.
    - **Multilingual TTS**: Support for 32+ languages with emotional nuances.
- **SOTA Webapp**: A premium dark-mode interface with glassmorphism, emotion visualizers, and neural dynamic tracking.

## 📦 Deployment & Setup

### Ports
- **Backend (MCP)**: `10760`
- **Frontend (Web)**: `10761`

### Environment Variables
Create a `.env` file in the root:
```env
HUME_API_KEY=your_hume_key
HUME_CONFIG_ID=your_evi_config_id
ELEVENLABS_API_KEY=your_eleven_key
```

### Installation
```powershell
# Backend
pip install -e .
python -m speech_mcp.server

# Frontend
cd web
npm install
npm run dev
```

## 🧩 MCP Tools

- `text_to_speech`: Synthesize audio across providers.
- `start_evi_session`: Initialize real-time Hume sessions.
- `manage_voice_clones`: Unified identity management (Create/List/Delete).

## ⚖️ Standards & Compliance

- **FastMCP 2.14.5**: Full adherence to modern agentic standards.
- **Dialogic Response Patterns**: All tools return structured metadata (`next_steps`, `recovery_options`, `quality_metrics`) for high-fidelity AI dialogue.
- **Portmanteau Pattern**: Consolidated tool schema to prevent tool explosion.
- **Networking**: Dual-server substrate on port **10760** (FastAPI + MCP SSE).

## 🧠 Agentic Features

### 1. SEP-1577 Sampling
This server supports **Iterative AI Sampling**. When performing complex speech orchestration, tools can request the host LLM to "sample" and suggest cognitive strategies or refine prompts.

**Workflow Example**:
1. Client calls `agentic_conversation_workflow`.
2. Server uses `ctx.sample()` to ask the LLM: *"Suggest a conversational strategy for: [User Goal]"*.
3. Server adopts the suggested strategy and returns a `requires_sampling: true` signal to the agent.

### 2. Dialogic Returns
Tools provide "Dialogue Guidance" to the calling agent.
```json
{
  "success": true,
  "status": "ready_for_dispatch",
  "next_steps": ["Connect to stream_url", "Begin audio playback"],
  "recovery_options": ["Check .env file", "Use windows fallback"]
}
```

### 3. Agentic Workflow Tool
The `agentic_conversation_workflow` tool is a **Mission Orchestrator**. It doesn't just synthesize text; it reasons about the conversation's goal and adjusts provide parameters autonomously.

## 📦 Deployment & Setup

### Launchers (SOTA)
- **`start.bat`**: Professional double-click launcher.
- **`start.ps1`**: PowerShell script that kills zombie processes and spawns the dual-server environment.

### Release Orchestration (SOTA)
For professional deployments, use the `release.ps1` script:
```powershell
# Bump version and tag (patch, minor, or major)
.\release.ps1 -Type patch -Message "feat: add neural dynamic tracking"
```

### CI/CD Pipeline
- **Continuous Integration**: GitHub Actions runs `ruff` and `uv` sync checks on every push.
- **Automated Releases**: Pushing tags (e.g., `v0.1.0`) triggers a GitHub Release with automated binary builds and release notes.

### Installation & Environment
This project is **UV-compatible**.
```powershell
# Install and lock environment
uv sync
uv lock

# Launch
.\start.bat
```
