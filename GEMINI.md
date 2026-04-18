# Speech-MCP: System Context

This document provides grounding for the AI agent. Refer to this before performing architectural changes, debugging, or tool development.

## 🛠 Tech Stack
- **Backend**: Python 3.12 + [FastMCP](https://github.com/jlowin/fastmcp) + FastAPI
- **Frontend**: React + Vite + Tailwind v4 + Biome (Linting)
- **Data Layer**: 
    - **RAG**: LanceDB + FastEmbed (`bge-small-en-v1.5`)
    - **Storage**: JSON-based state in `data/`
- **Voice Stack**:
    - **TTS**: Gemini 3.1 Flash (Priority), Hume Octave, ElevenLabs, Windows SAPI5
    - **STT**: Gemini 3.1 Multimodal Live
    - **Wake Word**: **openWakeWord** (Offline ONNX Models)

## 📡 Registry & Ports
- **Backend API**: `http://localhost:10918`
- **Frontend UI**: `http://localhost:10917`
- **WebSocket Gateway**: `ws://localhost:10918/ws/stream`
- **Telemetry Stream**: `ws://localhost:10918/ws/logs` (JSON Payload)

## 🏗 Directory Structure
- `/src/speech_mcp`: Core Python logic and MCP tool definitions
    - `server.py`: API and MCP entry point
    - `streaming.py`: WebSocket audio handlers
    - `tools/`: Modular tool implementations
        - `wake_word.py`: openWakeWord engine integration
        - `speech.py`: TTS / Dialogue synthesis
        - `rag.py`: LanceDB knowledge base
- `/web`: React frontend
- `/docs`: Detailed technical and user documentation
- `/scripts/demos`: Standalone demo scripts for provider testing

## 🧠 Development Standards
1. **Neutral Branding**: Component labels and logs should use technical descriptors (e.g., "Wake-Word Detection"). Avoid redundant status markers like "Alpha" in functional names.
2. **Zero-Diagnostic Policy**: Maintain zero Ruff/Biome warnings. Always run `just fix` before finishing a task.
3. **Semantic HTML**: All interactive elements must have unique, descriptive IDs for automated testing.
4. **Tool Integrity**: Preserve existing docstrings and FastMCP decorators.

---
*Reference global patterns in* `d:/Dev/repos/mcp-central-docs/patterns`
