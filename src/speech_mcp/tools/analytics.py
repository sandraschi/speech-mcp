"""Speech analytics tools - real latency/cost telemetry."""

from __future__ import annotations

import logging
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from speech_mcp.storage import analytics_prune, analytics_summary

logger = logging.getLogger(__name__)

# FastMCP tool annotations (TOOL_DESIGN_STANDARDS §9) - dict format works with all 3.x.
_README_ONLY = {"readonly": True}


def register_analytics_tools(mcp: FastMCP) -> None:
    """Register speech analytics tools."""

    @mcp.tool(annotations=_README_ONLY)
    async def speech_analytics(
        hours: Annotated[float, Field(description="Lookback window in hours (default 24).")] = 24.0,
    ) -> dict:
        """Summarize measured synthesis telemetry (calls, latency, errors).

        Samples are auto-recorded by TTS / readout / macro / translate calls
        (source='tool') and the REST endpoints (source='rest'). Prunes samples
        older than 14 days before summarizing.

        ## Return Format
        ``{"success": bool, "window_hours": float, "total_calls": int,
        "providers": {name: {calls, errors, success_rate, avg_latency_ms,
        p95_latency_ms}}}``

        ## Examples
        ``speech_analytics(hours=24)`` -> per-provider latency summary.
        """
        analytics_prune()
        return {"success": True, **analytics_summary(hours=hours)}
