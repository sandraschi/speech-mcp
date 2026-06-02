## Beta (pre-1.0)

Speech-MCP **0.6.2** makes the **humanoid & fleet voice thesis** visible across docs and the web cockpit, and aligns runtime version metadata with the package. APIs and env names may change before 1.0.

### Why this release

Good **speech perception and reply** are infrastructure for embodied agents and humanoids—not a side feature. This release documents that stance explicitly and ties it to what ships today: **FunASR** local STT, the **Fleet Voice Command Bus**, and optional cloud TTS/live for social quality.

**Canonical thesis:** [docs/HUMANOID_VOICE.md](https://github.com/sandraschi/speech-mcp/blob/main/docs/HUMANOID_VOICE.md)

### Highlights

#### Humanoid voice documentation

- **`docs/HUMANOID_VOICE.md`** (new) — full architecture and product thesis:
  - Perceive → understand → act → express loop for humanoids
  - Why Chinese open-weight industrial speech (FunASR, SenseVoice, CosyVoice ecosystem) fits edge robots
  - Fleet reference architecture (wake → FunASR → fleet-agent **10996** → yahboom/home-assistant MCPs)
  - Deployment topologies: edge-native, sidecar GPU (**10910**), cloud-augmented, NSSM headless
  - Operator checklist, latency budgeting, safety (beta; do not use cloud STT as sole e-stop)
  - Roadmap table (CosyVoice TTS, kyutai duplex, etc.)

#### README & agent indexing

- README: humanoid callout, FunASR quick enable, Chinese FOSS comparison table, doc index
- **`docs/CHINESE_AI_RESEARCH.md`** — landscape + fleet integration map
- **`llms.txt` / `llms-full.txt`** — humanoid doc first for MCP hosts
- Cross-links: [funasr.md](https://github.com/sandraschi/speech-mcp/blob/main/docs/providers/funasr.md), [VOICE_COMMAND_BUS.md](https://github.com/sandraschi/speech-mcp/blob/main/docs/VOICE_COMMAND_BUS.md), [YAHBOOM_RASPBOT_VOICE.md](https://github.com/sandraschi/speech-mcp/blob/main/docs/YAHBOOM_RASPBOT_VOICE.md), INSTALL, integration guide

#### Web cockpit (Vite, port 10908)

- **Dashboard** — purple “Humanoid & fleet voice” banner with link to thesis + navigation to Help / STT
- **Help** — default-open Humanoid section; expanded FunASR, REST/MCP STT, FAQ

#### Version alignment

- `pyproject.toml` and health/MCP responses report **0.6.2** (was stale `0.6.0` in server metadata)

### Already in 0.6.1 (unchanged behavior, documented in 0.6.2)

- **Fleet Voice Command Bus** — `FLEET_VOICE_DELEGATE=1`, wake → record → FunASR → `POST` fleet-agent `/api/voice/intent`
- **FunASR STT** — `transcribe_audio_file`, `transcribe_stream_chunk`, sidecar `scripts/start_funasr_sidecar.py` (**10910**)

### Install

```powershell
git clone https://github.com/sandraschi/speech-mcp
cd speech-mcp
just bootstrap
just start
```

FunASR (fleet STT):

```powershell
uv sync --extra funasr
# .env: FUNASR_ENABLED=true, FLEET_VOICE_DELEGATE=1 (see docs/HUMANOID_VOICE.md)
```

### Ports (fleet)

| Service | Port |
|---------|------|
| speech-mcp webapp | 10908 |
| speech-mcp backend / MCP HTTP | 10909 |
| FunASR OpenAI sidecar (optional) | 10910 |
| fleet-agent-mcp | 10996 |

### Desktop / Tauri

This repository has **no Tauri shell**. Distribution for this tag:

- **Python** sdist + wheel via GitHub Actions (`release.yml` on tag push)
- **Webapp** — run `just start` or Vite dev/build; backend serves API on **10909**

If you need a packaged desktop host, use fleet NSSM pattern or a separate Tauri wrapper repo—out of scope for speech-mcp **0.6.2**.

### Artifacts

- `dist/*.whl` and sdist attached by CI
- Full changelog: [CHANGELOG.md](https://github.com/sandraschi/speech-mcp/blob/main/CHANGELOG.md)

### Since v0.6.1

- Humanoid thesis doc + doc/web visibility pass
- README badge and expanded Chinese FOSS / FunASR operator content
- Version metadata fix in `server.py`
