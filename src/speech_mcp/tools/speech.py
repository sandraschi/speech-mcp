import os
from typing import Any

from elevenlabs.client import ElevenLabs
from fastmcp import Context, FastMCP
from hume import HumeClient


def _stream_base_url() -> str:
    base = os.getenv("SPEECH_MCP_BACKEND_URL", "http://localhost:10918")
    return base.replace("https://", "wss://").replace("http://", "ws://")


# We use a registration function patterns to keep dependencies local to the module
def register_speech_tools(
    mcp: FastMCP, hume_client: HumeClient | None, eleven_client: ElevenLabs | None, gemini_client: Any | None = None
):

    @mcp.tool()
    async def text_to_speech(
        text: str,
        voice_id: str = "Aoede",
        provider: str = "gemini",
        emotion: str | None = None,
        ctx: Context = None,
    ) -> dict:
        """
        Synthesize speech via Gemini 3.1 Flash, Hume AI, ElevenLabs, or Windows Local.

        PORTMANTEAU PATTERN RATIONALE:
        Consolidates four TTS providers into a single interface. Prevents tool
        explosion while exposing a unified stream-ready URL for all provider
        backends. Follows FastMCP 3.x SOTA standards.

        Args:
            text (str, required): Text to synthesize.
            voice_id (str): Voice identifier. Defaults to 'ito' (Hume). Use 'default'
                for Windows TTS, or an ElevenLabs voice ID for that provider.
            provider (str): TTS backend. One of: 'hume', 'elevenlabs', 'windows'.
            emotion (str | None): Optional emotion hint for expressive synthesis
                (Hume/ElevenLabs only). E.g. 'excited', 'calm', 'sad'.
            ctx (Context): FastMCP context for logging and correlation.
        """
        if ctx:
            await ctx.info(f"TTS [{provider}/{voice_id}]: {text[:40]}...")

        # Base stream URL (handled by the webapp binary proxy)
        stream_url = f"{_stream_base_url()}/ws/stream?provider={provider}&voice={voice_id}"

        # Provider-specific logic and metadata
        if provider == "hume":
            if not hume_client:
                return {
                    "success": False,
                    "error": "Hume API key missing",
                    "recovery_options": ["Check .env", "Use windows provider"],
                }
            return {
                "success": True,
                "provider": "Hume AI (Octave)",
                "voice": voice_id,
                "stream_url": stream_url,
                "status": "ready_for_dispatch",
                "next_steps": ["Connect to stream_url", "Begin audio playback"],
                "quality_metrics": {"latency_target": "low", "empathy_enabled": True},
            }

        elif provider == "elevenlabs":
            if not eleven_client:
                return {
                    "success": False,
                    "error": "ElevenLabs API key missing",
                    "recovery_options": ["Check .env"],
                }
            return {
                "success": True,
                "provider": "ElevenLabs",
                "voice": voice_id,
                "stream_url": stream_url,
                "status": "stream_ready",
                "recommendations": ["Use eleven_turbo_v2_5 for best latency"],
            }

        elif provider == "windows":
            return {
                "success": True,
                "provider": "Windows Local (SAPI5)",
                "voice": "Default",
                "stream_url": stream_url,
                "status": "local_fallback_ready",
            }

        elif provider == "gemini":
            if not gemini_client:
                return {
                    "success": False,
                    "error": "Gemini API key missing",
                    "recovery_options": ["Check GOOGLE_API_KEY in .env"],
                }

            # For Gemini, we automatically wrap the text in emotion tags if provided
            if emotion:
                text = f"[{emotion}] {text}"

            return {
                "success": True,
                "provider": "Gemini 3.1 Flash (SOTA)",
                "voice": voice_id,
                "stream_url": stream_url,
                "tags_applied": emotion if emotion else "none",
                "status": "ready_for_dispatch",
                "next_steps": ["Connect to stream_url", "Begin audio playback"],
                "quality_metrics": {"interruptible": True, "barge_in_ready": True},
            }

        return {"success": False, "error": f"Unsupported provider: {provider}"}

    @mcp.tool()
    async def manage_voice_clones(
        action: str,
        provider: str = "hume",
        name: str | None = None,
        audio_path: str | None = None,
        voice_id: str | None = None,
        ctx: Context = None,
    ) -> dict:
        """
        Manage voice clones across providers (Hume/ElevenLabs).

        Args:
            action (str): "list", "create", "delete", "info".
            provider (str): 'hume' or 'elevenlabs'.
            name (str | None): Custom name for new clones.
            audio_path (str | None): Local file path for cloning.
            voice_id (str | None): Target voice ID for info/delete.
            ctx (Context): FastMCP context.
        """
        if ctx:
            await ctx.info(f"Voice management: {action} via {provider}")

        if provider == "hume":
            if not hume_client:
                return {"success": False, "error": "Hume API key missing"}
            if action == "list":
                return {
                    "success": True,
                    "provider": "Hume AI",
                    "voices": [{"id": "ito", "name": "Ito", "type": "base"}],
                    "pagination": {"total": 1},
                }
            # Current Beta Limitation: Non-list actions are simulated
            return {
                "success": True,
                "action": action,
                "status": "simulated_placeholder",
                "message": (
                    f"Action '{action}' is documented as a placeholder for the Hume-Beta path. "
                    "Actual synthesis impact is simulated in this version."
                ),
                "is_active_beta": True,
            }

        elif provider == "elevenlabs":
            if not eleven_client:
                return {"success": False, "error": "ElevenLabs API key missing"}
            try:
                if action == "list":
                    voices = eleven_client.voices.get_all()
                    return {
                        "success": True,
                        "provider": "ElevenLabs",
                        "voices": [{"id": v.voice_id, "name": v.name} for v in voices.voices],
                    }
            except Exception as e:
                return {"success": False, "error": str(e)}

        return {"success": False, "error": "Unsupported provider/action"}
