"""PyInstaller + Tauri sidecar entry - dual transport.

- HTTP mode: --http flag OR MCP_PORT/PORT env set (Tauri spawns with --http)
- stdio mode: default fallback (Claude Desktop / IDE clients)
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))


# PyInstaller lazy-import traps (fleet Tauri protocol)
import _datetime  # noqa: F401
import _strptime  # noqa: F401


def main() -> None:
    parser = argparse.ArgumentParser(description="speech-mcp entry point (dual transport)")
    parser.add_argument("--http", action="store_true", help="Run HTTP mode (Tauri sidecar)")
    parser.add_argument("--port", type=int, default=10909)
    args, _ = parser.parse_known_args()

    env_port = os.environ.get("MCP_PORT") or os.environ.get("PORT")
    http_mode = args.http or bool(env_port)
    if env_port:
        args.port = int(env_port)

    if not http_mode:
        from speech_mcp.server import mcp

        asyncio.run(mcp.run_stdio_async(show_banner=False))
        return

    import uvicorn

    from speech_mcp.server import app, mcp

    mcp_app = mcp.http_app(path="/", transport="sse")
    app.mount("/mcp", mcp_app)
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="info")


if __name__ == "__main__":
    main()
