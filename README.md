# Speech-MCP (Multi-Provider Speech Gateway)

SOTA-grade MCP server and web application for industrial voice orchestration, supporting Hume AI (EVI/Octave) and ElevenLabs.

## 🚀 Overview

Speech-MCP is a federated gateway for advanced voice AI. It provides a unified MCP interface for text-to-speech, real-time empathic voice sessions, and high-fidelity voice cloning.

## 🛠️ Key Capabilities

- **Hume AI Integration**:
    - **EVI 2/3**: Real-time empathic voice interface with prosody-driven responses.
    - **Octave TTS**: Emotionally aware text-to-speech.
- **ElevenLabs Integration** (Roadmap/Alpha):
    - **Professional Voice Cloning (PVC)**: State-of-the-art neural cloning.
    - **Multilingual TTS**: Support for 32+ languages with emotional nuances.
- **SOTA Webapp**: A premium dark-mode interface with glassmorphism, emotion visualizers, and neural dynamic tracking.

## 📦 Deployment & Setup

### Ports
- **Backend (MCP)**: `10760`
- **Frontend (Web)**: `10761`

### Environment Variables
Create a `.env` file in the root:
```env
HUME_API_KEY=your_hume_key
HUME_CONFIG_ID=your_evi_config_id
ELEVENLABS_API_KEY=your_eleven_key
```

### Installation
```powershell
# Backend
pip install -e .
python -m speech_mcp.server

# Frontend
cd web
npm install
npm run dev
```

## 🧩 MCP Tools

- `text_to_speech`: Synthesize audio across providers.
- `start_evi_session`: Initialize real-time Hume sessions.
- `manage_voice_clones`: Unified identity management (Create/List/Delete).

## ⚖️ Standards

- **FastMCP 2.14.4+**: SOTA compliance.
- **Portmanteau Pattern**: Consolidated tool schema to prevent tool explosion.
- **Midnight Empathy UI**: Premium dark-mode aesthetics.
