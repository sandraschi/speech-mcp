# Advanced Research: Chinese Open-Weight Speech AI (2026)

The Chinese ecosystem leads in **open-weight industrial ASR**, expressive **TTS**, and **edge** deployment. speech-mcp treats **FunASR as the primary local STT path**; other projects below are documented for comparison, fleet planning, and future provider work.

**Canonical FunASR setup in this repo:** [providers/funasr.md](providers/funasr.md)

---

## Integrated — FunASR / Fun-ASR / SenseVoice (Alibaba Tongyi)

| Item | Detail |
|---|---|
| **Status** | Default local STT in speech-mcp |
| **MCP** | `transcribe_audio_file`, `transcribe_stream_chunk` |
| **REST** | `POST /api/v1/transcribe?provider=funasr` |
| **Toolkit** | [modelscope/FunASR](https://github.com/modelscope/FunASR) — training, export, ONNX, `funasr-server`, Docker, upstream MCP |
| **Model repos** | [Fun-ASR](https://github.com/FunAudioLLM/Fun-ASR), [SenseVoice](https://github.com/FunAudioLLM/SenseVoice) |
| **Papers** | [2509.12508](https://arxiv.org/abs/2509.12508) (Fun-ASR), [2407.04051](https://arxiv.org/abs/2407.04051) (FunAudioLLM), [2401.04251](https://arxiv.org/abs/2401.04251) (SenseVoice) |
| **Why first** | Open weights; no STT subscription; ~170× GPU / ~17× CPU RTF in published tables; unified VAD+ASR+punctuation+diarization; SenseVoice emotion/event tags; ONNX/CPU/GPU/Windows SDK; OpenAI-compatible sidecar |

---

## Candidates — TTS and cloning (not integrated)

### CosyVoice 2 / 3 (Alibaba FunAudioLLM)

- **Repo:** [FunAudioLLM/CosyVoice](https://github.com/FunAudioLLM/CosyVoice)
- **Strength:** Zero-shot and cross-lingual **TTS**, voice cloning, streaming synthesis
- **Fit:** Natural **pair with FunASR** (same research line) for fully local ZH/EN voice agents
- **speech-mcp:** Future `provider=cosyvoice` or sidecar

### ChatTTS (2noise)

- **Repo:** [2noise/ChatTTS](https://github.com/2noise/ChatTTS)
- **Strength:** Conversational prosody — pauses, laughter, oral fillers — optimized for dialogue not audiobooks
- **Fit:** Assistant replies where “sounds human” matters more than broadcast clarity
- **speech-mcp:** Future expressive TTS provider

### GPT-SoVITS (v2/v3)

- **Repo:** [RVC-Boss/GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)
- **Strength:** Few-shot **voice cloning**; very strong Chinese and Japanese
- **Fit:** Local ElevenLabs-style cloning without cloud PVC
- **speech-mcp:** Future; see also [local_voice_alternatives.md](local_voice_alternatives.md)

### Fish Speech / OpenAudio

- **Repo:** [fishaudio/fish-speech](https://github.com/fishaudio/fish-speech)
- **Strength:** Open TTS and voice cloning with active community releases
- **Fit:** Alternative to CosyVoice for multilingual clone workflows
- **speech-mcp:** Not integrated; evaluate license and VRAM before fleet adoption

---

## Candidates — ASR alternatives (not integrated)

### FireRedASR (Xiaohongshu)

- **Repo:** [FireRedTeam/FireRedASR](https://github.com/FireRedTeam/FireRedASR)
- **Strength:** Industrial Mandarin/English ASR, competitive WER on open benchmarks
- **Why not default here:** FunASR already covers toolkit + MCP + sidecar + diarization pipeline in one fleet package

### WeNet (community)

- **Repo:** [wenet-e2e/wenet](https://github.com/wenet-e2e/wenet)
- **Strength:** Classic end-to-end ASR toolkit; strong Kaldi replacement lineage
- **Why not default here:** More assembly required for VAD/punc/speaker stack vs FunASR `AutoModel`

### Whisper / faster-whisper (OpenAI)

- **Role:** General multilingual baseline
- **In speech-mcp:** Not the default STT; FunASR preferred for Chinese industrial RTF and unified post-processing

---

## Fleet integration map

| Pattern | Provider | Status |
|---|---|---|
| **Local batch STT** | **FunASR** | **Done (default)** |
| Local duplex conversation | kyutai-mcp (Moshi) | [Separate repo](https://github.com/sandraschi/kyutai-mcp) |
| Cloud TTS / live | Gemini, Hume, ElevenLabs | Done |
| Wake word | openWakeWord | Done |
| Fleet voice commands | FunASR + fleet-agent router | Done ([VOICE_COMMAND_BUS.md](VOICE_COMMAND_BUS.md)) |
| Local cloning | GPT-SoVITS | Future |
| Local expressive TTS | ChatTTS / CosyVoice | Future |

---

## Reading order for maintainers

1. [HUMANOID_VOICE.md](HUMANOID_VOICE.md) — thesis: speech for humanoids, fleet architecture, China industrial speech
2. [providers/funasr.md](providers/funasr.md) — operate FunASR in speech-mcp today
3. [tools-reference.md](tools-reference.md) — MCP STT tool parameters
4. [configuration.md](configuration.md) — env vars
5. This file — roadmap and sibling Chinese FOSS projects

---

*Updated May 2026. FunASR integration is production-oriented beta; other rows are research/candidate unless marked Done.*
