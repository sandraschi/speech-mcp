"""Voice bank - registered voice profiles across providers (incl. Gemini 3.8 studio)."""

from __future__ import annotations

import logging
import os
import time
from typing import Annotated, Literal

from fastmcp import FastMCP
from pydantic import Field

from speech_mcp.storage import (
    client_voice_bind,
    client_voice_list,
    client_voice_unbind,
    voice_profile_delete,
    voice_profile_get,
    voice_profile_list,
    voice_profile_register,
)

logger = logging.getLogger(__name__)

# FastMCP tool annotations (TOOL_DESIGN_STANDARDS §9) - dict format works with all 3.x.
_README_ONLY = {"readonly": True}
_MUTATING = {"readonly": False}

_MIN_REFERENCE_SECONDS = 5.0


def _reference_duration_note(path: str) -> dict:
    """Best-effort duration check for the replication reference sample.

    WAV is measured exactly; other containers are accepted on trust with
    seconds=None (the 30s requirement is then enforced by confirm_consent +
    the AI Studio upload, not by us guessing).
    """
    try:
        import wave

        with wave.open(path, "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate() or 1
            seconds = frames / float(rate)
        return {"seconds": round(seconds, 1), "too_short": seconds < _MIN_REFERENCE_SECONDS}
    except Exception:
        return {"seconds": None, "too_short": False}


def register_voice_bank_tools(mcp: FastMCP) -> None:
    """Register voice bank tools."""

    @mcp.tool(annotations=_MUTATING)
    async def manage_voice_bank(
        operation: Annotated[
            Literal["list", "register", "remove", "remix", "replicate", "bind_client", "unbind_client", "list_binds"],
            Field(
                description="list/register/remove/remix/replicate, or per-agent bind_client/unbind_client/list_binds."
            ),
        ],
        name: Annotated[str, Field(description="Profile name (used as voice_id alias in text_to_speech).")] = "",
        provider: Annotated[
            str, Field(description="Synthesis provider: elevenlabs, gemini, hume, gemma, windows, voicestudio.")
        ] = "elevenlabs",
        voice_id: Annotated[str, Field(description="Provider-specific voice id (gemini: saved 3.8 voice).")] = "",
        source: Annotated[
            str,
            Field(
                description="Origin: elevenlabs, gemini-studio, gemini-replication, cosyvoice, gpt-sovits, voicestudio, custom."
            ),
        ] = "custom",
        description: Annotated[str, Field(description="Human-readable description.")] = "",
        design_prompt: Annotated[
            str, Field(description="Gemini-only: NL voice-design prompt (role/accent/traits).")
        ] = "",
        language: Annotated[str, Field(description="Gemini-only: language/dialect for the designed voice.")] = "",
        gemini_model: Annotated[
            str, Field(description="Gemini-only: model for this voice (3.8 Flash / Flash-Lite).")
        ] = "",
        remix_prompt: Annotated[
            str, Field(description="remix-only: NL tweak, e.g. 'add subtle Southern US accent'.")
        ] = "",
        new_voice_id: Annotated[str, Field(description="remix-only: saved voice_id after remixing in AI Studio.")] = "",
        reference_audio_path: Annotated[
            str, Field(description="replicate-only: 30s clean single-speaker sample.")
        ] = "",
        consent_audio_path: Annotated[
            str, Field(description="replicate-only: verbal consent recording, same speaker.")
        ] = "",
        rights_statement: Annotated[
            str, Field(description="replicate-only: who owns this voice + why you may use it.")
        ] = "",
        confirm_consent: Annotated[
            bool, Field(description="replicate-only: must be True, explicit consent gate.")
        ] = False,
        client_id: Annotated[
            str, Field(description="bind_client/unbind_client-only: agent id, e.g. claude-code, cursor, pi.")
        ] = "",
    ) -> dict:
        """Manage the voice bank: named profiles routed to a provider + voice.

        A registered profile can be used directly in ``text_to_speech`` by
        passing its ``name`` as ``voice_id`` - the server resolves provider +
        voice. ``source="cosyvoice"``/``"gpt-sovits"`` reserves the profile for
        local cloning; cloning itself needs the optional model install
        (``uv sync --extra cosyvoice``) and is not silently faked.

        Gemini 3.8 studio flow: design the voice in AI Studio from
        ``design_prompt`` (see ``build_voice_design_prompt`` semantics),
        save it, then register the saved ``voice_id`` here with
        ``source="gemini-studio"``. ``remix`` tracks prompt tweaks against the
        same profile. ``replicate`` is consent-gated and registers
        ``status="pending_ai_studio"`` - completion happens in AI Studio,
        never silently in this tool. See docs/CLONING_GUARDRAILS.md.

        ## Return Format
        ``{"success": bool, "operation": str, ...}`` - ``list`` returns
        ``profiles``; ``register``/``remix``/``replicate`` return the profile;
        ``remove`` returns ``removed``.

        ## Examples
        ``manage_voice_bank(operation="register", name="benny",
        provider="elevenlabs", voice_id="ABC123")`` -> profile ready for
        ``text_to_speech(text="Hi", voice_id="benny")``.
        ``manage_voice_bank(operation="register", name="dragon",
        provider="gemini", voice_id="saved-voice-123", source="gemini-studio",
        design_prompt="fire-breathing dragon narrator")`` -> Gemini studio voice.
        ``manage_voice_bank(operation="remix", name="dragon",
        remix_prompt="soften the delivery")`` -> tracked remix intent.
        """
        if operation == "list":
            return {"success": True, "operation": operation, "profiles": voice_profile_list()}

        if operation == "register":
            if not name.strip():
                return {"success": False, "operation": operation, "error": "name is required"}
            meta: dict = {}
            if provider == "gemini":
                if design_prompt.strip():
                    meta["design_prompt"] = design_prompt.strip()
                if language.strip():
                    meta["language"] = language.strip()
                if gemini_model.strip():
                    meta["model"] = gemini_model.strip()
                if source == "custom":
                    source = "gemini-studio"
            res = voice_profile_register(name.strip(), provider, voice_id, source, description, meta or None)
            if "error" in res:
                return {"success": False, "operation": operation, "error": res["error"]}
            return {"success": True, "operation": operation, **res}

        if operation == "remove":
            removed = voice_profile_delete(name.strip()) if name.strip() else False
            return {"success": True, "operation": operation, "name": name, "removed": removed}

        if operation == "remix":
            if not name.strip():
                return {"success": False, "operation": operation, "error": "name is required"}
            if not remix_prompt.strip():
                return {"success": False, "operation": operation, "error": "remix_prompt is required"}
            profile = voice_profile_get(name.strip())
            if profile is None:
                return {"success": False, "operation": operation, "error": f"no voice profile named '{name}'"}
            if profile.get("provider") != "gemini":
                return {"success": False, "operation": operation, "error": "remix is Gemini-3.8-only"}
            meta = dict(profile.get("meta") or {})
            remixes = list(meta.get("remixes") or [])
            remixes.append(
                {"prompt": remix_prompt.strip(), "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "status": "tracked"}
            )
            meta["remixes"] = remixes
            if new_voice_id.strip():
                meta["remixed_voice_id"] = new_voice_id.strip()
                meta["remix_status"] = "remixed_in_ai_studio"
            else:
                meta["remix_status"] = (
                    "pending_ai_studio (Voice remixing rolls out as 'coming soon' - apply the prompt in AI Studio)"
                )
            # Re-register is blocked by UNIQUE(name); update via delete + register (keeps single-row contract).
            voice_profile_delete(name.strip())
            res = voice_profile_register(
                name.strip(),
                profile.get("provider", "gemini"),
                new_voice_id.strip() or profile.get("voice_id", ""),
                profile.get("source", "gemini-studio"),
                description or profile.get("description", ""),
                meta,
            )
            if "error" in res:
                return {"success": False, "operation": operation, "error": res["error"]}
            return {"success": True, "operation": operation, "remix": remix_prompt.strip(), **res}

        if operation == "replicate":
            if not name.strip():
                return {"success": False, "operation": operation, "error": "name is required"}
            if not reference_audio_path.strip() or not os.path.exists(reference_audio_path.strip()):
                return {
                    "success": False,
                    "operation": operation,
                    "error": "reference_audio_path is required and must exist (30s clean single-speaker sample)",
                }
            if not consent_audio_path.strip() or not os.path.exists(consent_audio_path.strip()):
                return {
                    "success": False,
                    "operation": operation,
                    "error": "consent_audio_path is required (verbal consent recording, same speaker)",
                    "recovery": "Record the voice owner consenting, save the file, and retry with its path.",
                }
            if not confirm_consent:
                return {
                    "success": False,
                    "operation": operation,
                    "error": "confirm_consent=True is required - no silent cloning",
                }
            if len(rights_statement.strip()) < 10:
                return {
                    "success": False,
                    "operation": operation,
                    "error": "rights_statement is required (who owns this voice + why you may use it)",
                }
            duration_note = _reference_duration_note(reference_audio_path.strip())
            if duration_note.get("too_short"):
                return {
                    "success": False,
                    "operation": operation,
                    "error": f"reference audio too short ({duration_note.get('seconds', 0):.1f}s) - minimum 5s, 30s recommended",
                }
            from speech_mcp.tools.safety import validate_speech_intent

            safety = await validate_speech_intent(f"{name} {description} {rights_statement}")
            if not safety.get("safe", True):
                logger.warning("[GUARDRAIL] replicate refused for '%s': %s", name, safety.get("reason"))
                return {
                    "success": False,
                    "operation": operation,
                    "error": f"refused by speech safety bastion: {safety.get('reason')}",
                }
            if voice_profile_get(name.strip()) is not None:
                return {"success": False, "operation": operation, "error": f"Voice profile '{name}' already exists"}
            meta = {
                "status": "pending_ai_studio",
                "reference_audio": reference_audio_path.strip(),
                "consent_audio": consent_audio_path.strip(),
                "rights_statement": rights_statement.strip(),
                "consent_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "watermark": "SynthID + C2PA on every Gemini-generated clip",
                "reference_seconds": duration_note.get("seconds"),
                "next": "Replicate the voice in Google AI Studio from the reference sample + consent recording, then register the saved voice_id via manage_voice_bank(operation='register', source='gemini-studio')",
            }
            res = voice_profile_register(name.strip(), "gemini", "", "gemini-replication", description, meta)
            if "error" in res:
                return {"success": False, "operation": operation, "error": res["error"]}
            return {"success": True, "operation": operation, "status": "pending_ai_studio", **res}

        if operation == "bind_client":
            if not client_id.strip():
                return {"success": False, "operation": operation, "error": "client_id is required"}
            if not name.strip():
                return {"success": False, "operation": operation, "error": "name is required"}
            res = client_voice_bind(client_id.strip(), name.strip())
            if "error" in res:
                return {"success": False, "operation": operation, "error": res["error"]}
            return {"success": True, "operation": operation, **res}

        if operation == "unbind_client":
            if not client_id.strip():
                return {"success": False, "operation": operation, "error": "client_id is required"}
            removed = client_voice_unbind(client_id.strip())
            return {"success": True, "operation": operation, "client_id": client_id.strip(), "removed": removed}

        if operation == "list_binds":
            binds = client_voice_list()
            resolved = []
            for b in binds:
                profile = voice_profile_get(b.get("profile_name", ""))
                resolved.append({**b, "profile": profile})
            return {"success": True, "operation": operation, "binds": resolved, "count": len(resolved)}

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
