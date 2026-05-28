# speech-mcp — Claude Code Guide

## Overview
Multi-provider speech gateway with Gemini, Hume AI, ElevenLabs TTS (Beta)

## Entry Points
- `uv run speech-mcp` → `speech_mcp.server:main`
- `uv run speech-mcp-webapp` → `speech_mcp.webapp:main`

## Standards
- FastMCP 3.2+ portmanteau tool pattern — tools use `operation` enum param
- Responses: structured dicts with `success`, `message`, domain-specific fields
- Dual transport: stdio (Claude Desktop) + HTTP (`MCP_TRANSPORT=http`)
- See [mcp-central-docs](https://github.com/sandraschi/mcp-central-docs) for fleet-wide coding standards

## Key Files
- `README.md` — full documentation
- `pyproject.toml` — build config and entry points
- `AGENTS.md` — OpenAI Codex agent context (if present)
