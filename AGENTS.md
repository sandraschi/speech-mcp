# AGENTS.md — speech-mcp

Rules for AI coding agents (Claude, Cursor, Windsurf, Goose) working on this repo.

## Project Identity

- **Name**: speech-mcp
- **Purpose**: Multi-provider speech gateway — Gemini Live, Hume AI, ElevenLabs TTS + voice cloning
- **Owner**: Sandra Schipal, Vienna
- **Fleet role**: Voice AI bridge for the entire fleet — TTS, STT, wake word, RAG

## Architecture Quick Reference

```
FastMCP stdio server  <──>  Claude Desktop / MCP clients
       │
FastAPI REST :10909  <──>  React/Vite frontend :10908
       │
MCP SSE :10909/mcp  <──>  Bridge target for ProxyProvider
       │
Providers (configured via .env)
  ├── Gemini 3.1 Flash TTS      (GOOGLE_API_KEY)
  ├── Hume AI Octave + EVI      (HUME_API_KEY)
  ├── ElevenLabs TTS + Cloning  (ELEVENLABS_API_KEY)
  ├── Gemma 4 local             (no key required)
  └── Windows SAPI5             (no key required)
       │
LanceDB (RAG)  ←  data/lancedb/
       │
openWakeWord (local wake word)  ←  no API key required
```

## Ports

| Service | Port |
|---------|------|
| Frontend (Vite) | 10908 |
| Backend (FastAPI + MCP SSE) | 10909 |

## Code Rules

### Python

- **Python 3.12+** — use modern type hints (`str | None`, `TypeAlias`)
- **Async-first**: all MCP tools must be `async def` — no blocking on event loop
- **Type annotations**: all tool params use `Annotated[T, Field(description="...")]` — no `Args:` blocks
- **No global state** except `_timers` and `_log_queue` in `server.py`
- **Logging**: use `logging.getLogger(__name__)` — never `print()`
- **Line length**: 120 chars (ruff enforces)

### Tool Registration

- Tools registered via `@mcp.tool()` decorator in domain modules under `src/speech_mcp/tools/`
- Portmanteau imports re-exported in `src/speech_mcp/tools/__init__.py`
- All tools return `{"success": bool, ...}` dict
- List/status/stats tools use `@mcp.tool(app=True)` with Prefab UI
- Long-running tools use `@mcp.tool(task=True)` (background tasks)

### Docstrings

- Summary: 1-3 lines
- `## Return Format`: explicit JSON structure
- `## Examples`: 1-3 concrete calls
- No `Args:` blocks — use `Annotated` in signatures

### RAG

- LanceDB vector store at `data/lancedb/`
- Built from `docs/*.md`
- Reindex: `uv run scripts/reindex_docs.py`

## FastMCP 3.2 Sampling & Bridge

- **ctx.sample()**: used in `ask_docs` + `agentic_conversation_workflow` — always for reasoning, never direct LLM calls
- **ctx.elicit()**: used in `agentic_conversation_workflow` for goal refinement
- **ProxyProvider**: bridge to external MCP servers via `MCP_BRIDGE_URLS` env var (comma-separated SSE URLs)
- **MCP SSE transport**: available at `http://127.0.0.1:10909/mcp` for inbound bridging

## Startup

```powershell
# Quick start (webapp)
cd D:\Dev\repos\speech-mcp\web
.\start.ps1

# MCP server only (stdio, for Claude Desktop)
uv run python -m speech_mcp

# Tests
uv run pytest tests/ -v -m "not live"
```

## Forbidden Actions

- **Never commit** `.env`, `__pycache__/`, `*.bak`, secrets
- **Never use ports** 3000, 5000, 5173, 8000, 8080
- **Never call** `os.getenv()` outside `server.py` — read from module-level constants
- **Never block** the event loop
- **Never install packages globally** — use `uv add`
- **Never** use stubs — mark as `not_implemented` or raise `NotImplementedError`

## Key Files

| File | Purpose |
|------|---------|
| `src/speech_mcp/server.py` | FastAPI app + FastMCP server + route registration |
| `src/speech_mcp/webapp.py` | Webapp entry point (uvicorn) |
| `src/speech_mcp/state.py` | Timer store, history, session state |
| `src/speech_mcp/streaming.py` | WebSocket handlers (Gemini Live, STT) |
| `src/speech_mcp/tools/speech.py` | TTS tools (all providers) |
| `src/speech_mcp/tools/agentic.py` | Agentic workflow + sampling |
| `src/speech_mcp/tools/rag.py` | RAG search + ask (ctx.sample) |
| `src/speech_mcp/tools/wake_word.py` | openWakeWord listener |
| `src/speech_mcp/tools/ui.py` | Prefab UI dashboards |
| `src/speech_mcp/tools/monitoring.py` | IoT action bridge |
| `src/speech_mcp/providers/gemini.py` | Gemini TTS/STT provider |
| `web/src/api.ts` | Backend URL + API client |
| `web/start.ps1` | Webapp launcher |

Install docs: follow mcp-central-docs/standards/AGENT_INSTALL_REFERENCE.md
