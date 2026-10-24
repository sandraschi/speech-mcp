import asyncio
import base64
import io
import json
import logging
import os
import tempfile
import wave
from typing import Any

import anyio
from elevenlabs.client import ElevenLabs
from fastapi import WebSocket, WebSocketDisconnect
from pythonosc import udp_client

logger = logging.getLogger(__name__)

# OSC client for lip-flap (VRChat / Avatar protocol)
osc_client = udp_client.SimpleUDPClient("127.0.0.1", 9000)


def calculate_amplitude(audio_b64: str) -> float:
    """Calculate normalized amplitude from base64 PCM data."""
    try:
        raw_bytes = base64.b64decode(audio_b64)
        if len(raw_bytes) < 2:
            return 0.0
        import numpy as np

        samples = np.frombuffer(raw_bytes, dtype=np.int16)
        if len(samples) == 0:
            return 0.0
        return float(np.abs(samples).mean() / 32768.0)
    except Exception:
        return 0.0


async def handle_websocket_stream(
    websocket: WebSocket,
    eleven_client: ElevenLabs | None,
    hume_client: Any | None = None,
    gemini_client: Any | None = None,
    muse_provider: Any | None = None,
):
    await websocket.accept()
    token = websocket.query_params.get("token")
    expected = os.getenv("SPEECH_MCP_AUTH_TOKEN")
    if expected and token != expected:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    provider = websocket.query_params.get("provider", "windows")
    voice_id = websocket.query_params.get("voice", "default")

    try:
        if provider == "windows":
            await _handle_windows(websocket)
        elif provider == "elevenlabs":
            if not eleven_client:
                await websocket.close(code=1008, reason="ElevenLabs not configured")
                return
            await _handle_elevenlabs(websocket, eleven_client, voice_id)
        elif provider == "hume":
            api_key = os.getenv("HUME_API_KEY")
            if not api_key:
                await websocket.close(code=1008, reason="HUME key not configured")
                return
            hume_cfg = websocket.query_params.get("config_id") or None
            hume_system = websocket.query_params.get("system", "")
            hume_voice = websocket.query_params.get("voice", "")
            await _handle_hume(websocket, hume_client, api_key, hume_cfg, hume_system, hume_voice)
        elif provider == "gemini":
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                await websocket.close(code=1008, reason="GOOGLE key not configured")
                return
            await _handle_gemini(websocket, api_key, voice_id)
        elif provider == "gemini_live":
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                await websocket.close(code=1008, reason="GOOGLE key not configured")
                return
            voice_id = websocket.query_params.get("voice", "Kore")
            system = websocket.query_params.get("system", "")
            model = websocket.query_params.get("model") or os.getenv(
                "SPEECH_MCP_GEMINI_LIVE_MODEL", "gemini-3.1-flash-live-preview"
            )
            thinking = websocket.query_params.get("thinking")
            await _handle_gemini_live(websocket, api_key, voice_id, system, model, thinking)
        elif provider == "stt":
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                await websocket.close(code=1008, reason="GOOGLE key not configured")
                return
            await _handle_stt_stream(websocket, api_key)
        elif provider == "muse":
            if not muse_provider:
                await websocket.close(code=1008, reason="Muse Voice Transcribe not configured")
                return
            await _handle_muse_stream(websocket, muse_provider)
        else:
            await websocket.close(code=1008, reason=f"Unknown provider: {provider}")
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.exception(f"WS error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            logger.debug("WS error reply failed (socket already closed)")


async def _handle_stt_stream(websocket: WebSocket, api_key: str):
    """Gemini Live STT proxy placeholder - use REST /api/v1/transcribe for file/chunk STT."""
    del api_key
    await websocket.send_json(
        {
            "type": "error",
            "message": "STT stream not implemented - use /api/v1/transcribe?provider=funasr",
        }
    )
    await websocket.close(code=1008, reason="STT stream not implemented")


async def _handle_windows(websocket: WebSocket):
    while True:
        try:
            msg = await websocket.receive_json()
            if msg.get("type") == "tts":
                text = msg.get("text")
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp_path = tmp.name

                def _synth(t=text, p=tmp_path):
                    import pyttsx3

                    e = pyttsx3.init()
                    e.save_to_file(t, p)
                    e.runAndWait()

                await asyncio.to_thread(_synth)
                with open(tmp_path, "rb") as f:
                    await websocket.send_bytes(f.read())
                os.remove(tmp_path)
        except Exception:
            break


async def _handle_elevenlabs(websocket: WebSocket, client: ElevenLabs, voice_id: str):
    while True:
        try:
            msg = await websocket.receive_json()
            if msg.get("type") == "tts":
                text = msg.get("text")
                audio_gen = client.text_to_speech.convert(voice_id=voice_id, text=text, output_format="mp3_44100_128")
                for chunk in audio_gen:
                    await websocket.send_bytes(chunk)
        except Exception:
            break


async def _handle_hume(
    websocket: WebSocket,
    hume_client: Any | None,
    api_key: str,
    config_id: str | None = None,
    system_instruction: str = "",
    voice_name: str = "",
):
    """Full-duplex Hume EVI voice chat proxy.

    Browser  <──PCM 16kHz──>  this WS  <──base64 audio_input──>  Hume EVI
                              <──WAV bytes──┘  └──audio_output──┘

    Browser sends:
      - binary frames: raw 16-bit PCM at 16kHz (mic audio)
      - JSON text frames: { type: "text", text: "..." }  (text injection)

    Browser receives:
      - binary frames: WAV audio (48kHz from EVI, playable via AudioContext)
      - JSON: { type: "session_ready", ... }
      - JSON: { type: "transcript", role: "user"|"model", text }
      - JSON: { type: "emotion", scores: {...}, top: [...] }
      - JSON: { type: "interrupted" } / { type: "turn_complete" }
      - JSON: { type: "error", message }
    """
    from hume.empathic_voice.chat.socket_client import AudioInput, SessionSettings, UserInput

    cfg = (config_id or os.getenv("HUME_CONFIG_ID") or "").strip() or None
    if hume_client is None:
        try:
            from hume import HumeClient as _HumeClient

            hume_client = _HumeClient(api_key=api_key)
        except Exception as e:
            await websocket.send_json({"type": "error", "message": f"Hume init failed: {e}"})
            await websocket.close()
            return

    def _text_of(obj: Any) -> str:
        try:
            m = getattr(obj, "message", None)
            if m is None:
                return ""
            c = getattr(m, "content", "")
            return c if isinstance(c, str) else str(c or "")
        except Exception:
            return ""

    def _emotion_of(obj: Any) -> dict | None:
        try:
            models = getattr(obj, "models", None)
            prosody = getattr(models, "prosody", None) if models is not None else None
            scores = getattr(prosody, "scores", None) if prosody is not None else None
            if scores is None:
                return None
            dump = scores.model_dump() if hasattr(scores, "model_dump") else dict(scores)
            if not isinstance(dump, dict) or not dump:
                return None
            top = sorted(dump.items(), key=lambda kv: kv[1], reverse=True)[:5]
            return {"scores": dict(top), "top": [k for k, _ in top]}
        except Exception:
            return None

    try:
        async with hume_client.empathic_voice.chat.connect(
            api_key=api_key,
            config_id=cfg,
            verbose_transcription=True,
        ) as hume_ws:
            # Tell EVI we stream Linear16 16kHz mono + optional system prompt.
            try:
                from hume.empathic_voice.types.audio_configuration import AudioConfiguration

                settings_kwargs: dict[str, Any] = {
                    "audio": AudioConfiguration(channels=1, sample_rate=16000, encoding="linear16")
                }
                if system_instruction:
                    settings_kwargs["system_prompt"] = system_instruction
                if voice_name and voice_name.lower() != "default":
                    settings_kwargs["voice_id"] = voice_name
                await hume_ws.send_publish(SessionSettings(**settings_kwargs))
            except Exception as e:
                logger.debug("Hume session_settings failed (continuing): %s", e)

            await websocket.send_json({"type": "session_ready", "provider": "hume_evi", "config_id": cfg})
            logger.info("Hume EVI session opened (config_id=%s)", cfg or "default")

            async def browser_to_hume():
                while True:
                    try:
                        msg = await websocket.receive()
                    except WebSocketDisconnect:
                        break
                    except Exception:
                        break
                    if msg.get("type") == "websocket.disconnect":
                        break
                    try:
                        if msg.get("bytes") is not None:
                            b64 = base64.b64encode(msg["bytes"]).decode("ascii")
                            await hume_ws.send_publish(AudioInput(data=b64))
                        elif msg.get("text") is not None:
                            try:
                                ctrl = json.loads(msg["text"])
                            except json.JSONDecodeError:
                                continue
                            if ctrl.get("type") == "text" and ctrl.get("text"):
                                await hume_ws.send_publish(UserInput(text=ctrl["text"]))
                            # "end_turn" / "interrupt": Hume handles turn-taking
                            # natively; nothing to forward.
                    except Exception as e:
                        logger.debug("browser_to_hume error: %s", e)
                        break

            async def hume_to_browser():
                try:
                    async for event in hume_ws:
                        try:
                            etype = getattr(event, "type", "")
                            if etype == "audio_output":
                                raw = base64.b64decode(getattr(event, "data", ""))
                                if raw:
                                    await websocket.send_bytes(raw)
                            elif etype == "user_message":
                                text = _text_of(event)
                                if not text:
                                    continue
                                interim = bool(getattr(event, "interim", False))
                                await websocket.send_text(
                                    json.dumps(
                                        {
                                            "type": "interim" if interim else "transcript",
                                            "role": "user",
                                            "text": text,
                                        }
                                    )
                                )
                            elif etype == "assistant_message":
                                text = _text_of(event)
                                if text:
                                    await websocket.send_text(
                                        json.dumps({"type": "transcript", "role": "model", "text": text})
                                    )
                                emo = _emotion_of(event)
                                if emo:
                                    await websocket.send_text(json.dumps({"type": "emotion", **emo}))
                            elif etype == "assistant_prosody":
                                emo = _emotion_of(event)
                                if emo:
                                    await websocket.send_text(json.dumps({"type": "emotion", **emo}))
                            elif etype == "user_interruption":
                                await websocket.send_text(json.dumps({"type": "interrupted"}))
                            elif etype == "assistant_end":
                                await websocket.send_text(json.dumps({"type": "turn_complete"}))
                            elif etype == "chat_metadata":
                                await websocket.send_text(
                                    json.dumps(
                                        {
                                            "type": "session_info",
                                            "chat_id": str(getattr(event, "chat_id", "")),
                                            "chat_group_id": str(getattr(event, "chat_group_id", "")),
                                        }
                                    )
                                )
                            elif etype in ("web_socket_error", "error"):
                                detail = str(getattr(event, "message", event))
                                await websocket.send_text(json.dumps({"type": "error", "message": detail}))
                        except WebSocketDisconnect:
                            break
                        except Exception as e:
                            logger.debug("hume_to_browser event error: %s", e)
                            continue
                except WebSocketDisconnect:
                    pass
                except Exception as e:
                    logger.debug("hume_to_browser loop error: %s", e)
                    try:
                        await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
                    except Exception:
                        logger.debug("hume error reply failed (socket already closed)")

            async with anyio.create_task_group() as tg:
                tg.start_soon(browser_to_hume)
                tg.start_soon(hume_to_browser)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.exception("Hume EVI session error: %s", e)
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
        except Exception:
            logger.debug("Hume EVI error reply failed (socket already closed)")


async def _handle_gemini(websocket: WebSocket, api_key: str, voice_id: str):
    """Synthesize via GeminiProvider and send as a single WAV chunk."""
    from speech_mcp.providers.gemini import GeminiProvider

    try:
        provider = GeminiProvider()
    except Exception as e:
        await websocket.send_json({"type": "error", "message": f"Gemini init failed: {e}"})
        await websocket.close()
        return

    while True:
        try:
            msg = await websocket.receive_json()
        except Exception:
            break
        if msg.get("type") == "interrupt":
            break
        if msg.get("type") == "tts":
            text = msg.get("text", "")
            if not text:
                continue
            effective_voice = voice_id if voice_id and voice_id.lower() != "default" else "Kore"
            try:
                wav_bytes = await asyncio.to_thread(
                    lambda t=text, v=effective_voice: provider.synthesize_wav(t, voice_name=v)
                )
                await websocket.send_bytes(wav_bytes)
            except Exception as e:
                logger.exception("Gemini WS TTS failed")
                detail = str(e) or "Unknown Gemini error"
                lowered = detail.lower()
                if any(s in lowered for s in ("resource_exhausted", "prepayment", "prepay", "billing", " 402", "(402")):
                    detail += " Top up: https://ai.studio/projects (AI Studio > Billing)."
                await websocket.send_json({"type": "error", "message": f"Gemini TTS failed: {detail}"})


def _pcm_to_wav_bytes(pcm_bytes: bytes, sample_rate: int = 24000) -> bytes:
    """Wrap raw 16-bit mono PCM in a WAV container."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    return buf.getvalue()


async def _handle_gemini_live(
    websocket: WebSocket,
    api_key: str,
    voice_id: str = "Kore",
    system_instruction: str = "",
    model: str = "gemini-3.1-flash-live-preview",
    thinking_level: str | None = None,
):
    """
    Full-duplex Gemini Live voice chat proxy.

    Browser  <──PCM 16kHz──>  this WS  <──PCM 16kHz──>  Gemini Live API
                              (wraps output PCM in WAV for browser AudioContext)

    Browser sends:
      - binary frames: raw 16-bit PCM at 16kHz (mic audio)
      - JSON text frames: { type: "text", text: "..." }  (text injection)
      - JSON text frames: { type: "interrupt" }           (barge-in)
      - JSON text frames: { type: "end_turn" }            (signal turn complete)

    Browser receives:
      - binary frames: WAV-wrapped 24kHz PCM chunks (model audio)
      - JSON text frames: { type: "transcript", role: "user"|"model", text: "..." }
      - JSON text frames: { type: "turn_complete" }
      - JSON text frames: { type: "interrupted" }
      - JSON text frames: { type: "error", message: "..." }
    """
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    # gemini-3.8-live-extended-thinking rejects sessions with no thinking_level set;
    # other live models default fine to MINIMAL.
    default_level = "MEDIUM" if "extended-thinking" in model else "MINIMAL"
    level_name = (thinking_level or default_level).upper()
    config = types.LiveConnectConfig(
        response_modalities=[types.Modality.AUDIO],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_id))
        ),
        output_audio_transcription=types.AudioTranscriptionConfig(),
        input_audio_transcription=types.AudioTranscriptionConfig(),
        system_instruction=system_instruction or None,
        thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel(level_name)),
    )

    try:
        async with client.aio.live.connect(model=model, config=config) as session:
            logger.info("Gemini Live session opened (model=%s, voice=%s)", model, voice_id)

            # Notify browser that session is ready
            await websocket.send_text(json.dumps({"type": "session_ready", "voice": voice_id, "model": model}))

            async def browser_to_gemini():
                """Read from browser WebSocket, forward to Gemini."""
                while True:
                    try:
                        # Try to receive - could be binary (PCM) or text (JSON control)
                        msg = await websocket.receive()
                        if msg["type"] == "websocket.disconnect":
                            break

                        if msg.get("bytes") is not None:
                            # Raw PCM from browser mic (16kHz, 16-bit, mono)
                            await session.send_realtime_input(
                                audio=types.Blob(
                                    data=msg["bytes"],
                                    mime_type="audio/pcm;rate=16000",
                                )
                            )
                        elif msg.get("text") is not None:
                            try:
                                ctrl = json.loads(msg["text"])
                                if ctrl.get("type") == "text":
                                    # Inject text as user message
                                    await session.send_realtime_input(text=ctrl.get("text", ""))
                                elif ctrl.get("type") == "end_turn":
                                    await session.send_realtime_input(audio_stream_end=True)
                                elif ctrl.get("type") == "interrupt":
                                    # Browser-initiated barge-in - just stop sending audio
                                    # Gemini VAD handles server-side interruption
                                    pass
                            except json.JSONDecodeError:
                                pass
                    except WebSocketDisconnect:
                        break
                    except Exception as e:
                        logger.debug("browser_to_gemini error: %s", e)
                        break

            async def gemini_to_browser():
                """Read from Gemini Live session, forward to browser."""
                async for response in session.receive():
                    try:
                        sc = response.server_content
                        if sc is None:
                            continue

                        # Barge-in / interruption from server
                        if sc.interrupted:
                            await websocket.send_text(json.dumps({"type": "interrupted"}))
                            continue

                        # Audio chunks
                        if sc.model_turn and sc.model_turn.parts:
                            for part in sc.model_turn.parts:
                                if part.inline_data and part.inline_data.data:
                                    wav = _pcm_to_wav_bytes(part.inline_data.data)
                                    await websocket.send_bytes(wav)

                        # Output transcription (model speech → text)
                        if hasattr(sc, "output_transcription") and sc.output_transcription:
                            t = sc.output_transcription
                            if hasattr(t, "text") and t.text:
                                await websocket.send_text(
                                    json.dumps(
                                        {
                                            "type": "transcript",
                                            "role": "model",
                                            "text": t.text,
                                        }
                                    )
                                )

                        # Input transcription (user speech → text)
                        if hasattr(sc, "input_transcription") and sc.input_transcription:
                            t = sc.input_transcription
                            if hasattr(t, "text") and t.text:
                                await websocket.send_text(
                                    json.dumps(
                                        {
                                            "type": "transcript",
                                            "role": "user",
                                            "text": t.text,
                                        }
                                    )
                                )

                        # Turn complete
                        if sc.turn_complete:
                            await websocket.send_text(json.dumps({"type": "turn_complete"}))

                    except WebSocketDisconnect:
                        break
                    except Exception as e:
                        logger.debug("gemini_to_browser error: %s", e)
                        try:
                            await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
                        except Exception:
                            logger.debug("gemini error reply failed (socket already closed)")
                        break

            async with anyio.create_task_group() as tg:
                tg.start_soon(browser_to_gemini)
                tg.start_soon(gemini_to_browser)

    except Exception as e:
        logger.exception("Gemini Live session error: %s", e)
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
        except Exception:
            logger.debug("Gemini Live error reply failed (socket already closed)")


async def _handle_muse_stream(websocket: WebSocket, muse_provider: Any):
    """
    Realtime diarized transcription proxy (Meta Muse Voice Transcribe).

    Browser  ──PCM 16kHz mono──>  this WS  ──PCM 16kHz mono──>  Muse realtime API
                                  <──JSON events─────────────── (transcript/speaker/speechComplete)

    Browser sends:
      - binary frames: raw 16-bit PCM at 16kHz (mixed mic + call audio)
      - JSON text frame: { type: "end_turn" }  (flush and close the session)

    Browser receives Muse's normalized events verbatim as JSON text frames, e.g.
      { type: "speechComplete", speaker: "A", turnId: 3, transcript: "..." }
      { type: "error", message: "..." }
    """
    from speech_mcp.providers.muse import MuseRealtimeSession

    session = MuseRealtimeSession(muse_provider.config)
    try:
        ack = await session.connect(mode="DIARIZATION", encoding="PCM_16KHZ")
        await websocket.send_text(json.dumps({"type": "session", **ack}))

        async def browser_to_muse():
            while True:
                try:
                    msg = await websocket.receive()
                    if msg["type"] == "websocket.disconnect":
                        break
                    if msg.get("bytes") is not None:
                        await session.send_audio(msg["bytes"])
                    elif msg.get("text") is not None:
                        try:
                            ctrl = json.loads(msg["text"])
                            if ctrl.get("type") == "end_turn":
                                await session.end_stream()
                        except json.JSONDecodeError:
                            pass
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.debug("browser_to_muse error: %s", e)
                    break

        async def muse_to_browser():
            try:
                while True:
                    event = await session.recv_event()
                    if event is None:
                        break
                    await websocket.send_text(json.dumps(event))
            except Exception as e:
                logger.debug("muse_to_browser error: %s", e)
                try:
                    await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
                except Exception:
                    logger.debug("Muse error reply failed (socket already closed)")

        async with anyio.create_task_group() as tg:
            tg.start_soon(browser_to_muse)
            tg.start_soon(muse_to_browser)

    except Exception as e:
        logger.exception("Muse stream session error: %s", e)
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
        except Exception:
            logger.debug("Muse session error reply failed (socket already closed)")
    finally:
        await session.close()
