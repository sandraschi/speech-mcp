# Speech-MCP Architecture

## Overview

Speech-MCP uses a **dual-server pattern**: the MCP server (stdio transport for Claude Desktop) and the webapp backend (HTTP/SSE/WebSocket) are separate processes sharing the same tool definitions.

```
Claude Desktop
    │
    │ (stdio JSON-RPC)
    ▼
speech_mcp.server          ← python -m speech_mcp.server
    │
    ├── FastMCP 3.2+ server
    ├── @mcp.tool: text_to_speech        (windows / hume / gemini / elevenlabs)
    ├── @mcp.tool: text_to_dialogue      (ElevenLabs multi-voice)
    ├── @mcp.tool: manage_voice_clones   (ElevenLabs IVC, Hume voices)
    ├── @mcp.tool: manage_domestic_utility (timers, weather)
    ├── @mcp.tool: trigger_action        (IoT / smart home)
    ├── @mcp.tool: search_docs           (RAG vector search)
    ├── @mcp.tool: ask_docs              (RAG + ctx.sample → grounded Q&A)
    ├── @mcp.tool: configure_local_wake_word (openWakeWord)
    └── @mcp.tool: agentic_conversation_workflow

Browser Dashboard
    │
    │ (HTTP REST + WebSocket)
    ▼
speech_mcp.webapp          ← python -m speech_mcp.webapp
    │
    ├── FastAPI app (port 10918)
    │   ├── GET  /api/v1/health
    │   ├── GET  /api/v1/voices
    │   ├── POST /api/v1/voices/clone       (ElevenLabs IVC multipart upload)
    │   ├── GET  /api/v1/tts/wav            (browser audio preview)
    │   ├── POST /api/v1/tts                (server-side playback)
    │   ├── GET  /api/v1/search?q=...       (RAG)
    │   ├── POST /api/v1/ask                (RAG + local LLM)
    │   ├── POST /api/v1/demos/run          (demo scripts)
    │   ├── POST /api/v1/wake_word
    │   ├── WS   /ws/stream?provider=...   (audio proxy — see below)
    │   ├── WS   /ws/logs                  (live log broadcast)
    │   └── /mcp → FastMCP SSE transport
    │
    └── Vite React frontend (port 10917)
        ├── VoiceChat          ← Gemini Live real-time voice (NEW)
        ├── CreativeLabs       ← Polyglot TTS + prosody demos
        ├── VoicesPage         ← ElevenLabs voice library + IVC cloning
        ├── SpeechToText       ← openWakeWord control
        ├── SemanticSearch     ← RAG search + local LLM Q&A
        ├── AgenticWorkflow
        ├── HistoryPage
        ├── SystemLogs
        ├── ToolsPage
        ├── SettingsPage
        └── ServiceLinkage     (fleet discovery)
```

---

## WebSocket Audio Proxy (`/ws/stream`)

The `provider` URL parameter selects the handler in `streaming.py`:

```
provider=gemini_live   → _handle_gemini_live()   Full-duplex Live API proxy
provider=gemini        → _handle_gemini()         Batch TTS → single WAV frame
provider=elevenlabs    → _handle_elevenlabs()     Streaming MP3 chunks
provider=windows       → _handle_windows()        SAPI5 WAV synthesis
provider=hume          → _handle_hume()           (stub)
provider=stt           → _handle_stt_stream()     Gemini Live STT proxy
```

### Gemini Live flow

```
Browser mic (16kHz int16 PCM binary frames)
    │
    ▼
_handle_gemini_live()
    ├── browser_to_gemini():
    │     binary  → session.send_realtime_input(audio=Blob(..., "audio/pcm;rate=16000"))
    │     JSON text → send_realtime_input(text=...) or audio_stream_end=True
    │
    └── gemini_to_browser():
          PCM chunks → _pcm_to_wav_bytes() → send_bytes to browser
          transcripts, interrupted, turn_complete → send_text JSON
    │
    ▼
client.aio.live.connect(model="gemini-3.1-flash-live-preview")
    └── google-genai SDK, GOOGLE_API_KEY
```

### Batch Gemini TTS flow

```
{ type: "tts", text: "..." } JSON frame
    │
    ▼
_handle_gemini()
    └── GeminiProvider.synthesize_wav(text, voice_name)
            └── google-genai: models.generate_content(model="gemini-3.1-flash-tts-preview")
                    └── PCM → WAV → send_bytes (single frame)
```

---

## TTS Provider Routing (MCP tools)

```
text_to_speech(provider="windows"|"hume"|"gemini"|"elevenlabs")
    │
    ├── "windows"     → pyttsx3 SAPI5 → winsound.PlaySound (no API key)
    ├── "hume"        → HumeClient.tts.synthesize_file() → WAV → winsound
    ├── "gemini"      → GeminiProvider.synthesize_wav() → WAV → winsound
    └── "elevenlabs"  → ElevenLabs.text_to_speech.convert() → MP3 → wmplayer
```

---

## RAG Stack

```
DocumentStore (vector_store.py)
    │
    └── BaseVectorStore (rag_core.py)
            │
            ├── LanceDB 0.29.x  ← embedded, no server needed
            │   └── data/lancedb/speech_docs.lance
            │
            └── FastEmbed 0.7.x
                └── BAAI/bge-small-en-v1.5 (384-dim, ~25MB)
```

Documents are ingested once and persist across restarts. The `ask_docs` tool retrieves top-8 chunks then calls `ctx.sample()` to generate a grounded answer via Claude sampling.

---

## Port Assignments

| Port | Service |
|---|---|
| 10918 | FastAPI backend (REST + WebSocket + MCP SSE) |
| 10917 | Vite React frontend dashboard |

---

## FastMCP Version

Targets **FastMCP 3.2+** (March 14, 2026).

Key APIs used:
- `@mcp.tool` — decorator without parentheses
- `ctx.sample()` — replaces deprecated `ctx.session.create_message()`
- `mcp.run_stdio_async()` — stdio transport entry point
- `mcp.http_app(transport="sse")` — SSE transport for webapp mounting
