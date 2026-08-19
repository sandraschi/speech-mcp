"""Persistent voice memory tools - episodic voice diary."""

from __future__ import annotations

import logging
from typing import Annotated

from fastmcp import Context, FastMCP
from pydantic import Field

from speech_mcp.storage import memory_recall, memory_search, memory_store

logger = logging.getLogger(__name__)

# FastMCP tool annotations (TOOL_DESIGN_STANDARDS §9) - dict format works with all 3.x.
_README_ONLY = {"readonly": True}
_MUTATING = {"readonly": False}


def register_memory_tools(mcp: FastMCP) -> None:
    """Register persistent voice memory tools."""

    @mcp.tool(annotations=_MUTATING)
    async def voice_memory_store(
        text: Annotated[str, Field(description="Episode content (what was said or heard).")],
        kind: Annotated[str, Field(description="Episode kind: tts, stt, note, chat.")] = "note",
        speaker: Annotated[str, Field(description="Speaker label, if known.")] = "",
        topic: Annotated[str, Field(description="Topic tag for later recall.")] = "",
        provider: Annotated[str, Field(description="Provider that produced the episode.")] = "",
        ctx: Context | None = None,
    ) -> dict:
        """Persist a voice episode to the episodic memory store.

        ## Return Format
        ``{"success": bool, "episode": {id, ts, kind, text, topic, ...}}``

        ## Examples
        ``voice_memory_store(text="Remember to buy milk", kind="note",
        topic="errands")`` -> stores and returns the new episode.
        """
        if not text.strip():
            return {"success": False, "error": "text is required"}
        episode = memory_store(text.strip(), kind=kind, speaker=speaker, topic=topic, provider=provider)
        if ctx:
            await ctx.info(f"Voice memory stored (#{episode['id']}, kind={kind})")
        return {"success": True, "episode": episode}

    @mcp.tool(annotations=_README_ONLY)
    async def voice_memory_recall(
        limit: Annotated[int, Field(description="Max episodes to return (1-200).")] = 20,
        kind: Annotated[str | None, Field(description="Filter by kind: tts, stt, note, chat.")] = None,
        topic: Annotated[str | None, Field(description="Filter by exact topic tag.")] = None,
    ) -> dict:
        """Recall recent voice memory episodes, newest first.

        ## Return Format
        ``{"success": bool, "count": int, "episodes": [...]}``

        ## Examples
        ``voice_memory_recall(limit=10, kind="note")`` -> last 10 notes.
        """
        episodes = memory_recall(limit=limit, kind=kind, topic=topic)
        return {"success": True, "count": len(episodes), "episodes": episodes}

    @mcp.tool(annotations=_README_ONLY)
    async def voice_memory_search(
        query: Annotated[str, Field(description="Keyword to search in episode text/topic/speaker.")],
        limit: Annotated[int, Field(description="Max results (1-100).")] = 10,
    ) -> dict:
        """Search voice memory by keyword.

        ## Return Format
        ``{"success": bool, "count": int, "results": [...]}``

        ## Examples
        ``voice_memory_search("milk")`` -> episodes mentioning "milk".
        """
        results = memory_search(query, limit=limit)
        return {"success": True, "count": len(results), "results": results}
