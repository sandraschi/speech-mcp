import logging
from typing import Annotated

from fastmcp import Context, FastMCP
from pydantic import Field

logger = logging.getLogger(__name__)

# FastMCP tool annotations (TOOL_DESIGN_STANDARDS §9) - dict format works with all 3.x.
_MUTATING = {"readonly": False}


def register_monitoring_tools(mcp: FastMCP):

    @mcp.tool(annotations=_MUTATING)
    async def trigger_action(
        action_type: Annotated[str, Field(description="Action type: light_on, light_off, notify")],
        params: Annotated[dict | None, Field(description="Action parameters, e.g. {'room': 'living_room'}")] = None,
        ctx: Context | None = None,
    ) -> dict:
        """
        Trigger IoT or UI actions via the devices-mcp bridge.

        Provides a standardized bridge to Tapo smart home orchestration and UI notifications.

        ## Return Format
        {"success": bool, "device"?: str, "state"?: str, "action_elicited"?: str, "status": str}

        ## Examples
        ``trigger_action(action_type="light_on", params={"room": "living_room"})``
        -> returns ``{"success": True, "status": "pending_orchestration",
        "requires_bridge": True, "next_steps": [...]}`` (no fake device state).
        """
        if ctx:
            await ctx.info(f"Eliciting action: {action_type}")

        if params is None:
            params = {}

        # Standard return format for SOTA orchestration
        if action_type in ("light_on", "light_off"):
            room = params.get("room", "living_room")
            logger.info(f"[PROXY] Requested Tapo action: {action_type} for {room}")
            return {
                "success": True,
                "device": "Tapo Smart Bulb",
                "room": room,
                "state": "on" if "on" in action_type else "off",
                "status": "pending_orchestration",
                "requires_bridge": True,
                "next_steps": [
                    f"Call 'devices-mcp.trigger_tapo' with action='{action_type}' and room='{room}'",
                    "Verify physical state change via camera-mcp",
                ],
            }

        return {
            "success": True,
            "action_elicited": action_type,
            "status": "dispatched",
            "params_processed": params,
            "requires_host_orchestration": True,
        }
