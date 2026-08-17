"""
Start FunASR OpenAI-compatible transcription sidecar.

Uses the official funasr-server CLI (FunASR v1.3.3+).
Default port 10914 (fleet-safe). Requires: uv sync --extra funasr

Usage:
    uv run python scripts/start_funasr_sidecar.py
    uv run python scripts/start_funasr_sidecar.py --port 10914 --device cuda:0
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="FunASR OpenAI-compatible sidecar")
    parser.add_argument(
        "--model",
        default=os.getenv("FUNASR_MODEL", "FunAudioLLM/Fun-ASR-Nano-2512"),
        help="Model to pre-load at startup",
    )
    parser.add_argument("--device", default=os.getenv("FUNASR_DEVICE", "cuda:0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("FUNASR_SIDECAR_PORT", "10914")))
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    exe = shutil.which("funasr-server")
    if not exe:
        print("funasr-server not found. Run: uv sync --extra funasr", file=sys.stderr)
        return 1

    cmd = [
        exe,
        "--model",
        args.model,
        "--device",
        args.device,
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]

    print(f"FunASR sidecar: http://{args.host}:{args.port}/v1")
    print(f"  model={args.model}  device={args.device}")
    print(f"Set FUNASR_OPENAI_URL=http://{args.host}:{args.port}/v1 in speech-mcp .env")

    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
