"""Runtime-settable device configuration.

Defaults come from env (FUNASR_DEVICE / SHERPA_PROVIDER) at first read, but the
device can be flipped at runtime via the configure_runtime MCP tool, the REST
endpoint /api/v1/runtime, or the webapp Settings page - without restarting the
server. Providers reload their model when the device changes.
"""

from __future__ import annotations

import os
import threading

_lock = threading.Lock()
_funasr_device: str | None = None  # None -> env default
_sherpa_device: str | None = None  # None -> env default


def funasr_device() -> str:
    with _lock:
        return _funasr_device or os.getenv("FUNASR_DEVICE", "cuda:0")


def set_funasr_device(device: str) -> str:
    global _funasr_device
    d = device.strip().lower()
    if d in ("cuda", "cuda:0"):
        d = "cuda:0"
    elif d == "cpu":
        d = "cpu"
    else:
        raise ValueError("funasr device must be 'cpu' or 'cuda:0'")
    with _lock:
        _funasr_device = d
        return d


def sherpa_device() -> str:
    with _lock:
        return _sherpa_device or os.getenv("SHERPA_PROVIDER", "") or "cpu"


def set_sherpa_device(device: str) -> str:
    global _sherpa_device
    d = device.strip().lower()
    if d in ("cuda", "cuda:0"):
        d = "cuda"
    elif d == "cpu":
        d = "cpu"
    else:
        raise ValueError("sherpa device must be 'cpu' or 'cuda'")
    with _lock:
        _sherpa_device = d
        return d


def snapshot() -> dict:
    return {
        "funasr": funasr_device(),
        "sherpa": sherpa_device(),
    }
