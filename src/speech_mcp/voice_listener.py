"""Unified wake-word + command capture loop for fleet delegation."""

from __future__ import annotations

import logging
import struct
import threading
import time
from collections.abc import Callable

import openwakeword
from openwakeword.model import Model

from speech_mcp.voice_bus import (
    command_seconds,
    fleet_voice_enabled,
    is_stop_request,
    pcm_to_wav_path,
    post_speech_intent,
    sleep_keyword,
    speak_reply,
    speak_reply_enabled,
    speak_sync,
    spoken_reply,
    transcribe_wav,
    wake_greeting,
)

logger = logging.getLogger(__name__)

_listener_thread: threading.Thread | None = None
_stop_event: threading.Event = threading.Event()
_listener_lock = threading.Lock()


def _run_fleet_listener(
    keyword: str,
    sensitivity: float,
    on_wake_notify: Callable[[str], None] | None,
) -> None:
    import pyaudio

    oww_model = None
    pa = None
    stream = None
    rate = 16000
    chunk = 1280
    cooldown = 2.0

    try:
        sleep_kw = sleep_keyword() or None
        models = [keyword]
        if sleep_kw and sleep_kw.lower() != keyword.lower():
            models.append(sleep_kw)
        for model in models:
            openwakeword.utils.download_models(models=[model])
        oww_model = Model(wakeword_models=models, vad_threshold=0.5, inference_framework="onnx")
        pa = pyaudio.PyAudio()
        stream = pa.open(
            rate=rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=chunk,
        )
        logger.info(
            "Fleet voice listener: wake='%s' sleep='%s' command=%.1fs delegate=%s",
            keyword,
            sleep_kw or "-",
            command_seconds(),
            fleet_voice_enabled(),
        )

        while not _stop_event.is_set():
            pcm_bytes = stream.read(chunk, exception_on_overflow=False)
            pcm = list(struct.unpack(f"{chunk}h", pcm_bytes))
            scores = oww_model.predict(pcm)
            for name, score in scores.items():
                if score < sensitivity:
                    continue
                oww_model.reset()
                if sleep_kw and name == sleep_kw:
                    logger.info("Sleep word detected: '%s' - stopping listener", name)
                    speak_sync("Going to sleep.")
                    _stop_event.set()
                    return
                logger.info("Wake detected: '%s' (%.4f)", name, score)
                if on_wake_notify:
                    on_wake_notify(name)

                greet = wake_greeting()
                if greet:
                    speak_sync(greet)

                if not fleet_voice_enabled():
                    time.sleep(cooldown)
                    break

                n_chunks = max(1, int(command_seconds() * rate / chunk))
                frames: list[bytes] = []
                for _ in range(n_chunks):
                    if _stop_event.is_set():
                        break
                    frames.append(stream.read(chunk, exception_on_overflow=False))
                wav_path = pcm_to_wav_path(frames, rate=rate)
                transcript = transcribe_wav(wav_path)
                if transcript:
                    if is_stop_request(transcript):
                        logger.info("Stop request in transcript; going to sleep")
                        speak_sync("Going to sleep.")
                        _stop_event.set()
                        return
                    result = post_speech_intent(wake=name, transcript=transcript)
                    logger.info("Fleet voice route: %s", result.get("message", result))
                    if speak_reply_enabled():
                        speak_reply(spoken_reply(result))
                else:
                    logger.warning("No transcript after wake; nothing delegated")
                time.sleep(cooldown)
                break

    except Exception as exc:
        logger.error("Fleet voice listener error: %s", exc)
    finally:
        if stream is not None:
            stream.stop_stream()
            stream.close()
        if pa is not None:
            pa.terminate()
        logger.info("Fleet voice listener stopped")


def start_fleet_listener(
    keyword: str,
    sensitivity: float,
    on_wake_notify: Callable[[str], None] | None = None,
) -> None:
    global _listener_thread, _stop_event
    with _listener_lock:
        if _listener_thread and _listener_thread.is_alive():
            _stop_event.set()
            _listener_thread.join(timeout=3.0)
        _stop_event = threading.Event()
        _listener_thread = threading.Thread(
            target=_run_fleet_listener,
            args=(keyword, sensitivity, on_wake_notify),
            daemon=True,
            name=f"fleet-voice-{keyword}",
        )
        _listener_thread.start()


def stop_fleet_listener() -> bool:
    global _listener_thread, _stop_event
    with _listener_lock:
        if _listener_thread and _listener_thread.is_alive():
            _stop_event.set()
            _listener_thread.join(timeout=3.0)
            _listener_thread = None
            return True
    return False


def fleet_listener_active() -> bool:
    return _listener_thread is not None and _listener_thread.is_alive()
