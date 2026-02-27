import asyncio
import logging
from datetime import datetime

from fastmcp import Context, FastMCP

from speech_mcp.state import _timers, run_timer

logger = logging.getLogger(__name__)


def register_utility_tools(mcp: FastMCP):

    @mcp.tool()
    async def manage_domestic_utility(
        action: str,
        type: str,
        value: str | int | None = None,
        label: str = "Default",
        ctx: Context = None,
    ) -> dict:
        """
        Manages timers, alarms, and domestic utility queries (Alexa pattern).

        PORTMANTEAU PATTERN RATIONALE:
        Consolidates timer management, alarm scheduling, and weather queries into a
        single domestic utility interface. Prevents tool proliferation.

        Args:
            action (str): Operation to perform. One of: 'set', 'cancel', 'query'.
            type (str): Utility type. One of: 'timer', 'alarm', 'weather'.
            value (str | int | None): Duration in seconds for timers, or time string
                for alarms (e.g. '07:30').
            label (str): Human-readable label for the utility.
            ctx (Context): FastMCP context.
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
                            "recommendation": "Wear a reductionist coat."
                            if "C" in weather_text
                            else "Stay optimal.",
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
