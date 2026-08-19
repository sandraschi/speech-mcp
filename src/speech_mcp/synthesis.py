"""Standalone text-to-speech dispatch used by readout/translate/chat tools.

Mirrors the dispatch in ``tools/speech.py::text_to_speech`` without the MCP
context, so other tools can speak without duplicating provider wiring.
Provider clients are passed in by the caller (avoids circular imports).
"""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import time

from speech_mcp.storage import analytics_record
from speech_mcp.tools.speech import _elevenlabs_speak, _hume_speak, _play_wav_file

logger = logging.getLogger(__name__)


async def speak_text(
    text: str,
    provider: str = "windows",
    voice_id: str = "default",
    description: str | None = None,
    gemini_client=None,
    eleven_client=None,
    hume_client=None,
    gemma_client=None,
) -> dict:
    """Synthesize ``text`` and play it on the PC speaker. Honest errors only."""
    text = text.strip()
    if not text:
        return {"success": False, "error": "empty text"}

    t0 = time.monotonic()
    result = await _speak_inner(
        text, provider, voice_id, description, gemini_client, eleven_client, hume_client, gemma_client
    )
    analytics_record(
        provider=provider,
        op="tts",
        latency_ms=round((time.monotonic() - t0) * 1000, 1),
        success=bool(result.get("success")),
        source="tool",
        meta={"voice_id": voice_id},
    )
    return result


async def _speak_inner(
    text: str,
    provider: str,
    voice_id: str,
    description: str | None,
    gemini_client,
    eleven_client,
    hume_client,
    gemma_client,
) -> dict:
    try:
        if provider == "gemma":
            gemma = gemma_client
            if not gemma:
                return {"success": False, "error": "Gemma provider not initialized"}
            played = await asyncio.to_thread(lambda: gemma.synthesize_and_play(text, voice=voice_id))
            return {"success": bool(played), "provider": "gemma", "voice": voice_id}

        if provider == "gemini":
            gemini = gemini_client
            if not gemini:
                return {"success": False, "error": "Gemini provider not configured"}
            wav = await asyncio.to_thread(lambda: gemini.synthesize_wav(text, voice_name=voice_id or "Kore"))
            if not wav:
                return {"success": False, "error": "Gemini returned empty audio"}
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(wav)
                tmp_path = tmp.name
            try:
                await _play_wav_file(tmp_path)
            finally:
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass
            return {"success": True, "provider": "gemini", "voice": voice_id}

        if provider == "hume":
            hume = hume_client
            if not hume:
                return {"success": False, "error": "Hume provider not configured"}
            await _hume_speak(hume, text, description=description)
            return {"success": True, "provider": "hume"}

        if provider == "elevenlabs":
            el = eleven_client
            if not el:
                return {"success": False, "error": "ElevenLabs not configured"}
            await asyncio.to_thread(lambda: _elevenlabs_speak(el, text, voice_id=voice_id))
            return {"success": True, "provider": "elevenlabs", "voice": voice_id}

        # windows (SAPI5) fallback
        import pyttsx3

        def _win():
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()

        await asyncio.to_thread(_win)
        return {"success": True, "provider": "windows"}
    except Exception as e:
        logger.exception("speak_text failed for provider %s", provider)
        return {"success": False, "provider": provider, "error": str(e)}
