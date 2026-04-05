# Speech-MCP Configuration Reference

## Environment Variables

Create a `.env` file in the project root (copied from `.env.example`):

```env
# Hume AI — EVI real-time conversation + Octave TTS
HUME_API_KEY=your-hume-api-key
HUME_CONFIG_ID=your-hume-evi-config-id

# ElevenLabs — voice cloning TTS
ELEVENLABS_API_KEY=your-elevenlabs-api-key
```

None of these are required — the server starts and uses Windows TTS if no keys are present.

## Provider Availability Matrix

| Provider | API Key Required | Voice Cloning | Emotion Control | Streaming |
|---|---|---|---|---|
| Hume AI | Yes (`HUME_API_KEY`) | No | Yes (EVI) | Yes |
| ElevenLabs | Yes (`ELEVENLABS_API_KEY`) | Yes | Limited | Yes |
| Windows TTS | No | No | No | No |

## RAG Configuration

The knowledge base is stored at `data/lancedb/` and uses:

- **Embedding model**: `BAAI/bge-small-en-v1.5` (FastEmbed, downloaded automatically on first run, ~25MB)
- **Table name**: `speech_docs`
- **Search type**: vector similarity (cosine)

To re-index documents, delete `data/lancedb/` and restart the server.

## Webapp Ports

| Service | Default port | Config |
|---|---|---|
| Backend | 10918 | `web/start.ps1` (`$BackendPort`); override via `PORT` when running uvicorn. |
| Frontend | 10917 | `web/start.ps1` (`$WebPort`); Vite `--port`. |

Set `SPEECH_MCP_BACKEND_URL` (e.g. `http://localhost:10918`) when the backend runs on another host/port so tools and the webapp use it. Set `CORS_ORIGINS` (comma-separated) if the frontend origin differs (default includes `http://localhost:10917`).

## Claude Desktop Config Location

```
C:\Users\<username>\AppData\Roaming\Claude\claude_desktop_config.json
```

See `docs/integration-guide.md` for the complete config snippet.

## Log Location

```
C:\Users\<username>\AppData\Roaming\Claude\logs\mcp-server-speech-mcp.log
```

## FastMCP Settings

FastMCP 3.x settings are controlled via environment variables:

| Variable | Default | Description |
|---|---|---|
| `FASTMCP_SHOW_SERVER_BANNER` | `true` | Show startup banner in logs |
| `FASTMCP_DECORATOR_MODE` | `function` | Set to `object` for v2 compatibility |
