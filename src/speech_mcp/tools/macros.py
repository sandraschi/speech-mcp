"""Voice macros - bind spoken phrases to multi-step actions."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Annotated, Literal

from fastmcp import Context, FastMCP
from pydantic import Field

from speech_mcp.state import _timers, run_timer
from speech_mcp.storage import macro_create, macro_delete, macro_get, macro_list

logger = logging.getLogger(__name__)

# FastMCP tool annotations (TOOL_DESIGN_STANDARDS §9) - dict format works with all 3.x.
_MUTATING = {"readonly": False}


def _describe_actions(actions: list[dict]) -> str:
    return "; ".join(
        f"{a.get('type', '?')}({a.get('target') or a.get('label') or a.get('text', '')[:40]})" for a in actions
    )


async def _run_actions(
    actions: list[dict],
    speak,
    weather_report,
) -> dict:
    """Execute a macro's action list. Unknown actions are reported, never silently skipped."""
    results: list[dict] = []
    for a in actions:
        atype = a.get("type", "")
        try:
            if atype == "tts":
                text = a.get("text", "")
                if text:
                    res = await speak(text, a.get("provider", "windows"), a.get("voice_id", "default"))
                    results.append({"action": "tts", "ok": bool(res.get("success")), "detail": res})
                else:
                    results.append({"action": "tts", "ok": False, "detail": {"error": "empty text"}})
            elif atype == "timer":
                seconds = int(a.get("seconds", 60))
                label = a.get("label", "Timer")
                timer_id = f"macro_{label}_{datetime.now().timestamp()}"
                task = asyncio.create_task(run_timer(timer_id, seconds, label))
                _timers[timer_id] = task
                results.append({"action": "timer", "ok": True, "detail": {"timer_id": timer_id, "seconds": seconds}})
            elif atype == "weather":
                loc = a.get("target", "Vienna")
                res = await weather_report(loc)
                results.append({"action": "weather", "ok": bool(res.get("success", False)), "detail": res})
            elif atype == "memory":
                from speech_mcp.storage import memory_store

                ep = memory_store(a.get("text", ""), kind="note", topic=a.get("topic", ""))
                results.append({"action": "memory", "ok": True, "detail": {"episode_id": ep["id"]}})
            else:
                results.append(
                    {"action": atype or "?", "ok": False, "detail": {"error": f"unknown action type '{atype}'"}}
                )
        except Exception as e:
            logger.exception("macro action %s failed", atype)
            results.append({"action": atype or "?", "ok": False, "detail": {"error": str(e)}})
    return {"results": results, "ok_all": all(r["ok"] for r in results)}


def register_macro_tools(mcp: FastMCP, speak, weather_report) -> None:
    """Register voice macro tools. ``speak`` is the speak_text dispatcher."""

    @mcp.tool(annotations=_MUTATING)
    async def voice_macros(
        operation: Annotated[
            Literal["list", "create", "run", "delete"],
            Field(description="list existing macros, create, run by phrase, or delete."),
        ],
        phrase: Annotated[str, Field(description="Spoken trigger phrase (case-insensitive).")] = "",
        label: Annotated[str, Field(description="Human label for create.")] = "",
        actions: Annotated[
            list[dict] | None, Field(description="Action list for create: [{type: tts|timer|weather|memory, ...}].")
        ] = None,
        ctx: Context | None = None,
    ) -> dict:
        """Manage voice macros: spoken phrases bound to multi-step actions.

        ## Return Format
        ``{"success": bool, "operation": str, ...}`` - ``list`` returns
        ``macros``; ``create`` returns the stored macro; ``run`` returns per-
        action ``results`` + ``ok_all``; ``delete`` returns ``deleted``.

        ## Examples
        ``voice_macros(operation="create", phrase="morning",
        actions=[{"type": "weather", "target": "Vienna"}, {"type": "tts",
        "text": "Good morning"}])`` -> binds "morning" to those actions.
        ``voice_macros(operation="run", phrase="morning")`` -> executes them.
        """
        if operation == "list":
            return {"success": True, "operation": operation, "macros": macro_list()}

        if operation == "create":
            if not phrase.strip():
                return {"success": False, "operation": operation, "error": "phrase is required"}
            res = macro_create(phrase, label=label, actions=actions or [])
            if "error" in res:
                return {"success": False, "operation": operation, "error": res["error"]}
            if ctx:
                await ctx.info(f"Macro created: '{phrase}' -> {_describe_actions(actions or [])}")
            return {"success": True, "operation": operation, **res}

        if operation == "run":
            macro = macro_get(phrase)
            if macro is None:
                return {"success": False, "operation": operation, "error": f"no macro for phrase '{phrase}'"}
            if not macro.get("enabled", 1):
                return {"success": False, "operation": operation, "error": f"macro '{phrase}' is disabled"}
            if ctx:
                await ctx.info(f"Running macro '{phrase}'")
            outcome = await _run_actions(macro.get("actions", []), speak, weather_report)
            return {"success": outcome["ok_all"], "operation": operation, "phrase": phrase, **outcome}

        if operation == "delete":
            deleted = macro_delete(phrase)
            return {"success": True, "operation": operation, "phrase": phrase, "deleted": deleted}

        return {"success": False, "operation": operation, "error": f"unknown operation '{operation}'"}
