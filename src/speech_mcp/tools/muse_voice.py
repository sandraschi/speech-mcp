"""Realtime diarized streaming STT via Meta Muse Voice Transcribe.

Agent-callable counterpart to tools/streaming_asr.py's streaming_stt: a single
global MuseRealtimeSession, driven by action strings, so an orchestration loop
can feed live audio turn-by-turn without holding the WebSocket open itself.
"""

from __future__ import annotations

import asyncio
import base64
import logging
from typing import Annotated, Any

from fastmcp import Context, FastMCP
from pydantic import Field

logger = logging.getLogger(__name__)

# FastMCP tool annotations (TOOL_DESIGN_STANDARDS §9) - dict format works with all 3.x.
_MUTATING = {"readonly": False}

_DRAIN_TIMEOUT_S = 0.05
_END_DRAIN_TIMEOUT_S = 5.0


def register_muse_tools(mcp: FastMCP, muse_provider: Any | None) -> None:
    """Register the muse_transcribe_stream tool. ``muse_provider`` may be None."""

    _session: Any | None = None
    _events: list[dict] = []
    _drain_task: asyncio.Task | None = None

    async def _drain_loop(session) -> None:
        nonlocal _events
        try:
            while True:
                event = await session.recv_event()
                if event is None:
                    break
                _events.append(event)
        except Exception as exc:
            _events.append({"type": "error", "message": str(exc)})

    def _pop_events() -> list[dict]:
        nonlocal _events
        popped, _events = _events, []
        return popped

    @mcp.tool(annotations=_MUTATING)
    async def muse_transcribe_stream(
        action: Annotated[str, Field(description="Operation: start, feed, end, or status.")],
        audio_b64: Annotated[
            str,
            Field(description="Base64-encoded int16 PCM audio (16 kHz, mono). Required for 'feed'."),
        ] = "",
        ctx: Context | None = None,
    ) -> dict:
        """
        Realtime diarized speech recognition (Meta Muse Voice Transcribe, cloud).

        Feeds live PCM chunks over one continuous session so speaker identity stays
        consistent across the whole call, unlike batching a recording into separate
        file uploads. Returns any transcript/speaker/speechComplete events received
        since the last call.

        ## Return Format
        {"success": bool, "action": str, "events": [{"type", ...}]}

        ## Examples
        muse_transcribe_stream(action="start")
        muse_transcribe_stream(action="feed", audio_b64="...")
        muse_transcribe_stream(action="end")
        """
        nonlocal _session, _drain_task

        if muse_provider is None:
            return {
                "success": False,
                "error": "Muse Voice Transcribe not configured. Set MUSE_ENABLED=true and MUSE_API_KEY.",
                "error_type": "not_enabled",
            }
        if ctx:
            await ctx.info(f"muse_transcribe_stream: {action}")

        if action == "status":
            return {"success": True, "action": action, "active": _session is not None, "events": _pop_events()}

        if action == "start":
            if _session is not None:
                return {"success": True, "action": action, "events": [], "note": "session already active"}
            from speech_mcp.providers.muse import MuseRealtimeSession

            session = MuseRealtimeSession(muse_provider.config)
            try:
                ack = await session.connect(mode="DIARIZATION", encoding="PCM_16KHZ")
            except Exception as exc:
                logger.exception("muse_transcribe_stream start failed")
                return {"success": False, "error": str(exc)}
            _session = session
            _drain_task = asyncio.create_task(_drain_loop(session))
            return {"success": True, "action": action, "session": ack, "events": []}

        if action == "feed":
            if _session is None:
                return {"success": False, "error": "No active session. Call action='start' first."}
            if not audio_b64:
                return {"success": False, "error": "audio_b64 required for feed"}
            try:
                pcm = base64.b64decode(audio_b64)
                await _session.send_audio(pcm)
            except Exception as exc:
                logger.exception("muse_transcribe_stream feed failed")
                return {"success": False, "error": str(exc)}
            await asyncio.sleep(_DRAIN_TIMEOUT_S)  # let recv_event() pick up anything already in flight
            return {"success": True, "action": action, "events": _pop_events()}

        if action == "end":
            if _session is None:
                return {"success": True, "action": action, "events": []}
            session, _session = _session, None
            try:
                await session.end_stream()
                if _drain_task is not None:
                    try:
                        await asyncio.wait_for(_drain_task, timeout=_END_DRAIN_TIMEOUT_S)
                    except TimeoutError:
                        _drain_task.cancel()
            finally:
                await session.close()
                _drain_task = None
            return {"success": True, "action": action, "events": _pop_events()}

        return {"success": False, "error": f"Unknown action '{action}'. Use start/feed/end/status."}
