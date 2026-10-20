"""Mistral Voxtral 3 provider - batch + realtime speech-to-text, and text-to-speech.

Verified against Mistral's public API reference and audio guides on 2026-10-20:

Batch transcription
    POST {base}/v1/audio/transcriptions   (multipart/form-data)
    fields: file | file_url | file_id, model, language, diarize,
            context_bias (list[str]), timestamp_granularities, stream
    -> {model, text, language, segments: [...], usage}

Speech synthesis
    POST {base}/v1/audio/speech           (application/json)
    fields: input, model, voice_id, response_format (pcm|wav|mp3|flac|opus),
            ref_audio, phoneme_hints, metadata, stream
    -> {"audio_data": "<base64>"}   (text/event-stream when stream=true)

Realtime transcription
    wss://api.mistral.ai/v1/audio/transcriptions/realtime?model=<realtime model>
    header: Authorization: Bearer <key>
    client events: session.update, input_audio.append, input_audio.end
    server events: session.created, session.updated, transcription.text.delta,
                   transcription.done, turn.start, turn.eager_end, turn.resume,
                   turn.end, error

Two documented constraints shape this module:

1. ``diarize`` and ``turn_detection`` are mutually exclusive in a realtime
   session - asking for both returns "Diarization is not compatible with turn
   detection". Sending ``turn_detection`` to the *file* endpoint returns 400.
2. Turn-detection thresholds must keep their order (start >= eager_end > end,
   and end_timeout_ms >= min_silence_ms) or the session rejects the update.

Self-hosting is a *different* lane, not a flag on the hosted one:

- ``mistralai/Voxtral-Mini-4B-Realtime-2602`` is Apache-2.0 and ships a vLLM
  deployment (``library_name: vllm``), so a local vLLM server speaks the
  OpenAI-shaped ``/v1/audio/transcriptions`` route.
- ``mistralai/Voxtral-4B-TTS-2603`` is **CC-BY-NC-4.0** (non-commercial).
  speech-mcp is MIT and embeds commercially, so this provider never loads those
  weights in-process and never defaults to them. TTS here is hosted-API only
  unless the operator points ``MISTRAL_TTS_BASE_URL`` at their own server.

The top-accuracy ``Voxtral Small Transcribe 3`` has no published weights; it is
hosted (or on-prem via Mistral). The self-hostable realtime model is the Mini.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import tempfile
from dataclasses import dataclass, field
from typing import Any

import httpx
import websockets

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.mistral.ai"
DEFAULT_STT_MODEL = "voxtral-small-latest"
DEFAULT_REALTIME_MODEL = "voxtral-mini-transcribe-realtime-3"
DEFAULT_TTS_MODEL = "voxtral-mini-tts-3"
REALTIME_PATH = "/v1/audio/transcriptions/realtime"

# Vocabulary that general ASR models reliably mangle on this fleet's audio.
# Override with MISTRAL_CONTEXT_BIAS (comma-separated) per deployment.
_DEFAULT_CONTEXT_BIAS: tuple[str, ...] = (
    "FastMCP",
    "MCP",
    "NSSM",
    "Voxtral",
    "LiveKit",
    "Uvicorn",
    "Mistral",
    "SSE",
)

# Default turn-detection profile (Mistral calls this the "Default" preset).
_DEFAULT_TURN_DETECTION: dict[str, float | int] = {
    "start_threshold": 0.5,
    "eager_end_threshold": 0.5,
    "end_threshold": 0.33,
    "min_silence_ms": 500,
    "end_timeout_ms": 3000,
}

_STATUS_HINTS: dict[int, str] = {
    400: "malformed request, or turn_detection/diarize used on the wrong endpoint",
    401: "the API key was not accepted",
    402: "payment required on the Mistral account",
    413: "audio payload too large",
    422: "unsupported field or value for this model",
    429: "rate limited; back off and retry",
}


@dataclass(frozen=True)
class MistralConfig:
    """Runtime configuration for the Voxtral 3 provider.

    ``self_hosted`` disables hosted-only features (diarization, context bias)
    instead of sending fields the local vLLM server may reject.
    """

    api_key: str = ""
    base_url: str = DEFAULT_BASE_URL
    stt_model: str = DEFAULT_STT_MODEL
    realtime_model: str = DEFAULT_REALTIME_MODEL
    tts_model: str = DEFAULT_TTS_MODEL
    tts_base_url: str = ""
    timeout_s: float = 300.0
    self_hosted: bool = False
    context_bias: tuple[str, ...] = field(default_factory=lambda: _DEFAULT_CONTEXT_BIAS)

    @property
    def rest_base(self) -> str:
        """Base URL without a trailing slash (the REST routes append /v1/...)."""
        return (self.base_url or DEFAULT_BASE_URL).rstrip("/")

    @property
    def speech_base(self) -> str:
        """Base URL for TTS, which may be a different host than STT."""
        return (self.tts_base_url or self.base_url or DEFAULT_BASE_URL).rstrip("/")

    @property
    def realtime_url(self) -> str:
        """WebSocket URL for realtime transcription, model pinned in the query."""
        return f"{self.rest_base.replace('https://', 'wss://').replace('http://', 'ws://')}{REALTIME_PATH}?model={self.realtime_model}"


def _headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"} if api_key else {}


def _format_transcript_lines(segments: list[dict]) -> str:
    """Human-readable transcript with timestamps and speaker labels (matches funasr.py)."""
    if not segments:
        return ""
    return "\n".join(
        f"[{s['start_s']:05.2f}s -> {s['end_s']:05.2f}s] [Speaker {s['speaker']}]: {s['text']}" for s in segments
    )


# Field names a segment chunk may use, paired with whether the value is milliseconds.
# The unit comes from the key name, never from the magnitude: a 1500 ms segment and
# a 1500 s segment are indistinguishable by value alone.
_START_KEYS: tuple[tuple[str, bool], ...] = (
    ("start_s", False),
    ("start", False),
    ("start_ms", True),
    ("startMs", True),
)
_END_KEYS: tuple[tuple[str, bool], ...] = (
    ("end_s", False),
    ("end", False),
    ("end_ms", True),
    ("endMs", True),
)


def _pick_seconds(item: dict, keys: tuple[tuple[str, bool], ...]) -> float:
    """Resolve the first present timestamp key into seconds."""
    for name, is_ms in keys:
        if name not in item or item[name] is None:
            continue
        try:
            number = float(item[name])
        except (TypeError, ValueError):
            continue
        return round(number / 1000.0, 3) if is_ms else round(number, 3)
    return 0.0


def _normalize_segments(raw: list[Any] | None) -> list[dict]:
    """Map Mistral segment chunks onto this repo's {speaker, start_s, end_s, text} shape.

    ``TranscriptionSegmentChunk`` is rendered as an opaque object in the public
    reference, so the accepted key spellings above are tolerant by design. Units
    are taken from the key name; a timestamp without a unit hint is read as seconds.
    """
    segments: list[dict] = []
    for item in raw or []:
        if not isinstance(item, dict):
            continue
        start = _pick_seconds(item, _START_KEYS)
        end = _pick_seconds(item, _END_KEYS)
        speaker = item.get("speaker", item.get("speaker_id", item.get("speakerId")))
        text = (item.get("text") or item.get("transcript") or "").strip()
        if not text:
            continue
        segments.append(
            {
                "speaker": speaker if speaker is not None else 1,
                "start_s": start,
                "end_s": end if end >= start else start,
                "text": text,
            }
        )
    return segments


def _decode_audio(payload: dict[str, Any]) -> bytes:
    """Pull base64 audio out of a /v1/audio/speech response."""
    data = payload.get("audio_data") or payload.get("audio")
    if not isinstance(data, str) or not data:
        raise ValueError("response contained no audio_data")
    return base64.b64decode(data)


class MistralProvider:
    """Voxtral 3 speech-to-text and text-to-speech over Mistral's REST API.

    Async surface matches ``FunASRProvider`` and ``MuseVoiceProvider``
    (``transcribe_file`` / ``transcribe_chunk`` / ``health_probe``) so it slots
    into the existing multi-provider STT and TTS tools unchanged.
    """

    def __init__(self, config: MistralConfig):
        if not config.self_hosted and not config.api_key:
            raise ValueError("MISTRAL_API_KEY is not set (or set MISTRAL_SELF_HOST_URL to use a local server).")
        self._config = config

    @property
    def config(self) -> MistralConfig:
        """The resolved configuration, exposed read-only for status reporting."""
        return self._config

    @property
    def model_id(self) -> str:
        """Batch transcription model id."""
        return self._config.stt_model

    async def transcribe_file(
        self,
        file_path: str,
        language: str = "auto",
        diarize: bool = True,
        context_bias: list[str] | None = None,
    ) -> dict:
        """Transcribe a local audio file, with speaker labels when the server supports it.

        ``context_bias`` biases recognition toward supplied terms. It defaults to
        the provider's configured vocabulary (fleet terms) and is skipped
        entirely when ``self_hosted`` because the local vLLM route does not
        document that field.
        """
        if not os.path.isfile(file_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "recovery": "Provide an existing WAV/MP3/FLAC path, or use transcribe_chunk for raw audio.",
                "provider": "mistral",
            }

        data: dict[str, Any] = {"model": self._config.stt_model}
        if language and language != "auto":
            data["language"] = language

        if not self._config.self_hosted:
            data["diarize"] = "true" if diarize else "false"
            # httpx repeats a list under one key, which is how the API expects
            # repeated context_bias fields in a multipart body.
            bias_terms = context_bias if context_bias is not None else list(self._config.context_bias)
            if bias_terms:
                data["context_bias"] = bias_terms

        try:
            with open(file_path, "rb") as audio:
                files = {"file": (os.path.basename(file_path), audio, "application/octet-stream")}
                async with httpx.AsyncClient(timeout=self._config.timeout_s) as client:
                    resp = await client.post(
                        f"{self._config.rest_base}/v1/audio/transcriptions",
                        headers=_headers(self._config.api_key),
                        data=data,
                        files=files,
                    )
        except Exception as exc:
            logger.exception("Mistral transcription request failed")
            return {"success": False, "error": str(exc), "provider": "mistral"}

        if resp.status_code != 200:
            hint = _STATUS_HINTS.get(resp.status_code, "unexpected response")
            return {
                "success": False,
                "error": f"[{resp.status_code}] {hint}: {resp.text[:300]}",
                "provider": "mistral",
            }

        try:
            payload = resp.json()
        except ValueError:
            return {"success": False, "error": "response was not JSON", "provider": "mistral"}

        segments = _normalize_segments(payload.get("segments"))
        text = (payload.get("text") or " ".join(s["text"] for s in segments)).strip()
        return {
            "success": True,
            "provider": "mistral",
            "model": payload.get("model", self._config.stt_model),
            "language": payload.get("language"),
            "text": text,
            "segments": segments,
            "formatted": _format_transcript_lines(segments),
        }

    async def transcribe_chunk(
        self,
        audio_base64: str,
        sample_rate: int = 16000,
        language: str = "auto",
        mime_type: str = "audio/wav",
    ) -> dict:
        """Stateless transcription of one base64-encoded audio chunk."""
        try:
            audio_bytes = base64.b64decode(audio_base64)
        except Exception as exc:
            return {"success": False, "error": f"Invalid base64 audio: {exc}", "provider": "mistral"}
        if not audio_bytes:
            return {"success": False, "error": "Empty audio payload", "provider": "mistral"}

        suffix = ".wav" if "wav" in mime_type else ".mp3" if ("mpeg" in mime_type or "mp3" in mime_type) else ".bin"
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

    async def synthesize_wav(self, text: str, voice_id: str | None = None) -> bytes:
        """Synthesize speech and return WAV bytes.

        Always requests ``response_format="wav"`` so callers never have to wrap
        PCM, and so the bytes drop straight into the existing play/save paths.
        """
        text = (text or "").strip()
        if not text:
            raise ValueError("text is required")
        body: dict[str, Any] = {
            "model": self._config.tts_model,
            "input": text,
            "response_format": "wav",
        }
        if voice_id and voice_id.lower() != "default":
            body["voice_id"] = voice_id

        async with httpx.AsyncClient(timeout=self._config.timeout_s) as client:
            resp = await client.post(
                f"{self._config.speech_base}/v1/audio/speech",
                headers=_headers(self._config.api_key),
                json=body,
            )
        if resp.status_code != 200:
            hint = _STATUS_HINTS.get(resp.status_code, "unexpected response")
            raise RuntimeError(f"Mistral TTS failed [{resp.status_code}] {hint}: {resp.text[:300]}")
        try:
            payload = resp.json()
        except ValueError as exc:
            raise RuntimeError("Mistral TTS returned a non-JSON body") from exc
        audio = _decode_audio(payload)
        if not audio:
            raise RuntimeError("Mistral TTS returned empty audio")
        return audio

    async def list_voices(self) -> dict:
        """List preset/custom voices available to this API key."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{self._config.speech_base}/v1/audio/voices",
                    headers=_headers(self._config.api_key),
                )
        except Exception as exc:
            return {"success": False, "error": str(exc), "provider": "mistral"}
        if resp.status_code != 200:
            return {
                "success": False,
                "error": f"[{resp.status_code}] {resp.text[:300]}",
                "provider": "mistral",
            }
        payload = resp.json()
        voices = payload if isinstance(payload, list) else payload.get("data", payload.get("voices", []))
        return {"success": True, "provider": "mistral", "voices": voices}

    async def health_probe(self) -> dict:
        """Cheap reachability check against /v1/models.

        A self-hosted vLLM server may not expose /v1/models depending on how it
        was launched, so a failure there is reported as ``configured`` rather
        than ``available: False`` - the server may still transcribe.
        """
        base = {
            "provider": "mistral",
            "model": self._config.stt_model,
            "self_hosted": self._config.self_hosted,
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self._config.rest_base}/v1/models", headers=_headers(self._config.api_key))
        except Exception as exc:
            return {**base, "available": False, "error": str(exc)}
        if resp.status_code != 200:
            return {**base, "available": False, "configured": True, "error": f"[{resp.status_code}]"}
        try:
            payload = resp.json()
        except ValueError:
            return {**base, "available": True, "configured": True}
        models = payload.get("data", []) if isinstance(payload, dict) else []
        return {
            **base,
            "available": True,
            "configured": True,
            "models": [
                m.get("id") for m in models if isinstance(m, dict) and "voxtral" in str(m.get("id", "")).lower()
            ],
        }


def _validate_turn_detection(td: dict[str, Any]) -> dict[str, Any]:
    """Enforce the documented ordering so a bad profile fails here, not mid-call."""
    merged = {**_DEFAULT_TURN_DETECTION, **td}
    if not (merged["start_threshold"] >= merged["eager_end_threshold"] > merged["end_threshold"]):
        raise ValueError(
            "turn_detection thresholds must satisfy start_threshold >= eager_end_threshold > end_threshold"
        )
    if merged["end_timeout_ms"] < merged["min_silence_ms"]:
        raise ValueError("turn_detection.end_timeout_ms must be >= min_silence_ms")
    return merged


class MistralRealtimeSession:
    """One realtime transcription session over Mistral's WebSocket endpoint.

    Two mutually exclusive modes, per the documented constraint:

    - **turn detection** (``turn_detection=...``): emits ``turn.start``,
      ``turn.eager_end``, ``turn.resume``, ``turn.end``. This is what a voice
      loop needs to decide when the speaker finished.
    - **diarization** (``diarize=True``): emits speaker-labelled text, but no
      turn events and no turn-based end-of-speech signal.

    Passing both raises immediately rather than letting the server reject the
    session after audio has already started (settings are frozen at that point).
    """

    def __init__(self, config: MistralConfig):
        self._config = config
        self._ws: Any = None

    async def connect(
        self,
        sample_rate: int = 24000,
        *,
        turn_detection: dict[str, Any] | None = None,
        diarize: bool = False,
        language: str | None = None,
    ) -> dict:
        """Open the session and apply settings before the first audio chunk."""
        if diarize and turn_detection is not None:
            raise ValueError(
                "Diarization is not compatible with turn detection: pick turn_detection for a "
                "voice loop, or diarize=True for a labelled transcript."
            )

        self._ws = await websockets.connect(
            self._config.realtime_url,
            additional_headers=_headers(self._config.api_key),
            max_size=None,
        )
        created = json.loads(await self._ws.recv())

        session: dict[str, Any] = {
            "audio_format": {"encoding": "pcm_s16le", "sample_rate": sample_rate},
        }
        if diarize:
            session["diarize"] = True
        else:
            session["turn_detection"] = _validate_turn_detection(turn_detection or {})
        if language:
            session["language"] = language

        await self._ws.send(json.dumps({"type": "session.update", "session": session}))
        return created

    async def send_audio(self, pcm: bytes) -> None:
        """Append raw PCM (s16le, mono) to the session."""
        await self._ws.send(json.dumps({"type": "input_audio.append", "audio": base64.b64encode(pcm).decode()}))

    async def end_stream(self) -> None:
        """Signal that no more audio follows; the server flushes transcription.done."""
        await self._ws.send(json.dumps({"type": "input_audio.end"}))

    async def recv_event(self) -> dict[str, Any] | None:
        """Return the next event, or None on a clean close.

        Server errors are raised as RuntimeError with the documented message so
        callers see "Diarization is not compatible..." instead of a bare close.
        """
        try:
            message = await self._ws.recv()
        except websockets.exceptions.ConnectionClosed as exc:
            if getattr(exc, "code", None) == 1000:
                return None
            raise RuntimeError(f"[{getattr(exc, 'code', '?')}] realtime session closed: {exc.reason or ''}") from exc
        if isinstance(message, bytes):
            return {"type": "unknown"}
        event = json.loads(message)
        if event.get("type") == "error":
            detail = event.get("error") or {}
            raise RuntimeError(detail.get("message") if isinstance(detail, dict) else str(detail))
        return event

    async def close(self) -> None:
        """Close the socket, tolerating an already-closed session."""
        if self._ws is not None:
            try:
                await self._ws.close()
            finally:
                self._ws = None
