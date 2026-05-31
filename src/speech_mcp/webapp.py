"""
Speech-MCP Webapp Entry Point

Runs the FastAPI backend (REST + WebSocket + MCP SSE) on fleet port 10909.

For Claude Desktop, use: python -m speech_mcp.server  (stdio mode)

Usage:
    python -m speech_mcp.webapp
    uv run python -m speech_mcp.webapp
"""

import os

import uvicorn

from speech_mcp.server import app, mcp

if __name__ == "__main__":
    # Mount MCP SSE transport into the FastAPI app
    mcp_app = mcp.http_app(transport="sse")
    app.mount("/mcp", mcp_app)

    port = int(os.getenv("SPEECH_MCP_PORT", "10909"))
    uvicorn.run(app, host="127.0.0.1", port=port)
