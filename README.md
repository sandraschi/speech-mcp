# Speech-MCP (Multi-Provider Speech Gateway)

![Status: Production-Ready](https://img.shields.io/badge/Status-Production--Ready-green?style=for-the-badge)
![FastMCP: 3.1.2](https://img.shields.io/badge/FastMCP-3.1.2-blue?style=for-the-badge)
![Release: February 2026](https://img.shields.io/badge/Release-Feb%202026-purple?style=for-the-badge)

SOTA-grade MCP server and web application for industrial voice orchestration, leveraging the latest **February 2026** AI stack.

> [!IMPORTANT]
> **SOTA Technology Context (As of Feb 27, 2026)**:
> This project is built using bleeding-edge standards and models released in the last 10 days:
> - **FastMCP 3.1.2+** (GA: Feb 18, 2026): Powering agentic sampling and session management.
> - **Gemini 3 Pro / Flash** (Released: Feb 19, 2026): Driving the RAG reasoning and strategy sampling.
> - **Gemini 3.1 Flash Image** (Published: Feb 26, 2026): Employed for UI asset generation.
> - **Hume EVI v3 / Octave**: 2026 industry standard for empathic prosody.
> - **ElevenLabs Turbo v2.5**: 2026 industry standard for low-latency neural TTS.
> - **LanceDB + FastEmbed**: Industrial RAG substrate for cognitive persistence.

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
- **Service Linkage Hub (Apps Hub)**: Central discovery portal for navigating the local MCP fleet (OpenClaw style).
- **Interaction Lab**: Domestic utility gateway for timers, weather reports, and IoT (Tapo/Ring) orchestration.
- **Creative Labs**: Expressive reader with poem narration and translation bridge.

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

- `text_to_speech`: Synthesize audio across providers (Hume/Eleven/Windows).
- `start_evi_session`: Initialize real-time Hume EVI sessions.
- `manage_voice_clones`: Unified identity management (Create/List/Delete).
- `agentic_conversation_workflow`: **[SEP-1577]** Mission orchestrator using iterative sampling.
- `orchestrate_alexa_pattern`: Specialized Alexa-style domestic mission logic.
- `search_docs`: Semantic RAG search over tech documentation.
- `ask_docs`: Grounded Q&A using retrieved context + AI sampling.
- `detect_wake_word`: VAD-ready activation trigger.
- `check_vocal_safety`: Intent-based risk analysis for vocal output.

## 🗺️ Roadmap & Next Steps (v0.x)

As a **Beta** release, we have identified several orchestration frontiers and technical debt targets:

### Current Shortcomings
- **Emotion Visualization**: ElevenLabs currently lacks the deep prosody-to-visual mapping available for Hume EVI.
- **Frontend State Persistence**: Audio stream settings do not currently persist across hard refreshes.
- **Agentic Loop Latency**: Iterative sampling (SEP-1577) adds a cognitive overhead of ~2-3 seconds per mission phase.

### Completion Estimates
- [ ] **v0.2.0 (March 2026)**: ElevenLabs real-time emotion mapping.
- [ ] **v0.3.0 (April 2026)**: Local-first persistence layer (SQLite/LanceDB).
- [ ] **v1.0.0 (H2 2026)**: Production-ready industrial stability.

---

## ⚖️ Standards & Compliance

- **FastMCP 3.1.x**: Full adherence to the latest agentic standards (GA Feb 18, 2026).
- **Security Bastion (v0.2.1)**: Hardened authentication and vocal scam detection (Released: Feb 27, 2026).
- **Portmanteau Pattern**: Consolidated tool schema to prevent tool explosion.
- **Networking**: Dual-server substrate on port **10760** (FastAPI + MCP SSE).

## 🧠 Agentic Features & RAG

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
