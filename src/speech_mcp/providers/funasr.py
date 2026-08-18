"""
Alibaba FunASR local STT provider.

Supports two deployment patterns:
  1. Native — lazy-loaded AutoModel (VAD + ASR + punctuation + speaker diarization)
  2. Sidecar — OpenAI-compatible /v1/audio/transcriptions HTTP endpoint

Models: Fun-ASR-Nano-2512, SenseVoiceSmall, and other FunASR hub entries.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import shutil
import tempfile
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FunASRConfig:
    """Runtime configuration for FunASR (env vars resolved in server.py)."""

    model: str = "FunAudioLLM/Fun-ASR-MLT-Nano-2512"
    device: str = "cuda:0"
    hub: str = "hf"
    vad_model: str | None = "fsmn-vad"
    punc_model: str | None = "ct-punc"
    spk_model: str | None = "cam++"
    openai_base_url: str | None = None
    batch_size: int = 1


def _extract_text_from_result(raw: Any) -> str:
    """Pull the recognized text out of a FunASR generate() result."""
    if not raw:
        return ""
    entry = raw[0] if isinstance(raw, list) else raw
    if not isinstance(entry, dict):
        return str(entry or "").strip()
    for key in ("text", "text_tn"):
        val = entry.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ""


def _parse_transcript_result(raw: Any) -> dict:
    """Normalize FunASR generate() output into structured segments + plain text."""
    if not raw:
        return {"text": "", "segments": []}

    entry = raw[0] if isinstance(raw, list) else raw
    if not isinstance(entry, dict):
        return {"text": str(entry), "segments": []}

    segments: list[dict] = []
    if "sentence_info" in entry:
        for sent in entry["sentence_info"]:
            start_ms = sent.get("start", 0)
            end_ms = sent.get("end", 0)
            segments.append(
                {
                    "speaker": sent.get("spk", 0),
                    "start_s": round(start_ms / 1000.0, 3),
                    "end_s": round(end_ms / 1000.0, 3),
                    "text": sent.get("text", ""),
                    "emotion": sent.get("emotion"),
                }
            )
        text = " ".join(s["text"] for s in segments if s["text"]).strip()
        # Some models (Fun-ASR-MLT) emit sentence_info with empty per-sentence
        # text while the global text holds the full transcript. Don't lose it.
        if not text:
            text = _extract_text_from_result(entry)
        return {"text": text, "segments": segments}

    text = _extract_text_from_result(entry)
    return {"text": text, "segments": segments}


def _format_transcript_lines(parsed: dict) -> str:
    """Human-readable transcript with timestamps and speaker labels."""
    if not parsed["segments"]:
        return parsed.get("text", "")

    lines: list[str] = []
    for seg in parsed["segments"]:
        emotion = seg.get("emotion")
        emotion_tag = f" ({emotion})" if emotion else ""
        lines.append(
            f"[{seg['start_s']:05.2f}s -> {seg['end_s']:05.2f}s] [Speaker {seg['speaker']}]{emotion_tag}: {seg['text']}"
        )
    return "\n".join(lines)


class FunASRProvider:
    """
    High-performance local ASR via Alibaba FunASR.

    Lazy-loads the model on first inference to keep MCP startup fast.
    """

    def __init__(self, config: FunASRConfig):
        self._config = config
        self._model: Any | None = None
        self._loaded_device: str | None = None
        self._vad_model: Any | None = None
        self._mode = "sidecar" if config.openai_base_url else "native"

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def model_id(self) -> str:
        return self._config.model

    def _ensure_native_model(self) -> Any:
        from speech_mcp.runtime_config import funasr_device

        device = funasr_device()

        # Device changed at runtime -> drop and reload on the new device.
        if self._model is not None and self._loaded_device != device:
            logger.info(
                "FunASR device changed %s -> %s; reloading model",
                self._loaded_device,
                device,
            )
            self._model = None

        if self._model is not None:
            return self._model

        try:
            from funasr import AutoModel  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("FunASR is not installed. Run: uv sync --extra funasr") from exc

        kwargs: dict[str, Any] = {
            "model": self._config.model,
            "device": device,
            "hub": self._config.hub,
            # Fun-ASR-MLT-Nano-2512 (and SenseVoice) ship remote code; required
            # for hub="hf" loading, otherwise AutoModel fails and STT is disabled.
            "trust_remote_code": True,
        }
        if self._config.vad_model:
            kwargs["vad_model"] = self._config.vad_model
        if self._config.punc_model:
            kwargs["punc_model"] = self._config.punc_model
        if self._config.spk_model:
            kwargs["spk_model"] = self._config.spk_model

        logger.info(
            "Loading FunASR model %s on %s (hub=%s)",
            self._config.model,
            device,
            self._config.hub,
        )
        self._model = AutoModel(**kwargs)
        self._loaded_device = device
        return self._model

    def _generate_sync(self, input_path: str, language: str = "auto") -> Any:
        if self._mode == "sidecar":
            return self._transcribe_sidecar_sync(input_path, language)

        model = self._ensure_native_model()
        gen_kwargs: dict[str, Any] = {"input": input_path, "batch_size": self._config.batch_size}
        if language and language != "auto":
            gen_kwargs["language"] = language
        return model.generate(**gen_kwargs)

    def _transcribe_sidecar_sync(self, input_path: str, language: str = "auto") -> list[dict]:
        base = (self._config.openai_base_url or "").rstrip("/")
        url = f"{base}/audio/transcriptions"
        data: dict[str, str] = {"model": self._config.model}
        if language and language != "auto":
            data["language"] = language

        with open(input_path, "rb") as audio_file:
            files = {"file": (os.path.basename(input_path), audio_file)}
            with httpx.Client(timeout=300.0) as client:
                resp = client.post(url, data=data, files=files)
                resp.raise_for_status()
                payload = resp.json()

        text = payload.get("text", "")
        return [{"text": text}]

    async def transcribe_file(
        self,
        file_path: str,
        language: str = "auto",
    ) -> dict:
        """
        Transcribe a local audio file (WAV, MP3, FLAC, etc.).

        Returns structured segments with speaker labels, timestamps, and emotions
        when the model supports them (e.g. SenseVoiceSmall).
        """
        if not os.path.isfile(file_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "recovery": "Provide an existing WAV/MP3/FLAC path, or use transcribe_stream_chunk with raw audio.",
            }

        try:
            raw = await asyncio.to_thread(lambda: self._generate_sync(file_path, language))
            parsed = _parse_transcript_result(raw)
            # MLT-class models often emit the full transcript without usable
            # per-sentence timestamps. When segments carry no text, fall back to
            # VAD-chunked transcription so each subtitle block gets a timestamp.
            if self._mode == "native" and not any(s["text"] for s in parsed["segments"]):
                if _extract_text_from_result(raw):
                    parsed = await asyncio.to_thread(
                        lambda: self._chunked_transcribe(file_path, language, min_chunk_s=2.0)
                    )
            return {
                "success": True,
                "provider": "funasr",
                "mode": self._mode,
                "model": self._config.model,
                "text": parsed["text"],
                "segments": parsed["segments"],
                "formatted": _format_transcript_lines(parsed),
            }
        except Exception as exc:
            logger.exception("FunASR file transcription failed")
            return {"success": False, "error": str(exc), "provider": "funasr"}

    def _vad_chunks_sync(self, audio_path: str) -> list[tuple[int, int]]:
        """Return speech chunks [(start_ms, end_ms)] via the fsmn-vad model."""
        from funasr import AutoModel  # type: ignore[import-not-found]

        from speech_mcp.runtime_config import funasr_device

        vad = self._vad_model
        if vad is None:
            vad = AutoModel(
                model=self._config.vad_model,
                device=funasr_device(),
                hub=self._config.hub,
                trust_remote_code=True,
                disable_update=True,
            )
            self._vad_model = vad
        res = vad.generate(input=audio_path, disable_pbar=True)
        chunks: list[tuple[int, int]] = []
        if not isinstance(res, list):
            res = [res]
        for entry in res:
            value = entry.get("value") if isinstance(entry, dict) else None
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, (list, tuple)) and len(item) >= 2:
                        start_ms, end_ms = int(item[0]), int(item[1])
                        if end_ms - start_ms >= 300:
                            chunks.append((start_ms, end_ms))
        return chunks

    def _chunked_transcribe(self, audio_path: str, language: str, min_chunk_s: float = 2.0) -> dict:
        """Transcribe each VAD speech chunk separately for reliable timestamps.

        The MLT model returns a full transcript without per-sentence
        timestamps; chunked transcription yields text + start/end per subtitle
        block. Slices are passed as raw waveforms (no temp files).
        """
        import numpy as np  # type: ignore[import-not-found]
        import soundfile as sf  # type: ignore[import-not-found]

        chunks = self._vad_chunks_sync(audio_path)
        if not chunks:
            return {"text": "", "segments": []}

        model = self._ensure_native_model()
        data, sr = sf.read(audio_path, dtype="float32", always_2d=False)
        if data.ndim > 1:
            data = data.mean(axis=1)

        segments: list[dict] = []
        tmpdir = tempfile.mkdtemp(prefix="funasr-chunk-")
        try:
            for _, (start_ms, end_ms) in enumerate(chunks):
                start_s, end_s = start_ms / 1000.0, end_ms / 1000.0
                if end_s - start_s < min_chunk_s:
                    continue
                s = int(start_ms * sr / 1000)
                e = min(int(end_ms * sr / 1000), len(data))
                clip = np.ascontiguousarray(data[s:e])
                tmp_path = os.path.join(tmpdir, f"c{start_ms}.wav")
                sf.write(tmp_path, clip, sr, format="WAV", subtype="PCM_16")
                kwargs: dict[str, Any] = {"input": tmp_path, "batch_size": 1}
                if language and language != "auto":
                    kwargs["language"] = language
                res = model.generate(**kwargs)
                text = _extract_text_from_result(res)
                if text:
                    segments.append(
                        {
                            "speaker": None,
                            "start_s": round(start_s, 3),
                            "end_s": round(end_s, 3),
                            "text": text,
                            "emotion": None,
                        }
                    )
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

        full_text = " ".join(s["text"] for s in segments if s["text"]).strip()
        return {"text": full_text, "segments": segments}

    async def transcribe_chunk(
        self,
        audio_base64: str,
        sample_rate: int = 16000,
        language: str = "auto",
        mime_type: str = "audio/wav",
    ) -> dict:
        """
        Stateless transcription of a single audio chunk (base64-encoded).

        Writes to a temp file and runs the same pipeline as transcribe_file.
        """
        try:
            audio_bytes = base64.b64decode(audio_base64)
        except Exception as exc:
            return {"success": False, "error": f"Invalid base64 audio: {exc}"}

        if not audio_bytes:
            return {"success": False, "error": "Empty audio payload"}

        suffix = ".wav" if "wav" in mime_type else ".mp3" if "mpeg" in mime_type or "mp3" in mime_type else ".bin"
        tmp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp_path = tmp.name
                tmp.write(audio_bytes)

            result = await self.transcribe_file(tmp_path, language=language)
            if result.get("success"):
                result["sample_rate"] = sample_rate
            return result
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    async def health_probe(self) -> dict:
        """Lightweight availability check without loading weights."""
        if self._mode == "sidecar":
            base = (self._config.openai_base_url or "").rstrip("/")
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(f"{base}/models")
                    ok = resp.status_code < 500
                return {
                    "available": ok,
                    "mode": "sidecar",
                    "url": base,
                }
            except Exception as exc:
                return {"available": False, "mode": "sidecar", "error": str(exc)}

        try:
            import funasr  # noqa: F401  # type: ignore[import-not-found]

            return {
                "available": True,
                "mode": "native",
                "model": self._config.model,
                "loaded": self._model is not None,
            }
        except ImportError:
            return {
                "available": False,
                "mode": "native",
                "error": "funasr package not installed — run: uv sync --extra funasr",
            }
