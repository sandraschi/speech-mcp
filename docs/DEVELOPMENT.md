# Development Documentation

This document covers the technical architecture, technology stack, and development standards for the Speech-MCP system.

## 🏗 Architecture

Speech-MCP is designed as a modular gateway for speech services:

- **FastMCP Substrate**: Manages the life cycle of tools and provides context-aware sampling.
- **FastAPI Bridge**: Exposes the MCP tools via HTTP/SSE and provides WebSocket streaming for audio.
- **Provider Layer**: Pluggable drivers for Gemini, Hume, and ElevenLabs.
- **Wake-Word Engine**: Fully offline detection powered by **openWakeWord**.

### Port Registry
- **10909**: Backend (MCP SSE + REST API + WebSockets)
- **10908**: Frontend (Vite/React Dashboard)

### Native distribution (Tauri 2 + MCPB)

| Artifact | Recipe | Output |
|----------|--------|--------|
| Claude Desktop bundle | `just mcpb-pack` | `dist/speech-mcp-v0.6.3.mcpb` |
| Windows installer | `just build-native` | `native/target/release/bundle/nsis/*.exe`, `msi/*.msi` |

Pipeline (`native/build.ps1`): Vite with `VITE_API_BASE=http://127.0.0.1:10909` → PyInstaller `speech-mcp-backend.exe` → Tauri bundle. Sidecar excludes FunASR/torch (install via `uv sync --extra funasr` separately).

Tag releases run `.github/workflows/release.yml` (wheel + MCPB on `windows-latest` only).

**CI:** single `windows-latest` job (Ruff, Biome, pytest) — no Ubuntu runners.

**Tauri NSIS/MSI (~180 MB):** build on Windows and upload:

```powershell
just publish-release-local tag=v0.6.3
```

Or `just build-native` then `gh release upload v0.6.3 native/target/release/bundle/nsis/*.exe native/target/release/bundle/msi/*.msi --clobber`.

---

## 🛠 Technology Stack

- **Python 3.12+**: Core backend logic.
- **FastMCP**: Standardized MCP tool definitions and sampling.
- **React + Tailwind v4**: Premium web dashboard.
- **openWakeWord**: Offline wake-word detection using ONNX.
- **LanceDB + FastEmbed**: Minimalist RAG for project documentation.

---

## 🛡️ Development Standards

All contributions must adhere to these standards:

1.  **Zero-Diagnostic Policy**: The project must maintain zero warnings from `ruff` (Python) and `biome` (Frontend). Run `just fix` before every PR.
2.  **Clean Code**: Avoid redundant branding (e.g., "Alpha", "SOTA") in component labels or log messages. Use clear, technical descriptors.
3.  **Semantic HTML**: All UI components must use semantic HTML5 tags and have unique IDs for automated testing.
4.  **Tool Integrity**: Never remove existing docstrings or FastMCP decorators.

---

## 📡 Internal Protocols

### WebSockets
- `/ws/stream`: Binary audio stream proxy.
- `/ws/logs`: JSON-formatted system telemetry for the dashboard.

### Logging Payload
Every log entry sent over the WebSocket includes a unique `id` for stable rendering:
```json
{
  "id": "uuid-v4",
  "time": "12:34:56",
  "level": "INFO",
  "context": "wake_word",
  "msg": "Listener started"
}
```
