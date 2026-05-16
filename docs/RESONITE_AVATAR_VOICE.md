# speech-mcp + Resonite: Voice for Avatars and Bots

**Status**: Design / Partial — OSC bridge not yet implemented  
**Date**: 2026-05-16  
**Related**: `deepfang/docs/RESONITE_COUNCIL_AGENT.md`, `deepfang/docs/WORLDLABS_RESONITE_INTEGRATION.md`

---

## The Vision

A Resonite avatar — whether it's your VRoid-based social avatar, a DeepFang council member vbot, or a robot stand-in (Unitree G1 shape) — speaks with a real synthesized voice driven by speech-mcp, not the flat robotic output of a script.

When the DeepFang council session produces a synthesis and routes it to the embodied Resonite adjudicator, that avatar's mouth moves and a Hume AI expressive voice comes out of its position in the 3D world. Other users in the Resonite session hear it spatially — louder when nearby, quieter when far.

This is not a gimmick. Embodied voice is cognitively different from text-in-a-panel. It anchors the agent as a presence.

---

## Architecture

```
DeepFang Council Session
        │
        ▼ adjudicator response text
council_tts_bridge.py
        │
        ▼ calls speech-mcp text_to_speech tool
speech-mcp MCP server
        │
        ▼ returns stream_url: ws://localhost:10909/ws/stream?provider=hume&voice=ito
Audio Stream Consumer (bridge script)
        │
        ├── Option A: Play locally via Windows audio (speaker output)
        │             → Resonite picks it up via mic if you're in VR headset
        │
        └── Option B: Route to Resonite via OSC audio trigger
                      → /resonite/avatar/speak  payload: audio_url or base64 PCM
                      → Resonite ProtoFlux plays clip at avatar position
```

Option A (local playback) works today with zero additional tooling — speech-mcp synthesizes, Windows plays it, if Resonite is open with audio routing the avatar appears to speak.

Option B (proper spatial audio in Resonite world) requires a small OSC bridge not yet built.

---

## Option A: Local Playback — Works Now

When the webapp is running and you have a script consuming the WebSocket stream, audio plays locally. For desktop Resonite sessions where you're not in VR, this is sufficient — the voice comes from your speakers while the avatar is on screen.

Quick test (Python, no additional deps beyond `websockets`):

```python
import asyncio
import websockets
import pyaudio

async def play_speech_stream(stream_url: str):
    """Consume speech-mcp WebSocket stream and play via local audio."""
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16, channels=1, rate=22050, output=True)
    
    async with websockets.connect(stream_url) as ws:
        async for chunk in ws:
            if isinstance(chunk, bytes):
                stream.write(chunk)
    
    stream.stop_stream()
    stream.close()
    pa.terminate()

# Use after calling text_to_speech tool
asyncio.run(play_speech_stream("ws://localhost:10909/ws/stream?provider=hume&voice=ito"))
```

> Note: The WebSocket stream provides audio forwarding for Hume and ElevenLabs TTS. For Gemini Live streaming, use the `/ws/stream` endpoint with the appropriate provider parameter.

---

## Option B: OSC Audio Bridge (Roadmap)

Resonite supports audio playback via ProtoFlux using audio clip assets. The bridge would:

1. Receive synthesized PCM from speech-mcp WebSocket
2. Encode to WAV/OGG and save to a temp URL (local HTTP server or file share)
3. Send OSC message to Resonite with the audio URL and avatar target
4. Resonite ProtoFlux loads and plays at avatar spatial position

```
OSC message to Resonite:
Address: /deepfang/avatar/speak
Arguments:
  avatar_id: str   — which avatar/slot should play
  audio_url: str   — http://localhost:PORT/temp/speech_XXXXXXXX.wav
  text: str        — lip-sync hint (if avatar has viseme system)
```

ProtoFlux setup on the Resonite side (sketch):

```
OSC Input → String[0] = avatar_id, String[1] = audio_url
    │
    ▼
Find world slot by avatar_id
    │
    ▼
HTTP Fetch audio_url → AudioClip asset
    │
    ▼
AudioOutput component at avatar position → Play()
    │
    ▼ (optional, if viseme system present)
Viseme driver → parse text for phoneme timing
```

---

## Voice Assignment per Avatar Type

Different Resonite avatar roles should have distinct voices to signal their function:

| Avatar Role | Recommended Provider | Voice | Why |
|---|---|---|---|
| Your main social avatar | Hume EVI | `kora` | Expressive, warm, conversational |
| DeepFang council Synthesizer | Hume Octave | `ito` | Authoritative, clear |
| Council Adversary vbot | ElevenLabs | Custom clone | Distinct, slightly edgy |
| Robot avatar (Unitree G1) | Windows TTS | `default` | Deliberately mechanical — it's a robot |
| Sensor agent (robohoover) | None / beep | — | It has no voice, just data readouts |

This is configured in the `council_tts_bridge.py` voice map (see `OPENCLAW_DEEPFANG_INTEGRATION.md`).

---

## VRoid Studio Integration

If you've built avatars in VRoid Studio and imported them to Resonite, they typically have blend shape bones for facial expressions. Full lip-sync would need a viseme system in Resonite ProtoFlux, driven by phoneme data from the TTS provider.

Hume AI's EVI v3 returns prosody and emotion data alongside audio — this is the right foundation for expressive avatar facial animation if the ProtoFlux viseme system is wired up. ElevenLabs similarly supports phoneme timing output.

This is a proper project (ProtoFlux viseme driver + speech-mcp phoneme relay) — but the audio layer described above is the prerequisite and is the simpler first step.

---

## Council of Dozens: Multi-Voice Debates in Resonite

The most compelling near-term use: run a DeepFang council debate while in a Resonite session, with each adjudicator's contribution synthesized in a distinct voice and played spatially from different positions in the world.

Rough layout:
- 12 avatar positions arranged in a circle (the "council chamber")
- Each position bound to an adjudicator identity and a voice
- When a round completes, the bridge script plays each contribution sequentially from its avatar's position
- You (or other human participants) sit in the center and listen to the debate

This is less sci-fi than it sounds — it's a structured audio experience, not real-time. The council runs, produces a debate record, and the record is then performed in the Resonite world as a spatial audio playback.

---

## What Needs Building

| Component | Effort | Status |
|---|---|---|
| `play_speech_stream.py` local audio consumer | 1 day | Not started |
| speech-mcp WebSocket full TTS streaming | 2-3 days | Placeholder in v0.2.x |
| `council_tts_bridge.py` (DeepFang → speech-mcp) | 1 day | Not started |
| OSC audio bridge to Resonite | 2-3 days | Design only |
| Resonite ProtoFlux audio player ProtoFlux | 1 day (in-world) | Not started |
| Full lip-sync / viseme system | 1-2 weeks | Long-term goal |

The local playback path is realistic in a day once the WebSocket streaming is fully wired in speech-mcp. The OSC path is a week of work but produces the genuinely spatial result.
