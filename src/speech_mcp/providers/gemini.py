import logging
import os

import google.generativeai as genai

logger = logging.getLogger(__name__)


class GeminiTTSProvider:
    """
    Industrial provider for Gemini 3.1 Flash TTS.
    Supports natural language audio tags [whispers], [happy], etc.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is not configured")

        genai.configure(api_key=self.api_key)
        self.model_id = "gemini-3.1-flash-tts-preview"
        self.model = genai.GenerativeModel(self.model_id)

    async def synthesize(self, text: str, voice_name: str = "Aoede") -> bytes:
        """
        Unary synthesis for batch generation.
        """
        try:
            # SOTA Configuration for Gemini 3.1 Flash TTS
            config = {
                "response_modalities": ["audio"],
                "speech_config": {"voice_config": {"prebuilt_voice_config": {"voice_name": voice_name}}},
            }

            # Using the official GenAI SDK pattern
            response = await self.model.generate_content_async(contents=text, generation_config=config)

            # Extract audio data from the first candidate's first part
            if response.candidates and response.candidates[0].content.parts:
                part = response.candidates[0].content.parts[0]
                if hasattr(part, "inline_data"):
                    return part.inline_data.data
                elif hasattr(part, "audio_data"):  # Future-proofing for SDK changes
                    return part.audio_data

            raise ValueError("No audio data returned from Gemini TTS")

        except Exception as e:
            logger.error(f"Gemini TTS Synthesis failed: {e}")
            raise

    def get_live_url(self) -> str:
        """
        Returns the WebSocket entry point for Gemini Multimodal Live.
        Used for SOTA interruptible streaming.
        """
        # SOTA Endpoint for April 2026
        return "wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService/MultimodalLive"

    @property
    def voices(self):
        return ["Aoede", "Charon", "Fenrir", "Kore", "Orion", "Puck"]
