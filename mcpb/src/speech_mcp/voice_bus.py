"""Fleet Voice Command Bus — post STT intents to fleet-agent."""

from __future__ import annotations

import json
import logging
import os
import tempfile
import wave
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_transcribe_path: Callable[[Path], str] | None = None


def set_transcribe_path_hook(fn: Callable[[Path], str]) -> None:
    """Register STT from server startup (FunASR transcribe_file, etc.)."""
    global _transcribe_path
    _transcribe_path = fn


def fleet_voice_enabled() -> bool:
    flag = os.environ.get("FLEET_VOICE_DELEGATE", "").strip().lower()
    if flag in ("0", "false", "no"):
        return False
    if flag in ("1", "true", "yes"):
        return True
    return bool(os.environ.get("FLEET_VOICE_ROUTER_URL", "").strip())


def router_url() -> str:
    return os.environ.get(
        "FLEET_VOICE_ROUTER_URL",
        "http://127.0.0.1:10996/api/voice/intent",
    ).strip()


def command_seconds() -> float:
    try:
        return max(2.0, min(float(os.environ.get("FLEET_VOICE_COMMAND_SECONDS", "6")), 30.0))
    except ValueError:
        return 6.0


def pcm_to_wav_path(pcm_frames: list[bytes], *, rate: int = 16000, channels: int = 1) -> Path:
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    path = Path(tmp.name)
    tmp.close()
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        for frame in pcm_frames:
            wf.writeframes(frame)
    return path


def transcribe_wav(path: Path) -> str:
    if _transcribe_path is None:
        logger.warning("No STT hook registered; voice command capture skipped")
        return ""
    try:
        text = _transcribe_path(path).strip()
        logger.info("Voice STT: %s", text[:120])
        return text
    except Exception as exc:
        logger.error("Voice STT failed: %s", exc)
        return ""
    finally:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


def post_speech_intent(*, wake: str, transcript: str) -> dict[str, Any]:
    import urllib.error
    import urllib.request

    payload = {
        "wake": wake,
        "transcript": transcript,
        "timestamp": datetime.now(UTC).isoformat(),
        "source": "speech-mcp",
    }
    url = router_url()
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {"success": True}
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        try:
            return json.loads(err_body)
        except json.JSONDecodeError:
            return {"success": False, "error": err_body or str(exc)}
    except Exception as exc:
        logger.error("Voice intent POST failed: %s", exc)
        return {"success": False, "error": str(exc)}
