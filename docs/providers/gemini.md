# Gemini 3.1 Flash TTS: SOTA Emotional Synthesis

Gemini 3.1 Flash TTS is the cornerstone of the Project AG speech fleet. While other providers offer high fidelity, Gemini **wipes the floor** with the competition when it comes to raw **emotional intelligence and dynamic prosody**.

---

## 🎭 The Power of Emotion
Unlike traditional TTS that requires complex SSML or separate "style" parameters, Gemini 3.1 parses **Natural Language Emotion Tags** directly within your text stream. This allows for extremely granular, context-aware performance.

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
Gemini 3.1 provides six high-fidelity voices, each with a distinct personality:

1. **Aoede**: Warm, balanced, and highly expressive. The default recommendation for agents.
2. **Charon**: Deep, authoritative, and steady. Ideal for monitoring and security.
3. **Fenrir**: Energetic and bright. Perfect for creative tasks or gaming integrations.
4. **Kore**: Sophisticated and precise. Best for technical data and analysis.
5. **Orion**: Friendly and approachable. Good for general consumer-facing tasks.
6. **Puck**: Playful and slightly mischievous. Great for "Assistant" personalities.

---

## ⚡ SOTA WebSocket Streaming (Barge-in)
The `speech-mcp` gateway utilizes the Gemini Multimodal Live API to provide ultra-low latency, interruptible streaming.

### Why this is SOTA:
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
