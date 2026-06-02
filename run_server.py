"""PyInstaller + Tauri sidecar entry — HTTP web bridge on port 10909."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))


def main() -> None:
    parser = argparse.ArgumentParser(description="speech-mcp HTTP web bridge")
    parser.add_argument("--http", action="store_true", help="Run HTTP (required for Tauri)")
    parser.add_argument("--port", type=int, default=10909)
    args = parser.parse_args()

    if not args.http:
        parser.error("Tauri sidecar requires --http")

    import uvicorn

    from speech_mcp.server import app, mcp

    mcp_app = mcp.http_app(transport="sse")
    app.mount("/mcp", mcp_app)
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="info")


if __name__ == "__main__":
    main()
