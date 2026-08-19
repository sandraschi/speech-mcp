import asyncio
import logging
from typing import Annotated, Any

from fastmcp import Context, FastMCP
from pydantic import Field

logger = logging.getLogger(__name__)

# FastMCP tool annotations (TOOL_DESIGN_STANDARDS §9) - dict format works with all 3.x.
_README_ONLY = {"readonly": True}


def register_stt_tools(
    mcp: FastMCP,
    funasr_provider: Any | None,
    gemini_client: Any | None = None,
    gemma_client: Any | None = None,
):
    """Register speech-to-text tools (FunASR native, cloud fallbacks)."""

    @mcp.tool(annotations=_README_ONLY)
    async def transcribe_audio_file(
        file_path: Annotated[str, Field(description="Absolute path to a local audio file (WAV, MP3, FLAC).")],
        provider: Annotated[
            str, Field(description="STT backend: funasr (local, recommended), gemini, gemma.")
        ] = "funasr",
        language: Annotated[
            str, Field(description="Target language code (en, zh, ja, de, …) or 'auto' for detection.")
        ] = "auto",
        ctx: Context | None = None,
    ) -> dict:
        """
        Transcribe a local audio file with speaker labels, timestamps, and punctuation.

        FunASR (default) runs VAD + ASR + punctuation + diarization in one pass.
        SenseVoice models also emit emotion tags per segment.

        ## Return Format
        {
          "success": bool,
          "provider": str,
          "text": str,
          "segments": [{"speaker", "start_s", "end_s", "text", "emotion"?}],
          "formatted": str
        }

        ## Examples
        await transcribe_audio_file("D:/recordings/meeting.wav")
        await transcribe_audio_file("/tmp/podcast.mp3", language="ja")
        await transcribe_audio_file("C:/audio/note.wav", provider="gemini")
        """
        logger.info("STT [%s]: %s", provider, file_path)

        if provider == "funasr":
            if not funasr_provider:
                return {
                    "success": False,
                    "error": "FunASR not configured.",
                    "recovery": (
                        "Set FUNASR_ENABLED=true in .env and run: uv sync --extra funasr. "
                        "Or set FUNASR_OPENAI_URL to a running FunASR sidecar."
                    ),
                }
            return await funasr_provider.transcribe_file(file_path, language=language)

        if provider == "gemini":
            gemini = gemini_client
            if not gemini:
                return {"success": False, "error": "GOOGLE_API_KEY not configured"}
            try:
                with open(file_path, "rb") as f:
                    audio_bytes = f.read()
                text = await asyncio.to_thread(lambda: gemini.transcribe(audio_bytes, mime_type="audio/wav"))
                return {"success": True, "provider": "gemini", "text": text, "segments": [], "formatted": text}
            except Exception as exc:
                return {"success": False, "error": str(exc), "provider": "gemini"}

        if provider == "gemma":
            gemma = gemma_client
            if not gemma:
                return {"success": False, "error": "Gemma provider not initialized"}
            try:
                with open(file_path, "rb") as f:
                    audio_bytes = f.read()
                text = await asyncio.to_thread(lambda: gemma.transcribe(audio_bytes, mime_type="audio/wav"))
                return {"success": True, "provider": "gemma", "text": text, "segments": [], "formatted": text}
            except Exception as exc:
                return {"success": False, "error": str(exc), "provider": "gemma"}

        return {
            "success": False,
            "error": f"Unknown provider '{provider}'. Use funasr, gemini, or gemma.",
        }

    @mcp.tool(annotations=_README_ONLY)
    async def transcribe_stream_chunk(
        audio_base64: Annotated[str, Field(description="Base64-encoded audio chunk (WAV or MP3).")],
        provider: Annotated[str, Field(description="STT backend: funasr (default), gemini, gemma.")] = "funasr",
        language: Annotated[str, Field(description="Language code or 'auto'.")] = "auto",
        sample_rate: Annotated[int, Field(description="Input sample rate in Hz (informational).")] = 16000,
        mime_type: Annotated[str, Field(description="MIME type of the chunk, e.g. audio/wav.")] = "audio/wav",
        ctx: Context | None = None,
    ) -> dict:
        """
        Stateless transcription of a single audio fragment from a stream bridge.

        Designed for chunked input from microphones, WebSocket bridges, or robot
        audio pipelines. Each call is independent — no session state retained.

        ## Return Format
        Same as transcribe_audio_file.

        ## Examples
        await transcribe_stream_chunk(base64_wav_chunk)
        await transcribe_stream_chunk(chunk_b64, language="zh", sample_rate=16000)
        """
        logger.info("STT chunk [%s] (%d b64 chars)", provider, len(audio_base64))

        if provider == "funasr":
            if not funasr_provider:
                return {
                    "success": False,
                    "error": "FunASR not configured.",
                    "recovery": "Set FUNASR_ENABLED=true or FUNASR_OPENAI_URL in .env",
                }
            return await funasr_provider.transcribe_chunk(
                audio_base64,
                sample_rate=sample_rate,
                language=language,
                mime_type=mime_type,
            )

        if provider in ("gemini", "gemma"):
            import base64

            try:
                audio_bytes = base64.b64decode(audio_base64)
            except Exception as exc:
                return {"success": False, "error": f"Invalid base64: {exc}"}

            if provider == "gemini":
                gemini = gemini_client
                if not gemini:
                    return {"success": False, "error": "GOOGLE_API_KEY not configured"}
                try:
                    text = await asyncio.to_thread(lambda: gemini.transcribe(audio_bytes, mime_type=mime_type))
                    return {"success": True, "provider": "gemini", "text": text, "segments": [], "formatted": text}
                except Exception as exc:
                    return {"success": False, "error": str(exc)}

            if not gemma_client:
                return {"success": False, "error": "Gemma provider not initialized"}
            try:
                text = await gemma_client.transcribe(audio_bytes, mime_type=mime_type)
                return {"success": True, "provider": "gemma", "text": text, "segments": [], "formatted": text}
            except Exception as exc:
                return {"success": False, "error": str(exc)}

        return {"success": False, "error": f"Unknown provider '{provider}'"}
