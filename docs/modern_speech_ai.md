# Modern Speech AI & Advanced Research (2025-2026)

## The Architectural Shift: From Pipeline to Native Audio

Traditional voice AI stacks three sequential stages: Speech-to-Text → LLM → Text-to-Speech. Each hop adds latency (typically 1–3 seconds total) and loses prosodic information — the model reasons on text, not on how something was said.

The 2025–2026 generation collapses this into **native audio-to-audio** models that process raw PCM directly, reason on acoustic features (tone, pace, emotion), and synthesise speech without an intermediate text representation. This is the architecture behind Gemini Live, Hume EVI, and OpenAI Realtime API.

## The Dual-Track Landscape

Speech AI has split into two distinct product categories:

**High-expressiveness batch TTS** — Request/response, highest quality, rich emotional control. Use for narration, character voices, Creative Labs-style demos. Examples: `gemini-3.1-flash-tts-preview` (audio tags, 100+ languages), ElevenLabs v3, Hume Octave.

**Real-time full-duplex conversation** — Persistent WebSocket, sub-second latency, barge-in, affective response. Use for voice assistants, robot control, live demos. Examples: `gemini-3.1-flash-live-preview`, Hume EVI, OpenAI Realtime API.

Speech-MCP implements both tracks. See [gemini_live.md](gemini_live.md) for the real-time implementation.

## Gemini Live API (2025–2026)

Google's native audio conversation model. Key progression:

- `gemini-2.0-flash-exp` (2025) — initial multimodal live preview, raw PCM, limited voices
- `gemini-live-2.5-flash-native-audio` (late 2025) — stable native audio, 30 HD voices, 24 languages, affective dialog
- `gemini-3.1-flash-live-preview` (March 2026, current) — lowest latency, `thinkingLevel` tuning, improved multilingual VAD, 128k context

The critical engineering distinction: the model processes raw 16-bit PCM natively. There is no internal STT step — the model reasons acoustically. This is why it can detect emotional tone, pick up on hesitation, and respond to prosodic cues that text transcription would discard.

Audio specs: 16kHz int16 mono input, 24kHz int16 mono output. Session max: 10 minutes.

## Hume AI

**EVI (Empathic Voice Interface)** — Full-duplex conversation model that optimises for human emotional wellbeing. Uses an "Empathic Large Language Model" (eLLM) trained to be sensitive to emotional expression in voice. The voice is dynamically generated to match the conversation context rather than being a fixed voice identity.

**Octave (TTS)** — Batch synthesis with `description` parameter: provide a prose style prompt ("warm, scholarly, slightly melancholic") rather than selecting from preset voices. Produces highly consistent character voices.

## ElevenLabs

Strongest offering for voice identity. Instant Voice Clone (IVC) creates a cloned voice from as little as 5 seconds of audio. The cloned voice is available immediately via API. `text_to_dialogue` enables multi-voice scenes with natural conversational pacing in a single API call.

## Chinese AI (2025-2026)

Several efficient, open models for on-device or self-hosted deployment:

- **SenseVoice** (Alibaba) — fast multilingual STT with emotion recognition
- **CosyVoice 2** — zero-shot voice cloning, runs on consumer GPU
- **GPT-SoVITS v3** — zero-shot cloning framework, strong for Japanese and Chinese; community-trained models for many voices
- **ChatTTS** — optimised for conversational naturalness including filler words

These are relevant for the Yahboom robot use case where cloud API latency is unacceptable and offline operation is required.

## Dialogic Patterns

**Barge-in** — User speech interrupts model output mid-sentence. The model stops generating, flushes its audio buffer, and processes the new input. Implemented in Gemini Live via `server_content.interrupted`.

**Backchanneling** — Brief vocal acknowledgements ("mm-hmm", "right") while the user is speaking. Signals active listening without taking the floor. EVI does this natively; Gemini Live does not currently.

**Affective dialog** — The model adapts its response style (pace, warmth, directness) to match the user's detected emotional state. `gemini-3.1-flash-live-preview` with `thinkingLevel` above minimal.

**Proactive audio** (preview) — Model only responds when addressed; ignores ambient conversation. Relevant for always-on robot or ambient assistant deployments.

## Robot Voice Integration

Native audio models are well-suited for robot control because they can process voice commands without an STT step, making the response path shorter and more robust to acoustic variability. The Yahboom integration pattern (see `docs/YAHBOOM_RASPBOT_VOICE.md`) uses Gemini Live as the brain and routes model responses to robot actuators via `yahboom-mcp`.
