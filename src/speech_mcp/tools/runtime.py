"""Runtime device control: flip CPU/GPU for funasr + sherpa without restarting."""

from __future__ import annotations

import logging
from typing import Annotated

from fastmcp import Context, FastMCP
from pydantic import Field

logger = logging.getLogger(__name__)


def register_runtime_tools(mcp: FastMCP, sherpa_asr) -> None:
    @mcp.tool()
    async def configure_runtime(
        action: Annotated[str, Field(description="Operation: status or set_device.")],
        target: Annotated[str, Field(description="Provider to configure: funasr or sherpa.")] = "funasr",
        device: Annotated[str, Field(description="Device: cpu, cuda:0 (funasr) or cpu, cuda (sherpa).")] = "cpu",
        ctx: Context | None = None,
    ) -> dict:
        """
        Switch a speech provider between CPU and GPU at runtime.

        FunASR runs on CPU or cuda:0; switching reloads the model on the new
        device on next use. sherpa-onnx runs on CPU or cuda; switching rebuilds
        the recognizer immediately. Requires CUDA-capable torch for funasr GPU.

        ## Return Format
        {"success": bool, "target": str, "device": str, "gpu_available": bool, "gpu_name": str}

        ## Examples
        configure_runtime(action="status")
        configure_runtime(action="set_device", target="funasr", device="cuda:0")
        configure_runtime(action="set_device", target="sherpa", device="cpu")
        """
        from speech_mcp.runtime_config import (
            funasr_device,
            set_funasr_device,
            set_sherpa_device,
            sherpa_device,
        )

        gpu = _gpu_status()

        if action == "status":
            return {
                "success": True,
                "action": action,
                "funasr_device": funasr_device(),
                "sherpa_device": sherpa_device(),
                "gpu_available": gpu.get("available", False),
                "gpu_name": gpu.get("name", "n/a"),
                "funasr_loaded": bool(_funasr_loaded()),
                "sherpa_configured": bool(sherpa_asr),
            }

        if action == "set_device":
            try:
                if target == "funasr":
                    applied = set_funasr_device(device)
                    # FunASR reloads on next use when the device changed.
                    if _funasr_loaded():
                        logger.info("FunASR device set to %s (reloads on next transcription)", applied)
                elif target == "sherpa":
                    if sherpa_asr is None:
                        return {"success": False, "error": "sherpa-onnx not enabled (SHERPA_ASR_ENABLED=1)"}
                    applied = set_sherpa_device(device)
                    sherpa_asr.set_device(applied)
                else:
                    return {"success": False, "error": f"Unknown target '{target}'. Use funasr or sherpa."}
                if ctx:
                    await ctx.info(f"Runtime device set: {target} -> {applied}")
                return {
                    "success": True,
                    "action": action,
                    "target": target,
                    "device": applied,
                    "gpu_available": gpu.get("available", False),
                    "gpu_name": gpu.get("name", "n/a"),
                }
            except ValueError as e:
                return {"success": False, "error": str(e)}
            except Exception as e:
                logger.exception("runtime device change failed")
                return {"success": False, "error": str(e)}

        return {"success": False, "error": f"Unknown action '{action}'. Use status or set_device."}


def _gpu_status() -> dict:
    try:
        from speech_mcp.server import _gpu_info

        return _gpu_info()
    except Exception:
        return {"available": False}


def _funasr_loaded() -> bool:
    try:
        from speech_mcp.server import funasr_provider

        return bool(funasr_provider and getattr(funasr_provider, "_model", None) is not None)
    except Exception:
        return False
