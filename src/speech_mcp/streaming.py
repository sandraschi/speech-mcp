import base64
import json
import logging
import os
import tempfile
from typing import Any

import anyio
import websockets
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
    gemini_url = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService/MultimodalLive?key={api_key}"
    async with websockets.connect(gemini_url) as gemini_ws:
        setup_frame = {
            "setup": {
                "model": "models/gemini-2.0-flash-exp",
                "generation_config": {
                    "response_modalities": ["AUDIO"],
                    "speech_config": {"voice_config": {"prebuilt_voice_config": {"voice_name": voice_id}}},
                },
            }
        }
        await gemini_ws.send(json.dumps(setup_frame))
        async def g2c():
            async for m in gemini_ws:
                data = json.loads(m)
                if "serverContent" in data:
                    content = data["serverContent"]
                    if "modelTurn" in content:
                        for p in content["modelTurn"]["parts"]:
                            if "inlineData" in p:
                                await websocket.send_bytes(base64.b64decode(p["inlineData"]["data"]))
                elif "setupComplete" in data:
                    pass
        async def c2g():
            while True:
                msg = await websocket.receive_json()
                if msg.get("type") == "tts":
                    f = {"clientContent": {"turns": [{"parts": [{"text": msg["text"]}]}], "turnComplete": True}}
                    await gemini_ws.send(json.dumps(f))
        async with anyio.create_task_group() as tg:
            tg.start_soon(g2c)
            tg.start_soon(c2g)

async def _handle_stt_stream(websocket: WebSocket, api_key: str):
    gemini_url = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService/MultimodalLive?key={api_key}"
    async with websockets.connect(gemini_url) as gemini_ws:
        setup = {
            "setup": {
                "model": "models/gemini-2.0-flash-exp",
                "generation_config": {"response_modalities": ["TEXT"]},
            }
        }
        await gemini_ws.send(json.dumps(setup))
        async def g2c():
            async for m in gemini_ws:
                data = json.loads(m)
                if "serverContent" in data:
                    content = data["serverContent"]
                    if "modelTurn" in content:
                        for p in content["modelTurn"]["parts"]:
                            if "text" in p:
                                await websocket.send_json({"type": "transcript", "text": p["text"], "is_final": content.get("turnComplete", False)})
                elif "setupComplete" in data:
                    await websocket.send_json({"type": "status", "status": "listening"})
        async def c2g():
            while True:
                try:
                    chunk = await websocket.receive_bytes()
                    f = {
                        "realtimeInput": {
                            "mediaChunks": [
                                {
                                    "data": base64.b64encode(chunk).decode("utf-8"),
                                    "mimeType": "audio/pcm",
                                }
                            ]
                        }
                    }
                    await gemini_ws.send(json.dumps(f))
                except Exception:
                    break
        async with anyio.create_task_group() as tg:
            tg.start_soon(g2c)
            tg.start_soon(c2g)
