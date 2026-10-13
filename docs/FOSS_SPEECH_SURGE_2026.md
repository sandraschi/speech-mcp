# Why local speech is surging in FOSS / local AI (2026-09-29)

Evidence: `debpalash/VoiceStudio` — 43,942 stars / 5,086 forks (gh API 2026-09-29),
v0.5.6 shipping every 2-3 days. Open-source, fully-local ElevenLabs alternative:
voice cloning, voice design, video dubbing, dictation, transcription, audiobooks,
646 languages claimed.

Source: clone at `D:\Dev\repos\_upstream\VoiceStudio`, docs/mcp.md + speech-platform.md
+ feature-catalog.md, audit `reports/wrappee-drift-speech-mcp-2026-09-29.md`.

## Thesis

Speech is the missing I/O layer for everything else devs are building.
LLMs got local first (Ollama, LM Studio). Speech is next, for the same reasons:
privacy, no per-minute tax, offline robots, daily workflows.

1. **Agents need mouths and ears.** Speak this diff, transcribe this meeting,
   clone my voice for a demo — from Claude Code / Cursor / Pi, without cloud billing.
   VoiceStudio ships MCP (`generate_speech`, `clone_voice`, `transcribe`) for exactly this.
2. **Local-first is the requirement, not a feature.** No keys, no accounts,
   CUDA/MPS/ROCm/CPU auto-detect. Their core value (CLAUDE.md): "a first-run that
   actually works." That is what gets starred.
3. **Chinese open-weight velocity.** FunAudioLLM family (FunASR, SenseVoice,
   CosyVoice 2/3, Fun-ASR Nano), Sherpa-ONNX, Parakeet, GPT-SoVITS, Fish-Speech,
   FireRedASR, WeNet — ModelScope/HF weights, ONNX edge, published RTF benchmarks.
   speech-mcp already bets this way: FunASR default (VAD+punc+diarization, ~170x RT GPU).
4. **Killer apps are boring and daily.** Floating dictation widget, Rust-sidecar
   native insertion, 50-video batch dub, PDF-to-audiobook, vocal isolation,
   diarization, AI watermark. Not chatbots — hands-free commands, noisy rooms,
   structured transcripts for planners.

## What this means for speech-mcp

Stay a **gateway**, not a zoo. VoiceStudio proves demand AND proves the cost of
hosting 17 TTS + 10 ASR in-process: dependency scar tissue
(setuptools<80, pyannote<4, pedalboard<0.9.21, sherpa-onnx-core explicit,
socksio, truststore, fastapi<0.137), VRAM leaks (sidecar per request → OOM),
ROCm/CUDA splits, ffmpeg breakage. See pyproject.toml comments — every pin has
an issue number.

Strategy:
- Keep 2-3 curated local defaults in-process: FunASR (batch STT), sherpa-onnx
  (streaming + barge-in), Kokoro / Qwen3-TTS (small local TTS).
- Route the zoo via sidecar: `providers/voicestudio.py` (disabled by default,
  MCP + OpenAI-compat STT fallback, no weights in-process). Add CosyVoice /
  IndexTTS only as remote endpoints if needed.
- Steal the patterns, not the engines: files-mode MCP (audio_url, no base64 in
  context), per-client voice bindings, `.well-known` discovery, audioseal watermark opt-in.
- License boundary: VoiceStudio is AGPL-3.0 + commercial dual. speech-mcp is MIT.
  Never embed — talk HTTP/MCP to a running instance.

Related: HUMANOID_VOICE.md (why voice is load-bearing for humanoids),
CHINESE_AI_RESEARCH.md (engine landscape), LOCAL_VOICE_OFFLINE_2026.md,
reports/wrappee-drift-speech-mcp-2026-09-29.md.
