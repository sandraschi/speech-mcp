# Onboarding — speech-mcp

Get from zero to "the PC talks and listens" in ~15 minutes. This is the **default
required entry point**: without the steps below you get a dashboard with red
provider dots and silent STT — that is normal, not broken.

## What needs what (pick your path)

| You want | You need | Costs money? |
|----------|----------|--------------|
| Windows voice out of the box (SAPI5) | Nothing — works after `just start` | No |
| Local speech-to-text (FunASR, 31 langs) | `uv sync --extra funasr` + `FUNASR_ENABLED=true` | No (GPU helps; CPU works) |
| Streaming STT + barge-in (sherpa-onnx, ja/en/de) | `uv sync --extra sherpa` + `just sherpa-download` | No |
| Best cloud TTS (Gemini 3.8 Flash) | `GOOGLE_API_KEY` | Yes — Google AI Studio billing |
| Expressive TTS (Hume) / cloning (ElevenLabs) | `HUME_API_KEY` / `ELEVENLABS_API_KEY` | Yes — vendor billing |
| Offline wake word (openWakeWord) | `configure_local_wake_word(action="start")`, no key | No |

## Steps

```powershell
git clone https://github.com/sandraschi/speech-mcp
cd speech-mcp
Copy-Item .env.example .env          # fill in only the keys for your path
just bootstrap                        # deps + pre-commit + web frontend
just start                            # backend :10909 + frontend :10908
```

Open `http://localhost:10908` → Dashboard hero explains the rest. Health page
(`/api/v1/health`) shows exactly which providers are live and why the others are not.

Local STT (recommended for agents — no per-minute billing):

```powershell
uv sync --extra funasr
# .env: FUNASR_ENABLED=true, FUNASR_MODEL=FunAudioLLM/Fun-ASR-MLT-Nano-2512, FUNASR_DEVICE=cuda:0
```

Full STT guide: `docs/providers/funasr.md`. Streaming + barge-in: `docs/STREAMING_ASR.md`.
Voice command bus (wake → fleet-agent intent): `docs/VOICE_COMMAND_BUS.md`.

## Money / account pitfalls

- Cloud keys are **pay-as-you-go on the vendor side** (Google AI Studio, Hume,
  ElevenLabs). Set billing caps there first; speech-mcp never spends without a key.
- FunASR model downloads are ~1 GB (Nano) from HuggingFace/ModelScope — first run is slow.
- Kokoro local TTS needs the **espeak-ng system binary**
  (`winget install espeak-ng`), not just the `kokoro` PyPI extra.
- torch (FunASR native) is ~2.5 GB CUDA wheels; use the sidecar
  (`scripts/start_funasr_sidecar.py` + `FUNASR_OPENAI_URL`) to keep it out of the
  main MCP process.

## Sanity check (no key needed)

1. `just start`, open the cockpit → Backend Status shows green.
2. Voices page → provider `windows` → speak "Hello" — you hear SAPI5.
3. `search_docs(query="FunASR")` as an MCP tool — RAG answers from local docs.
4. If a provider dot is red, `/api/v1/health` names the missing key or extra.

## After onboarding

The Dashboard KPIs are live data (not samples). If you add a key later, restart the
backend (`just start` zombie-clears ports first) — providers are probed at startup.

Deeper docs: `docs/configuration.md` (env matrix), `docs/TROUBLESHOOTING.md`,
`docs/HUMANOID_VOICE.md` (fleet voice thesis).
