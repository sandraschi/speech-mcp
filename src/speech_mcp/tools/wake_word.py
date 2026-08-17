"""
Wake word detection using openWakeWord + PyAudio.

The listener runs as a daemon thread so it doesn't block the MCP event loop.
One listener can be active at a time (singleton pattern). On detection the
callback fires a log entry and optionally calls a user-supplied coroutine.

Built-in models available (auto-downloaded on first use):
  alexa, hey_jarvis, hey_mycroft, hey_rhasspy, timers, weather

Requires:
  - openwakeword installed (uv add openwakeword)
  - onnxruntime installed (uv add onnxruntime)
  - pyaudio installed (uv add pyaudio)
"""

import asyncio
import logging
import struct
import threading
from collections.abc import Callable
from typing import Annotated

import numpy as np
import openwakeword
from fastmcp import Context, FastMCP
from openwakeword.model import Model
from pydantic import Field

logger = logging.getLogger(__name__)

# ── Singleton listener state ───────────────────────────────────────────────────

_listener_thread: threading.Thread | None = None
_stop_event: threading.Event = threading.Event()
_listener_lock = threading.Lock()


def _run_listener(
    keyword: str,
    sensitivity: float,
    on_detection: Callable[[str], None],
) -> None:
    """
    Blocking mic capture + openWakeWord processing loop.
    Runs in a daemon thread. Stops when _stop_event is set.
    """
    import pyaudio

    oww_model = None
    pa = None
    stream = None

    try:
        # Pre-download models if missing
        openwakeword.utils.download_models(models=[keyword])  # type: ignore[attr-defined]

        # Initialize openWakeWord Model
        # vad_threshold=0.5 helps filter out non-speech noise
        oww_model = Model(wakeword_models=[keyword], vad_threshold=0.5, inference_framework="onnx")

        CHUNK = 1280  # 80ms at 16kHz
        pa = pyaudio.PyAudio()
        stream = pa.open(
            rate=16000,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=CHUNK,
        )

        logger.info(
            "Wake word listener started (openWakeWord): keyword='%s' sensitivity=%.2f",
            keyword,
            sensitivity,
        )

        while not _stop_event.is_set():
            pcm_bytes = stream.read(CHUNK, exception_on_overflow=False)
            # Unpack bytes to int16 samples as a numpy array (predict expects ndarray)
            pcm = np.asarray(struct.unpack(f"{CHUNK}h", pcm_bytes), dtype=np.int16)

            # Get predictions
            scores: dict[str, float] = oww_model.predict(pcm)  # type: ignore[arg-type, assignment]

            # Check if any model score exceeds the sensitivity (threshold)
            for name, score in scores.items():
                if score >= sensitivity:
                    logger.info("Wake word detected: '%s' (score: %.4f)", name, score)
                    on_detection(name)
                    oww_model.reset()  # Reset buffer to prevent immediate double-trigger

    except Exception as e:
        logger.error("Wake word listener error: %s", e)
    finally:
        if stream is not None:
            stream.stop_stream()
            stream.close()
        if pa is not None:
            pa.terminate()
        logger.info("Wake word listener stopped.")


def register_wake_word_tools(mcp: FastMCP) -> None:

    @mcp.tool()
    async def configure_local_wake_word(
        ctx: Context,
        keyword: Annotated[
            str, Field(description="Wake word model: alexa, hey_jarvis, hey_mycroft, hey_rhasspy, timers, weather")
        ] = "hey_jarvis",
        sensitivity: Annotated[float, Field(description="Detection threshold 0.0-1.0.", ge=0.0, le=1.0)] = 0.5,
        action: Annotated[str, Field(description="Operation: start, stop, or status")] = "start",
    ) -> dict:
        """
        Start or stop a local wake-word listener using openWakeWord (offline).

        When a wake word is detected, a log entry is written and a notification
        is sent via ctx.info. The listener runs as a background daemon thread.

        Built-in keyword options: 'alexa', 'hey_jarvis', 'hey_mycroft', 'hey_rhasspy', 'timers', 'weather'.

        ## Return Format
        {"success": bool, "status": str, "engine": str, "keyword"?: str, "listening"?: bool}

        ## Examples
        configure_local_wake_word(keyword="hey_jarvis", action="start")
        configure_local_wake_word(action="status")
        configure_local_wake_word(action="stop")
        """
        return await wake_word_configure(ctx=ctx, keyword=keyword, sensitivity=sensitivity, action=action)


async def wake_word_configure(
    ctx: Context | None = None,
    keyword: str = "hey_jarvis",
    sensitivity: float = 0.5,
    action: str = "start",
) -> dict:
    """Shared implementation used by the MCP tool and the REST bridge."""
    global _listener_thread, _stop_event

    # -- status ----------------------------------------------------------------
    from speech_mcp.voice_bus import fleet_voice_enabled
    from speech_mcp.voice_listener import fleet_listener_active, stop_fleet_listener

    if action == "status":
        running = (_listener_thread is not None and _listener_thread.is_alive()) or fleet_listener_active()
        return {
            "success": True,
            "listening": running,
            "engine": "openWakeWord",
            "fleet_delegate": fleet_voice_enabled(),
            "status": "active" if running else "stopped",
        }

    # -- stop ------------------------------------------------------------------
    if action == "stop":
        with _listener_lock:
            stopped = False
            if _listener_thread and _listener_thread.is_alive():
                _stop_event.set()
                _listener_thread.join(timeout=3.0)
                _listener_thread = None
                stopped = True
            if stop_fleet_listener():
                stopped = True
            if stopped:
                if ctx:
                    await ctx.info("Wake word listener stopped.")
                else:
                    logger.info("Wake word listener stopped.")
                return {"success": True, "status": "stopped"}
            return {"success": True, "status": "was_not_running"}

    # -- start -----------------------------------------------------------------
    if action != "start":
        return {"success": False, "error": f"Unknown action '{action}'. Use start/stop/status."}

    import os

    from speech_mcp.voice_bus import fleet_voice_enabled, router_url
    from speech_mcp.voice_listener import fleet_listener_active, start_fleet_listener, stop_fleet_listener

    fleet_mode = fleet_voice_enabled()
    wake_kw = os.environ.get("FLEET_VOICE_WAKE_KEYWORD", keyword).strip() or keyword

    with _listener_lock:
        if _listener_thread and _listener_thread.is_alive():
            _stop_event.set()
            _listener_thread.join(timeout=3.0)
        stop_fleet_listener()

        _stop_event = threading.Event()

        def _on_detection(kw: str) -> None:
            logger.info("[WAKE WORD] '%s' detected", kw)
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.call_soon_threadsafe(
                        lambda: asyncio.ensure_future(ctx.info(f"Wake word '{kw}' detected")) if ctx else None
                    )
            except RuntimeError:
                pass

        if fleet_mode:
            start_fleet_listener(wake_kw, sensitivity, _on_detection)
        else:
            _listener_thread = threading.Thread(
                target=_run_listener,
                args=(wake_kw, sensitivity, _on_detection),
                daemon=True,
                name=f"oww-{wake_kw}",
            )
            _listener_thread.start()

    note = (
        f"Fleet Voice Command Bus active -> {router_url()}"
        if fleet_mode
        else "Offline wake only (set FLEET_VOICE_DELEGATE=1 to route commands)."
    )
    if ctx:
        await ctx.info(f"Wake word listener started: '{wake_kw}' (threshold {sensitivity}). {note}")
    else:
        logger.info("Wake word listener started: '%s' (threshold %s). %s", wake_kw, sensitivity, note)

    return {
        "success": True,
        "status": "listening",
        "engine": "openWakeWord",
        "keyword": wake_kw,
        "threshold": sensitivity,
        "fleet_delegate": fleet_mode,
        "router_url": router_url() if fleet_mode else None,
        "note": note,
        "stop_with": "configure_local_wake_word action='stop'",
    }
