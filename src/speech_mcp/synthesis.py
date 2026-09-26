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
    voicestudio_client=None,
    model: str | None = None,
) -> dict:
    """Synthesize ``text`` and play it on the PC speaker. Honest errors only."""
    text = text.strip()
    if not text:
        return {"success": False, "error": "empty text"}

    t0 = time.monotonic()
    result = await _speak_inner(
        text,
        provider,
        voice_id,
        description,
        gemini_client,
        eleven_client,
        hume_client,
        gemma_client,
        voicestudio_client,
        model,
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
    voicestudio_client=None,
    model: str | None = None,
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
            effective_voice = voice_id or "Kore"
            _default_model = getattr(gemini, "default_model", None)
            _default_model = _default_model if isinstance(_default_model, str) else "gemini-3.8-flash-tts"
            effective_model = model or _default_model
            wav = await asyncio.to_thread(
                lambda: gemini.synthesize_wav(text, voice_name=effective_voice, model=effective_model)
            )
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
            return {"success": True, "provider": "gemini", "voice": effective_voice, "model": effective_model}

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

        if provider == "voicestudio":
            if not voicestudio_client:
                return {"success": False, "error": "VoiceStudio not configured - set VOICESTUDIO_ENABLED=true"}
            result = await voicestudio_client.synthesize(text, voice_id)
            if not result.get("success"):
                return result
            wav = result.get("wav_bytes")
            if not wav:
                return {"success": False, "provider": "voicestudio", "error": "VoiceStudio returned empty audio"}
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
            return {"success": True, "provider": "voicestudio", "voice": voice_id}

        # qwen (local Qwen3-TTS: endpoint or extra, honest errors)
        if provider == "qwen":
            from speech_mcp.providers.qwen_tts import QwenTTSProvider

            qwen = QwenTTSProvider()
            wav = await asyncio.to_thread(lambda: qwen.synthesize_wav(text, voice=voice_id))
            if not wav:
                return {"success": False, "provider": "qwen", "error": "Qwen-TTS returned empty audio"}
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
            return {"success": True, "provider": "qwen", "voice": voice_id}

        # kokoro (local 82M Apache TTS, honest extra)
        if provider == "kokoro":
            from speech_mcp.providers.kokoro import KokoroProvider

            koko = KokoroProvider()
            wav = await asyncio.to_thread(lambda: koko.synthesize_wav(text, voice=voice_id))
            if not wav:
                return {"success": False, "provider": "kokoro", "error": "Kokoro returned empty audio"}
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
            return {"success": True, "provider": "kokoro", "voice": voice_id}

        # windows (SAPI5) fallback
        import pyttsx3

        def _win():
            engine = pyttsx3.init()
            if voice_id and voice_id != "default":
                try:
                    voices = engine.getProperty("voices") or []
                    target_id = None
                    for v in voices:
                        vid = getattr(v, "id", "") or ""
                        vname = getattr(v, "name", "") or ""
                        if voice_id == vid or voice_id.lower() in vname.lower() or voice_id.lower() in vid.lower():
                            target_id = vid
                            break
                    if not target_id:
                        alias_map = {"heart": "zira", "sky": "hazel", "adam": "david"}
                        alias = alias_map.get(voice_id.lower())
                        if alias:
                            for v in voices:
                                if alias in (getattr(v, "name", "") or "").lower():
                                    target_id = getattr(v, "id", "")
                                    break
                    if not target_id and voices:
                        idx = abs(hash(voice_id)) % len(voices)
                        target_id = getattr(voices[idx], "id", None)
                    if target_id:
                        engine.setProperty("voice", target_id)
                except Exception:
                    pass
            engine.say(text)
            engine.runAndWait()

        await asyncio.to_thread(_win)
        return {"success": True, "provider": "windows", "voice": voice_id}
    except Exception as e:
        logger.exception("speak_text failed for provider %s", provider)
        return {"success": False, "provider": provider, "error": str(e)}
