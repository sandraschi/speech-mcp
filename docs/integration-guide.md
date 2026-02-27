# Speech-MCP Integration Guide

## Prerequisites

- Python 3.11+
- `uv` package manager (recommended) or `pip`
- API keys for at least one TTS provider (optional — Windows TTS works with no keys)

## Installation

```bash
git clone https://github.com/sandraschi/speech-mcp
cd speech-mcp
uv sync
```

## Claude Desktop Configuration

Add to `C:\Users\<you>\AppData\Roaming\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "speech-mcp": {
      "command": "D:\\Dev\\repos\\speech-mcp\\.venv\\Scripts\\python.exe",
      "args": ["-m", "speech_mcp.server"],
      "cwd": "D:\\Dev\\repos\\speech-mcp",
      "env": {
        "HUME_API_KEY": "your-hume-api-key",
        "HUME_CONFIG_ID": "your-hume-config-id",
        "ELEVENLABS_API_KEY": "your-elevenlabs-api-key"
      }
    }
  }
}
```

**Minimum working config (Windows TTS only, no API keys needed):**

```json
{
  "mcpServers": {
    "speech-mcp": {
      "command": "D:\\Dev\\repos\\speech-mcp\\.venv\\Scripts\\python.exe",
      "args": ["-m", "speech_mcp.server"],
      "cwd": "D:\\Dev\\repos\\speech-mcp"
    }
  }
}
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `HUME_API_KEY` | No | Hume AI API key for EVI and Octave TTS |
| `HUME_CONFIG_ID` | No | Hume EVI config ID for session management |
| `ELEVENLABS_API_KEY` | No | ElevenLabs API key for voice cloning TTS |

If no API keys are provided, the server falls back to Windows local TTS automatically.

## Starting the Webapp Dashboard

The webapp runs separately from the Claude Desktop MCP server. Two processes are needed:

```powershell
# From D:\Dev\repos\speech-mcp\
.\start.ps1
```

This starts:
- **Backend** on `http://localhost:10760` (FastAPI + MCP SSE)
- **Frontend** on `http://localhost:10761` (Vite React dashboard)

Open `http://localhost:10761` in your browser for the dashboard.

## Verifying the MCP Server Works

After restarting Claude Desktop, test in chat:

```
Use the text_to_speech tool to say "Hello from speech-mcp" using Windows TTS
```

Or test the RAG knowledge base:

```
Use search_docs to find information about expressive speech synthesis
```

## Troubleshooting

**Claude Desktop shows no speech-mcp tools**: Check logs at  
`C:\Users\<you>\AppData\Roaming\Claude\logs\mcp-server-speech-mcp.log`

**TTS returns stream_url but audio doesn't play**: The webapp backend must be running on port 10760 to serve the WebSocket stream. Run `.\start.ps1`.

**ImportError on startup**: Run `uv sync` in the project root to ensure all dependencies are installed.
