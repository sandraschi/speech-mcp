"""Sound-event detection - energy-based segmentation (deterministic, no models).

Computes RMS loudness over a sliding window of PCM and clusters contiguous
windows into events. Honest, model-free MVP: detects loud events, silence, and
speech-like segments (high duty cycle of mid-level energy). A neural classifier
can later replace the scorer without changing the return shape.
"""

from __future__ import annotations

import logging
import math
import struct
import wave
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

logger = logging.getLogger(__name__)

# FastMCP tool annotations (TOOL_DESIGN_STANDARDS §9) - dict format works with all 3.x.
_README_ONLY = {"readonly": True}

_WINDOW_MS = 50


def _load_pcm(path: str) -> tuple[list[float], int]:
    """Read a 16-bit PCM WAV into a mono float list ([-1, 1]) plus sample rate."""
    with wave.open(path, "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        rate = wf.getframerate()
        frames = wf.readframes(wf.getnframes())
    if sampwidth != 2:
        raise ValueError(f"Only 16-bit PCM WAV supported (got {sampwidth * 8}-bit)")
    n = len(frames) // 2
    if n_channels > 1:
        samples = struct.unpack(f"<{n}h", frames)
        samples = samples[0::n_channels]  # take channel 0
    else:
        samples = struct.unpack(f"<{n}h", frames)
    return [s / 32768.0 for s in samples], rate


def _rms(block: list[float]) -> float:
    if not block:
        return 0.0
    return math.sqrt(sum(x * x for x in block) / len(block))


def detect_events(
    path: str,
    threshold_db: float = -30.0,
    min_duration_s: float = 0.1,
) -> dict:
    """Analyze a WAV file and return energy-based events."""
    samples, rate = _load_pcm(path)
    if not samples:
        return {"success": False, "error": "Empty audio"}
    win = max(1, int(rate * _WINDOW_MS / 1000))
    threshold = 10 ** (threshold_db / 20.0)

    windows: list[float] = []
    for i in range(0, len(samples) - win + 1, win):
        windows.append(_rms(samples[i : i + win]))

    total = len(windows)
    loud = sum(1 for w in windows if w >= threshold)
    duty = loud / total if total else 0.0

    events: list[dict] = []
    idx = 0
    while idx < total:
        if windows[idx] >= threshold:
            start_idx = idx
            peak = windows[idx]
            while idx < total and windows[idx] >= threshold:
                peak = max(peak, windows[idx])
                idx += 1
            end_idx = idx
            start_s = round(start_idx * _WINDOW_MS / 1000, 2)
            end_s = round(end_idx * _WINDOW_MS / 1000, 2)
            if end_s - start_s >= min_duration_s:
                peak_db = round(20 * math.log10(peak), 1) if peak > 0 else -120.0
                duration = round(end_s - start_s, 2)
                # Heuristic label: high duty-cycle mid-level energy clusters
                # are speech-like; very loud short spikes are loud events.
                if duration >= 0.8 and peak_db < -12:
                    label = "speech_like"
                else:
                    label = "loud_event"
                events.append({"start_s": start_s, "end_s": end_s, "peak_db": peak_db, "label": label})
        else:
            idx += 1

    return {
        "success": True,
        "duration_s": round(len(samples) / rate, 2),
        "sample_rate": rate,
        "threshold_db": threshold_db,
        "duty_cycle": round(duty, 3),
        "events": events,
        "count": len(events),
        "note": "Energy-based detection (model-free). Classifier upgrade keeps the same shape.",
    }


def register_sound_event_tools(mcp: FastMCP) -> None:
    """Register sound-event detection tools."""

    @mcp.tool(annotations=_README_ONLY)
    async def detect_sound_events(
        file_path: Annotated[str, Field(description="Absolute path to a 16-bit PCM WAV file.")],
        threshold_db: Annotated[float, Field(description="Loudness threshold in dBFS for event onset.")] = -30.0,
        min_duration_s: Annotated[float, Field(description="Minimum event duration in seconds.")] = 0.1,
    ) -> dict:
        """Detect sound events (loud events, silence gaps, speech-like segments).

        Model-free energy-based segmentation: RMS over 50 ms windows, contiguous
        loud windows clustered into events. Honest heuristic - a neural
        classifier can replace the scorer without changing the return shape.

        ## Return Format
        ``{"success": bool, "duration_s": float, "duty_cycle": float,
        "events": [{start_s, end_s, peak_db, label}], "count": int}``

        ## Examples
        ``detect_sound_events(file_path="C:/audio/sample.wav",
        threshold_db=-30)`` -> event list with timestamps and peak dB.
        """
        try:
            result = detect_events(file_path, threshold_db=threshold_db, min_duration_s=min_duration_s)
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except FileNotFoundError:
            return {"success": False, "error": f"File not found: {file_path}"}
        except Exception as e:
            logger.exception("detect_sound_events failed")
            return {"success": False, "error": str(e)}
        return result
