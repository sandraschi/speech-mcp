import logging

from fastmcp import Context, FastMCP

logger = logging.getLogger(__name__)


def register_monitoring_tools(mcp: FastMCP):

    @mcp.tool()
    async def trigger_action(
        action_type: str,
        params: dict | None = None,
        ctx: Context = None,
    ) -> dict:
        """
        Elicit physical effects (IoT lights, smart devices) or UI notifications.

        Provides a standardized bridge to devices-mcp / Tapo smart home orchestration.

        Args:
            action_type (str): Action to trigger. Examples: 'light_on',
                'light_off', 'notify'. Follows devices-mcp naming conventions.
            params (dict | None): Action parameters. For light actions: {'room': 'living_room'}.
                For notifications: {'message': 'Timer expired!'}.
            ctx (Context): FastMCP context.
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
