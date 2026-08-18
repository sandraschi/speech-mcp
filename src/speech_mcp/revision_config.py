"""Subtitle-revision config (torch-free).

Kept separate from server.py so the revision pass (a pure local-LLM feature)
never imports torch/CUDA. Import this module from revise.py instead of
speech_mcp.server.
"""

from __future__ import annotations

import os

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()
REVISE_LLM_MODEL = os.getenv("REVISE_LLM_MODEL", "gemma4:12b").strip()
REVISE_BATCH = int(os.getenv("REVISE_BATCH", "12"))
