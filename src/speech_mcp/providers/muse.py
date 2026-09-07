"""
Meta Muse Voice Transcribe provider.

Muse Voice Transcribe (released 2026-09-01, model id ``muse-voice-transcribe-1.0``)
combines streaming ASR, speaker diarization, and end-of-turn detection in one model.
Cloud-hosted only via the Meta Model API; requires MUSE_API_KEY.

Two endpoints, confirmed against Meta's own client recipe
(github.com/meta-models/meta-model-cookbook, 06_muse_voice/01_voice_api_fundamentals):

- One-shot file: POST https://api.meta.ai/v1/asr/transcribe (multipart, Authorization
  header). 32MB / 10-minute caps. Returns {transcript, turns, audioDurationMs}.
- Realtime: wss://api.meta.ai/v1/asr/realtime. Credential rides inside the JSON
  handshake, not an HTTP header. Audio goes as raw binary PCM frames (mono 16-bit,
  16kHz or 24kHz). Events come back tagged by "type": session, transcript,
  speaker, speechComplete (correlate by turnId), error.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import tempfile
from dataclasses import dataclass
from typing import Any

import httpx
import websockets

logger = logging.getLogger(__name__)

DEFAULT_STREAM_URL = "wss://api.meta.ai/v1/asr/realtime"
DEFAULT_TRANSCRIBE_URL = "https://api.meta.ai/v1/asr/transcribe"
DEFAULT_MODEL = "muse-voice-transcribe-1.0"

# Server closes ungracefully with these codes; map to actionable messages
# (mirrors the cookbook client's _closed() table).
_CLOSE_ADVICE: dict[int, str] = {
    1008: "bad request, or audio was paced too slowly or too fast",
    1011: "server error, or the maximum session duration was reached",
    1013: "rate limited; back off and reconnect",
}


@dataclass(frozen=True)
class MuseConfig:
    """Runtime configuration for Muse Voice Transcribe (env vars resolved in server.py)."""

    api_key: str
    model: str = DEFAULT_MODEL
    stream_url: str = DEFAULT_STREAM_URL
    transcribe_url: str = DEFAULT_TRANSCRIBE_URL


def _format_transcript_lines(segments: list[dict]) -> str:
    """Human-readable transcript with timestamps and speaker labels (matches funasr.py)."""
    if not segments:
        return ""
    lines = [f"[{s['start_s']:05.2f}s -> {s['end_s']:05.2f}s] [Speaker {s['speaker']}]: {s['text']}" for s in segments]
    return "\n".join(lines)


def _turns_to_segments(turns: list[dict]) -> list[dict]:
    """Normalize Muse's {speaker, startMs, endMs, transcript} turns into the
    {speaker, start_s, end_s, text} shape shared by every STT provider in this repo."""
    segments = []
    for turn in turns:
        start_ms = turn.get("startMs") or 0
        end_ms = turn.get("endMs") or start_ms
        segments.append(
            {
                "speaker": turn.get("speaker"),
                "start_s": round(start_ms / 1000.0, 3),
                "end_s": round(end_ms / 1000.0, 3),
                "text": (turn.get("transcript") or "").strip(),
            }
        )
    return segments


class MuseVoiceProvider:
    """
    Cloud STT via Meta's Muse Voice Transcribe.

    Same async surface as FunASRProvider (transcribe_file / transcribe_chunk /
    health_probe) so it drops straight into the existing multi-provider STT tools.
    """

    def __init__(self, config: MuseConfig):
        if not config.api_key:
            raise ValueError("MUSE_API_KEY is not set.")
        self._config = config

    @property
    def model_id(self) -> str:
        return self._config.model

    @property
    def config(self) -> MuseConfig:
        return self._config

    async def transcribe_file(self, file_path: str, language: str = "auto") -> dict:
        """Transcribe a local audio file via the one-shot file endpoint, diarized."""
        if not os.path.isfile(file_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "recovery": "Provide an existing WAV/MP3/FLAC path, or use transcribe_stream_chunk.",
            }

        request: dict[str, Any] = {
            "mode": "DIARIZATION",
            "model": self._config.model,
            "audioEncoding": "WAV",
        }
        if language and language != "auto":
            request["languageBias"] = [language]

        try:
            with open(file_path, "rb") as audio:
                async with httpx.AsyncClient(timeout=300.0) as client:
                    resp = await client.post(
                        self._config.transcribe_url,
                        headers={"Authorization": f"Bearer {self._config.api_key}"},
                        files={
                            "request": (None, json.dumps(request), "application/json"),
                            "audio": (os.path.basename(file_path), audio),
                        },
                    )
            if resp.status_code != 200:
                hint = {
                    400: "audio longer than the 10-minute cap, or a malformed request",
                    401: "the credential was not accepted",
                    413: "body over 32 MB",
                    429: "rate limited; back off and retry",
                }.get(resp.status_code, "unexpected response")
                return {
                    "success": False,
                    "error": f"[{resp.status_code}] {hint}: {resp.text[:300]}",
                    "provider": "muse",
                }

            payload = resp.json()
            segments = _turns_to_segments(payload.get("turns") or [])
            text = payload.get("transcript") or " ".join(s["text"] for s in segments if s["text"])
            return {
                "success": True,
                "provider": "muse",
                "model": self._config.model,
                "text": text.strip(),
                "segments": segments,
                "formatted": _format_transcript_lines(segments),
            }
        except Exception as exc:
            logger.exception("Muse file transcription failed")
            return {"success": False, "error": str(exc), "provider": "muse"}

    async def transcribe_chunk(
        self,
        audio_base64: str,
        sample_rate: int = 16000,
        language: str = "auto",
        mime_type: str = "audio/wav",
    ) -> dict:
        """Stateless transcription of a single audio chunk (base64-encoded)."""
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
        """Config-only check; there is no cheap ping for the realtime/file endpoints."""
        return {"available": True, "model": self._config.model}


def _normalize_event(frame: dict[str, Any]) -> dict[str, Any]:
    """Flatten a server frame into a type-tagged dict (handshake ack has no 'type')."""
    if "type" in frame:
        return frame
    if "sessionId" in frame:
        return {"type": "session", "sessionId": frame["sessionId"]}
    return {"type": "unknown", **frame}


class MuseRealtimeSession:
    """
    One realtime diarized transcription session over wss://api.meta.ai/v1/asr/realtime.

    Shared low-level client used by both the muse_transcribe_stream MCP tool
    (tools/muse_voice.py) and the browser-facing WS bridge (streaming.py), so the
    wire protocol is implemented exactly once.
    """

    def __init__(self, config: MuseConfig):
        self._config = config
        self._ws: Any = None

    async def connect(self, mode: str = "DIARIZATION", encoding: str = "PCM_16KHZ") -> dict:
        handshake = {
            "mode": mode,
            "authorization": {"accessToken": self._config.api_key},
            "audioEncoding": encoding,
            "model": self._config.model,
            "partialMode": "CUMULATIVE",
        }
        self._ws = await websockets.connect(self._config.stream_url, max_size=None)
        await self._ws.send(json.dumps(handshake))
        ack = _normalize_event(json.loads(await self._ws.recv()))
        if ack.get("type") == "error":
            await self.close()
            raise RuntimeError(ack.get("message", "handshake rejected"))
        return ack

    async def send_audio(self, pcm: bytes) -> None:
        await self._ws.send(pcm)

    async def end_stream(self) -> None:
        await self._ws.send(json.dumps({"type": "endStream"}))

    async def recv_event(self) -> dict[str, Any] | None:
        """Return the next normalized event, or None on a clean session close."""
        try:
            message = await self._ws.recv()
        except websockets.exceptions.ConnectionClosed as exc:
            code = getattr(exc, "code", None)
            if code == 1000:
                return None
            reason = (getattr(exc, "reason", "") or "").strip()
            advice = _CLOSE_ADVICE.get(code, "connection closed unexpectedly")
            detail = f": {reason}" if reason else ""
            raise RuntimeError(f"[{code}] {advice}{detail}") from exc
        if isinstance(message, bytes):
            return {"type": "unknown"}
        event = _normalize_event(json.loads(message))
        if event.get("type") == "error":
            raise RuntimeError(event.get("message", "unknown transcription error"))
        return event

    async def close(self) -> None:
        if self._ws is not None:
            await self._ws.close()
            self._ws = None
