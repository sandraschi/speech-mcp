# Project Wikipedia: Speech-MCP

| Attribute | Specification |
| :--- | :--- |
| **Project Name** | Speech-MCP (Multi-Provider Speech Gateway) |
| **Status** | ![Status: Beta](https://img.shields.io/badge/Status-Beta-orange) |
| **Standard** | ![FastMCP: 2.14.5](https://img.shields.io/badge/FastMCP-2.14.5-blue) |
| **Architecture** | Dual-Substrate (FastAPI + MCP SSE) |
| **Core AI** | Hume AI (EVI 2), ElevenLabs (PVC) |
| **Local Fallback** | `pyttsx3` (Windows Native) |
| **Orchestrator** | Antigravity IDE (Native) |

## 📖 Encyclopedia

### Agentic Cognitive Layer
A complex orchestration system using **FastMCP 2.14.5**. Unlike traditional TTS/STT bridges, Speech-MCP implements **Iterative Sampling** (SEP-1577) which allows the server to borrow the host LLM's reasoning to refine vocal prosody and conversational strategy.

### Dialogic Design
Every tool return is "Dialogic"—structured to guide an agent with `next_steps`. This eliminates the "dead-end" problem in tool execution.

### Alexa 2.0 Pattern
An industrial mission pattern defined in `arazzo.yaml`. It interleaves Voice Activity Projection (VAP) and Emotional Prosody Analysis to simulate near-human turn-taking dynamics.

## 🔗 Documentation Map

- **[Installation Guide](file:///D:/Dev/repos/speech-mcp/README.md)**
- **[Agentic Technical Specs](file:///D:/Dev/repos/speech-mcp/docs/AGENTIC_ORCHESTRATION.md)**
- **[DevOps & Release](file:///D:/Dev/repos/speech-mcp/docs/RELEASING.md)**
- **[ArXiv Research Notes](file:///D:/Dev/repos/speech-mcp/docs/CHINESE_AI_RESEARCH.md)**

---
*Verified for industrial use by Antigravity Agentic Systems (Februray 2026).*
