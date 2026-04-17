# Speech-MCP (Multi-Provider Speech Gateway)

[![FastMCP Version](https://img.shields.io/badge/FastMCP-3.2.0-blue?style=flat-square&logo=python&logoColor=white)](https://github.com/sandraschi/fastmcp) [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![Linted with Biome](https://img.shields.io/badge/Linted_with-Biome-60a5fa?style=flat-square&logo=biome&logoColor=white)](https://biomejs.dev/) [![Built with Just](https://img.shields.io/badge/Built_with-Just-000000?style=flat-square&logo=gnu-bash&logoColor=white)](https://github.com/casey/just)
[![Status: Industrial](https://img.shields.io/badge/Status-Industrial-green?style=for-the-badge)](https://github.com/sandraschi/speech-mcp)

SOTA-grade MCP server and web application for industrial voice orchestration. This gateway leverages the **April 2026** AI stack, featuring native Generative UI and deep emotional prosody.

---

## 🎭 The Gemini 3.1 Revolution: Emotion Dominance

While other providers offer high fidelity, **Gemini 3.1 Flash TTS wipes the floor with the competition in raw emotional intelligence.**

Through natural language tags (e.g., `[whispers]`, `[happy]`, `[serious]`), Gemini 3.1 can shift its psychological state mid-sentence, providing a level of "acting" that traditional models cannot match.

> [!TIP]
> **Deep Dives**: See our specialized provider guides:
> - [**Gemini 3.1 Deep-Dive**](docs/providers/gemini.md): The SOTA standard for emotional performance.
> - [**Hume AI EVI**](docs/providers/hume.md): The leader in empathic user detection.
> - [**ElevenLabs**](docs/providers/elevenlabs.md): The gold standard for professional voice cloning.

---

## 🛠️ SOTA Technology Stack (April 2026)
This project is built using bleeding-edge standards:
- **FastMCP 3.2.0 (The "Apps" Release)**: Powering Generative UI dashboards and server-side interactive elements.
- **Gemini 3.1 Flash TTS**: Driving the fleet's emotional synthesis and native barge-in.
- **PvPorcupine 3.0**: Industrial-grade local wake-word trigger logic.
- **SEP-1577**: Standardized agentic sampling for conversational strategy.

---

## 🎙️ Key Capabilities

- **Local LLM Elicitation**: Proactive model discovery for Ollama and LM Studio directly via the web interface.
- **Generative UI Dashboards**: FastMCP 3.2 powered real-time prosody and status monitors.
- **Barge-in (Interruptible TTS)**: Gemini Live VAD allows for natural conversation overlap without "babbling."
- **Local Wake-Word**: Picovoice integration for physical activation fallback ("Hey Computer").
- **Empathic Feedback**: Hume EVI v3 for tracking user emotional vectors.

---

## 🔬 Local LLM Infrastructure

Speech-MCP now supports **Dynamic Local Intelligence**. 

1. **Ollama**: Connect via `http://localhost:11434` (Default).
2. **LM Studio**: Connect via `http://localhost:1234`.

The webapp proactively elicites available models on page load, allowing you to switch between local inference clusters without manual configuration. **Semantic Retrieval is fully integrated with Ollama/LM Studio for real-time grounded generation.**

---

---

## 🛠️ Deployment & Setup

### Ports
- **Backend (MCP)**: `10918` (Updated for April 2026 fleet)
- **Frontend (Web)**: `10917`

### Environment Variables
Create a `.env` file in the root:
```env
# Required for SOTA Features
GOOGLE_API_KEY=your_gemini_key
PICOVOICE_API_KEY=your_pvporcupine_key

# Additional Providers
HUME_API_KEY=your_hume_key
ELEVENLABS_API_KEY=your_eleven_key
```

### Installation
```powershell
git clone https://github.com/sandraschi/speech-mcp.git
cd speech-mcp
uv pip install -e .
python -m speech_mcp.server
```

---

## 🛠️ FastMCP 3.2 Tools

- `agentic_conversation_workflow`: **[Hardened]** Autonomous mission orchestrator with clarify-on-ambiguity (`ctx.elicit`).
- `configure_local_wake_word`: Sets up Porcupine monitoring for physical triggers.
- `text_to_speech`: Multi-provider synthesis with Gemini emotion support.
- `Prosody Dashboard`: **[Generative UI]** Real-time emotional telemetry.

---

## 🚀 Industrial Roadmap
- [x] FastMCP 3.2 Upgrade (Apps Release)
- [x] Gemini 3.1 Flash TTS Integration
- [x] SOTA Bidirectional WebSocket Proxy
- [ ] Multimodal Video Synthesis (Roadmap Q3 2026)


## 🛡️ Industrial Quality Stack

This project adheres to **SOTA 14.1** industrial standards for high-fidelity agentic orchestration:

- **Python (Core)**: [Ruff](https://astral.sh/ruff) for linting and formatting. Zero-tolerance for `print` statements in core handlers (`T201`).
- **Webapp (UI)**: [Biome](https://biomejs.dev/) for sub-millisecond linting. Strict `noConsoleLog` enforcement.
- **Protocol Compliance**: Hardened `stdout/stderr` isolation to ensure crash-resistant JSON-RPC communication.
- **Automation**: [Justfile](./justfile) recipes for all fleet operations (`just lint`, `just fix`, `just dev`).
- **Security**: Automated audits via `bandit` and `safety`.
