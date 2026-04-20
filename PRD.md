# PRD - Speech-MCP Multi-Provider Gateway

## 1. Goal
Create a unified, standard-compliant orchestration layer for the world's most advanced speech and voice AI APIs (Hume AI and ElevenLabs).

## 2. Requirements

### 2.1 Backend (MCP Server)
- **Multi-Provider Support**: Seamlessly switch between Hume, ElevenLabs, Gemini, and Gemma 4.
- **Local-First Sensing**: Native STT/TTS support via Gemma 4 to minimize cloud latency and exit the API dependency loop.
- **Prosody Awareness**: Ingest and preserve emotional vectors from audio streams for high-fidelity reasoning.
- **technical Compliance**: Use FastMCP 3.2+ with proper tool documentation and portmanteau patterns.
- **Streaming**: Support for streaming audio responses via WebSocket (EVI).
- **Security**: Robust management of provider API keys via environment variables.

### 2.2 Frontend (technical Webapp)
- **Aesthetics**: Premium dark-mode UI ("Midnight Empathy") with 60fps animations.
- **Dashboard**: Real-time emotional visualization (Hume) and high-fidelity playback.
- **Voice Management**: Unified UI for cloning identities across providers.
- **Self-Discovery**: Tools page with dynamic schema analysis.

## 3. Success Metrics
- Latency < 150ms for native local sensing (Tier 2).
- Zero translation loss in emotional prosody during synthesis.
- 100% compliance with **SOTA 14.1** agentic standards.

## 4. Roadmap
- **Phase 1**: Hume AI Baseline (Complete).
- **Phase 2**: ElevenLabs Integration (Complete).
- **Phase 3**: Local LLM & Native Multimodal (Complete — Gemma 4).
- **Phase 4**: World Labs Spatial Synchrony (In Progress).
- **Phase 5**: Robotics Integration (ROS 2/Yahboom).
