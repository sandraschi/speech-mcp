"""
Speech-MCP Webapp Entry Point

Runs the FastAPI backend (REST + WebSocket + MCP SSE) on port 10760.
This is the browser-facing mode — NOT for Claude Desktop.

For Claude Desktop, use: python -m speech_mcp.server  (stdio mode)

Usage:
    python -m speech_mcp.webapp
    uv run python -m speech_mcp.webapp
"""

import uvicorn

from speech_mcp.server import app, mcp

if __name__ == "__main__":
    # Mount MCP SSE transport into the FastAPI app
    mcp_app = mcp.http_app(transport="sse")
    app.mount("/mcp", mcp_app)

    # Binding to localhost for security (Docker/Production should override via env)
    uvicorn.run(app, host="127.0.0.1", port=10760)
