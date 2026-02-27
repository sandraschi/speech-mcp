# Speech-MCP Tools Reference

## Implemented Tools (v0.2.1)

---

### `text_to_speech`

Synthesize speech via Hume AI, ElevenLabs, or Windows Local TTS.

**Parameters:**

| Name | Type | Default | Description |
|---|---|---|---|
| `text` | str | required | Text to synthesize |
| `voice_id` | str | `"ito"` | Voice identifier. `"ito"` or `"kora"` for Hume; ElevenLabs voice ID; `"default"` for Windows |
| `provider` | str | `"hume"` | TTS backend: `"hume"`, `"elevenlabs"`, or `"windows"` |
| `emotion` | str | None | Emotion hint for expressive synthesis: `"excited"`, `"calm"`, `"sad"` etc. |

**Returns:** `stream_url` (WebSocket) for audio consumption, plus provider info and recovery options.

**Example:**
```
Use text_to_speech to say "Good evening" in a calm tone using Hume
```

---

### `manage_domestic_utility`

Alexa-style domestic utility gateway: timers, alarms, and weather queries.

**Parameters:**

| Name | Type | Default | Description |
|---|---|---|---|
| `action` | str | required | `"set"`, `"cancel"`, or `"query"` |
| `type` | str | required | `"timer"`, `"alarm"`, or `"weather"` |
| `value` | str\|int | None | Duration in seconds for timers, or time string `"07:30"` for alarms |
| `label` | str | `"Default"` | Human-readable label for the utility |

**Example:**
```
Set a timer for 10 minutes labeled "pasta"
Cancel the pasta timer
Query all active timers
```

---

### `trigger_action`

Elicit physical effects via IoT bridge (Tapo smart lights) or trigger UI notifications.

**Parameters:**

| Name | Type | Default | Description |
|---|---|---|---|
| `action_type` | str | required | `"light_on"`, `"light_off"`, `"notify"` |
| `params` | dict | None | e.g. `{"room": "living_room"}` or `{"message": "Timer done!"}` |

**Example:**
```
Turn on the living room lights via trigger_action
```

---

### `search_docs`

Semantic search over the speech-mcp knowledge base (LanceDB + FastEmbed).

**Parameters:**

| Name | Type | Default | Description |
|---|---|---|---|
| `query` | str | required | Natural language search query |
| `limit` | int | `5` | Maximum results to return |

**Returns:** List of matching chunks with filename, relevance score, and content.

**Example:**
```
Search docs for "expressive voice cloning techniques"
```

---

### `ask_docs`

Ask complex questions using RAG retrieval + LLM sampling. Requires sampling capability in the MCP client.

**Parameters:**

| Name | Type | Default | Description |
|---|---|---|---|
| `question` | str | required | Natural language question |

**Returns:** Grounded answer text plus source filenames used.

**Example:**
```
Ask docs: what are the differences between Hume EVI and standard TTS?
```

---

## Under Construction (v0.3.0 Planned)

These tools are in the Antigravity IDE task backlog. They appear in `glama.json` as `under_construction` and are **not yet functional**.

| Tool | Description |
|---|---|
| `detect_wake_word` | Local wake-word detection ("Hey Edna") |
| `start_evi_session` | Bidirectional Hume EVI real-time audio session |
| `agentic_conversation_workflow` | Multi-turn conversation with TTS output per turn |
| `manage_voice_clones` | ElevenLabs voice clone library management |

Once implemented, speech-mcp becomes a full **Alexa-class** local AI voice assistant: wake word → live conversation → smart home control → expressive TTS response.
