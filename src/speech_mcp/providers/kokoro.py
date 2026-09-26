"""Kokoro local TTS provider (82M, Apache 2.0, small-local king).

Needs ``uv sync --extra kokoro`` (``kokoro`` pip package + espeak-ng).
No API key, runs on CPU. Fallback when VRAM is tight or Qwen-TTS absent.
Docs: research/2026-09-26-open-speech-radar.md section 3.
"""

from __future__ import annotations

import io
import logging
import os
import wave

logger = logging.getLogger(__name__)


def _wav_from_pcm(pcm: bytes, rate: int = 24000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(pcm)
    return buf.getvalue()


class KokoroProvider:
    """Local Kokoro TTS. Honest-extra pattern (same as funasr/sherpa)."""

    VOICES: list[str] = ["default", "af_heart", "af_sky", "am_adam"]

    def __init__(self, voice: str | None = None):
        self.default_voice = (voice or os.getenv("KOKORO_VOICE", "")).strip() or "default"

    @property
    def available(self) -> bool:
        try:
            import kokoro  # noqa: F401
        except ImportError:
            return False
        return True

    def synthesize_wav(self, text: str, voice: str = "default") -> bytes:
        text = (text or "").strip()
        if not text:
            raise ValueError("empty text")
        try:
            from kokoro import KPipeline  # type: ignore
        except ImportError as e:
            raise RuntimeError(
                f"Kokoro not installed - run `uv sync --extra kokoro` (needs kokoro + espeak-ng). ({e})"
            ) from e
        lang = os.getenv("KOKORO_LANG", "a").strip() or "a"
        voice_id = voice if voice and voice != "default" else self.default_voice
        if voice_id == "default":
            voice_id = "af_heart"
        try:
            pipeline = KPipeline(lang_code=lang)
            chunks = bytearray()
            rate = 24000
            for _gs, _ps, audio in pipeline(text, voice=voice_id):
                import numpy as np

                pcm = (np.asarray(audio) * 32767).astype("<i2").tobytes()
                chunks.extend(pcm)
                rate = getattr(pipeline, "sample_rate", rate) or rate
            if not chunks:
                raise ValueError("Kokoro returned empty audio")
            return _wav_from_pcm(bytes(chunks), rate=rate)
        except Exception as e:
            raise RuntimeError(f"Kokoro synthesis failed: {e}") from e

    @property
    def voices(self) -> list[str]:
        return list(self.VOICES)


kokoro_provider = KokoroProvider()
