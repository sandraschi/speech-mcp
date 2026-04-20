# Project Manifest — Speech-MCP

| Attribute | Value |
| :--- | :--- |
| **Name** | speech-mcp |
| **Version** | 0.6.0 |
| **Status** | Beta |
| **FastMCP** | 3.2.4 |
| **Python** | 3.13 |
| **Architecture** | FastMCP MCP server + optional FastAPI webapp |
| **MCP server name** | `speechops` (in Claude Desktop) |

---

## What it does

speech-mcp is a multi-provider text-to-speech and sensing MCP server. It enables the fleet with both cloud-based expressive synthesis and local-first native multimodal reasoning.

| Provider | Mode | Quality | Key |
|---|---|---|---|
| Windows SAPI5 | Batch TTS | Basic | None |
| **Gemma 4** | **Native Multimodal** | **SOTA Local** | None |
| Gemini 3.1 Flash | Batch TTS | High-fidelity | `GOOGLE_API_KEY` |
| Hume AI Octave | Batch TTS | Expressive | `HUME_API_KEY` |
| ElevenLabs | Batch TTS + Cloning | High-fidelity | `ELEVEN_API_KEY` |

Beyond TTS, the server includes semantic search over its own documentation (RAG), Alexa-style timer/weather utilities, a social-engineering safety validator, and inline Prefab UI dashboards rendered directly in the Claude Desktop conversation.

---

## Technical Providers (Internal)

| Provider ID | Implementation Class | Notes |
|---|---|---|
| `windows` | `speech_mcp.providers.local.LocalProvider` | SAPI5 Bridge |
| `gemma` | `speech_mcp.providers.gemma.GemmaProvider` | Native 2026 Engine |
| `gemini` | `speech_mcp.providers.gemini.GeminiProvider` | Cloud Flash TTS |
| `hume` | `speech_mcp.providers.hume.HumeProvider` | Emotional Octave |
| `elevenlabs` | `speech_mcp.providers.elevenlabs.ElevenLabsProvider` | IVC / Professional |

---

## Tool inventory

| Tool | Status | Note |
|---|---|---|
| `text_to_speech` | ✅ Working | Multi-provider synthesis |
| `transcribe` | ✅ Working | Hybrid (Gemma Local -> Gemini Cloud) |
| `manage_voice_clones` | ✅ Working | ElevenLabs / Hume |
| `search_docs` | ✅ Working | Semantic search |
| `ask_docs` | ✅ Working | RAG via ctx.sample |
| `manage_domestic_utility` | ✅ Working | Timer + Weather |
| `safety_validate_intent` | ✅ Working | Agentic safety |
| `prosody_dashboard` | ✅ Prefab UI | Emotional monitoring |
| `speech_activity_chart` | ✅ Prefab UI | Telemetry |
| `start_evi_session` | ⚠️ Stub | Hume EVI WS |
| `detect_wake_word` | ⚠️ Armed | Tier 1 VAD |
| `orchestrate_alexa_pattern`| ✅ Working | Skill orchestration |
| `configure_local_wake_word`| ✅ Working | Porcupine listener |

---

## Documentation map

| Doc | Contents |
|---|---|
| `docs/integration-guide.md` | Installation, Claude Desktop config |
| `docs/configuration.md` | All env vars, provider matrix |
| `docs/tools-reference.md` | Every tool — parameters, examples |
| `docs/prefab_ui_reference.md` | prefab_ui 0.19.x details |
| `CHANGELOG.md` | Version history |

---

## Repo

[github.com/sandraschi/speech-mcp](https://github.com/sandraschi/speech-mcp)
[glama.ai/mcp/servers?query=sandraschi](https://glama.ai/mcp/servers?query=sandraschi)

---

*Last updated: 2026-04-20 (v0.6.0)*
