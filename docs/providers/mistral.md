# Mistral Voxtral 3 provider

Speech-to-text and text-to-speech through Mistral's Voxtral 3 family, either on
Mistral's hosted API or against a self-hosted vLLM server.

- Provider id: `mistral`
- Env: `MISTRAL_ENABLED=true` plus either `MISTRAL_API_KEY` (hosted) or
  `MISTRAL_SELF_HOST_URL` (local)
- Source: `src/speech_mcp/providers/mistral.py`
- Registered in `transcribe_audio_file(provider="mistral")`,
  `text_to_speech(provider="mistral")` and `synthesize_to_file(provider="mistral")`

## What it adds over the other providers

| Capability | Why it matters here |
|---|---|
| **Context biasing** | Pass keyphrases (`FastMCP`, repo names, tool names, people) so recognition stops mangling fleet vocabulary. No fine-tuning, hosted only. |
| **Diarization** | Speaker-labelled segments with timestamps in one request. |
| **Native end-of-turn** | Realtime sessions emit `turn.start` / `turn.eager_end` / `turn.resume` / `turn.end`, so a voice loop stops on semantic turn end instead of an energy threshold. |
| **35+ TTS languages, 50+ dialects** | A second multilingual voice option next to Gemini and ElevenLabs. |

## Two lanes, two behaviours

### Hosted (`MISTRAL_API_KEY`)

```
MISTRAL_ENABLED=true
MISTRAL_API_KEY=...
MISTRAL_STT_MODEL=voxtral-small-latest            # highest accuracy
MISTRAL_REALTIME_MODEL=voxtral-mini-transcribe-realtime-3
MISTRAL_TTS_MODEL=voxtral-mini-tts-3
```

Batch, realtime and TTS all work, including diarization and `context_bias`.

Cost reference (Mistral price list, 2026-10-20): batch Mini $0.0035/min,
batch Small $0.0040/min, realtime $0.008/min ($0.48/hr), TTS $13 per 1M chars.

**Do not point an always-listening loop at the realtime endpoint.** At
$0.008/min that is roughly $350/month. Keep wake-word detection local
(openWakeWord) and open a Voxtral session only for the utterance after wake.

### Self-hosted (`MISTRAL_SELF_HOST_URL`)

```
MISTRAL_ENABLED=true
MISTRAL_SELF_HOST_URL=http://127.0.0.1:8010
```

Serve `mistralai/Voxtral-Mini-4B-Realtime-2602` (Apache-2.0) with vLLM:

```
vllm serve mistralai/Voxtral-Mini-4B-Realtime-2602 --port 8010
```

In this mode the provider omits `diarize` and `context_bias`, because the local
route does not document those fields and a rejected request is worse than a
missing feature. The realtime URL derives `ws://` from the same base.

### Licensing - read before self-hosting TTS

| Model | Licence | Usable here |
|---|---|---|
| `Voxtral-Mini-4B-Realtime-2602` | Apache-2.0 | Yes, self-host freely |
| `Voxtral-Mini-3B-2507`, `Voxtral-Small-24B-2507` | Apache-2.0 | Yes (Voxtral 2 generation) |
| `Voxtral-4B-TTS-2603` | **CC-BY-NC-4.0** | **No** - non-commercial; speech-mcp is MIT and ship-embeddable |
| Voxtral Small Transcribe 3 | not published | Hosted / on-prem via Mistral |

The provider therefore never loads TTS weights in-process. Hosted TTS, or your
own licensed server via `MISTRAL_TTS_BASE_URL`, are the supported paths.

## Realtime session rules

Two documented constraints are enforced in code rather than left to the server:

1. **Diarization and turn detection are mutually exclusive.** Asking for both
   raises `ValueError` locally. Pick `turn_detection` for a voice loop, or
   `diarize=True` for a labelled transcript.
2. **Threshold ordering.** `start_threshold >= eager_end_threshold >
   end_threshold` and `end_timeout_ms >= min_silence_ms`, validated before the
   socket opens (settings are frozen once audio starts).

Text lags turn events. On `turn.eager_end` it is safe to start preparing a
reply; act only on `turn.end`, and keep appending deltas until the streaming
delay has passed.

## Verification status

- Unit tests: `tests/test_mistral_provider.py` (16 tests) assert the exact
  multipart fields, timestamp normalization, error mapping, TTS body, and the
  realtime `session.update` payload against a fake transport.
- **Not yet verified against the live API**: no `MISTRAL_API_KEY` on this
  machine at build time. The first live check should confirm the batch model id,
  the segment field spellings, and that `/v1/audio/speech` accepts
  `response_format="wav"` (the reference lists it, but the playground examples
  omit it).
