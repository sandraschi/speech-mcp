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
            await _handle_hume(websocket, api_key)
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
            await _handle_gemini_live(websocket, api_key, voice_id, system)
        elif provider == "stt":
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                await websocket.close(code=1008, reason="GOOGLE key not configured")
                return
            await _handle_stt_stream(websocket, api_key)
        else:
            await websocket.close(code=1008, reason=f"Unknown provider: {provider}")
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.exception(f"WS error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


async def _handle_stt_stream(websocket: WebSocket, api_key: str):
    """Gemini Live STT proxy placeholder — use REST /api/v1/transcribe for file/chunk STT."""
    del api_key
    await websocket.send_json(
        {
            "type": "error",
            "message": "STT stream not implemented — use /api/v1/transcribe?provider=funasr",
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

                await anyio.to_thread.run_sync(_synth)
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
                audio_gen = client.generate(text=text, voice=voice_id, stream=True)
                for chunk in audio_gen:
                    await websocket.send_bytes(chunk)
        except Exception:
            break


async def _handle_hume(websocket: WebSocket, api_key: str):
    # Hume uses its own socket-like protocol, but we can proxy it
    pass


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
                wav_bytes = await anyio.to_thread.run_sync(
                    lambda t=text, v=effective_voice: provider.synthesize_wav(t, voice_name=v)
                )
                await websocket.send_bytes(wav_bytes)
            except Exception as e:
                logger.exception("Gemini WS TTS failed")
                await websocket.send_json({"type": "error", "message": str(e)})


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

    model = "gemini-3.1-flash-live-preview"
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_id))
        ),
        output_audio_transcription=types.AudioTranscriptionConfig(),
        input_audio_transcription=types.AudioTranscriptionConfig(),
        system_instruction=system_instruction or None,
        thinking_config=types.ThinkingConfig(thinking_level="minimal"),
    )

    try:
        async with client.aio.live.connect(model=model, config=config) as session:
            logger.info("Gemini Live session opened (voice=%s)", voice_id)

            # Notify browser that session is ready
            await websocket.send_text(json.dumps({"type": "session_ready", "voice": voice_id, "model": model}))

            async def browser_to_gemini():
                """Read from browser WebSocket, forward to Gemini."""
                while True:
                    try:
                        # Try to receive — could be binary (PCM) or text (JSON control)
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
                                    # Browser-initiated barge-in — just stop sending audio
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
                        if sc.model_turn:
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
                            pass
                        break

            async with anyio.create_task_group() as tg:
                tg.start_soon(browser_to_gemini)
                tg.start_soon(gemini_to_browser)

    except Exception as e:
        logger.exception("Gemini Live session error: %s", e)
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
        except Exception:
            pass
