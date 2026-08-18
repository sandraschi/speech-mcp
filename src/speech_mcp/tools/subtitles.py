"""Plex cross-connect: fetch episode audio via plex-mcp, transcribe, build SRT."""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import tempfile

import httpx

logger = logging.getLogger(__name__)


def _find_ffmpeg() -> str:
    env = os.getenv("FFMPEG_PATH")
    if env and os.path.exists(env):
        return env
    for cand in ("C:\\ffmpeg\\ffmpeg.exe", "C:\\ffmpeg\\bin\\ffmpeg.exe"):
        if os.path.exists(cand):
            return cand
    which = shutil.which("ffmpeg")
    return which or "ffmpeg"


FFMPEG_PATH = _find_ffmpeg()


def _segments_to_srt(segments: list[dict]) -> str:
    def _ts(seconds: float) -> str:
        ms = round(seconds * 1000)
        h, rem = divmod(ms, 3600000)
        m, rem = divmod(rem, 60000)
        s, ms = divmod(rem, 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    blocks: list[str] = []
    for i, seg in enumerate(segments, 1):
        blocks.append(f"{i}\n{_ts(seg['start_s'])} --> {_ts(seg['end_s'])}\n{seg['text'].strip()}")
    return "\n\n".join(blocks) + "\n"


async def _fetch_stream_url(plex_mcp_url: str, media_key: str) -> dict:
    url = f"{plex_mcp_url.rstrip('/')}/api/media/{media_key}/stream-url"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
    if not data.get("success") or not (data.get("audio_url") or data.get("download_url")):
        raise RuntimeError(f"plex-mcp returned no stream URLs for {media_key}: {data}")
    return data


async def _audio_to_wav(source_url: str, out_wav: str, timeout_s: int = 1800) -> None:
    cmd = [
        FFMPEG_PATH,
        "-y",
        "-i",
        source_url,
        "-vn",
        "-sn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-f",
        "wav",
        out_wav,
    ]
    proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE)
    try:
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
    except TimeoutError:
        proc.kill()
        raise RuntimeError(f"ffmpeg timed out after {timeout_s}s extracting audio") from None
    if proc.returncode != 0:
        tail = (stderr or b"").decode("utf-8", errors="replace")[-800:]
        raise RuntimeError(f"ffmpeg failed (exit {proc.returncode}): {tail}")


async def fetch_audio_and_transcribe(
    *,
    plex_mcp_url: str,
    media_key: str,
    language: str,
    funasr,
) -> dict:
    """Get audio for a Plex item, transcribe with FunASR, return SRT + metadata."""
    stream = await _fetch_stream_url(plex_mcp_url, media_key)
    title = stream.get("title") or ""
    # Direct download of the original file is the reliable path; ffmpeg skips
    # video/subtitle tracks. The audio-only HLS transcode URL is a bonus when
    # Plex serves it correctly.
    source_url = stream.get("download_url") or stream.get("audio_url")
    source_kind = "download_url" if stream.get("download_url") else "audio_url"
    if not source_url:
        return {"success": False, "error": "plex-mcp returned no stream URL for this item"}

    tmpdir = tempfile.mkdtemp(prefix="speech-mcp-plex-")
    wav_path = os.path.join(tmpdir, "episode.wav")
    try:
        logger.info("Fetching audio for '%s' (%s) from %s", title, media_key, source_url[:90])
        await _audio_to_wav(source_url, wav_path)
        result = await funasr.transcribe_file(wav_path, language=language)
        if not result.get("success"):
            return {"success": False, "error": result.get("error", "transcription failed")}
        segments = result.get("segments", [])
        return {
            "success": True,
            "title": title,
            "text": result.get("text", ""),
            "segments": segments,
            "srt": _segments_to_srt(segments),
            "info": {
                "media_key": media_key,
                "title": title,
                "duration_s": stream.get("duration_s"),
                "segment_count": len(segments),
                "source": source_kind,
            },
        }
    except Exception as e:
        logger.exception("Plex audio fetch/transcribe failed")
        return {"success": False, "error": str(e)}
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
