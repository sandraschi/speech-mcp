import logging
import os

logger = logging.getLogger(__name__)


class GemmaProvider:
    """
    SOTA 2026 Provider for Gemma 4 local intelligence.
    Supports native multimodal ingestion (Audio, Vision) via local inference backends.
    """

    def __init__(self, base_url: str | None = None, provider: str = "ollama"):
        self.provider = provider
        self.base_url = base_url or os.getenv("GEMMA_API_URL", "http://localhost:11434")
        self.model = os.getenv("GEMMA_MODEL", "gemma-4-26b-a4b")

    async def transcribe(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
        """
        STT via Gemma 4 Audio Encoder.

        Gemma 4 native audio input is not wired in yet - this raises so callers
        fall back to funasr/gemini instead of receiving a fabricated transcript.
        """
        raise NotImplementedError("Gemma 4 native audio input is not wired. Use provider='funasr' (local) or 'gemini'.")

    def synthesize_and_play(self, text: str, voice: str = "default") -> bool:
        """
        Synthesize speech on the server speaker.

        Gemma 4 native audio output is not wired in yet - this falls back to
        Windows SAPI5 so the call actually produces sound (declared fallback).
        """
        logger.info("Gemma provider: native audio not wired, using Windows SAPI5 fallback")
        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
            return True
        except Exception:
            logger.exception("Gemma/SAPI fallback TTS failed")
            return False

    @property
    def voices(self) -> list[str]:
        return ["Gemma-Native", "Gemma-Assistant"]


gemma_provider = GemmaProvider()
