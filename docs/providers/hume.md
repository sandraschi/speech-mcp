# Hume AI EVI: Empathic Voice Interface

Hume AI provides the fleet's **empathic feedback loop**. While Gemini focuses on performance-driven emotion, Hume specializes in **detecting and responding** to the user's emotional state in real-time.

---

## 👂 EVI v3 Integration
Hume is integrated via the Empathic Voice Interface (EVI) protocol, allowing for low-latency, emotionally-aware conversations.

### Key Capabilities:
1. **Prosody Tracking**: Measures 50+ emotional nuances in the user's voice (e.g., anxiety, boredom, triumph).
2. **Dynamic Adaptation**: The model shifts its own tone to match or complement the user's emotional vector.
3. **Interrupt Handling**: Native support for conversational overlap.

---

## 🛠️ Usage in Speech-MCP
Hume is typically engaged for **long-form discovery** or **affective monitoring** where the user's emotional state is critical (e.g., therapeutic or coaching agents).

### Integration Tools:
- `start_evi_session`: Initializes a persistent WebSocket connection.
- `orchestrate_alexa_pattern`: Uses Hume's emotional analysis to decide the next tool sequence.

---

## ⚡ Performance vs. Gemini
| Feature | Hume EVI | Gemini 3.1 |
| :--- | :--- | :--- |
| **Primary Strength** | User Empathy Detection | Emotional Performance (TTS) |
| **Latency** | ~250ms (Round-trip) | ~140ms (TTFB) |
| **Customization** | Configuration IDs | Natural Language Tags |
| **Native VAD** | Yes | Yes (Higher fidelity) |

---

## ⚙️ Configuration
Requires `HUME_API_KEY` and an optional `HUME_CONFIG_ID`.

```python
# Deployment
res = await start_evi_session(ctx)
# The frontend connects to the returned websocket_url via our stream proxy.
```
