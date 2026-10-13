"""Studio workflows: dubbing + audiobooks composed from existing gateway parts.

No new engines, no new dependencies. FunASR timed segments (+ diarization) +
local-LLM translation + files-mode TTS + ffmpeg assembly. Both tools run as
background tasks (they can take many minutes on long inputs).

Honest limits (not stubs, just scope):
- Voiceover-style dub with timed placement + atempo fit, NOT lip-sync. Word-level
  alignment like WhisperX wav2vec2 is a VoiceStudio-side feature; use the
  voicestudio provider voice or the VoiceStudio app when lip-sync matters.
- No vocal isolation (demucs not bundled). Dub from clean dialogue stems.
- Audiobooks accept .txt/.md only. PDF ingest needs pypdf (not a dependency);
  .pdf returns not_implemented with guidance instead of a silent failure.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import shutil
import tempfile
import wave
from typing import Annotated, Any

from fastmcp import Context, FastMCP
from pydantic import Field

from speech_mcp.storage import client_voice_get, voice_profile_get
from speech_mcp.tools.speech import synthesize_wav_bytes
from speech_mcp.tools.subtitles import FFMPEG_PATH, _audio_to_wav, _segments_to_srt
from speech_mcp.tools.translate import _llm_translate

logger = logging.getLogger(__name__)

# FastMCP tool annotations (TOOL_DESIGN_STANDARDS §9) - dict format works with all 3.x.
_MUTATING = {"readonly": False}

_MAX_ATEMPO = 2.0


def _wav_duration_s(path: str) -> float:
    """Duration of a WAV file in seconds (raises on unreadable input)."""
    with wave.open(path, "rb") as wf:
        return wf.getnframes() / float(wf.getframerate() or 1)


async def _run_ffmpeg(args: list[str], timeout_s: int = 1800) -> None:
    """Run ffmpeg, raising RuntimeError with the stderr tail on failure."""
    proc = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE
    )
    try:
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
    except TimeoutError:
        proc.kill()
        raise RuntimeError(f"ffmpeg timed out after {timeout_s}s") from None
    if proc.returncode != 0:
        tail = (stderr or b"").decode("utf-8", errors="replace")[-800:]
        raise RuntimeError(f"ffmpeg failed (exit {proc.returncode}): {tail}")


def _resolve_tts(provider_default: str, voice_or_profile: str, client_id: str = "") -> tuple[str, str]:
    """Resolve (provider, voice) from bank alias -> client binding -> defaults."""
    provider = (provider_default or "gemini").strip().lower()
    voice = (voice_or_profile or "default").strip() or "default"
    try:
        if voice.lower() != "default":
            profile = voice_profile_get(voice)
            if profile:
                provider = str(profile.get("provider") or provider).lower()
                voice = str(profile.get("voice_id") or "default")
        elif client_id.strip():
            bind = client_voice_get(client_id.strip())
            if bind and bind.get("profile"):
                prof = bind["profile"]
                provider = str(prof.get("provider") or provider).lower()
                voice = str(prof.get("voice_id") or voice)
    except Exception as e:
        logger.warning("studio voice resolution failed: %s", e)
    return provider, voice


def _fit_atempo(tts_dur: float, slot_dur: float) -> tuple[float, bool]:
    """Playback rate so rendered speech fits its time slot. Returns (rate, clamped)."""
    if slot_dur <= 0 or tts_dur <= slot_dur:
        return 1.0, False
    rate = tts_dur / slot_dur
    if rate <= _MAX_ATEMPO:
        return round(rate, 3), False
    return _MAX_ATEMPO, True


def _split_sentences(text: str, max_chars: int) -> list[str]:
    """Split text into sentence-aware chunks of at most max_chars."""
    sentences = re.split(r"(?<=[.!?…\n])\s+", text.strip())
    chunks: list[str] = []
    current = ""
    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        if len(sent) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            for i in range(0, len(sent), max_chars):
                chunks.append(sent[i : i + max_chars])
            continue
        if len(current) + len(sent) + 1 > max_chars:
            chunks.append(current)
            current = sent
        else:
            current = f"{current} {sent}".strip() if current else sent
    if current:
        chunks.append(current)
    return chunks


def register_studio_tools(
    mcp: FastMCP,
    funasr_provider: Any | None,
    gemini_client: Any | None = None,
    voicestudio_client: Any | None = None,
) -> None:
    """Register studio workflow tools (dubbing + audiobooks)."""

    # NOTE: registered as a plain tool (not task=True -- that needs the
    # fastmcp[tasks]/docket extra, not installed here). Long inputs take minutes;
    # max_segments caps the run and progress streams via ctx.
    @mcp.tool(annotations=_MUTATING)
    async def dub_audio_track(
        source_path: Annotated[str, Field(description="Absolute path to a video or audio file to dub.")],
        target_language: Annotated[str, Field(description="Dub language, e.g. 'German', 'Japanese'.")] = "German",
        provider: Annotated[
            str, Field(description="TTS provider: gemini, qwen, kokoro, windows, voicestudio.")
        ] = "gemini",
        default_voice: Annotated[str, Field(description="Voice id or bank profile for unmapped speakers.")] = "default",
        voice_map: Annotated[
            dict[str, str] | None,
            Field(description="Speaker label -> voice id/bank profile, e.g. {'SPEAKER_00': 'morgan'}."),
        ] = None,
        client_id: Annotated[str, Field(description="Optional agent id for bound-voice fallback.")] = "",
        output_dir: Annotated[
            str, Field(description="Directory for dubbed.wav + translated.srt (created as needed).")
        ] = "",
        llm_provider: Annotated[str, Field(description="Translation LLM: ollama or lmstudio.")] = "ollama",
        llm_model: Annotated[str | None, Field(description="Translation model override.")] = None,
        llm_base_url: Annotated[str | None, Field(description="Translation base URL override.")] = None,
        max_segments: Annotated[int, Field(description="Safety cap on segments per run.")] = 120,
        ctx: Context | None = None,
    ) -> dict:
        """
        Dub a video/audio file: extract dialogue, transcribe with timestamps + speakers,
        translate per segment, re-synthesize each line, and place it back on the timeline.

        Voiceover-style dub (timed placement with atempo fit), not lip-sync. Needs FunASR
        (timed segments + diarization) and a reachable local LLM for translation.

        ## Return Format
        {"success": bool, "dubbed_wav": str, "translated_srt": str, "segment_count": int,
        "rendered_count": int, "skipped": [...], "clamped": [...], "voices_used": [...]}

        ## Examples
        `dub_audio_track(source_path="D:/video/ep01.mkv", target_language="German")` -> dubbed track.
        """
        if not source_path or not os.path.isfile(source_path):
            return {"success": False, "error": f"source file not found: {source_path}"}
        if not funasr_provider:
            return {"success": False, "error": "FunASR not configured - dubbing needs timed segments + diarization"}

        base_dir = (output_dir or "").strip()
        if not base_dir:
            base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "studio")
        try:
            os.makedirs(base_dir, exist_ok=True)
        except Exception as e:
            return {"success": False, "error": f"cannot create output_dir: {e}"}

        tmpdir = tempfile.mkdtemp(prefix="speech-mcp-dub-")
        try:
            if ctx:
                await ctx.info("Dub step 1/4: extracting + transcribing dialogue")
            wav_path = os.path.join(tmpdir, "source.wav")
            await _audio_to_wav(source_path, wav_path)
            tresult = await funasr_provider.transcribe_file(wav_path, language="auto")
            if not tresult.get("success"):
                return {"success": False, "error": f"transcription failed: {tresult.get('error')}"}
            segments = [s for s in (tresult.get("segments") or []) if str(s.get("text") or "").strip()]
            if not segments or any("start_s" not in s or "end_s" not in s for s in segments):
                return {
                    "success": False,
                    "error": "no timed segments returned (dubbing needs FunASR segment timestamps)",
                }
            if len(segments) > max_segments:
                return {
                    "success": False,
                    "error": f"{len(segments)} segments exceed max_segments={max_segments} - split the input",
                }

            if ctx:
                await ctx.info(f"Dub step 2/4: translating {len(segments)} segments to {target_language}")
            lines: list[dict] = []
            for i, seg in enumerate(segments):
                src = str(seg["text"]).strip()
                try:
                    out = await _llm_translate(src, target_language, llm_provider, llm_model, llm_base_url)
                    if out.startswith("Generation failed"):
                        lines.append({"text": src, "translated": False, "warning": out[:120]})
                    else:
                        lines.append({"text": out.strip(), "translated": True})
                except Exception as e:
                    lines.append({"text": src, "translated": False, "warning": str(e)[:120]})
                if ctx and (i + 1) % 20 == 0:
                    await ctx.info(f"Translated {i + 1}/{len(segments)}")

            if ctx:
                await ctx.info(f"Dub step 3/4: synthesizing {len(segments)} lines")
            voice_map = voice_map or {}
            rendered: list[dict] = []
            skipped: list[dict] = []
            voices_used: set[str] = set()
            for i, (seg, line) in enumerate(zip(segments, lines, strict=True)):
                speaker = str(seg.get("speaker") or "SPEAKER_00")
                prov, voice = _resolve_tts(provider, voice_map.get(speaker, default_voice), client_id)
                voices_used.add(f"{prov}/{voice}")
                try:
                    data = await synthesize_wav_bytes(
                        line["text"], prov, voice, gemini_client=gemini_client, voicestudio_client=voicestudio_client
                    )
                except Exception as e:
                    skipped.append({"index": i, "speaker": speaker, "error": str(e)[:160]})
                    continue
                seg_path = os.path.join(tmpdir, f"seg_{i:04d}.wav")
                with open(seg_path, "wb") as f:
                    f.write(data)
                rendered.append({"index": i, "seg": seg, "path": seg_path, "prov": prov, "voice": voice})
                if ctx and (i + 1) % 20 == 0:
                    await ctx.info(f"Synthesized {i + 1}/{len(segments)}")

            if not rendered:
                return {"success": False, "error": "no segments rendered", "skipped": skipped}
            if ctx:
                await ctx.info(f"Dub step 4/4: assembling {len(rendered)} lines on the timeline")

            total_dur = max(float(s["seg"]["end_s"]) for s in rendered) + 1.0
            inputs: list[str] = []
            filters: list[str] = []
            labels: list[str] = []
            clamped: list[dict] = []
            for n, r in enumerate(rendered):
                start = float(r["seg"]["start_s"])
                slot = max(0.3, float(r["seg"]["end_s"]) - start)
                tts_dur = _wav_duration_s(r["path"])
                rate, was_clamped = _fit_atempo(tts_dur, slot)
                if was_clamped:
                    clamped.append({"index": r["index"], "tts_s": round(tts_dur, 2), "slot_s": round(slot, 2)})
                chain = f"[{n}:a]aformat=sample_fmts=s16:sample_rates=16000:channel_layouts=mono,aresample=16000"
                if rate != 1.0:
                    chain += f",atempo={rate}"
                if was_clamped:
                    chain += f",atrim=0:{slot:.3f}"
                chain += f",adelay={int(start * 1000)}|{int(start * 1000)}[a{n}]"
                filters.append(chain)
                labels.append(f"[a{n}]")
                inputs += ["-i", r["path"]]
            filters.append(f"{''.join(labels)}amix=inputs={len(rendered)}:normalize=0[mix]")
            filters.append(f"[mix]atrim=0:{total_dur:.3f}[aout]")
            dubbed_wav = os.path.join(base_dir, "dubbed.wav")
            await _run_ffmpeg(
                [
                    FFMPEG_PATH,
                    "-y",
                    *inputs,
                    "-filter_complex",
                    ";".join(filters),
                    "-map",
                    "[aout]",
                    "-ar",
                    "16000",
                    "-ac",
                    "1",
                    "-c:a",
                    "pcm_s16le",
                    dubbed_wav,
                ]
            )

            srt_segs = [
                {"start_s": float(s["start_s"]), "end_s": float(s["end_s"]), "text": ln["text"]}
                for s, ln in zip(segments, lines, strict=True)
            ]
            translated_srt = os.path.join(base_dir, "translated.srt")
            with open(translated_srt, "w", encoding="utf-8") as f:
                f.write(_segments_to_srt(srt_segs))

            return {
                "success": True,
                "dubbed_wav": dubbed_wav,
                "translated_srt": translated_srt,
                "segment_count": len(segments),
                "rendered_count": len(rendered),
                "skipped": skipped,
                "clamped": clamped,
                "voices_used": sorted(voices_used),
                "total_duration_s": round(total_dur, 1),
                "note": "Voiceover-style dub with timed placement (atempo fit); not lip-sync. No vocal isolation applied.",
            }
        except Exception as e:
            logger.exception("dub_audio_track failed")
            return {"success": False, "error": str(e)}
        finally:
            await asyncio.to_thread(shutil.rmtree, tmpdir, ignore_errors=True)

    @mcp.tool(annotations=_MUTATING)
    async def make_audiobook(
        text_path: Annotated[str, Field(description="Absolute path to a .txt or .md file to narrate.")],
        provider: Annotated[
            str, Field(description="TTS provider: gemini, qwen, kokoro, windows, voicestudio.")
        ] = "gemini",
        voice_id: Annotated[str, Field(description="Voice id or voice-bank profile name.")] = "default",
        client_id: Annotated[str, Field(description="Optional agent id for bound-voice fallback.")] = "",
        output_dir: Annotated[str, Field(description="Directory for audiobook.wav + chapters.json.")] = "",
        title: Annotated[str, Field(description="Title used for output file names.")] = "audiobook",
        max_chars_per_chunk: Annotated[int, Field(description="Max characters per synthesis chunk.")] = 1500,
        max_chunks: Annotated[int, Field(description="Safety cap on chunks per run.")] = 60,
        ctx: Context | None = None,
    ) -> dict:
        """
        Narrate a text/markdown file: sentence-aware chunking, per-chunk synthesis,
        ffmpeg assembly into one WAV plus a chapters file with start offsets.

        ## Return Format
        {"success": bool, "audiobook_wav": str, "chapters_json": str, "chunk_count": int,
        "total_duration_s": float, "chapters": [{index, start_s, chars}]}

        ## Examples
        `make_audiobook(text_path="D:/books/chapter01.md", voice_id="morgan")` -> narrated WAV.
        """
        if not text_path or not os.path.isfile(text_path):
            return {"success": False, "error": f"text file not found: {text_path}"}
        ext = os.path.splitext(text_path)[1].lower()
        if ext == ".pdf":
            return {
                "success": False,
                "error": "PDF ingest not bundled (pypdf) - export to .txt/.md or dub via the VoiceStudio sidecar",
                "error_type": "not_implemented",
            }
        if ext not in (".txt", ".md", ".markdown"):
            return {"success": False, "error": f"unsupported extension '{ext}' (use .txt or .md)"}

        prov, voice = _resolve_tts(provider, voice_id, client_id)

        base_dir = (output_dir or "").strip()
        if not base_dir:
            base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "studio")
        try:
            os.makedirs(base_dir, exist_ok=True)
        except Exception as e:
            return {"success": False, "error": f"cannot create output_dir: {e}"}
        safe_title = re.sub(r"[^A-Za-z0-9_-]+", "_", (title or "audiobook").strip()) or "audiobook"

        tmpdir = tempfile.mkdtemp(prefix="speech-mcp-book-")
        try:
            with open(text_path, encoding="utf-8", errors="replace") as f:
                raw = re.sub(r"\s+", " ", f.read()).strip()
            if not raw:
                return {"success": False, "error": "input file has no readable text"}
            chunks = _split_sentences(raw, max(500, max_chars_per_chunk))
            if len(chunks) > max_chunks:
                return {
                    "success": False,
                    "error": f"{len(chunks)} chunks exceed max_chunks={max_chunks} - split the input file",
                }

            chunk_paths: list[str] = []
            for i, chunk in enumerate(chunks):
                if ctx and (i % 10 == 0 or i + 1 == len(chunks)):
                    await ctx.info(f"Narrating chunk {i + 1}/{len(chunks)}")
                try:
                    data = await synthesize_wav_bytes(
                        chunk, prov, voice, gemini_client=gemini_client, voicestudio_client=voicestudio_client
                    )
                except Exception as e:
                    return {"success": False, "error": f"chunk {i} synthesis failed: {e}", "chunks_done": i}
                path = os.path.join(tmpdir, f"chunk_{i:04d}.wav")
                with open(path, "wb") as f:
                    f.write(data)
                chunk_paths.append(path)

            chapters = []
            cursor = 0.0
            for i, path in enumerate(chunk_paths):
                dur = _wav_duration_s(path)
                chapters.append({"index": i, "start_s": round(cursor, 2), "chars": len(chunks[i])})
                cursor += dur

            inputs: list[str] = []
            filters: list[str] = []
            for n in range(len(chunk_paths)):
                filters.append(
                    f"[{n}:a]aformat=sample_fmts=s16:sample_rates=16000:channel_layouts=mono,aresample=16000[a{n}]"
                )
                inputs += ["-i", chunk_paths[n]]
            filters.append(
                f"{''.join(f'[a{n}]' for n in range(len(chunk_paths)))}concat=n={len(chunk_paths)}:v=0:a=1[aout]"
            )
            audiobook_wav = os.path.join(base_dir, f"{safe_title}.wav")
            await _run_ffmpeg(
                [
                    FFMPEG_PATH,
                    "-y",
                    *inputs,
                    "-filter_complex",
                    ";".join(filters),
                    "-map",
                    "[aout]",
                    "-ar",
                    "16000",
                    "-ac",
                    "1",
                    "-c:a",
                    "pcm_s16le",
                    audiobook_wav,
                ]
            )

            chapters_json = os.path.join(base_dir, f"{safe_title}.chapters.json")
            with open(chapters_json, "w", encoding="utf-8") as f:
                json.dump({"title": safe_title, "provider": prov, "voice": voice, "chapters": chapters}, f, indent=2)

            return {
                "success": True,
                "audiobook_wav": audiobook_wav,
                "chapters_json": chapters_json,
                "chunk_count": len(chunks),
                "total_duration_s": round(cursor, 1),
                "chapters": chapters,
            }
        except Exception as e:
            logger.exception("make_audiobook failed")
            return {"success": False, "error": str(e)}
        finally:
            await asyncio.to_thread(shutil.rmtree, tmpdir, ignore_errors=True)
