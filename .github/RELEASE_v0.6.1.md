## Beta (pre-1.0)

Speech-MCP **0.6.1** adds the **Fleet Voice Command Bus**: optional wake-word → short utterance capture → FunASR transcription → HTTP POST to fleet-agent (`/api/voice/intent`). APIs and env names may change before 1.0.

### Highlights

- **Fleet Voice Command Bus** — set `FLEET_VOICE_DELEGATE=1` and `FLEET_VOICE_ROUTER_URL` (default `http://127.0.0.1:10996/api/voice/intent`)
- **Wake word integration** — `configure_local_wake_word` reports `fleet_delegate` and router URL when active
- **FunASR hook** — post-wake file transcription when FunASR is enabled
- **Docs** — [docs/VOICE_COMMAND_BUS.md](https://github.com/sandraschi/speech-mcp/blob/main/docs/VOICE_COMMAND_BUS.md)

### Install

```powershell
git clone https://github.com/sandraschi/speech-mcp
cd speech-mcp
just bootstrap
just start
```

See [INSTALL.md](https://github.com/sandraschi/speech-mcp/blob/main/INSTALL.md). Requires **FunASR** optional extra for fleet STT: `uv sync --extra funasr`.

### Since v0.6.0

- Fleet voice bus + listener modules and tests
- Biome `lineEnding: lf` for stable web CI

Full changelog: [CHANGELOG.md](https://github.com/sandraschi/speech-mcp/blob/main/CHANGELOG.md)
