"""Fleet voice readouts - spoken status + reading mode."""

from __future__ import annotations

import logging
from typing import Annotated

from fastmcp import Context, FastMCP
from pydantic import Field

from speech_mcp.state import _timers, get_store

logger = logging.getLogger(__name__)

# FastMCP tool annotations (TOOL_DESIGN_STANDARDS §9) - dict format works with all 3.x.
_MUTATING = {"readonly": False}

PROVIDER_LABELS = {
    "hume": "Hume AI",
    "elevenlabs": "ElevenLabs",
    "gemini": "Gemini",
    "gemma": "Gemma local",
    "funasr": "FunASR local STT",
    "windows": "Windows SAPI",
    "sherpa_streaming": "Sherpa streaming",
}


def _compose_status(providers: dict[str, bool]) -> str:
    configured = [PROVIDER_LABELS.get(k, k) for k, ok in providers.items() if ok]
    try:
        rag_sources = len(get_store().list_sources())
    except Exception:
        rag_sources = 0
    timers = len(_timers)
    parts = []
    parts.append(f"{len(configured)} of {len(providers)} speech providers configured.")
    if configured:
        parts.append("Configured: " + ", ".join(configured) + ".")
    parts.append(f"Knowledge base holds {rag_sources} source documents.")
    parts.append(f"{timers} active timer{'s' if timers != 1 else ''}.")
    gpu = None
    try:
        from speech_mcp.server import _gpu_info

        gpu = _gpu_info()
    except Exception:
        gpu = None
    if gpu and gpu.get("available"):
        parts.append(f"GPU: {gpu.get('name', 'CUDA')} with {gpu.get('vram_free_gb', '?')} gigabytes free.")
    else:
        parts.append("Running on CPU.")
    return " ".join(parts)


def register_readout_tools(mcp: FastMCP, providers: dict[str, bool], speak_fn) -> None:
    """Register spoken readout tools. ``speak_fn`` is the speak_text dispatcher."""

    @mcp.tool(annotations=_MUTATING)
    async def spoken_status_readout(
        provider: Annotated[
            str, Field(description="TTS provider for the readout: windows, gemini, gemma, hume, elevenlabs.")
        ] = "windows",
        voice_id: Annotated[str, Field(description="Voice for the readout.")] = "default",
        ctx: Context | None = None,
    ) -> dict:
        """Speak a live fleet status readout (providers, RAG, timers, GPU).

        ## Return Format
        ``{"success": bool, "text": str, "spoken": {...}}``

        ## Examples
        ``spoken_status_readout()`` -> speaks the current status over SAPI5.
        """
        text = _compose_status(providers)
        spoken = await speak_fn(text, provider, voice_id)
        if ctx:
            await ctx.info(f"Readout spoken: {text[:80]}...")
        return {"success": bool(spoken.get("success")), "text": text, "spoken": spoken}

    @mcp.tool(annotations=_MUTATING)
    async def read_aloud(
        text: Annotated[
            str | None, Field(description="Text to speak aloud. Mutually exclusive with file_path.")
        ] = None,
        file_path: Annotated[
            str | None, Field(description="Path to a text file to speak. Mutually exclusive with text.")
        ] = None,
        provider: Annotated[
            str, Field(description="TTS provider: windows, gemini, gemma, hume, elevenlabs.")
        ] = "windows",
        voice_id: Annotated[str, Field(description="Voice for synthesis.")] = "default",
    ) -> dict:
        """Reading mode: speak arbitrary text or the contents of a text file.

        ## Return Format
        ``{"success": bool, "spoken": {...}, "chars": int}``

        ## Examples
        ``read_aloud(file_path="C:/notes.txt")`` -> reads the file aloud.
        """
        if text is None and file_path is None:
            return {"success": False, "error": "Provide text or file_path"}
        if text is not None and file_path is not None:
            return {"success": False, "error": "Provide only one of text or file_path"}
        if file_path is not None:
            try:
                with open(file_path, encoding="utf-8") as f:
                    text = f.read()
            except OSError as e:
                return {"success": False, "error": f"Cannot read {file_path}: {e}"}
        assert text is not None
        if not text.strip():
            return {"success": False, "error": "Nothing to read - empty input"}
        spoken = await speak_fn(text.strip(), provider, voice_id)
        return {"success": bool(spoken.get("success")), "spoken": spoken, "chars": len(text.strip())}
