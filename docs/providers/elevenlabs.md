# ElevenLabs: High-Fidelity Professional Synthesis

ElevenLabs represents the fleet's **gold standard for raw audio fidelity**. While Gemini leads in dynamic emotion, ElevenLabs provides the most stable and high-bandwidth vocal clones for professional use cases.

---

## 💎 Professional Voice Cloning (PVC)
The `speech-mcp` gateway supports ElevenLabs PVC, allowing for near-indistinguishable clones of specific individuals.

### Key Models:
- **Turbo v2.5**: The lowest latency model, ideal for real-time conversation.
- **Multilingual v2**: High-quality cross-lingual synthesis with consistent voice identity.

---

## ⚡ Latency vs. Quality Trade-offs
| Feature | Turbo v2.5 | Multilingual v2 |
| :--- | :--- | :--- |
| **End-to-end Latency** | ~180-300ms | ~600-900ms |
| **Audio Fidelity** | High (44.1kHz) | Ultra High (48kHz) |
| **Stability** | Very High | Elite |
| **Use Case** | Real-time agents | Long-form narration |

---

## 🛠️ Usage in Speech-MCP
ElevenLabs acts as the "Premium" fallback or primary engine for well-defined agent personalities.

### Tools:
- `text_to_speech(provider='elevenlabs', voice_id='...')`: Triggers an ElevenLabs synthesis stream.

---

## ⚡ Contrast with Gemini 3.1
| Feature | ElevenLabs | Gemini 3.1 |
| :--- | :--- | :--- |
| **Emotional Control** | Manual (Stability/Similarity) | **SOTA (NL Tags)** |
| **Cloning** | Professional (requires 30min audio) | Prebuilt (Adaptive) |
| **Cost** | Usage-based (Quota) | Integrated (Fleet) |

---

## ⚙️ Configuration
Requires `ELEVENLABS_API_KEY`. 

```python
# To use a specific clone:
voice_id = "your_pvc_id_here"
await text_to_speech(text="SOTA fidelity secured.", provider="elevenlabs", voice_id=voice_id)
```
