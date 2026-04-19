# Gemini Live API — Real-Time Voice Chat in Speech-MCP

## What it is

Gemini Live is Google's full-duplex, low-latency voice conversation API. Unlike the batch TTS pipeline (`gemini-3.1-flash-tts-preview`), it maintains a persistent WebSocket session where audio streams in both directions simultaneously. The model listens, understands, and speaks without the traditional STT → LLM → TTS latency stack.

Current model: **`gemini-3.1-flash-live-preview`**

Key capabilities:
- Sub-second response latency (no STT/TTS pipeline — native audio-to-audio)
- Barge-in / interruption: user can speak while model is talking
- Affective dialog: model adapts tone to user's emotional expression
- Input and output transcripts available alongside audio
- 24 languages supported
- Tool/function calling mid-conversation (synchronous)
- 10-minute session limit (reconnect to continue)

Audio format: input raw 16-bit PCM at 16kHz mono; output raw 16-bit PCM at 24kHz mono.

---

## Architecture in Speech-MCP

```
Browser (VoiceChat page)
    │
    │  WS binary:  raw 16kHz PCM (mic)
    │  WS text:    { type: "text"|"end_turn"|"interrupt" }
    ▼
/ws/stream?provider=gemini_live&voice=Kore&system=...
    │  (speech_mcp/streaming.py — _handle_gemini_live)
    │
    ├── browser_to_gemini():
    │     binary frames → session.send_realtime_input(audio=Blob(..., "audio/pcm;rate=16000"))
    │     text "text"  → session.send_realtime_input(text=...)
    │     text "end_turn" → session.send_realtime_input(audio_stream_end=True)
    │
    └── gemini_to_browser():
          PCM chunks → wrap in WAV headers → send_bytes to browser
          transcripts → send_text JSON
          interrupted → send_text JSON
          turn_complete → send_text JSON
    │
    ▼
client.aio.live.connect(model="gemini-3.1-flash-live-preview", config=LiveConnectConfig)
    │  (google-genai SDK, GOOGLE_API_KEY)
    ▼
Gemini Live API (Google)
```

The backend acts as a secure proxy — the API key never reaches the browser.

PCM chunks from Gemini are wrapped in WAV headers before forwarding because the browser's `AudioContext.decodeAudioData()` cannot decode raw PCM. The WAV wrapping is minimal overhead (44-byte header per chunk).

---

## VoiceChat Page

Located at `web/src/components/VoiceChat.tsx`. Accessible via the **Voice Chat** sidebar item.

### Mic pipeline

```
getUserMedia({ channelCount: 1, echoCancellation: true, noiseSuppression: true })
    │
    └── ScriptProcessor (bufferSize=4096, 48kHz)
            │  onaudioprocess
            └── resampleAndEncode(float32, 48kHz → int16, 16kHz)
                    │
                    └── ws.send(int16.buffer)  — binary frame
```

`ScriptProcessor` is deprecated in favour of `AudioWorklet` but remains universally supported without needing additional worker files. A future migration to `AudioWorklet` would reduce main-thread pressure for long sessions.

### Audio playback pipeline

```
ws.onmessage (ArrayBuffer)
    │
    └── AudioContext.decodeAudioData(wavBytes)
            │
            └── BufferSourceNode.start(nextPlayTime)
                    nextPlayTime += audioBuffer.duration
                    (gapless sequential scheduling)
```

Chunks are scheduled back-to-back using a monotonic `nextPlayTime` reference, producing gapless playback even across multiple chunks per model turn.

### Browser messages sent to backend

| Frame type | Content | Meaning |
|---|---|---|
| binary | Raw int16 PCM, 16kHz | Mic audio chunk |
| text JSON | `{ type: "text", text: "..." }` | Inject text as user turn |
| text JSON | `{ type: "end_turn" }` | Signal end of user audio stream |
| text JSON | `{ type: "interrupt" }` | Client-side barge-in signal |

### Browser messages received from backend

| Frame type | Content | Meaning |
|---|---|---|
| binary | WAV bytes (24kHz) | Model audio chunk — play immediately |
| text JSON | `{ type: "session_ready", voice, model }` | Session established |
| text JSON | `{ type: "transcript", role: "user"\|"model", text }` | Speech transcript |
| text JSON | `{ type: "turn_complete" }` | Model finished speaking |
| text JSON | `{ type: "interrupted" }` | Server-side barge-in — flush playback buffer |
| text JSON | `{ type: "error", message }` | Error from Gemini or backend |

---

## Configuration

Required in `.env`:
```
GOOGLE_API_KEY=your-key   # free at https://aistudio.google.com/apikey
```

Optional URL parameters on the WebSocket:
```
provider=gemini_live     (required — selects this handler)
voice=Kore               (any Gemini Live voice name, default: Kore)
system=You are...        (system instruction / persona, URL-encoded)
token=...                (SPEECH_MCP_AUTH_TOKEN if set)
```

---

## Voices

Gemini Live uses the same prebuilt voice catalogue as the TTS model.
Voices available in VoiceChat UI: Aoede, Charon, Fenrir, Kore, Orion, Puck, Leda, Orus, Zephyr.

The native audio model (`gemini-3.1-flash-live-preview`) uses a different synthesis engine than the batch TTS model (`gemini-3.1-flash-tts-preview`). Voice quality is very good but not identical — the live model optimises for latency over maximum expressiveness.

---

## Comparison: Live API vs Batch TTS

| | Gemini Live (`gemini-3.1-flash-live-preview`) | Batch TTS (`gemini-3.1-flash-tts-preview`) |
|---|---|---|
| Latency | Sub-second (streaming) | 1–3s round-trip |
| Quality | Very good | Highest |
| Emotion tags | No (prosody is implicit) | Yes (`[whispers]`, `[excited]`, etc.) |
| Multilingual | Yes (24 languages) | Yes (100+ languages) |
| Interruption | Yes (barge-in) | No |
| Use case | Conversation, robot control | Narration, Creative Labs, demos |
| Session state | Stateful (10 min max) | Stateless |
| Context window | 128k tokens | Per-request |

---

## Robot Integration (Yahboom / yahboom-mcp)

The intended bridge pattern for real-time robot voice control:

```
Robot STT (Yahboom CI1302 or ROS2 ASR)
    │ text
    ▼
yahboom-mcp bridge
    │ WS text frame: { type: "text", text: "..." }
    ▼
VoiceChat /ws/stream session (or direct backend WS)
    │ model audio (WAV chunks)
    ▼
yahboom-mcp bridge
    │ audio → robot TTS module or PC speaker
    ▼
Robot speaker
```

The bridge can also listen for `transcript` frames (model text output) and route commands to robot actuators (movement, lights, camera) via the existing yahboom-mcp tool set.

See `docs/YAHBOOM_RASPBOT_VOICE.md` for hardware details.

---

## Known Limitations

- **10-minute session limit**: Gemini Live sessions hard-cap at 10 minutes. Reconnect and optionally re-seed context. Speech-MCP does not currently implement automatic reconnection — this is a planned improvement.
- **ScriptProcessor deprecation**: The mic pipeline uses the deprecated `ScriptProcessor` API. Works in all current browsers but will eventually need migration to `AudioWorklet`.
- **No video input**: Only audio is streamed to the Live API. Video/screen-share input is not implemented.
- **System prompt locked at session start**: Cannot be changed mid-session; end and restart to change persona.
- **English-primary VAD**: Gemini's built-in VAD performs best with English. Other languages work but may have slightly higher false-end-of-turn rates.
