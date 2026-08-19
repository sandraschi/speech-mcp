"""Skill-first chat tool - skill preprompt + personality composition via local LLM."""

from __future__ import annotations

import logging
from typing import Annotated

from fastmcp import Context, FastMCP
from pydantic import Field

from speech_mcp.personas import persona_system
from speech_mcp.providers.local import local_llm_provider
from speech_mcp.skills import get_skill
from speech_mcp.storage import memory_store

logger = logging.getLogger(__name__)

# FastMCP tool annotations (TOOL_DESIGN_STANDARDS §9) - dict format works with all 3.x.
_MUTATING = {"readonly": False}


def compose_system(personality: str, skill: str | None) -> str:
    """Skill-first system prompt: skill content (if any) + persona framing."""
    parts: list[str] = []
    if skill:
        content = get_skill(skill)
        if content:
            parts.append(f"You have access to the '{skill}' skill. Use it:\n{content[:2000]}")
    persona = persona_system(personality)
    if persona:
        parts.append(persona)
    if not parts:
        parts.append("You are a helpful assistant for the speech-mcp gateway.")
    return "\n\n".join(parts)


def register_chat_tools(mcp: FastMCP) -> None:
    """Register the skill-first chat tool."""

    @mcp.tool(annotations=_MUTATING)
    async def chat_message(
        message: Annotated[str, Field(description="User message to the chat assistant.")],
        personality: Annotated[
            str, Field(description="Persona name (sherlock, zen, engineer, professor, custom).")
        ] = "custom",
        skill: Annotated[str | None, Field(description="Skill name to load as the system preprompt.")] = None,
        provider: Annotated[str, Field(description="Local LLM provider: ollama or lmstudio.")] = "ollama",
        model: Annotated[str | None, Field(description="Model override.")] = None,
        base_url: Annotated[str | None, Field(description="Provider base URL override.")] = None,
        remember: Annotated[bool, Field(description="Store the exchange in voice memory.")] = True,
        ctx: Context | None = None,
    ) -> dict:
        """Chat with a local LLM, composed skill-first + personality.

        Loads the skill content (if ``skill`` is given) as the base system
        prompt, appends the persona framing, then generates via the local LLM.

        ## Return Format
        ``{"success": bool, "reply": str, "personality": str, "skill": str}``

        ## Examples
        ``chat_message(message="Summarize FunASR setup",
        personality="engineer", skill="speech-expert")`` -> grounded reply.
        """
        if not message.strip():
            return {"success": False, "error": "message is required"}
        system = compose_system(personality, skill)
        base = base_url or ("http://localhost:11434" if provider == "ollama" else "http://localhost:1234")
        effective = model or ("llama3" if provider == "ollama" else "default")
        reply = await local_llm_provider.generate(
            provider=provider, base_url=base, model=effective, prompt=message.strip(), system=system
        )
        if reply.startswith("Generation failed"):
            return {"success": False, "error": reply}
        if remember:
            memory_store(message.strip(), kind="chat", topic=personality, provider=provider, meta={"role": "user"})
            memory_store(reply, kind="chat", topic=personality, provider=provider, meta={"role": "assistant"})
        if ctx:
            await ctx.info(f"Chat ({personality}) replied in {len(reply)} chars")
        return {"success": True, "reply": reply, "personality": personality, "skill": skill}
