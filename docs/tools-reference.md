# Speech-MCP Tools Reference

## v0.6.0 — May 2026

---

## Speech

### `text_to_speech`

Synthesize speech and **play it immediately on the PC speaker**.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `text` | str | required | Text to speak. Gemini supports inline audio tags: `[excited]`, `[whispers]`, `[laughs]`, `[sighs]`, `[fast]`, `[slow]` |
| `provider` | str | `"windows"` | TTS backend — see providers table below |
| `voice_id` | str | `"default"` | Voice name. Provider-specific — see below |
| `description` | str | None | **Hume only.** Prose style prompt, e.g. `"warm, slightly melancholic female voice"`. Drives Octave's expressive synthesis |

**Providers:**

| Provider | Key required | Voice options | Notes |
|---|---|---|---|
| `windows` | No | `"default"` only | Windows SAPI5, always available, robotic but instant |
| `hume` | `HUME_API_KEY` | Named: `ITO`, `KORA`, or omit for dynamic | Hume Octave REST. `description` drives prosody |
| `gemini` | `GOOGLE_API_KEY` | `Kore`, `Aoede`, `Charon`, `Fenrir`, `Orion`, `Puck`, `Leda`, `Zephyr` + 23 more | Gemini 3.1 Flash TTS (released 2026-04-15). Audio tags in text drive delivery |

**Returns:** `{"success": true, "provider": "...", "bytes_played": N, "status": "played"}`

**Examples:**
```
Say "Good evening" using the windows provider
Say "[cheerfully] Welcome! [whispers] This part is quiet." using gemini, voice Kore
Say "The reductionist universe..." using hume with description "warm, academic, slightly melancholic"
```

---

### `manage_voice_clones`

List or manage voice clones across providers.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `action` | str | required | `"list"`, `"create"`, `"delete"`, `"info"` |
| `provider` | str | `"hume"` | `"hume"` or `"elevenlabs"` |
| `name` | str | None | Name for new clone |
| `audio_path` | str | None | Local file path for cloning source |
| `voice_id` | str | None | Target voice ID for info/delete |

**Note:** `list` is fully implemented for both providers. `create`/`delete` are stubs.

---

## Agentic

### `start_evi_session`

Returns WebSocket connection parameters for a Hume EVI real-time session.
Requires `HUME_API_KEY`. `HUME_CONFIG_ID` must be set for a configured EVI persona.

### `detect_wake_word`

Arms Gemini Live VAD telemetry for a session. Returns activation configuration.

### `orchestrate_alexa_pattern`

Alexa 2.0-style mission orchestrator. Uses `ctx.sample()` to generate a
conversational strategy for a given `user_goal`.

| Parameter | Type | Description |
|---|---|---|
| `user_goal` | str | High-level objective for the session |

### `agentic_conversation_workflow`

SEP-1577 multi-step orchestrator. Elicits clarification if the goal is vague,
samples a strategy, and returns a structured mission plan.

| Parameter | Type | Description |
|---|---|---|
| `goal` | str | Objective for the conversational mission |

---

## RAG / Knowledge Base

### `search_docs`

Semantic vector search over the speech-mcp documentation corpus.
Uses LanceDB + FastEmbed (`BAAI/bge-small-en-v1.5`). Model downloads ~25 MB on first run.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | str | required | Natural language search query |
| `limit` | int | `5` | Max results |

**Returns:** List of `{filename, score, content}` chunks.

### `ask_docs`

RAG + LLM sampling. Retrieves relevant chunks then uses `ctx.sample()` to generate
a grounded answer. Requires sampling support in the MCP host (Claude Desktop: yes).

| Parameter | Type | Description |
|---|---|---|
| `question` | str | Natural language question |

**Returns:** `{answer, sources[]}` — answer grounded in indexed docs.

---

## Safety

### `safety_validate_intent`

Pattern-matches text against social-engineering triggers (money transfers,
impersonation, credential phishing, accident-bail scenarios).

| Parameter | Type | Description |
|---|---|---|
| `text` | str | Text to validate before synthesis |

**Returns:** `{safe: bool, risk_level: "LOW"|"HIGH"|"CRITICAL", reason?}`

### `safety_log_audit`

Writes a forensic log entry for high-intensity emotional speech.

| Parameter | Type | Description |
|---|---|---|
| `text` | str | Synthesized text |
| `provider` | str | Provider used |
| `emotional_intensity` | float | 0.0–1.0 |

### `safety_verify_auth`

Validates a bearer token against `SPEECH_MCP_AUTH_TOKEN` env var.

---

## Monitoring / IoT

### `trigger_action`

Proxy to Tapo smart home or UI notification bus.

| Parameter | Type | Description |
|---|---|---|
| `action_type` | str | `"light_on"`, `"light_off"`, `"notify"` |
| `params` | dict | `{"room": "living_room"}` or `{"message": "..."}` |

---

## Utility

### `manage_domestic_utility`

Alexa-pattern timer, alarm, and weather gateway.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `action` | str | required | `"set"`, `"cancel"`, `"query"` |
| `type` | str | required | `"timer"`, `"alarm"`, `"weather"` |
| `value` | str\|int | None | Seconds for timer, `"07:30"` for alarm, unused for weather |
| `label` | str | `"Default"` | Human-readable label; location name for weather queries |

Weather fetches live from wttr.in. Timers run as asyncio tasks and log on expiry.

---

## UI (Prefab Apps)

These tools render interactive inline UIs in Claude Desktop.

### `prosody_dashboard`

Dashboard showing current emotional vector, engine performance metrics, and
provider status. Uses `Metric`, `Badge`, `Row`, `Separator` components.

### `speech_activity_chart`

Bar chart of token usage across recent speech sessions. Uses `BarChart` +
`ChartSeries` from `prefab_ui.components.charts`.

---

## Wake Word

### `configure_local_wake_word`

Configures openWakeWord for local wake-word detection.
No API key required — runs fully offline.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `keyword` | str | `"computer"` | Built-in keyword: `"computer"`, `"jarvis"`, `"alexa"`, etc. |
| `sensitivity` | float | `0.5` | Detection sensitivity 0.0–1.0 |
