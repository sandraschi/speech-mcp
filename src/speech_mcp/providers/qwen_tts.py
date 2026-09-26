"""Qwen3-TTS local provider (0.6B Flash class, realtime-capable).

Priority:
1. OpenAI-compat endpoint at QWEN_TTS_URL (e.g. local Qwen3-TTS server,
   vLLM, LM Studio with a TTS model) - no extra install.
2. In-process via ``transformers``/``modelscope`` model QWEN_TTS_MODEL
   (default Qwen/Qwen3-TTS-12Hz-0.6B) - needs ``uv sync --extra qwen-tts``.

Neither available -> explicit error, never silent fake audio.
Docs: research/2026-09-26-open-speech-radar.md section 3.
"""

from __future__ import annotations

import io
import logging
import os
import wave

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "Qwen/Qwen3-TTS-12Hz-0.6B"
DEFAULT_VOICE = "default"


def _wav_from_pcm(pcm: bytes, rate: int = 24000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(pcm)
    return buf.getvalue()


class QwenTTSProvider:
    """Local Qwen TTS. Honest-extra pattern (same as funasr/sherpa)."""

    MODEL_ID = DEFAULT_MODEL

    VOICES: list[str] = ["default"]

    def __init__(
        self,
        endpoint: str | None = None,
        model: str | None = None,
    ):
        self.endpoint = (endpoint or os.getenv("QWEN_TTS_URL", "")).strip().rstrip("/") or None
        self.model = (model or os.getenv("QWEN_TTS_MODEL", "")).strip() or DEFAULT_MODEL
        self._local = None

    @property
    def available(self) -> bool:
        if self.endpoint:
            return True
        try:
            import transformers  # noqa: F401
        except ImportError:
            return False
        return True

    def _require_local(self):
        try:
            import torch  # noqa: F401
            from transformers import AutoModelForTextToWaveform  # type: ignore
        except ImportError as e:
            raise RuntimeError(
                "Qwen-TTS not installed - run `uv sync --extra qwen-tts` "
                f"or set QWEN_TTS_URL to a running endpoint. ({e})"
            ) from e
        return AutoModelForTextToWaveform

    def synthesize_wav(self, text: str, voice: str = DEFAULT_VOICE) -> bytes:
        text = (text or "").strip()
        if not text:
            raise ValueError("empty text")
        if self.endpoint:
            return self._synthesize_via_endpoint(text, voice)
        return self._synthesize_local(text, voice)

    def _synthesize_via_endpoint(self, text: str, voice: str) -> bytes:
        import requests

        assert self.endpoint
        url = f"{self.endpoint}/v1/audio/speech"
        payload = {"model": self.model, "input": text, "voice": voice or DEFAULT_VOICE, "response_format": "wav"}
        try:
            resp = requests.post(url, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.content
            if not data:
                raise ValueError("Qwen-TTS endpoint returned empty audio")
            return data
        except Exception as e:
            raise RuntimeError(f"Qwen-TTS endpoint failed ({self.endpoint}): {e}") from e

    def _synthesize_local(self, text: str, voice: str) -> bytes:
        cls = self._require_local()
        raise RuntimeError(
            "Qwen-TTS in-process path is scaffold-only until the model weights "
            "are vendored - set QWEN_TTS_URL to a running Qwen3-TTS server "
            f"(model={self.model}). ({cls.__name__} resolved, wiring pending.)"
        )

    @property
    def voices(self) -> list[str]:
        return list(self.VOICES)


qwen_tts_provider = QwenTTSProvider()
