"""Qwen3-TTS local provider (0.6B Flash class, realtime-capable).

Priority:
1. OpenAI-compat endpoint at QWEN_TTS_URL (e.g. local Qwen3-TTS server,
   vLLM, LM Studio with a TTS model) - no extra install.
2. In-process via the official ``qwen-tts`` package
   (``from qwen_tts import Qwen3TTSModel``, model
   Qwen/Qwen3-TTS-12Hz-0.6B-Base) - needs ``uv sync --extra qwen-tts``.
   Stock transformers has NO Qwen3TTS class - do not use it here.

Neither available -> explicit error, never silent fake audio.
Docs: research/2026-09-26-open-speech-radar.md section 3.
"""

from __future__ import annotations

import io
import logging
import os
import wave

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "Qwen/Qwen3-TTS-12Hz-0.6B-Base"
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
        self._local = None

    @property
    def available(self) -> bool:
        if self.endpoint:
            return True
        try:
            import qwen_tts  # noqa: F401
        except ImportError:
            return False
        return True

    def _load_model(self):
        if self._local is not None:
            return self._local
        try:
            import torch
            from qwen_tts import Qwen3TTSModel
        except ImportError as e:
            raise RuntimeError(f"qwen-tts not installed - run `uv sync --extra qwen-tts`. ({e})") from e
        use_cuda = torch.cuda.is_available()
        try:
            self._local = Qwen3TTSModel.from_pretrained(
                self.model,
                device_map="cuda:0" if use_cuda else "cpu",
                dtype=torch.bfloat16 if use_cuda else torch.float32,
            )
        except Exception as e:
            raise RuntimeError(f"Qwen-TTS model load failed ({self.model}): {e}") from e
        return self._local

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
        """Voice-clone synthesis (Base model path, per official README).

        Needs QWEN_TTS_REF_AUDIO (+ QWEN_TTS_REF_TEXT) - 3 s of reference
        speech. Without it the Base model has no voice to clone.
        """
        model = self._load_model()
        ref_audio = os.getenv("QWEN_TTS_REF_AUDIO", "").strip()
        ref_text = os.getenv("QWEN_TTS_REF_TEXT", "").strip()
        if not ref_audio or not ref_text:
            raise RuntimeError(
                "Qwen-TTS Base needs QWEN_TTS_REF_AUDIO + QWEN_TTS_REF_TEXT "
                "(3s reference speech) for voice cloning - or set QWEN_TTS_URL "
                "to a running endpoint. Clone your own voice once, reuse forever."
            )
        language = os.getenv("QWEN_TTS_LANG", "English").strip() or "English"
        try:
            wavs, sr = model.generate_voice_clone(
                text=text,
                language=language,
                ref_audio=ref_audio,
                ref_text=ref_text,
            )
        except Exception as e:
            raise RuntimeError(f"Qwen-TTS synthesis failed: {e}") from e
        if wavs is None or len(wavs) == 0:
            raise ValueError("Qwen-TTS returned empty audio")
        import numpy as np

        pcm = (np.asarray(wavs[0]) * 32767).astype("<i2").tobytes()
        return _wav_from_pcm(bytes(pcm), rate=int(sr))

    @property
    def voices(self) -> list[str]:
        return list(self.VOICES)


qwen_tts_provider = QwenTTSProvider()
