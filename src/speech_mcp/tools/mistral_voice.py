"""Realtime Voxtral streaming STT via Mistral's WebSocket endpoint.

Agent-callable counterpart to ``transcribe_audio_file``: one live session driven
by action strings, so an orchestration loop feeds audio turn-by-turn and reads
the turn events instead of holding the socket itself.

Two modes, mutually exclusive by Mistral's design:

- ``mode="turns"`` (default): turn detection, returns ``turn.start`` /
  ``turn.eager_end`` / ``turn.resume`` / ``turn.end`` plus text deltas. This is
  what a voice loop uses to decide the speaker has finished.
- ``mode="diarize"``: speaker labels, no turn events.
"""

from __future__ import annotations

import asyncio
import base64
import logging
from typing import Annotated, Any

from fastmcp import Context, FastMCP
from pydantic import Field

logger = logging.getLogger(__name__)

# FastMCP tool annotations (TOOL_DESIGN_STANDARDS 9) - dict format works with all 3.x.
_MUTATING = {"readonly": False}

_DRAIN_TIMEOUT_S = 0.05
_END_DRAIN_TIMEOUT_S = 5.0


def register_mistral_voice_tools(mcp: FastMCP, mistral_provider: Any | None) -> None:
    """Register the mistral_transcribe_stream tool. ``mistral_provider`` may be None."""

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
    async def mistral_transcribe_stream(
        action: Annotated[str, Field(description="Operation: start, feed, end, or status.")],
        audio_b64: Annotated[
            str,
            Field(description="Base64-encoded int16 PCM audio (mono). Required for 'feed'."),
        ] = "",
        sample_rate: Annotated[
            int,
            Field(description="PCM sample rate in Hz. Must match what you send; 16000 or 24000 are typical."),
        ] = 24000,
        mode: Annotated[
            str,
            Field(description="'turns' (end-of-turn events, for voice loops) or 'diarize' (speaker labels)."),
        ] = "turns",
        ctx: Context | None = None,
    ) -> dict:
        """
        Realtime speech recognition (Mistral Voxtral 3, WebSocket).

        Streams PCM chunks over one continuous session. In 'turns' mode the events
        include turn.start / turn.eager_end / turn.resume / turn.end, where only
        turn.end means the speaker actually finished - eager ends fire on ordinary
        pauses between sentences.

        Text lags the turn events: keep appending transcription.text.delta after
        turn.end until the next turn.start, or until the streaming delay passes.

        Diarization and turn detection cannot share a session; picking 'diarize'
        switches turn events off.

        ## Return Format
        {"success": bool, "action": str, "events": [{"type", ...}]}

        ## Examples
        mistral_transcribe_stream(action="start", mode="turns")
        mistral_transcribe_stream(action="feed", audio_b64="...")
        mistral_transcribe_stream(action="end")
        """
        nonlocal _session, _drain_task

        if mistral_provider is None:
            return {
                "success": False,
                "error": (
                    "Mistral Voxtral not configured. Set MISTRAL_ENABLED=true plus MISTRAL_API_KEY, "
                    "or point MISTRAL_SELF_HOST_URL at a local vLLM."
                ),
                "error_type": "not_enabled",
            }
        if ctx:
            await ctx.info(f"mistral_transcribe_stream: {action}")

        if action == "status":
            return {"success": True, "action": action, "active": _session is not None, "events": _pop_events()}

        if action == "start":
            if _session is not None:
                return {"success": True, "action": action, "events": [], "note": "session already active"}
            from speech_mcp.providers.mistral import MistralRealtimeSession

            session = MistralRealtimeSession(mistral_provider.config)
            try:
                ack = await session.connect(
                    sample_rate=sample_rate,
                    diarize=mode == "diarize",
                    turn_detection=None if mode == "diarize" else {},
                )
            except Exception as exc:
                logger.exception("mistral_transcribe_stream start failed")
                return {"success": False, "error": str(exc)}
            _session = session
            _drain_task = asyncio.create_task(_drain_loop(session))
            return {"success": True, "action": action, "session": ack, "mode": mode, "events": []}

        if action == "feed":
            if _session is None:
                return {"success": False, "error": "No active session. Call action='start' first."}
            if not audio_b64:
                return {"success": False, "error": "audio_b64 required for feed"}
            try:
                await _session.send_audio(base64.b64decode(audio_b64))
            except Exception as exc:
                logger.exception("mistral_transcribe_stream feed failed")
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
