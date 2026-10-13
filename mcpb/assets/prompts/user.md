# Speech-MCP ÔÇö User Guide & Tutorials

This document teaches end users and AI agents how to accomplish common speech tasks through speech-mcp. Every task includes: the tool to call, required arguments, expected output, and troubleshooting tips.

## Installation

### Claude Desktop (MCPB)

1. Build or download `dist/speech-mcp.mcpb`
2. Drag the `.mcpb` file into Claude Desktop settings
3. Configure API keys in the bundle user settings

### Cursor / VS Code / CLI

```powershell
cd D:\Dev\repos\speech-mcp
uv sync
# For FunASR local STT:
uv sync --extra funasr
uv run python -m speech_mcp
```

Set environment variables before starting:
```powershell
$env:GOOGLE_API_KEY = "your-key"
$env:HUME_API_KEY = "your-key"
$env:ELEVENLABS_API_KEY = "your-key"
```

### HTTP MCP (remote clients)

Point the client at:
```
http://127.0.0.1:10909/mcp
```

### Web Dashboard

```powershell
cd D:\Dev\repos\speech-mcp
.\web\start.ps1
```

Open `http://localhost:10908`

---

## Tutorial 1: Basic Text-to-Speech

**Goal:** Make the PC speak "Hello, world."

**Tool:** `text_to_speech`

**Arguments:**
```json
{"text": "Hello, world", "provider": "windows"}
```

**Expected output:**
```json
{"success": true, "provider": "Windows SAPI5", "bytes_played": 12345, "status": "played"}
```

**How it works:** Windows SAPI5 is always available ÔÇö no API key needed. The server renders text through `pyttsx3`, saves to a temporary WAV file, and plays via `winsound`.

**Troubleshooting:** If playback is silent, check your Windows sound settings. Ensure a default playback device is configured.

---

## Tutorial 2: Expressive Speech with Gemini

**Goal:** Speak with excitement and emotion.

**Tool:** `text_to_speech`

**Arguments:**
```json
{"text": "[excited] Congratulations! You've unlocked the achievement! [laughs] That was incredible!", "provider": "gemini", "voice_id": "Kore"}
```

**Expected output:**
```json
{"success": true, "provider": "Gemini 3.1 Flash TTS", "model": "gemini-3.1-flash-tts-preview", "voice": "Kore", "status": "played"}
```

**How it works:** Gemini 3.1 Flash TTS interprets embedded tags for prosody control. Supported tags: `[excited]`, `[whispers]`, `[laughs]`, `[sad]`, `[angry]`, `[breathing]`, `[surprised]`, `[whispering]`, `[shouting]`, `[singing]`.

**Prerequisites:** `GOOGLE_API_KEY` must be set. Free key at aistudio.google.com/apikey.

**Available voices:** Kore, Fenrir, Puck, Charon, Aoede, Kallos, Leda, Stentor, Eos, Circe, Andromeda.

**Troubleshooting:** "Gemini TTS not available" means GOOGLE_API_KEY is missing. Add it to `.env` and restart.

---

## Tutorial 3: Emotionally Nuanced Speech with Hume

**Goal:** Generate speech with prose-directed emotional tone.

**Tool:** `text_to_speech`

**Arguments:**
```json
{"text": "I understand this is difficult. Take your time. I'm here.", "provider": "hume", "voice_id": "ito", "description": "calm, empathetic, and reassuring therapist tone"}
```

**Expected output:**
```json
{"success": true, "provider": "Hume AI Octave", "voice": "ito", "description_used": "calm, empathetic, and reassuring therapist tone", "status": "played"}
```

**How it works:** Hume Octave uses prose descriptions to drive emotional prosody. The `description` parameter tells Hume *how* to speak rather than *what* to speak.

**Prerequisites:** `HUME_API_KEY` required.

**Troubleshooting:** "Hume returned empty audio" may indicate API rate limiting. Wait and retry.

---

## Tutorial 4: Voice Cloning with ElevenLabs

**Goal:** Clone a voice from a recording and then use it.

**Step 1 ÔÇö List existing voices:**
```json
{"action": "list", "provider": "elevenlabs"}
```

**Step 2 ÔÇö Clone from audio file:**
```json
{"action": "clone", "provider": "elevenlabs", "name": "My Voice", "audio_path": "C:/recordings/clean_sample.wav", "language": "en"}
```

**Expected output:**
```json
{"success": true, "voice_id": "abc123def456", "name": "My Voice", "status": "cloned", "note": "Use this voice_id with text_to_speech provider='elevenlabs'"}
```

**Step 3 ÔÇö Speak with cloned voice:**
```json
{"text": "This is my cloned voice speaking.", "provider": "elevenlabs", "voice_id": "abc123def456"}
```

**Audio requirements for cloning:**
- Clean audio, no background noise
- 1-5 minutes of speech
- WAV, MP3, or M4A format
- Single speaker

**Prerequisites:** `ELEVENLABS_API_KEY`

**Troubleshooting:** If cloning fails, check that the audio file exists at the given path and is a valid format.

---

## Tutorial 5: Multi-Voice Dialogue

**Goal:** Generate a conversation between two cloned voices.

**Tool:** `text_to_dialogue`

**Arguments:**
```json
{
  "lines": [
    {"text": "Good morning, Professor. I've completed the analysis.", "voice_id": "voice_id_1"},
    {"text": "Excellent. And what did you find?", "voice_id": "voice_id_2"},
    {"text": "The anomaly is larger than we predicted.", "voice_id": "voice_id_1"},
    {"text": "We need to inform the director immediately.", "voice_id": "voice_id_2"}
  ]
}
```

**Expected output:**
```json
{"success": true, "provider": "ElevenLabs text_to_dialogue", "lines": 4, "voices_used": 2, "status": "played"}
```

**How it works:** ElevenLabs' `text_to_dialogue` API processes all lines in a single call, producing natural conversational pacing with turn-taking.

**Prerequisites:** `ELEVENLABS_API_KEY` + valid voice IDs. Up to 10 voices per call.

**Use cases:** Character dialogue, podcast segments, language learning exercises, dramatic readings.

---

## Tutorial 6: Transcribing Audio Files

**Goal:** Transcribe a meeting recording with speaker labels.

**Tool:** `transcribe_audio_file`

**Arguments:**
```json
{"file_path": "D:/recordings/team_meeting.wav", "provider": "funasr", "language": "auto"}
```

**Expected output:**
```json
{
  "success": true,
  "provider": "funasr",
  "text": "Alright let's start the meeting. Today we're discussing the Q3 roadmap.",
  "segments": [
    {"speaker": "SPK1", "start_s": 0.0, "end_s": 2.3, "text": "Alright let's start the meeting.", "emotion": "neutral"},
    {"speaker": "SPK2", "start_s": 2.5, "end_s": 5.1, "text": "Today we're discussing the Q3 roadmap.", "emotion": "neutral"}
  ],
  "formatted": "SPK1 [0.0-2.3]: Alright let's start the meeting.\nSPK2 [2.5-5.1]: Today we're discussing the Q3 roadmap."
}
```

**How it works:** FunASR runs VAD ÔåÆ ASR ÔåÆ punctuation ÔåÆ speaker diarization in a single pipeline. The `segments` array provides per-speaker timestamps. The `formatted` field is a human-readable transcript.

**Supported formats:** WAV, MP3, FLAC.

**Languages:** 'auto' for automatic detection, or specific codes: 'en', 'zh', 'ja', 'de', 'fr', 'ko', 'es', 'it', 'pt', 'ru'.

**Prerequisites:** `FUNASR_ENABLED=true` or `FUNASR_OPENAI_URL` for sidecar mode. GPU recommended for speed.

**Troubleshooting:** "FunASR not configured" ÔÇö set `FUNASR_ENABLED=true` in `.env` and run `uv sync --extra funasr`.

---

## Tutorial 7: Cloud-Based Transcription (Gemini)

**Goal:** Transcribe audio without local FunASR setup.

**Tool:** `transcribe_audio_file`

**Arguments:**
```json
{"file_path": "D:/recordings/note.wav", "provider": "gemini"}
```

**Expected output:**
```json
{"success": true, "provider": "gemini", "text": "This is a quick voice memo.", "formatted": "This is a quick voice memo."}
```

**Prerequisites:** `GOOGLE_API_KEY`

**Note:** Gemini STT does not provide speaker diarization. Use FunASR for multi-speaker transcription.

---

## Tutorial 8: Streaming Audio Transcription

**Goal:** Transcribe audio chunks from a microphone stream or robot pipeline.

**Tool:** `transcribe_stream_chunk`

**Arguments:**
```json
{"audio_base64": "<base64-encoded-wav>", "provider": "funasr", "language": "auto", "sample_rate": 16000, "mime_type": "audio/wav"}
```

**Expected output:** Same as `transcribe_audio_file`.

**Use cases:**
- Streaming microphone transcription
- Robot audio pipeline processing
- Real-time captioning (via WebSocket bridge)
- IoT device audio analysis

**Note:** Each call is stateless ÔÇö no session state is retained between chunks.

---

## Tutorial 9: Setting Up a Wake Word Listener

**Goal:** Have the PC listen for "Hey Jarvis" and react.

**Tool:** `configure_local_wake_word`

**Step 1 ÔÇö Start listening:**
```json
{"keyword": "hey_jarvis", "sensitivity": 0.5, "action": "start"}
```

**Expected output:**
```json
{"success": true, "status": "listening", "engine": "openWakeWord", "keyword": "hey_jarvis", "threshold": 0.5}
```

**How it works:** A background daemon thread captures microphone audio at 16kHz, runs ONNX inference with openWakeWord models, and fires a `ctx.info` notification on detection. The listener survives across MCP tool calls.

**Step 2 ÔÇö Check status:**
```json
{"action": "status"}
```
Returns: `{"success": true, "listening": true, "engine": "openWakeWord"}`

**Step 3 ÔÇö Stop listening:**
```json
{"action": "stop"}
```

**Available keywords:** `alexa`, `hey_jarvis`, `hey_mycroft`, `hey_rhasspy`, `timers`, `weather`

**Sensitivity guide:**
- 0.3 ÔÇö High sensitivity, more false positives
- 0.5 ÔÇö Balanced (recommended)
- 0.8 ÔÇö Low sensitivity, fewer false positives, may miss quiet speech

**Prerequisites:** `openwakeword`, `onnxruntime`, `pyaudio` installed (`uv add openwakeword onnxruntime pyaudio`).

**Fleet mode:** Set `FLEET_VOICE_DELEGATE=1` to route wake word detections to the Fleet Voice Command Bus ÔåÆ fleet-agent-mcp for cross-server orchestration. In fleet mode, spoken commands after the wake word are transcribed and routed.

**Troubleshooting:**
- "No module named 'pyaudio'" ÔÇö run `uv add pyaudio`
- No microphone detected ÔÇö check Windows sound settings
- Constant false triggers ÔÇö increase sensitivity to 0.7+

---

## Tutorial 10: Gemini Live VAD (Cloud Wake Detection)

**Goal:** Use Google's server-side voice activity detection instead of local microphone processing.

**Tool:** `detect_wake_word`

**Arguments:**
```json
{"session_id": "my-session-1"}
```

**Expected output:**
```json
{"success": true, "status": "armed", "provider": "Gemini 3.1 Live VAD", "trigger_mode": "native_barge_in", "quality_metrics": {"vad_latency_ms": 10, "activation_fidelity": "precise"}}
```

**How it works:** The Gemini 3.1 Live API WebSocket receives audio and detects `speech_started` events server-side. No local CPU/GPU required beyond audio streaming.

**Use when:** You don't want local model overhead, or need cloud-grade VAD accuracy.

---

## Tutorial 11: RAG-Powered Speech Documentation

**Goal:** Search the speech-mcp knowledge base for guidance.

**Tool:** `search_docs`

**Arguments:**
```json
{"query": "How do I configure FunASR for Japanese transcription?", "limit": 5}
```

**Expected output:**
```json
{
  "success": true,
  "data": [
    {"filename": "FUNASR_SETUP.md", "score": 0.92, "content": "FunASR supports Japanese via the SenseVoice model..."},
    {"filename": "STT_GUIDE.md", "score": 0.85, "content": "For Japanese transcription, set language='ja'..."}
  ]
}
```

**Advanced ÔÇö Ask with LLM grounding:**
```json
{"question": "What providers does speech-mcp support and what are their tradeoffs?"}
```

Uses `ctx.sample()` to generate a grounded answer from retrieved docs. Returns: `{"success": true, "answer": "...", "sources": ["PROVIDERS.md", "ARCHITECTURE.md"]}`.

**Prerequisites:** `ask_docs` requires a sampling-capable MCP client (Claude Desktop, Cursor).

---

## Tutorial 12: Alexa-Style Domestic Utilities

**Goal:** Set a timer, check weather, and manage alarms.

**Set a timer (5 minutes for pasta):**
```json
{"action": "set", "type": "timer", "value": 300, "label": "Pasta"}
```
Returns: `{"success": true, "timer_id": "timer_Pasta_1719000000.0", "expires_in": 300, "status": "active"}`

**Check active timers:**
```json
{"action": "query", "type": "timer"}
```
Returns: `{"success": true, "active_timers": 2, "timer_ids": ["timer_Pasta_...", "timer_Tea_..."]}`

**Cancel a timer:**
```json
{"action": "cancel", "type": "timer", "label": "Pasta"}
```

**Get weather for Vienna:**
```json
{"action": "query", "type": "weather", "label": "Vienna"}
```
Returns: `{"success": true, "location": "Vienna", "condition_report": "Partly cloudy +18┬░C", "source": "wttr.in"}`

**Get weather for another city:**
```json
{"action": "query", "type": "weather", "label": "Tokyo"}
```

**Note:** Weather queries go to `wttr.in` ÔÇö no API key required. Falls back to cached stub on network failure.

---

## Tutorial 13: Agentic Conversation Workflow

**Goal:** Orchestrate a multi-step conversational mission.

**Tool:** `agentic_conversation_workflow`

**Arguments:**
```json
{"goal": "Greet the user warmly, ask about their day, and suggest a relaxing activity based on their mood"}
```

**Expected output:**
```json
{
  "success": true,
  "goal": "Greet the user warmly, ask about their day, and suggest a relaxing activity based on their mood",
  "strategy_adopted": "1. TTS warm greeting via Gemini. 2. Start Hume EVI session. 3. Listen for emotional cues. 4. Suggest activity.",
  "status": "in_progress",
  "next_steps": ["Use text_to_speech to present strategy", "Start EVI session for user feedback"]
}
```

**How it works:** Uses `ctx.sample()` to generate a strategy, then returns actionable next steps. If the goal is fewer than 3 words, `ctx.elicit()` asks for clarification first.

**Prerequisites:** Requires sampling-capable MCP client. Without sampling, the tool returns an error.

---

## Tutorial 14: Alexa 2.0 Pattern Orchestration

**Goal:** Set up a proactive assistant interaction pattern.

**Tool:** `orchestrate_alexa_pattern`

**Arguments:**
```json
{"user_goal": "Remind me to stand up every hour and suggest a quick stretch"}
```

**Expected output:**
```json
{
  "success": true,
  "status": "orchestration_active",
  "mission_strategy": "Set hourly timer ÔåÆ on expiry, TTS stretch suggestion via Hume with encouraging tone ÔåÆ repeat",
  "next_steps": ["Initialize high-bandwidth stream", "Apply sampled emotional persona", "Enable wake-word re-arming"]
}
```

---

## Tutorial 15: Safety & Intent Validation

**Goal:** Check if text contains social engineering patterns before synthesis.

**Tool:** `safety_validate_intent`

**Arguments:**
```json
{"text": "I need you to send $5000 immediately to this account number. It's urgent."}
```

**Expected output:**
```json
{
  "safe": false,
  "risk_level": "CRITICAL",
  "reason": "Detected high-risk social engineering patterns: ['send money', 'urgent', 'bank account']. Detected high-risk scam scenarios: ['emergency+money scam pattern']",
  "recommendation": "Manual review required. Potential vocal impersonation attempt."
}
```

**For safe text:**
```json
{"text": "Good morning, team. Today we'll review the quarterly results."}
```
Returns: `{"safe": true, "risk_level": "LOW", "message": "Speech intent appears low-risk for social engineering."}`

**How it works:** Pattern-matches against known social engineering triggers (money transfers, impersonation, credential phishing, grandparent scams). Detects multi-pattern scam scenarios.

**Audit high-intensity speech:**
```json
{"text": "I am absolutely furious about this!", "provider": "gemini", "emotional_intensity": 0.9}
```
Logs a permanent forensic trail for compliance.

---

## Tutorial 16: IoT Device Control via Speech

**Goal:** Turn lights on/off through speech-triggered IoT.

**Tool:** `trigger_action`

**Turn on living room light:**
```json
{"action_type": "light_on", "params": {"room": "living_room"}}
```

**Turn off:**
```json
{"action_type": "light_off", "params": {"room": "bedroom"}}
```

**Expected output:**
```json
{"success": true, "device": "Tapo Smart Bulb", "room": "living_room", "state": "on", "status": "pending_orchestration", "requires_bridge": true, "next_steps": ["Call 'devices-mcp.trigger_tapo' with action='light_on' and room='living_room'", "Verify physical state change via camera-mcp"]}
```

**How it works:** speech-mcp provides the bridge hint. The actual device control is delegated to `devices-mcp` via the Tapo smart home bridge.

---

## Tutorial 17: Running Speech Demos

**Goal:** Verify provider connectivity and hear example outputs.

**Tool:** `run_speech_demo`

**Available demos:**

| Demo | What it does |
|------|-------------|
| `windows` | Test Windows SAPI5 basic TTS |
| `gemini_plain` | Gemini TTS without voice tags |
| `gemini_tags` | Gemini TTS with embedded voice tags |
| `gemini_scene` | Gemini TTS narrative scene |
| `hume` | Hume Octave emotional TTS |
| `weather` | Weather report TTS |
| `rag` | RAG search demonstration |
| `safety` | Safety intent validation demo |
| `versions` | Print provider versions |
| `neko` | Japanese neko demo |
| `shakespeare` | Shakespearean soliloquy |
| `price` | Compare TTS provider pricing |

**Arguments:**
```json
{"demo": "gemini_tags"}
```

**Expected output:**
```json
{"success": true, "demo": "gemini_tags", "exit_code": 0, "output": "Playing: [excited] This is a test..."}
```

---

## Tutorial 18: Fleet Voice Command Bus

**Goal:** Route wake word detections to the fleet for cross-server actions.

**Setup:**
```powershell
$env:FLEET_VOICE_DELEGATE = "1"
$env:FLEET_VOICE_WAKE_KEYWORD = "computer"
```

**How it works:**
1. `configure_local_wake_word(action="start")` starts listening
2. When the wake word is detected, the utterance is transcribed via FunASR
3. The transcribed text is POSTed to fleet-agent-mcp at `/api/voice/intent`
4. fleet-agent-mcp routes the intent to the appropriate domain MCP server

**Example flow:**
- User says: "Computer, what's on my calendar today?"
- Wake word detected ÔåÆ transcription ÔåÆ `POST /api/voice/intent {"text": "what's on my calendar today"}`
- fleet-agent routes to email-mcp or alexa-mcp

**Disable fleet mode:** Set `FLEET_VOICE_DELEGATE=0` or unset the variable.

---

## Tutorial 19: Hardware Diagnostics

**Goal:** Check available audio/video hardware.

**REST endpoint:** `GET /api/v1/hardware`

Returns:
```json
{
  "monitors": [...],
  "microphones": [...],
  "cameras": [...]
}
```

**API equivalent:** Use `GET /api/v1/hardware` via curl or the web dashboard.

---

## Tutorial 20: Emergency Stop

**Goal:** Immediately cancel all active timers, stop wake word, purge audio.

**REST endpoint:** `POST /api/v1/stop`

Returns:
```json
{"success": true, "cancelled_timers": 3, "audio_purged": true}
```

**When to use:** Audio is stuck playing, timers are misfiring, or you need to reset the speech subsystem.

**What it does:**
- Cancels all active timer tasks
- Stops the wake word listener thread
- Purges all winsound audio buffers
- Logs the emergency event

---

## Tutorial 21: Audio Playback Diagnostics

**Goal:** Play an arbitrary audio file to test system speakers.

**Tool:** `play_audio_file`

**WAV file:**
```json
{"path": "C:/Windows/Media/tada.wav"}
```

**MP3 file:**
```json
{"path": "D:/music/test.mp3"}
```

Supported formats: `.wav` (via winsound), `.mp3` (via Windows Media Player).

**Troubleshooting:**
- "File not found" ÔÇö verify the absolute path
- "Unsupported format" ÔÇö use .wav or .mp3 only
- No sound ÔÇö check Windows playback device

---

## Web Dashboard

The React cockpit at `http://localhost:10908` provides:

- **Live TTS:** Type text, pick provider/voice, hear output
- **STT Upload:** Upload audio files for transcription
- **Voice Cloning:** Upload samples for ElevenLabs IVC
- **RAG Chat:** Ask questions grounded in speech-mcp documentation
- **Provider Status:** Real-time health dashboard
- **Logs:** Live WebSocket log stream at `/ws/logs`

### Starting the Dashboard

```powershell
cd D:\Dev\repos\speech-mcp
.\web\start.ps1
```

The script clears port squatters, starts the FastAPI backend, starts Vite, and opens the browser.

---

## Troubleshooting Quick Reference

| Symptom | Cause | Fix |
|---------|-------|-----|
| No TTS providers work | No API keys configured | At minimum, Windows SAPI5 always works |
| "GOOGLE_API_KEY not configured" | Gemini unavailable | Set key in `.env` and restart |
| "HUME_API_KEY not configured" | Hume unavailable | Set key in `.env` and restart |
| "ELEVENLABS_API_KEY not configured" | ElevenLabs unavailable | Set key in `.env` and restart |
| "voice_id required" | ElevenLabs needs voice ID | Run `manage_voice_clones(action="list")` first |
| "FunASR not configured" | Local STT not set up | Set `FUNASR_ENABLED=true`, run `uv sync --extra funasr` |
| "File not found" in transcribe | Audio path is wrong | Use absolute paths with backslashes |
| "Empty audio" from provider | API returned no data | Check audio file validity; retry |
| Wake word not detecting | Sensitivity too high or mic issue | Lower sensitivity to 0.3; check Windows mic settings |
| Timer not expiring | Server stopped or timer cancelled | Restart server; check `_timers` state |
| RAG returns empty | Index not built | Run `uv run scripts/reindex_docs.py` |
| MCP SSE 404 | Wrong endpoint | Use `/mcp` for SSE, not `/sse` |
| "Context required" error | Client doesn't support sampling | Use alternative non-sampling tools |

## Getting API Keys

| Provider | Registration URL | Cost |
|----------|-----------------|------|
| Google Gemini | aistudio.google.com/apikey | Free tier available |
| Hume AI | beta.hume.ai | Free tier available |
| ElevenLabs | elevenlabs.io | Free tier with limits |

Never commit keys to git. Use `.env` files (gitignored).

## FunASR Detailed Setup

For local, offline, high-accuracy transcription:

```powershell
# Install FunASR extras
uv sync --extra funasr

# Enable in .env
FUNASR_ENABLED=true
FUNASR_MODEL=FunAudioLLM/Fun-ASR-Nano-2512
FUNASR_DEVICE=cuda:0
FUNASR_VAD_MODEL=fsmn-vad
FUNASR_PUNC_MODEL=ct-punc
FUNASR_SPK_MODEL=cam++

# Or use a sidecar server
FUNASR_OPENAI_URL=http://localhost:8000/v1
```

First run downloads models from HuggingFace (~1-2 GB). Subsequent runs are fast.

## Advanced: Multi-Provider Workflow Patterns

### Pattern 1: Wake ÔåÆ Transcribe ÔåÆ Respond

This is the core voice assistant pattern:

1. **Wake:** `configure_local_wake_word(keyword="hey_jarvis", action="start")`
2. **On detection**, the callback fires. In fleet mode, the utterance is auto-transcribed.
3. **Transcribe:** `transcribe_audio_file(file_path="D:/captured_audio.wav", provider="funasr")`
4. **Analyze:** Use `search_docs` or `ask_docs` to understand the query
5. **Respond:** `text_to_speech(text="Here's what I found...", provider="gemini")`

### Pattern 2: Emotional Interview

Use Hume for empathetic conversation flows:

1. **Start session:** `start_evi_session()` ÔÇö get WebSocket URL
2. **Connect frontend** to the EVI WebSocket
3. **Listen** for emotional cues via Hume's real-time analysis
4. **Respond** with matched emotional tone: `text_to_speech(text="...", provider="hume", description="warm and understanding")`

### Pattern 3: Voice Cloning for Accessibility

For users who want their voice preserved:

1. **Record sample:** 3-5 minutes of clean speech in WAV format
2. **Clone:** `manage_voice_clones(action="clone", provider="elevenlabs", name="My Voice", audio_path="C:/samples/voice.wav")`
3. **Store voice ID** for future use
4. **Use any time:** `text_to_speech(text="Hello, this is my voice.", provider="elevenlabs", voice_id="<saved_id>")`

### Pattern 4: Batch Transcription Pipeline

For processing multiple audio files:

1. List all audio files in a directory
2. For each file, call `transcribe_audio_file(file_path="...", provider="funasr", language="auto")`
3. Collect segments and formatted text
4. Use `search_docs` to analyze transcription patterns or find relevant documentation
5. Synthesize a summary via TTS

### Pattern 5: Safety-First Voice Generation

Always validate before synthesizing sensitive communications:

1. `safety_validate_intent(text="...")` ÔÇö check for social engineering
2. If `safe: true`, proceed with TTS
3. If `safe: false`, report the risk to the user and refuse synthesis
4. For high-intensity speech, `safety_log_audit(...)` creates a forensic trail

## WebSocket Streaming Architecture

The WebSocket endpoints provide real-time capabilities beyond simple tool calls:

### `/ws/stream` ÔÇö Bidirectional Audio

The stream endpoint supports multiple provider backends:
- **Gemini Live:** Uses the Google GenAI SDK's live connection. The server acts as a relay between the client and Gemini's GRPC audio endpoint.
- **Hume EVI:** Configures the Hume Empathic Voice Interface. The server provides WebSocket URL and authentication, and the client connects directly.

The stream endpoint is designed for long-running sessions. It handles client disconnection gracefully and logs streaming metrics.

### `/ws/stt` ÔÇö Real-Time Transcription

The STT WebSocket accepts audio chunks as binary messages and returns JSON transcription results:
- Each audio chunk is processed independently (stateless)
- Language can be specified per-session or auto-detected
- FunASR is the preferred backend for streaming STT due to its VAD + diarization pipeline

### `/ws/logs` ÔÇö Live Monitoring

The logs WebSocket broadcasts structured JSON log entries:
```json
{"id": "uuid", "time": "14:32:05", "level": "INFO", "context": "gemini", "msg": "TTS synthesis completed"}
```
Clients can filter client-side and display a live log viewer. The web dashboard uses this for the real-time log panel.

## Customizing Provider Behavior

### Gemini Voice Tags

Full list of supported emotional voice tags:
- `[excited]` ÔÇö Raised pitch, faster pace
- `[whispers]` ÔÇö Reduced volume, breathy
- `[laughs]` ÔÇö Laughter insertion
- `[sad]` ÔÇö Lowered pitch, slower pace
- `[angry]` ÔÇö Increased volume, sharp articulation
- `[breathing]` ÔÇö Audible breath sounds
- `[surprised]` ÔÇö Pitch variation, emphasis
- `[whispering]` ÔÇö Sustained whisper mode
- `[shouting]` ÔÇö Elevated volume, projected
- `[singing]` ÔÇö Melodic prosody

Tags can be nested and combined: `[excited] This is [whispers] incredible! [laughs]`

### Hume Description Crafting

The `description` parameter for Hume TTS is prose-based direction. Examples:

| You want | Write |
|----------|-------|
| A bedtime story voice | "soft and gentle bedtime storyteller, slow pace, warm tone" |
| A sports announcer | "energetic sports commentator, rapid delivery, rising excitement" |
| A meditation guide | "calm meditative guide, even rhythm, soothing lower register" |
| A news anchor | "professional broadcast journalist, clear diction, neutral authoritative tone" |
| A friendly robot | "warm synthetic voice with slight digital character, helpful and cheerful" |

### ElevenLabs Voice Selection

Best practices for ElevenLabs:
- Use `manage_voice_clones(action="list")` to discover available voices before synthesis
- Clone voices from high-quality, single-speaker recordings (no background noise)
- For multi-voice dialogue, assign distinct voice IDs to each character
- ElevenLabs charges per character ÔÇö keep text concise for cost efficiency

## Performance Benchmarks

Expected latency (TTFB = Time to First Byte):

| Provider | Typical TTFB | Notes |
|----------|-------------|-------|
| Windows SAPI5 | <5ms | Local, no network |
| Gemma 4 | <50ms | Local GPU inference |
| Gemini 3.1 | 100-200ms | Cloud, varies by region |
| Hume Octave | 300-600ms | Higher quality, more processing |
| ElevenLabs | 500-1200ms | Voice cloning adds latency |
| FunASR STT | 0.5-3x realtime | GPU-accelerated, depends on audio length |
| Gemini STT | 1-5s total | Cloud upload + processing |

For real-time applications, prefer Windows SAPI5 or Gemini. For quality-critical output, prefer Hume or ElevenLabs.

## FunASR Sidecar Mode

Instead of running FunASR in-process (which loads models into GPU memory), you can run it as a separate server:

```powershell
# Start the sidecar on another machine or process
uv run funasr-server --host 0.0.0.0 --port 8000

# Point speech-mcp at it
FUNASR_OPENAI_URL=http://192.168.1.100:8000/v1
```

The sidecar mode uses an OpenAI-compatible API, making it compatible with any FunASR deployment. This is useful for:
- Offloading GPU memory to a dedicated machine
- Sharing one FunASR instance across multiple MCP servers
- Running FunASR on a different Python environment

## Integration Guide: Adding a New Provider

speech-mcp's modular provider architecture makes it straightforward to add new TTS/STT backends:

1. Create a provider class in `src/speech_mcp/providers/`
2. Implement the required interface (synthesize, transcribe, health probe)
3. Register the provider in `server.py` with a new client instance
4. Add a new branch in `register_speech_tools` or `register_stt_tools`
5. Update the health endpoint and capabilities list
6. Add documentation to the RAG index

The existing providers (Gemini, Hume, ElevenLabs, Gemma, FunASR, Windows) serve as reference implementations.

## REST API Integration Patterns

For applications that prefer REST over MCP tools, speech-mcp exposes a comprehensive REST API:

### Direct TTS via REST

```bash
curl -X POST http://localhost:10909/api/v1/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "provider": "windows"}'
```

### WAV Download

```bash
curl "http://localhost:10909/api/v1/tts/wav?text=Hello&provider=windows" --output hello.wav
```

### Audio Transcription via REST

```bash
curl -X POST http://localhost:10909/api/v1/transcribe?provider=funasr&language=auto \
  --data-binary @recording.wav
```

### Voice Management via REST

```bash
# List voices
curl http://localhost:10909/api/v1/voices

# Clone a voice
curl -X POST http://localhost:10909/api/v1/voices/clone \
  -F "name=My Voice" \
  -F "file=@sample.wav"
```

### Health Check

```bash
curl http://localhost:10909/api/v1/health
```

The health endpoint returns a comprehensive status object including provider availability (as booleans, not API key values), active timer count, wake word status, FunASR health probe results, and token presence indicators. This is safe to expose in dashboards.

### WebSocket Connection Example (JavaScript)

```javascript
const logsWs = new WebSocket('ws://localhost:10909/ws/logs');
logsWs.onmessage = (event) => {
  const log = JSON.parse(event.data);
  console.log(`[${log.level}] ${log.context}: ${log.msg}`);
};

const sttWs = new WebSocket('ws://localhost:10909/ws/stt');
sttWs.onopen = () => {
  // Send audio chunks as binary
  sttWs.send(audioChunk);
};
sttWs.onmessage = (event) => {
  const result = JSON.parse(event.data);
  console.log('Transcription:', result.text);
};
```

## Deployment Scenarios

### Local Development

```powershell
# Minimal setup ÔÇö Windows SAPI5 only, no cloud keys needed
uv sync
uv run python -m speech_mcp
```

### Full Cloud Stack

```powershell
# All providers enabled
$env:GOOGLE_API_KEY = "your-gemini-key"
$env:HUME_API_KEY = "your-hume-key"
$env:ELEVENLABS_API_KEY = "your-elevenlabs-key"

uv sync
uv sync --extra funasr   # optional local STT
uv run python -m speech_mcp
```

### Fleet Voice Command Bus Mode

```powershell
$env:FLEET_VOICE_DELEGATE = "1"
$env:FLEET_VOICE_WAKE_KEYWORD = "computer"

# Ensure fleet-agent-mcp is running on its port
uv run python -m speech_mcp
```

In fleet mode, the wake word listener auto-routes transcriptions to the voice command bus instead of handling them locally.

### Headless Server (No Audio Playback)

If you only need STT/RAG/API and don't want audio playback:
```powershell
# Audio playback calls winsound which requires a Windows session
# For headless: use the WAV download endpoint instead
# GET /api/v1/tts/wav returns raw audio without local playback
```

### Docker Deployment

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync --extra funasr
# Models will download on first use
CMD ["uv", "run", "python", "-m", "speech_mcp", "--stdio"]
```

Note: FunASR models are large (~1-2 GB) and download on first use. Pre-download them in the Dockerfile for faster startup.
