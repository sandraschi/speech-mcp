# speech-mcp Integration Guide: OpenClaw and OpenFang

**Status**: Design / Partial Implementation  
**Date**: 2026-02-27

---

## Overview

Speech-mcp provides the voice layer for two larger systems in the fleet:

- **OpenClaw** — the messaging gateway (WhatsApp, Telegram, Discord, Slack). Speech-mcp gives OpenClaw a voice output channel and transcription input channel.
- **OpenFang** — the agentic mesh orchestrator. Speech-mcp gives OpenFang Council of Dozens debates an audible read-out, and gives the Resonite avatar embodiment a voice.

These integrations are independent and can be enabled selectively.

---

## Part 1: OpenClaw Integration

### What OpenClaw is

OpenClaw is the Claude-facing gateway that routes messages from chat platforms (WhatsApp, Telegram, Discord, Slack) into Claude sessions and back out. It runs on `OPENCLAW_GATEWAY_URL`, exposes a Tool Invoke API, and supports multi-channel routing.

### What speech-mcp adds

| Capability | Direction | How |
|---|---|---|
| Read incoming messages aloud | OpenClaw → speech-mcp | Call `text_to_speech` with message content |
| Voice reply confirmation | Claude → speech-mcp → OpenClaw | Synthesize and stream before sending text reply |
| Wake word detection | speech-mcp → OpenClaw | Trigger on wake word, route to active session |

### Wiring it up

OpenClaw can call speech-mcp tools directly via the MCP bridge if both are registered in Claude Desktop. Alternatively, speech-mcp's REST API can be called from an OpenClaw skill:

```python
# In an OpenClaw skill (Python)
import httpx

async def speak_message(text: str, provider: str = "windows"):
    """Synthesize a message via speech-mcp REST API."""
    async with httpx.AsyncClient() as client:
        # speech-mcp webapp must be running on port 10760
        resp = await client.get(
            "http://localhost:10760/api/v1/voices"
        )
        # Then trigger synthesis via the MCP tool (if via Claude session)
        # or via a direct WebSocket to ws://localhost:10760/ws/stream
        return resp.json()
```

The cleaner path is to call the `text_to_speech` MCP tool from within a Claude session that has both `speech-mcp` and `openclaw-molt-mcp` loaded. Claude can then orchestrate: receive a message via OpenClaw, synthesize it via speech-mcp, and send a reply back through OpenClaw.

### Practical use case: voice notifications

When an urgent WhatsApp message arrives while you're at the server, OpenClaw receives it and speech-mcp reads it aloud via Windows TTS (no API key needed). Setup:

1. Ensure speech-mcp webapp is running (`.\start.ps1` in `D:\Dev\repos\speech-mcp`)
2. In OpenClaw, configure a skill that calls `text_to_speech` for messages matching an urgency filter
3. Provider `"windows"` is zero-latency, zero-cost for notification use cases

---

## Part 2: OpenFang Integration

### What OpenFang is

OpenFang is the agentic orchestration platform at `D:\Dev\repos\openfang`. Its core feature is the **Council of Dozens** — multi-agent debate sessions where each council member is an LLM adjudicator (or a physical sensor, or a Resonite avatar) reasoning from a specific lens.

### What speech-mcp adds to OpenFang

| Capability | Use Case |
|---|---|
| Council debate read-out | Synthesize each adjudicator's contribution as it comes in |
| Session summaries | Read out the equilibrium synthesis at session end |
| Voice avatar in Resonite | speech-mcp provides the voice for Resonite-embodied council members |
| Wake word → council trigger | Say "Council, begin" to start a debate session |

### Council debate audio pipeline

OpenFang's `council_orchestrator.py` produces structured debate records. Speech-mcp can consume these via a bridge script:

```python
# scripts/council_tts_bridge.py (to be implemented)
# Runs alongside a council session, streams each round to speech-mcp

import asyncio
import httpx

async def speak_council_round(adjudicator: str, text: str):
    """Speak a council adjudicator's contribution."""
    # Choose voice per adjudicator for distinct audio identity
    voice_map = {
        "Architect": ("hume", "ito"),
        "Adversary": ("elevenlabs", "voice_id_adversarial"),
        "Synthesizer": ("windows", "default"),
    }
    provider, voice = voice_map.get(adjudicator, ("windows", "default"))
    
    # Call speech-mcp MCP tool via stdio client, or call REST API directly
    # REST path (webapp must be running):
    async with httpx.AsyncClient() as client:
        await client.get(
            f"http://localhost:10760/api/v1/voices"
            # Full audio trigger requires WebSocket stream consumer
        )
```

In the full implementation each adjudicator would have a distinct voice — Hume's expressive synthesis for the Synthesizer role, a more clipped ElevenLabs voice for the Adversary.

### RAG cross-pollination

OpenFang has its own RAG (`src/openfang/core/openfang_rag.py`) for its knowledge base. Speech-mcp's `search_docs` tool can be added as a bridge in OpenFang's bridge registry, making speech AI documentation available to council members reasoning about voice interface decisions:

```json
// In openfang/configs/bridge_registry.json (add entry)
{
  "speech-mcp": {
    "tools": ["search_docs", "ask_docs"],
    "scope": "read",
    "allowed_callers": ["council_research_synthesiser"],
    "description": "Speech AI knowledge base — TTS providers, prosody, turn-taking research"
  }
}
```

### OpenFang fleet registration

Speech-mcp should be registered in the OpenFang fleet:

```json
// Add to openfang/configs/federation_map.json
{
  "server_id": "speech-mcp",
  "name": "Speech MCP",
  "description": "Multi-provider TTS (Hume AI, ElevenLabs, Windows), RAG knowledge base for speech AI",
  "port": 10760,
  "webapp_port": 10761,
  "repo": "D:/Dev/repos/speech-mcp",
  "tags": ["speech", "tts", "voice", "rag", "hume", "elevenlabs"],
  "requires_env": ["HUME_API_KEY", "ELEVENLABS_API_KEY"],
  "optional_env": true
}
```

---

## Part 3: OpenFang + OpenClaw together

The full pipeline once all three are connected:

```
User (voice or text)
    │
    ├── Wake word detected → speech-mcp → trigger
    │
    ▼
OpenClaw gateway (routes to Claude session)
    │
    ▼
Claude + speech-mcp + OpenFang MCP tools loaded
    │
    ├── Claude invokes OpenFang council session
    ├── Council runs, produces synthesis
    ├── Claude calls text_to_speech on synthesis result
    └── Audio streams to speaker via ws://localhost:10760/ws/stream
```

This is a working design — no components need to be built from scratch, only wired.

---

## Current Status

| Integration | Status | Blocker |
|---|---|---|
| speech-mcp standalone | Working | — |
| OpenClaw → speech-mcp REST | Design only | Need OpenClaw skill implementation |
| OpenFang fleet registration | Not done | Add to federation_map.json |
| Council TTS bridge script | Not done | Needs council_tts_bridge.py |
| Bridge registry entry | Not done | Needs federation_map.json update |
| Resonite avatar voice | See RESONITE_AVATAR_VOICE.md | OSC + speech-mcp wiring needed |
