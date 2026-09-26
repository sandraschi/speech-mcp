# Local Voice Offline - What Shipped 2026-09-26

Fritz can now talk and listen with zero cloud. This doc records what was
built, the honest numbers, and what is still scaffold.

## Providers (new)

| Provider | Role | State | Key |
|---|---|---|---|
| `qwen` | Qwen3-TTS 0.6B local TTS | Scaffold - endpoint works, in-process wiring pending | `QWEN_TTS_URL` or `qwen-tts` extra |
| `kokoro` | Kokoro 82M local TTS (Apache, CPU) | **Working, verified** | `kokoro` extra + espeak-ng binary |
| `gemma` | Gemma 4 native audio | Stub (STT raises, TTS falls back SAPI5) - README says so | None |

Chain for offline speech: `qwen -> kokoro -> windows SAPI5`.
Cloud stays available: `gemini` (3.8 Flash/Lite), `hume`, `elevenlabs`.

Enable: `uv sync --extra kokoro` (+ `winget install espeak-ng` on Windows),
then `text_to_speech("hi", provider="kokoro")`.

## Confirm gate (new)

`voice_confirms` table + 3 MCP tools for spoken readback on
irreversible/external actions:

- `voice_confirm_request(action, summary)` -> `{id, readback}` - speak readback via TTS
- `voice_confirm_resolve(id, yes/no)` - only `confirmed` may execute (ja/nein accepted)
- `voice_confirm_list()` - pending queue for Hub/Inbox, 300 s TTL, audit trail

## Speaker tag

`post_speech_intent` payload carries `speaker` (kwarg or `FLEET_VOICE_SPEAKER`
env, empty = unidentified). Fritz routes to `memory_user:<id>`.
Backward compatible - `voice_listener.py` call sites unchanged.

## ZH streaming

`zh` resolves to the `ja` multilingual weights (model covers zh) - no second
download. `SHERPA_ASR_LANG=zh` works after downloading `ja` once:

```powershell
uv run python scripts/download_sherpa_models.py ja
```

## Bench (measured 2026-09-26, Goliath CPU streaming)

Harness: `scripts/bench_stt_roundtrip.py` - kokoro speaks known text,
sherpa streaming transcribes chunked, WER scored. No cherry-picking.

| Lang | WER | Note |
|---|---|---|
| en | 0.286 / 0.111 / 0.300 | Real pipeline number. Errors are endpoint cutoffs (trailing words) + token splits (TO MORROW). Tuning headroom: endpoint rules, chunk size. |
| de | 0.714 / 1.000 | TTS-limited (kokoro is English-native), NOT a de-model score. Native DE audio needed. |
| zh | plumbing only | Recognizer builds on shared ja dir, silence -> empty, no crash. No reference audio yet. |

Kokoro proof: `synthesize_wav("Hello Fritz...")` -> 134 KB wav, offline.
Suite: 52 passed, 6 skipped (`pytest -m "not live"`). Ruff clean.

## Still open

1. Qwen-TTS in-process wiring (needs weight vendoring) - endpoint path works.
2. Native DE/ZH reference audio for true model scores.
3. Endpoint-rule tuning to fix trailing-word cutoffs (biggest EN WER driver).
4. Fritz-side voice-loop e2e (other repo).
