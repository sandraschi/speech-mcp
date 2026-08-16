"""Fleet Voice Command Bus — post STT intents to fleet-agent."""

from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
import wave
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_transcribe_path: Callable[[Path], str] | None = None
_speak_hook: Callable[[str], None] | None = None


def set_transcribe_path_hook(fn: Callable[[Path], str]) -> None:
    """Register STT from server startup (FunASR transcribe_file, etc.)."""
    global _transcribe_path
    _transcribe_path = fn


def set_speak_hook(fn: Callable[[str], None]) -> None:
    """Register a provider-aware TTS for spoken replies (optional).

    Without a hook, speak_reply() falls back to Windows SAPI5 (pyttsx3).
    """
    global _speak_hook
    _speak_hook = fn


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
    req = urllib.request.Request(  # noqa: S310  # env-controlled http:// router URL
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310
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


def speak_reply_enabled() -> bool:
    """Spoken confirmation of routed results; on by default when delegating.

    Set FLEET_VOICE_SPEAK_REPLY=0 to mute.
    """
    flag = os.environ.get("FLEET_VOICE_SPEAK_REPLY", "").strip().lower()
    return flag not in ("0", "false", "no", "off")


def wake_greeting() -> str:
    """Spoken greeting after the wake word, before command capture."""
    return os.environ.get("FLEET_VOICE_WAKE_GREETING", "Hello, mistress.").strip()


def sleep_keyword() -> str:
    """Second openWakeWord model that stops the listener (sleep word).

    Stock placeholder until a custom 'sleepsleep' ONNX is trained — any
    openWakeWord model name works (alexa, hey_jarvis, hey_mycroft, ...).
    """
    return os.environ.get("FLEET_VOICE_SLEEP_KEYWORD", "hey_mycroft").strip()


def is_stop_request(transcript: str) -> bool:
    """Detect a spoken stop request in the captured transcript."""
    text = (transcript or "").lower().replace(" ", "")
    return "sleepsleep" in text or "gotosleep" in text


def speak_sync(text: str) -> None:
    """Blocking TTS (SAPI5 fallback) — used by the listener thread so the
    greeting/stop confirmation finishes before mic capture resumes."""
    if not text.strip():
        return
    try:
        import pyttsx3

        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception as exc:
        logger.warning("Sync TTS failed: %s", exc)


def spoken_reply(result: dict[str, Any]) -> str:
    """Compose a short spoken line from a routed intent result."""
    msg = str(result.get("message") or "").strip()
    if result.get("success"):
        text = f"OK. {msg}" if msg else "Done."
    else:
        text = f"Sorry. {msg}" if msg else "Sorry, that failed."
    if len(text) > 300:
        text = f"{text[:297].rstrip()}..."
    return text


def speak_reply(text: str) -> None:
    """Speak the routed result aloud (best-effort, never blocks the listener)."""
    if not text.strip():
        return
    if _speak_hook is not None:
        try:
            _speak_hook(text)
            return
        except Exception as exc:
            logger.warning("Speak hook failed, falling back to SAPI5: %s", exc)

    def _tts() -> None:
        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
        except Exception as exc:
            logger.warning("TTS speak-back failed: %s", exc)

    threading.Thread(target=_tts, daemon=True, name="voice-speak").start()
