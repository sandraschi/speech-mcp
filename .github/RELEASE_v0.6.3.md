## Beta (pre-1.0)

Speech-MCP **0.6.3** ships **fleet-standard distribution**: Claude Desktop **MCPB** plus a **Tauri 2** Windows installer (NSIS + MSI) bundling the React cockpit and PyInstaller backend sidecar.

### Install options

| Channel | Artifact | Use case |
|---------|----------|----------|
| **Claude Desktop** | `speech-mcp-v0.6.3.mcpb` | Drag-and-drop MCP extension (stdio server) |
| **Windows desktop** | `Speech MCP_*_x64-setup.exe` (NSIS) or `.msi` | Full webapp + API on **10909** without separate `just start` |
| **Python** | `.whl` / sdist | `uv pip install` / CI integrators |

All five artifacts are on this release page. Tauri installers are produced on a **local Windows** machine (`just build-native` or `just publish-release-local`), not GitHub Actions.

### Tauri native app

- **UI:** embedded Vite build → talks to `http://127.0.0.1:10909`
- **Sidecar:** `speech-mcp-backend.exe` (PyInstaller); FunASR/torch **not** bundled — install separately with `uv sync --extra funasr` if you need local STT outside the desktop bundle
- **Build locally:** `just build-native` (Rust + Node + Python + PyInstaller required)

### MCPB package

- Root `manifest.json` — MCP server `python -m speech_mcp.server`
- Pack: `just mcpb-pack`

### Since v0.6.2

- Humanoid voice thesis docs and web visibility (unchanged behavior)
- Release pipeline now includes **MCPB + Tauri** alongside Python wheels

### Docs

- [docs/HUMANOID_VOICE.md](https://github.com/sandraschi/speech-mcp/blob/main/docs/HUMANOID_VOICE.md)
- [docs/DEVELOPMENT.md](https://github.com/sandraschi/speech-mcp/blob/main/docs/DEVELOPMENT.md) — `build-native`, `mcpb-pack`

Full changelog: [CHANGELOG.md](https://github.com/sandraschi/speech-mcp/blob/main/CHANGELOG.md)
