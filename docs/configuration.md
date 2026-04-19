# Speech-MCP Configuration Reference

## Environment Variables

Create or edit `.env` in the project root:

```env
# Hume AI — Octave TTS + EVI real-time conversation
HUME_API_KEY=your-hume-api-key
HUME_CONFIG_ID=your-hume-evi-config-id   # from evi.hume.ai — needed for EVI chat, not TTS

# ElevenLabs — voice cloning TTS
ELEVENLABS_API_KEY=your-elevenlabs-api-key

# Google Gemini — Gemini 2.5 Flash TTS
# Free key at https://aistudio.google.com/apikey
GOOGLE_API_KEY=your-google-api-key

# Picovoice — local wake-word detection (optional)
# FREE PLAN is perpetual for personal non-commercial use (1 device, no expiry, no CC).
# The "Free Trial" on their site is a separate 7-day enterprise eval path — ignore it.
# Sign up at https://console.picovoice.ai/ and copy the AccessKey from the dashboard.
PICOVOICE_API_KEY=your-picovoice-key

# Auth token for WebSocket stream endpoint (optional)
SPEECH_MCP_AUTH_TOKEN=your-secret-token

# OSC for avatar lip-flap (optional)
OSC_HOST=127.0.0.1
OSC_PORT=8000
```

None are required — the server starts and defaults to Windows TTS with no keys.

---

## Provider Availability Matrix

| Provider | Key | Mode | Audio quality | Notes |
|---|---|---|---|---|
| `windows` | None | Batch | Low (SAPI5 robotic) | Always works, instant, no API key |
| `hume` | `HUME_API_KEY` | Batch | High (Octave) | `description` prose style prompt |
| `gemini` | `GOOGLE_API_KEY` | Batch | Highest | Model: `gemini-3.1-flash-tts-preview` |
| `elevenlabs` | `ELEVENLABS_API_KEY` | Batch | High | Voice cloning supported |
| `gemini_live` | `GOOGLE_API_KEY` | Real-time | Very good | Full-duplex conversation, sub-second latency |

---

## Gemini Live (Real-Time Voice Chat)

Uses the same `GOOGLE_API_KEY` as batch TTS. No additional key needed.

Model: `gemini-3.1-flash-live-preview`

Audio format: input 16kHz int16 PCM, output 24kHz int16 PCM (wrapped in WAV per chunk by the backend proxy).

Session limit: 10 minutes. Reconnect to continue; context is not automatically carried over.

Available voices in VoiceChat UI: Aoede, Charon, Fenrir, Kore (default), Orion, Puck, Leda, Orus, Zephyr.

See [docs/gemini_live.md](gemini_live.md) for full protocol documentation.

---

## Gemini Voices (prebuilt, `gemini-3.1-flash-tts-preview`)

Aoede, Charon, Fenrir, **Kore** (default), Orion, Puck, Leda, Orus, Zephyr,
Callirrhoe, Autonoe, Enceladus, Iocaste, Umbriel, Algieba, Despina, Erinome,
Algenib, Rasalgethi, Laomedeia, Achernar, Alnilam, Schedar, Gacrux, Pulcherrima,
Achird, Zubenelgenubi, Vindemiatrix, Sadachbia, Sadaltager, Sulafar

### Gemini Audio Tags

Embed directly in the text string:

```
[excited]  [whispers]  [laughs]  [sighs]  [fast]  [slow]
[sadly]  [cheerfully]  [dramatically]  [nervously]
```

Example: `"[cheerfully] Good morning! [whispers] Don't tell anyone, but..."`.

---

## RAG Configuration

Knowledge base at `data/lancedb/`, auto-indexed on first start from `docs/*.md`.

| Setting | Value |
|---|---|
| Embedding model | `BAAI/bge-small-en-v1.5` (FastEmbed, ~25 MB, auto-downloaded) |
| DB engine | LanceDB |
| Table | `speech_docs` |
| Search type | Vector similarity (cosine) |

To re-index from scratch: delete `data/lancedb/` and restart.

---

## Webapp Ports

| Service | Default port | Override |
|---|---|---|
| Backend (FastAPI) | `10918` | `PORT` env var |
| Frontend (Vite) | `10917` | `web/vite.config.ts` |
| CORS origins | `http://localhost:10917` | `CORS_ORIGINS` env var (comma-separated) |

Set `SPEECH_MCP_BACKEND_URL` if the backend runs on a different host/port.

---

## Claude Desktop Config

`C:\Users\<you>\AppData\Roaming\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "speechops": {
      "command": "uv",
      "args": [
        "--directory", "D:/Dev/repos/speech-mcp",
        "run", "python", "-m", "speech_mcp.server"
      ],
      "env": {
        "PYTHONPATH": "D:/Dev/repos/speech-mcp/src",
        "PYTHONUNBUFFERED": "1",
        "GOOGLE_API_KEY": "your-google-api-key",
        "HUME_API_KEY": "your-hume-api-key"
      }
    }
  }
}
```

Keys in the `env` block take priority over `.env` file values.

---

## Log Location

```
C:\Users\<you>\AppData\Roaming\Claude\logs\mcp-server-speechops.log
```

---

## FastMCP Settings

| Variable | Default | Description |
|---|---|---|
| `FASTMCP_SHOW_SERVER_BANNER` | `true` | Startup banner in logs |
| `SPEECH_MCP_BACKEND_URL` | `http://localhost:10918` | Backend base URL for stream proxy |
