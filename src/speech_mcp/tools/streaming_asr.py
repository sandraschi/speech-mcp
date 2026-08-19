"""Streaming STT and barge-in MCP tools (sherpa-onnx backend)."""

from __future__ import annotations

import base64
import logging
from typing import Annotated

from fastmcp import Context, FastMCP
from pydantic import Field

logger = logging.getLogger(__name__)

# FastMCP tool annotations (TOOL_DESIGN_STANDARDS §9) - dict format works with all 3.x.
_MUTATING = {"readonly": False}


def register_streaming_asr_tools(mcp: FastMCP, sherpa_asr) -> None:
    """Register streaming STT tools. ``sherpa_asr`` is a SherpaStreamingASR or None."""

    @mcp.tool(annotations=_MUTATING)
    async def streaming_stt(
        action: Annotated[
            str,
            Field(description="Operation: status, reset, feed, or end."),
        ],
        audio_b64: Annotated[
            str,
            Field(description="Base64-encoded int16 PCM audio (16 kHz, mono). Required for 'feed'."),
        ] = "",
        sample_rate: Annotated[
            int,
            Field(description="PCM sample rate. Only 16000 is supported by sherpa-onnx."),
        ] = 16000,
        ctx: Context | None = None,
    ) -> dict:
        """
        Streaming speech recognition (sherpa-onnx, CPU).

        Feeds live PCM chunks and returns partial transcript + endpoint flags,
        so a voice loop can render text as it is recognized and stop when the
        user pauses. Languages: en (English), ja (Japanese), de (German).

        ## Return Format
        {"success": bool, "action": str, "partial": str, "endpoint": bool, "language": str}

        ## Examples
        streaming_stt(action="status")
        streaming_stt(action="reset")
        streaming_stt(action="feed", audio_b64="...")
        streaming_stt(action="end")
        """
        if sherpa_asr is None:
            return {
                "success": False,
                "error": "sherpa-onnx streaming STT not enabled. Set SHERPA_ASR_ENABLED=1 and 'uv sync --extra sherpa'.",
                "error_type": "not_enabled",
            }
        if ctx:
            await ctx.info(f"streaming_stt: {action}")

        if action == "status":
            return {
                "success": True,
                "action": action,
                "language": sherpa_asr.lang,
                "partial": sherpa_asr.recognizer.get_result(sherpa_asr.stream).strip(),
                "endpoint": sherpa_asr.recognizer.is_endpoint(sherpa_asr.stream),
            }
        if action == "reset":
            sherpa_asr.reset()
            return {"success": True, "action": action, "partial": "", "endpoint": False}
        if action == "feed":
            if not audio_b64:
                return {"success": False, "error": "audio_b64 required for feed"}
            if sample_rate != 16000:
                return {"success": False, "error": "sample_rate must be 16000"}
            try:
                raw = base64.b64decode(audio_b64)
                import numpy as np

                pcm = np.frombuffer(raw, dtype=np.int16)
                if pcm.size == 0:
                    return {"success": True, "action": action, "partial": "", "endpoint": False}
                result = sherpa_asr.accept(pcm)
                return {"success": True, "action": action, "partial": result["partial"], "endpoint": result["endpoint"]}
            except Exception as e:
                logger.exception("streaming_stt feed failed")
                return {"success": False, "error": str(e)}
        if action == "end":
            text = sherpa_asr.final()
            return {"success": True, "action": action, "text": text, "partial": text, "endpoint": True}
        return {"success": False, "error": f"Unknown action '{action}'. Use status/reset/feed/end."}

    @mcp.tool(annotations=_MUTATING)
    async def barge_in_feed(
        audio_b64: Annotated[str, Field(description="Base64 int16 PCM (16 kHz) from the live mic.")],
        ctx: Context | None = None,
    ) -> dict:
        """
        Feed mic audio for barge-in detection (sherpa-onnx VAD).

        Returns transcripts of utterances detected so far. A non-empty
        ``utterances`` list means the user spoke (interrupt the assistant).
        Requires sherpa-onnx + silero VAD (see docs/STREAMING_ASR.md).

        ## Return Format
        {"success": bool, "utterances": list[str], "barge_in": bool}

        ## Examples
        barge_in_feed(audio_b64="...")
        """
        barge = getattr(sherpa_asr, "_barge_in", None)
        if barge is None:
            return {
                "success": False,
                "error": "barge-in not initialized. Set SHERPA_ASR_ENABLED=1 and SHERPA_BARGE_IN=1.",
                "error_type": "not_enabled",
            }
        try:
            raw = base64.b64decode(audio_b64)
            import numpy as np

            pcm = np.frombuffer(raw, dtype=np.int16)
            utterances = barge.feed(pcm)
            return {"success": True, "utterances": utterances, "barge_in": bool(utterances)}
        except Exception as e:
            logger.exception("barge_in_feed failed")
            return {"success": False, "error": str(e)}
