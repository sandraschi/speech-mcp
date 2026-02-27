# Speech-MCP Architecture

## Overview

Speech-MCP uses a **dual-server pattern**: the MCP server (stdio transport for Claude Desktop) and the webapp backend (HTTP/SSE/WebSocket) are separate processes sharing the same tool definitions.

```
Claude Desktop
    │
    │ (stdio JSON-RPC)
    ▼
speech_mcp.server          ← python -m speech_mcp.server
    │
    ├── FastMCP 3.x server
    ├── @mcp.tool: text_to_speech
    ├── @mcp.tool: manage_domestic_utility
    ├── @mcp.tool: trigger_action
    ├── @mcp.tool: search_docs
    └── @mcp.tool: ask_docs (uses ctx.sample → Claude sampling)

Browser Dashboard
    │
    │ (HTTP REST + WebSocket)
    ▼
speech_mcp.webapp          ← python -m speech_mcp.webapp
    │
    ├── FastAPI app (port 10760)
    │   ├── GET  /api/v1/health
    │   ├── GET  /api/v1/search?q=...
    │   ├── GET  /api/v1/voices
    │   ├── WS   /ws/stream (audio proxy, partial)
    │   └── /mcp → FastMCP SSE transport (MCP over HTTP)
    │
    └── Vite React frontend (port 10761)
        ├── VoicesPage
        ├── ToolsPage
        ├── SemanticSearch
        ├── StreamPlayback
        ├── InteractionLab
        ├── CreativeLabs
        └── ServiceLinkage (fleet discovery)
```

## RAG Stack

```
DocumentStore (vector_store.py)
    │
    └── BaseVectorStore (rag_core.py)
            │
            ├── LanceDB 0.29.x  ← embedded, no server needed
            │   └── data/lancedb/speech_docs.lance
            │
            └── FastEmbed 0.7.x
                └── BAAI/bge-small-en-v1.5 (384-dim, ~25MB)
```

Documents are ingested once and persist across restarts. The `ask_docs` tool retrieves the top-8 chunks then calls `ctx.sample()` to generate a grounded answer via Claude's sampling capability.

## TTS Provider Routing

```
text_to_speech(provider="hume"|"elevenlabs"|"windows")
    │
    ├── "hume"        → HumeClient (requires HUME_API_KEY)
    ├── "elevenlabs"  → ElevenLabs client (requires ELEVENLABS_API_KEY)
    └── "windows"     → pyttsx3 local TTS (no API key)

All providers return a stream_url pointing to ws://localhost:10760/ws/stream
```

## FastMCP Version

This server targets **FastMCP 3.0+** (PrefectHQ/fastmcp, GA February 18 2026).

Key 3.x APIs used:
- `@mcp.tool` — decorator without parentheses (preferred 3.x style)
- `ctx.sample()` — replaces deprecated `ctx.session.create_message()`
- `mcp.run_stdio_async()` — stdio transport entry point
- `mcp.http_app(transport="sse")` — SSE transport for webapp mounting

## Port Assignments

| Port | Service |
|---|---|
| 10760 | FastAPI backend (REST + WebSocket + MCP SSE) |
| 10761 | Vite React frontend dashboard |

Ports are in the SOTA fleet range 10700–10800 as per `WEBAPP_PORTS.md`.
