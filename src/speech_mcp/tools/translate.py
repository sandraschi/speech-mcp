"""Translation bridge tools - STT -> local LLM translate -> optional TTS."""

from __future__ import annotations

import logging
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from speech_mcp.providers.local import local_llm_provider

logger = logging.getLogger(__name__)

# FastMCP tool annotations (TOOL_DESIGN_STANDARDS §9) - dict format works with all 3.x.
_README_ONLY = {"readonly": True}

_TRANSLATE_SYSTEM = (
    "You are a professional translator. Translate the user's text into the "
    "requested target language. Preserve meaning, tone, and named entities. "
    "Output ONLY the translation, no commentary."
)


async def _llm_translate(
    text: str, target_language: str, provider: str, model: str | None, base_url: str | None
) -> str:
    base = base_url or ("http://localhost:11434" if provider == "ollama" else "http://localhost:1234")
    effective = model or ("llama3" if provider == "ollama" else "default")
    prompt = f"Translate the following text to {target_language}:\n\n{text}"
    return await local_llm_provider.generate(
        provider=provider, base_url=base, model=effective, prompt=prompt, system=_TRANSLATE_SYSTEM
    )


def register_translate_tools(mcp: FastMCP, funasr_provider, speak_fn) -> None:
    """Register translation tools. ``funasr_provider`` enables audio input."""

    @mcp.tool(annotations=_README_ONLY)
    async def translate_text(
        text: Annotated[str, Field(description="Text to translate.")],
        target_language: Annotated[str, Field(description="Target language, e.g. 'Japanese', 'German'.")],
        provider: Annotated[str, Field(description="Local LLM provider: ollama or lmstudio.")] = "ollama",
        model: Annotated[str | None, Field(description="Model override (default: provider default).")] = None,
        base_url: Annotated[str | None, Field(description="Provider base URL override.")] = None,
    ) -> dict:
        """Translate text via a local LLM (no cloud translation dependency).

        ## Return Format
        ``{"success": bool, "text": str, "translation": str, "provider": str}``

        ## Examples
        ``translate_text("Hello, how are you?", "Japanese")`` -> Japanese text.
        """
        if not text.strip():
            return {"success": False, "error": "text is required"}
        translation = await _llm_translate(text, target_language, provider, model, base_url)
        if translation.startswith("Generation failed"):
            return {"success": False, "error": translation}
        return {"success": True, "text": text, "translation": translation, "provider": provider}

    @mcp.tool(annotations=_README_ONLY)
    async def translate_speech(
        file_path: Annotated[str, Field(description="Absolute path to an audio file to transcribe + translate.")],
        target_language: Annotated[str, Field(description="Target language for the translation.")],
        speak: Annotated[bool, Field(description="Speak the translation aloud via TTS.")] = False,
        source_language: Annotated[str, Field(description="STT source language (auto for FunASR).")] = "auto",
        provider: Annotated[str, Field(description="Local LLM provider: ollama or lmstudio.")] = "ollama",
        model: Annotated[str | None, Field(description="Model override.")] = None,
        base_url: Annotated[str | None, Field(description="Provider base URL override.")] = None,
    ) -> dict:
        """Transcribe an audio file (FunASR), translate, optionally speak it.

        Requires FunASR (``FUNASR_ENABLED=true`` or sidecar) and a reachable
        local LLM. Returns the source transcript, translation, and (when
        ``speak=True``) the TTS result.

        ## Return Format
        ``{"success": bool, "transcript": str, "translation": str,
        "spoken": {...}|null, "errors": [...]}``

        ## Examples
        ``translate_speech(file_path="C:/audio/greeting.wav",
        target_language="Japanese", speak=True)`` -> transcript + Japanese
        translation, spoken aloud.
        """
        errors: list[str] = []
        if funasr_provider is None:
            return {"success": False, "error": "FunASR not configured - set FUNASR_ENABLED=true or FUNASR_OPENAI_URL"}
        try:
            result = await funasr_provider.transcribe_file(file_path, language=source_language)
        except Exception as e:
            logger.exception("translate_speech transcription failed")
            return {"success": False, "error": f"Transcription failed: {e}"}
        if not result.get("success"):
            return {"success": False, "error": result.get("error", "transcription failed")}
        transcript = str(result.get("text") or result.get("formatted") or "").strip()
        if not transcript:
            return {"success": False, "error": "No speech detected in the audio file"}

        translation = await _llm_translate(transcript, target_language, provider, model, base_url)
        if translation.startswith("Generation failed"):
            errors.append(translation)
            translation = ""

        spoken = None
        if speak and translation:
            spoken = await speak_fn(translation, "windows", "default")
            if not spoken.get("success"):
                errors.append(f"TTS failed: {spoken.get('error')}")

        return {
            "success": bool(translation) or bool(errors),
            "transcript": transcript,
            "translation": translation,
            "spoken": spoken,
            "errors": errors,
        }
