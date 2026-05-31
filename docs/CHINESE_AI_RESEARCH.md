# Advanced Research: Chinese Open-Weight Speech AI (2026)

The Chinese AI speech ecosystem leads in open-weight industrial ASR, prosodic TTS, and edge deployment. **FunASR is now integrated into speech-mcp** — the rest remain future provider candidates.

## Integrated

### FunASR / Fun-ASR / SenseVoice (Alibaba Tongyi) ✅

- **Status:** Integrated in speech-mcp as default local STT (`transcribe_audio_file`, `transcribe_stream_chunk`)
- **Guide:** [providers/funasr.md](providers/funasr.md)
- **Papers:** [2509.12508](https://arxiv.org/abs/2509.12508) (Fun-ASR), [2407.04051](https://arxiv.org/abs/2407.04051) (FunAudioLLM)
- **Repos:** [modelscope/FunASR](https://github.com/modelscope/FunASR), [FunAudioLLM/Fun-ASR](https://github.com/FunAudioLLM/Fun-ASR), [FunAudioLLM/SenseVoice](https://github.com/FunAudioLLM/SenseVoice)
- **Why it wins:** Open weights, no subscription, 170× GPU RTF, unified VAD+ASR+punc+diarization, emotion via SenseVoice, ONNX/CPU/GPU/Windows SDK edge matrix, OpenAI-compatible `funasr-server` sidecar

## Candidates (not yet integrated)

### GPT-SoVITS (v3+)

- **Strength:** High-fidelity zero-shot voice cloning
- **Use case:** Local ElevenLabs alternative for TTS/cloning

### ChatTTS

- **Strength:** Conversational prosody — laughter, pauses, oral interjections
- **Use case:** Prosody-first assistant responses

### CosyVoice 2/3 (Alibaba)

- **Strength:** Zero-shot multilingual TTS, cross-lingual cloning
- **Use case:** TTS complement to FunASR STT (same FunAudioLLM family)

## Fleet integration map

| Pattern | Provider | Status |
|---|---|---|
| Local batch STT | FunASR | ✅ Done |
| Local duplex conversation | kyutai-mcp (Moshi) | Separate repo |
| Cloud TTS/STT | Gemini, Hume, ElevenLabs | ✅ Done |
| Wake word | openWakeWord | ✅ Done |
| Local cloning | GPT-SoVITS | Future |
| Local expressive TTS | ChatTTS / CosyVoice | Future |

---

*Updated May 2026 after FunASR integration. Benchmarks and links verified against arXiv 2509.12508 and official GitHub releases.*
