# PRD — Speech-MCP Multi-Provider Speech Gateway

## 1. Goal

A fleet-grade speech gateway (MCP server + React webapp) for embodied agents and
voice assistants: local STT (FunASR multilingual + sherpa-onnx streaming with
barge-in), cloud/local TTS, realtime voice, wake word, RAG, and a voice command
bus into fleet-agent. Focus languages: Japanese, English, German.

## 2. Requirements

### 2.1 Backend (MCP server + FastAPI)

- **Local STT — FunASR**: `transcribe_audio_file`, `transcribe_stream_chunk`.
  Default model `Fun-ASR-MLT-Nano-2512` (31 languages incl. EN/JA/DE), VAD +
  punctuation + diarization, native torch (cuda/cpu) or OpenAI-compatible
  sidecar (port 10914).
- **Local streaming STT — sherpa-onnx** (ja/en/de, CPU): `streaming_stt`
  (partials + endpoint), `barge_in_feed` (barge-in). No echo cancellation —
  gate mic feeding while the assistant speaks.
- **TTS**: windows (SAPI5), gemini, hume, elevenlabs, gemma (SAPI fallback).
- **Realtime**: Gemini Live + Hume EVI over WebSocket.
- **Fleet voice bus**: wake word (openWakeWord) -> streaming/batch STT ->
  `post_speech_intent` on fleet-agent.
- **FastMCP 3.4+** portmanteau tools, Prefab UI cards with real data, structured
  dict returns with `message`/`error`/`suggestions`.
- **Security**: API keys via `.env`; optional `SPEECH_MCP_AUTH_TOKEN` on REST.

### 2.2 Webapp (React/Vite/Tailwind)

- Dark-mode dashboard with live provider status (real data — no fabricated
  telemetry), Tools/Skills/Chat-adjacent pages, Apps Hub with live port probes,
  voice cloning, RAG search, STT control, settings, health, logs, help.

## 3. Success Metrics

- Local STT available fully offline (FunASR batch + sherpa streaming).
- Barge-in latencies driven by endpoint detection (trailing-silence rules).
- All gates green: ruff, format, pyright 0 errors, pytest, tsc, biome.

## 4. Roadmap

- Phase 1: Hume/ElevenLabs/Gemini TTS (Complete)
- Phase 2: FunASR local STT (Complete)
- Phase 3: Wake word + fleet voice bus (Complete)
- Phase 4: Streaming STT + barge-in via sherpa-onnx, ja/en/de (Complete)
- Phase 5: Robotics integration (Yahboom/ROS 2) (Next)
