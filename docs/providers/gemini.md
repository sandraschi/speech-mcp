# Gemini 3.8 Flash TTS: Creative Voice Studio (3.1 legacy supported)

Gemini 3.8 Flash TTS is the cornerstone of the Project AG speech fleet. While other providers offer high fidelity, Gemini **wipes the floor** with the competition when it comes to raw **emotional intelligence and dynamic prosody**.

Models (Sept 2026, blog: `gemini-3-8-text-to-speech`):
- `gemini-3.8-flash-tts` (default) - creative direction, voice design, character voices
- `gemini-3.8-flash-lite-tts` - high-volume dubbing, voice agents, cost-efficient scale
- `gemini-3.1-flash-tts-preview` - legacy, backwards compat

Select via `text_to_speech(..., provider="gemini", model="gemini-3.8-flash-lite-tts")`,
`POST /api/v1/tts {"model": ...}`, `GET /api/v1/tts/wav?model=...`, or env `GEMINI_TTS_MODEL`.

---

## 🎭 The Power of Emotion
Unlike traditional TTS that requires complex SSML or separate "style" parameters, Gemini parses **Natural Language Emotion Tags** directly within your text stream. 3.8 adds `<laughs>/<sigh>/<gasp>` vocal bursts and `|mhm|/|yeah|` backchanneling plus line-by-line stage directions.

### Standard Emotional Tags
Simply wrap any segment in square brackets to shift the model's psychological state:

| Tag | Effect | Best Use Case |
| :--- | :--- | :--- |
| `[whispers]` | Lowers volume, increases breathiness | Secrets, intimacy, late-night utility |
| `[shouts]` | Increases volume and projection | Alarms, excitement, warnings |
| `[happy]` | Upward pitch inflections, faster tempo | Success, friendly greetings |
| `[sad]` | Downward pitch, slower, slightly tremulous | Error reports, empathy, condolences |
| `[serious]` | Flattened pitch, authoritative tone | Data readouts, security alerts |
| `[confused]` | Hesitant pacing, upward endings | Clarification requests, ambiguous goals |

**Example Tool Input:**
> `[happy] Welcome home, Sandra! [whispers] The system is running in silent mode for you.`

---

## 🎙️ Prebuilt Voices
Gemini provides 31 base voices plus 2,000+ 3.8 production voices (Mexican Spanish, Quebec French, Scots English, 100+ languages). Custom/saved 3.8 voices pass through as arbitrary `voice_id` strings.

Key voices include **Aoede** (warm, expressive), **Charon** (deep, authoritative), **Fenrir** (energetic), **Kore** (precise), **Orion** (friendly), and **Puck** (playful). See the full list at `docs/configuration.md`.

Voice replication (30s sample, consent-gated, SynthID + C2PA) must go through `CLONING_GUARDRAILS.md` - no silent cloning.

---

## ⚡ Advanced WebSocket Streaming (Barge-in)
The `speech-mcp` gateway utilizes the Gemini Multimodal Live API to provide ultra-low latency, interruptible streaming.

### Why this is Advanced:
1. **Native VAD**: The Gemini server detects when you start speaking and immediately halts its own generation. No "babbling" over the user.
2. **Bidirectional Proxy**: The gateway maintains a persistent connection, allowing for instant emotional shifts mid-sentence.
3. **Lip-Flap Sync**: The proxy extracts amplitude data in real-time and broadcasts it over OSC (port 9000) for high-fidelity avatar synchronization.

---

## 🛠️ Configuration
Ensure your `GOOGLE_API_KEY` is active in the `.env` file.

```bash
# Activation in agentic.py
await ctx.info("Arming Gemini Live VAD telemetry...")
# The system now listens for barge-in events automatically.
```
