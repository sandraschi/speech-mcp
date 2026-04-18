# Project Manifest — Speech-MCP

| Attribute | Value |
| :--- | :--- |
| **Name** | speech-mcp |
| **Version** | 0.4.0 |
| **Status** | Beta |
| **FastMCP** | 3.2.4 |
| **Python** | 3.13 |
| **Architecture** | FastMCP MCP server + optional FastAPI webapp |
| **MCP server name** | `speechops` (in Claude Desktop) |

---

## What it does

speech-mcp is a multi-provider text-to-speech MCP server. Ask Claude Desktop to
speak something and audio comes out of your PC speakers. Three providers are
currently functional:

| Provider | Quality | Key |
|---|---|---|
| Windows SAPI5 | Basic | None |
| Hume AI Octave | Expressive, prose-directed | `HUME_API_KEY` |
| Gemini 2.5 Flash TTS | High-fidelity, audio-tag directed | `GOOGLE_API_KEY` |

Beyond TTS, the server includes semantic search over its own documentation (RAG),
Alexa-style timer/weather utilities, a social-engineering safety validator, and
two inline Prefab UI dashboards rendered directly in the Claude Desktop conversation.

---

## Tool inventory

| Tool | Status | Provider needed |
|---|---|---|
| `text_to_speech` | ✅ Working — plays audio | None / Hume / Gemini / ElevenLabs |
| `text_to_dialogue` | ✅ Working — multi-voice dialogue | ElevenLabs |
| `manage_voice_clones` | ✅ list + IVC clone + delete | ElevenLabs / Hume |
| `search_docs` | ✅ Working | None (local) |
| `ask_docs` | ✅ Working | None (uses ctx.sample) |
| `manage_domestic_utility` | ✅ Working (timer + weather) | None |
| `safety_validate_intent` | ✅ Working | None |
| `safety_log_audit` | ✅ Working | None |
| `safety_verify_auth` | ✅ Working | `SPEECH_MCP_AUTH_TOKEN` |
| `trigger_action` | ⚠️ Stub (proxy only) | None |
| `prosody_dashboard` | ✅ Prefab UI | None |
| `speech_activity_chart` | ✅ Prefab UI | None |
| `start_evi_session` | ⚠️ Returns config only | `HUME_API_KEY` |
| `detect_wake_word` | ⚠️ Arms VAD config only | None |
| `orchestrate_alexa_pattern` | ✅ Working (sampling) | None |
| `agentic_conversation_workflow` | ✅ Working (sampling) | None |
| `configure_local_wake_word` | ✅ Working — real Porcupine listener | `PICOVOICE_API_KEY` |

---

## Documentation map

| Doc | Contents |
|---|---|
| `docs/integration-guide.md` | Installation, Claude Desktop config, troubleshooting |
| `docs/configuration.md` | All env vars, provider matrix, ports |
| `docs/tools-reference.md` | Every tool — parameters, returns, examples |
| `docs/prefab_ui_reference.md` | prefab_ui 0.19.x components, charts, actions, Rx |
| `docs/providers/gemini.md` | Gemini TTS deep-dive |
| `docs/providers/hume.md` | Hume AI EVI + Octave |
| `docs/providers/elevenlabs.md` | ElevenLabs voice cloning |
| `CHANGELOG.md` | Version history |

---

## Repo

[github.com/sandraschi/speech-mcp](https://github.com/sandraschi/speech-mcp)
[glama.ai/mcp/servers?query=sandraschi](https://glama.ai/mcp/servers?query=sandraschi)

---

*Last updated: 2026-04-17 (v0.4.0)*
