"""Subtitle revision: homophone / jukugo disambiguation via a local LLM.

For Japanese subtitle text (anime especially), ASR kanji choices are often
acoustically right but lexically wrong (koushou -> 交渉 vs 高尚 vs 公証). This
pass reads each subtitle line with surrounding context and flags/replaces
jukugo where the kanji does not fit, returning a change log a human can review.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from speech_mcp.providers.local import local_llm_provider

logger = logging.getLogger(__name__)

# FastMCP tool annotations (TOOL_DESIGN_STANDARDS §9) - dict format works with all 3.x.
_MUTATING = {"readonly": False}

_BLOCK_RE = re.compile(r"^(\d+)\s*\n(\d{1,2}:\d{2}:\d{2},\d{3}) --> (\d{1,2}:\d{2}:\d{2},\d{3})\s*(.*)$", re.M)


def parse_srt(srt_text: str) -> list[dict]:
    """Parse SRT into [{index, start, end, text}] (text may be multi-line)."""
    blocks: list[dict] = []
    current: dict | None = None
    for line in srt_text.splitlines():
        line = line.rstrip()
        if not line.strip():
            if current is not None and current["text"].strip():
                blocks.append(current)
            current = None
            continue
        if current is None:
            m = re.match(r"^(\d+)\s*$", line.strip())
            if m:
                current = {"index": int(m.group(1)), "start": "", "end": "", "text": ""}
                continue
            continue
        if not current["start"] and "-->" in line:
            parts = re.split(r"\s*-->\s*", line)
            current["start"] = parts[0].strip()
            current["end"] = parts[1].split()[0].strip() if len(parts) > 1 else ""
            continue
        current["text"] += ("\n" if current["text"] else "") + line
    if current is not None and current["text"].strip():
        blocks.append(current)
    return blocks


def build_srt(blocks: list[dict]) -> str:
    out: list[str] = []
    for i, b in enumerate(blocks, 1):
        out.append(str(i))
        out.append(f"{b['start']} --> {b['end']}")
        out.append(b["text"].strip())
        out.append("")
    return "\n".join(out)


_SYSTEM_PROMPT = """\
You are a meticulous Japanese subtitle editor. A speech-to-text engine produced
these subtitle lines, and it often picks the WRONG kanji for a reading
(homophone / jukugo error). Example: the reading "koushou" could be 交渉
(negotiation), 高尚 (noble), 公証 (notarization), 鉱床 (mineral deposit);
only context decides. Anime subtitles are especially full of this because of
character names and casual speech.

You receive subtitle blocks as JSON:
[{"index":1,"start":"...","end":"...","text":"..."}, ...]
Surrounding lines are the context. A series title / glossary may be given.

Your job: for EVERY subtitle line, examine each two-kanji compound whose reading
shares kanji options. Judge the current kanji against the context:
- If it is clearly wrong, set "revised" to the correct kanji, confidence >= 0.8.
- If it is ambiguous (multiple plausible kanji) or the line has ASR noise that
  hints at a homophone, output an entry with "review": true and "revised" equal
  to "original" so a human checks it.
- Never change timestamps, indices, or kana readings. Keep the reading intact.

Output STRICT JSON only (parseable by json.loads), no markdown, no prose:
{"changes":[{"index":1,"original":"安堵","revised":"安藤","reading":"ando","reason":"person's name, not 'relief'","confidence":0.85,"review":false}]}
If no line has any homophone candidate, output {"changes":[]}.
"""


async def _pick_model(base_url: str) -> str | None:
    """Return the configured revision model, falling back to an installed one."""
    from speech_mcp.revision_config import OLLAMA_BASE_URL, REVISE_LLM_MODEL

    base = OLLAMA_BASE_URL
    try:
        models = await local_llm_provider.list_models("ollama", base)
    except Exception as e:
        logger.warning("Ollama unreachable at %s: %s", base, e)
        return None
    if not models:
        return None
    if REVISE_LLM_MODEL in models:
        return REVISE_LLM_MODEL
    for name in models:
        if "gemma" in name or "deepseek" in name or "qwen" in name:
            return name
    return models[0]


async def _revise_batch(
    blocks: list[dict],
    base_url: str,
    model: str,
    series: str = "",
    glossary: str = "",
) -> list[dict]:
    # Cap per-line text: very long ASR blocks make small local models generate
    # (or loop) indefinitely. 200 chars is plenty for jukugo spotting.
    bounded = [dict(b, text=(b.get("text") or "")[:200]) for b in blocks]
    payload = {
        "series": series,
        "glossary": glossary,
        "blocks": bounded,
    }
    system = _SYSTEM_PROMPT
    user = json.dumps(payload, ensure_ascii=False)
    for attempt in range(2):
        # Stream with a hard token cap: any batch is bounded even if the model
        # loops on pathological input. Do NOT pass ollama `options` - gemma4:12b
        # returns empty responses when num_predict/temperature are supplied.
        raw = await local_llm_provider.generate_stream_capped(
            "ollama", base_url, model, user, system, max_tokens=2000, timeout=300.0
        )
        raw = raw.strip()
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.M).strip()
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            logger.warning("Revision LLM returned non-JSON (attempt %s): %.200s", attempt + 1, raw)
            continue
        try:
            data = json.loads(raw[start : end + 1])
        except json.JSONDecodeError as e:
            logger.warning("Revision LLM JSON parse failed (attempt %s): %s", attempt + 1, e)
            continue
        changes = data.get("changes", []) or []
        if changes or attempt == 1:
            return changes
        logger.warning("Revision LLM returned empty changes (attempt %s); retrying", attempt + 1)
    return []


async def revise_srt(srt_text: str, *, series: str = "", glossary: str = "", language: str = "ja") -> dict:
    """Core revision: parse SRT, run the LLM pass per batch, apply confident fixes.

    Returns {success, revised_srt, changes (all flagged incl. review-only),
    applied_count, flagged_count, model, language}.
    """
    from speech_mcp.revision_config import OLLAMA_BASE_URL, REVISE_BATCH

    base_url = OLLAMA_BASE_URL
    model = await _pick_model(base_url)
    if not model:
        return {
            "success": False,
            "error": "No local LLM reachable for revision (Ollama on :11434). Start Ollama or set OLLAMA_BASE_URL.",
            "revised_srt": srt_text,
            "changes": [],
            "applied_count": 0,
            "flagged_count": 0,
        }

    blocks = parse_srt(srt_text)
    if not blocks:
        return {
            "success": False,
            "error": "Could not parse SRT text",
            "revised_srt": srt_text,
            "changes": [],
            "applied_count": 0,
            "flagged_count": 0,
        }

    all_changes: list[dict] = []
    batch_size = max(5, min(REVISE_BATCH, 60))
    for i in range(0, len(blocks), batch_size):
        batch = blocks[i : i + batch_size]
        all_changes.extend(await _revise_batch(batch, base_url, model, series, glossary))

    # Apply confident, non-identical fixes. Keep everything in the change log.
    by_index: dict[int, str] = {}
    for c in all_changes:
        try:
            idx = int(c["index"])
        except (KeyError, TypeError, ValueError):
            continue
        revised = (c.get("revised") or "").strip()
        original = (c.get("original") or "").strip()
        confidence = float(c.get("confidence") or 0.0)
        if revised and revised != original and confidence >= 0.8:
            by_index[idx] = revised

    revised_blocks = []
    for b in blocks:
        nb = dict(b)
        if b["index"] in by_index:
            nb["text"] = by_index[b["index"]]
        revised_blocks.append(nb)
    revised_srt = build_srt(revised_blocks)

    applied_indexes = set(by_index.keys())
    for c in all_changes:
        try:
            c["applied"] = int(c.get("index", -1)) in applied_indexes
        except (KeyError, TypeError, ValueError):
            c["applied"] = False

    return {
        "success": True,
        "revised_srt": revised_srt,
        "changes": all_changes,
        "applied_count": len(applied_indexes),
        "flagged_count": len(all_changes),
        "language": language,
        "model": model,
    }


def register_revise_tools(mcp: FastMCP) -> None:
    @mcp.tool(annotations=_MUTATING)
    async def revise_subtitles(
        srt_text: Annotated[str, Field(description="SRT subtitle text to revise.")],
        language: Annotated[str, Field(description="Language of the transcript (default ja).")] = "ja",
        series: Annotated[str, Field(description="Series/show name for context (helps disambiguation).")] = "",
        glossary: Annotated[
            str,
            Field(description="Optional glossary of character/term names, one per line."),
        ] = "",
        ctx=None,
    ) -> dict:
        """
        Revise an SRT transcript, fixing homophone/jukugo kanji via a local LLM.

        The ASR often picks the acoustically correct but lexically wrong kanji
        for a reading (koushou = 交渉/高尚/公証). This pass reads each line with
        surrounding context and flags/replaces wrong compounds. For Japanese
        anime subtitles the output still needs a human review pass.

        ## Return Format
        {"success": bool, "revised_srt": str, "changes": [{index, original, revised, reading, reason, confidence, review, applied}], "applied_count": int, "flagged_count": int, "language": str}

        ## Examples
        revise_subtitles(srt_text=raw_srt, language="ja", series="Urusei Yatsura")
        """
        return await revise_srt(srt_text, series=series, glossary=glossary, language=language)
