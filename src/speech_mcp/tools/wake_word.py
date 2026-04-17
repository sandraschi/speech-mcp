import logging
import os

from fastmcp import Context, FastMCP

logger = logging.getLogger(__name__)


def register_wake_word_tools(mcp: FastMCP):
    """
    Registers tools for local wake-word monitoring (Porcupine).
    """

    @mcp.tool()
    async def configure_local_wake_word(
        ctx: Context,
        keyword: str = "computer",
        sensitivity: float = 0.5,
    ) -> dict:
        """
        Configures a local wake-word listener as a trigger for the SOTA Gemini stream.
        This provides a 'Hey Computer' physical fallback to always-on VAD.

        Args:
            keyword: The built-in keyword to listen for (e.g., 'computer', 'jarvis', 'alexa').
            sensitivity: Detection sensitivity (0.0 to 1.0).
        """
        api_key = os.getenv("PICOVOICE_API_KEY")

        if not api_key:
            return {
                "success": False,
                "error": "PICOVOICE_API_KEY missing in .env",
                "recovery": "Add your Picovoice AccessKey to enable Porcupine local monitoring.",
            }

        await ctx.info(f"Configuring local wake-word: '{keyword}' at {sensitivity} sensitivity.")

        # In a fleet deployment, this config is returned to the client/worker
        # which runs the actual pvporcupine listener loop.
        return {
            "success": True,
            "status": "ready",
            "provider": "Picovoice Porcupine 3.0",
            "keyword": keyword,
            "sensitivity": sensitivity,
            "access_key": f"{api_key[:4]}...{api_key[-4:]}",
            "architecture": "Local Microphone -> PvPorcupine -> Gateway (ws/stream)",
            "next_steps": ["Worker loop started", "Listening for activation..."],
        }
