"""VoiceStudio local TTS/clone sidecar provider (optional, disabled by default).

VoiceStudio (debpalash/VoiceStudio, AGPL-3.0) runs as a separate process:
Python backend on :3900, Rust control sidecar on :3902. speech-mcp never
embeds its code - this provider only talks HTTP/MCP to a running instance.

Transports used here:
  - Streamable HTTP MCP ``POST {base_url}/mcp`` for generate_speech,
    clone_voice, list_voices, check_health (per-agent voice via
    X-VoiceStudio-Client-Id header).
  - OpenAI-compatible ``POST {base_url}/v1/audio/transcriptions`` for STT
    fallback (files/scripts path; FunASR stays the default STT).
  - Loopback discovery ``GET {base_url}/.well-known/voicestudio-speech``.

Env (resolved in server.py, mirrored here for standalone use):
  VOICESTUDIO_ENABLED=false, VOICESTUDIO_URL=http://127.0.0.1:3900,
  VOICESTUDIO_CLIENT_ID=speech-mcp, VOICESTUDIO_TIMEOUT_S=120,
  VOICESTUDIO_BASE_PATH= (files-mode shared dir, required for path I/O).
"""

from __future__ import annotations

import base64
import json
import logging
import os
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_URL = "http://127.0.0.1:3900"
DEFAULT_CLIENT_ID = "speech-mcp"
DEFAULT_TIMEOUT_S = 120.0


@dataclass(frozen=True)
class VoiceStudioConfig:
    """Runtime configuration for VoiceStudio (env vars resolved in server.py)."""

    base_url: str = DEFAULT_URL
    client_id: str = DEFAULT_CLIENT_ID
    timeout_s: float = DEFAULT_TIMEOUT_S
    base_path: str | None = None


def config_from_env() -> VoiceStudioConfig:
    """Build config from VOICESTUDIO_* env vars (disabled by default)."""
    try:
        timeout = float(os.getenv("VOICESTUDIO_TIMEOUT_S", str(DEFAULT_TIMEOUT_S)))
    except ValueError:
        timeout = DEFAULT_TIMEOUT_S
    base_path = os.getenv("VOICESTUDIO_BASE_PATH", "").strip() or None
    return VoiceStudioConfig(
        base_url=os.getenv("VOICESTUDIO_URL", DEFAULT_URL).rstrip("/"),
        client_id=os.getenv("VOICESTUDIO_CLIENT_ID", DEFAULT_CLIENT_ID),
        timeout_s=max(10.0, timeout),
        base_path=base_path,
    )


def is_enabled() -> bool:
    """True only when VOICESTUDIO_ENABLED=1/true/yes (default: False)."""
    return os.getenv("VOICESTUDIO_ENABLED", "").lower() in ("1", "true", "yes")


def _extract_mcp_result(result: Any) -> dict:
    """Unwrap a fastmcp CallToolResult into the tool result dict."""
    data = getattr(result, "data", None)
    if isinstance(data, dict):
        return data
    structured = getattr(result, "structured_content", None)
    if isinstance(structured, dict):
        return structured
    texts = [c.text for c in getattr(result, "content", []) if hasattr(c, "text")]
    for text in texts:
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except (ValueError, TypeError):
            continue
    return {"text": " ".join(texts)}


class VoiceStudioProvider:
    """Thin async client for a locally running VoiceStudio backend.

    No weights are loaded in-process. All synthesis happens in VoiceStudio;
    this class only ferries text in and WAV bytes out.
    """

    def __init__(self, config: VoiceStudioConfig | None = None):
        self._config = config or config_from_env()

    @property
    def base_url(self) -> str:
        return self._config.base_url

    @property
    def client_id(self) -> str:
        return self._config.client_id

    async def _mcp_call(self, tool: str, arguments: dict) -> dict:
        # fastmcp.Client performs the MCP handshake (initialize -> capture
        # Mcp-Session-Id -> notifications/initialized) automatically before
        # the first tools/call, and re-attaches the session id to every
        # subsequent request on this client instance. See BUG-047.
        from fastmcp import Client
        from fastmcp.client.transports import StreamableHttpTransport

        transport = StreamableHttpTransport(
            f"{self._config.base_url}/mcp",
            headers={"X-VoiceStudio-Client-Id": self._config.client_id},
        )
        async with Client(transport, timeout=self._config.timeout_s) as client:
            result = await client.call_tool(tool, arguments)
        return _extract_mcp_result(result)

    async def health_probe(self) -> dict:
        """Lightweight availability check (no model load, no synthesis)."""
        import httpx

        base = self._config.base_url
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                disco = await client.get(f"{base}/.well-known/voicestudio-speech")
                ok = disco.status_code < 500
                try:
                    health = await self._mcp_call("check_health", {})
                except Exception as exc:
                    logger.debug("VoiceStudio check_health via MCP failed: %s", exc)
                    health = {}
            return {"available": ok, "mode": "sidecar", "url": base, "backend": health}
        except Exception as exc:
            return {"available": False, "mode": "sidecar", "url": base, "error": str(exc)}

    async def list_voices(self) -> dict:
        """Enumerate VoiceStudio voices via MCP list_voices."""
        try:
            result = await self._mcp_call("list_voices", {})
            voices = result.get("voices", result.get("profiles", []))
            return {"success": True, "provider": "voicestudio", "voices": voices, "raw": result}
        except Exception as exc:
            logger.exception("VoiceStudio list_voices failed")
            return {
                "success": False,
                "provider": "voicestudio",
                "error": str(exc),
                "error_type": "connection",
                "suggestions": [
                    "Start VoiceStudio (Electron app or Docker backend) so :3900 serves /mcp.",
                    "Set VOICESTUDIO_URL if the backend runs on another host/port.",
                ],
            }

    async def _download_audio_url(self, audio_url: str) -> bytes | None:
        import httpx

        url = audio_url if audio_url.startswith("http") else f"{self._config.base_url}{audio_url}"
        async with httpx.AsyncClient(timeout=self._config.timeout_s) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.content or None

    async def synthesize_wav(self, text: str, voice_id: str = "default", profile_id: str | None = None) -> bytes:
        """Synthesize text -> WAV bytes. Raises on failure (caller maps to dict)."""
        text = (text or "").strip()
        if not text:
            raise ValueError("empty text")
        args: dict[str, Any] = {"text": text}
        voice = profile_id or (None if voice_id in ("", "default") else voice_id)
        if voice:
            args["profile_id"] = voice
        # Prefer files mode (audio served at /audio/<id>.wav, no base64 in context).
        if self._config.base_path:
            args["output_mode"] = "files"
        result = await self._mcp_call("generate_speech", args)
        b64 = result.get("wav_base64") or result.get("audio_base64")
        if b64:
            return base64.b64decode(b64)
        audio_url = result.get("audio_url")
        if audio_url:
            data = await self._download_audio_url(str(audio_url))
            if data:
                return data
        output_path = result.get("output_path")
        if output_path and os.path.isfile(str(output_path)):
            with open(str(output_path), "rb") as f:
                return f.read()
        raise RuntimeError(f"VoiceStudio returned no audio (keys: {sorted(result.keys())})")

    async def synthesize(self, text: str, voice_id: str = "default") -> dict:
        """Synthesize text -> WAV bytes wrapped in a dialogic dict."""
        try:
            wav = await self.synthesize_wav(text, voice_id)
            if not wav:
                raise RuntimeError("VoiceStudio returned empty audio")
            return {"success": True, "provider": "voicestudio", "voice": voice_id, "wav_bytes": wav}
        except Exception as exc:
            logger.exception("VoiceStudio synthesis failed")
            return {
                "success": False,
                "provider": "voicestudio",
                "error": str(exc),
                "error_type": "connection",
                "suggestions": [
                    "Start VoiceStudio backend (Electron app, or Docker) on VOICESTUDIO_URL.",
                    "Pre-install the OmniVoice model (first call downloads ~2.3GB).",
                    "For Docker/remote agents set OMNIVOICE_MCP_ALLOWED_HOSTS on the backend.",
                ],
            }

    async def clone_voice(self, name: str, ref_audio_path: str) -> dict:
        """Clone a voice from a reference file (consent-verified audio only)."""
        if not name.strip():
            return {"success": False, "error": "name is required"}
        if not os.path.isfile(ref_audio_path):
            return {"success": False, "error": f"File not found: {ref_audio_path}"}
        try:
            if self._config.base_path:
                result = await self._mcp_call("clone_voice", {"name": name, "ref_audio_path": ref_audio_path})
            else:
                with open(ref_audio_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("ascii")
                result = await self._mcp_call("clone_voice", {"name": name, "ref_audio_b64": b64})
            profile_id = result.get("profile_id") or result.get("voice_id") or result.get("id")
            if not profile_id:
                return {"success": False, "error": f"clone returned no profile_id: {sorted(result.keys())}"}
            return {"success": True, "provider": "voicestudio", "profile_id": str(profile_id), "name": name}
        except Exception as exc:
            logger.exception("VoiceStudio clone_voice failed")
            return {"success": False, "provider": "voicestudio", "error": str(exc), "error_type": "connection"}

    async def transcribe_file(self, file_path: str, language: str = "auto") -> dict:
        """Transcribe via OpenAI-compatible endpoint (fallback; FunASR stays default)."""
        import httpx

        if not os.path.isfile(file_path):
            return {"success": False, "provider": "voicestudio", "error": f"File not found: {file_path}"}
        try:
            base = self._config.base_url.rstrip("/")
            data: dict[str, str] = {"model": "voicestudio"}
            if language and language != "auto":
                data["language"] = language
            with open(file_path, "rb") as audio_file:
                files = {"file": (os.path.basename(file_path), audio_file)}
                async with httpx.AsyncClient(timeout=300.0) as client:
                    resp = await client.post(f"{base}/v1/audio/transcriptions", data=data, files=files)
                    resp.raise_for_status()
                    payload = resp.json()
            return {"success": True, "provider": "voicestudio", "text": payload.get("text", ""), "raw": payload}
        except Exception as exc:
            logger.exception("VoiceStudio transcription failed")
            return {"success": False, "provider": "voicestudio", "error": str(exc), "error_type": "connection"}
