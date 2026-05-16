import asyncio
import logging
from datetime import datetime
from typing import Annotated

from fastmcp import Context, FastMCP
from pydantic import Field

from speech_mcp.state import _timers, run_timer

logger = logging.getLogger(__name__)


def register_utility_tools(mcp: FastMCP):

    @mcp.tool()
    async def manage_domestic_utility(
        action: Annotated[str, Field(description="Operation: set, cancel, query")],
        type: Annotated[str, Field(description="Utility type: timer, alarm, weather")],
        value: Annotated[str | int | None, Field(
            description="Duration in seconds for timers, time string for alarms."
        )] = None,
        label: Annotated[str, Field(description="Human-readable label.")] = "Default",
        ctx: Context = None,
    ) -> dict:
        """
        Manage timers, alarms, and domestic utility queries (Alexa pattern).

        [RATIONALE]
        Consolidates timer management, alarm scheduling, and weather queries into a
        single domestic utility interface to prevent tool proliferation.

        ## Return Format
        {"success": bool, "timer_id"?: str, "expires_in"?: int, "status": str, "cancelled"?: list}

        ## Examples
        await manage_domestic_utility("set", "timer", value=120, label="Pasta")
        await manage_domestic_utility("cancel", "timer", label="Pasta")
        await manage_domestic_utility("query", "timer")
        """
        if ctx:
            await ctx.info(f"Domestic Utility: {action} {type} ({label})")

        if type == "timer":
            if action == "set":
                timer_id = f"timer_{label}_{datetime.now().timestamp()}"
                seconds = int(value) if value else 60
                task = asyncio.create_task(run_timer(timer_id, seconds, label))
                _timers[timer_id] = task
                return {
                    "success": True,
                    "timer_id": timer_id,
                    "expires_in": seconds,
                    "status": "active",
                    "next_steps": [f"Timer '{label}' will expire in {seconds}s"],
                }
            elif action == "cancel":
                matched = {k: v for k, v in _timers.items() if label in k}
                for k, v in matched.items():
                    v.cancel()
                    del _timers[k]
                return {"success": True, "cancelled": list(matched.keys())}
            elif action == "query":
                return {
                    "success": True,
                    "active_timers": len(_timers),
                    "timer_ids": list(_timers.keys()),
                }

        elif type == "weather":
            import httpx

            location = label if label != "Default" else "Vienna"
            try:
                # Use wttr.in for a SOTA text-based weather report
                async with httpx.AsyncClient() as client:
                    resp = await client.get(f"https://wttr.in/{location}?format=%C+%t")
                    if resp.status_code == 200:
                        weather_text = resp.text.strip()
                        return {
                            "success": True,
                            "location": location,
                            "condition_report": weather_text,
                            "status": "realtime_data",
                            "recommendation": "Wear a reductionist coat." if "C" in weather_text else "Stay optimal.",
                            "source": "wttr.in",
                        }
            except Exception as e:
                logger.error(f"Weather error: {e}")

            return {
                "success": True,
                "location": location,
                "condition": "Cloudy with a chance of data",
                "temp": "21°C",
                "status": "cached_stub",
                "note": "Real-time fetch failed, using reductionist baseline.",
            }

        return {
            "success": False,
            "error": f"Action '{action}' / type '{type}' combination not implemented",
        }
