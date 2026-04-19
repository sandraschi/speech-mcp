# Local Voice Alternatives

Speech-MCP uses cloud APIs for all voice features. For offline or privacy-sensitive deployments, **kyutai-mcp** provides a local alternative based on the Moshi open-source speech model.

## kyutai-mcp

**Repo:** https://github.com/sandraschi/kyutai-mcp

Kyutai-mcp supervises a local [Moshi](https://github.com/kyutai-labs/moshi) process (Kyutai's real-time speech model), exposing it via MCP tools and a web dashboard.

### What it provides

- Real-time full-duplex voice conversation — same concept as Gemini Live but running locally
- Persona-aware WebSocket proxy with transcript capture
- Staged voice pipeline: quick-ack → intent → agentic research (Ollama/LM Studio) → spoken response
- Live data briefings: weather (Open-Meteo), world news (BBC RSS), AI news, stocks (Yahoo Finance)
- Moshi process supervisor (start/stop/status) via MCP and REST
- Dashboard webapp at port 10925

### Hardware requirements

- RTX 4090 (24GB VRAM) or equivalent — 8GB GPUs not supported by Moshi
- CUDA toolkit
- Python 3.12+, uv

### Comparison with speech-mcp

| | kyutai-mcp | speech-mcp |
|---|---|---|
| Engine | Moshi (local, open-source) | Gemini Live / TTS, Hume, ElevenLabs |
| Privacy | Fully offline | Cloud |
| Cost | Free after hardware | API usage |
| Voice quality | Good | Very good to highest |
| Multilingual | Limited | 100+ languages (Gemini TTS), 24 (Gemini Live) |
| Voice cloning | No | Yes (ElevenLabs IVC) |
| Emotion control | Implicit (native audio) | Explicit tags (`[whispers]`, etc.) |
| Agentic briefings | Yes (local LLM via Ollama/LM Studio) | Via RAG + `ask_docs` |

### Running alongside speech-mcp

Both servers can run simultaneously — they use separate port ranges:

| Service | speech-mcp | kyutai-mcp |
|---|---|---|
| Backend | 10918 | 10924 |
| Frontend | 10917 | 10925 |
| MCP HTTP | — | 10926 |

### Robot integration

Both can serve as the brain for robot voice control. The Yahboom bridge pattern from `docs/YAHBOOM_RASPBOT_VOICE.md` applies to either — replace the Gemini Live WebSocket endpoint with kyutai-mcp's voice pipeline when offline operation is needed.

## Other local options

**GPT-SoVITS v3** — Zero-shot voice cloning, strong for Japanese and Chinese. No conversation capability, TTS only. Runs on consumer GPU.

**CosyVoice 2** — Zero-shot voice cloning from Alibaba. Primarily Chinese/English TTS.

**Ollama + Kokoro/Piper TTS** — Combine a local LLM (Ollama) with a fast local TTS engine (Piper or Kokoro) for a fully offline pipeline. No native audio model — still the traditional STT→LLM→TTS stack with its latency.

None of the above are currently integrated into speech-mcp directly, but the `text_to_speech` tool's provider routing is designed to be extended.
