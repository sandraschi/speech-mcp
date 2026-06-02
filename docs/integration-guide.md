# Speech-MCP Integration Guide

## Prerequisites

- Python 3.12+
- `uv` package manager
- **FunASR (recommended):** NVIDIA GPU optional; `uv sync --extra funasr` — see [providers/funasr.md](providers/funasr.md)
- API keys for cloud TTS (optional — Windows TTS and FunASR STT work without cloud keys)

---

## Installation

```bash
git clone https://github.com/sandraschi/speech-mcp
cd speech-mcp
uv sync --extra funasr
cp .env.example .env
```

Set `FUNASR_ENABLED=true` in `.env` for local STT. For cloud TTS only (no torch): `uv sync` without the funasr extra.

Dependencies install into `.venv/`. On first FunASR run, hub models download from HuggingFace/ModelScope. FastEmbed downloads `BAAI/bge-small-en-v1.5` (~25 MB) for RAG on first use.

---

## Claude Desktop Configuration

`C:\Users\<you>\AppData\Roaming\Claude\claude_desktop_config.json`

### Full config (all providers)

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
        "HUME_API_KEY": "your-hume-api-key",
        "HUME_CONFIG_ID": "your-hume-evi-config-id",
        "ELEVENLABS_API_KEY": "your-elevenlabs-api-key",
        "FUNASR_ENABLED": "true",
        "FUNASR_MODEL": "FunAudioLLM/Fun-ASR-Nano-2512",
        "FUNASR_DEVICE": "cuda:0"
      }
    }
  }
}
```

### Minimum config (Windows TTS only, no API keys)

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
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

---

## Environment Variables

| Variable | Required | Where to get |
|---|---|---|
| `FUNASR_ENABLED` | No (recommended) | `true` after `uv sync --extra funasr` — [funasr.md](providers/funasr.md) |
| `FUNASR_OPENAI_URL` | No | Sidecar e.g. `http://127.0.0.1:10910/v1` instead of native torch |
| `FUNASR_MODEL` | No | Default `FunAudioLLM/Fun-ASR-Nano-2512` |
| `FUNASR_DEVICE` | No | `cuda:0`, `cpu`, or `mps` |
| `GOOGLE_API_KEY` | No | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) — free |
| `HUME_API_KEY` | No | [platform.hume.ai](https://platform.hume.ai) |
| `HUME_CONFIG_ID` | No | [evi.hume.ai](https://evi.hume.ai) — EVI chat only, not needed for TTS |
| `ELEVENLABS_API_KEY` | No | [elevenlabs.io](https://elevenlabs.io) |
| `openWakeWord` | No | Built-in local wake word (no API key) |

Variables can be placed in `.env` in the project root **or** in the Claude Desktop
config `env` block. The config block takes priority.

---

## Verifying the Server Works

After restarting Claude Desktop, check the server appears in Settings → Extensions,
then test in chat:

```
Use text_to_speech to say "Hello from speech-mcp" using the windows provider
```

You should hear audio through your PC speakers immediately.

Test Gemini with audio tags (requires `GOOGLE_API_KEY`):

```
Use text_to_speech with provider gemini, voice Kore:
"[cheerfully] Hello! [whispers] The reductionist universe has room for wonder."
```

Test the RAG knowledge base:

```
Use search_docs to find information about Hume Octave expressive synthesis
```

Test FunASR STT (requires `FUNASR_ENABLED` or sidecar):

```
Use transcribe_audio_file with provider funasr on a short WAV path on disk
```

See [CHINESE_AI_RESEARCH.md](CHINESE_AI_RESEARCH.md) for other Chinese open speech models (CosyVoice, ChatTTS, GPT-SoVITS).

---

## Troubleshooting

**Server doesn't appear in Claude Desktop:**
Check `C:\Users\<you>\AppData\Roaming\Claude\logs\mcp-server-speechops.log`.
Common causes: missing `uv` on PATH, wrong `--directory` path, import error on startup.

**Audio doesn't play:**
Confirm Windows default audio device is working. The `windows` provider uses
`winsound.PlaySound` (SAPI5 WAV). The `hume` and `gemini` providers also use
`winsound` after synthesising to a temp WAV file.

**Gemini TTS fails with "Gemini TTS not available":**
`GOOGLE_API_KEY` is not set or the value is blank. Add it to `.env` or the
Claude Desktop config `env` block and restart.

**Hume TTS fails with "HUME_API_KEY not configured":**
Same as above for `HUME_API_KEY`.

**RAG slow on first call:**
FastEmbed downloads `BAAI/bge-small-en-v1.5` (~25 MB) on first use and caches it.
Subsequent calls are fast.

**FunASR / transcribe tools not configured:**
Run `uv sync --extra funasr`. Set `FUNASR_ENABLED=true` or `FUNASR_OPENAI_URL` in `.env` or Claude Desktop `env`. First model load downloads weights from the hub.

**FunASR CUDA OOM:**
Use `FUNASR_DEVICE=cpu`, a smaller hub model, or the sidecar on another machine; clear `FUNASR_SPK_MODEL` to disable diarization.

**`ImportError: No module named 'fastmcp.ui'`:**
Stale `.pyc` cache. Delete `src/speech_mcp/__pycache__/` and restart.

---

## Webapp Dashboard (optional)

The webapp runs separately from the MCP server:

```powershell
# From D:\Dev\repos\speech-mcp\
.\start.ps1
```

- Backend: `http://localhost:10909`
- Frontend: `http://localhost:10908`

The MCP tools work without the webapp running.
