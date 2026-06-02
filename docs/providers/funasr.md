# FunASR — Alibaba Tongyi Local Speech Recognition

> **Why this matters:** Chinese open-weight speech AI is firing on all thrusters. FunASR ships industrial-grade ASR with open weights, arXiv-backed benchmarks, ModelScope/HuggingFace hubs, edge variants from 234M to 7.7B, and **no subscription tax**. speech-mcp integrates it as the default local STT backend.
>
> **Humanoids & fleet:** [HUMANOID_VOICE.md](../HUMANOID_VOICE.md) — why local STT + Voice Command Bus matter for embodied agents.

---

## The stack (three layers, one ecosystem)

| Layer | Repo | Role |
|---|---|---|
| **Toolkit** | [modelscope/FunASR](https://github.com/modelscope/FunASR) (~16k★) | Training, export, ONNX runtime, Docker SDKs, `funasr-server` CLI, MCP server (v1.3.3+) |
| **Foundation models** | [FunAudioLLM/Fun-ASR](https://github.com/FunAudioLLM/Fun-ASR) | LLM-integrated ASR — Nano (0.8B) and full (7.7B) |
| **Voice understanding** | [FunAudioLLM/SenseVoice](https://github.com/FunAudioLLM/SenseVoice) (~8k★) | ASR + emotion + audio events + LID in one non-autoregressive pass |

All three are Tongyi / Alibaba DAMO Academy lineage. Code is MIT; **model weights** use the [FunASR Model License Agreement](https://github.com/modelscope/FunASR/blob/main/MODEL_LICENSE) (review before commercial redistribution).

---

## Papers (read these)

| Paper | arXiv | What it covers |
|---|---|---|
| **Fun-ASR Technical Report** | [2509.12508](https://arxiv.org/abs/2509.12508) | LLM-ASR architecture, tens-of-millions-of-hours training, RL (FunRL/GRPO), industry benchmarks, streaming, noise robustness, code-switching, hotword RAG |
| **FunAudioLLM** | [2407.04051](https://arxiv.org/abs/2407.04051) | SenseVoice + CosyVoice family — multilingual ASR, emotion, audio events, voice generation |

Key claim from the Fun-ASR report: open benchmarks can mislead — models that look SOTA on Librispeech/AISHELL often collapse on **real industry sets** (noisy far-field, dialect, lyrics, hiphop). Fun-ASR-nano (0.8B) tracks close to closed Seed-ASR on those harder sets while staying fully open-weight.

---

## Model zoo — pick your hardware

### End-to-end LLM-ASR (recommended for accuracy)

| Model | Params | Hub ID | Best for |
|---|---|---|---|
| **Fun-ASR-Nano-2512** | ~800M | `FunAudioLLM/Fun-ASR-Nano-2512` | Default — 31 languages, dialects, low latency, diarization pipeline |
| **Fun-ASR-MLT-Nano** | ~800M | `FunAudioLLM/Fun-ASR-MLT-Nano-2512` | Explicit 31-language multilingual variant |
| **Fun-ASR** (full) | ~7.7B | `FunAudioLLM/Fun-ASR` | Maximum accuracy when VRAM allows |
| **SenseVoiceSmall** | 234M | `iic/SenseVoiceSmall` | Edge / CPU-friendly — ASR + **emotion tags** + audio event detection |

### Pipeline components (mix-and-match)

| Component | Model | Params | Task |
|---|---|---|---|
| VAD | `fsmn-vad` | 0.4M | Voice activity segmentation |
| ASR | `paraformer-zh` / `paraformer-en` | 220M | Non-autoregressive streaming/batch |
| Punctuation | `ct-punc` | 290M | Punctuation restoration |
| Diarization | `cam++` | 7.2M | Speaker embedding / labels |
| KWS | `fsmn-kws` | 0.7M | Keyword spotting (streaming) |

FunASR's value proposition: **one `AutoModel()` call** wires VAD → ASR → punctuation → speakers instead of juggling four Whisper-adjacent services.

---

## Benchmarks (from arXiv 2509.12508)

### Open-source test sets (WER %, lower is better)

| Test set | Whisper-large-v3 | Fun-ASR-nano | Fun-ASR (7.7B) |
|---|---|---|---|
| AISHELL-1 | 4.72 | 1.80 | 1.22 |
| Librispeech-clean | 1.86 | 1.76 | 1.51 |
| Librispeech-other | 3.43 | 4.33 | 3.03 |
| WenetSpeech Meeting | 18.39 | 6.60 | 6.17 |

### Industry evaluation sets (WER % — where it actually hurts)

| Scenario | Whisper-v3 | Fun-ASR-nano | Fun-ASR |
|---|---|---|---|
| Nearfield | 16.58 | 7.79 | 6.31 |
| Farfield | 22.21 | 5.79 | 4.34 |
| Complex background | 32.57 | 14.59 | 11.45 |
| Dialect | 66.14 | 28.18 | **15.21** |
| Lyrics | 54.82 | 30.85 | 21.00 |
| **Average** | 33.39 | 16.72 | **12.70** |

Whisper still wins some clean English benches; Fun-ASR wins **messy real-world** — exactly what agent fleets transcribe (meetings, robots, field recordings).

### Speed (community + official claims)

| Engine | Typical RTF (GPU) | Typical RTF (CPU) |
|---|---|---|
| Whisper-large-v3 | ~13× realtime | ~1–2× |
| SenseVoiceSmall | ~15×+ | strong |
| Fun-ASR-nano | up to **170×** | ~**17×** |

RTF = audio_duration / compute_time. Higher is faster. Agent loops care because STT blocking = orchestration stalls.

---

## Edge & deployment matrix

Different hardware → different artifact, **same API surface**:

| Target | Format | How | Notes |
|---|---|---|---|
| **GPU workstation** | PyTorch | `FUNASR_DEVICE=cuda:0` native in speech-mcp | Best throughput |
| **CPU / airgapped** | PyTorch | `FUNASR_DEVICE=cpu` | Viable for clips; SenseVoiceSmall preferred |
| **INT8 ONNX** | ONNX | `funasr.export.export_model --quantize True` | ~4× memory reduction |
| **C++ low-latency** | ONNX runtime | `funasr-onnx-offline-rtf` binaries | Industrial batch |
| **Windows SDK** | CPU ONNX | FunASR runtime SDK 2.0+ | Offline Mandarin/English file + realtime |
| **Mobile / ARM** | sherpa-onnx INT8 | Pre-built SenseVoice / Nano ONNX | Android APK patterns exist |
| **Sidecar service** | HTTP | `funasr-server --port 10910` | OpenAI `/v1/audio/transcriptions` drop-in |
| **Docker** | CPU/GPU images | `funasr-runtime-sdk-cpu` / `-gpu` | Ports 10095–10098 |

Community ONNX exports: [csukuangfj/FunASR-nano-onnx](https://huggingface.co/csukuangfj/FunASR-nano-onnx) (encoder + LLM split, INT8 variants).

---

## vs. the usual suspects

| | FunASR (local) | Whisper (local) | Cloud STT (Google/Azure) |
|---|---|---|---|
| **Cost** | Hardware only | Hardware only | Per-minute subscription |
| **Privacy** | Fully offline | Fully offline | Data leaves device |
| **Diarization + punctuation** | Built into pipeline | Needs add-ons | Varies |
| **Emotion / events** | SenseVoice native | No | Rare |
| **Chinese dialects** | Strong (7 dialects, 26 accents on Nano) | Weak | Good but $$ |
| **Agent integration** | MCP tools + OpenAI sidecar + native FunASR MCP (v1.3.3) | DIY | API key + rate limits |
| **Open weights** | Yes | Yes | No |

---

## speech-mcp integration

### Quick enable (native GPU)

```powershell
cd D:\Dev\repos\speech-mcp
uv sync --extra funasr
```

`.env`:

```env
FUNASR_ENABLED=true
FUNASR_MODEL=FunAudioLLM/Fun-ASR-Nano-2512
FUNASR_DEVICE=cuda:0
FUNASR_HUB=hf
```

### Sidecar (shared fleet service)

```powershell
uv sync --extra funasr
uv run python scripts/start_funasr_sidecar.py
# or: funasr-server --model FunAudioLLM/Fun-ASR-Nano-2512 --device cuda:0 --port 10910
```

`.env`:

```env
FUNASR_OPENAI_URL=http://127.0.0.1:10910/v1
```

Port **10910** is fleet-safe (avoids forbidden 8000).

### MCP tools

| Tool | Purpose |
|---|---|
| `transcribe_audio_file` | Batch — files, meetings, podcasts |
| `transcribe_stream_chunk` | Stateless chunks from mic/robot bridges |

Default provider is `funasr`. Override with `provider=gemini` or `provider=gemma`.

**Example agent prompts:**

```
Transcribe D:/recordings/standup.wav
Transcribe C:/audio/interview.mp3 with language ja
```

**Structured return:**

```json
{
  "success": true,
  "provider": "funasr",
  "text": "full transcript",
  "segments": [
    {"speaker": 0, "start_s": 0.12, "end_s": 3.45, "text": "...", "emotion": "neutral"}
  ],
  "formatted": "[00.12s -> 03.45s] [Speaker 0] (neutral): ..."
}
```

### REST

```http
POST /api/v1/transcribe?provider=funasr&language=auto
Content-Type: application/octet-stream

<raw audio bytes>
```

---

## Configuration reference

| Variable | Default | Description |
|---|---|---|
| `FUNASR_ENABLED` | `false` | Native in-process inference |
| `FUNASR_OPENAI_URL` | — | Sidecar base URL (e.g. `http://127.0.0.1:10910/v1`) |
| `FUNASR_MODEL` | `FunAudioLLM/Fun-ASR-Nano-2512` | Hub model ID |
| `FUNASR_DEVICE` | `cuda:0` | `cuda:0`, `cpu`, `mps` |
| `FUNASR_HUB` | `hf` | `hf` (HuggingFace) or `ms` (ModelScope) |
| `FUNASR_VAD_MODEL` | `fsmn-vad` | VAD sub-model |
| `FUNASR_PUNC_MODEL` | `ct-punc` | Punctuation sub-model |
| `FUNASR_SPK_MODEL` | `cam++` | Speaker diarization sub-model |

Set `FUNASR_SPK_MODEL=` empty to disable diarization and save VRAM.

---

## Ecosystem links

| Resource | URL |
|---|---|
| FunASR toolkit | https://github.com/modelscope/FunASR |
| Fun-ASR models | https://github.com/FunAudioLLM/Fun-ASR |
| SenseVoice | https://github.com/FunAudioLLM/SenseVoice |
| FunAudioLLM demos | https://funaudiollm.github.io/ |
| Agent integration guide | https://modelscope.github.io/FunASR/agent.html |
| OpenAI API example | https://github.com/modelscope/FunASR/tree/main/examples/openai_api |
| ModelScope hub | https://modelscope.cn/models/FunAudioLLM/Fun-ASR-Nano-2512 |

---

## Comparison with kyutai-mcp (fleet neighbor)

| | FunASR (speech-mcp) | kyutai-mcp |
|---|---|---|
| Task | Batch + chunk **transcription** | Full-duplex **conversation** |
| Engine | FunASR unified pipeline | Moshi |
| Output | Timestamps, speakers, punctuation, emotion | Real-time dialogue |
| Ports | 10909 (speech-mcp backend) | 10924–10926 |
| Subscription | None | None |

Both run simultaneously. Use FunASR when agents need **accurate transcripts**; use kyutai-mcp when you need **live voice chat** offline.

---

## Citation

```bibtex
@misc{an2025funasrtechnicalreport,
  title={Fun-ASR Technical Report},
  author={Keyu An and Yanni Chen and Zhigao Chen and others},
  year={2025},
  eprint={2509.12508},
  archivePrefix={arXiv},
  primaryClass={cs.CL},
  url={https://arxiv.org/abs/2509.12508}
}
```

```bibtex
@article{funaudiollm2024,
  title={FunAudioLLM: Voice Understanding and Generation Foundation Models},
  author={FunAudioLLM Team},
  journal={arXiv preprint arXiv:2407.04051},
  year={2024}
}
```

---

*Integrated in speech-mcp v0.6+. See also [CHINESE_AI_RESEARCH.md](../CHINESE_AI_RESEARCH.md) for the broader Chinese speech ecosystem (CosyVoice, ChatTTS, GPT-SoVITS).*
