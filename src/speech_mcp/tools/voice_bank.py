"""Voice bank - registered voice profiles across providers."""

from __future__ import annotations

import logging
from typing import Annotated, Literal

from fastmcp import FastMCP
from pydantic import Field

from speech_mcp.storage import voice_profile_delete, voice_profile_get, voice_profile_list, voice_profile_register

logger = logging.getLogger(__name__)

# FastMCP tool annotations (TOOL_DESIGN_STANDARDS §9) - dict format works with all 3.x.
_README_ONLY = {"readonly": True}
_MUTATING = {"readonly": False}


def register_voice_bank_tools(mcp: FastMCP) -> None:
    """Register voice bank tools."""

    @mcp.tool(annotations=_MUTATING)
    async def manage_voice_bank(
        operation: Annotated[
            Literal["list", "register", "remove"],
            Field(description="list profiles, register a new profile, or remove one."),
        ],
        name: Annotated[str, Field(description="Profile name (used as voice_id alias in text_to_speech).")] = "",
        provider: Annotated[
            str, Field(description="Synthesis provider: elevenlabs, gemini, hume, gemma, windows.")
        ] = "elevenlabs",
        voice_id: Annotated[str, Field(description="Provider-specific voice id.")] = "",
        source: Annotated[str, Field(description="Origin: elevenlabs, cosyvoice, gpt-sovits, custom.")] = "custom",
        description: Annotated[str, Field(description="Human-readable description.")] = "",
    ) -> dict:
        """Manage the voice bank: named profiles routed to a provider + voice.

        A registered profile can be used directly in ``text_to_speech`` by
        passing its ``name`` as ``voice_id`` - the server resolves provider +
        voice. ``source="cosyvoice"``/``"gpt-sovits"`` reserves the profile for
        local cloning; cloning itself needs the optional model install
        (``uv sync --extra cosyvoice``) and is not silently faked.

        ## Return Format
        ``{"success": bool, "operation": str, ...}`` - ``list`` returns
        ``profiles``; ``register`` returns the profile; ``remove`` returns
        ``removed``.

        ## Examples
        ``manage_voice_bank(operation="register", name="benny",
        provider="elevenlabs", voice_id="ABC123")`` -> profile ready for
        ``text_to_speech(text="Hi", voice_id="benny")``.
        """
        if operation == "list":
            return {"success": True, "operation": operation, "profiles": voice_profile_list()}

        if operation == "register":
            if not name.strip():
                return {"success": False, "operation": operation, "error": "name is required"}
            res = voice_profile_register(name.strip(), provider, voice_id, source, description)
            if "error" in res:
                return {"success": False, "operation": operation, "error": res["error"]}
            return {"success": True, "operation": operation, **res}

        if operation == "remove":
            removed = voice_profile_delete(name.strip()) if name.strip() else False
            return {"success": True, "operation": operation, "name": name, "removed": removed}

        return {"success": False, "operation": operation, "error": f"unknown operation '{operation}'"}

    @mcp.tool(annotations=_README_ONLY)
    async def voice_bank_resolve(
        name: Annotated[str, Field(description="Profile name to resolve.")],
    ) -> dict:
        """Resolve a voice bank profile to its provider + voice_id.

        ## Return Format
        ``{"success": bool, "profile": {name, provider, voice_id, source}}``

        ## Examples
        ``voice_bank_resolve(name="benny")`` -> provider + voice id.
        """
        profile = voice_profile_get(name.strip()) if name.strip() else None
        if profile is None:
            return {"success": False, "error": f"no voice profile named '{name}'"}
        return {"success": True, "profile": profile}
