# Agentic Orchestration Guide (FastMCP 3.2.4)

This document details the advanced cognitive orchestration layer of Speech-MCP, leveraging the **FastMCP 3.2.4** standards (May 2026).

> [!IMPORTANT]
> **Antigravity Extension Layer**: While compliant with standard MCP, Speech-MCP is optimized for the **Antigravity Extension Layer**, allowing for seamless multi-turn cognitive loops and autonomous sampling refinement.

## 🧠 Core Agentic Standards

### 1. Dialogic Tool Returns
Tools in Speech-MCP do not return flat data. They return **Dialogic Structures** designed to guide the calling agent toward the mission goal.

**Key Metadata**:
- `status`: Categorical state (e.g., `ready`, `waiting_on_input`).
- `next_steps`: Actionable follow-up suggestions for the agent.
- `recovery_options`: Self-healing paths in case of failure.
- `quality_metrics`: Empirical data about the synthesis/session quality.

### 2. SEP-1577 Sampling
We implement the **Sampling Protocol**, allowing tools to "glom on" to the host LLM's reasoning power.

**Workflow**:
1. Agent calls a tool (e.g., `agentic_conversation_workflow`).
2. The tool uses `ctx.sample()` to ask the host LLM for strategy refinement.
3. The tool executes based on the sampled intelligence.
4. The tool returns `requires_sampling: true`, signaling to Antigravity that an iterative cognitive cycle is in progress.

## 🔬 Advanced Dialogic Patterns (ArXiv Research 2026)

Based on recent studies (e.g., *The Role of Prosodic and Lexical Cues in Turn-Taking*), Speech-MCP leverages the following advanced "tricks":

### 1. Voice Activity Projection (VAP)
Instead of relying on simple silent-segment detection (VAD), we implement (or simulate via Hume EVI) VAP-style turn-taking. 
- **The Trick**: Scaling the synthesis delay based on the **Emotional Prosody** of the user's closing sentence. A "high-energy" unfinished thought prevents the agent from interrupting, even if lexical cues suggest a stop.

### 2. Lexical-Prosodic Fallback
Agents should prioritize **Prosodic Cues** (emotional tone) over **Lexical content** when ambiguity exists. 
- **The Trick**: If a user says "Stop" but with a playful, high-energy tone, the agent might interpret it as a mock-protest and continue the empathic loop (Social Mimicry).

### 3. Kinematic Prosodic Boundaries
Predicting the end of a turn by analyzing the **micro-latency** and **pitch-bend** at sentence terminals.

---

## 💻 Integration Examples

### Python Agentic Client
[agentic_client.py](file:///D:/Dev/repos/speech-mcp/examples/agentic_client.py)
> Demonstrates how a Python agent can consume Dialogic returns and orchestrate a multi-turn mission using the `stdio` transport.

### Webapp Consumption (TypeScript)
[webapp_consumption.ts](file:///D:/Dev/repos/speech-mcp/examples/webapp_consumption.ts)
> Illustrates the "Proactive Orchestration" pattern for Advanced web interfaces on port 10908.

---

## 📈 Roadmap (v0.6.0+)
- **Alexa 2.0 Pattern**: Interleaved VAD-driven listening and responding with near-zero latency.
- **Cognitive Persistence**: Cross-session memory for agentic speech missions.
- **Local LLM Glomming**: Direct orchestration with Ollama-hosted models for sub-100ms reasoning.
